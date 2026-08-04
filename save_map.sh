#!/bin/bash
MAP_NAME=${1:-phong_demo}
export CYCLONEDDS_URI='<CycloneDDS><Domain id="any"><Discovery><MaxAutoParticipantIndex>500</MaxAutoParticipantIndex></Discovery></Domain></CycloneDDS>'
source /opt/ros/humble/setup.bash
source ~/robot_ws/install/setup.bash 2>/dev/null

python3 ~/robot_ws/scripts/save_map.py "$MAP_NAME"
