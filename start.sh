#!/bin/bash
set -e
RAKO_BRIDGE_IP=`python -m rakomqtt.RakoBridge`
set +e

set -m
trap 'list=$( jobs -rp ); test -n "$list" && kill $list' CHLD
python -um rakomqtt "${RAKO_BRIDGE_IP}" "$@" &
python -um rakomqtt --mode commander --rako-bridge-host "${RAKO_BRIDGE_IP}" "$@" &
wait
