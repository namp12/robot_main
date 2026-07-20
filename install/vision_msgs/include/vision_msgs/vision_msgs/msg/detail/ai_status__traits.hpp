// generated from rosidl_generator_cpp/resource/idl__traits.hpp.em
// with input from vision_msgs:msg/AIStatus.idl
// generated code does not contain a copyright notice

#ifndef VISION_MSGS__MSG__DETAIL__AI_STATUS__TRAITS_HPP_
#define VISION_MSGS__MSG__DETAIL__AI_STATUS__TRAITS_HPP_

#include <stdint.h>

#include <sstream>
#include <string>
#include <type_traits>

#include "vision_msgs/msg/detail/ai_status__struct.hpp"
#include "rosidl_runtime_cpp/traits.hpp"

// Include directives for member types
// Member 'header'
#include "std_msgs/msg/detail/header__traits.hpp"

namespace vision_msgs
{

namespace msg
{

inline void to_flow_style_yaml(
  const AIStatus & msg,
  std::ostream & out)
{
  out << "{";
  // member: header
  {
    out << "header: ";
    to_flow_style_yaml(msg.header, out);
    out << ", ";
  }

  // member: fps
  {
    out << "fps: ";
    rosidl_generator_traits::value_to_yaml(msg.fps, out);
    out << ", ";
  }

  // member: inference_time_ms
  {
    out << "inference_time_ms: ";
    rosidl_generator_traits::value_to_yaml(msg.inference_time_ms, out);
    out << ", ";
  }

  // member: cpu_usage
  {
    out << "cpu_usage: ";
    rosidl_generator_traits::value_to_yaml(msg.cpu_usage, out);
    out << ", ";
  }

  // member: memory_mb
  {
    out << "memory_mb: ";
    rosidl_generator_traits::value_to_yaml(msg.memory_mb, out);
    out << ", ";
  }

  // member: model_loaded
  {
    out << "model_loaded: ";
    rosidl_generator_traits::value_to_yaml(msg.model_loaded, out);
    out << ", ";
  }

  // member: num_detections
  {
    out << "num_detections: ";
    rosidl_generator_traits::value_to_yaml(msg.num_detections, out);
    out << ", ";
  }

  // member: status
  {
    out << "status: ";
    rosidl_generator_traits::value_to_yaml(msg.status, out);
  }
  out << "}";
}  // NOLINT(readability/fn_size)

inline void to_block_style_yaml(
  const AIStatus & msg,
  std::ostream & out, size_t indentation = 0)
{
  // member: header
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "header:\n";
    to_block_style_yaml(msg.header, out, indentation + 2);
  }

  // member: fps
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "fps: ";
    rosidl_generator_traits::value_to_yaml(msg.fps, out);
    out << "\n";
  }

  // member: inference_time_ms
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "inference_time_ms: ";
    rosidl_generator_traits::value_to_yaml(msg.inference_time_ms, out);
    out << "\n";
  }

  // member: cpu_usage
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "cpu_usage: ";
    rosidl_generator_traits::value_to_yaml(msg.cpu_usage, out);
    out << "\n";
  }

  // member: memory_mb
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "memory_mb: ";
    rosidl_generator_traits::value_to_yaml(msg.memory_mb, out);
    out << "\n";
  }

  // member: model_loaded
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "model_loaded: ";
    rosidl_generator_traits::value_to_yaml(msg.model_loaded, out);
    out << "\n";
  }

  // member: num_detections
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "num_detections: ";
    rosidl_generator_traits::value_to_yaml(msg.num_detections, out);
    out << "\n";
  }

  // member: status
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "status: ";
    rosidl_generator_traits::value_to_yaml(msg.status, out);
    out << "\n";
  }
}  // NOLINT(readability/fn_size)

inline std::string to_yaml(const AIStatus & msg, bool use_flow_style = false)
{
  std::ostringstream out;
  if (use_flow_style) {
    to_flow_style_yaml(msg, out);
  } else {
    to_block_style_yaml(msg, out);
  }
  return out.str();
}

}  // namespace msg

}  // namespace vision_msgs

namespace rosidl_generator_traits
{

[[deprecated("use vision_msgs::msg::to_block_style_yaml() instead")]]
inline void to_yaml(
  const vision_msgs::msg::AIStatus & msg,
  std::ostream & out, size_t indentation = 0)
{
  vision_msgs::msg::to_block_style_yaml(msg, out, indentation);
}

[[deprecated("use vision_msgs::msg::to_yaml() instead")]]
inline std::string to_yaml(const vision_msgs::msg::AIStatus & msg)
{
  return vision_msgs::msg::to_yaml(msg);
}

template<>
inline const char * data_type<vision_msgs::msg::AIStatus>()
{
  return "vision_msgs::msg::AIStatus";
}

template<>
inline const char * name<vision_msgs::msg::AIStatus>()
{
  return "vision_msgs/msg/AIStatus";
}

template<>
struct has_fixed_size<vision_msgs::msg::AIStatus>
  : std::integral_constant<bool, false> {};

template<>
struct has_bounded_size<vision_msgs::msg::AIStatus>
  : std::integral_constant<bool, false> {};

template<>
struct is_message<vision_msgs::msg::AIStatus>
  : std::true_type {};

}  // namespace rosidl_generator_traits

#endif  // VISION_MSGS__MSG__DETAIL__AI_STATUS__TRAITS_HPP_
