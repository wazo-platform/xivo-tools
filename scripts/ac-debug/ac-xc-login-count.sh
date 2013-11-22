#!/bin/sh
# Script that counts the number of XiVO Client login and logout
# Example of usage :
## for log in $(ls -1 /var/log/xivo-ctid.log*); do ls --full-time -l $log |grep -oE '[0-9]{4}-[0-9]{2}-[0-9]{2}'; /usr/local/sbin/xivo-client-nblogin.sh $log; done

# TODO:
## - counts login/logout per hour
## - differenciate {by_client,by_server_stop,by_server_reload,broken_pipe}
## - take into account xivo-ctid start (STARTING = all clients were disconnected)

if [ $# -ne 1 ]; then
    echo "Usage: $0 <path to xivo-ctid log file>"
    exit 1
fi

XCTID_LOG=$1
XC_CNX="LOGIN SUCCESSFUL"
XC_DCNX="\(interface_cti\): disconnected "

TEMP_RES=$(mktemp)

zgrep -E "${XC_CNX}|${XC_DCNX}" ${XCTID_LOG} > ${TEMP_RES}

XC_LOGIN_NB=$(grep -E "${XC_CNX}" ${TEMP_RES} |wc -l)
XC_LOGOUT_NB=$(grep -E "${XC_DCNX}" ${TEMP_RES} |wc -l)

echo "Login: ${XC_LOGIN_NB}"
echo "Logout: ${XC_LOGOUT_NB}"

rm ${TEMP_RES}
