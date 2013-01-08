#!/bin/bash
# Migration XiVO 1.1 to 12 - Migrate Voicemenu in the webi in dialplan
#
# What does it do :
# - export a XiVO 1.1 voicemenu created via the web interface (that is stored in the DB),
# - to an asterisk extension file
# 
# Warning :
# This script is intended to ease migration from XiVO 1.1 towards XiVO 12.
# You should know what you are doing !


# File
MIGR_VCM_FILE=/root/Migration-1.1-to-12/voicemenu_list.dat
MIGR_VCM_EXT_FILE=/root/Migration-1.1-to-12/voicemenu.conf

# Erase file
> ${MIGR_VCM_EXT_FILE}

# Get all SVI name
mysql --defaults-file=/etc/mysql/debian.cnf --skip-column-names asterisk -e "SELECT CONCAT(id,',',name) FROM voicemenu;" > ${MIGR_VCM_FILE}

for VCM in $(cat ${MIGR_VCM_FILE} |cut -d',' -f2); do
   MIGR_VCM_CONTEXT="voicemenu-${VCM}"
   echo "[${MIGR_VCM_CONTEXT}]" >> ${MIGR_VCM_EXT_FILE}
   mysql --defaults-file=/etc/mysql/debian.cnf --skip-column-names asterisk -e "
	SELECT CONCAT('exten = ',exten,',',priority,',',
			CASE WHEN app = 'Macro' AND appdata LIKE 'voicemenu%'
				THEN 'Goto'
				ELSE app
				END,
			'(',
			appdata,
			')')
	FROM extensions 
	WHERE context = '${MIGR_VCM_CONTEXT}' 
	ORDER BY id;" >> ${MIGR_VCM_EXT_FILE}
   echo -e "\n" >> ${MIGR_VCM_EXT_FILE}
done

# Replace 'voicemenu' with the correct context
for VCM_LINE in $(cat ${MIGR_VCM_FILE}); do
	VCM_ID=$(echo ${VCM_LINE}|cut -d',' -f1)
	VCM_CONTEXT=$(echo ${VCM_LINE}|cut -d',' -f2)
	sed -i -r "s/voicemenu\|${VCM_ID}\|1/voicemenu-${VCM_CONTEXT},s,1/" ${MIGR_VCM_EXT_FILE}
done

# Replace 'extension' destination with the correct Goto command
sed -i -r "s/Macro\(extension\|(.*)\|(.*)\)/Goto(\2,\1,1)/" ${MIGR_VCM_EXT_FILE}

# Add even a little bit of presentation
sed -i -r "s/^exten = [^s],1.*$/\n\0/" ${MIGR_VCM_EXT_FILE}

# Replace other Macro destination with a BIG warning
sed -i -r "s/^exten = .*,Macro\(.*$/;; XXX \0 ;; TODO : check this rewrite dialplan accordingly/" ${MIGR_VCM_EXT_FILE}
