#!/bin/bash
# Migration XiVO 1.1 to 12 - 1st step
# 
# Warning :
# This script is intended to ease migration from XiVO 1.1 towards XiVO 12.
# You should know what you are doing !



####################################
#
# FUNCTIONS
#
####################################

#delete_OLD_DIRECTORY
#$1 : Directory to delete
delete_OLD_DIRECTORY()
{
if [ "$1" ]
then
	if [ -d "$1" ]
	then
		rm -r "$1"
	fi
else
	echo "delete_OLD_DIRECTORY() - Missing argument"
	exit 1
fi
}

#delete_OLD_FILE
#$1 : File to delete
delete_OLD_FILE()
{
if [ "$1" ]
then
	if [ -f "$1" ]
	then
		rm "$1"
	fi
else
	echo "delete_OLD_FILE() - Missing argument"
	exit 1
fi
}


#add_MySQL_HEADER()
#$1 : Destination file
#$2 : MySQL header
add_MySQL_HEADER()
{
if [ "$1" ] && [ "$2" ]
then
	echo "$2" >> "$1"
else
	echo "add_MySQL_HEADER() - Missing argument"
	exit 1
fi
}


#exec_MySQL_REQUEST()
#$1 : MySQL command
#$2 : Temporary mysql file
exec_MySQL_REQUEST()
{
if [ "$1" ] && [ "$2" ]
then
	if [ -f $2 ]
	then
		rm $2
	fi
	/usr/bin/mysql --defaults-file=/etc/mysql/debian.cnf asterisk -e "$1"
else
	echo "exec_MySQL_REQUEST() - Missing argument"
	exit 1
fi
}


#copy_MySQL_RESULT()
#$1 : Destination file
#$2 : Temporary mysql file
copy_MySQL_RESULT()
{
if [ "$1" ] && [ "$2" ]
then
	cat "$2" >> "$1"
	sed -i 's/\\N//g' "$1"	
	rm "$2"
else
	echo "copy_MySQL_RESULT() - Missing argument"
	exit 1
fi
}

#move_MySQL_RESULT()
#$1 : Destination file
#$2 : Temporary mysql file
move_MySQL_RESULT()
{
if [ "$1" ] && [ "$2" ]
then
	mv "$2" "$1"
	sed -i 's/\\N//g' "$1"
else
	echo "move_MySQL_RESULT() - Missing argument"
	exit 1
fi
}

#################################################
#
# WORK
#
#################################################

delete_OLD_DIRECTORY /root/Migration-1.1-to-12
rm /tmp/*.csv
mkdir /root/Migration-1.1-to-12



#################################################
#
# EXPORT ALL (ALMOST) USERS DATA
#
#################################################

#HEADER
mysql_final_user_file="/root/Migration-1.1-to-12/users.csv"
mysql_HEADER="firstname|lastname|enableclient|username|password|profileclient|outcallerid|mobilephonenumber|bosssecretary|enablehint|phonenumber|context|protocol|voicemailname|voicemailmailbox|voicemailpassword|voicemailemail|voicemailattach|voicemaildelete|voicemailskippass|incallexten|incallcontext|language"
add_MySQL_HEADER "$mysql_final_user_file" "$mysql_HEADER"

#################################################
#
# EXPORT ALL (ALMOST) USERS DATA TO users.csv FILE
#
#################################################

#HEADER
mysql_temporary_user_file="/tmp/tmp_1.csv"
mysql_request="SELECT id FROM userfeatures WHERE context!='xivo-initconfig' AND protocol='sip' ORDER BY id INTO OUTFILE '$mysql_temporary_user_file' FIELDS TERMINATED BY '|' OPTIONALLY ENCLOSED BY '';"
/usr/bin/mysql --defaults-file=/etc/mysql/debian.cnf asterisk -e "$mysql_request"
number_users=$(cat $mysql_temporary_user_file | wc -l)

#WORK
for ((i = 1; i <= $number_users; i += 1))
do
	#GLOBAL VARIABLE
	current_user_id=$(sed -n "$i"p $mysql_temporary_user_file)
	current_mysql_temporary_file="/tmp/tmp_2.csv"

	#USERFEATURES
	current_mysql_request="SELECT firstname, lastname, enableclient, loginclient as username, passwdclient as password, profileclient, outcallerid, mobilephonenumber, bsfilter as bosssecretary, enablehint, number as phonenumber, context, protocol FROM userfeatures WHERE id='$current_user_id' INTO OUTFILE '$current_mysql_temporary_file' FIELDS TERMINATED BY '|' OPTIONALLY ENCLOSED BY '';"
	/usr/bin/mysql --defaults-file=/etc/mysql/debian.cnf asterisk -e "$current_mysql_request"
	current_user_features_data=$(cat $current_mysql_temporary_file)
	rm $current_mysql_temporary_file

	#VOICEMAIL
	current_mysql_request="SELECT COUNT(*) FROM userfeatures WHERE id='$current_user_id' AND voicemailid IS NULL INTO OUTFILE '$current_mysql_temporary_file' FIELDS TERMINATED BY '|' OPTIONALLY ENCLOSED BY '';"
	/usr/bin/mysql --defaults-file=/etc/mysql/debian.cnf asterisk -e "$current_mysql_request"
	does_user_have_voicemail=$(cat $current_mysql_temporary_file)
	echo $does_user_have_voicemail
	rm $current_mysql_temporary_file
	if [ "$does_user_have_voicemail" = "1" ]
	then
		current_user_voicemail_data="||||||"
	else
		current_mysql_request="SELECT fullname as voicemailname, mailbox as voicemailmailbox, password as voicemailpassword, email as voicemailemail, attach as voicemailattach, deletevoicemail as voicemaildelete, skipcheckpass as voicemailskippass FROM userfeatures, voicemail, voicemailfeatures WHERE userfeatures.id='$current_user_id' AND userfeatures.voicemailid=voicemail.uniqueid AND voicemail.uniqueid=voicemailfeatures.voicemailid INTO OUTFILE '$current_mysql_temporary_file' FIELDS TERMINATED BY '|' OPTIONALLY ENCLOSED BY '';"		
		/usr/bin/mysql --defaults-file=/etc/mysql/debian.cnf asterisk -e "$current_mysql_request"
		current_user_voicemail_data=$(cat $current_mysql_temporary_file)
		echo $current_user_voicemail_data
		rm $current_mysql_temporary_file
	fi

	#INCALL
	current_mysql_request="SELECT COUNT(*) FROM userfeatures, dialaction WHERE userfeatures.id='$current_user_id' AND category='incall' AND id=actionarg1 INTO OUTFILE '$current_mysql_temporary_file' FIELDS TERMINATED BY '|' OPTIONALLY ENCLOSED BY '';"
	/usr/bin/mysql --defaults-file=/etc/mysql/debian.cnf asterisk -e "$current_mysql_request"
	does_user_have_incall=$(cat $current_mysql_temporary_file)
	rm $current_mysql_temporary_file
	if [ "$does_user_have_incall" != "1" ]
	then
		current_user_incall_data="|"
	else
		current_mysql_request="SELECT incall.exten as incallexten, incall.context as incallcontext FROM userfeatures, incall, dialaction WHERE userfeatures.id='$current_user_id' AND userfeatures.id=dialaction.actionarg1 AND dialaction.action='user' AND dialaction.categoryval=incall.id AND dialaction.category='incall' INTO OUTFILE '$current_mysql_temporary_file' FIELDS TERMINATED BY '|' OPTIONALLY ENCLOSED BY '';"		
		/usr/bin/mysql --defaults-file=/etc/mysql/debian.cnf asterisk -e "$current_mysql_request"
		current_user_incall_data=$(cat $current_mysql_temporary_file)
		rm $current_mysql_temporary_file
	fi

	#LANGUAGE
	current_user_language="fr_FR"

	#ALL DATA
	all_current_user_data="$current_user_features_data|$current_user_voicemail_data|$current_user_incall_data|$current_user_language"
	echo $all_current_user_data >> $mysql_final_user_file

done

#REPLACE ALL NULL DATA
sed -i 's/\\N//g' $mysql_final_user_file

#################################################
#
# EXPORT USERS DATA TO BE CREATED MANUALLY
#
#################################################

#################################################
# CUSTOM PROTOCOL LINE
#################################################
#VARIABLES
mysql_REQUEST="SELECT firstname, lastname, number FROM userfeatures WHERE protocol!='sip' INTO OUTFILE '/tmp/tmp_users_custom_protocol_line.csv' FIELDS TERMINATED BY '|' OPTIONALLY ENCLOSED BY '';"
mysql_final_user_file="/root/Migration-1.1-to-12/manual_users_custom_protocol_line.csv"
mysql_temporary_user_file="/tmp/tmp_users_custom_protocol_line.csv"

#WORK
exec_MySQL_REQUEST "$mysql_REQUEST" "$mysql_temporary_user_file"
move_MySQL_RESULT $mysql_final_user_file $mysql_temporary_user_file


#################################################
# CUSTOM RING SECONDS
#################################################
#VARIABLES
mysql_REQUEST="SELECT firstname, lastname, number FROM userfeatures WHERE ringseconds!='30' INTO OUTFILE '/tmp/tmp_users_ringseconds.csv' FIELDS TERMINATED BY '|' OPTIONALLY ENCLOSED BY '';"
mysql_final_user_file="/root/Migration-1.1-to-12/manual_users_ringseconds.csv"
mysql_temporary_user_file="/tmp/tmp_users_ringseconds.csv"

#WORK
exec_MySQL_REQUEST "$mysql_REQUEST" "$mysql_temporary_user_file"
move_MySQL_RESULT $mysql_final_user_file $mysql_temporary_user_file


#################################################
# CUSTOM SIMULT CALLS
#################################################
#VARIABLES
mysql_REQUEST="SELECT firstname, lastname, number FROM userfeatures WHERE simultcalls!='5' INTO OUTFILE '/tmp/tmp_users_simultcalls.csv' FIELDS TERMINATED BY '|' OPTIONALLY ENCLOSED BY '';"
mysql_final_user_file="/root/Migration-1.1-to-12/manual_users_simultcalls.csv"
mysql_temporary_user_file="/tmp/tmp_users_simultcalls.csv"

#WORK
exec_MySQL_REQUEST "$mysql_REQUEST" "$mysql_temporary_user_file"
move_MySQL_RESULT $mysql_final_user_file $mysql_temporary_user_file

#################################################
# CUSTOM SUBROUTINE
#################################################
#VARIABLES
mysql_REQUEST="SELECT firstname, lastname, number FROM userfeatures WHERE preprocess_subroutine!='' INTO OUTFILE '/tmp/tmp_users_subroutine.csv' FIELDS TERMINATED BY '|' OPTIONALLY ENCLOSED BY '';"
mysql_final_user_file="/root/Migration-1.1-to-12/manual_users_subroutine.csv"
mysql_temporary_user_file="/tmp/tmp_users_subroutine.csv"

#WORK
exec_MySQL_REQUEST "$mysql_REQUEST" "$mysql_temporary_user_file"
move_MySQL_RESULT $mysql_final_user_file $mysql_temporary_user_file

#################################################
# CUSTOM MUSIC ON HOLD
#################################################
#VARIABLES
mysql_REQUEST="SELECT firstname, lastname, number FROM userfeatures WHERE musiconhold!='' AND musiconhold!='default' INTO OUTFILE '/tmp/tmp_users_musiconhold.csv' FIELDS TERMINATED BY '|' OPTIONALLY ENCLOSED BY '';"
mysql_final_user_file="/root/Migration-1.1-to-12/manual_users_musiconhold.csv"
mysql_temporary_user_file="/tmp/tmp_users_musiconhold.csv"

#WORK
exec_MySQL_REQUEST "$mysql_REQUEST" "$mysql_temporary_user_file"
move_MySQL_RESULT $mysql_final_user_file $mysql_temporary_user_file

#################################################
# CUSTOM DIALACTION
#################################################
#VARIABLES
mysql_REQUEST="SELECT firstname, lastname, number, event, action, actionarg1, actionarg2 FROM dialaction, userfeatures WHERE category='user' AND categoryval=id AND action!='none' ORDER BY number ASC, event INTO OUTFILE '/tmp/tmp_users_dialaction.csv' FIELDS TERMINATED BY '|' OPTIONALLY ENCLOSED BY '';"
mysql_final_user_file="/root/Migration-1.1-to-12/manual_users_dialaction.csv"
mysql_temporary_user_file="/tmp/tmp_users_dialaction.csv"

#WORK
exec_MySQL_REQUEST "$mysql_REQUEST" "$mysql_temporary_user_file"
move_MySQL_RESULT $mysql_final_user_file $mysql_temporary_user_file

#################################################
# CUSTOM FUNCKEY
#################################################
#VARIABLES
mysql_REQUEST="SELECT firstname, lastname, number, fknum, exten, typeextenumbers, typevalextenumbers, label, supervision FROM userfeatures, phonefunckey WHERE userfeatures.id=phonefunckey.iduserfeatures ORDER BY number, fknum INTO OUTFILE '/tmp/tmp_users_funckey.csv' FIELDS TERMINATED BY '|' OPTIONALLY ENCLOSED BY '';"
mysql_final_user_file="/root/Migration-1.1-to-12/manual_users_funckey.csv"
mysql_temporary_user_file="/tmp/tmp_users_funckey.csv"

#WORK
exec_MySQL_REQUEST "$mysql_REQUEST" "$mysql_temporary_user_file"
move_MySQL_RESULT $mysql_final_user_file $mysql_temporary_user_file

#################################################
# INCALL NOT ON USER
#################################################
#VARIABLES
mysql_REQUEST="SELECT incall.exten, action, actionarg1, actionarg2 FROM incall, dialaction WHERE dialaction.categoryval=incall.id AND dialaction.category='incall' AND action!='user' INTO OUTFILE '/tmp/tmp_incall.csv' FIELDS TERMINATED BY '|' OPTIONALLY ENCLOSED BY '';"
mysql_final_user_file="/root/Migration-1.1-to-12/manual_incall.csv"
mysql_temporary_user_file="/tmp/tmp_incall.csv"

#WORK
exec_MySQL_REQUEST "$mysql_REQUEST" "$mysql_temporary_user_file"
move_MySQL_RESULT $mysql_final_user_file $mysql_temporary_user_file

#################################################
# VOICEMAIL NOT ON USER
#################################################
#VARIABLES
mysql_REQUEST="SELECT fullname, mailbox FROM voicemail WHERE voicemail.uniqueid NOT IN (SELECT voicemailid FROM userfeatures) INTO OUTFILE '/tmp/tmp_voicemail.csv' FIELDS TERMINATED BY '|' OPTIONALLY ENCLOSED BY '';"
mysql_final_user_file="/root/Migration-1.1-to-12/manual_voicemail.csv"
mysql_temporary_user_file="/tmp/tmp_voicemail.csv"

#WORK
exec_MySQL_REQUEST "$mysql_REQUEST" "$mysql_temporary_user_file"
move_MySQL_RESULT $mysql_final_user_file $mysql_temporary_user_file
