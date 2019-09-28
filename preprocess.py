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

allLoadTypes = ['navigationStart', 'fetchStart', 'domainLookupStart',
                      'domainLookupEnd', 'connectStart', 'connectEnd',
                      #'secureConnectionStart', # this entry was not tested
                      'requestStart',
                      'responseStart', 'responseEnd', 'domLoading',
                      'domInteractive', 'domContentLoadedEventStart',
                      'domContentLoadedEventEnd', 'domComplete',
                      'loadEventStart', 'loadEventEnd' ]


loadTypes           = ['navigationStart', 'requestStart', 'domLoading', 'domComplete', 'loadEventEnd' ]
#loadTypes           = allLoadTypes
phases              = loadTypes[0:len(loadTypes)-1]
phasesSimple        = ['Setup Connection','Download Page','Process Page','Run Dynamic Content','End']
#phasesSimple        = allLoadTypes
phaseMap            = dict(zip(phases,phasesSimple))

sites = [ 'amazon',     'bbc',  'cnn',
          'craigslist', 'ebay', 'espn',
          'google',     'msn',  'slashdot',
          'twitter',    'youtube']

powmon_sample_period = 100.0 # sample period is 100ms


# Functions
def indexTimestamp(timestamp,timestampArr):
    count = 0
    while(count < len(timestampArr) and timestampArr[count] < timestamp):
        count +=1
    return count

def timestampInterval(start,end,timestampArr):
    start = indexTimestamp(start,timestampArr)
    end = indexTimestamp(end,timestampArr)
    if end < start:
        return (-1,-1)
    return (start,end+1) # plus 1 for python indexing

def filterZeros(data): # remove less than 0 data
    return data[data >= 0]

def filterOutliers(data, m): # remove outliers
    return data[abs(data - np.mean(data)) < m * np.std(data)]

def cleanup_entry(entry,m):
    return filterZeros(filterOutliers(entry,m))

def cleanupData(data,m=3):
    for coreConfig in coreConfigs:
        for govConfig in govConfigs:
            for site in sites:
                for loadType in loadTypes:
                    for matrixType in ["loadtime","energy"]:
                        data[coreConfig][govConfig][site][loadType][matrixType] = \
                            cleanup_entry(data[coreConfig][govConfig][site][loadType][matrixType],m)


def parseAndCalcEnergy(filePrefix="sim-data-", iterations=10,cleanData=True,verbose=False):
    if filePrefix[-1] != '-': # some quick error checking
        filePrefix += "-"

    pmcDir = "powmon-data/"
    jsonDir = "json-data/"

    pmcPrefix = pmcDir + filePrefix
    jsonPrefix = jsonDir + filePrefix

    # Layout for the data:
    # websiteData[coreConfig][govConfig][siteName][loadTimeType][iteration]['energy'|'loadtime'] -> npArray of values
    baseContainer = {'energy':np.zeros((iterations,)), 'loadtime': np.zeros((iterations,))}
    byLoadType =    dict(zip(loadTypes,[deepcopy(baseContainer) for loadType in loadTypes]))
    bySite =        dict(zip(sites,[deepcopy(byLoadType) for site in sites]))
    byGov =         dict(zip(govConfigs,[deepcopy(bySite) for config in govConfigs]))
    websiteData =   dict(zip(coreConfigs,[deepcopy(byGov) for config in coreConfigs]))

    knownCoreConfigs = []
    collectedIterations = 0

    for coreConfig in coreConfigs:
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
                    if verbose:
                        print("skipping additional iterations...")
                    break # stop if we can't hold anymore data, TODO allow for dynamic number of files

                pmcFile = pmcFiles[fileIndex]
                jsonFile = jsonFilePrefix + fileID + ".json" # look at same id'd json file
                if verbose:
                    print ("on file " + pmcFile)
                    print("with file " + jsonFile)

                try:
                    pmcData = pmc.read_data(pmcFile) # ndarray
                    jsonData = pj.read_selenium_data(jsonFile) # dict of mixed types
                except:
                    continue
                collectedIterations += 1

                energyThreshold = 0.01
                for site in sites:
                    for index,loadType in enumerate(loadTypes):
                        if (index < len(loadTypes) - 1): # don't calculate pow for the extra 'interval'
                            loadtime = jsonData['timestamps'][site][0][loadTypes[index+1]][0] - jsonData['timestamps'][site][0][loadType][0]
                            websiteData[coreConfig][govConfig][site][loadType]['loadtime'][iteration] = loadtime

                            if loadtime == 0: # don't waste time on 0 energies
                                websiteData[coreConfig][govConfig][site][loadType]['energy'][iteration] = -100
                                continue

                            start,end = timestampInterval(int(jsonData['timestamps'][site][0][loadType][0]),
                                    int(jsonData['timestamps'][site][0][loadTypes[index+1]][0]),
                                    pmcData['Time_Milliseconds'])
                            if start == -1 or end == -1: # error getting timestamp
                                if verbose:
                                    print("unable to calculate timestamps in loadType " + loadType + ",skipping...")
                                continue

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
                                    if verbose:
                                        print("In loadType: " + loadType)
                                        print("0 energy calculated from (" + str(minPower) + " * 0.5*(" + str(maxPower) + "-" + str(minPower) + ")) * " + str(scaleFactor))
                                        print("scaleFactor = " + str(loadtime) + "/" + str(powmon_sample_period))
                                        print("loadtime = " + str(jsonData['timestamps'][site][0][loadTypes[index+1]][0])  + " - " + str(jsonData['timestamps'][site][0][loadType][0]))
                                    if loadtime == 0: # if we didn't get any meaningful data because of a low loadtime
                                        energy = -100 # make sure it gets filtered out
                            elif start == end -1: # edge case where data is not available
                                if verbose:
                                    print("edge case found with loadType" + loadType)
                                energy = -100
                            else:
                                energy =  pmc.calc_energy(pmcData['Power_A7'][start:end], pmcData['Time_Milliseconds'][start:end])
                                energy += pmc.calc_energy(pmcData['Power_A15'][start:end], pmcData['Time_Milliseconds'][start:end])
                                if energy <= energyThreshold and verbose:
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

    if cleanData:
        cleanupData(websiteData,m=3)
    return (websiteData,knownCoreConfigs,collectedIterations)

def avgMatrix(timeAndEnergy,iterStart=0,iterStop=0): # return avged matrix
    if iterStop == 0:
        iterStop = len(timeAndEnergy['4l-4b']['ii']['amazon']['navigationStart']['energy'])
    for coreConfig in coreConfigs:
        for loadType in loadTypes:
            for govConfig in govConfigs:
                for site in sites:
                    timeAndEnergy[coreConfig][govConfig][site][loadType]['energy'] = \
                        np.mean(timeAndEnergy[coreConfig][govConfig][site][loadType]['energy'][iterStart:iterStop])
                    timeAndEnergy[coreConfig][govConfig][site][loadType]['loadtime'] = \
                        np.mean(timeAndEnergy[coreConfig][govConfig][site][loadType]['loadtime'][iterStart:iterStop])
    return timeAndEnergy

if __name__ == "__main__":
    print("Processing data...")
    data,foundConfigs,maxIterations = parseAndCalcEnergy(filePrefix="sim-data-",iterations=20)[0]
    if sys.flags.interactive: # we are in an interactive shell
        print("Running in interactive mode: type 'data' to see data values")
    else:
        print(data) # just print
        print("Running this file with python -i will allow you to interact directly with the data")
