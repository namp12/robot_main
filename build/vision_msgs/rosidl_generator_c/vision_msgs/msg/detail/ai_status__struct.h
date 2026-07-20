// generated from rosidl_generator_c/resource/idl__struct.h.em
// with input from vision_msgs:msg/AIStatus.idl
// generated code does not contain a copyright notice

#ifndef VISION_MSGS__MSG__DETAIL__AI_STATUS__STRUCT_H_
#define VISION_MSGS__MSG__DETAIL__AI_STATUS__STRUCT_H_

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
// Member 'status'
#include "rosidl_runtime_c/string.h"

/// Struct defined in msg/AIStatus in the package vision_msgs.
/**
  * AI Vision node status and performance metrics
  *
  * Published periodically by robot_ai node for monitoring.
 */
typedef struct vision_msgs__msg__AIStatus
{
  /// Header with timestamp
  std_msgs__msg__Header header;
  /// Current inference FPS (actual frames processed per second)
  float fps;
  /// Last inference time in milliseconds
  float inference_time_ms;
  /// CPU usage percentage
  float cpu_usage;
  /// RAM usage in megabytes
  float memory_mb;
  /// Whether model is loaded and ready
  bool model_loaded;
  /// Number of detections in last frame
  int32_t num_detections;
  /// Current status: "Running", "Idle", "Error"
  rosidl_runtime_c__String status;
} vision_msgs__msg__AIStatus;

// Struct for a sequence of vision_msgs__msg__AIStatus.
typedef struct vision_msgs__msg__AIStatus__Sequence
{
  vision_msgs__msg__AIStatus * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} vision_msgs__msg__AIStatus__Sequence;

#ifdef __cplusplus
}
#endif

#endif  // VISION_MSGS__MSG__DETAIL__AI_STATUS__STRUCT_H_
