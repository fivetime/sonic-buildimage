#!/bin/sh
# Set correct high/crit thresholds for the Z9100 jc42 temp sensor (i2c-1/1-0018),
# whose thresholds ship uninitialized (0 C) and cause false ALARM in show environment.
set -eu
for i in $(seq 1 60); do
    for hw in /sys/class/hwmon/hwmon*; do
        [ -f "$hw/name" ] || continue
        [ "$(cat "$hw/name")" = "jc42" ] || continue
        target=$(readlink -f "$hw/device" 2>/dev/null || true)
        case "$target" in
            */i2c-1/1-0018)
                echo 85000 > "$hw/temp1_max"  2>/dev/null || true
                echo 95000 > "$hw/temp1_crit" 2>/dev/null || true
                exit 0
                ;;
        esac
    done
    sleep 2
done
echo "z9100-jc42-thresholds: jc42 i2c-1/1-0018 hwmon not found" >&2
exit 0
