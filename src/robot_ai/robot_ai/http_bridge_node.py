import os
import json
import threading
import subprocess
from http.server import HTTPServer, BaseHTTPRequestHandler

import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from sensor_msgs.msg import LaserScan

ros_node = None
command_publisher = None
tts_publisher = None
detection_publisher = None
conversation_publisher = None
partial_publisher = None
final_publisher = None
esp32_tx_publisher = None

latest_scan_data = {
    "angle_min": -3.14159,
    "angle_max": 3.14159,
    "angle_increment": 0.017453,
    "ranges": []
}


def _on_scan_callback(msg):
    global latest_scan_data
    import math
    clean_ranges = [float(r) if not math.isinf(r) and not math.isnan(r) else 0.0 for r in msg.ranges]
    latest_scan_data = {
        "angle_min": float(msg.angle_min),
        "angle_max": float(msg.angle_max),
        "angle_increment": float(msg.angle_increment),
        "ranges": clean_ranges
    }


import queue

tts_queue = queue.Queue()


def _tts_worker_loop():
    """Background worker thread executing TTS playback sequentially without blocking HTTP server."""
    while True:
        try:
            text = tts_queue.get()
            if text:
                _play_tts_audio(text)
            tts_queue.task_done()
        except Exception:
            pass


def speak_on_pi(text: str):
    """Enqueue TTS text for non-blocking background playback."""
    if text and text.strip():
        tts_queue.put(text.strip())


def _play_tts_audio(text: str):
    """Play audio to Bluetooth LA16 / ALSA speaker using Google TTS with automatic text chunking."""
    if not text or not text.strip():
        return

    import urllib.parse
    import urllib.request
    import re

    # Chunk text into <= 150 char segments for Google TTS API
    sentences = re.split(r'([.!?,;\n])', text)
    chunks = []
    current = ""
    for item in sentences:
        if len(current) + len(item) <= 150:
            current += item
        else:
            if current.strip():
                chunks.append(current.strip())
            current = item
    if current.strip():
        chunks.append(current.strip())

    if not chunks:
        chunks = [text[:150]]

    mp3_path = "/tmp/speak.mp3"
    wav_path = "/tmp/speak.wav"
    headers = {'User-Agent': 'Mozilla/5.0'}

    try:
        combined_mp3 = bytearray()
        for chunk in chunks:
            url = f"https://translate.google.com/translate_tts?ie=UTF-8&q={urllib.parse.quote(chunk)}&tl=vi&client=tw-ob"
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=5) as response:
                combined_mp3.extend(response.read())

        with open(mp3_path, 'wb') as f:
            f.write(combined_mp3)

        # Convert MP3 to 22.05kHz 16-bit Mono WAV for PulseAudio smooth playback
        try:
            subprocess.run(["ffmpeg", "-y", "-i", mp3_path, "-ar", "22050", "-ac", "1", wav_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            if os.path.exists(wav_path):
                res = subprocess.run(["paplay", wav_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                if res.returncode == 0:
                    return
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
    except Exception as e:
        logger.error(f"TTS playback error on Pi: {e}")


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

    def do_GET(self):
        if self.path in {"/scan", "/robot/scan", "/api/v1/robot/scan"}:
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(latest_scan_data).encode())
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        if self.path not in {"/command", "/robot/command", "/tts", "/speech/tts", "/detection", "/conversation", "/speech/partial", "/partial", "/speech/final", "/speech/text"}:
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
                elif self.path in {"/speech/partial", "/partial"}:
                    if partial_publisher:
                        partial_publisher.publish(msg)
                elif self.path in {"/speech/final", "/speech/text"}:
                    if final_publisher:
                        final_publisher.publish(msg)
                    ros_node.get_logger().info(f'HTTP FINAL STT: "{text}"')
                elif self.path == "/detection":
                    if detection_publisher:
                        detection_publisher.publish(msg)
                elif self.path == "/conversation":
                    if conversation_publisher:
                        conversation_publisher.publish(msg)
                    ros_node.get_logger().info(f'HTTP CONVERSATION: "{text[:100]}..."')
                else:
                    if command_publisher:
                        command_publisher.publish(msg)
                    if esp32_tx_publisher:
                        esp32_tx_publisher.publish(msg)
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


class ReusableHTTPServer(HTTPServer):
    allow_reuse_address = True


def main():
    global ros_node
    global command_publisher
    global tts_publisher
    global detection_publisher
    global conversation_publisher
    global partial_publisher
    global final_publisher
    global esp32_tx_publisher

    rclpy.init()

    ros_node = Node("http_bridge")

    command_publisher = ros_node.create_publisher(String, "/robot/command", 10)
    tts_publisher = ros_node.create_publisher(String, "/speech/text", 10)
    detection_publisher = ros_node.create_publisher(String, "/ai/detection", 10)
    conversation_publisher = ros_node.create_publisher(String, "/ai/conversation", 10)
    partial_publisher = ros_node.create_publisher(String, "/speech/partial_text", 10)
    final_publisher = ros_node.create_publisher(String, "/speech/final_text", 10)
    esp32_tx_publisher = ros_node.create_publisher(String, "/esp32/serial_tx", 10)
    ros_node.create_subscription(LaserScan, "/scan", _on_scan_callback, 10)

    server = ReusableHTTPServer(("0.0.0.0", 8001), Handler)

    threading.Thread(target=_tts_worker_loop, daemon=True).start()
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
