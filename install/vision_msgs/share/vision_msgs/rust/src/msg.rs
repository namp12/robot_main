#[cfg(feature = "serde")]
use serde::{Deserialize, Serialize};



// Corresponds to vision_msgs__msg__Detection
/// Single object detection result
///
/// Published by vision_ai_node after YOLO inference.
/// Each detection contains the class name, confidence score,
/// and bounding box in pixel coordinates.

#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct Detection {
    /// Class label from YOLO model (e.g. "person", "car", "bottle")
    pub class_name: std::string::String,

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
    <Self as rosidl_runtime_rs::Message>::from_rmw_message(super::msg::rmw::Detection::default())
  }
}

impl rosidl_runtime_rs::Message for Detection {
  type RmwMsg = super::msg::rmw::Detection;

  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> {
    match msg_cow {
      std::borrow::Cow::Owned(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
        class_name: msg.class_name.as_str().into(),
        class_id: msg.class_id,
        confidence: msg.confidence,
        x_min: msg.x_min,
        y_min: msg.y_min,
        x_max: msg.x_max,
        y_max: msg.y_max,
      }),
      std::borrow::Cow::Borrowed(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
        class_name: msg.class_name.as_str().into(),
      class_id: msg.class_id,
      confidence: msg.confidence,
      x_min: msg.x_min,
      y_min: msg.y_min,
      x_max: msg.x_max,
      y_max: msg.y_max,
      })
    }
  }

  fn from_rmw_message(msg: Self::RmwMsg) -> Self {
    Self {
      class_name: msg.class_name.to_string(),
      class_id: msg.class_id,
      confidence: msg.confidence,
      x_min: msg.x_min,
      y_min: msg.y_min,
      x_max: msg.x_max,
      y_max: msg.y_max,
    }
  }
}


// Corresponds to vision_msgs__msg__DetectionArray
/// Array of object detections from a single frame
///
/// Published by vision_ai_node on /vision/detections.
/// Contains all detected objects plus metadata about the frame.

#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct DetectionArray {
    /// Header with timestamp and frame_id
    pub header: std_msgs::msg::Header,

    /// List of individual detections
    pub detections: Vec<super::msg::Detection>,

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
    <Self as rosidl_runtime_rs::Message>::from_rmw_message(super::msg::rmw::DetectionArray::default())
  }
}

impl rosidl_runtime_rs::Message for DetectionArray {
  type RmwMsg = super::msg::rmw::DetectionArray;

  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> {
    match msg_cow {
      std::borrow::Cow::Owned(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
        header: std_msgs::msg::Header::into_rmw_message(std::borrow::Cow::Owned(msg.header)).into_owned(),
        detections: msg.detections
          .into_iter()
          .map(|elem| super::msg::Detection::into_rmw_message(std::borrow::Cow::Owned(elem)).into_owned())
          .collect(),
        image_width: msg.image_width,
        image_height: msg.image_height,
        inference_time_ms: msg.inference_time_ms,
      }),
      std::borrow::Cow::Borrowed(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
        header: std_msgs::msg::Header::into_rmw_message(std::borrow::Cow::Borrowed(&msg.header)).into_owned(),
        detections: msg.detections
          .iter()
          .map(|elem| super::msg::Detection::into_rmw_message(std::borrow::Cow::Borrowed(elem)).into_owned())
          .collect(),
      image_width: msg.image_width,
      image_height: msg.image_height,
      inference_time_ms: msg.inference_time_ms,
      })
    }
  }

  fn from_rmw_message(msg: Self::RmwMsg) -> Self {
    Self {
      header: std_msgs::msg::Header::from_rmw_message(msg.header),
      detections: msg.detections
          .into_iter()
          .map(super::msg::Detection::from_rmw_message)
          .collect(),
      image_width: msg.image_width,
      image_height: msg.image_height,
      inference_time_ms: msg.inference_time_ms,
    }
  }
}


