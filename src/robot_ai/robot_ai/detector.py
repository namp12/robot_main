"""
detector.py - YOLO object detection engine.

Handles pre-processing, inference, and post-processing for YOLO models.
Works with both ONNX Runtime and Ultralytics backends.

This module is pure computation - no ROS2 dependencies.
Receives numpy frames, returns detection results as dictionaries.

Author: robot
License: Apache-2.0
"""

import time
from typing import List, Dict, Any, Optional, Tuple

import cv2
import numpy as np

from .model_loader import ModelLoader
from .config import AIConfig


class Detector:
    """
    YOLO object detector.

    Supports two backends:
      1. ONNX Runtime (preferred) - direct tensor I/O
      2. Ultralytics - high-level API

    Thread-safe for inference (model is read-only after loading).
    """

    def __init__(self, model_loader: ModelLoader, config: AIConfig) -> None:
        """
        Initialize detector.

        Args:
            model_loader: Loaded ModelLoader instance.
            config: AI configuration.
        """
        self._loader = model_loader
        self._config = config

    def detect(self, frame: np.ndarray) -> Dict[str, Any]:
        """
        Run object detection on a frame.

        Args:
            frame: BGR image as numpy array (H, W, 3).

        Returns:
            Dictionary with:
              - 'detections': list of detection dicts
              - 'inference_time_ms': float
              - 'image_width': int
              - 'image_height': int
        """
        if not self._loader.is_loaded:
            return {
                'detections': [],
                'inference_time_ms': 0.0,
                'image_width': frame.shape[1],
                'image_height': frame.shape[0],
            }

        start_time = time.time()

        # Choose backend
        if self._loader.backend == 'onnx':
            detections = self._detect_onnx(frame)
        elif self._loader.backend == 'ultralytics':
            detections = self._detect_ultralytics(frame)
        else:
            detections = []

        inference_time_ms = (time.time() - start_time) * 1000.0

        return {
            'detections': detections,
            'inference_time_ms': inference_time_ms,
            'image_width': frame.shape[1],
            'image_height': frame.shape[0],
        }

    def _detect_onnx(self, frame: np.ndarray) -> List[Dict[str, Any]]:
        """
        Run detection using ONNX Runtime backend.

        Steps:
          1. Letterbox resize to model input size
          2. Normalize and transpose to NCHW format
          3. Run inference
          4. Post-process output (extract boxes, NMS)
        """
        session = self._loader.get_session()
        input_name = self._loader.get_input_name()
        input_size = self._config.model_input_size

        orig_h, orig_w = frame.shape[:2]

        # ---- Pre-processing ----
        # Letterbox resize (maintain aspect ratio, pad with gray)
        input_blob, ratio, (pad_w, pad_h) = self._letterbox(
            frame, input_size, input_size
        )

        # Normalize: [0, 255] -> [0, 1]
        input_blob = input_blob.astype(np.float32) / 255.0

        # Transpose: HWC -> NCHW (batch=1)
        input_blob = np.transpose(input_blob, (2, 0, 1))
        input_blob = np.expand_dims(input_blob, axis=0)

        # ---- Inference ----
        outputs = session.run(None, {input_name: input_blob})
        output = outputs[0]  # Shape: (1, num_detections, 4+num_classes+num_masks)

        # ---- Post-processing ----
        detections = self._postprocess_onnx(
            output, orig_w, orig_h, ratio, pad_w, pad_h
        )

        return detections

    def _detect_ultralytics(self, frame: np.ndarray) -> List[Dict[str, Any]]:
        """
        Run detection using Ultralytics backend.

        Ultralytics handles pre/post-processing internally.
        """
        model = self._loader.get_ultralytics_model()

        results = model(
            frame,
            conf=self._config.confidence_threshold,
            iou=self._config.iou_threshold,
            verbose=False,
            device='cpu'
        )

        detections = []
        class_names = self._loader.class_names

        for result in results:
            if result.boxes is None:
                continue

            boxes = result.boxes
            for i in range(len(boxes)):
                box = boxes.xyxy[i].cpu().numpy().astype(int)
                x_min, y_min, x_max, y_max = box.tolist()
                conf = float(boxes.conf[i].cpu().numpy())
                cls_id = int(boxes.cls[i].cpu().numpy())

                cls_name = class_names[cls_id] if cls_id < len(class_names) else f'class_{cls_id}'

                detections.append({
                    'class_name': cls_name,
                    'class_id': cls_id,
                    'confidence': conf,
                    'bbox': [x_min, y_min, x_max, y_max],
                    'center': [
                        float(x_min + x_max) / 2.0,
                        float(y_min + y_max) / 2.0,
                    ],
                })

        return detections

    def _postprocess_onnx(
        self,
        output: np.ndarray,
        orig_w: int,
        orig_h: int,
        ratio: float,
        pad_w: float,
        pad_h: float
    ) -> List[Dict[str, Any]]:
        """
        Post-process ONNX output into detection dictionaries.

        YOLOv8/v11 output format: (1, 84, 8400)
          - 84 = 4 (bbox) + 80 (classes)
          - 8400 = number of candidate boxes

        Args:
            output: Raw model output array.
            orig_w: Original image width.
            orig_h: Original image height.
            ratio: Letterbox scaling ratio.
            pad_w: Horizontal padding from letterbox.
            pad_h: Vertical padding from letterbox.

        Returns:
            List of detection dictionaries.
        """
        # Handle both output shapes: (1, 84, 8400) and (1, 8400, 84)
        if output.ndim == 3:
            if output.shape[1] < output.shape[2]:
                # (1, 84, 8400) -> transpose to (8400, 84)
                output = output[0].T
            else:
                # (1, 8400, 84) -> squeeze to (8400, 84)
                output = output[0]

        # Split bbox and class scores
        boxes = output[:, :4]           # cx, cy, w, h
        scores = output[:, 4:]          # 80 class scores

        # Get best class per box
        class_ids = np.argmax(scores, axis=1)
        confidences = scores[np.arange(len(scores)), class_ids]

        # Filter by confidence threshold
        mask = confidences >= self._config.confidence_threshold
        boxes = boxes[mask]
        class_ids = class_ids[mask]
        confidences = confidences[mask]

        if len(boxes) == 0:
            return []

        # Convert cx,cy,w,h -> x1,y1,x2,y2
        x1 = boxes[:, 0] - boxes[:, 2] / 2
        y1 = boxes[:, 1] - boxes[:, 3] / 2
        x2 = boxes[:, 0] + boxes[:, 2] / 2
        y2 = boxes[:, 1] + boxes[:, 3] / 2

        # Remove letterbox padding and rescale to original image
        x1 = (x1 - pad_w) / ratio
        y1 = (y1 - pad_h) / ratio
        x2 = (x2 - pad_w) / ratio
        y2 = (y2 - pad_h) / ratio

        # Clip to image bounds
        x1 = np.clip(x1, 0, orig_w)
        y1 = np.clip(y1, 0, orig_h)
        x2 = np.clip(x2, 0, orig_w)
        y2 = np.clip(y2, 0, orig_h)

        # Non-Maximum Suppression
        indices = cv2.dnn.NMSBoxes(
            bboxes=[[float(x1[i]), float(y1[i]),
                      float(x2[i] - x1[i]), float(y2[i] - y1[i])]
                     for i in range(len(x1))],
            scores=[float(c) for c in confidences],
            score_threshold=self._config.confidence_threshold,
            nms_threshold=self._config.iou_threshold,
        )

        # Build detection list
        detections = []
        class_names = self._loader.class_names

        if len(indices) > 0:
            for idx in indices.flatten()[:self._config.max_detections]:
                cls_id = int(class_ids[idx])
                cls_name = class_names[cls_id] if cls_id < len(class_names) else f'class_{cls_id}'

                bx1, by1 = int(x1[idx]), int(y1[idx])
                bx2, by2 = int(x2[idx]), int(y2[idx])

                detections.append({
                    'class_name': cls_name,
                    'class_id': cls_id,
                    'confidence': float(confidences[idx]),
                    'bbox': [bx1, by1, bx2, by2],
                    'center': [
                        float(bx1 + bx2) / 2.0,
                        float(by1 + by2) / 2.0,
                    ],
                })

        return detections

    @staticmethod
    def _letterbox(
        img: np.ndarray,
        target_w: int,
        target_h: int,
        color: Tuple[int, int, int] = (114, 114, 114)
    ) -> Tuple[np.ndarray, float, Tuple[float, float]]:
        """
        Resize image with unchanged aspect ratio using padding.

        Args:
            img: Input BGR image.
            target_w: Target width.
            target_h: Target height.
            color: Padding color.

        Returns:
            Tuple of (resized_image, scale_ratio, (pad_w, pad_h))
        """
        shape = img.shape[:2]  # [h, w]
        h, w = shape[0], shape[1]

        # Scale ratio (new / old)
        r = min(target_w / w, target_h / h)

        # Compute padding
        new_unpad_w = int(round(w * r))
        new_unpad_h = int(round(h * r))
        pad_w = (target_w - new_unpad_w) / 2
        pad_h = (target_h - new_unpad_h) / 2

        # Resize
        if (w, h) != (new_unpad_w, new_unpad_h):
            img = cv2.resize(
                img, (new_unpad_w, new_unpad_h),
                interpolation=cv2.INTER_LINEAR
            )

        # Add padding
        top, bottom = int(round(pad_h - 0.1)), int(round(pad_h + 0.1))
        left, right = int(round(pad_w - 0.1)), int(round(pad_w + 0.1))
        img = cv2.copyMakeBorder(
            img, top, bottom, left, right,
            cv2.BORDER_CONSTANT, value=color
        )

        return img, r, (pad_w, pad_h)
