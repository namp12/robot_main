// generated from rosidl_generator_cpp/resource/idl__struct.hpp.em
// with input from vision_msgs:msg/AIStatus.idl
// generated code does not contain a copyright notice

#ifndef VISION_MSGS__MSG__DETAIL__AI_STATUS__STRUCT_HPP_
#define VISION_MSGS__MSG__DETAIL__AI_STATUS__STRUCT_HPP_

#include <algorithm>
#include <array>
#include <cstdint>
#include <memory>
#include <string>
#include <vector>

#include "rosidl_runtime_cpp/bounded_vector.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


// Include directives for member types
// Member 'header'
#include "std_msgs/msg/detail/header__struct.hpp"

#ifndef _WIN32
# define DEPRECATED__vision_msgs__msg__AIStatus __attribute__((deprecated))
#else
# define DEPRECATED__vision_msgs__msg__AIStatus __declspec(deprecated)
#endif

namespace vision_msgs
{

namespace msg
{

// message struct
template<class ContainerAllocator>
struct AIStatus_
{
  using Type = AIStatus_<ContainerAllocator>;

  explicit AIStatus_(rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  : header(_init)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->fps = 0.0f;
      this->inference_time_ms = 0.0f;
      this->cpu_usage = 0.0f;
      this->memory_mb = 0.0f;
      this->model_loaded = false;
      this->num_detections = 0l;
      this->status = "";
    }
  }

  explicit AIStatus_(const ContainerAllocator & _alloc, rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  : header(_alloc, _init),
    status(_alloc)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->fps = 0.0f;
      this->inference_time_ms = 0.0f;
      this->cpu_usage = 0.0f;
      this->memory_mb = 0.0f;
      this->model_loaded = false;
      this->num_detections = 0l;
      this->status = "";
    }
  }

  // field types and members
  using _header_type =
    std_msgs::msg::Header_<ContainerAllocator>;
  _header_type header;
  using _fps_type =
    float;
  _fps_type fps;
  using _inference_time_ms_type =
    float;
  _inference_time_ms_type inference_time_ms;
  using _cpu_usage_type =
    float;
  _cpu_usage_type cpu_usage;
  using _memory_mb_type =
    float;
  _memory_mb_type memory_mb;
  using _model_loaded_type =
    bool;
  _model_loaded_type model_loaded;
  using _num_detections_type =
    int32_t;
  _num_detections_type num_detections;
  using _status_type =
    std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>>;
  _status_type status;

  // setters for named parameter idiom
  Type & set__header(
    const std_msgs::msg::Header_<ContainerAllocator> & _arg)
  {
    this->header = _arg;
    return *this;
  }
  Type & set__fps(
    const float & _arg)
  {
    this->fps = _arg;
    return *this;
  }
  Type & set__inference_time_ms(
    const float & _arg)
  {
    this->inference_time_ms = _arg;
    return *this;
  }
  Type & set__cpu_usage(
    const float & _arg)
  {
    this->cpu_usage = _arg;
    return *this;
  }
  Type & set__memory_mb(
    const float & _arg)
  {
    this->memory_mb = _arg;
    return *this;
  }
  Type & set__model_loaded(
    const bool & _arg)
  {
    this->model_loaded = _arg;
    return *this;
  }
  Type & set__num_detections(
    const int32_t & _arg)
  {
    this->num_detections = _arg;
    return *this;
  }
  Type & set__status(
    const std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>> & _arg)
  {
    this->status = _arg;
    return *this;
  }

  // constant declarations

  // pointer types
  using RawPtr =
    vision_msgs::msg::AIStatus_<ContainerAllocator> *;
  using ConstRawPtr =
    const vision_msgs::msg::AIStatus_<ContainerAllocator> *;
  using SharedPtr =
    std::shared_ptr<vision_msgs::msg::AIStatus_<ContainerAllocator>>;
  using ConstSharedPtr =
    std::shared_ptr<vision_msgs::msg::AIStatus_<ContainerAllocator> const>;

  template<typename Deleter = std::default_delete<
      vision_msgs::msg::AIStatus_<ContainerAllocator>>>
  using UniquePtrWithDeleter =
    std::unique_ptr<vision_msgs::msg::AIStatus_<ContainerAllocator>, Deleter>;

  using UniquePtr = UniquePtrWithDeleter<>;

  template<typename Deleter = std::default_delete<
      vision_msgs::msg::AIStatus_<ContainerAllocator>>>
  using ConstUniquePtrWithDeleter =
    std::unique_ptr<vision_msgs::msg::AIStatus_<ContainerAllocator> const, Deleter>;
  using ConstUniquePtr = ConstUniquePtrWithDeleter<>;

  using WeakPtr =
    std::weak_ptr<vision_msgs::msg::AIStatus_<ContainerAllocator>>;
  using ConstWeakPtr =
    std::weak_ptr<vision_msgs::msg::AIStatus_<ContainerAllocator> const>;

  // pointer types similar to ROS 1, use SharedPtr / ConstSharedPtr instead
  // NOTE: Can't use 'using' here because GNU C++ can't parse attributes properly
  typedef DEPRECATED__vision_msgs__msg__AIStatus
    std::shared_ptr<vision_msgs::msg::AIStatus_<ContainerAllocator>>
    Ptr;
  typedef DEPRECATED__vision_msgs__msg__AIStatus
    std::shared_ptr<vision_msgs::msg::AIStatus_<ContainerAllocator> const>
    ConstPtr;

  // comparison operators
  bool operator==(const AIStatus_ & other) const
  {
    if (this->header != other.header) {
      return false;
    }
    if (this->fps != other.fps) {
      return false;
    }
    if (this->inference_time_ms != other.inference_time_ms) {
      return false;
    }
    if (this->cpu_usage != other.cpu_usage) {
      return false;
    }
    if (this->memory_mb != other.memory_mb) {
      return false;
    }
    if (this->model_loaded != other.model_loaded) {
      return false;
    }
    if (this->num_detections != other.num_detections) {
      return false;
    }
    if (this->status != other.status) {
      return false;
    }
    return true;
  }
  bool operator!=(const AIStatus_ & other) const
  {
    return !this->operator==(other);
  }
};  // struct AIStatus_

// alias to use template instance with default allocator
using AIStatus =
  vision_msgs::msg::AIStatus_<std::allocator<void>>;

// constant definitions

}  // namespace msg

}  // namespace vision_msgs

#endif  // VISION_MSGS__MSG__DETAIL__AI_STATUS__STRUCT_HPP_
