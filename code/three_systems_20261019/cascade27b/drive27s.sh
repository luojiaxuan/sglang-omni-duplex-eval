#!/bin/bash
# note (luojiaxuan): host side on the sweep node: servers and the sweep in their containers. $1 run directory on the host.
H=$1; R=/data/runs/20261019-27b; SHA=3dd888e02ac44fd64414241fc9ea55ab80a22adc
podman exec sglang-omni-jaxan-1 bash $R/servers27s.sh $R > $H/logs/srv-driver.log 2>&1 &
podman exec sglang-omni-jaxan-2 bash $R/sweep27.sh $R $SHA > $H/logs/sweep-driver.log 2>&1
echo "DRIVER_EXIT=$?"
