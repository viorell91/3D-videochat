#!/bin/bash


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
