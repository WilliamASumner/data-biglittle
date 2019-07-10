#!/bin/bash
CURR_DIR="/home/odroid/data-collector"
BBENCH_DIR="/home/odroid/bbench-3.0"
STHHAMP_DIR="/home/odroid/experimental-platform-software"
MONOUT_DIR="$CURR_DIR/powmon"

sigint() {
	echo "signal INT caught, cleaning up"
	echo "killing cdatalog"
	kill `pgrep cdatalog`

	echo "killing firefox"
	kill `pgrep firefox`

	exit 0
}

if [ $# -lt 2 ]; then
	echo "not enough args"
	echo "usage: ./$0 [core config] [outputfolder]"
	exit
fi


trap 'sigint' SIGINT 

# run firefox on the bbench suite

# start up perf (and firefox) in the background
echo "Starting up firefox with cores: $1..."
sudo -u odroid taskset -c $1 firefox "$BBENCH_DIR/index.html" &
# perf options:[freq (Hz)] [timestamp] [per-thread] [addresses]
#perf record -F 99 --call-graph dwarf -T -s -d -- sudo -u odroid firefox "$BBENCH_DIR/index.html" &

# start up the southhampton monitor
# options are: [outputfile] [period (us)] [use-pmcs] [performance counters...]
echo "Starting southhampton monitor"
"$STHHAMP_DIR/datalogging_code/cdatalog" "$MONOUT_DIR/$2" 10000 1 0x08 0x16 0x60 0x61 0x08 0x40 0x41 0x14 0x50 0x51 &

wait `pgrep firefox` # wait until firefox is done

kill `pgrep cdatalog`


#FIXME - find a way to get data out of firefox page, maybe with an addon
#mv "$BBENCH_DIR/results.html" "$CURR_DIR/results.html"
