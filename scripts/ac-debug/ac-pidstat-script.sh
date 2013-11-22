#!/bin/bash

# EA - 2011-11-24 jeu. 09:25 
# Needs 
# - pidstat binary (apt-get install sysstat)
# Usage 
# Can be used in a cron like :
## MAILTO=""
##
## */1 09-20 27 7 * root /usr/local/sbin/pidstat-script.sh amiproxy
## */1 09-20 27 7 * root /usr/local/sbin/pidstat-script.sh xivo-ctid
## */1 09-20 27 7 * root /usr/local/sbin/pidstat-script.sh postgres


PIDSTAT=$(which pidstat)
DATE=$(date +%Y%m%d)
LOGDIR=/var/local
LOGPREFIX=pidstat
LOGMAXAGE="7" # in days
LOGMAXAGEHOUR=$((${LOGMAXAGE}*24))

# Vars init
if [ $# -eq 2 ]; then
    PROGNAME=$1
    LOGDIR=$2
    LOGFILE=${LOGDIR}/${LOGPREFIX}-${DATE}-${PROGNAME}.log
elif [ $# -eq 1 ]; then
    PROGNAME=$1
    LOGFILE=${LOGDIR}/${LOGPREFIX}-${DATE}-${PROGNAME}.log
else
    PROGNAME=""
    LOGFILE=${LOGDIR}/${LOGPREFIX}-${DATE}.log
fi


[ -x ${PIDSTAT} ] || exit 1

if [ -n ${PROGNAME} ]; then
    ARGS="-r -u -d -l -h -C ${PROGNAME} 5 12"
else
    ARGS="-r -u -d -l -h 5 12"
fi

# Init of logfile
if [ ! -f ${LOGFILE} ]; then 
    touch ${LOGFILE}
    $(${PIDSTAT} -r -u -d -h | grep -Ev '^ [0-9]' > ${LOGFILE})
fi

# Collect stats
$(${PIDSTAT} ${ARGS} |grep -E '^ [0-9]'|sed -r 's/,/./g' >> ${LOGFILE})


# Remove old logfiles
find ${LOGDIR}/${LOGPREFIX}* -type f -mtime +${LOGMAXAGE} -exec rm -rf {} \;
