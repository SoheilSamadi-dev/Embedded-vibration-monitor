#!/bin/bash
# Copyright (c) 2026 Soheil Samadi
# SPDX-License-Identifier: AGPL-3.0-only
# Licensed under the GNU AGPL v3; see LICENSE in the repository root.


# Set NICLA_DEVICE to the stable serial path shown by ls /dev/serial/by-id/.
DEVICE="${NICLA_DEVICE:?Set NICLA_DEVICE to your Nicla serial device path}"

stty -F "$DEVICE" 115200 raw -echo || exit 1

while IFS= read -r line; do
    printf '%s %s\n' "$(date '+%F %T')" "$line"
done < "$DEVICE" | tee -a "$HOME/embedded-condition-monitor/nicla-timestamped.log"
