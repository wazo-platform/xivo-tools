#!/bin/bash

# EA - 20131204
# Needs :
#  - dstat
#  - iotop
# Does :
#  Launch both utilities in logs in /var/local/
#  plus it removes log older than 30 days
# Usage :
#  Can be used in a crontab like (for a 24 hour log with a line each 15s) :
## # Cron which launches monitor utility
## MAILTO=""
## 
## ## Launch two monitor utilities dstat and iotop
## 02 0 * * * root /usr/local/sbin/ac-xivo-monitor-script.sh 24 15


dstat_fct() {
    /usr/bin/dstat -tcdgilmnf --output /var/local/`date +%Y%m%d`-`hostname`-dstat.log $1 $2
}

iotop_fct() {
    /usr/bin/iotop -b -o -t -d $1 -n $2 > /var/local/`date +%Y%m%d`-`hostname`-iotop.log
}

if [ $# -ne 2 ]; then
    echo "Usage: $0 DURATION DELAY"
    echo "Where :"
    echo "  - DURATION : how many HOURS the test will be run,"
    echo "  - DELAY : how many SECONDS between each line of log"
    exit 1
fi

DURATION=$1
DELAY=$2

COUNT_NB=$((${DURATION} * 60 * 60 / ${DELAY}))

dstat_fct $DELAY $COUNT_NB &
iotop_fct $DELAY $COUNT_NB &

find /var/local/*{dstat,iotop}.log -mtime +30 -exec rm -f {} \;


