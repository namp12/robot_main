// generated from rosidl_generator_cpp/resource/idl__builder.hpp.em
// with input from vision_msgs:msg/DetectionArray.idl
// generated code does not contain a copyright notice

#ifndef VISION_MSGS__MSG__DETAIL__DETECTION_ARRAY__BUILDER_HPP_
#define VISION_MSGS__MSG__DETAIL__DETECTION_ARRAY__BUILDER_HPP_

#include <algorithm>
#include <utility>

#include "vision_msgs/msg/detail/detection_array__struct.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


namespace vision_msgs
{

namespace msg
{

namespace builder
{

class Init_DetectionArray_inference_time_ms
{
public:
  explicit Init_DetectionArray_inference_time_ms(::vision_msgs::msg::DetectionArray & msg)
  : msg_(msg)
  {}
  ::vision_msgs::msg::DetectionArray inference_time_ms(::vision_msgs::msg::DetectionArray::_inference_time_ms_type arg)
  {
    msg_.inference_time_ms = std::move(arg);
    return std::move(msg_);
  }

private:
  ::vision_msgs::msg::DetectionArray msg_;
};

class Init_DetectionArray_image_height
{
public:
  explicit Init_DetectionArray_image_height(::vision_msgs::msg::DetectionArray & msg)
  : msg_(msg)
  {}
  Init_DetectionArray_inference_time_ms image_height(::vision_msgs::msg::DetectionArray::_image_height_type arg)
  {
    msg_.image_height = std::move(arg);
    return Init_DetectionArray_inference_time_ms(msg_);
  }

private:
  ::vision_msgs::msg::DetectionArray msg_;
};

class Init_DetectionArray_image_width
{
public:
  explicit Init_DetectionArray_image_width(::vision_msgs::msg::DetectionArray & msg)
  : msg_(msg)
  {}
  Init_DetectionArray_image_height image_width(::vision_msgs::msg::DetectionArray::_image_width_type arg)
  {
    msg_.image_width = std::move(arg);
    return Init_DetectionArray_image_height(msg_);
  }

private:
  ::vision_msgs::msg::DetectionArray msg_;
};

class Init_DetectionArray_detections
{
public:
  explicit Init_DetectionArray_detections(::vision_msgs::msg::DetectionArray & msg)
  : msg_(msg)
  {}
  Init_DetectionArray_image_width detections(::vision_msgs::msg::DetectionArray::_detections_type arg)
  {
    msg_.detections = std::move(arg);
    return Init_DetectionArray_image_width(msg_);
  }

private:
  ::vision_msgs::msg::DetectionArray msg_;
};

class Init_DetectionArray_header
{
public:
  Init_DetectionArray_header()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_DetectionArray_detections header(::vision_msgs::msg::DetectionArray::_header_type arg)
  {
    msg_.header = std::move(arg);
    return Init_DetectionArray_detections(msg_);
  }

private:
  ::vision_msgs::msg::DetectionArray msg_;
};

}  // namespace builder

}  // namespace msg

template<typename MessageType>
auto build();

template<>
inline
auto build<::vision_msgs::msg::DetectionArray>()
{
  return vision_msgs::msg::builder::Init_DetectionArray_header();
}

}  // namespace vision_msgs

#endif  // VISION_MSGS__MSG__DETAIL__DETECTION_ARRAY__BUILDER_HPP_
