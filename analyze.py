# analyze.py
# Takes json data from BBench and PMC data from Powmon
# and generates a machine-learning friendly output file
# that summarizes the data
# Written by Will Sumner
import numpy as np
import matplotlib.pyplot as plt
import sys,glob
from copy import deepcopy

import pmc
import process_json as pj


# Global values
badConfigs = [(0,0),(1,4),(2,4),(1,2),(2,2),(1,1),(2,1),(1,0),(2,0),(0,2)] # configs we will skip
badLittle  = [3] # configs we will skip
badBig     = [3] # configs we will skip
coreConfigs = []
for little in range(5): # 0 - 4
    for big in range(5):
        if ((little,big) in badConfigs) or (little in badLittle) or (big in badBig):
            continue
        coreConfigs.append(str(little)+"l-"+str(big)+"b")


govConfigs = ["ii"] #["ip","pi","pp","ii"]

loadTypes           = ['navigationStart', 'requestStart', 'domLoading', 'domComplete', 'loadEventEnd' ]
loadTypesEnglish    = ['Setup Connection','Download Page','Process Page','Run Dynamic Content']
loadTypesEnglishMap = dict(zip(loadTypes[0:4],loadTypesEnglish))

sites = [ 'amazon',     'bbc',  'cnn',
          'craigslist', 'ebay', 'espn',
          'google',     'msn',  'slashdot',
          'twitter',    'youtube']

powmon_sample_period = 100.0 # sample period is 100ms

#loadTypes = ['navigationStart', 'fetchStart', 'domainLookupStart',
#                      'domainLookupEnd', 'connectStart', 'connectEnd',
#                      #'secureConnectionStart',
#                      'requestStart',
#                      'responseStart', 'responseEnd', 'domLoading',
#                      'domInteractive', 'domContentLoadedEventStart',
#                      'domContentLoadedEventEnd', 'domComplete',
#                      'loadEventStart', 'loadEventEnd' ]


# Functions
def index_timestamp(timestamp,timestampArr):
    count = 0
    while(count < len(timestampArr) and timestampArr[count] < timestamp):
        count +=1
    return count

def timestamp_interval(start,end,timestampArr):
    start = index_timestamp(start,timestampArr)
    end = index_timestamp(end,timestampArr)
    return (start,end+1) # plus 1 for python indexing

def analyzeData(iterations=10):
    filePrefix = "selenium-redo-"
    if len(sys.argv) > 1:
        filePrefix = sys.argv[1]
        if filePrefix[-1] != '-':
            filePrefix += "-"

    pmcDir = "powmon-data/"
    jsonDir = "json-data/"

    pmcPrefix = pmcDir + filePrefix
    jsonPrefix = jsonDir + filePrefix

    # Layout for the data:
    # websiteData[coreConfig][govConfig][siteName][loadTimeType][iteration][energy|loadtime] -> npArray of values
    baseContainer = {'energy':np.zeros((iterations,)), 'loadtime': np.zeros((iterations,))}
    byLoadType =    dict(zip(loadTypes,[deepcopy(baseContainer) for loadType in loadTypes]))
    bySite =        dict(zip(sites,[deepcopy(byLoadType) for site in sites]))
    byGov =         dict(zip(govConfigs,[deepcopy(bySite) for config in govConfigs]))
    websiteData =   dict(zip(coreConfigs,[deepcopy(byGov) for config in coreConfigs]))

    knownCoreConfigs = []

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
            if len(ids) != 0: # we found a file!
                if not coreConfig in knownCoreConfigs:
                    knownCoreConfigs.append(coreConfig) # track which core configs we've found
            for fileIndex,fileID in enumerate(ids): # for each pair of data files
                iteration = fileIndex
                if (iteration >= iterations):
                    print("skipping additional iterations...")
                    break # stop if we can't hold anymore data, TODO allow for dynamic number of files

                pmcFile = pmcFiles[fileIndex]
                print ("on file " + pmcFile)
                jsonFile = jsonFilePrefix + fileID + ".json" # look at same id'd json file
                print("with file " + jsonFile)

                pmcData = pmc.read_data(pmcFile) # ndarray
                jsonData = pj.read_selenium_data(jsonFile) # dict of mixed types

                energyThreshold = 0.01
                for site in sites:
                    for index,loadType in enumerate(loadTypes):
                        if (index < len(loadTypes) - 1): # don't calculate pow for the extra 'interval'
                            loadtime = jsonData['timestamps'][site][0][loadTypes[index+1]][0] - jsonData['timestamps'][site][0][loadType][0]
                            websiteData[coreConfig][govConfig][site][loadType]['loadtime'][iteration] = loadtime

                            start,end = timestamp_interval(int(jsonData['timestamps'][site][0][loadType][0]),
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
                                if energy <= energyThreshold:
                                    print("0 energy calculated from (" + str(minPower) + "0.5*(" + str(maxPower) + "-" + str(minPower) + ")) * " + str(scaleFactor))
                                    print("scaleFactor = " + str(loadtime) + "/" + str(powmon_sample_period))
                            elif start == end -1: # edge case where data is not available
                                print("edge case found with loadType" + loadType)
                                energy = -100
                            else:
                                energy =  pmc.calc_energy(pmcData['Power_A7'][start:end], pmcData['Time_Milliseconds'][start:end])
                                energy += pmc.calc_energy(pmcData['Power_A15'][start:end], pmcData['Time_Milliseconds'][start:end])
                                if energy <= energyThreshold:
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
    return (websiteData,knownCoreConfigs)

if __name__ == "__main__":
    print(analyzeData(3))
