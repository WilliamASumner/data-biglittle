# plot.py
# Creates a plot of the data from analyze.py
from __future__ import print_function
import matplotlib.pyplot as plt
import numpy as np

import sys

import preprocess
from preprocess import loadTypes,sites,coreConfigs,govConfigs,loadTypesEnglishMap
import pmc
import process_json as pj

def get_cmap(n, name='hsv'):
    '''Returns a function that maps each index in 0, 1, ..., n-1 to a distinct
    RGB color; the keyword argument name must be a standard mpl colormap name.'''
    return plt.cm.get_cmap(name, n)

def annotate_ax(ax,xy,desc="Description",offset=(5,5)):
    ax.annotate(desc,
            xy=xy,
            xytext=(xy[0]+offset[0],xy[1]+offset[1]),
            arrowprops=dict(shrink=0.05, headwidth=3,headlength=3,width=0.5))

    def max_point(x,y):
        maxVal = np.amax(y)
    i, = np.where(y == maxVal)
    return (x[i],y[i])

def normalize_array(x):
    x = np.asarray(x)
    s = np.sum(x)
    if s == 0:
        return x
    return x /(np.sum(x))

def generalBar(data,labels,axes=None,fig=None,width=0.35):
    if fig is None or axes is None:
        fig, axes = plt.subplots(1,1, figsize=(8,8))
    ind = np.arange(data.shape[0])
    axes.bar(ind,data,width)
    axes.set_xticks(ind)
    return (fig,axes)


def comparisonBar(timeData,energyData,axes=None,fig=None,bottom=None,timeErrBars=None,energyErrBars=None,width=0.35):
    if fig is None or axes is None:
        fig, axes = plt.subplots(1,1, figsize=(8,8))

    if bottom is None:
        bottomTime    = np.zeros(timeData.shape[1]) # start at 0
        bottomEnergy  = np.zeros(energyData.shape[1])
    else:
        bottomTime    = bottom
        bottomEnergy  = bottom
    baseTime = None

    timeInd = np.arange(timeData.shape[1])
    energyInd = np.arange(energyData.shape[1])

    for (i,(loadtimes,energies)) in enumerate(zip(timeData,energyData)): # for each "layer"
        if i == 0: # first place is optimal
            optTime   = axes.bar(timeInd-width/2.0,loadtimes,width) # plotting optimal
            optEnergy = axes.bar(energyInd+width/2.0,energies,width)
        else:
            baseTime   = axes.bar(timeInd-width/2.0,loadtimes,width,bottom=bottomTime,yerr=timeErrBars) # only err bars on collected data
            baseEnergy = axes.bar(energyInd+width/2.0,energies,width,bottom=bottomEnergy,yerr=energyErrBars)
        bottomTime    = loadtimes
        bottomEnergy  = energies
    axes.set_xticks(timeInd) # set up xticks
    if baseTime is not None:
        axes.legend((optTime,baseTime,optEnergy,baseEnergy),('Oracle Time','Base time','Oracle Energy','Base Energy')) # TODO fix this to be generic
    else:
        axes.legend((optTime,optEnergy),('Time','Energy')) # TODO fix this to be generic

    return (fig,axes)

def siteScatterPlot(energyAndTime,coreConfigs,site='amazon',axes=None,figure=None,errorBars=False):
    symbols=['x','o','*','s','>','<','+','v','X','D','p','H']
    colors = ['red','green','blue','orange','purple','cyan','black','grey','maroon']
    if axes is None or figure is None: # if no fig
        fig,ax = plt.subplots(4,1,figsize=(8,8)) # create a new figure
    else:
        ax = axes
        fig = figure
    for govIndex,gov in enumerate(govConfigs):
        for eventIndex,loadType in enumerate(loadTypes[0:len(loadTypes)-1]):
            for configIndex,config in enumerate(coreConfigs):
                loadTypeData = energyAndTime[config][gov][site][loadType]
                loadTypeData['loadtime'] = loadTypeData['loadtime']
                loadTypeData['energy']   = loadTypeData['energy']
                x = np.median(loadTypeData['loadtime'])
                y = np.median(loadTypeData['energy'])

                if errorBars:
                    cx = np.std(loadTypeData['loadtime'])
                    cy = np.std(loadTypeData['energy'])
                    ax[eventIndex%4].errorbar(x,y,xerr=cx,yerr=cy,
                            label=config,c=colors[configIndex],
                            alpha=1,marker=symbols[configIndex])
                else:
                    ax[eventIndex%4].scatter(x,y, label=config,
                            c=colors[configIndex], alpha=1,
                            marker=symbols[configIndex])


            ax[eventIndex%4].set_title(loadTypesEnglishMap[loadType])
            ax[eventIndex%4].set_ylabel('Energy (mJ)')
            ax[eventIndex%4].set_xlabel('Load Time (ms)')

        handles,labels = ax[3].get_legend_handles_labels() # only apply a legend to the bottom one
        display = tuple([i for i in range(len(coreConfigs))]) # only display the first few handles
        fig.legend([handle for i,handle in enumerate(handles) if i in display],
                      [label for i,label in enumerate(labels) if i in display],
                      bbox_to_anchor=(1.2,1),
                      loc="upper right",
                      bbox_transform=plt.gcf().transFigure)
        return (fig,ax)

def main():
    graphType = "scatter"
    if len(sys.argv) > 1 and sys.argv[1] in ["scatter","stackedbar"]:
        graphType = sys.argv[1]

    outputPrefix = "graphs/"

    energyAndTime,knownCoreConfigs = preprocess.parseAndCalcEnergy(iterations=20,filePrefix="sim-data",verbose=True)

    if graphType == "scatter":
        siteScatterPlot(energyAndTime,outputPrefix,knownCoreConfigs)
        plt.show()
        #plt.savefig(outputPrefix+site+"-"+gov+"-scatter.pdf")

if __name__ == "__main__":
    main()
