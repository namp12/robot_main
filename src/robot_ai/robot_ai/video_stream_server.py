import cv2
import time
import numpy as np
from http.server import BaseHTTPRequestHandler, HTTPServer
from socketserver import ThreadingMixIn
import threading

camera = None
_latest_jpeg_bytes: bytes | None = None
_lock = threading.Lock()
_running = True


def camera_capture_loop():
    """Luồng ngầm độc quyền đọc /dev/video0 tránh tranh chấp đa luồng HTTP."""
    global camera, _latest_jpeg_bytes, _running
    while _running:
        try:
            if camera is not None and camera.isOpened():
                ret, frame = camera.read()
                if ret and frame is not None:
                    res, jpeg = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), 75])
                    if res:
                        with _lock:
                            _latest_jpeg_bytes = jpeg.tobytes()
                else:
                    time.sleep(0.02)
            else:
                time.sleep(0.05)
        except Exception:
            time.sleep(0.02)
        time.sleep(0.025)  # ~40 FPS capture rate


class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    """Threaded HTTP server to handle multiple viewers without blocking."""
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
                    with _lock:
                        data = _latest_jpeg_bytes

                    if data is None:
                        # Frame fallback khi Camera chưa sẵn sàng
                        img = np.zeros((480, 640, 3), dtype=np.uint8)
                        img[:] = (40, 20, 10)
                        cv2.putText(img, "CAMERA INITIALIZING...", (140, 240), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
                        _, jpeg = cv2.imencode('.jpg', img)
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

    def log_message(self, format, *args):
        # Suppress logging to improve performance
        return


def main():
    global camera, _running
    print("==============================================")
    print("  RASPBERRY PI - THREAD-SAFE VIDEO STREAM     ")
    print("==============================================")
    # Auto-detect working camera device index (tries 0, 1, 2, 4)
    camera = None
    for idx in [0, 1, 2, 4]:
        print(f"Testing camera index /dev/video{idx}...")
        cap = cv2.VideoCapture(idx, cv2.CAP_V4L2)
        if not cap.isOpened():
            cap = cv2.VideoCapture(idx)

        if cap.isOpened():
            cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            cap.set(cv2.CAP_PROP_FPS, 30)

            # Test frame read to verify device isn't a dummy metadata node
            ret, test_frame = cap.read()
            if ret and test_frame is not None and test_frame.size > 0:
                print(f"🎯 Camera ACTIVE on /dev/video{idx} ({test_frame.shape[1]}x{test_frame.shape[0]})!")
                camera = cap
                break
            else:
                cap.release()

    if camera is None or not camera.isOpened():
        print("ERROR: Cannot open any camera device (/dev/video0, /dev/video1, /dev/video2)!")
        return

    _running = True
    capture_thread = threading.Thread(target=camera_capture_loop, daemon=True)
    capture_thread.start()

    port = 8080
    server = ThreadedHTTPServer(('0.0.0.0', port), CamHandler)
    print(f"Video MJPEG Streamer running on http://0.0.0.0:{port}/video_feed")
    print("Press CTRL+C to stop.")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping Video Stream Server...")
    finally:
        _running = False
        server.shutdown()
        if camera:
            camera.release()
        print("Camera released.")


if __name__ == '__main__':
    main()
