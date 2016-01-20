#!/bin/bash
# This cron will check the daemon is running and re-start if it's not.

if [ -z "$1" ]; then
    echo "ERROR: Please specify the full path to the python bin"
    exit 1
fi

if [ -z "$2" ]; then
    echo "ERROR: Please specify the full path to the daemon file"
    exit 1
fi

check=`ps aux | grep "$1 $2" | grep -v "grep"`

if [ $? != 0 ]; then
    echo "The Warboard daemon is not running! Restarting now..."
    $1 $2 &
    exit 1
fi
