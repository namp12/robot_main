# Array of object detections from a single frame
#
# Published by vision_ai_node on /vision/detections.
# Contains all detected objects plus metadata about the frame.

# Header with timestamp and frame_id
std_msgs/Header header

# List of individual detections
Detection[] detections

# Original image dimensions
int32 image_width
int32 image_height

# Inference time in milliseconds
float32 inference_time_ms
