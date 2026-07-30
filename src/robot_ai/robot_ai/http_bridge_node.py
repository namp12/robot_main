import rclpy
from rclpy.node import Node
from std_msgs.msg import String

from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import threading


ros_node = None
publisher = None


class Handler(BaseHTTPRequestHandler):

    def do_POST(self):

        if self.path not in {"/command", "/robot/command"}:
            self.send_response(404)
            self.end_headers()
            return

        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length)
        text = ""

        try:
            content_type = self.headers.get('Content-Type', '')
            if 'application/json' in content_type:
                data = json.loads(body)
                text = data.get('text', '')
            elif 'application/x-www-form-urlencoded' in content_type:
                params = dict(x.split('=') for x in body.decode().split('&') if '=' in x)
                text = params.get('text', '')
            else:
                raw = body.decode('utf-8', errors='ignore').strip()
                if raw.startswith('{') and raw.endswith('}'):
                    try:
                        data = json.loads(raw)
                        text = data.get('text', '')
                    except json.JSONDecodeError:
                        text = raw
                else:
                    text = raw

            if text:
                msg = String()
                msg.data = text
                publisher.publish(msg)

                ros_node.get_logger().info(f'HTTP COMMAND: {text}')

            response = {
                'status': 'received',
                'text': text
            }

            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(response).encode())

        except json.JSONDecodeError as e:
            ros_node.get_logger().error(f'Invalid JSON request body: {e}')
            self.send_response(400)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'status': 'error', 'message': 'Invalid JSON body'}).encode())
        except Exception as e:
            ros_node.get_logger().error(str(e))
            self.send_response(400)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'status': 'error', 'message': 'Invalid request'}).encode())


def main():

    global ros_node
    global publisher

    rclpy.init()

    ros_node = Node("http_bridge")

    publisher = ros_node.create_publisher(
        String,
        "/robot/command",
        10
    )

    server = HTTPServer(
        ("0.0.0.0", 8001),
        Handler
    )

    thread = threading.Thread(
        target=server.serve_forever,
        daemon=True
    )

    thread.start()

    ros_node.get_logger().info(
        "HTTP bridge listening on port 8001"
    )

    try:
        rclpy.spin(ros_node)

    except KeyboardInterrupt:
        pass

    server.shutdown()
    ros_node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
