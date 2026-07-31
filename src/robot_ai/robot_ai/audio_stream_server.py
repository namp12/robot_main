import socket
import sys
import time
import numpy as np

try:
    import sounddevice as sd
except ImportError:
    print("ERR: sounddevice missing on Pi. Install via: pip install sounddevice")
    sys.exit(1)

SAMPLE_RATE = 16000
CHANNELS = 1
CHUNK_SIZE = 1024


def main():
    target_ip = sys.argv[1] if len(sys.argv) > 1 else "255.255.255.255"  # Broadcast or PC IP
    target_port = 5000

    print("==============================================")
    print("      RASPBERRY PI - AUDIO STREAM SENDER      ")
    print("==============================================")
    print(f"Target PC IP: {target_ip}:{target_port}")
    print("Streaming Microphone PCM 16kHz Mono over UDP...")

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    if target_ip == "255.255.255.255":
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

    def audio_callback(indata, frames, time_info, status):
        if status:
            pass
        # Send raw bytes (float32 array)
        raw_bytes = indata.tobytes()
        try:
            sock.sendto(raw_bytes, (target_ip, target_port))
        except Exception:
            pass

    try:
        with sd.InputStream(samplerate=SAMPLE_RATE, channels=CHANNELS, dtype='float32', blocksize=CHUNK_SIZE, callback=audio_callback):
            print("Microphone streaming ACTIVE. Press CTRL+C to stop.")
            while True:
                time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping Audio Streamer...")
    except Exception as e:
        print(f"Audio error: {e}")
    finally:
        sock.close()
        print("Audio Streamer closed.")


if __name__ == '__main__':
    main()
