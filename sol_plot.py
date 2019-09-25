# sol_plot.py
# Creates a plot of the solution from sim.py and the data from preprocess.py
from __future__ import print_function
import matplotlib.pyplot as plt
from matplotlib.patches import Ellipse # shapes

import numpy as np

import sys
import data_plot

from sim import solveConfigModel
from preprocess import parseAndCalcEnergy,avgMatrix
from preprocess import loadTypes,phases,phasesSimple,sites,phaseMap
from data_plot import siteScatterPlot,comparisonBar,genericCompBar,generalBar,newline

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

    colors = [[] for i in range(4)] # two layers of color for each data set

    for p,phase in enumerate(phases):
        if solMatrix[site][phase] is None:
            continue
        baseTime   = timeAndEnergy['4l-4b']['ii'][site][phase]['loadtime'] # baseline values
        baseEnergy = timeAndEnergy['4l-4b']['ii'][site][phase]['energy']

        minTime = min(baseTime,solMatrix[site][phase][0])
        minEnergy = min(baseTime,solMatrix[site][phase][1])

        if minTime == baseTime:
            colors[0].append(data_plot.blue) # baseTime gets a blue color
            colors[1].append(data_plot.orange)
        else:
        #elif solMatrix[site][phase][0] == baseTime:
            colors[0].append(data_plot.orange)
            colors[1].append(data_plot.blue)
       # else:
       #     colors[0].append(data_plot.grey) # grey out matches
       #     colors[1].append(data_plot.grey)

        if minEnergy == baseEnergy:
            colors[2].append(data_plot.green)
            colors[3].append(data_plot.red)
        #elif solMatrix[site][phase][1] == baseEnergy:
        else:
            colors[2].append(data_plot.red)
            colors[3].append(data_plot.green)
        #else:
        #    colors[2].append(data_plot.grey) # grey out matches
        #    colors[3].append(data_plot.grey)


        timeData[0][p]   = minTime # bottom values, smaller of the two
        energyData[0][p] = minEnergy

        timeData[1][p]   = max(baseTime,solMatrix[site][phase][0]) - minTime
        energyData[1][p] = max(baseEnergy,solMatrix[site][phase][0]) - minEnergy

    fig,axes,energyAxis = comparisonBar(timeData,energyData,twoAxes=True,colors=colors)


    fig.suptitle(site + " Oracle and Baseline Comparison (absolute)",y=1.01,fontsize='xx-large')
    axes.set_xticklabels(phasesSimple)
    axes.set_ylabel('Average Load Time (ms) per Phase')
    energyAxis.set_ylabel('Average Energy (mJ) per Phase')
    #axes.legend(handles,('Oracle Time','Base time','Oracle Energy','Base Energy')) # TODO fix this to be generic

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
        timeData[0][p]   = timeAndEnergy['4l-4b']['ii'][site][phase]['loadtime'] / solMatrix[site][phase][0] # optimal values calculated for the phase
        energyData[0][p] = timeAndEnergy['4l-4b']['ii'][site][phase]['energy'] /solMatrix[site][phase][1] # offset on top of old data

        timeErr[p]    = 0 # TODO find a way to scale error
        energyErr[p]  = 0

    fig,axes,energyAxis = comparisonBar(timeData,energyData,timeErrBars=timeErr,energyErrBars=energyErr)

    fig.suptitle(site + " Oracle and Baseline Comparison (relative)",y=1.01,fontsize='xx-large')
    axes.set_xticklabels(phasesSimple)
    axes.set_ylabel('Efficiency improvement over baseline')

    l = newline([0,1],[1,1],axes) # draw a line at the breakeven point
    l.set_linestyle('dashed')
    l.set_color('black')

    fig.tight_layout()
    if writeOut:
        plt.savefig(outputPrefix+site+"-comparison-rel.pdf",bbox_inches="tight")
        plt.clf()
    else: 
        plt.show()
    plt.close(fig)


def graphComparisonAll(timeAndEnergy,solMatrix,outputPrefix="graphs/",writeOut=False):
    values = np.zeros((1,3,len(sites)))
# General shape is (layers,side by side bars (runs),number of data points per run)

    

    for s,site in enumerate(sites):
        timeData = np.zeros(len(phases))
        energyData = np.zeros(len(phases))

        for p,phase in enumerate(phases):
            if solMatrix[site][phase] is None:
                timeData[p] = np.NaN
                energyData[p] = np.NaN
            else:
                timeData[p]   = np.mean(timeAndEnergy['4l-4b']['ii'][site][phase]['loadtime']) / solMatrix[site][phase][0] # optimal values calculated for the phase
                energyData[p] = np.mean(timeAndEnergy['4l-4b']['ii'][site][phase]['energy']) /solMatrix[site][phase][1] # offset on top of old data

        values[0][0][s] = np.nanmin(timeData) # min val
        values[0][1][s] = np.nanmax(timeData) # max val
        values[0][2][s] = np.nanmean(timeData) # avg val

    fig,axes,handles = genericCompBar(values)

    fig.suptitle(site + " Oracle and Baseline Comparison (relative)",y=1.01,fontsize='xx-large')
    axes.set_xticklabels(phasesSimple)
    axes.set_ylabel('Efficiency improvement over baseline')

    fig.tight_layout()
    if writeOut:
        plt.savefig(outputPrefix+site+"-comparison-rel.pdf",bbox_inches="tight")
        plt.clf()
    else: 
        plt.show()
    plt.close(fig)





def graphModelTime(solMatrix,outputPrefix="graphs/",timeParam='optimize',writeOut=False):
    if timeParam not in ['optimize','construction']:
        raise Exception('Invalid time parameter: \"{}\" either optimize or construction'.format(timeParam))
    loadTimes = np.zeros(len(sites)) # displaying solution times of all phases
    if timeParam == 'optimize':
        ind = 3
    else:
        ind = 4
    for s,site in enumerate(sites):
        if not(solMatrix[site][phases[0]] is None):
            loadTimes[s] = solMatrix[site][phases[0]][ind] # only need one time for whole site
    (fig,axes) = generalBar(loadTimes*1000,sites)

    if timeParam == 'optimize':
        fig.suptitle("Site Model Optimization Times",y=1.01,fontsize='xx-large')
    else:
        fig.suptitle("Site Model Construction Times",y=1.01,fontsize='xx-large')
    axes.set_ylabel('Time to Optimize Model (ms)')
    axes.set_xticklabels(sites)
    fig.tight_layout()
    if writeOut:
        plt.savefig(outputPrefix+"modeltimes-" + timeParam + ".pdf",bbox_inches="tight")
        plt.clf()
    else: 
        plt.show()
    plt.close(fig)



def main():
    timeAndEnergy,coreConfigs = parseAndCalcEnergy(filePrefix="sim-data",iterations=20)
    timeAndEnergySet = avgMatrix(timeAndEnergy) # avg all iterations
    solMatrix = solveConfigModel(timeAndEnergySet,coreConfigs,logFilename='gurobi_sol_plot.log') # optimize model
    verbose = True
    #graphComparisonAll(timeAndEnergy,solMatrix,outputPrefix="graphs/",writeOut=False)

    for site in sites:
        if verbose:
            print(site)
            print("optimal")
        graphOptimal(timeAndEnergySet,coreConfigs,solMatrix,site=site,writeOut=True)
        if verbose:
            print("relative comparison")
        graphRelComparison(timeAndEnergySet,solMatrix,site=site,writeOut=True)
        if verbose:
            print("absolute comparison")
        graphAbsComparison(timeAndEnergySet,solMatrix,site=site,writeOut=True)
    if verbose:
        print("model solving times")
    graphModelTime(solMatrix,timeParam='optimize',writeOut=True)
    if verbose:
        print("model construction times")
    graphModelTime(solMatrix,timeParam='construction',writeOut=True)

if __name__ == '__main__':
    main()

