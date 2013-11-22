#!/bin/sh

#,Time,PID,%usr,%system,%guest,%CPU,CPU,minflt/s,majflt/s,VSZ,RSS,%MEM,kB_rd/s,kB_wr/s,kB_ccwr/s,Command
DEFAULT_LINE=",2532,0.00,0.00,0.00,0.00,0,0.00,0.00,10348,4356,0.21,0.00,0.00,0.00,/usr/sbin/amiproxy"
i=0
j=0 
k=0
l=0
n=0

LOG_ORI=$1
LOG_ORI_FNAME=$(echo $1|cut -d'.' -f1)

INIT=1341915821
END=1341940150

cp $LOG_ORI_FNAME.csv $LOG_ORI_FNAME.in.csv

while read line; do
    if [ $j -eq 0 ]; then
        j=$(($j+1))
        continue
    fi
    k=0
    #echo "for: $INIT"
    for i in $(seq ${INIT} ${END}); do
        line_ts=$(echo $line | cut -d',' -f2)
    #    echo "infor: "$i $line_ts 
        if [ $i -lt $line_ts ]; then
    #        echo $i $j $k $n $line_ts
            new_line=","$i$DEFAULT_LINE
            l=$(($k+$j))
            sed "${l}a\ ${new_line}" $LOG_ORI_FNAME.in.csv > $LOG_ORI_FNAME.out.csv
            k=$(($k+1))
        else
            k=$(($k+1))
            if [ ! -e ${LOG_ORI_FNAME}.out.csv ]; then
                cp $LOG_ORI_FNAME.in.csv $LOG_ORI_FNAME.out.csv
            fi
            break
        fi
        cp $LOG_ORI_FNAME.out.csv $LOG_ORI_FNAME.in.csv
    done
    j=$(($j+$k))
   # echo $line_ts
    INIT=$((${line_ts}+1))
   # echo $INIT
    n=$(($n+1))
    echo $n
   # if [ $n -eq 12 ]; then
   #     break
   # fi
done < $LOG_ORI_FNAME.csv 


exit 0
