#!/bin/bash

# Functions
println() {
    level=$1
    text=$2

    if [ "$level" == "error" ]; then
        echo -en "\033[0;36;31m$text\033[0;38;39m\n\r"
    elif [ "$level" == "warn" ]; then
        echo -en "\033[0;36;33m$text\033[0;38;39m\n\r"
    else
        echo -en "\033[0;36;40m$text\033[0;38;39m\n\r"
    fi
}

ask_yn_question() {
    QUESTION=$1

    while true; do
        println warn "${QUESTION} (y/n) "
        read REPLY
        if [ "${REPLY}" == "y" ];
        then
                return 0;
        fi
        if [ "${REPLY}" == "n" ];
        then
                return 1;
        fi
        echo "Don't tell ya life, reply using 'y' or 'n'"'!'
    done
}

# Main
if [ $# -ne 1 ]; then
    echo "usage: $0 <nb of day since problem>"
    echo -e "\t where <nb of day since problem> is the number of day since the problem occured"
    echo -e "\t\t 0 : problem occured today"
    echo -e "\t\t 1 : problem occured yesterday"
    exit 1
else
    NB_OF_DAY=$1
    if [ "${NB_OF_DAY}" -gt 14 ]; then
        println error "Problem occured too long ago. I probably won't be able to get the log"
        if ! ask_yn_question "Do you want to continue anyway ?"; then
            exit 1
        fi
        println info "OK, let's try anyway"
    fi
fi

DATE_OF_PB=$(date +"%Y%m%d" -d "- ${NB_OF_DAY} days")
DST_FILE="/var/local/ac-debug-$(date +%Y%m%d)-from-${DATE_OF_PB}.tar"
rm -f ${DST_FILE}

OTHER_LOG="/var/log/syslog
           /var/log/daemon.log
           /var/log/daemon.log"

XIVO_LOG="/var/log/xivo-agentd.log
          /var/log/xivo-ctid.log
          /var/log/asterisk/full
          /var/log/xivo-web-interface/xivo.log
          /var/log/nginx/xivo.access.log"

MONITOR_LOG="/var/local/pidstat*${DATE_OF_PB}*
            /var/local/${DATE_OF_PB}*dstat.log
            /var/local/${DATE_OF_PB}*iotop.log"

# Get other logs :
if [ $NB_OF_DAY -eq 0 ]; then
    for log in ${OTHER_LOG}; do
        tar rvf ${DST_FILE} $log
    done
elif [ $NB_OF_DAY -eq 1 ]; then
    for log in ${OTHER_LOG}; do
        tar rvf ${DST_FILE} $log"."${NB_OF_DAY}
    done
else
    for log in ${XIVO_LOG}; do
        tar rvf ${DST_FILE} $log"."${NB_OF_DAY}".gz"
    done
fi

# Get xivo logs :
if [ $NB_OF_DAY -eq 0 ]; then
    for log in ${XIVO_LOG}; do
        tar rvf ${DST_FILE} $log
    done
else
    for log in ${XIVO_LOG}; do
        tar rvf ${DST_FILE} $log".${NB_OF_DAY}.gz"
    done
fi

# Get monitor logs
for log in ${MONITOR_LOG}; do
    tar rvf ${DST_FILE} $log
done

println "gzip ${DST_FILE}"
gzip ${DST_FILE}
println info "You can now retrieve ${DST_FILE}.gz and send it to the support team"

