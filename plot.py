# plot.py
# Creates a plot of the data from analyze.py
from __future__ import print_function
import matplotlib.pyplot as plt
import numpy as np

import sys
import glob

import analyze
import pmc
import process_json as pj

def get_cmap(n, name='hsv'):
    '''Returns a function that maps each index in 0, 1, ..., n-1 to a distinct
    RGB color; the keyword argument name must be a standard mpl colormap name.'''
    return plt.cm.get_cmap(name, n)

def define_graph(ax,data,depVar,title=None,unit=None,numTicks=8,varName="unknown"):
    if type(depVar) == type(''):
        if (depVar.split("_")[-1][0:2] == "0x"): # pmc variable
            depClean = depVar.split("_")
            depClean = " ".join(depClean[0:2]) + " " + events[depClean[-1]]
        else:
            depClean=depVar.replace("_"," ")
    else:
        depClean=varName
    if (title is None):
        title = depClean + " over Time"
    if (unit is None):
        unit = "Count"
    ax.set_ylabel(depClean + "(" + unit + ")")
    ax.set_xlabel("Time(us)")
    ax.set_title(title)
    if type(depVar) == type(''): # string
        ax.plot(data['Time_Milliseconds'], data[depVar])
    else:
        ax.plot(data['Time_Milliseconds'][0:len(depVar)], depVar)
    ax.set_xlim(0,np.amax(data['Time_Milliseconds']))
    if type(depVar) == type(''): # string
        ax.set_ylim(0,np.amax(data[depVar]))
    else:
        ax.set_ylim(0,np.amax(depVar))

    sx,ex=ax.get_xlim()
    sy,ey=ax.get_ylim()
    ax.xaxis.set_ticks(np.arange(sx,ex,(ex-sx)/float(numTicks)))
    ax.yaxis.set_ticks(np.arange(sy,ey,(ey-sy)/float(numTicks)))


def annotate_ax(ax,xy,desc="Description",offset=(5,5)):
    ax.annotate(desc,
                xy=xy,
                xytext=(xy[0]+offset[0],xy[1]+offset[1]),
                arrowprops=dict(shrink=0.05, headwidth=3,headlength=3,width=0.5))

def max_point(x,y):
    maxVal = np.amax(y)
    i, = np.where(y == maxVal)
    return (x[i],y[i])

def main():
    #if len(sys.argv) != 3:
    #    print("error: needs two args: [pmcFile] [jsonFile]")
    #    return
    filePrefix = "5-10-"
    if len(sys.argv) > 1:
        filePrefix = sys.argv[1]
        if filePrefix[-1] != '-':
            filePrefix += "-"

    pmcDir = "powmon-data/"
    jsonDir = "json-data/"

    pmcPrefix = pmcDir + filePrefix
    jsonPrefix = jsonDir + filePrefix

    coreConfigs = []
    badConfigs = ["0l-0b","1l-4b","2l-4b","1l-2b","1l-0b","2l-0b"]
    for little in ["0l","1l","2l","4l"]:
        for big in ["0b","1b","2b","4b"]:
            if (little+"-"+big in badConfigs):
                continue
            coreConfigs.append(little+"-"+big)
    governorConfigs = ["ip","pi","pp","ii"]

    siteTotalLoadTimes = dict() # per Site
    siteTotalEnergies = dict()

    coreConfigLoadTimes = dict() # by coreConfig
    coreConfigEnergies = dict()

    governorLoadTimes = dict() # by governor
    governorEnergies = dict()


    for coreConfig in coreConfigs:
        pmcFile = pmcPrefix + coreConfig + "-"
        jsonFile = jsonPrefix + coreConfig + "-"
        for govConfig in governorConfigs:
            pmcFile += govConfig+"-"
            jsonFile += govConfig+"-"
            pmcFiles = glob.glob(pmcFile+"*") # just use pmc files to get id
            ids = []
            for index,f in enumerate(pmcFiles):
                ids.append(pmcFiles[index].split("-")[-1]) # id is last field

            for fileIndex,fileID in enumerate(ids): # for each pair of data files
                pmcFile = pmcFiles[fileIndex]
                print("on file " + pmcFile)
                jsonFile += ids[index] + ".json" # look at same id'd json file

                pmcData=pmc.read_data(pmcFile) # ndarray
                jsonData=pj.read_data(jsonFile) # dict of ndarrays and other values

                numSites = len(jsonData['sites']) # get basic data 
                iterations=jsonData['iterations']

                for i,site in enumerate(jsonData['sites']): # calc avg loadtimes for each site
                    #loadTimes.append(np.mean(jsonData['load_times'][i]))
                    avgLoadTime = np.mean(jsonData['load_times'][i])
                    if site not in siteTotalLoadTimes:
                        siteTotalLoadTimes[site] = [avgLoadTime]
                    else:
                        siteTotalLoadTimes[site].append(avgLoadTime)

                    if coreConfig not in coreConfigLoadTimes:
                        coreConfigLoadTimes[coreConfig] = [avgLoadTime]
                    else:
                        coreConfigLoadTimes[coreConfig].append(avgLoadTime)


                siteTimestamps = dict(zip(jsonData["sites"],
                        [np.zeros((2,iterations)) for x in range(numSites)]))

                count = 0
                for i in range(iterations): # calculate each site's timestamps
                    for site in jsonData['sites']: # for each site
                        siteTimestamps[site][0][i] = jsonData["timestamps"][count]
                        siteTimestamps[site][1][i] = jsonData["timestamps"][count+1]
                        count += 2

                for site in jsonData['sites']:
                    siteEnergies = []
                    for i in range(iterations): # for each iteration on that site
                        start,end = analyze.timestamp_interval( # get start/end sample
                                siteTimestamps[site][0][i],
                                siteTimestamps[site][1][i],
                                pmcData["Time_Milliseconds"])
                        if start == end or end < start: # error
                            energy = -1 # easy to spot error data
                        else:
                            energy = pmc.calc_energy(pmcData['Power_A7'][start:end],
                                    pmcData['Time_Milliseconds'][start:end])
                            energy += pmc.calc_energy(pmcData['Power_A15'][start:end],
                                    pmcData['Time_Milliseconds'][start:end])
                        siteEnergies.append(energy)
                    if site not in siteTotalEnergies:
                        siteTotalEnergies[site] = [np.mean(siteEnergies)]
                    else:
                        siteTotalEnergies[site].append(np.mean(siteEnergies))
                    #energies.append(np.mean(siteEnergies)) # get average for that site
                    if coreConfig not in coreConfigEnergies:
                        coreConfigEnergies[coreConfig] = [np.mean(siteEnergies)]
                    else:
                        coreConfigEnergies[coreConfig].append(np.mean(siteEnergies))

    fig, axs = plt.subplots(3,4, figsize=(8,8))

    cmap=get_cmap(100)
    symbols=['x','o','*','+','>','<','s','v','X','D','p','H']
    for siteIndex,site in enumerate(jsonData['sites']):
        axs[siteIndex%3][siteIndex%4].set_title(site)
        axs[siteIndex%3][siteIndex%4].set_xlabel('Load times (ms)')
        axs[siteIndex%3][siteIndex%4].set_ylabel('Energy Used (J)')
        for configIndex,coreConfig in enumerate(coreConfigs):
            if coreConfig in coreConfigLoadTimes and coreConfig in coreConfigEnergies:
                x = coreConfigLoadTimes[coreConfig][siteIndex]
                y = coreConfigEnergies[coreConfig][siteIndex]
                axs[siteIndex%3][siteIndex%4].scatter(x,y,
                        label=coreConfig,c="black",
                        alpha=0.8,marker=symbols[configIndex])

        if (siteIndex == 0):
            fig.legend(loc=4)
    fig.tight_layout()
    plt.show()

if __name__ == "__main__":
    main()
