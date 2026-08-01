#!/usr/bin/env python3
"""
dialogue_tts_node.py

ROS2 node that converts ASR text into a dialogue response, optionally
calls OpenAI ChatGPT, publishes navigation/command intent, and speaks
back via pyttsx3 when available.

The node is designed for Pi4 edge operation with remote AI enabled only
when configured, and a lightweight offline fallback otherwise.
"""

import json
import os
import re
import traceback
from concurrent.futures import ThreadPoolExecutor
from typing import Optional, Tuple

import rclpy
from rclpy.node import Node
from std_msgs.msg import String


class DialogueTTSNode(Node):
    def __init__(self) -> None:
        super().__init__('dialogue_tts_node')

        # ---- Params ----
        self.declare_parameter('openai_enabled', True)
        self.declare_parameter('openai_model', 'gpt-3.5-turbo')
        self.declare_parameter('openai_temperature', 0.7)
        self.declare_parameter('response_max_tokens', 150)
        self.declare_parameter('tts_enabled', True)
        self.declare_parameter('speech_text_topic', '/speech/text')
        self.declare_parameter('response_topic', '/dialogue/response')
        self.declare_parameter('command_topic', '/dialogue/command')
        self.declare_parameter('openai_api_key', '')
        self.declare_parameter('openai_system_prompt', (
            'You are a helpful robot assistant. Keep answers short, polite, and '
            'focused on the user request. If the user asks for movement commands, '
            'return the best matching navigation intent.'
        ))

        self._openai_enabled = bool(self.get_parameter('openai_enabled').value)
        self._openai_model = str(self.get_parameter('openai_model').value)
        self._openai_temperature = float(self.get_parameter('openai_temperature').value)
        self._response_max_tokens = int(self.get_parameter('response_max_tokens').value)
        self._tts_enabled = bool(self.get_parameter('tts_enabled').value)
        self._speech_text_topic = str(self.get_parameter('speech_text_topic').value)
        self._response_topic = str(self.get_parameter('response_topic').value)
        self._command_topic = str(self.get_parameter('command_topic').value)
        self._openai_api_key = str(self.get_parameter('openai_api_key').value).strip()
        self._openai_system_prompt = str(self.get_parameter('openai_system_prompt').value)

        # ---- Publishers / Subscribers ----
        self._response_pub = self.create_publisher(String, self._response_topic, 10)
        self._command_pub = self.create_publisher(String, self._command_topic, 10)
        self._speech_sub = self.create_subscription(
            String,
            self._speech_text_topic,
            self._on_speech_text,
            10,
        )

        # ---- Thread pool for OpenAI and TTS work ----
        self._executor = ThreadPoolExecutor(max_workers=2)

        # ---- TTS initialization ----
        self._tts_engine = None
        if self._tts_enabled:
            try:
                import pyttsx3
                self._tts_engine = pyttsx3.init()
            except Exception as exc:
                self.get_logger().warning(f'pyttsx3 unavailable: {exc}. TTS disabled.')
                self._tts_engine = None

        # ---- OpenAI initialization ----
        self._openai = None
        if self._openai_enabled:
            try:
                import openai
                self._openai = openai
                api_key = self._openai_api_key or os.environ.get('OPENAI_API_KEY', '')
                if api_key:
                    self._openai.api_key = api_key
                else:
                    self.get_logger().warning(
                        'openai_enabled=true but no OPENAI_API_KEY found. Remote AI disabled.'
                    )
                    self._openai = None
            except Exception as exc:
                self.get_logger().warning(f'OpenAI package unavailable: {exc}. Remote AI disabled.')
                self._openai = None

        self.get_logger().info(
            'DialogueTTS node started: '
            f'openai_enabled={self._openai is not None}, '
            f'tts_enabled={self._tts_engine is not None}'
        )

    def _on_speech_text(self, msg: String) -> None:
        text = msg.data.strip()
        if not text:
            return

        self.get_logger().info(f'Received speech text: {text}')
        self._executor.submit(self._handle_query, text)

    def _handle_query(self, text: str) -> None:
        try:
            response_text, command = self._generate_response(text)
            if not response_text:
                response_text = 'Xin lỗi, tôi chưa trả lời được.'

            self._publish_text(response_text)
            if command:
                self._publish_command(command)

            if self._tts_engine is not None:
                self._executor.submit(self._speak, response_text)

        except Exception:
            self.get_logger().error(f'Error handling query:\n{traceback.format_exc()}')

    def _publish_text(self, text: str) -> None:
        msg = String()
        msg.data = text
        self._response_pub.publish(msg)

    def _publish_command(self, command: str) -> None:
        msg = String()
        msg.data = command
        self._command_pub.publish(msg)
        self.get_logger().info(f'Published command intent: {command}')

    def _generate_response(self, text: str) -> Tuple[str, Optional[str]]:
        command = self._parse_command(text)
        response = None

        if self._openai is not None:
            response = self._call_openai(text)

        if response:
            return response, command

        response = self._fallback_response(text, command)
        return response, command

    def _call_openai(self, text: str) -> Optional[str]:
        try:
            if hasattr(self._openai, 'ChatCompletion'):
                completion = self._openai.ChatCompletion.create(
                    model=self._openai_model,
                    messages=[
                        {'role': 'system', 'content': self._openai_system_prompt},
                        {'role': 'user', 'content': text},
                    ],
                    temperature=self._openai_temperature,
                    max_tokens=self._response_max_tokens,
                )
                choice = completion.choices[0]
                return choice.message.content.strip()

            if hasattr(self._openai, 'Completion'):
                completion = self._openai.Completion.create(
                    model=self._openai_model,
                    prompt=text,
                    temperature=self._openai_temperature,
                    max_tokens=self._response_max_tokens,
                )
                return completion.choices[0].text.strip()

        except Exception as exc:
            self.get_logger().warning(f'OpenAI request failed: {exc}')

        return None

    def _fallback_response(self, text: str, command: Optional[str]) -> str:
        lower = text.lower()

        if command:
            if command == 'stop':
                return 'Đã hiểu. Tôi sẽ dừng lại ngay.'
            if command == 'forward':
                return 'Được rồi, tiến về phía trước.'
            if command == 'backward':
                return 'Tôi sẽ lùi lại.'
            if command == 'left':
                return 'Quay trái ngay.'
            if command == 'right':
                return 'Quay phải ngay.'
            if command == 'follow':
                return 'Tôi sẽ theo bạn.'
            if command == 'home':
                return 'Tôi sẽ trở về vị trí ban đầu.'
            if command == 'navigate':
                return 'Hãy chỉ cho tôi điểm đến.'

        if any(greet in lower for greet in ['xin chào', 'chào', 'hello', 'hi']):
            return 'Chào bạn! Tôi ở đây và sẵn sàng giúp.'
        if 'tên bạn' in lower or 'bạn tên' in lower:
            return 'Mình là trợ lý robot.'
        if 'bao nhiêu' in lower and 'pin' in lower:
            return 'Pin đang ở mức đủ dùng.'
        if lower.endswith('?'):
            return 'Đây là câu hỏi hay — tôi sẽ suy nghĩ về nó.'

        return f'Tôi nghe được: {text}'

    def _parse_command(self, text: str) -> Optional[str]:
        lower = text.lower()
        if any(word in lower for word in ['dừng', 'stop', 'ngừng', 'đứng lại', 'dừng lại']):
            return 'stop'
        if any(word in lower for word in ['tiến', 'đi tới', 'đi về', 'tiến về', 'go forward']):
            return 'forward'
        if any(word in lower for word in ['lùi', 'quay sau', 'backward', 'go back']):
            return 'backward'
        if any(word in lower for word in ['trái', 'quay trái', 'left']):
            return 'left'
        if any(word in lower for word in ['phải', 'quay phải', 'right']):
            return 'right'
        if any(word in lower for word in ['theo', 'follow']):
            return 'follow'
        if any(word in lower for word in ['về nhà', 'trở về', 'home']):
            return 'home'
        if any(word in lower for word in ['đi đến', 'đến', 'navigate', 'go to', 'move to']):
            return 'navigate'
        if re.search(r'^(đi|lái|hướng)', lower):
            return 'navigate'
        return None

    def _speak(self, text: str) -> None:
        try:
            self._tts_engine.say(text)
            self._tts_engine.runAndWait()
        except Exception as exc:
            self.get_logger().error(f'TTS failed to speak: {exc}')

    def destroy_node(self) -> None:
        self.get_logger().info('Shutting down DialogueTTS node')
        self._executor.shutdown(wait=False)
        super().destroy_node()


def main(args=None) -> None:
    rclpy.init(args=args)
    node = None
    try:
        node = DialogueTTSNode()
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        if node is not None:
            node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
