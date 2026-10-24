#!/bin/bash
# note (luojiaxuan): host side: servers and bench in their containers, and the servers container
# stopped once recording ends so the judge gets the GPU. $1 servers container, $2 bench container.
SRV=$1; BENCH_C=$2; H=$HOME/runs/fdb-anchor; R=/data/runs/fdb-anchor; SHA=3dd888e02ac44fd64414241fc9ea55ab80a22adc
podman exec $SRV bash $R/servers.sh $R > $H/logs/srv-driver.log 2>&1 &
podman exec $BENCH_C bash $R/bench.sh $R $SHA > $H/logs/bench-driver.log 2>&1 &
BENCH=$!
until [ -e $H/logs/recorded ]; do
  kill -0 $BENCH 2>/dev/null || { echo "BENCH_EXITED_EARLY"; exit 1; }
  sleep 20
done
podman stop -t 20 $SRV && touch $H/logs/servers-stopped
wait $BENCH
echo "DRIVER_EXIT=$?"
