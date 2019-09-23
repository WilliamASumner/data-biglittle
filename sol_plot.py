# sol_plot.py
# Creates a plot of the solution from sim.py and the data from preprocess.py
from __future__ import print_function
import matplotlib.pyplot as plt
from matplotlib.patches import Ellipse # shapes

import numpy as np

import sys

from sim import solveConfigModel
from preprocess import parseAndCalcEnergy,loadTypes,phases,avgMatrix,sites
from data_plot import siteScatterPlot,comparisonBar,generalBar

def getAxDims(ax,fig):
    if ax is None or fig is None:
        return (0,0)
    bbox = ax.get_window_extent().transformed(fig.dpi_scale_trans.inverted())
    width, height = bbox.width*fig.dpi,bbox.height*fig.dpi
    return (width,height)

def graphShape(time,energy,ax,fig,size=1):
    if ax is None:
        return
    x0, x1  = ax.get_xlim()
    y0, y1  = ax.get_ylim()
    scaleY  = abs(y1-y0)/10.0
    scaleX  = abs(x1-x0)/10.0
    dimX,dimY = getAxDims(ax,fig)
    maxd = max(dimY,dimX)
    ellipse = Ellipse((time,energy),maxd/dimX*size*scaleX,maxd/dimY*size*scaleY)
    ellipse.set_facecolor((0.9,0.1,0.1,0.4))
    ax.add_artist(ellipse)
    #ax.annotate('Optimal Config', xy=(time, energy), xytext=(time+textOffset, energy+textOffset),
            #arrowprops=dict(facecolor='black', shrink=0.01))

def graphOptimal(timeAndEnergy,coreConfigs,solMatrix,site='amazon',outputPrefix="graphs/",writeOut=False):
    fig,axes = siteScatterPlot(timeAndEnergy,coreConfigs,site=site,axes=None,figure=None,errorBars=False)
    fig.suptitle(site + " Optimal Loadtime and Energy",y=1.01,fontsize='xx-large')

    for p,phase in enumerate(phases):
        if solMatrix[site][phase] is None:
            continue
        graphShape(solMatrix[site][phase][0],solMatrix[site][phase][1],axes[p],fig,size=0.3)
    fig.tight_layout()

    if writeOut:
        plt.savefig(outputPrefix+site+"-optimal-annotated.pdf",bbox_inches="tight")
        plt.clf()
    else: 
        plt.show()
    plt.close(fig)


def graphAbsComparison(timeAndEnergy,solMatrix,site='amazon',outputPrefix="graphs/",writeOut=False):
    timeData   = np.zeros((2,len(phases)))
    energyData = np.zeros((2,len(phases)))

    timeErr   = np.zeros(len(phases))
    energyErr = np.zeros(len(phases))

    for p,phase in enumerate(phases):
        if solMatrix[site][phase] is None:
            continue
        timeData[0][p]   = solMatrix[site][phase][0] # optimal values calculated for the phase
        energyData[0][p] = solMatrix[site][phase][1] # offset on top of old data
        timeData[1][p]   = np.mean(timeAndEnergy['4l-4b']['ii'][site][phase]['loadtime'])
        energyData[1][p] = np.mean(timeAndEnergy['4l-4b']['ii'][site][phase]['energy'])

        timeErr[p]    = np.std(timeAndEnergy['4l-4b']['ii'][site][phase]['loadtime'])
        energyErr[p]  = np.std(timeAndEnergy['4l-4b']['ii'][site][phase]['energy'])

    fig,axes = comparisonBar(timeData,energyData,timeErrBars=timeErr,energyErrBars=energyErr)

    fig.suptitle(site + " Oracle and Baseline Comparison (absolute)",y=1.01,fontsize='xx-large')
    axes.set_xticklabels(phases)
    axes.set_ylabel('Average Load Time (ms) per Phase')
    energyAxis = axes.twinx()
    energyAxis.set_ylabel('Average Energy (mJ) per Phase')

    fig.tight_layout()
    if writeOut:
        plt.savefig(outputPrefix+site+"-comparison-abs.pdf",bbox_inches="tight")
        plt.clf()
    else: 
        plt.show()
    plt.close(fig)


def graphRelComparison(timeAndEnergy,solMatrix,site='amazon',outputPrefix="graphs/",writeOut=False):
    timeData   = np.zeros((1,len(phases)))
    energyData = np.zeros((1,len(phases)))

    timeErr   = np.zeros(len(phases))
    energyErr = np.zeros(len(phases))

    for p,phase in enumerate(phases):
        if solMatrix[site][phase] is None:
            continue
        timeData[0][p]   = np.mean(timeAndEnergy['4l-4b']['ii'][site][phase]['loadtime']) / solMatrix[site][phase][0] # optimal values calculated for the phase
        energyData[0][p] = np.mean(timeAndEnergy['4l-4b']['ii'][site][phase]['energy']) /solMatrix[site][phase][1] # offset on top of old data

        timeErr[p]    = 0 # TODO find a way to scale error
        energyErr[p]  = 0

    fig,axes = comparisonBar(timeData,energyData,timeErrBars=timeErr,energyErrBars=energyErr)

    fig.suptitle(site + " Oracle and Baseline Comparison (relative)",y=1.01,fontsize='xx-large')
    axes.set_xticklabels(phases)
    axes.set_ylabel('Times Improvement over baseline')

    fig.tight_layout()
    if writeOut:
        plt.savefig(outputPrefix+site+"-comparison-rel.pdf",bbox_inches="tight")
        plt.clf()
    else: 
        plt.show()
    plt.close(fig)

def graphModelTime(solMatrix,outputPrefix="graphs/",writeOut=False):
    loadTimes = np.zeros(len(sites)) # displaying solution times of all phases
    for s,site in enumerate(sites):
        if not(solMatrix[site][phases[0]] is None):
            loadTimes[s] = solMatrix[site][phases[0]][3] # only need one time for whole site
    (fig,axes) = generalBar(loadTimes*1000,sites)

    fig.suptitle("Site Model Optimization Times",y=1.01,fontsize='xx-large')
    axes.set_ylabel('Time to Optimize Model (ms)')
    axes.set_xticklabels(sites)
    fig.tight_layout()
    if writeOut:
        plt.savefig(outputPrefix+"modeltimes.pdf",bbox_inches="tight")
        plt.clf()
    else: 
        plt.show()
    plt.close(fig)



def main():
    timeAndEnergy,coreConfigs = parseAndCalcEnergy(filePrefix="sim-data",iterations=20)
    timeAndEnergySet = avgMatrix(timeAndEnergy) # avg all iterations
    solMatrix = solveConfigModel(timeAndEnergySet,coreConfigs,logFilename='sol_plot.log') # optimize model
    verbose = True

    for site in sites:
        if verbose:
            print(site)
            print("optimal")
        graphOptimal(timeAndEnergySet,coreConfigs,solMatrix,site=site,writeOut=True)
        if verbose:
            print("relative comparison")
        graphRelComparison(timeAndEnergy,solMatrix,site=site,writeOut=True)
        if verbose:
            print("absolute comparison")
        graphAbsComparison(timeAndEnergy,solMatrix,site=site,writeOut=True)
    if verbose:
        print("model solving times")
    graphModelTime(solMatrix,writeOut=True)

if __name__ == '__main__':
    main()

