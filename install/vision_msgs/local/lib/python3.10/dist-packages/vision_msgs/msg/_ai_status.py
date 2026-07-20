# generated from rosidl_generator_py/resource/_idl.py.em
# with input from vision_msgs:msg/AIStatus.idl
# generated code does not contain a copyright notice


# Import statements for member types

import builtins  # noqa: E402, I100

import math  # noqa: E402, I100

import rosidl_parser.definition  # noqa: E402, I100


class Metaclass_AIStatus(type):
    """Metaclass of message 'AIStatus'."""

    _CREATE_ROS_MESSAGE = None
    _CONVERT_FROM_PY = None
    _CONVERT_TO_PY = None
    _DESTROY_ROS_MESSAGE = None
    _TYPE_SUPPORT = None

    __constants = {
    }

    @classmethod
    def __import_type_support__(cls):
        try:
            from rosidl_generator_py import import_type_support
            module = import_type_support('vision_msgs')
        except ImportError:
            import logging
            import traceback
            logger = logging.getLogger(
                'vision_msgs.msg.AIStatus')
            logger.debug(
                'Failed to import needed modules for type support:\n' +
                traceback.format_exc())
        else:
            cls._CREATE_ROS_MESSAGE = module.create_ros_message_msg__msg__ai_status
            cls._CONVERT_FROM_PY = module.convert_from_py_msg__msg__ai_status
            cls._CONVERT_TO_PY = module.convert_to_py_msg__msg__ai_status
            cls._TYPE_SUPPORT = module.type_support_msg__msg__ai_status
            cls._DESTROY_ROS_MESSAGE = module.destroy_ros_message_msg__msg__ai_status

            from std_msgs.msg import Header
            if Header.__class__._TYPE_SUPPORT is None:
                Header.__class__.__import_type_support__()

    @classmethod
    def __prepare__(cls, name, bases, **kwargs):
        # list constant names here so that they appear in the help text of
        # the message class under "Data and other attributes defined here:"
        # as well as populate each message instance
        return {
        }


class AIStatus(metaclass=Metaclass_AIStatus):
    """Message class 'AIStatus'."""

    __slots__ = [
        '_header',
        '_fps',
        '_inference_time_ms',
        '_cpu_usage',
        '_memory_mb',
        '_model_loaded',
        '_num_detections',
        '_status',
    ]

    _fields_and_field_types = {
        'header': 'std_msgs/Header',
        'fps': 'float',
        'inference_time_ms': 'float',
        'cpu_usage': 'float',
        'memory_mb': 'float',
        'model_loaded': 'boolean',
        'num_detections': 'int32',
        'status': 'string',
    }

    SLOT_TYPES = (
        rosidl_parser.definition.NamespacedType(['std_msgs', 'msg'], 'Header'),  # noqa: E501
        rosidl_parser.definition.BasicType('float'),  # noqa: E501
        rosidl_parser.definition.BasicType('float'),  # noqa: E501
        rosidl_parser.definition.BasicType('float'),  # noqa: E501
        rosidl_parser.definition.BasicType('float'),  # noqa: E501
        rosidl_parser.definition.BasicType('boolean'),  # noqa: E501
        rosidl_parser.definition.BasicType('int32'),  # noqa: E501
        rosidl_parser.definition.UnboundedString(),  # noqa: E501
    )

    def __init__(self, **kwargs):
        assert all('_' + key in self.__slots__ for key in kwargs.keys()), \
            'Invalid arguments passed to constructor: %s' % \
            ', '.join(sorted(k for k in kwargs.keys() if '_' + k not in self.__slots__))
        from std_msgs.msg import Header
        self.header = kwargs.get('header', Header())
        self.fps = kwargs.get('fps', float())
        self.inference_time_ms = kwargs.get('inference_time_ms', float())
        self.cpu_usage = kwargs.get('cpu_usage', float())
        self.memory_mb = kwargs.get('memory_mb', float())
        self.model_loaded = kwargs.get('model_loaded', bool())
        self.num_detections = kwargs.get('num_detections', int())
        self.status = kwargs.get('status', str())

    def __repr__(self):
        typename = self.__class__.__module__.split('.')
        typename.pop()
        typename.append(self.__class__.__name__)
        args = []
        for s, t in zip(self.__slots__, self.SLOT_TYPES):
            field = getattr(self, s)
            fieldstr = repr(field)
            # We use Python array type for fields that can be directly stored
            # in them, and "normal" sequences for everything else.  If it is
            # a type that we store in an array, strip off the 'array' portion.
            if (
                isinstance(t, rosidl_parser.definition.AbstractSequence) and
                isinstance(t.value_type, rosidl_parser.definition.BasicType) and
                t.value_type.typename in ['float', 'double', 'int8', 'uint8', 'int16', 'uint16', 'int32', 'uint32', 'int64', 'uint64']
            ):
                if len(field) == 0:
                    fieldstr = '[]'
                else:
                    assert fieldstr.startswith('array(')
                    prefix = "array('X', "
                    suffix = ')'
                    fieldstr = fieldstr[len(prefix):-len(suffix)]
            args.append(s[1:] + '=' + fieldstr)
        return '%s(%s)' % ('.'.join(typename), ', '.join(args))

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return False
        if self.header != other.header:
            return False
        if self.fps != other.fps:
            return False
        if self.inference_time_ms != other.inference_time_ms:
            return False
        if self.cpu_usage != other.cpu_usage:
            return False
        if self.memory_mb != other.memory_mb:
            return False
        if self.model_loaded != other.model_loaded:
            return False
        if self.num_detections != other.num_detections:
            return False
        if self.status != other.status:
            return False
        return True

    @classmethod
    def get_fields_and_field_types(cls):
        from copy import copy
        return copy(cls._fields_and_field_types)

    @builtins.property
    def header(self):
        """Message field 'header'."""
        return self._header

    @header.setter
    def header(self, value):
        if __debug__:
            from std_msgs.msg import Header
            assert \
                isinstance(value, Header), \
                "The 'header' field must be a sub message of type 'Header'"
        self._header = value

    @builtins.property
    def fps(self):
        """Message field 'fps'."""
        return self._fps

    @fps.setter
    def fps(self, value):
        if __debug__:
            assert \
                isinstance(value, float), \
                "The 'fps' field must be of type 'float'"
            assert not (value < -3.402823466e+38 or value > 3.402823466e+38) or math.isinf(value), \
                "The 'fps' field must be a float in [-3.402823466e+38, 3.402823466e+38]"
        self._fps = value

    @builtins.property
    def inference_time_ms(self):
        """Message field 'inference_time_ms'."""
        return self._inference_time_ms

    @inference_time_ms.setter
    def inference_time_ms(self, value):
        if __debug__:
            assert \
                isinstance(value, float), \
                "The 'inference_time_ms' field must be of type 'float'"
            assert not (value < -3.402823466e+38 or value > 3.402823466e+38) or math.isinf(value), \
                "The 'inference_time_ms' field must be a float in [-3.402823466e+38, 3.402823466e+38]"
        self._inference_time_ms = value

    @builtins.property
    def cpu_usage(self):
        """Message field 'cpu_usage'."""
        return self._cpu_usage

    @cpu_usage.setter
    def cpu_usage(self, value):
        if __debug__:
            assert \
                isinstance(value, float), \
                "The 'cpu_usage' field must be of type 'float'"
            assert not (value < -3.402823466e+38 or value > 3.402823466e+38) or math.isinf(value), \
                "The 'cpu_usage' field must be a float in [-3.402823466e+38, 3.402823466e+38]"
        self._cpu_usage = value

    @builtins.property
    def memory_mb(self):
        """Message field 'memory_mb'."""
        return self._memory_mb

    @memory_mb.setter
    def memory_mb(self, value):
        if __debug__:
            assert \
                isinstance(value, float), \
                "The 'memory_mb' field must be of type 'float'"
            assert not (value < -3.402823466e+38 or value > 3.402823466e+38) or math.isinf(value), \
                "The 'memory_mb' field must be a float in [-3.402823466e+38, 3.402823466e+38]"
        self._memory_mb = value

    @builtins.property
    def model_loaded(self):
        """Message field 'model_loaded'."""
        return self._model_loaded

    @model_loaded.setter
    def model_loaded(self, value):
        if __debug__:
            assert \
                isinstance(value, bool), \
                "The 'model_loaded' field must be of type 'bool'"
        self._model_loaded = value

    @builtins.property
    def num_detections(self):
        """Message field 'num_detections'."""
        return self._num_detections

    @num_detections.setter
    def num_detections(self, value):
        if __debug__:
            assert \
                isinstance(value, int), \
                "The 'num_detections' field must be of type 'int'"
            assert value >= -2147483648 and value < 2147483648, \
                "The 'num_detections' field must be an integer in [-2147483648, 2147483647]"
        self._num_detections = value

    @builtins.property
    def status(self):
        """Message field 'status'."""
        return self._status

    @status.setter
    def status(self, value):
        if __debug__:
            assert \
                isinstance(value, str), \
                "The 'status' field must be of type 'str'"
        self._status = value
