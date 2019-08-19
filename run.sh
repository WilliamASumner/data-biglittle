#!/bin/bash

#set -e # stop on errors

HOME="/home/odroid"
CURR_DIR="/home/odroid/data-collector"
BBENCH_DIR="/home/odroid/bbench-3.0"
STHHAMP_DIR="/home/odroid/experimental-platform-software"

MONOUT_DIR="$CURR_DIR/powmon-data"
JSON_DIR="$CURR_DIR/json-data"
SUFFIX="all"

AVAIL_GOVS="/sys/devices/system/cpu/cpu0/cpufreq/scaling_available_governors"
BIG_CPU_GOV="/sys/devices/system/cpu/cpu0/cpufreq/scaling_governor"
LIL_CPU_GOV="/sys/devices/system/cpu/cpu7/cpufreq/scaling_governor"
OLD_BIG_CPU_GOV=""
OLD_LIL_CPU_GOV=""

DUMMY_SERVER_FILE="http://was42@tucunare.cs.pitt.edu:8080/index.html"

INTERNET_WAS_OFF="yes"
GDM_WAS_OFF="yes" 

PROFILE_SAMPLE_PERIOD_US=100000 #10Hz for Powmon

COMMAND_TO_RUN="python sel.py" # firefox $BBENCH_DIR/index.html 

PROG_NAME=$0
CORE_CONFIG=$1
OUTPUT_FILE=$2
GOV_STR=$3


give_usage() {
	echo -e \
"usage: sudo $PROG_NAME\t[core-config:{x}l-{y}b]\n\
\t\t\t[output-filename]\n\
\t\t\t[governors: pi,ip,pp,ii]" >&2
	exit 1
}

array_contains () {
	local array="$1[@]"
	local seeking=$2
	local in=1
	for element in "${!array}"; do
		if [[ $element == $seeking ]]; then
			in=0
			break
		fi
	done
	return $in
}

check_core_config() {
	if ! [[ `echo $1 | grep -i B` ]] || ! [[ `echo $1 | grep -i L` ]]; then # there's a missing b/l
		echo "error"
		return
	fi
	l=$( echo $1 | grep -io [0-9]*l | grep -o [0-9]* )
	b=$( echo $1 | grep -io [0-9]*b | grep -o [0-9]* )

	if [ "$l" -lt 0 ]; then
		echo "error: less than 0 little cores"
	elif [ "$b" -lt 0 ]; then
		echo "error: less than 0 big cores"
	elif [ "$l" -gt 4 ]; then
		echo "error: more than 4 little cores"
	elif [ "$b" -gt 4 ]; then
		echo "error: more than 4 big cores"
	elif [ "$l" -eq 0 ]; then
		if [ "$b" -eq 0 ]; then
			echo "error: no cores"
		fi
	fi
}

get_config() {
	l=$( echo $1 | grep -io [0-9]*l | grep -o [0-9]* )
	b=$( echo $1 | grep -io [0-9]*b | grep -o [0-9]* )
	lilStr=""
	bigStr=""

	if [ $l -eq 4 ]; then
		if [ $b -eq 4 ]; then
			echo "0-7"
			return
		else
			if [ $b -eq 0 ]; then
				echo "0-3"
				return
			else
				lilStr="0-3"
			fi
		fi
	elif [ $b -eq 4 ]; then
		if [ $l -eq 0 ]; then
			echo "4-7"
			return
		else
			bigStr="4-7"
		fi
	fi

	declare -a littles bigs
	if [ -z $lilStr ]; then
		for (( i=1; i<=$l; i++ )) # get lists of random cores
		do
			x=$( echo $RANDOM % 4 | bc )
			array_contains littles "$x"
			while [ $? -eq 0 ]; do
				x=$( echo $RANDOM % 4 | bc )
				array_contains littles "$x"
			done
			littles=("${littles[@]}" "$x")
		done
	fi

	if [ -z $bigStr ]; then
		for (( i=1; i<=$b; i++ ))
		do
			x=$( echo $RANDOM % 4 + 4 | bc )
			array_contains bigs "$x"
			while [ $? -eq 0 ]; do
				x=$( echo $RANDOM % 4 + 4 | bc )
				array_contains bigs "$x"
			done
			bigs=("${bigs[@]}" "$x")
		done
	fi

	declare -a lilSorted bigSorted

	if [ ${#littles[@]} -gt 0 ]; then
		IFS=$'\n' lilSorted=($(sort <<<"${littles[*]}"))
		unset IFS
		lilStr="${lilSorted[*]}"
	fi
	if [ ${#bigs[@]} -gt 0 ]; then
		IFS=$'\n' bigSorted=($(sort <<<"${bigs[*]}"))
		unset IFS
		bigStr="${bigSorted[*]}"
	fi

	if ! [ -z "$lilStr" ]; then
		if ! [ -z "$bigStr" ]; then
			config_str="$lilStr $bigStr"
		else
			config_str="$lilStr"
		fi
	else
		config_str="$bigStr"
	fi

	echo ${config_str// /,}
}

set_governor() {
	if ! [[ `cat $AVAIL_GOVS` ]]; then # no available governors
		echo "error: unable to read available governors"
		exit 1
	elif ! [[ `cat $AVAIL_GOVS | grep performance` ]]; then # no performance governor
		echo "error: no performance governor available"
		exit 1
	fi

	NEW_BIG_CPU_GOV="performance"
	NEW_LIL_CPU_GOV="performance"

	if [[ "$1" == "ip" ]]; then
		NEW_BIG_CPU_GOV="interactive"
		NEW_LIL_CPU_GOV="performance"
	elif [[ "$1" == "pi" ]]; then
		NEW_BIG_CPU_GOV="performance"
		NEW_LIL_CPU_GOV="interactive"
	elif [[ "$1" == "ii" ]]; then
		NEW_BIG_CPU_GOV="interactive"
		NEW_LIL_CPU_GOV="interactive"
	elif [[ "$1" == "pp" ]]; then
		NEW_BIG_CPU_GOV="performance"
		NEW_LIL_CPU_GOV="performance"
	else
		echo "error: invalid governor string"
		exit 1
	fi

	OLD_BIG_CPU_GOV=`cat $BIG_CPU_GOV` # save the old state
	OLD_LIL_CPU_GOV=`cat $LIL_CPU_GOV`

	if [ -z $OLD_BIG_CPU_GOV ]; then
		echo "error: unable to save big cluster governor"
	fi
	if [ -z $OLD_LIL_CPU_GOV ] ; then
		echo "error: unable to save little cluster governor"
	fi

	echo $NEW_BIG_CPU_GOV > "$BIG_CPU_GOV"
	echo $NEW_LIL_CPU_GOV > "$LIL_CPU_GOV"

	# governor did not change...
	if ! [[ `cat $BIG_CPU_GOV | grep $NEW_BIG_CPU_GOV` ]] || ! [[ `cat $LIL_CPU_GOV | grep $NEW_LIL_CPU_GOV` ]]; then
		echo "error: unable to change governor"
		exit 1
	fi
}

restore_governor() {
	if [ -z $OLD_BIG_CPU_GOV ]; then # couldn't save, don't try to restore
		return
	elif [ -z $OLD_LIL_CPU_GOV ] ; then
		return
	fi
	echo "restoring governors to $OLD_BIG_CPU_GOV and $OLD_LIL_CPU_GOV"

	echo $OLD_BIG_CPU_GOV > $BIG_CPU_GOV
	echo $OLD_LIL_CPU_GOV > $LIL_CPU_GOV
}

sigint() {
	echo "signal INT caught, cleaning up"
	echo "killing cdatalog..."
	kill `pgrep cdatalog`
	echo "killed"

	echo "killing python and selenium..."
	kill `pgrep python` # kill all the processes involved with selenium
	kill `pgrep chromedriver` #TODO find a simpler/cleaner way to do this
	kill `pgrep chromium-browse`
	kill `pgrep Xvfb`
	echo "killed"

	#echo "killing firefox"
	#if [[ `pgrep firefox` ]]; then
	#	kill `pgrep firefox`
	#fi

	if ! [ -f $CURR_DIR/output.json ]; then
		echo "error: '$COMMAND_TO_RUN' did not create a file called 'output.json'"
	else 
		echo "mv $CURR_DIR/output.json $JSON_DIR/$OUTPUT_FILE-$SUFFIX.json"
		mv $CURR_DIR/output.json $JSON_DIR/$OUTPUT_FILE-$SUFFIX.json
	fi
	echo "restoring governor..."
	restore_governor

	#if [[ "$INTERNET_WAS_OFF" == "no" ]]; then # restart internet if it was disabled by this script
	#	echo "ifconfig eth0 up"
	#	ifconfig eth0 up
	#fi

	#if [[ "$GDM_WAS_OFF" == "no" ]]; then # restart gdm if need be
	#	echo "service gdm3 start"
	#	service gdm3 start
	#fi
	exit 2 # want to return that we hit a ctrl-c
}

trap 'sigint' SIGINT 

# Startup checks
if [ "$EUID" -ne 0 ]; then
	echo "error: sudo privileges needed by this script"
	give_usage
elif ! [[ `lsmod | grep perf` ]]; then
	echo "error: perf kernel module not found."
	echo "please run sudo insmod -f $STHHAMP_DIR/datalogging_code/perf.ko"
	give_usage
elif [ $# -lt 3 ]; then
	echo "error: not enough args"
	give_usage
elif [[ `check_core_config $CORE_CONFIG` ]]; then
	echo "error: invalid core configuration $CORE_CONFIG"
	give_usage
fi



if [[ `service gdm3 status | grep running` ]]; then # gdm is being run, stop it
	GDM_WAS_OFF="no"
	#service gdm3 stop
	echo "please disable gdm"
	echo "example command: sudo service gdm3 stop"
	give_usage
fi

if [[ $OUTPUT_FILE == "test" ]]; then
	echo "performing a dry run..."
else 
	echo "contacting server..."
	NUM_RETRIES=20 # retry the connection a few times
	wget -q -O /dev/null $DUMMY_SERVER_FILE # try to load a test file from the server 
	RET_VAL=$?
	while ! [[ $NUM_RETRIES == "0" ]] && ! [[ $RET_VAL == "0" ]]; do # while we haven't exceeded our tries and have a bad return value
		sleep 0.5 # wait for a little
		echo "trying again to contact server..." 
		NUM_RETRIES=$(( $NUM_RETRIES - 1 ))
		wget -q -O /dev/null $DUMMY_SERVER_FILE # try to load a test file from the server 
		RET_VAL=$?
	done
	if ! [ $RET_VAL -eq 0 ]; then
		echo "error: unable to connect to server, error returned from wget was $RET_VAL"
		echo "trying using 'man wget' to find out more information"
		#INTERNET_WAS_OFF="no"
		#ifconfig eth0 down # old way was to disable internet and load from disk
		give_usage
	fi
	echo "Connected to server!"
fi

# Preprocessing 
core_config_flag=$(get_config $CORE_CONFIG)
ID=`mktemp -u XXXXXXXX`
SUFFIX="$CORE_CONFIG-$GOV_STR-$ID"


echo ""

echo "experiment id is $ID"
echo "starting up command with cores: $core_config_flag..."
echo "sudo -u odroid taskset -c $core_config_flag $COMMAND_TO_RUN &"

echo ""

if ! [[ $OUTPUT_FILE == "test" ]]; then # IF NOT A TEST
	echo "setting governor with str $GOV_STR..."
	set_governor $GOV_STR # check that it is in correct mode


    # start up the southhampton monitor
    # options are: [outputfile] [period (us)] [use-pmcs] [performance counters...]

	# assign the power monitor to core 0, which never turns off
	taskset -c 0 "$STHHAMP_DIR/datalogging_code/cdatalog" "$MONOUT_DIR/$OUTPUT_FILE-$SUFFIX" $PROFILE_SAMPLE_PERIOD_US 1 0x08 0x16 0x60 0x61 0x08 0x40 0x41 0x14 0x50 0x51 &

    # perf options: -F [freq (Hz)] -T [timestamp] -s [per-thread] -d [addresses]
	# start up command
	perf record -F 10 --call-graph fp -T -s -d -- sudo -u odroid taskset -c $core_config_flag $COMMAND_TO_RUN

	if [[ `pgrep cdatalog` ]]; then # if the power monitor hasn't finished yet
		echo "killing cdatalog..."
		pkill cdatalog # kill it
	fi

	if ! [ -f $CURR_DIR/output.json ]; then
		echo "error: '$COMMAND_TO_RUN' did not write out a json file"
	else 
		echo "mv $CURR_DIR/output.json $JSON_DIR/$OUTPUT_FILE-$SUFFIX.json"
		mv $CURR_DIR/output.json $JSON_DIR/$OUTPUT_FILE-$SUFFIX.json # save command output
	fi
	restore_governor

	#if [[ "$INTERNET_WAS_OFF" == "no" ]]; then # restart internet if it was disabled by this script
	#	echo "ifconfig eth0 up"
	#	ifconfig eth0 up
	#fi
	#if [[ "$GDM_WAS_OFF" == "no" ]]; then # restart gdm if need be
	#	echo "service gdm3 start"
	#	service gdm3 start
	#fi
else 
	echo "setting governor with str $GOV_STR..."
	set_governor $GOV_STR

	echo "starting southhampton monitor"
	echo "taskset -c 0 $STHHAMP_DIR/datalogging_code/cdatalog $MONOUT_DIR/$OUTPUT_FILE-$SUFFIX $PROFILE_SAMPLE_PERIOD_US 1 0x08 0x16 0x60 0x61 0x08 0x40 0x41 0x14 0x50 0x51 &"

	echo "starting command"
	echo "sudo -u odroid taskset -c $core_config_flag $COMMAND_TO_RUN &"

	echo "moving output file"
	echo "mv $CURR_DIR/output.json $JSON_DIR/$OUTPUT_FILE-$SUFFIX.json"

	restore_governor

	if [[ "$INTERNET_WAS_OFF" == "no" ]]; then # restart internet if it was disabled by this script
		echo "ifconfig eth0 up"
		#ifconfig eth0 up
	fi
	if [[ "$GDM_WAS_OFF" == "no" ]]; then # restart gdm if need be
		echo "service gdm3 start"
		service gdm3 start
	fi
fi
