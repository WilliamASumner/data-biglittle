# plot.py
# Creates a plot of the data from analyze.py
from __future__ import print_function
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Wedge, Polygon # shapes
from matplotlib.collections import PatchCollection

import numpy as np

import sys

from sim import solveConfigModel
from preprocess import parseAndCalcEnergy,loadTypes
from data_plot import siteScatterPlot

def graphShape(time,energy,ax,size=1):
    if ax is None:
        return
    offsetFactor = 0.1
    ax.annotate('Optimal Config', xy=(time, energy), xytext=(time+offsetFactor, energy+offsetFactor),
            arrowprops=dict(facecolor='black', shrink=0.01))

def graphOptimal(timeAndEnergy,coreConfigs,solMatrix,outputPrefix="graphs/"):
    phases = loadTypes[0:len(loadTypes)-1]

    fig,axs = siteScatterPlot(timeAndEnergy,coreConfigs,site='amazon',axes=None,figure=None,errorBars=False)
    for p,phase in enumerate(phases):
        graphShape(solMatrix['amazon'][phase][0],solMatrix['amazon'][phase][1],axs[p],size=100)
    plt.show()

def main():
    timeAndEnergy,coreConfigs = parseAndCalcEnergy(filePrefix="sim-data",iterations=20)
    solMatrix = solveConfigModel(timeAndEnergy,coreConfigs) # for sim-data
    graphOptimal(timeAndEnergy,coreConfigs,solMatrix)



if __name__ == '__main__':
    main()

