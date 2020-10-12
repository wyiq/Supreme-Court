#!/bin/bash

SCRIPT=$(readlink -f "$0")
SCRIPTPATH=$(dirname "$SCRIPT")
echo $SCRIPTPATH

function log() {
  cur_DATETIME=$(date +"%Y/%m/%d %H:%M")
  echo $cur_DATETIME $* 
  echo $cur_DATETIME $* >> $SCRIPTPATH/auto-sh.log
}

running=$(ps aux | grep "[p]ython3 .*step2.py")
if [[ "$running" != "" ]]; then
  log "It is running"
  exit 0
fi

status_file="$SCRIPTPATH/status.txt"
if [ -f $status_file ]; then
  log "It is finished"
  exit 0
fi

log "run step2.py"
# otherwise, start the job
rm /home/ubuntu/tmp/audio/core.* > /dev/null  2>&1

/usr/bin/python3 /home/ubuntu/tmp/audio/step2.py
