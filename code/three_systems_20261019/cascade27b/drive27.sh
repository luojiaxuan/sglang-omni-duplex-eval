#!/bin/bash
# note (luojiaxuan): host side: servers and bench in their containers, and the servers container
# stopped once recording ends so the judge gets a GPU. $1 run directory on the host.
H=$1; R=/data/runs/20261019-27b; SHA=3dd888e02ac44fd64414241fc9ea55ab80a22adc
podman exec sglang-omni-jaxan-2 bash $R/servers27.sh $R > $H/logs/srv-driver.log 2>&1 &
podman exec sglang-omni-jaxan-3 bash $R/bench27.sh $R $SHA > $H/logs/bench-driver.log 2>&1 &
BENCH=$!
until [ -e $H/logs/recorded ]; do
  kill -0 $BENCH 2>/dev/null || { echo "BENCH_EXITED_EARLY"; exit 1; }
  sleep 20
done
podman stop -t 20 sglang-omni-jaxan-2 && touch $H/logs/servers-stopped
wait $BENCH
echo "DRIVER_EXIT=$?"
