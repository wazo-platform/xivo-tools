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
DST_FILE="/var/local/ac-debug-get-infos-$(date +%Y%m%d%H%M%S).txt"
rm -f ${DST_FILE}

echo "SYSTEM" >> ${DST_FILE}
echo "------" >> ${DST_FILE}
echo "" >> ${DST_FILE}
# US2.2
echo "+ uptime : `uptime`" >> ${DST_FILE}
echo "" >> ${DST_FILE}

echo "ASTERISK" >> ${DST_FILE}
echo "--------" >> ${DST_FILE}
echo "" >> ${DST_FILE}
# US4.2.
echo "+ asterisk current calls" >> ${DST_FILE}
asterisk -rx 'core show channels verbose' >>  ${DST_FILE}
echo "" >> ${DST_FILE}
# US4.3.
echo "+ asterisk current threads" >> ${DST_FILE}
asterisk -rx 'core show threads' >>  ${DST_FILE}
echo "" >> ${DST_FILE}
# US4.5.
echo "+ asterisk queue" >> ${DST_FILE}
asterisk -rx 'queue show' >> ${DST_FILE}
echo "" >> ${DST_FILE}
# US4.7.
echo "+ asterisk hints" >> ${DST_FILE}
asterisk -rx 'core show hints' >> ${DST_FILE}
echo "" >> ${DST_FILE}
# US4.8.
echo "+ asterisk sip peers" >> ${DST_FILE}
asterisk -rx 'sip show peers' >> ${DST_FILE}
echo "" >> ${DST_FILE}


echo "AGENTS" >> ${DST_FILE}
echo "------" >> ${DST_FILE}
echo "" >> ${DST_FILE}
# US4.6.
echo "+ agent status" >> ${DST_FILE}
xivo-agentctl -c 'status' >> ${DST_FILE}
echo "" >> ${DST_FILE}

println info "Debug info were printed in ${DST_FILE}"

exit 0
