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
detection_publisher = None
conversation_publisher = None


def speak_on_pi(text: str):
    """Đọc giọng nói chuẩn tiếng Việt ra Loa Bluetooth / Audio Jack của Raspberry Pi."""
    if not text or not text.strip():
        return

    # 1. Thử tải giọng nói tự nhiên trực tuyến từ Google TTS
    try:
        import urllib.parse
        import urllib.request
        encoded_text = urllib.parse.quote(text)
        url = f"https://translate.google.com/translate_tts?ie=UTF-8&client=tw-ob&tl=vi&q={encoded_text}"
        
def speak_on_pi(text: str):
    """Phát âm thanh mượt mà qua Loa Bluetooth LA16 mà không bị rè/giật."""
    if not text:
        return
    try:
        url = f"https://translate.google.com/translate_tts?ie=UTF-8&q={urllib.parse.quote(text)}&tl=vi&client=tw-ob"
        mp3_path = "/tmp/speak.mp3"
        wav_path = "/tmp/speak.wav"
        headers = {'User-Agent': 'Mozilla/5.0'}
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req) as response:
            with open(mp3_path, 'wb') as f:
                f.write(response.read())

        # Convert MP3 to 22.05kHz 16-bit Mono WAV for PulseAudio smooth playback
        try:
            subprocess.run(["ffmpeg", "-y", "-i", mp3_path, "-ar", "22050", "-ac", "1", wav_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            if os.path.exists(wav_path):
                # Try paplay (PulseAudio native - 100% smooth on Bluetooth LA16 speaker)
                res = subprocess.run(["paplay", wav_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                if res.returncode == 0:
                    return
                # Try aplay
                res = subprocess.run(["aplay", "-D", "default", wav_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                if res.returncode == 0:
                    return
        except Exception:
            pass

        # Fallback players with buffer boost
        players = [
            ["mpg123", "-b", "2048", "-q", mp3_path],
            ["mpv", "--no-video", "--ao=pulse", mp3_path],
            ["ffplay", "-nodisp", "-autoexit", mp3_path],
            ["cvlc", "--play-and-exit", mp3_path]
        ]
        for cmd in players:
            try:
                res = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                if res.returncode == 0:
                    return
            except FileNotFoundError:
                continue
    except Exception:
        pass


class Handler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        # Tắt in log HTTP 200 liên tục để giữ Terminal Pi sạch sẽ và tăng tốc độ
        return

    def handle(self):
        try:
            super().handle()
        except (ConnectionResetError, BrokenPipeError):
            if ros_node:
                ros_node.get_logger().info("HTTP client disconnected before request completed")
            return

    def do_POST(self):
        if self.path not in {"/command", "/robot/command", "/tts", "/speech/tts", "/detection", "/conversation"}:
            self.send_response(404)
            self.end_headers()
            return

        # Save PC client IP for targeted UDP audio streaming
        try:
            client_ip = self.client_address[0]
            if client_ip and client_ip != "127.0.0.1":
                with open('/tmp/last_pc_ip.txt', 'w') as f:
                    f.write(client_ip)
        except Exception:
            pass

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
                elif self.path == "/detection":
                    if detection_publisher:
                        detection_publisher.publish(msg)
                    # Suppress spam log print for detection
                elif self.path == "/conversation":
                    if conversation_publisher:
                        conversation_publisher.publish(msg)
                    ros_node.get_logger().info(f'HTTP CONVERSATION: "{text[:100]}..."')
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
    global detection_publisher
    global conversation_publisher

    rclpy.init()

    ros_node = Node("http_bridge")

    command_publisher = ros_node.create_publisher(String, "/robot/command", 10)
    tts_publisher = ros_node.create_publisher(String, "/speech/text", 10)
    detection_publisher = ros_node.create_publisher(String, "/ai/detection", 10)
    conversation_publisher = ros_node.create_publisher(String, "/ai/conversation", 10)

    server = HTTPServer(("0.0.0.0", 8001), Handler)

    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    ros_node.get_logger().info("HTTP bridge listening on port 8001 (Command, TTS, Detection & Conversation Endpoints)")

    try:
        rclpy.spin(ros_node)
    except KeyboardInterrupt:
        pass

    server.shutdown()
    ros_node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
