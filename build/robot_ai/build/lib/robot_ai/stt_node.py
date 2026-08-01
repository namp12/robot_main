#!/usr/bin/env python3
"""
stt_node.py

ROS2 node that captures microphone audio and publishes recognized text
on /speech/text. Supports Google Speech, PocketSphinx, Whisper, and
OpenAI Whisper if available through SpeechRecognition.
"""

import os
import traceback
from concurrent.futures import ThreadPoolExecutor
from typing import Optional

import rclpy
from rclpy.node import Node
from std_msgs.msg import String


class SpeechToTextNode(Node):
    def __init__(self) -> None:
        super().__init__('speech_to_text_node')

        self.declare_parameter('speech_text_topic', '/speech/text')
        self.declare_parameter('language', 'vi-VN')
        self.declare_parameter('stt_engine', 'whisper_api')
        self.declare_parameter('microphone_index', -1)
        self.declare_parameter('phrase_time_limit', 6.0)
        self.declare_parameter('pause_threshold', 0.8)
        self.declare_parameter('timeout', 10.0)
        self.declare_parameter('energy_threshold', 300)
        self.declare_parameter('dynamic_energy_threshold', True)
        self.declare_parameter('openai_enabled', True)
        self.declare_parameter('openai_api_key', '')

        self._speech_text_topic = self.get_parameter('speech_text_topic').value
        self._language = self.get_parameter('language').value
        self._stt_engine = str(self.get_parameter('stt_engine').value).lower()
        self._microphone_index = int(self.get_parameter('microphone_index').value)
        self._phrase_time_limit = float(self.get_parameter('phrase_time_limit').value)
        self._pause_threshold = float(self.get_parameter('pause_threshold').value)
        self._timeout = float(self.get_parameter('timeout').value)
        self._energy_threshold = int(self.get_parameter('energy_threshold').value)
        self._dynamic_energy_threshold = bool(self.get_parameter('dynamic_energy_threshold').value)
        self._openai_enabled = bool(self.get_parameter('openai_enabled').value)
        self._openai_api_key = str(self.get_parameter('openai_api_key').value).strip()

        self._speech_pub = self.create_publisher(String, self._speech_text_topic, 10)
        self._executor = ThreadPoolExecutor(max_workers=2)

        self._recognizer = None
        self._microphone = None
        self._stop_listening = None

        self._initialize_recognizer()

    def _initialize_recognizer(self) -> None:
        try:
            import speech_recognition as sr
        except ImportError:
            self.get_logger().error(
                'SpeechRecognition package not installed. Install it with: pip3 install SpeechRecognition'
            )
            return

        self._recognizer = sr.Recognizer()
        self._recognizer.pause_threshold = self._pause_threshold
        self._recognizer.energy_threshold = self._energy_threshold
        self._recognizer.dynamic_energy_threshold = self._dynamic_energy_threshold

        mic_kwargs = {}
        if self._microphone_index >= 0:
            mic_kwargs['device_index'] = self._microphone_index

        try:
            with sr.Microphone(**mic_kwargs) as source:
                self._recognizer.adjust_for_ambient_noise(source, duration=1.0)
                self.get_logger().info(
                    f'Calibrated ambient noise level: energy_threshold={self._recognizer.energy_threshold}'
                )
                self._microphone = source

            self._stop_listening = self._recognizer.listen_in_background(
                sr.Microphone(**mic_kwargs),
                self._audio_callback,
                phrase_time_limit=self._phrase_time_limit,
            )
            self.get_logger().info(
                f'Speech recognition started: engine={self._stt_engine}, language={self._language}'
            )
        except Exception as exc:
            self.get_logger().error(f'Failed to start microphone listener: {exc}')
            self.get_logger().debug(traceback.format_exc())
            self._recognizer = None

    def _audio_callback(self, recognizer, audio) -> None:
        self._executor.submit(self._process_audio, audio)

    def _process_audio(self, audio) -> None:
        try:
            transcript = self._recognize_audio(audio)
            if transcript:
                msg = String()
                msg.data = transcript
                self._speech_pub.publish(msg)
                self.get_logger().info(f'Recognized speech: {transcript}')
        except Exception as exc:
            self.get_logger().warning(f'Speech recognition failed: {exc}')
            self.get_logger().debug(traceback.format_exc())

    def _recognize_audio(self, audio) -> Optional[str]:
        if self._recognizer is None:
            return None

        engine = self._stt_engine
        try:
            if engine in {'whisper_api', 'openai_whisper_api', 'whisper-api'}:
                if hasattr(self._recognizer, 'recognize_whisper_api'):
                    api_key = self._openai_api_key or os.environ.get('OPENAI_API_KEY', '')
                    if not api_key:
                        self.get_logger().warning(
                            'whisper_api selected but no OPENAI_API_KEY available. Falling back to Google STT.'
                        )
                    else:
                        return self._recognizer.recognize_whisper_api(
                            audio,
                            key=api_key,
                            language=self._language,
                        )
                else:
                    self.get_logger().warning('recognize_whisper_api not available in SpeechRecognition library')

            if engine == 'whisper' and hasattr(self._recognizer, 'recognize_whisper'):
                return self._recognizer.recognize_whisper(audio, language=self._language)
            if engine == 'sphinx' and hasattr(self._recognizer, 'recognize_sphinx'):
                return self._recognizer.recognize_sphinx(audio, language=self._language)
            return self._recognizer.recognize_google(audio, language=self._language)
        except Exception as exc:
            self.get_logger().warning(f'Recognizer error ({engine}): {exc}')
            return None

    def destroy_node(self) -> None:
        if self._stop_listening is not None:
            self._stop_listening(wait_for_stop=False)
        self._executor.shutdown(wait=False)
        super().destroy_node()


def main(args=None) -> None:
    rclpy.init(args=args)
    node = SpeechToTextNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
