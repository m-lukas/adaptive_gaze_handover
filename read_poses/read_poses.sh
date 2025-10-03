#!/bin/bash

# Automatically grab one message from /joint_states and extract joint positions
joint_line=$(rostopic echo /joint_states -n1 | grep "position:")
prefix="position: ["
suffix="]"

echo "Recording joint positions. Press [Enter] to record a position."
echo "Press any other key + [Enter] to finish and output all movement commands."
echo ""

commands=()

while true; do
    # Wait for user input
    read -p "Press Enter to record or any other key + Enter to finish: " key
    if [[ -n "$key" ]]; then
        break
    fi

    # Extract the joint position line from rostopic
    joint_line=$(rostopic echo /joint_states -n1 | grep "position:")
    if [[ "$joint_line" == position:* ]]; then
        # Extract values from the position array
        positions=${joint_line#"$prefix"}
        positions=${positions%"$suffix"}
        commands+=("move_to_pose(move_group, $positions)")
        echo "Recorded."
    else
        echo "Error: Could not extract joint positions from /joint_states"
        exit 1
    fi
done

echo ""
echo "Recorded movement commands:"
output=""
for cmd in "${commands[@]}"; do
    echo "$cmd"
    output+="$cmd"$'\n'
done

echo "$output" | xclip -selection clipboard
