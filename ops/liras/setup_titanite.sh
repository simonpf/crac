#!/bin/bash

export JOINT_FLIGHT_PATH=/home/simonpf/src/joint_flight
export LIRAS_PATH=/home/simonpf/src/joint_flight
#export LIRAS_PATH=/old/projects/LIRAS/Development/liras/

export ARTS_BUILD_PATH=/home/simonpf/build/arts
export ARTS_INCLUDE_PATH=/home/simonpf/src/arts_wip/controlfiles

export PYTHONPATH=/home/simonpf/src/parts
export PYTHONPATH=/home/simonpf/src/crac:${PYTHONPATH}
export PYTHONPATH=/home/simonpf/src/joint_flight/:${PYTHONPATH}
