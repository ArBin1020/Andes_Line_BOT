#!/bin/bash

MQTT_SCRIPT="mqtt_client.py"
FLASK_SCRIPT="app.py"
MQTT_PID_FILE="mqtt_client.pid"
FLASK_PID_FILE="app.pid"


export PYTHONPATH=$(dirname $BASH_SOURCE)

start() {
    echo "Starting MQTT and Flask..."
    nohup python3 $MQTT_SCRIPT & echo $! > $MQTT_PID_FILE
    nohup python3 $FLASK_SCRIPT & echo $! > $FLASK_PID_FILE
    echo "MQTT and Flask started."
}

stop() {
    echo "Stopping MQTT and Flask..."
    if [ -f $MQTT_PID_FILE ]; then
        MQTT_PID=$(cat $MQTT_PID_FILE)
        kill $MQTT_PID
        rm $MQTT_PID_FILE
        echo "MQTT stopped."
    else
        echo "MQTT is not running."
    fi

    if [ -f $FLASK_PID_FILE ]; then
        FLASK_PID=$(cat $FLASK_PID_FILE)
        kill $FLASK_PID
        rm $FLASK_PID_FILE
        echo "Flask stopped."
    else
        echo "Flask is not running."
    fi
}

restart() {
    echo "Restarting MQTT and Flask..."
    stop
    start
}

case "$1" in
    start)
        start
        ;;
    stop)
        stop
        ;;
    restart)
        restart
        ;;
    *)
        echo "Usage: $0 {start|stop|restart}"
        exit 1
        ;;
esac
