// generated from rosidl_generator_c/resource/idl__struct.h.em
// with input from vision_msgs:msg/Detection.idl
// generated code does not contain a copyright notice

#ifndef VISION_MSGS__MSG__DETAIL__DETECTION__STRUCT_H_
#define VISION_MSGS__MSG__DETAIL__DETECTION__STRUCT_H_

#ifdef __cplusplus
extern "C"
{
#endif

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>


// Constants defined in the message

// Include directives for member types
// Member 'class_name'
#include "rosidl_runtime_c/string.h"

/// Struct defined in msg/Detection in the package vision_msgs.
/**
  * Single object detection result
  *
  * Published by vision_ai_node after YOLO inference.
  * Each detection contains the class name, confidence score,
  * and bounding box in pixel coordinates.
 */
typedef struct vision_msgs__msg__Detection
{
  /// Class label from YOLO model (e.g. "person", "car", "bottle")
  rosidl_runtime_c__String class_name;
  /// Class ID from YOLO model (integer index)
  int32_t class_id;
  /// Detection confidence
  float confidence;
  /// Bounding box in pixel coordinates (top-left origin)
  /// Left edge
  int32_t x_min;
  /// Top edge
  int32_t y_min;
  /// Right edge
  int32_t x_max;
  /// Bottom edge
  int32_t y_max;
  /// Bounding box center point
  float center_x;
  float center_y;
} vision_msgs__msg__Detection;

// Struct for a sequence of vision_msgs__msg__Detection.
typedef struct vision_msgs__msg__Detection__Sequence
{
  vision_msgs__msg__Detection * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} vision_msgs__msg__Detection__Sequence;

#ifdef __cplusplus
}
#endif

#endif  // VISION_MSGS__MSG__DETAIL__DETECTION__STRUCT_H_
