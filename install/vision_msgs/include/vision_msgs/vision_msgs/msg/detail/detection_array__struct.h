// generated from rosidl_generator_c/resource/idl__struct.h.em
// with input from vision_msgs:msg/DetectionArray.idl
// generated code does not contain a copyright notice

#ifndef VISION_MSGS__MSG__DETAIL__DETECTION_ARRAY__STRUCT_H_
#define VISION_MSGS__MSG__DETAIL__DETECTION_ARRAY__STRUCT_H_

#ifdef __cplusplus
extern "C"
{
#endif

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>


// Constants defined in the message

// Include directives for member types
// Member 'header'
#include "std_msgs/msg/detail/header__struct.h"
// Member 'detections'
#include "vision_msgs/msg/detail/detection__struct.h"

/// Struct defined in msg/DetectionArray in the package vision_msgs.
/**
  * Array of object detections from a single frame
  *
  * Published by vision_ai_node on /vision/detections.
  * Contains all detected objects plus metadata about the frame.
 */
typedef struct vision_msgs__msg__DetectionArray
{
  /// Header with timestamp and frame_id
  std_msgs__msg__Header header;
  /// List of individual detections
  vision_msgs__msg__Detection__Sequence detections;
  /// Original image dimensions
  int32_t image_width;
  int32_t image_height;
  /// Inference time in milliseconds
  float inference_time_ms;
} vision_msgs__msg__DetectionArray;

// Struct for a sequence of vision_msgs__msg__DetectionArray.
typedef struct vision_msgs__msg__DetectionArray__Sequence
{
  vision_msgs__msg__DetectionArray * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} vision_msgs__msg__DetectionArray__Sequence;

#ifdef __cplusplus
}
#endif

#endif  // VISION_MSGS__MSG__DETAIL__DETECTION_ARRAY__STRUCT_H_
