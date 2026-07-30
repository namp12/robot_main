#!/usr/bin/env python3
"""
dialogue_tts_node.py

Simple ROS2 node that subscribes to `/speech/text`, generates a reply
via OpenAI (if configured) or a rule-based fallback, publishes the
response on `/dialogue/response` and speaks it using `pyttsx3`.

This node is intentionally lightweight and safe-fallbacking so it can
run on edge devices without network.
"""

import os
import threading
import traceback
from typing import Optional

import rclpy
from rclpy.node import Node
from std_msgs.msg import String


class DialogueTTSNode(Node):
    def __init__(self) -> None:
        super().__init__('dialogue_tts_node')

        # Parameters
        self.declare_parameter('openai_enabled', False)
        self.declare_parameter('openai_model', 'gpt-3.5-turbo')

        self._openai_enabled = self.get_parameter('openai_enabled').value
        self._openai_model = self.get_parameter('openai_model').value

        # Publisher for textual responses
        self._pub = self.create_publisher(String, '/dialogue/response', 10)

        # Subscriber to ASR text
        self._sub = self.create_subscription(
            String, '/speech/text', self._on_speech_text, 10
        )

        # Try to import optional backends
        self._openai = None
        self._tts = None
        try:
            import pyttsx3
            self._tts = pyttsx3.init()
        except Exception:
            self.get_logger().warning('pyttsx3 not available; TTS disabled')

        if self._openai_enabled:
            try:
                import openai
                self._openai = openai
                # If API key provided via env, set it
                key = os.environ.get('OPENAI_API_KEY')
                if key:
                    self._openai.api_key = key
            except Exception:
                self.get_logger().warning('openai package not available; GPT disabled')
                self._openai = None

        self.get_logger().info('DialogueTTS node started')

    def _on_speech_text(self, msg: String) -> None:
        text = msg.data.strip()
        if not text:
            return

        self.get_logger().info(f'Received text: {text}')

        # Generate response (may block briefly) in worker thread
        thread = threading.Thread(target=self._handle_query, args=(text,), daemon=True)
        thread.start()

    def _handle_query(self, text: str) -> None:
        try:
            resp = self._generate_response(text)
            if resp is None:
                resp = 'Xin lỗi, tôi chưa trả lời được.'

            # Publish textual response
            out = String()
            out.data = resp
            self._pub.publish(out)

            # Speak it (non-blocking to ROS main thread)
            if self._tts is not None:
                try:
                    # run TTS in a short-lived thread to avoid blocking
                    t = threading.Thread(target=self._speak, args=(resp,), daemon=True)
                    t.start()
                except Exception:
                    self.get_logger().error('Failed to start TTS thread')

        except Exception:
            self.get_logger().error(f'Error handling query:\n{traceback.format_exc()}')

    def _generate_response(self, text: str) -> Optional[str]:
        """Generate textual response using OpenAI if available, else fallback."""
        # Use OpenAI chat API if configured
        if self._openai is not None and os.environ.get('OPENAI_API_KEY'):
            try:
                # Prefer ChatCompletion interface if available
                if hasattr(self._openai, 'ChatCompletion'):
                    completion = self._openai.ChatCompletion.create(
                        model=self._openai_model,
                        messages=[{"role": "user", "content": text}],
                        max_tokens=256,
                    )
                    choice = completion.choices[0]
                    return choice.message.content.strip()

                # Fallback older completion
                elif hasattr(self._openai, 'Completion'):
                    completion = self._openai.Completion.create(
                        model=self._openai_model,
                        prompt=text,
                        max_tokens=256,
                    )
                    return completion.choices[0].text.strip()

            except Exception:
                self.get_logger().warning('OpenAI request failed, falling back')

        # Simple rule-based fallback for offline use
        # Echo + simple heuristics
        lower = text.lower()
        if any(g in lower for g in ['xin chào', 'chào', 'hello', 'hi']):
            return 'Chào bạn! Tôi có thể giúp gì hôm nay?'
        if 'tên' in lower and ('bạn' in lower or 'của bạn' in lower):
            return 'Mình là trợ lý robot.'
        if lower.endswith('?'):
            return 'Đó là câu hỏi hay — tôi sẽ suy nghĩ về nó.'

        # Default: echo
        return f'Tôi nghe được: {text}'

    def _speak(self, text: str) -> None:
        try:
            # pyttsx3 may be blocking; run here in a separate thread
            self._tts.say(text)
            self._tts.runAndWait()
        except Exception:
            self.get_logger().error('TTS failed to speak')


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
            node.get_logger().info('Shutting down DialogueTTS node')
            node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
