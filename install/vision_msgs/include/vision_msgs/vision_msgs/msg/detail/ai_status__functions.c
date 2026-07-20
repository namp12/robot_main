// generated from rosidl_generator_c/resource/idl__functions.c.em
// with input from vision_msgs:msg/AIStatus.idl
// generated code does not contain a copyright notice
#include "vision_msgs/msg/detail/ai_status__functions.h"

#include <assert.h>
#include <stdbool.h>
#include <stdlib.h>
#include <string.h>

#include "rcutils/allocator.h"


// Include directives for member types
// Member `header`
#include "std_msgs/msg/detail/header__functions.h"
// Member `status`
#include "rosidl_runtime_c/string_functions.h"

bool
vision_msgs__msg__AIStatus__init(vision_msgs__msg__AIStatus * msg)
{
  if (!msg) {
    return false;
  }
  // header
  if (!std_msgs__msg__Header__init(&msg->header)) {
    vision_msgs__msg__AIStatus__fini(msg);
    return false;
  }
  // fps
  // inference_time_ms
  // cpu_usage
  // memory_mb
  // model_loaded
  // num_detections
  // status
  if (!rosidl_runtime_c__String__init(&msg->status)) {
    vision_msgs__msg__AIStatus__fini(msg);
    return false;
  }
  return true;
}

void
vision_msgs__msg__AIStatus__fini(vision_msgs__msg__AIStatus * msg)
{
  if (!msg) {
    return;
  }
  // header
  std_msgs__msg__Header__fini(&msg->header);
  // fps
  // inference_time_ms
  // cpu_usage
  // memory_mb
  // model_loaded
  // num_detections
  // status
  rosidl_runtime_c__String__fini(&msg->status);
}

bool
vision_msgs__msg__AIStatus__are_equal(const vision_msgs__msg__AIStatus * lhs, const vision_msgs__msg__AIStatus * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  // header
  if (!std_msgs__msg__Header__are_equal(
      &(lhs->header), &(rhs->header)))
  {
    return false;
  }
  // fps
  if (lhs->fps != rhs->fps) {
    return false;
  }
  // inference_time_ms
  if (lhs->inference_time_ms != rhs->inference_time_ms) {
    return false;
  }
  // cpu_usage
  if (lhs->cpu_usage != rhs->cpu_usage) {
    return false;
  }
  // memory_mb
  if (lhs->memory_mb != rhs->memory_mb) {
    return false;
  }
  // model_loaded
  if (lhs->model_loaded != rhs->model_loaded) {
    return false;
  }
  // num_detections
  if (lhs->num_detections != rhs->num_detections) {
    return false;
  }
  // status
  if (!rosidl_runtime_c__String__are_equal(
      &(lhs->status), &(rhs->status)))
  {
    return false;
  }
  return true;
}

bool
vision_msgs__msg__AIStatus__copy(
  const vision_msgs__msg__AIStatus * input,
  vision_msgs__msg__AIStatus * output)
{
  if (!input || !output) {
    return false;
  }
  // header
  if (!std_msgs__msg__Header__copy(
      &(input->header), &(output->header)))
  {
    return false;
  }
  // fps
  output->fps = input->fps;
  // inference_time_ms
  output->inference_time_ms = input->inference_time_ms;
  // cpu_usage
  output->cpu_usage = input->cpu_usage;
  // memory_mb
  output->memory_mb = input->memory_mb;
  // model_loaded
  output->model_loaded = input->model_loaded;
  // num_detections
  output->num_detections = input->num_detections;
  // status
  if (!rosidl_runtime_c__String__copy(
      &(input->status), &(output->status)))
  {
    return false;
  }
  return true;
}

vision_msgs__msg__AIStatus *
vision_msgs__msg__AIStatus__create()
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  vision_msgs__msg__AIStatus * msg = (vision_msgs__msg__AIStatus *)allocator.allocate(sizeof(vision_msgs__msg__AIStatus), allocator.state);
  if (!msg) {
    return NULL;
  }
  memset(msg, 0, sizeof(vision_msgs__msg__AIStatus));
  bool success = vision_msgs__msg__AIStatus__init(msg);
  if (!success) {
    allocator.deallocate(msg, allocator.state);
    return NULL;
  }
  return msg;
}

void
vision_msgs__msg__AIStatus__destroy(vision_msgs__msg__AIStatus * msg)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (msg) {
    vision_msgs__msg__AIStatus__fini(msg);
  }
  allocator.deallocate(msg, allocator.state);
}


bool
vision_msgs__msg__AIStatus__Sequence__init(vision_msgs__msg__AIStatus__Sequence * array, size_t size)
{
  if (!array) {
    return false;
  }
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  vision_msgs__msg__AIStatus * data = NULL;

  if (size) {
    data = (vision_msgs__msg__AIStatus *)allocator.zero_allocate(size, sizeof(vision_msgs__msg__AIStatus), allocator.state);
    if (!data) {
      return false;
    }
    // initialize all array elements
    size_t i;
    for (i = 0; i < size; ++i) {
      bool success = vision_msgs__msg__AIStatus__init(&data[i]);
      if (!success) {
        break;
      }
    }
    if (i < size) {
      // if initialization failed finalize the already initialized array elements
      for (; i > 0; --i) {
        vision_msgs__msg__AIStatus__fini(&data[i - 1]);
      }
      allocator.deallocate(data, allocator.state);
      return false;
    }
  }
  array->data = data;
  array->size = size;
  array->capacity = size;
  return true;
}

void
vision_msgs__msg__AIStatus__Sequence__fini(vision_msgs__msg__AIStatus__Sequence * array)
{
  if (!array) {
    return;
  }
  rcutils_allocator_t allocator = rcutils_get_default_allocator();

  if (array->data) {
    // ensure that data and capacity values are consistent
    assert(array->capacity > 0);
    // finalize all array elements
    for (size_t i = 0; i < array->capacity; ++i) {
      vision_msgs__msg__AIStatus__fini(&array->data[i]);
    }
    allocator.deallocate(array->data, allocator.state);
    array->data = NULL;
    array->size = 0;
    array->capacity = 0;
  } else {
    // ensure that data, size, and capacity values are consistent
    assert(0 == array->size);
    assert(0 == array->capacity);
  }
}

vision_msgs__msg__AIStatus__Sequence *
vision_msgs__msg__AIStatus__Sequence__create(size_t size)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  vision_msgs__msg__AIStatus__Sequence * array = (vision_msgs__msg__AIStatus__Sequence *)allocator.allocate(sizeof(vision_msgs__msg__AIStatus__Sequence), allocator.state);
  if (!array) {
    return NULL;
  }
  bool success = vision_msgs__msg__AIStatus__Sequence__init(array, size);
  if (!success) {
    allocator.deallocate(array, allocator.state);
    return NULL;
  }
  return array;
}

void
vision_msgs__msg__AIStatus__Sequence__destroy(vision_msgs__msg__AIStatus__Sequence * array)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (array) {
    vision_msgs__msg__AIStatus__Sequence__fini(array);
  }
  allocator.deallocate(array, allocator.state);
}

bool
vision_msgs__msg__AIStatus__Sequence__are_equal(const vision_msgs__msg__AIStatus__Sequence * lhs, const vision_msgs__msg__AIStatus__Sequence * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  if (lhs->size != rhs->size) {
    return false;
  }
  for (size_t i = 0; i < lhs->size; ++i) {
    if (!vision_msgs__msg__AIStatus__are_equal(&(lhs->data[i]), &(rhs->data[i]))) {
      return false;
    }
  }
  return true;
}

bool
vision_msgs__msg__AIStatus__Sequence__copy(
  const vision_msgs__msg__AIStatus__Sequence * input,
  vision_msgs__msg__AIStatus__Sequence * output)
{
  if (!input || !output) {
    return false;
  }
  if (output->capacity < input->size) {
    const size_t allocation_size =
      input->size * sizeof(vision_msgs__msg__AIStatus);
    rcutils_allocator_t allocator = rcutils_get_default_allocator();
    vision_msgs__msg__AIStatus * data =
      (vision_msgs__msg__AIStatus *)allocator.reallocate(
      output->data, allocation_size, allocator.state);
    if (!data) {
      return false;
    }
    // If reallocation succeeded, memory may or may not have been moved
    // to fulfill the allocation request, invalidating output->data.
    output->data = data;
    for (size_t i = output->capacity; i < input->size; ++i) {
      if (!vision_msgs__msg__AIStatus__init(&output->data[i])) {
        // If initialization of any new item fails, roll back
        // all previously initialized items. Existing items
        // in output are to be left unmodified.
        for (; i-- > output->capacity; ) {
          vision_msgs__msg__AIStatus__fini(&output->data[i]);
        }
        return false;
      }
    }
    output->capacity = input->size;
  }
  output->size = input->size;
  for (size_t i = 0; i < input->size; ++i) {
    if (!vision_msgs__msg__AIStatus__copy(
        &(input->data[i]), &(output->data[i])))
    {
      return false;
    }
  }
  return true;
}
