# plot.py
# Creates a plot of the data from analyze.py
from __future__ import print_function
import matplotlib.pyplot as plt
import numpy as np

import sys

import analyze
from analyze import loadTypes,sites,coreConfigs,govConfigs,loadTypesEnglishMap
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

def filter_iterations(data,iterations):
    return data[0:iterations+1]

def filter_zeros(data):
    return data[data >= 0]

def filter_outliers(data, m=2):
    return data[abs(data - np.mean(data)) < m * np.std(data)]

def preprocess_data(data,iterations):
    return filter_iterations(filter_zeros(filter_outliers(data)),iterations)

def stackedBar(websiteData,outputPrefix,coreConfigs):
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
                    means = [np.median(loadTypeData['loadtime']),
                            np.median(loadTypeData['energy'])]
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


def scatterPlot(websiteData,outputPrefix,coreConfigs):
    symbols=['x','o','*','+','>','<','s','v','X','D','p','H']
    for siteIndex,site in enumerate(sites):
        for gov in govConfigs:
            addLegend = True
            fig, axs = plt.subplots(4,1, figsize=(8,8))
            for eventIndex,loadType in enumerate(loadTypes[0:len(loadTypes)-1]):
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

def multiScatterPlot(websiteData,outputPrefix,coreConfigs):
    symbols=['x','o','*','s','>','<','+','v','X','D','p','H']
    colors = ['red','green','blue','orange','purple','cyan','black','grey','maroon']
    for siteIndex,site in enumerate(sites):
        fig, axs = plt.subplots(4,1, figsize=(8,8))
        for govIndex,gov in enumerate(govConfigs):
            for eventIndex,loadType in enumerate(loadTypes[0:len(loadTypes)-1]):
                for configIndex,config in enumerate(coreConfigs):
                    loadTypeData = websiteData[config][gov][site][loadType]
                    loadTypeData['loadtime'] = preprocess_data(loadTypeData['loadtime'],10)
                    loadTypeData['energy'] = preprocess_data(loadTypeData['energy'],10)
                    x = np.median(loadTypeData['loadtime'])
                    y = np.median(loadTypeData['energy'])
                    cx = np.std(loadTypeData['loadtime'])
                    cy = np.std(loadTypeData['energy'])

                    axs[eventIndex%4].errorbar(x,y,xerr=cx,yerr=cy,
                            label=config,c=colors[configIndex],
                            alpha=1,marker=symbols[configIndex])

                axs[eventIndex%4].set_title(loadTypesEnglishMap[loadType])
                axs[eventIndex%4].set_ylabel('Energy (mJ)')
                axs[eventIndex%4].set_xlabel('Load Time (ms)')

        handles,labels = axs[3].get_legend_handles_labels() # only apply a legend to the bottom one
        display = tuple([i for i in range(len(coreConfigs))]) # only display the first few handles
        fig.legend([handle for i,handle in enumerate(handles) if i in display],
                      [label for i,label in enumerate(labels) if i in display])

        fig.tight_layout()
        plt.savefig(outputPrefix+site+"-multiscatter.pdf")
        plt.close()

def main():
    graphType = "multiscatter"
    if len(sys.argv) > 1 and sys.argv[1] in ["multiscatter","scatter","stackedbar"]:
        graphType = sys.argv[1]

    outputPrefix = "plots/"

    websiteData,knownCoreConfigs = analyze.analyzeData(10)

    if graphType == "scatter":
        scatterPlot(websiteData,outputPrefix,knownCoreConfigs)
    elif graphType == "multiscatter":
        multiScatterPlot(websiteData,outputPrefix,knownCoreConfigs)
    elif graphType == "stackedbar":
        stackedBar(websiteData,outputPrefix,knownCoreConfigs)

if __name__ == "__main__":
    main()
