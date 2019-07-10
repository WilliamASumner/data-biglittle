import sys
import argparse

# List of things to run
# perf record
# firefox to bbench index.html
# bbench then bbench
# collect

parser = argparse.ArgumentParser()

# Options to pass to perf
parser.add_argument('-f','--foo')

# Options to pass to 
