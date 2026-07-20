"""
model_loader.py - ONNX model loading and management.

Handles loading YOLOv11n ONNX model into ONNX Runtime session.
Manages model lifecycle: load, validate, get metadata.

Uses ONNX Runtime for efficient inference on CPU (RPi4).
Falls back to PyTorch/ultralytics only if ONNX model is not available.

Author: robot
License: Apache-2.0
"""

import os
import time
import logging
from typing import Optional, List, Tuple

import numpy as np

logger = logging.getLogger(__name__)


class ModelLoader:
    """
    Loads and manages YOLO ONNX model via ONNX Runtime.

    Supports:
      - ONNX Runtime (preferred, lower RAM, faster on CPU)
      - Ultralytics PyTorch fallback (if .pt file provided)

    Thread-safe for inference after loading.
    """

    def __init__(
        self,
        model_path: str,
        enable_gpu: bool = False,
        num_threads: int = 1
    ) -> None:
        """
        Initialize model loader.

        Args:
            model_path: Path to .onnx or .pt model file.
            enable_gpu: Whether to try GPU (not available on RPi4).
            num_threads: Number of intra-op threads for ONNX Runtime.
        """
        self._model_path = model_path
        self._enable_gpu = enable_gpu
        self._num_threads = num_threads

        self._session = None          # ONNX Runtime InferenceSession
        self._class_names: List[str] = []
        self._input_name: str = ''
        self._input_shape: Tuple[int, ...] = ()
        self._loaded: bool = False
        self._backend: str = ''       # 'onnx' or 'ultralytics'
        self._ultralytics_model = None  # Fallback YOLO model

    @property
    def is_loaded(self) -> bool:
        """Whether model is loaded successfully."""
        return self._loaded

    @property
    def class_names(self) -> List[str]:
        """List of class names from the model."""
        return self._class_names

    @property
    def input_shape(self) -> Tuple[int, ...]:
        """Model input tensor shape."""
        return self._input_shape

    @property
    def backend(self) -> str:
        """Backend being used: 'onnx' or 'ultralytics'."""
        return self._backend

    def load(self) -> bool:
        """
        Load the model from disk.

        Tries ONNX Runtime first (if .onnx file).
        Falls back to ultralytics (if .pt file or onnxruntime unavailable).

        Returns:
            bool: True if model loaded successfully.
        """
        if not self._model_path:
            logger.error('Model path is empty')
            return False

        if not os.path.isfile(self._model_path):
            logger.error(f'Model file not found: {self._model_path}')
            return False

        ext = os.path.splitext(self._model_path)[1].lower()

        if ext == '.onnx':
            return self._load_onnx()
        elif ext == '.pt':
            return self._load_ultralytics()
        else:
            logger.error(f'Unsupported model format: {ext}. Use .onnx or .pt')
            return False

    def _load_onnx(self) -> bool:
        """
        Load model using ONNX Runtime.

        ONNX Runtime is preferred because:
          - Lower RAM usage (~150MB vs ~400MB for PyTorch)
          - Faster inference on CPU
          - No PyTorch dependency
        """
        try:
            import onnxruntime as ort
        except ImportError:
            logger.warning(
                'onnxruntime not installed. '
                'Install with: pip3 install onnxruntime\n'
                'Falling back to ultralytics...'
            )
            return self._load_ultralytics()

        try:
            logger.info(f'Loading ONNX model: {self._model_path}')
            start = time.time()

            # Configure ONNX Runtime session
            sess_options = ort.SessionOptions()
            sess_options.intra_op_num_threads = self._num_threads
            sess_options.inter_op_num_threads = 1
            sess_options.graph_optimization_level = (
                ort.GraphOptimizationLevel.ORT_ENABLE_ALL
            )
            # Reduce memory allocation
            sess_options.enable_mem_pattern = True

            # Select execution provider
            if self._enable_gpu and 'CUDAExecutionProvider' in ort.get_available_providers():
                providers = ['CUDAExecutionProvider', 'CPUExecutionProvider']
                logger.info('Using CUDA GPU provider')
            else:
                providers = ['CPUExecutionProvider']
                logger.info('Using CPU provider')

            self._session = ort.InferenceSession(
                self._model_path,
                sess_options=sess_options,
                providers=providers
            )

            # Get input metadata
            input_info = self._session.get_inputs()[0]
            self._input_name = input_info.name
            self._input_shape = tuple(input_info.shape)
            logger.info(f'Model input: {self._input_name} shape={self._input_shape}')

            # Get class names from model metadata
            self._class_names = self._extract_onnx_class_names()

            load_time = (time.time() - start) * 1000
            self._loaded = True
            self._backend = 'onnx'

            logger.info(
                f'ONNX model loaded in {load_time:.0f}ms: '
                f'{len(self._class_names)} classes, '
                f'input={self._input_shape}'
            )
            return True

        except Exception as exc:
            logger.error(f'Failed to load ONNX model: {exc}')
            self._session = None
            return False

    def _extract_onnx_class_names(self) -> List[str]:
        """
        Extract class names from ONNX model metadata.

        YOLOv8/v11 ONNX models store class names in metadata
        under the 'names' key as a dict string.

        Returns:
            List of class name strings.
        """
        try:
            metadata = self._session.get_modelmeta().custom_metadata_map

            if 'names' in metadata:
                # Parse names dict: "0: person, 1: bicycle, ..."
                import ast
                names_str = metadata['names']
                names_dict = ast.literal_eval(names_str)
                max_id = max(int(k) for k in names_dict.keys())
                return [names_dict.get(str(i), f'class_{i}') for i in range(max_id + 1)]
        except Exception:
            pass

        # Fallback: COCO 80 classes
        return self._get_coco_names()

    def _load_ultralytics(self) -> bool:
        """
        Fallback: load model using ultralytics (PyTorch).

        Only used when ONNX Runtime is not available or .pt file is provided.
        Uses more RAM (~400MB) but works without conversion.
        """
        try:
            from ultralytics import YOLO
        except ImportError:
            logger.error(
                'Neither onnxruntime nor ultralytics is installed.\n'
                'Install one:\n'
                '  pip3 install onnxruntime          (preferred, lower RAM)\n'
                '  pip3 install ultralytics           (PyTorch, higher RAM)'
            )
            return False

        try:
            logger.info(f'Loading ultralytics model: {self._model_path}')
            start = time.time()

            self._ultralytics_model = YOLO(self._model_path)
            self._class_names = list(self._ultralytics_model.names.values())

            load_time = (time.time() - start) * 1000
            self._loaded = True
            self._backend = 'ultralytics'

            logger.info(
                f'Ultralytics model loaded in {load_time:.0f}ms: '
                f'{len(self._class_names)} classes'
            )
            return True

        except Exception as exc:
            logger.error(f'Failed to load ultralytics model: {exc}')
            self._ultralytics_model = None
            return False

    def get_session(self):
        """Get the ONNX Runtime session (None if using ultralytics)."""
        return self._session

    def get_input_name(self) -> str:
        """Get the input tensor name for ONNX Runtime."""
        return self._input_name

    def get_ultralytics_model(self):
        """Get the ultralytics YOLO model (None if using ONNX)."""
        return self._ultralytics_model

    @staticmethod
    def _get_coco_names() -> List[str]:
        """Return standard COCO 80 class names."""
        return [
            'person', 'bicycle', 'car', 'motorcycle', 'airplane', 'bus',
            'train', 'truck', 'boat', 'traffic light', 'fire hydrant',
            'stop sign', 'parking meter', 'bench', 'bird', 'cat', 'dog',
            'horse', 'sheep', 'cow', 'elephant', 'bear', 'zebra', 'giraffe',
            'backpack', 'umbrella', 'handbag', 'tie', 'suitcase', 'frisbee',
            'skis', 'snowboard', 'sports ball', 'kite', 'baseball bat',
            'baseball glove', 'skateboard', 'surfboard', 'tennis racket',
            'bottle', 'wine glass', 'cup', 'fork', 'knife', 'spoon', 'bowl',
            'banana', 'apple', 'sandwich', 'orange', 'broccoli', 'carrot',
            'hot dog', 'pizza', 'donut', 'cake', 'chair', 'couch',
            'potted plant', 'bed', 'dining table', 'toilet', 'tv', 'laptop',
            'mouse', 'remote', 'keyboard', 'cell phone', 'microwave',
            'oven', 'toaster', 'sink', 'refrigerator', 'book', 'clock',
            'vase', 'scissors', 'teddy bear', 'hair drier', 'toothbrush'
        ]

    def unload(self) -> None:
        """Release model resources."""
        self._session = None
        self._ultralytics_model = None
        self._loaded = False
        self._class_names = []
        logger.info('Model unloaded')
