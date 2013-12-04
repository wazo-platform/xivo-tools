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

copy_script() {
    if [ -e $1 ]; then
        cp $1 /usr/local/sbin/
    else
        println error "$1 doesn't exist in $(pwd)" 
        println error "Please launch the installation script in the installation directory" 
        exit 1
    fi
}


# Main
if [ $# -ne 2 ]; then
    echo "usage: $0 <YYYYMM> <services to monitor>"
    echo -e "\t where <YYYYMM> is the months during when the monitor will be active"
    echo -e "\t where <services to monitor> is a comma separated list of services like"
    echo -e "\t\t xivo-ctid,postgres"
    exit 1
else
    DATE=$1
    MONTHS_TO_MON=${DATE:4:6}
    OIFS=${IFS}
    IFS=','          # Change IFS to ',' 
    SERVICES_TO_MON=(${2}) # Make an array
    IFS=${OIFS}
fi



println warn "This script will install debug scripts on your XiVO"
if ! ask_yn_question "Are you sure you want to continue ?"; then
    exit 1
fi

println info "Copying script in /usr/local/sbin directory"
copy_script ac-pidstat-script.sh
copy_script ac-xc-login-count.sh
copy_script ac-xivo-monitor-script.sh
copy_script ac-debug-get-logs.sh
println info "Scritps successfully copied in /usr/local/sbin directory"


println info "Create pidstat crontab"
touch /etc/cron.d/ac-pidstat-crontab
> /etc/cron.d/ac-pidstat-crontab
echo 'MAILTO=""' > /etc/cron.d/ac-pidstat-crontab
echo '' >> /etc/cron.d/ac-pidstat-crontab
for serv in ${SERVICES_TO_MON[@]}; do
    echo "*/1 * * ${MONTHS_TO_MON} * root /usr/local/sbin/ac-pidstat-script.sh ${serv}" >> /etc/cron.d/ac-pidstat-crontab
done
IFS=${OIFS}


println info "Create ac-xivo-monitor crontab"
touch /etc/cron.d/ac-xivo-monitor-crontab
> /etc/cron.d/ac-xivo-monitor-crontab
echo 'MAILTO=""' > /etc/cron.d/ac-xivo-monitor-crontab
echo '' >> /etc/cron.d/ac-xivo-monitor-crontab
echo '## Launch two monitor utilities dstat and iotop' >> /etc/cron.d/ac-xivo-monitor-crontab
echo "02 0 * ${MONTHS_TO_MON} * root /usr/local/sbin/ac-xivo-monitor-script.sh 24 15" >> /etc/cron.d/ac-xivo-monitor-crontab


println info "Create ac-xc-logins crontab"
touch /etc/cron.d/ac-xc-logins
> /etc/cron.d/ac-xc-logins
echo 'MAILTO=""' > /etc/cron.d/ac-xc-logins
echo '' >> /etc/cron.d/ac-xc-logins
echo "* * * ${MONTHS_TO_MON} * root echo \"\$(date) xivo-ctid[\$(pgrep xivo-ctid)] \$(lsof | grep \$(pgrep xivo-ctid) | grep ':50[01]3->' | wc -l) client connection\" >> /var/log/xivo-ctid.log" >> /etc/cron.d/ac-xc-logins

println info "Installation finished"
