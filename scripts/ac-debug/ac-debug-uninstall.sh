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

println warn "It will remove all scripts and file installed by ac-debug-install.sh script"
println info "Log files will be kept"
if ! ask_yn_question "Are you sure you want to continue ?"; then
    exit 1
fi

println info "Removing scrpits"
rm /usr/local/sbin/ac-pidstat-script.sh
rm /usr/local/sbin/ac-xc-login-count.sh
rm /usr/local/sbin/ac-xivo-monitor-script.sh
rm /usr/local/sbin/ac-debug-get-logs.sh
println info "Removing crontab"
rm /etc/cron.d/ac-pidstat-crontab
rm /etc/cron.d/ac-xivo-monitor-crontab
rm /etc/cron.d/ac-xc-logins

println info "Uninstallation finished"
