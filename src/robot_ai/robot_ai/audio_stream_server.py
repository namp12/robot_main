import socket
import sys
import time
import subprocess
import numpy as np

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

    # Try sounddevice first
    sd_success = False
    try:
        import sounddevice as sd

        def audio_callback(indata, frames, time_info, status):
            raw_bytes = indata.tobytes()
            try:
                sock.sendto(raw_bytes, (target_ip, target_port))
            except Exception:
                pass

        with sd.InputStream(samplerate=SAMPLE_RATE, channels=CHANNELS, dtype='float32', blocksize=CHUNK_SIZE, callback=audio_callback):
            print("Microphone streaming ACTIVE (via sounddevice). Press CTRL+C to stop.")
            sd_success = True
            while True:
                time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping Audio Streamer...")
        sock.close()
        return
    except Exception as e:
        print(f"sounddevice unavailable: {e}. Switching to ALSA arecord fallback...")

    # Fallback to Linux ALSA arecord
    if not sd_success:
        cmd = [
            "arecord",
            "-D", "default",
            "-r", str(SAMPLE_RATE),
            "-c", str(CHANNELS),
            "-f", "S16_LE",
            "-t", "raw"
        ]
        try:
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
            print("Microphone streaming ACTIVE (via ALSA arecord). Press CTRL+C to stop.")
            bytes_per_chunk = CHUNK_SIZE * 2  # 16-bit = 2 bytes per sample
            while True:
                data = proc.stdout.read(bytes_per_chunk)
                if not data:
                    break
                # Convert int16 to float32 normalized [-1, 1]
                int16_arr = np.frombuffer(data, dtype=np.int16)
                float32_arr = (int16_arr / 32768.0).astype(np.float32)
                sock.sendto(float32_arr.tobytes(), (target_ip, target_port))
        except KeyboardInterrupt:
            print("\nStopping Audio Streamer...")
        except Exception as e:
            print(f"ALSA arecord error: {e}")
        finally:
            if 'proc' in locals():
                proc.terminate()

    sock.close()
    print("Audio Streamer closed.")


if __name__ == '__main__':
    main()
