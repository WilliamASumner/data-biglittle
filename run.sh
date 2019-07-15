#!/bin/bash
CURR_DIR="/home/odroid/data-collector"
BBENCH_DIR="/home/odroid/bbench-3.0"
STHHAMP_DIR="/home/odroid/experimental-platform-software"
MONOUT_DIR="$CURR_DIR/powmon-data"
JSON_DIR="$CURR_DIR/json-data"
SUFFIX="all"
PROG_NAME=$0
CORE_CONFIG=$1
OUTPUT_FILE=$2

give_usage() {
	echo "usage: sudo $PROG_NAME [core-config:{x}B-{y}L] [output-filename]" >&2
	exit
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

sigint() {
	echo "signal INT caught, cleaning up"
	echo "killing cdatalog"
	kill `pgrep cdatalog`

	echo "killing firefox"
	kill `pgrep firefox`

	mv ~/Downloads/info.txt $JSON_DIR/$OUTPUT_FILE-$SUFFIX.json # save bbench output

	exit 0
}

# Startup checks
if [ "$EUID" -ne 0 ]; then
	echo "error: sudo privileges needed by this script"
	give_usage
elif ! [[ `lsmod | grep perf` ]]; then
	echo "error: perf kernel module not found."
	echo "please run sudo insmod -f $STHHAMP_DIR/datalogging_code/perf.ko"
	give_usage
elif [ $# -lt 2 ]; then
	echo "error: not enough args"
	give_usage
elif [[ `check_core_config $CORE_CONFIG` ]]; then
	echo "error: invalid core configuration $CORE_CONFIG"
	give_usage
fi
if [[ $OUTPUT_FILE == "test" ]]; then
	echo "performing a dry run..."
fi

trap 'sigint' SIGINT 

# Preprocessing 
core_config_flag=$(get_config $CORE_CONFIG)
SUFFIX=$core_config_flag

# start up firefox in the background
echo "starting up firefox with cores: $core_config_flag..."
echo "sudo -u odroid taskset -c $core_config_flag firefox $BBENCH_DIR/index.html &"
if ! [[ $OUTPUT_FILE == "test" ]]; then
	sudo -u odroid taskset -c $core_config_flag firefox "$BBENCH_DIR/index.html" &
fi

#perf options:[freq (Hz)] [timestamp] [per-thread] [addresses]
#perf record -F 99 --call-graph dwarf -T -s -d -- sudo -u odroid firefox "$BBENCH_DIR/index.html" &

# start up the southhampton monitor
# options are: [outputfile] [period (us)] [use-pmcs] [performance counters...]
echo "starting southhampton monitor"
echo "$STHHAMP_DIR/datalogging_code/cdatalog $MONOUT_DIR/$OUTPUT_FILE-$SUFFIX 10000 1 0x08 0x16 0x60 0x61 0x08 0x40 0x41 0x14 0x50 0x51 &"
if ! [[ $OUTPUT_FILE == "test" ]]; then
	"$STHHAMP_DIR/datalogging_code/cdatalog" "$MONOUT_DIR/$OUTPUT_FILE-$SUFFIX" 10000 1 0x08 0x16 0x60 0x61 0x08 0x40 0x41 0x14 0x50 0x51 &

	wait `pgrep firefox` # wait until firefox is done
	kill `pgrep cdatalog` # try killing the monitor just to be sure
	mv ~/Downloads/info.txt "$JSON_DIR/$OUTPUT_FILE-$SUFFIX.json"
fi

