#!/bin/bash

FILEPREFIX=$1

declare -a configs governors iterconfig itergovernor # declare arrays
configs=("4l-0b" "4l-4b" "0l-4b") # all core configs to test with
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
	for (( i=1; i <= 3; i++ ))
	do
		x=$( echo "$RANDOM % 3" | bc )
		array_contains iterconfig ${configs["$x"]}
		while [ $? -eq 0 ]; do
			x=$( echo "$RANDOM % 3" | bc )
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
if [ -z "$FILEPREFIX" ]; then # if they forget to use a output prefix... 
	FILEPREFIX="output" # punish them with this vague one
fi

for i in {1..1}; do # for each iteration
	echo "iteration $i"
	gen_itergovernor

	# for each governor, could be for each config first,
	# but the idea behind looping through various configs 
	# in the inner loop is to possiblity that caching will help a config
	# since it will not be run consecutively 
	for gov in "pp"; do #${itergovernor[@]}; do  # for each governor, configs could be looped through first,
		gen_iterconfig
		for config in "4l-0b"; do #${iterconfig[@]}; do
			echo "running ./run.sh $config $FILEPREFIX $gov"
			./run.sh $config $FILEPREFIX $gov
			RET_VAL=$?
			if [[ "$RETVAL" == "1" ]]; then # run.sh didn't like something...
				echo "run.sh exited with an error, see above output"
				exit
			elif [[ "$RETVAL" == "2" ]]; then # run.sh was hit with a ctrl-c
				echo  "run.sh caught a SIGINT, exiting..."
				exit
			fi
		done
	done
done
