#[cfg(feature = "serde")]
use serde::{Deserialize, Serialize};


#[link(name = "vision_msgs__rosidl_typesupport_c")]
extern "C" {
    fn rosidl_typesupport_c__get_message_type_support_handle__vision_msgs__msg__Detection() -> *const std::ffi::c_void;
}

#[link(name = "vision_msgs__rosidl_generator_c")]
extern "C" {
    fn vision_msgs__msg__Detection__init(msg: *mut Detection) -> bool;
    fn vision_msgs__msg__Detection__Sequence__init(seq: *mut rosidl_runtime_rs::Sequence<Detection>, size: usize) -> bool;
    fn vision_msgs__msg__Detection__Sequence__fini(seq: *mut rosidl_runtime_rs::Sequence<Detection>);
    fn vision_msgs__msg__Detection__Sequence__copy(in_seq: &rosidl_runtime_rs::Sequence<Detection>, out_seq: *mut rosidl_runtime_rs::Sequence<Detection>) -> bool;
}

// Corresponds to vision_msgs__msg__Detection
#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]

/// Single object detection result
///
/// Published by vision_ai_node after YOLO inference.
/// Each detection contains the class name, confidence score,
/// and bounding box in pixel coordinates.

#[repr(C)]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct Detection {
    /// Class label from YOLO model (e.g. "person", "car", "bottle")
    pub class_name: rosidl_runtime_rs::String,

    /// Class ID from YOLO model (integer index)
    pub class_id: i32,

    /// Detection confidence
    pub confidence: f32,

    /// Bounding box in pixel coordinates (top-left origin)
    /// Left edge
    pub x_min: i32,

    /// Top edge
    pub y_min: i32,

    /// Right edge
    pub x_max: i32,

    /// Bottom edge
    pub y_max: i32,

}



impl Default for Detection {
  fn default() -> Self {
    unsafe {
      let mut msg = std::mem::zeroed();
      if !vision_msgs__msg__Detection__init(&mut msg as *mut _) {
        panic!("Call to vision_msgs__msg__Detection__init() failed");
      }
      msg
    }
  }
}

impl rosidl_runtime_rs::SequenceAlloc for Detection {
  fn sequence_init(seq: &mut rosidl_runtime_rs::Sequence<Self>, size: usize) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { vision_msgs__msg__Detection__Sequence__init(seq as *mut _, size) }
  }
  fn sequence_fini(seq: &mut rosidl_runtime_rs::Sequence<Self>) {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { vision_msgs__msg__Detection__Sequence__fini(seq as *mut _) }
  }
  fn sequence_copy(in_seq: &rosidl_runtime_rs::Sequence<Self>, out_seq: &mut rosidl_runtime_rs::Sequence<Self>) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { vision_msgs__msg__Detection__Sequence__copy(in_seq, out_seq as *mut _) }
  }
}

impl rosidl_runtime_rs::Message for Detection {
  type RmwMsg = Self;
  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> { msg_cow }
  fn from_rmw_message(msg: Self::RmwMsg) -> Self { msg }
}

impl rosidl_runtime_rs::RmwMessage for Detection where Self: Sized {
  const TYPE_NAME: &'static str = "vision_msgs/msg/Detection";
  fn get_type_support() -> *const std::ffi::c_void {
    // SAFETY: No preconditions for this function.
    unsafe { rosidl_typesupport_c__get_message_type_support_handle__vision_msgs__msg__Detection() }
  }
}


#[link(name = "vision_msgs__rosidl_typesupport_c")]
extern "C" {
    fn rosidl_typesupport_c__get_message_type_support_handle__vision_msgs__msg__DetectionArray() -> *const std::ffi::c_void;
}

#[link(name = "vision_msgs__rosidl_generator_c")]
extern "C" {
    fn vision_msgs__msg__DetectionArray__init(msg: *mut DetectionArray) -> bool;
    fn vision_msgs__msg__DetectionArray__Sequence__init(seq: *mut rosidl_runtime_rs::Sequence<DetectionArray>, size: usize) -> bool;
    fn vision_msgs__msg__DetectionArray__Sequence__fini(seq: *mut rosidl_runtime_rs::Sequence<DetectionArray>);
    fn vision_msgs__msg__DetectionArray__Sequence__copy(in_seq: &rosidl_runtime_rs::Sequence<DetectionArray>, out_seq: *mut rosidl_runtime_rs::Sequence<DetectionArray>) -> bool;
}

// Corresponds to vision_msgs__msg__DetectionArray
#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]

/// Array of object detections from a single frame
///
/// Published by vision_ai_node on /vision/detections.
/// Contains all detected objects plus metadata about the frame.

#[repr(C)]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct DetectionArray {
    /// Header with timestamp and frame_id
    pub header: std_msgs::msg::rmw::Header,

    /// List of individual detections
    pub detections: rosidl_runtime_rs::Sequence<super::super::msg::rmw::Detection>,

    /// Original image dimensions
    pub image_width: i32,


    // This member is not documented.
    #[allow(missing_docs)]
    pub image_height: i32,

    /// Inference time in milliseconds
    pub inference_time_ms: f32,

}



impl Default for DetectionArray {
  fn default() -> Self {
    unsafe {
      let mut msg = std::mem::zeroed();
      if !vision_msgs__msg__DetectionArray__init(&mut msg as *mut _) {
        panic!("Call to vision_msgs__msg__DetectionArray__init() failed");
      }
      msg
    }
  }
}

impl rosidl_runtime_rs::SequenceAlloc for DetectionArray {
  fn sequence_init(seq: &mut rosidl_runtime_rs::Sequence<Self>, size: usize) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { vision_msgs__msg__DetectionArray__Sequence__init(seq as *mut _, size) }
  }
  fn sequence_fini(seq: &mut rosidl_runtime_rs::Sequence<Self>) {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { vision_msgs__msg__DetectionArray__Sequence__fini(seq as *mut _) }
  }
  fn sequence_copy(in_seq: &rosidl_runtime_rs::Sequence<Self>, out_seq: &mut rosidl_runtime_rs::Sequence<Self>) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { vision_msgs__msg__DetectionArray__Sequence__copy(in_seq, out_seq as *mut _) }
  }
}

impl rosidl_runtime_rs::Message for DetectionArray {
  type RmwMsg = Self;
  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> { msg_cow }
  fn from_rmw_message(msg: Self::RmwMsg) -> Self { msg }
}

impl rosidl_runtime_rs::RmwMessage for DetectionArray where Self: Sized {
  const TYPE_NAME: &'static str = "vision_msgs/msg/DetectionArray";
  fn get_type_support() -> *const std::ffi::c_void {
    // SAFETY: No preconditions for this function.
    unsafe { rosidl_typesupport_c__get_message_type_support_handle__vision_msgs__msg__DetectionArray() }
  }
}


