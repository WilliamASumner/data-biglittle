#!/bin/bash

FILEPREFIX=$1
ITERATIONS=$2

usage () {
    echo "$0 [file-prefix=output] [num-iterations=10]"
    exit 0
}

declare -a configs governors iterconfig itergovernor # declare arrays
configs=("4l-0b" "4l-4b" "0l-4b" "4l-1b" "4l-2b" "2l-0b" "1l-0b" "0l-2b" "0l-1b") # all core configs to test with
governors=("pi" "ii" "ip" "pp") # all core configs to test with

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

gen_iterconfig() { # generate a permutation of the configs
	iterconfig=()
	for (( i=1; i <= 9; i++ ))
	do
		x=$( echo "$RANDOM % 9" | bc )
		array_contains iterconfig ${configs["$x"]}
		while [ $? -eq 0 ]; do
			x=$( echo "$RANDOM % 9" | bc )
			array_contains iterconfig ${configs["$x"]}
		done
		iterconfig=("${iterconfig[@]}" ${configs["$x"]})
	done
}

gen_itergovernor() { # generate a permutation of the governors
	itergovernor=()
	for (( i=1; i <= 4; i++ ))
	do
		x=$( echo "$RANDOM % 4" | bc )
		array_contains itergovernor ${governors["$x"]}
		while [ $? -eq 0 ]; do
			x=$( echo "$RANDOM % 4" | bc )
			array_contains itergovernor ${governors["$x"]}
		done
		itergovernor=("${itergovernor[@]}" ${governors["$x"]})
	done
}

#startup checks
if [[ "$1" == "-h" ]]; then # simple -h check, no fancy getopt
    usage
fi
if [ -z "$FILEPREFIX" ]; then # if they forget to use a prefix... 
	FILEPREFIX="output" # punish them with this vague one
	echo "WARNING: using prefix output" # warn them of their mistake
fi
if [ -z "$ITERATIONS" ]; then # if no iterations specified
	ITERATIONS=10 # use 10
	echo "WARNING: using 10 iterations" # warn them about this
fi

if [ -f errlog ]; then # if old error log exists, save it
	mv errlog errlog.old
fi


for (( iter=1; iter <=$ITERATIONS; iter++ )); do
	echo "iteration $iter"
	#gen_itergovernor

	# for each governor, could be for each config first,
	# but the idea behind looping through various configs 
	# in the inner loop is to possiblity that caching will help a config
	# since it will not be run consecutively 
	for gov in "ii"; do #${itergovernor[@]}; do  # for each governor, configs could be looped through first,
		gen_iterconfig
		for config in ${iterconfig[@]}; do
			echo "iteration: $iter"
			echo "running ./run.sh $config $FILEPREFIX $gov"
			./run.sh $config $FILEPREFIX $gov >> errlog 2>> errlog
			RETVAL=$?
			if [[ "$RETVAL" == "1" ]]; then # run.sh didn't like something...
				echo "run.sh exited with an error, see log output"
				tail -n 5 errlog
				exit 1
			elif [[ "$RETVAL" == "2" ]]; then # run.sh was hit with a ctrl-c
				echo  "run.sh caught a SIGINT, exiting..."
				exit 0
			fi
		done
	done
	sleep 180 # constantly using the ethernet gives kevent dropped errors after a while...
done
