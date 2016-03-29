#!/bin/bash

# get directory of script
DIR="$( cd "$( dirname "$0" )" && pwd )"

# assuming a local guacmole version is located properly
#LOCAL_GUACAMOLE="$DIR/../../../guacamole"
#LOCAL_AVANGO="$DIR/../../../avango"

# if not, this path will be used
#GUACAMOLE=/opt/guacamole/new_renderer
GUACAMOLE=/opt/kinect-resources/libexample-video3d
AVANGO=/opt/avango/new_renderer

# third party libs
export LD_LIBRARY_PATH=/opt/boost/boost_1_55_0/lib:/opt/zmq/current/lib:/opt/Awesomium/lib:/opt/pbr/inst_cb/lib

# schism
export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/opt/schism/current/lib/linux_x86

# avango
export LD_LIBRARY_PATH="$LOCAL_AVANGO/lib":$AVANGO/lib:$LD_LIBRARY_PATH
export PYTHONPATH=$AVANGO/lib/python3.4

# guacamole
export LD_LIBRARY_PATH="$LOCAL_GUACAMOLE/lib":$GUACAMOLE/lib:$LD_LIBRARY_PATH



# run daemon
python3 ./daemon.py > /dev/null &
#python3 daemon.py

# run head position
#ssh arachne 'cd "/opt/kinect-resources/rgbd-framework/rgbd-calib/build/build/Release" && ./zmq_sender -p 3.0 1.55 -0.48 127.0.0.1:7010' & # from origin to head position
#ssh eris 'cd "/opt/kinect-resources/rgbd-framework/rgbd-calib/build/build/Release" && ./zmq_sender -p 3.74 1.55 1.0 127.0.0.1:7010' & # from origin to head position
#ssh athena 'cd "/opt/kinect-resources/rgbd-framework/rgbd-calib/build/build/Release" && ./zmq_sender -p 0.0 1.0 0.0 127.0.0.1:7010' & # from origin to head position


# run server
cd "$DIR" && DISPLAY=:0.0 python3.4 ./server.py

# kill daemon
kill %1
#kill python3
ssh arachne 'killall python3 -KILL'
ssh eris 'killall python3 -KILL'
ssh athena 'killall python3 -KILL'

#kill python3.4
ssh arachne 'killall python3.4 -KILL'
ssh eris 'killall python3.4 -KILL'
ssh athena 'killall python3.4 -KILL'

#kill zmq-sender
#ssh arachne 'killall zmq_sender -KILL'
#ssh eris 'killall zmq_sender -KILL'
#ssh athena 'killall zmq_sender -KILL'

logout
