#!/bin/bash

# Set NICLA_DEVICE to the stable serial path shown by ls /dev/serial/by-id/.
DEVICE="${NICLA_DEVICE:?Set NICLA_DEVICE to your Nicla serial device path}"

stty -F "$DEVICE" 115200 raw -echo || exit 1

while IFS= read -r line; do
    printf '%s %s\n' "$(date '+%F %T')" "$line"
done < "$DEVICE" | tee -a "$HOME/embedded-condition-monitor/nicla-timestamped.log"
