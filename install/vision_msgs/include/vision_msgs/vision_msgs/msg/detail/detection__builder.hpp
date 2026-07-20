// generated from rosidl_generator_cpp/resource/idl__builder.hpp.em
// with input from vision_msgs:msg/Detection.idl
// generated code does not contain a copyright notice

#ifndef VISION_MSGS__MSG__DETAIL__DETECTION__BUILDER_HPP_
#define VISION_MSGS__MSG__DETAIL__DETECTION__BUILDER_HPP_

#include <algorithm>
#include <utility>

#include "vision_msgs/msg/detail/detection__struct.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


namespace vision_msgs
{

namespace msg
{

namespace builder
{

class Init_Detection_center_y
{
public:
  explicit Init_Detection_center_y(::vision_msgs::msg::Detection & msg)
  : msg_(msg)
  {}
  ::vision_msgs::msg::Detection center_y(::vision_msgs::msg::Detection::_center_y_type arg)
  {
    msg_.center_y = std::move(arg);
    return std::move(msg_);
  }

private:
  ::vision_msgs::msg::Detection msg_;
};

class Init_Detection_center_x
{
public:
  explicit Init_Detection_center_x(::vision_msgs::msg::Detection & msg)
  : msg_(msg)
  {}
  Init_Detection_center_y center_x(::vision_msgs::msg::Detection::_center_x_type arg)
  {
    msg_.center_x = std::move(arg);
    return Init_Detection_center_y(msg_);
  }

private:
  ::vision_msgs::msg::Detection msg_;
};

class Init_Detection_y_max
{
public:
  explicit Init_Detection_y_max(::vision_msgs::msg::Detection & msg)
  : msg_(msg)
  {}
  Init_Detection_center_x y_max(::vision_msgs::msg::Detection::_y_max_type arg)
  {
    msg_.y_max = std::move(arg);
    return Init_Detection_center_x(msg_);
  }

private:
  ::vision_msgs::msg::Detection msg_;
};

class Init_Detection_x_max
{
public:
  explicit Init_Detection_x_max(::vision_msgs::msg::Detection & msg)
  : msg_(msg)
  {}
  Init_Detection_y_max x_max(::vision_msgs::msg::Detection::_x_max_type arg)
  {
    msg_.x_max = std::move(arg);
    return Init_Detection_y_max(msg_);
  }

private:
  ::vision_msgs::msg::Detection msg_;
};

class Init_Detection_y_min
{
public:
  explicit Init_Detection_y_min(::vision_msgs::msg::Detection & msg)
  : msg_(msg)
  {}
  Init_Detection_x_max y_min(::vision_msgs::msg::Detection::_y_min_type arg)
  {
    msg_.y_min = std::move(arg);
    return Init_Detection_x_max(msg_);
  }

private:
  ::vision_msgs::msg::Detection msg_;
};

class Init_Detection_x_min
{
public:
  explicit Init_Detection_x_min(::vision_msgs::msg::Detection & msg)
  : msg_(msg)
  {}
  Init_Detection_y_min x_min(::vision_msgs::msg::Detection::_x_min_type arg)
  {
    msg_.x_min = std::move(arg);
    return Init_Detection_y_min(msg_);
  }

private:
  ::vision_msgs::msg::Detection msg_;
};

class Init_Detection_confidence
{
public:
  explicit Init_Detection_confidence(::vision_msgs::msg::Detection & msg)
  : msg_(msg)
  {}
  Init_Detection_x_min confidence(::vision_msgs::msg::Detection::_confidence_type arg)
  {
    msg_.confidence = std::move(arg);
    return Init_Detection_x_min(msg_);
  }

private:
  ::vision_msgs::msg::Detection msg_;
};

class Init_Detection_class_id
{
public:
  explicit Init_Detection_class_id(::vision_msgs::msg::Detection & msg)
  : msg_(msg)
  {}
  Init_Detection_confidence class_id(::vision_msgs::msg::Detection::_class_id_type arg)
  {
    msg_.class_id = std::move(arg);
    return Init_Detection_confidence(msg_);
  }

private:
  ::vision_msgs::msg::Detection msg_;
};

class Init_Detection_class_name
{
public:
  Init_Detection_class_name()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_Detection_class_id class_name(::vision_msgs::msg::Detection::_class_name_type arg)
  {
    msg_.class_name = std::move(arg);
    return Init_Detection_class_id(msg_);
  }

private:
  ::vision_msgs::msg::Detection msg_;
};

}  // namespace builder

}  // namespace msg

template<typename MessageType>
auto build();

template<>
inline
auto build<::vision_msgs::msg::Detection>()
{
  return vision_msgs::msg::builder::Init_Detection_class_name();
}

}  // namespace vision_msgs

#endif  // VISION_MSGS__MSG__DETAIL__DETECTION__BUILDER_HPP_
