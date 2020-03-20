#!/bin/bash

set -m
trap 'list=$( jobs -rp ); test -n "$list" && kill $list' CHLD
python -um rakomqtt --mode watcher "$@" &
python -um rakomqtt --mode commander "$@" &
wait
