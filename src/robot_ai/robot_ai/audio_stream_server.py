import socket
import sys
import time
import subprocess
import numpy as np

SAMPLE_RATE = 16000
CHANNELS = 1
CHUNK_SIZE = 1024


def find_alsa_usb_mic() -> str:
    """Auto-detect USB Camera Microphone ALSA card from arecord -l."""
    import re
    try:
        res = subprocess.run(["arecord", "-l"], capture_output=True, text=True)
        lines = res.stdout.splitlines()
        for line in lines:
            if "card" in line.lower() and ("u2k" in line.lower() or "ugreen" in line.lower() or "usb" in line.lower() or "camera" in line.lower() or "device" in line.lower() or "audio" in line.lower() or "mic" in line.lower()):
                m = re.search(r'card\s+(\d+)', line, re.IGNORECASE)
                if m:
                    card_num = m.group(1)
                    return f"plughw:{card_num},0"
        # If no explicit string, pick the first card (card 1)
        for line in lines:
            m = re.search(r'card\s+([1-9])', line, re.IGNORECASE)
            if m:
                return f"plughw:{m.group(1)},0"
    except Exception:
        pass
    return "plughw:1,0"


def main():
    target_ip = sys.argv[1] if len(sys.argv) > 1 else "255.255.255.255"  # Broadcast or PC IP
    target_port = 5000

    print("==============================================")
    print("      RASPBERRY PI - AUDIO STREAM SENDER      ")
    print("==============================================")
    alsa_dev = find_alsa_usb_mic()
    print(f"Target PC IP: {target_ip}:{target_port}")
    print(f"ALSA Mic Device Detected: {alsa_dev}")
    print("Streaming USB Camera Microphone PCM 16kHz Mono over UDP...")

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
        print(f"sounddevice unavailable: {e}. Switching to ALSA arecord fallback ({alsa_dev})...")

    # Fallback to Linux ALSA arecord with auto-detected USB camera mic
    if not sd_success:
        cmd = [
            "arecord",
            "-D", alsa_dev,
            "-r", str(SAMPLE_RATE),
            "-c", str(CHANNELS),
            "-f", "S16_LE",
            "-t", "raw"
        ]
        try:
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
            print(f"Microphone streaming ACTIVE via ALSA ({alsa_dev}). Press CTRL+C to stop.")
            bytes_per_chunk = CHUNK_SIZE * 2  # 16-bit = 2 bytes per sample
            last_ip_check = 0.0
            pc_ip = target_ip

            while True:
                data = proc.stdout.read(bytes_per_chunk)
                if not data:
                    break

                now = time.time()
                if now - last_ip_check > 2.0:
                    last_ip_check = now
                    try:
                        import os
                        if os.path.exists('/tmp/last_pc_ip.txt'):
                            with open('/tmp/last_pc_ip.txt', 'r') as f:
                                ip_str = f.read().strip()
                                if ip_str and ip_str != "127.0.0.1":
                                    pc_ip = ip_str
                    except Exception:
                        pass

                # Convert int16 to float32 normalized [-1, 1]
                int16_arr = np.frombuffer(data, dtype=np.int16)
                float32_arr = (int16_arr / 32768.0).astype(np.float32)
                raw_payload = float32_arr.tobytes()

                # Send both to Broadcast and Direct PC IP for 100% reliable reception
                try:
                    sock.sendto(raw_payload, ("255.255.255.255", target_port))
                except Exception:
                    pass

                if pc_ip and pc_ip != "255.255.255.255":
                    try:
                        sock.sendto(raw_payload, (pc_ip, target_port))
                    except Exception:
                        pass

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
