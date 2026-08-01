import cv2
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from socketserver import ThreadingMixIn
import threading

camera = None


class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    """Threaded HTTP server to handle multiple viewers if needed."""
    daemon_threads = True


class CamHandler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', '*')
        self.end_headers()

    def do_GET(self):
        if self.path.startswith('/video_feed') or self.path == '/':
            self.send_response(200)
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
            self.send_header('Access-Control-Allow-Headers', '*')
            self.send_header('Content-Type', 'multipart/x-mixed-replace; boundary=FRAME')
            self.end_headers()
            while True:
                try:
                    frame = None
                    if camera is not None and camera.isOpened():
                        ret, frame = camera.read()
                    
                    if frame is None:
                        # Frame fallback khi Camera bị khoá hoặc ngắt kết nối
                        frame = np.zeros((480, 640, 3), dtype=np.uint8)
                        frame[:] = (40, 20, 10)
                        cv2.putText(frame, "CAMERA HARDWARE BUSY / OFFLINE", (50, 240), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                        cv2.putText(frame, "Check USB cable or close other camera apps", (70, 280), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)

                    # Compress frame to JPEG
                    ret, jpeg = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), 75])
                    if not ret:
                        continue

                    data = jpeg.tobytes()
                    self.wfile.write(b'--FRAME\r\n')
                    self.send_header('Content-Type', 'image/jpeg')
                    self.send_header('Content-Length', str(len(data)))
                    self.end_headers()
                    self.wfile.write(data)
                    self.wfile.write(b'\r\n')
                    time.sleep(0.033)  # ~30 FPS limit
                except (BrokenPipeError, ConnectionResetError):
                    break
                except Exception:
                    break
        else:
            self.send_response(404)
            self.end_headers()


def main():
    global camera
    print("==============================================")
    print("      RASPBERRY PI - VIDEO STREAM SERVER      ")
    print("==============================================")
    print("Opening /dev/video0...")

    camera = cv2.VideoCapture(0)
    camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    if not camera.isOpened():
        print("ERROR: Cannot open camera /dev/video0!")
        return

    port = 8080
    server = ThreadedHTTPServer(('0.0.0.0', port), CamHandler)
    print(f"Video MJPEG Streamer running on http://0.0.0.0:{port}/video_feed")
    print("Press CTRL+C to stop.")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping Video Stream Server...")
    finally:
        server.shutdown()
        if camera:
            camera.release()
        print("Camera released.")


if __name__ == '__main__':
    main()
