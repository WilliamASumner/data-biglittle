# sol_plot.py
# Creates a plot of the solution from sim.py and the data from preprocess.py
from __future__ import print_function
import matplotlib.pyplot as plt
from matplotlib.patches import Ellipse # shapes

import numpy as np

import sys

import data_plot
import sim
from copy import deepcopy

import preprocess as preproc
from preprocess import parseAndCalcEnergy,avgMatrix
from preprocess import loadTypes,phases,phasesSimple,sites,phaseMap
import data_plot as dp

verbose = True

def printv(string):
    if verbose:
        print(string)

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

def graphOptimal(timeAndEnergySet,coreConfigs,solMatrix,site='amazon',outputPrefix="graphs/",writeOut=False):
    fig,axes = dp.siteScatterPlot(timeAndEnergySet,coreConfigs,site=site,axes=None,figure=None,errorBars=False)
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


def graphAbsComparison(timeAndEnergySet,solMatrix,site='amazon',outputPrefix="graphs/",writeOut=False):
    timeData   = np.zeros((2,len(phases)))
    energyData = np.zeros((2,len(phases)))

    colors = [[] for i in range(4)] # two layers of color for each data set

    for p,phase in enumerate(phases):
        if solMatrix[site][phase] is None:
            continue
        baseTime   = timeAndEnergySet['4l-4b']['ii'][site][phase]['loadtime'] # baseline values
        baseEnergy = timeAndEnergySet['4l-4b']['ii'][site][phase]['energy']

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

    fig,axes,energyAxis = dp.comparisonBar(timeData,energyData,twoAxes=True,colors=colors)


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

    fig,axes,energyAxis = dp.comparisonBar(timeData,energyData,timeErrBars=timeErr,energyErrBars=energyErr)

    fig.suptitle(site + " Oracle and Baseline Comparison (relative)",y=1.01,fontsize='xx-large')
    axes.set_xticklabels(phasesSimple)
    axes.set_ylabel('Efficiency improvement over baseline')

    l = dp.newline([0,1],[1,1],axes) # draw a line at the breakeven point
    l.set_linestyle('dashed')
    l.set_color('grey')

    fig.tight_layout()
    if writeOut:
        plt.savefig(outputPrefix+site+"-comparison-rel.pdf",bbox_inches="tight")
        plt.clf()
    else: 
        plt.show()
    plt.close(fig)


def graphCompAllSites(timeAndEnergySet,solMatrix,outputPrefix="graphs/",compType='loadtime',writeOut=False,horizontal=False):
    compTypes = ['loadtime','energy']
    compTypeTitle = {'loadtime':'load speed','energy':'energy efficiency'}
    if compType not in compTypes:
        raise Exception('Invalid comparison type: \"{}\" either loadtime or energy'.format(compType))
    values = np.zeros((1,3,len(sites)))
    err    = np.zeros((1,1,len(sites)))

    palette = colors=[data_plot.blue,data_plot.red,data_plot.green]
    # General shape is (layers,side by side bars (runs),number of data points per run)


    fig, axes = plt.subplots(1,1, figsize=(16,8)) # use a custom fig size

    for s,site in enumerate(sites):
        data = np.zeros(len(phases))

        for p,phase in enumerate(phases):
            if solMatrix[site][phase] is None:
                data[p] = np.NaN
            else:
                data[p]   = timeAndEnergySet['4l-4b']['ii'][site][phase][compType] / solMatrix[site][phase][compTypes.index(compType)]

        values[0][0][s] = np.nanmin(data) # min val
        values[0][1][s] = np.nanmax(data) # max val
        values[0][2][s] = np.nanmean(data) # avg val

    fig,axes,handles = dp.genericCompBar(values,fig=fig,axes=axes,colors=palette,barh=horizontal)

    title = compTypeTitle[compType] + " comparisons for all sites (relative)"
    fig.suptitle(title.title(),y=1.01,fontsize='xx-large')

    if horizontal:
        axes.set_yticklabels(sites + ["Overall"])
        axes.set_xlabel('Efficiency improvement over baseline (a higher number is better)')
        l = dp.newline([1,0],[1,1],axes) # draw a line at the breakeven point
    else:
        axes.set_xticklabels(sites + ["Overall"])
        axes.set_ylabel('Efficiency improvement over baseline (a higher number is better)')
        l = dp.newline([0,1],[1,1],axes) # draw a line at the breakeven point


    axes.legend(handles[0],("Min","Max","Mean"))

    rects = axes.patches
    labels = []
    for s, site in enumerate(sites):
        labels.append(str(round(values[0][0][s],2)))
    for s,site in enumerate(sites):
        labels.append(str(round(values[0][1][s],2)))
    for s,site in enumerate(sites):
        labels.append(str(round(values[0][2][s],2)))


    y0,y1 = axes.get_ylim()
    for rect, label in zip(rects, labels):
        height = rect.get_height()
        axes.text(rect.get_x() + rect.get_width() / 2, height + (y1-y0)/50.0, label,
                ha='center', va='bottom')


    l.set_linestyle('dashed')
    l.set_color('grey')

    fig.tight_layout()
    if writeOut:
        plt.savefig(outputPrefix+"All-sites-min-max-averages-" + compType + ".pdf",bbox_inches="tight")
        plt.clf()
    else: 
        plt.show()
    plt.close(fig)


def graphAllSitesAverages(timeAndEnergySet,solMatrix,outputPrefix="graphs/",compType='loadtime',writeOut=False,horizontal=False):
    compTypes = ['loadtime','energy']
    compTypeTitle = {'loadtime':'load speed','energy':'energy efficiency'}
    if compType not in compTypes:
        raise Exception('Invalid comparison type: \"{}\" either loadtime or energy'.format(compType))
    #values = np.zeros((1,3,len(sites)))
    #err    = np.zeros((1,1,len(sites)))

    values = np.zeros((1,1,len(sites)+1))
    err    = np.zeros((1,1,len(sites)+1))

    #palette = colors=[data_plot.blue,data_plot.red,data_plot.green]
    palette = colors=[data_plot.green]
# General shape is (layers,side by side bars (runs),number of data points per run)

    
    fig, axes = plt.subplots(1,1, figsize=(16,8)) # use a custom fig size

    for s,site in enumerate(sites):
        data = np.zeros(len(phases))

        for p,phase in enumerate(phases):
            if solMatrix[site][phase] is None:
                data[p] = np.NaN
            else:
                data[p]   = timeAndEnergySet['4l-4b']['ii'][site][phase][compType] / solMatrix[site][phase][compTypes.index(compType)]

        #values[0][0][s] = np.nanmin(data) # min val
        #values[0][1][s] = np.nanmax(data) # max val
        #values[0][2][s] = np.nanmean(data) # avg val
        values[0][0][s] = np.nanmean(data) # avg val
        err[0][0][s] = np.nanstd(data) # avg val
    values[0][0][s+1] = np.nanmean(values[0][0][0:len(sites)-1])
    err[0][0][s+1] = np.nanstd(values[0][0][0:len(sites)-1])

    fig,axes,handles = dp.genericCompBar(values,fig=fig,axes=axes,colors=palette,barh=horizontal,errBars=err)

    title = compTypeTitle[compType] + " comparisons for all sites (relative)"
    fig.suptitle(title.title(),y=1.01,fontsize='xx-large')

    if horizontal:
        axes.set_yticklabels(sites + ["Overall"])
        axes.set_xlabel('Efficiency improvement over baseline (a higher number is better)')
        l = dp.newline([1,0],[1,1],axes) # draw a line at the breakeven point
    else:
        axes.set_xticklabels(sites + ["Overall"])
        axes.set_ylabel('Efficiency improvement over baseline (a higher number is better)')
        l = dp.newline([0,1],[1,1],axes) # draw a line at the breakeven point


    #axes.legend(handles[0],("Min","Max","Mean"))
    axes.legend(handles[0],("Mean","Max"))

    rects = axes.patches
    labels = []
    for s, site in enumerate(sites):
        labels.append(str(round(values[0][0][s],2)))
    labels.append(str(round(values[0][0][s+1],2)))
    #for s,site in enumerate(sites):
    #    labels.append(str(round(values[0][1][s],2)))
    #for s,site in enumerate(sites):
    #    labels.append(str(round(values[0][2][s],2)))

        
    y0,y1 = axes.get_ylim()
    for rect, label in zip(rects, labels):
        height = rect.get_height()
        axes.text(rect.get_x() + rect.get_width() / 2 + 0.25, height + (y1-y0)/50.0, label,
                ha='center', va='bottom')


    l.set_linestyle('dashed')
    l.set_color('grey')

    fig.tight_layout()
    if writeOut:
        plt.savefig(outputPrefix+"All-sites-averages-" + compType + ".pdf",bbox_inches="tight")
        plt.clf()
    else: 
        plt.show()
    plt.close(fig)



def graphCompAllSamples(timeAndEnergy,solMatrices,outputPrefix="graphs/",compType='loadtime',writeOut=False,horizontal=False):
    compTypes = ['loadtime','energy']
    compTypeTitle = {'loadtime':'load speed','energy':'energy efficiency'}
    if compType not in compTypes:
        raise Exception('Invalid comparison type: \"{}\" either loadtime or energy'.format(compType))
    values  = np.zeros((1,3,len(sites)))
    err     = np.zeros((1,3,len(sites)))
    palette = colors=[data_plot.blue,data_plot.red,data_plot.green]
# General shape is (layers,side by side bars (runs),number of data points per run)


    fig, axes = plt.subplots(1,1, figsize=(16,8)) # use a custom fig size
    iterations = 27

    for s,site in enumerate(sites):
        data = np.zeros(len(phases)*iterations)

        i = 0
        for p,phase in enumerate(phases):
            for i in range(iterations):
                if solMatrices[i][site][phase] is None:
                    data[i] = np.NaN
                else:
                    data[i] = timeAndEnergy['4l-4b']['ii'][site][phase][compType][i] / solMatrices[i][site][phase][compTypes.index(compType)]
                i += 1

        values[0][0][s] = np.nanmin(data) # min val
        values[0][1][s] = np.nanmax(data) # max val
        values[0][2][s] = np.nanmean(data) # avg val
        err[0][2][s] = np.nanstd(data) # std val

    fig,axes,handles = dp.genericCompBar(values,fig=fig,axes=axes,colors=palette,barh=horizontal,errBars=err)

    title = compTypeTitle[compType] + " comparisons for all sites (relative)"
    fig.suptitle(title.title(),y=1.01,fontsize='xx-large')

    if horizontal:
        axes.set_yticklabels(sites)
        axes.set_xlabel('Efficiency improvement over baseline (a higher number is better)')
        l = dp.newline([1,0],[1,1],axes) # draw a line at the breakeven point
    else:
        axes.set_xticklabels(sites)
        axes.set_ylabel('Efficiency improvement over baseline (a higher number is better)')
        l = dp.newline([0,1],[1,1],axes) # draw a line at the breakeven point


    axes.legend(handles[0],("Min","Max","Mean"))

    rects = axes.patches
    labels = []
    for s, site in enumerate(sites):
        labels.append(str(round(values[0][0][s],2)))
    for s,site in enumerate(sites):
        labels.append(str(round(values[0][1][s],2)))
    for s,site in enumerate(sites):
        labels.append(str(round(values[0][2][s],2)))

        
    y0,y1 = axes.get_ylim()
    for rect, label in zip(rects, labels):
        height = rect.get_height()
        axes.text(rect.get_x() + rect.get_width() / 2, height + (y1-y0)/50.0, label,
                ha='center', va='bottom')


    l.set_linestyle('dashed')
    l.set_color('grey')

    fig.tight_layout()
    if writeOut:
        plt.savefig(outputPrefix+"All-sites-comparison-" + compType + ".pdf",bbox_inches="tight")
        plt.clf()
    else: 
        plt.show()
    plt.close(fig)

def graphModelTime(solMatrix,outputPrefix="graphs/",timeParam='optimize',writeOut=False):
    if timeParam not in ['optimize','construct']:
        raise Exception('Invalid time parameter: \"{}\" either optimize or construct'.format(timeParam))
    loadTimes = np.zeros(len(sites)) # displaying solution times of all phases
    if timeParam == 'optimize':
        ind = 3
    else:
        ind = 4
    for s,site in enumerate(sites):
        if not(solMatrix[site][phases[0]] is None):
            loadTimes[s] = solMatrix[site][phases[0]][ind] # only need one time for whole site
    (fig,axes) = dp.generalBar(loadTimes*1000,sites)

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

# Adapted from https://matplotlib.org/3.1.1/gallery/statistics/customized_violin.html
def set_axis_style(ax, labels,xlabel):
    ax.get_xaxis().set_tick_params(direction='out')
    ax.xaxis.set_ticks_position('bottom')
    ax.set_xticks(np.arange(1, len(labels) + 1))
    ax.set_xticklabels(labels)
    ax.set_xlim(0.25, len(labels) + 0.75)
    ax.set_xlabel(xlabel)

def graphViolinPlot(timeAndEnergy,solMatrix,coreConfig,site='amazon',outputPrefix="graphs/",graphType='loadtime',writeOut=False):
    validTypes = ['loadtime','energy','opt-loadtime','opt-energy']
    if graphType not in validTypes:
        raise Exception('Invalid graph type: \"{}\", valid values: {}'.format(timeParam,validTypes))
    fig, axes = plt.subplots(1,4,figsize=(16,8))

    violins = []
    iterations = 27
    if graphType == 'loadtime':
        for p,phase in enumerate(phases):
            iters = np.zeros(iterations)
            for i,val in enumerate(iters):
                iters[i] = timeAndEnergy[coreConfig]['ii'][site][phase][graphType][i]
            fig, ax,medianHandle = dp.violinPlot([iters],axes[p],fig)
            fig.suptitle("Distribution of " + graphType + " with " + site + " and configuration " + coreConfig,y=1.01,fontsize='xx-large')
            set_axis_style(ax,[phase],'')
            if graphType == 'loadtime':
                ax.set_ylabel("Loadtime (ms)")

        ax.legend([medianHandle],['Median'])
    #fig, ax = dp.violinPlot(violins,axes[p])



    # all data must be sorted before it can be plotted


    fig.tight_layout()
    if writeOut:
        title = "-".join([coreConfig,site,graphType])
        plt.savefig(outputPrefix + title + ".pdf",bbox_inches="tight")
        plt.clf()
    else: 
        plt.show()
    plt.close(fig)


def main():
    dataPrefix = "sim-data/sim-data"
    graphPrefix = "graphs/"
    doPerSiteComparisons = True
    doAvgViolins = False
    doSampleViolins = False
    doPerSampleComparisons = False # TODO fix this
    modelSolvingGraphs = False
    minMaxAvgCompGraphs = True

    try:
        printv("Attempting to load data...")
        timeAndEnergyRaw,coreConfigs,maxIterations = preproc.readData(dataPrefix + "-processed.json")
    except IOError: # file does not exist
        printv("Failed to load existing data")
        printv("Parsing data and calculating energy...")
        timeAndEnergyRaw,coreConfigs,maxIterations = preproc.parseAndCalcEnergy(filePrefix=dataPrefix,cleanData=False,iterations=27)
        printv("Writing data to disk...")
        preproc.writeData([timeAndEnergyRaw,coreConfigs,maxIterations],dataPrefix + "-processed.json")

    timeAndEnergyClean = deepcopy(timeAndEnergyRaw)
    timeAndEnergySet   = deepcopy(timeAndEnergyRaw)
    printv("Cleaning data...")
    preproc.cleanupData(timeAndEnergyClean,maxStds=3)

    printv("Averaging data across iterations...")
    preproc.avgMatrix(timeAndEnergySet) # avg all iterations

    printv("Creating and solving averaged ILP model...")
    avgSolMatrix = sim.solveConfigModel(timeAndEnergySet,coreConfigs,logFilename='gurobi-logs/gurobi_avg_sol_plot.log') # optimize model

    if doPerSampleComparisons:
        solMatrixSamples = []
        printv("Solving sample ILP models...")
        iterations = 27
        for site in sites:
            printv(site)
            for coreConfig in coreConfigs:
                #printv("\t"+ coreConfig)
                for i in range(iterations):
                    #printv("\t\t"+str(i))
                    logFile = 'gurobi-logs/gurobi_sol_plot_'+site+'_'+coreConfig+'_'+str(i)+'.log'
                    solMatrixSamples.append(sim.solveConfigModel(preproc.extractIter(timeAndEnergyClean,i),coreConfigs,logFilename=logFile))

        printv("Graphing per Sample site comparisons")
        graphCompAllSamples(timeAndEnergyRaw,solMatrixSamples,outputPrefix="graphs/",compType='energy',writeOut=False)


    if doSampleViolins:
        printv("Graphing Violin plots...")

    if doAvgViolins:
        printv("Graphing Averaged Violin plots...")
        for site in sites:
            printv(site)
            for coreConfig in coreConfigs:
                graphViolinPlot(timeAndEnergyRaw,avgSolMatrix,coreConfig,site=site,outputPrefix=graphPrefix+"Violins-Phases/",graphType='loadtime',writeOut=True)

    if doPerSiteComparisons:
        for site in sites:
            printv(site)
            printv("optimal")

            graphOptimal(timeAndEnergySet,coreConfigs,avgSolMatrix,outputPrefix=graphPrefix,site=site,writeOut=True)

            printv("relative comparison")
            graphRelComparison(timeAndEnergySet,avgSolMatrix,outputPrefix=graphPrefix,site=site,writeOut=True)

            printv("absolute comparison")
            graphAbsComparison(timeAndEnergySet,avgSolMatrix,outputPrefix=graphPrefix,site=site,writeOut=True)
    if modelSolvingGraphs:

        printv("model solving times")
        graphModelTime(avgSolMatrix,outputPrefix=graphPrefix,timeParam='optimize',writeOut=True)

        printv("model construction times")
        graphModelTime(avgSolMatrix,outputPrefix=graphPrefix,timeParam='construct',writeOut=True)

    if minMaxAvgCompGraphs:
        printv("Min Max Avg Loadtime Comparison")
        graphCompAllSites(timeAndEnergySet,avgSolMatrix,outputPrefix=graphPrefix,writeOut=True,compType='loadtime')

        printv("Min Max Avg Energy Comparison")
        graphCompAllSites(timeAndEnergySet,avgSolMatrix,outputPrefix=graphPrefix,writeOut=True,compType='energy')

    printv("Average Loadtime Comparison")
    graphAllSitesAverages(timeAndEnergySet,avgSolMatrix,outputPrefix=graphPrefix,writeOut=True,compType='loadtime')

    printv("Average Energy Comparison")
    graphAllSitesAverages(timeAndEnergySet,avgSolMatrix,outputPrefix=graphPrefix,writeOut=True,compType='energy')


if __name__ == '__main__':
    main()

