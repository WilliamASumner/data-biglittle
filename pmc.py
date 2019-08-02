# pmc.py
# Reads in data from powmon
# and calculates the energy from the Power data
# Written by Will Sumner
import matplotlib.pyplot as plt
import numpy as np
from scipy import integrate
import sys

events=dict()
# Counters for both clusters
events['0x08'] = "Instructions"

# Counters for A15
events['0x40'] = "L1 Read"
events['0x41'] = "L1 Write"
events['0x14'] = "L1 Instr Access"
events['0x50'] = "L2 Data Read"
events['0x51'] = "L2 Data Write"

# Counters for A7
events['0x16'] = "L2 Data Access"
events['0x60'] = "Bus Access Read"
events['0x61'] = "Bus Access Write"

def read_data(filename):
    data = np.genfromtxt(filename,
           delimiter='\t',
           names=True,
           filling_values=0)
    return data

def calc_energy(powArr,timeArr):
    return integrate.simps(powArr,timeArr) #  calculates in mJ (W*ms)

def main():
    if (len(sys.argv) != 2):
        print("error: not enough arguments")
        return

    data = read_data(sys.argv[1])
    return data
if __name__ == "__main__":
    data = main()
