import socket
import sys
import time
import subprocess
import numpy as np

SAMPLE_RATE = 16000
CHANNELS = 1
CHUNK_SIZE = 512  # 512 samples int16 = 1024 bytes (Perfect Wi-Fi UDP packet without fragmentation)


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
    print(f"ALSA Mic Device Selected: {alsa_dev}")
    print("Streaming USB Camera Microphone PCM 16kHz Mono over UDP...")

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

    # Try software virtual devices first (PulseAudio / PipeWire) to allow shared audio access,
    # then fallback to explicit hardware ALSA devices.
    devices_to_try = [
        ("parec", ["parec", "--format=s16le", "--rate=" + str(SAMPLE_RATE), "--channels=" + str(CHANNELS)]),
        ("arecord", ["arecord", "-D", "default", "-r", str(SAMPLE_RATE), "-c", str(CHANNELS), "-f", "S16_LE", "-t", "raw"]),
        ("arecord", ["arecord", "-D", "pulse", "-r", str(SAMPLE_RATE), "-c", str(CHANNELS), "-f", "S16_LE", "-t", "raw"]),
        ("arecord", ["arecord", "-D", alsa_dev, "-r", str(SAMPLE_RATE), "-c", str(CHANNELS), "-f", "S16_LE", "-t", "raw"]),
        ("arecord", ["arecord", "-D", "plughw:1,0", "-r", str(SAMPLE_RATE), "-c", str(CHANNELS), "-f", "S16_LE", "-t", "raw"]),
    ]

    proc = None
    max_retries = 3

    for attempt in range(max_retries):
        for tool_type, cmd in devices_to_try:
            try:
                dev_name = cmd[2] if tool_type == "arecord" and len(cmd) > 2 else tool_type
                print(f"Opening audio capture [{tool_type}] on device: {dev_name} (Attempt {attempt + 1})...")
                proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
                time.sleep(0.3)
                if proc.poll() is None:
                    print(f"🎯 Audio Microphone capture ACTIVE via [{dev_name}]. Streaming UDP to port {target_port}...")
                    alsa_dev = dev_name
                    break
                else:
                    proc = None
            except Exception as e:
                print(f"Failed to open audio device: {e}")
                proc = None
        if proc is not None:
            break
        print("⚠️ Audio device temporarily busy, retrying in 0.5s...")
        time.sleep(0.5)

    if proc is None or proc.poll() is not None:
        print("❌ FATAL: Could not open any audio microphone device on Pi 4!")
        sock.close()
        return

    bytes_per_chunk = CHUNK_SIZE * 2  # 16-bit = 2 bytes per sample
    last_ip_check = 0.0
    pc_ip = target_ip
    chunk_counter = 0

    try:
        while True:
            data = proc.stdout.read(bytes_per_chunk)
            if not data:
                break

            now = time.time()
            if now - last_ip_check > 3.0:
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
                print(f"🎙️ [PI AUDIO STREAM] 🟢 Đang thu âm từ [{alsa_dev}] & truyền tới PC IP ({pc_ip}:5000) - Gói: {chunk_counter}")

            # Send raw int16 PCM bytes directly (matches PhoWhisper decoder int16 format)
            raw_payload = data
            chunk_counter += 1

            # Send to Direct PC IP if available, otherwise Broadcast (never send both to prevent duplicate audio packets)
            if pc_ip and pc_ip != "255.255.255.255":
                try:
                    sock.sendto(raw_payload, (pc_ip, target_port))
                except Exception:
                    pass
            else:
                try:
                    sock.sendto(raw_payload, ("255.255.255.255", target_port))
                except Exception:
                    pass

    except KeyboardInterrupt:
        print("\nStopping Audio Streamer...")
    except Exception as e:
        print(f"ALSA streaming error: {e}")
    finally:
        if proc and proc.poll() is None:
            proc.terminate()
        sock.close()
        print("Audio Streamer closed.")


if __name__ == '__main__':
    main()
