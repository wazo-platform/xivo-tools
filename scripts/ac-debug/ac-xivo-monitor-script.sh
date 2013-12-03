#!/bin/bash

# EA - 20130610
# Needs :
#  - dstat
#  - iotop
# Does :
#  Launch both utilities in logs in /var/local/
#  plus it removes log older than 30 days
# Usage :
#  Can be used in a crontab like :
## # Cron which launches monitor utility
## MAILTO=""
## 
## ## Launch two monitor utilities dstat and iotop
## 02 0 * * * root /usr/local/sbin/ac-xivo-monitor-script.sh 2870


dstat_fct() {
    /usr/bin/dstat -tcdgilmnf --output /var/local/`date +%Y%m%d`-`hostname`-dstat.log 15 $1
}

iotop_fct() {
    /usr/bin/iotop -b -o -t -d 15 -n $1 > /var/local/`date +%Y%m%d`-`hostname`-iotop.log
}

COUNT_NB=$1

dstat_fct $COUNT_NB &
iotop_fct $COUNT_NB &

find /var/local/*{dstat,iotop}.log -mtime +30 -exec rm -f {} \;


