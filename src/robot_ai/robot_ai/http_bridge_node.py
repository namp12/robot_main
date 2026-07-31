import os
import json
import threading
import subprocess
from http.server import HTTPServer, BaseHTTPRequestHandler

import rclpy
from rclpy.node import Node
from std_msgs.msg import String

ros_node = None
command_publisher = None
tts_publisher = None


def speak_on_pi(text: str):
    """Đọc giọng nói chuẩn tiếng Việt ra Loa Bluetooth / Audio Jack của Raspberry Pi."""
    if not text or not text.strip():
        return

    # 1. Thử dùng pyttsx3 với giọng đọc tiếng Việt
    try:
        import pyttsx3
        engine = pyttsx3.init()
        voices = engine.getProperty('voices')
        for v in voices:
            if 'vietnam' in v.name.lower() or 'vi' in v.id.lower():
                engine.setProperty('voice', v.id)
                break
        engine.say(text)
        engine.runAndWait()
        engine.stop()
        return
    except Exception:
        pass

    # 2. Fallback sang espeak-ng giọng tiếng Việt chuẩn (-v vi)
    try:
        cmd = f'espeak-ng -v vi "{text}" 2>/dev/null'
        os.system(cmd)
    except Exception:
        pass


class Handler(BaseHTTPRequestHandler):

    def do_POST(self):
        if self.path not in {"/command", "/robot/command", "/tts", "/speech/tts"}:
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

                if self.path in {"/tts", "/speech/tts"}:
                    if tts_publisher:
                        tts_publisher.publish(msg)
                    ros_node.get_logger().info(f'HTTP TTS: "{text}"')
                    # Đọc câu thoại ra Loa Bluetooth cắm tại Pi 4
                    threading.Thread(target=speak_on_pi, args=(text,), daemon=True).start()
                else:
                    if command_publisher:
                        command_publisher.publish(msg)
                    ros_node.get_logger().info(f'HTTP COMMAND: "{text}"')

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
    global command_publisher
    global tts_publisher

    rclpy.init()

    ros_node = Node("http_bridge")

    command_publisher = ros_node.create_publisher(String, "/robot/command", 10)
    tts_publisher = ros_node.create_publisher(String, "/speech/text", 10)

    server = HTTPServer(("0.0.0.0", 8001), Handler)

    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    ros_node.get_logger().info("HTTP bridge listening on port 8001 (Command & TTS Endpoints)")

    try:
        rclpy.spin(ros_node)
    except KeyboardInterrupt:
        pass

    server.shutdown()
    ros_node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
