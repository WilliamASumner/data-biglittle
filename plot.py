# plot.py
# Creates a plot of the data from analyze.py
from __future__ import print_function
import matplotlib.pyplot as plt
import numpy as np

import sys,glob
from copy import deepcopy

import analyze
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

def stackedBar(sites,govConfigs,loadTypes,coreConfigs,websiteData,outputPrefix):
    width = 0.35
    ind = np.arange(2) # one for energy and one for load time
    for site in sites:
        for gov in govConfigs:
            fig, axs = plt.subplots(3,1, figsize=(8,8))
            for index,config in enumerate(coreConfigs):
                prevMeans = [0,0] # start at the bottom
                #print("config: " + config)
                for loadType in loadTypes:
                    loadTypeData = websiteData[config][gov][site][loadType]
                    means = [np.mean(loadTypeData['loadtime']),
                            np.mean(loadTypeData['energy'])]
                    #print(loadTypeData['loadtime'])
                    #print(normalize_array(loadTypeData['loadtime']))
                    #print("means " + str(means))
                    stds = [np.std(loadTypeData['loadtime']),
                            np.std(loadTypeData['energy'])]
                    axs[index].bar(ind,means,width,bottom=prevMeans)
                    if np.sum(means) != 0:
                        prevMeans = means # no copying required because means becomes a new list
                axs[index].set_title(site + " with configuration " + config)
                axs[index].set_xticks(ind)
                axs[index].set_xticklabels(('Load Time (ms)','Energy (mJ)'))
                axs[index].set_ylabel('Average Load Time (ms) per Phase')
                energyAxis = axs[index].twinx()
                energyAxis.set_ylabel('Average Energy (mJ) per Phase')
            axs[0].legend(loadTypes)

        fig.tight_layout()
        plt.savefig(outputPrefix+site+"-"+gov+"-stackedbar.pdf")
        plt.close()


def scatterPlot(sites,govConfigs,loadTypes,loadTypeMap,coreConfigs,websiteData,outputPrefix):
    symbols=['x','o','*','+','>','<','s','v','X','D','p','H']
    for siteIndex,site in enumerate(sites):
        for gov in govConfigs:
            addLegend = True
            fig, axs = plt.subplots(4,1, figsize=(8,8))
            for eventIndex,loadType in enumerate(loadTypes[0:len(loadTypes)-1]):
                loadTimes = []
                energies = []
                for configIndex,config in enumerate(coreConfigs):
                    loadTypeData = websiteData[config][gov][site][loadType]

                    axs[eventIndex%4].scatter(loadTypeData['loadtime'][0],
                            loadTypeData['energy'][0],
                            label=config,c="black",
                            alpha=0.8,marker=symbols[configIndex])

                    axs[eventIndex%4].set_title(loadTypeMap[loadType])
                axs[eventIndex%4].set_ylabel('Energy (mJ)')
                if eventIndex % 4 == 3:
                    axs[eventIndex%4].set_xlabel('Load Time (ms)')
                if (addLegend):
                    fig.legend(loc=4)
                    addLegend = False

            fig.tight_layout()
            plt.savefig(outputPrefix+site+"-"+gov+"-scatter.pdf")
            plt.close()

def multiScatterPlot(sites,govConfigs,loadTypes,loadTypeMap,coreConfigs,websiteData,outputPrefix):
    symbols=['x','o','*','+','>','<','s','v','X','D','p','H']
    colors = ['r','g','b','orange']
    for siteIndex,site in enumerate(sites):
        fig, axs = plt.subplots(4,1, figsize=(8,8))
        for govIndex,gov in enumerate(govConfigs):
            for eventIndex,loadType in enumerate(loadTypes[0:len(loadTypes)-1]):
                loadTimes = []
                energies = []
                for configIndex,config in enumerate(coreConfigs):
                    loadTypeData = websiteData[config][gov][site][loadType]
                    x = np.mean(loadTypeData['loadtime'])
                    y = np.mean(loadTypeData['energy'])
                    cx = np.std(loadTypeData['loadtime'])
                    cy = np.std(loadTypeData['energy'])

                    axs[eventIndex%4].errorbar(x,y,xerr=cx,yerr=cy,
                            label=config,c= colors[govIndex],
                            alpha=0.75,marker=symbols[configIndex])

                axs[eventIndex%4].set_title(loadTypeMap[loadType])
                axs[eventIndex%4].set_ylabel('Energy (mJ)')
                axs[eventIndex%4].set_xlabel('Load Time (ms)')

        handles,labels = axs[3].get_legend_handles_labels() # only apply a legend to the bottom one
        circles = [plt.Circle((0, 0), 0.2, color=col) for col in colors]
        circleLabels = govConfigs
        display = (0,1,2) # only display the first few handles
        fig.legend([handle for i,handle in enumerate(handles) if i in display]+circles,
                      [label for i,label in enumerate(labels) if i in display]+circleLabels)

        #fig.tight_layout()
        plt.savefig(outputPrefix+site+"-multiscatter.pdf")
        plt.close()





def main():
    #if len(sys.argv) != 3:
    #    print("error: needs two args: [pmcFile] [jsonFile]")
    #    return
    filePrefix = "selenium-"
    outputPrefix = "plots/"
    if len(sys.argv) > 1:
        filePrefix = sys.argv[1]
        if filePrefix[-1] != '-':
            filePrefix += "-"

    pmcDir = "powmon-data/"
    jsonDir = "json-data/"

    pmcPrefix = pmcDir + filePrefix
    jsonPrefix = jsonDir + filePrefix

    coreConfigs = []
    #badConfigs = ["0l-0b","1l-4b","2l-4b","1l-2b","1l-0b","2l-0b"] # old code
    #for little in ["0l","1l","2l","4l"]:
    #    for big in ["0b","1b","2b","4b"]:
    #        if (little+"-"+big in badConfigs):
    #            continue
    #        coreConfigs.append(little+"-"+big)
    coreConfigs=["4l-0b","4l-4b","0l-4b"] # we know which configurations we're testing now
    govConfigs = ["ip","pi","pp","ii"]

    #loadTypes = ['navigationStart', 'fetchStart', 'domainLookupStart',
    #                      'domainLookupEnd', 'connectStart', 'connectEnd',
    #                      #'secureConnectionStart',
    #                      'requestStart',
    #                      'responseStart', 'responseEnd', 'domLoading',
    #                      'domInteractive', 'domContentLoadedEventStart',
    #                      'domContentLoadedEventEnd', 'domComplete',
    #                      'loadEventStart', 'loadEventEnd' ]


    loadTypes = ['navigationStart', 'requestStart',
            'domLoading',
            'domComplete',
            'loadEventEnd' ]
    loadTypesEnglish = ['Setup Connection','Download Page','Process Page','Run Dynamic Content']
    loadTypesEnglishMap = dict(zip(loadTypes[0:4],loadTypesEnglish))

    sites = [ 'amazon', 'bbc', 'cnn',
            'craigslist', 'ebay', 'espn',
            'google', 'msn', 'slashdot',
            'twitter', 'youtube']

    iterations = 3 # TODO make this generic
    powmon_sample_period = 100.0 # sample period is 100ms

    # Layout for the data:
    # websiteData[coreConfig][govConfig][siteName][loadTimeType][iteration][energy|loadtime] -> npArray of values
    baseContainer = {'energy':np.zeros((iterations,)), 'loadtime': np.zeros((iterations,))}
    byLoadType =    dict(zip(loadTypes,[deepcopy(baseContainer) for loadType in loadTypes]))
    bySite =        dict(zip(sites,[deepcopy(byLoadType) for site in sites]))
    byGov =         dict(zip(govConfigs,[deepcopy(bySite) for config in govConfigs]))
    websiteData =   dict(zip(coreConfigs,[deepcopy(byGov) for config in coreConfigs]))

    for coreConfig in coreConfigs: # load/organize the data
        pmcFile = pmcPrefix + coreConfig + "-"
        jsonFilePrefix = jsonPrefix + coreConfig + "-"
        for govConfig in govConfigs:
            pmcFilePrefix = pmcPrefix + coreConfig + "-" +  govConfig + "-"
            jsonFilePrefix = jsonPrefix + coreConfig + "-" + govConfig + "-"

            pmcFiles = glob.glob(pmcFilePrefix+"*") # just use pmc files to get id
            ids = []
            for index,f in enumerate(pmcFiles):
                ids.append(pmcFiles[index].split("-")[-1]) # id is last field
            for fileIndex,fileID in enumerate(ids): # for each pair of data files
                iteration = fileIndex
                pmcFile = pmcFiles[fileIndex]
                print ("on file " + pmcFile)
                jsonFile = jsonFilePrefix + fileID + ".json" # look at same id'd json file
                print("with file " + jsonFile)

                pmcData = pmc.read_data(pmcFile) # ndarray
                jsonData = pj.read_selenium_data(jsonFile) # dict of mixed types

                threshold = 0.01
                for site in sites:
                    for index,loadType in enumerate(loadTypes):
                        if (index < len(loadTypes) - 1): # don't calculate pow for the extra 'interval'
                            loadtime = jsonData['timestamps'][site][0][loadTypes[index+1]][0] - jsonData['timestamps'][site][0][loadType][0]
                            websiteData[coreConfig][govConfig][site][loadType]['loadtime'][iteration] = loadtime

                            start,end = analyze.timestamp_interval(int(jsonData['timestamps'][site][0][loadType][0]),
                                    int(jsonData['timestamps'][site][0][loadTypes[index+1]][0]),
                                    pmcData['Time_Milliseconds'])
                            if (start == end-1 and end < len(pmcData['Power_A7'])): # time interval is lower than our powmon recorded, estimate
                                scaleFactor = loadtime/powmon_sample_period
                                minPower = min(pmcData['Power_A7'][start-1],pmcData['Power_A7'][end])
                                maxPower = max(pmcData['Power_A7'][start-1],pmcData['Power_A7'][end])
                                energyLittle = (minPower + 0.5*(maxPower-minPower)) * scaleFactor * (pmcData['Time_Milliseconds'][end] - pmcData['Time_Milliseconds'][start])
                                minPower = min(pmcData['Power_A15'][start-1],pmcData['Power_A15'][end])
                                maxPower = max(pmcData['Power_A15'][start-1],pmcData['Power_A15'][end])
                                energyBig = (minPower + 0.5*(maxPower-minPower)) * scaleFactor * (pmcData['Time_Milliseconds'][end] - pmcData['Time_Milliseconds'][start])
                                energy = energyBig + energyLittle
                                if energy <= threshold:
                                    print("0 energy calculated from (" + str(minPower) + "0.5*(" + str(maxPower) + "-" + str(minPower) + ")) * " + str(scaleFactor))
                                    print("scaleFactor = " + str(loadtime) + "/" + str(powmon_sample_period))
                            elif start == end -1: # edge case where data is not available
                                print("edge case found with loadType" + loadType)
                                energy = -100
                            else:
                                energy =  pmc.calc_energy(pmcData['Power_A7'][start:end], pmcData['Time_Milliseconds'][start:end])
                                energy += pmc.calc_energy(pmcData['Power_A15'][start:end], pmcData['Time_Milliseconds'][start:end])
                                if energy <= threshold:
                                    print("0 energy calculated from regular integration")
                                    print(start)
                                    print(end)
                                    print(pmcData['Power_A7'][start:end])
                                    print(pmcData['Power_A15'][start:end])
                                    print(pmcData['Time_Milliseconds'][start:end])

                            if (start != end): # if we didn't do an approximation
                                websiteData[coreConfig][govConfig][site][loadType]['energy'][iteration] = energy
                            else:
                                websiteData[coreConfig][govConfig][site][loadType]['energy'][iteration] = \
                                        energy*(loadtime/powmon_sample_period)

    graphType = "multiscatter"

    if graphType == "scatter":
        scatterPlot(sites,govConfigs,loadTypes,loadTypesEnglishMap,coreConfigs,websiteData,outputPrefix)
    elif graphType == "multiscatter":
        multiScatterPlot(sites,govConfigs,loadTypes,loadTypesEnglishMap,coreConfigs,websiteData,outputPrefix)
    elif graphType == "stackedbar":
        stackedBar(sites,govConfigs,loadTypes,coreConfigs,websiteData,outputPrefix)


# old code
#cmap=get_cmap(100)
#axs[siteIndex%3][siteIndex%4].scatter(x,y,
#label=coreConfig,c="black",
#alpha=0.8,marker=symbols[configIndex])
#fig.legend(loc=4)

if __name__ == "__main__":
    main()
