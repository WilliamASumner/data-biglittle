#!/bin/bash
CURR_DIR="/home/odroid/data-collector"
BBENCH_DIR="/home/odroid/bbench-3.0"
STHHAMP_DIR="/home/odroid/experimental-platform-software"
MONOUT_DIR="$CURR_DIR/powmon-data"
JSON_DIR="$CURR_DIR/json-data"
SUFFIX="all"

sigint() {
	echo "signal INT caught, cleaning up"
	echo "killing cdatalog"
	kill `pgrep cdatalog`

	echo "killing firefox"
	kill `pgrep firefox`

	mv ~/Downloads/info.txt $JSON_DIR/$2-$SUFFIX.json # save bbench output

	exit 0
}

# Startup checks
if [ "$EUID" -ne 0 ]; then
	echo "Please run as 'sudo $0 [...]'"
	exit
elif ! [[ `lsmod | grep perf` ]]; then
	echo "Error: perf kernel module not found."
	echo "please run sudo insmod -f $STHHAMP_DIR/datalogging_code/perf.ko"
	exit
elif [ $# -lt 2 ]; then
	echo "not enough args, missing either core configuration or filename"
	echo "usage: sudo $0 [core-config] [output-file]"
	exit
fi

trap 'sigint' SIGINT 

# Preprocessing 
#TODO add more configurations 'xB-yL'
if [[ `echo $1 | grep 0-3` ]]; then # running on all little
	echo "little configuration detected"
	SUFFIX="little"
elif [[ `echo $1 | grep 4-7` ]]; then # running on all little
	echo "big configuration detected"
	SUFFIX="big"
elif ! [[ `echo $1 | grep 0-7` ]]; then # it's some new config
	echo "unknown configuration detected"
	SUFFIX="$1"
fi

# start up perf (and firefox) in the background
echo "Starting up firefox with cores: $1..."
echo "sudo -u odroid taskset -c $1 firefox $BBENCH_DIR/index.html &"
sudo -u odroid taskset -c $1 firefox "$BBENCH_DIR/index.html" &
#perf options:[freq (Hz)] [timestamp] [per-thread] [addresses]
#perf record -F 99 --call-graph dwarf -T -s -d -- sudo -u odroid firefox "$BBENCH_DIR/index.html" &

# start up the southhampton monitor
# options are: [outputfile] [period (us)] [use-pmcs] [performance counters...]
echo "Starting southhampton monitor"
echo "$STHHAMP_DIR/datalogging_code/cdatalog $MONOUT_DIR/$2-$SUFFIX 10000 1 0x08 0x16 0x60 0x61 0x08 0x40 0x41 0x14 0x50 0x51 &"
"$STHHAMP_DIR/datalogging_code/cdatalog" "$MONOUT_DIR/$2-$SUFFIX" 10000 1 0x08 0x16 0x60 0x61 0x08 0x40 0x41 0x14 0x50 0x51 &

wait `pgrep firefox` # wait until firefox is done

kill `pgrep cdatalog` # try killing the monitor just to be sure

mv ~/Downloads/info.txt "$JSON_DIR/$2-$SUFFIX.json"
