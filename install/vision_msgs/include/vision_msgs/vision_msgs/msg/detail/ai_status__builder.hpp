// generated from rosidl_generator_cpp/resource/idl__builder.hpp.em
// with input from vision_msgs:msg/AIStatus.idl
// generated code does not contain a copyright notice

#ifndef VISION_MSGS__MSG__DETAIL__AI_STATUS__BUILDER_HPP_
#define VISION_MSGS__MSG__DETAIL__AI_STATUS__BUILDER_HPP_

#include <algorithm>
#include <utility>

#include "vision_msgs/msg/detail/ai_status__struct.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


namespace vision_msgs
{

namespace msg
{

namespace builder
{

class Init_AIStatus_status
{
public:
  explicit Init_AIStatus_status(::vision_msgs::msg::AIStatus & msg)
  : msg_(msg)
  {}
  ::vision_msgs::msg::AIStatus status(::vision_msgs::msg::AIStatus::_status_type arg)
  {
    msg_.status = std::move(arg);
    return std::move(msg_);
  }

private:
  ::vision_msgs::msg::AIStatus msg_;
};

class Init_AIStatus_num_detections
{
public:
  explicit Init_AIStatus_num_detections(::vision_msgs::msg::AIStatus & msg)
  : msg_(msg)
  {}
  Init_AIStatus_status num_detections(::vision_msgs::msg::AIStatus::_num_detections_type arg)
  {
    msg_.num_detections = std::move(arg);
    return Init_AIStatus_status(msg_);
  }

private:
  ::vision_msgs::msg::AIStatus msg_;
};

class Init_AIStatus_model_loaded
{
public:
  explicit Init_AIStatus_model_loaded(::vision_msgs::msg::AIStatus & msg)
  : msg_(msg)
  {}
  Init_AIStatus_num_detections model_loaded(::vision_msgs::msg::AIStatus::_model_loaded_type arg)
  {
    msg_.model_loaded = std::move(arg);
    return Init_AIStatus_num_detections(msg_);
  }

private:
  ::vision_msgs::msg::AIStatus msg_;
};

class Init_AIStatus_memory_mb
{
public:
  explicit Init_AIStatus_memory_mb(::vision_msgs::msg::AIStatus & msg)
  : msg_(msg)
  {}
  Init_AIStatus_model_loaded memory_mb(::vision_msgs::msg::AIStatus::_memory_mb_type arg)
  {
    msg_.memory_mb = std::move(arg);
    return Init_AIStatus_model_loaded(msg_);
  }

private:
  ::vision_msgs::msg::AIStatus msg_;
};

class Init_AIStatus_cpu_usage
{
public:
  explicit Init_AIStatus_cpu_usage(::vision_msgs::msg::AIStatus & msg)
  : msg_(msg)
  {}
  Init_AIStatus_memory_mb cpu_usage(::vision_msgs::msg::AIStatus::_cpu_usage_type arg)
  {
    msg_.cpu_usage = std::move(arg);
    return Init_AIStatus_memory_mb(msg_);
  }

private:
  ::vision_msgs::msg::AIStatus msg_;
};

class Init_AIStatus_inference_time_ms
{
public:
  explicit Init_AIStatus_inference_time_ms(::vision_msgs::msg::AIStatus & msg)
  : msg_(msg)
  {}
  Init_AIStatus_cpu_usage inference_time_ms(::vision_msgs::msg::AIStatus::_inference_time_ms_type arg)
  {
    msg_.inference_time_ms = std::move(arg);
    return Init_AIStatus_cpu_usage(msg_);
  }

private:
  ::vision_msgs::msg::AIStatus msg_;
};

class Init_AIStatus_fps
{
public:
  explicit Init_AIStatus_fps(::vision_msgs::msg::AIStatus & msg)
  : msg_(msg)
  {}
  Init_AIStatus_inference_time_ms fps(::vision_msgs::msg::AIStatus::_fps_type arg)
  {
    msg_.fps = std::move(arg);
    return Init_AIStatus_inference_time_ms(msg_);
  }

private:
  ::vision_msgs::msg::AIStatus msg_;
};

class Init_AIStatus_header
{
public:
  Init_AIStatus_header()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_AIStatus_fps header(::vision_msgs::msg::AIStatus::_header_type arg)
  {
    msg_.header = std::move(arg);
    return Init_AIStatus_fps(msg_);
  }

private:
  ::vision_msgs::msg::AIStatus msg_;
};

}  // namespace builder

}  // namespace msg

template<typename MessageType>
auto build();

template<>
inline
auto build<::vision_msgs::msg::AIStatus>()
{
  return vision_msgs::msg::builder::Init_AIStatus_header();
}

}  // namespace vision_msgs

#endif  // VISION_MSGS__MSG__DETAIL__AI_STATUS__BUILDER_HPP_
