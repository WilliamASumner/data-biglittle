# plot.py
# Creates a plot of the data from analyze.py
from __future__ import print_function
import matplotlib.pyplot as plt
import matplotlib.lines as mlines
import numpy as np

import sys

import preprocess
from preprocess import loadTypes,sites,coreConfigs,govConfigs,phaseMap
import pmc
import process_json as pj

orange = (1, .7, .43)
red = (1, .46, .43)
green = (.36, .84, .42)
blue = (.31, .68, .71)
grey = (.7, .7, .7)

def annotate_ax(ax,xy,desc="Description",offset=(5,5)):
    ax.annotate(desc,
            xy=xy,
            xytext=(xy[0]+offset[0],xy[1]+offset[1]),
            arrowprops=dict(shrink=0.05, headwidth=3,headlength=3,width=0.5))

def max_point(x,y):
    maxVal = np.amax(y)
    i, = np.where(y == maxVal)
    return (x[i],y[i])


def newline(p1, p2,ax): # from https://stackoverflow.com/questions/36470343/how-to-draw-a-line-with-matplotlib
    xmin, xmax = ax.get_xbound()

    if(p2[0] == p1[0]):
        xmin = xmax = p1[0]
        ymin, ymax = ax.get_ybound()
    else:
        ymax = p1[1]+(p2[1]-p1[1])/(p2[0]-p1[0])*(xmax-p1[0])
        ymin = p1[1]+(p2[1]-p1[1])/(p2[0]-p1[0])*(xmin-p1[0])

    l = mlines.Line2D([xmin,xmax], [ymin,ymax])
    ax.add_line(l)
    return l

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

def genericCompBar(data,axes=None,fig=None,timeErrBars=None,energyErrBars=None,width=0.35):
    # General shape is (# layers,#entries,#side by side bars)
    if len(data.shape) > 3:
        raise Exception("Invalid shape: {}, must be 3 or 2 dimensions".format(data.shape))

    if fig is None or axes is None:
        fig, axes = plt.subplots(1,1, figsize=(8,8))

    handles = dict()
    ind = np.arange(data.shape[-1])

    if len(data.shape) == 1:
        if not(l in handles):
            handles[l] = []
        handles[l].append(axes.bar(ind+width*r,data,width)) # give handles similar structure to what they were 
    else:
        for l,layer in enumerate(data):
            prevBottom = np.zeros(data.shape[-1])
            for r,run in enumerate(layer):
                offset = width/data.shape[1] # offset by number of runs
                if not(l in handles):
                    handles[l] = []
                handles[l].append(axes.bar(ind+width*r,data[l][r],width,bottom=prevBottom)) # give handles similar structure to what they were 
                prevBottom = data[l][r]
    axes.set_xticks((ind+width*r)/2) # set up xticks

    return (fig,axes,handles)




def comparisonBar(timeData,energyData,axes=None,fig=None,bottom=None,timeErrBars=None,energyErrBars=None,width=0.35,twoAxes=False,colors=None):
    if fig is None or axes is None:
        fig, axes = plt.subplots(1,1, figsize=(8,8))

    if bottom is None:
        bottomTime    = np.zeros(timeData.shape[1]) # start at 0
        bottomEnergy  = np.zeros(energyData.shape[1])
    else:
        bottomTime    = bottom
        bottomEnergy  = bottom
    baseTime = None

    if colors is None:
        colors = [[red for i in range(timeData.shape[1])],
                [red for i in range(timeData.shape[1])],
                [green for i in range(timeData.shape[1])],
                [green for i in range(timeData.shape[1])]] # TODO refactor this mess...

    timeInd = np.arange(timeData.shape[1])
    energyInd = np.arange(energyData.shape[1])

    if twoAxes:
        secondAxis = axes.twinx()
    else:
        secondAxis = axes

    for (i,(loadtimes,energies)) in enumerate(zip(timeData,energyData)): # for each "layer"
        if i == 0: # first place down smaller of the two graphs
            minTime   = axes.bar(timeInd-width/2.0,loadtimes,width,color=colors[0]) # plotting optimal
            minEnergy = secondAxis.bar(energyInd+width/2.0,energies,width,color=colors[2])
        else:
            baseTime   = axes.bar(timeInd-width/2.0,loadtimes,width,bottom=bottomTime,yerr=timeErrBars,color=colors[1]) # only err bars on collected data
            baseEnergy = secondAxis.bar(energyInd+width/2.0,energies,width,bottom=bottomEnergy,yerr=energyErrBars,color=colors[3])
        bottomTime    = loadtimes
        bottomEnergy  = energies
    axes.set_xticks(timeInd) # set up xticks
    if baseTime is not None:
        leg = axes.legend((minTime,baseTime,minEnergy,baseEnergy),('Oracle Time','Base time','Oracle Energy','Base Energy')) # TODO fix this to be generic
        leg.legendHandles[0].set_color(orange)
        leg.legendHandles[1].set_color(blue)
        leg.legendHandles[2].set_color(red)
        leg.legendHandles[3].set_color(green)

    else:
        axes.legend((minTime,minEnergy),('Time','Energy')) # TODO fix this to be generic

    return (fig,axes,secondAxis)

def siteScatterPlot(timeAndEnergySet,coreConfigs,site='amazon',axes=None,figure=None,errorBars=False):
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
                loadTypeData = timeAndEnergySet[config][gov][site][loadType]
                x = loadTypeData['loadtime']
                y = loadTypeData['energy']

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


            ax[eventIndex%4].set_title(phaseMap[loadType])
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
