#!/bin/bash
# usage: sweep_arm.sh <arm> <port> '<turn_detection json>'; waits for the server, records the capabilities, then records the arm
S=/data/runs/20261010-sweep
until curl -sf http://127.0.0.1:$2/health > /dev/null; do sleep 10; done
curl -sf http://127.0.0.1:$2/v1/realtime/capabilities > $S/logs/capabilities-$1.json
echo "$(date -u +%FT%TZ) server ready: $(cut -c1-300 $S/logs/capabilities-$1.json)"
$S/sweep_record.sh "$1" "$2" "$3"
