# analyze.py
# Takes json data from BBench and PMC data from Powmon
# and generates a machine-learning friendly output file
# that summarizes the data
# Written by Will Sumner
from __future__ import print_function
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
phasesSimple        = ['Setup Connection','Download Page','Process Page','Run Dynamic Content']
#phasesSimple        = allLoadTypes
phaseMap            = dict(zip(phases,phasesSimple))

sites = [ 'amazon',     'bbc',  'cnn',
          'craigslist', 'ebay', 'espn',
          'google',     'msn',  'slashdot',
          'twitter',    'youtube']

powmon_sample_period = 100.0 # sample period is 100ms
verboseGlobal = True

def printv(string):
    global verboseGlobal
    if verboseGlobal:
        print(string)

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

def cleanupEntry(entry,maxStds):
    return filterZeros(filterOutliers(entry,maxStds))

def cleanupData(data,maxStds=3):
    for coreConfig in coreConfigs:
        for govConfig in govConfigs:
            for site in sites:
                for phase in phases:
                    for matrixType in ["loadtime","energy"]:
                        data[coreConfig][govConfig][site][phase][matrixType] = \
                            cleanupEntry(data[coreConfig][govConfig][site][phase][matrixType],maxStds)


def parseAndCalcEnergy(filePrefix="sim-data-", iterations=10,cleanData=False,verbose=False):
    global verboseGlobal
    verboseGlobal = verbose
    if filePrefix[-1] != '-': # some quick error checking
        filePrefix += "-"

    pmcDir = "powmon-data/"
    jsonDir = "json-data/"

    pmcPrefix = pmcDir + filePrefix
    jsonPrefix = jsonDir + filePrefix

    # Layout for the data: # TODO fix this --- really bad design, maybe try to leverage numpy multidim arrays more
    # websiteData[coreConfig][govConfig][siteName][loadTimeType][iteration]['energy'|'loadtime'] -> npArray of values
    baseContainer = {'energy':np.zeros((iterations,)), 'loadtime': np.zeros((iterations,))}
    byLoadType =    dict(zip(phases,[deepcopy(baseContainer) for phase in phases]))
    bySite =        dict(zip(sites,[deepcopy(byLoadType) for site in sites]))
    byGov =         dict(zip(govConfigs,[deepcopy(bySite) for config in govConfigs]))
    websiteData =   dict(zip(coreConfigs,[deepcopy(byGov) for config in coreConfigs]))

    knownCoreConfigs = []
    maxIterations = 0
    warnedIterations = False

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
                    if (not(warnedIterations)):
                        print("Warning: additional iteration data found, skipping.")
                        warnedIterations = True
                    break # stop if we can't hold anymore data, TODO allow for dynamic number of files

                pmcFile = pmcFiles[fileIndex]
                jsonFile = jsonFilePrefix + fileID + ".json" # look at same id'd json file
                printv("on file " + pmcFile)
                printv("with file " + jsonFile)

                try:
                    pmcData = pmc.readPMCData(pmcFile) # ndarray
                except IOError as e:
                    print(e)
                    continue

                try:
                    jsonData = pj.readSeleniumData(jsonFile) # dict of mixed types
                except IOError as e:
                    print(e)
                    continue

                energyThreshold = 0.01
                for site in sites:
                    for index,phase in enumerate(phases):
                        loadtime = jsonData['timestamps'][site][0][loadTypes[index+1]][0] - jsonData['timestamps'][site][0][phase][0]
                        websiteData[coreConfig][govConfig][site][phase]['loadtime'][iteration] = loadtime

                        if loadtime == 0: # don't waste time on 0 energies
                            websiteData[coreConfig][govConfig][site][phase]['energy'][iteration] = -100
                            continue

                        start,end = timestampInterval(int(jsonData['timestamps'][site][0][phase][0]),
                                int(jsonData['timestamps'][site][0][loadTypes[index+1]][0]),
                                pmcData['Time_Milliseconds'])
                        if start == -1 or end == -1: # error getting timestamp
                            printv("unable to calculate timestamps in phase " + phase + ", skipping...")
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
                                printv("In phase: " + phase)
                                printv(str(energy) + " energy calculated from (" + str(minPower) + \
                                        " * 0.5*(" + str(maxPower) + "-" + str(minPower) + ")) * " + str(scaleFactor))

                                printv("scaleFactor = " + str(loadtime) + "/" + str(powmon_sample_period))

                                printv("loadtime = " + str(jsonData['timestamps'][site][0][loadTypes[index+1]][0])  + " - " +  \
                                       str(jsonData['timestamps'][site][0][phase][0]))

                            if loadtime == 0: # if we didn't get any meaningful data because of a low loadtime
                                energy = -100 # make sure it gets filtered out
                        elif start == end -1: # edge case where data is not available
                            printv("edge case found with phase" + phase)
                            energy = -100
                        else:
                            energy =  pmc.calcEnergy(pmcData['Power_A7'][start:end], pmcData['Time_Milliseconds'][start:end])
                            energy += pmc.calcEnergy(pmcData['Power_A15'][start:end], pmcData['Time_Milliseconds'][start:end])
                            if energy <= energyThreshold:
                                printv(str(energy) + " energy calculated from regular integration")
                                printv(start)
                                printv(end)
                                printv(pmcData['Power_A7'][start:end])
                                printv(pmcData['Power_A15'][start:end])
                                printv(pmcData['Time_Milliseconds'][start:end])

                        if (start != end): # if we didn't do an approximation
                            websiteData[coreConfig][govConfig][site][phase]['energy'][iteration] = energy
                        else:
                            websiteData[coreConfig][govConfig][site][phase]['energy'][iteration] = \
                                    energy*(loadtime/powmon_sample_period)
            maxIterations = max(fileIndex,maxIterations)

    if cleanData:
        cleanupData(websiteData,maxStds=3)
    return (websiteData,knownCoreConfigs,maxIterations)

def avgMatrix(timeAndEnergy,iterStart=0,iterStop=0): # update to avged matrix
    if iterStop == 0:
        iterStop = len(timeAndEnergy['4l-4b']['ii']['amazon']['navigationStart']['energy'])
    for coreConfig in coreConfigs:
        for phase in phases:
            for govConfig in govConfigs:
                for site in sites:
                    timeAndEnergy[coreConfig][govConfig][site][phase]['energy'] = \
                        np.mean(timeAndEnergy[coreConfig][govConfig][site][phase]['energy'][iterStart:iterStop])
                    timeAndEnergy[coreConfig][govConfig][site][phase]['loadtime'] = \
                        np.mean(timeAndEnergy[coreConfig][govConfig][site][phase]['loadtime'][iterStart:iterStop])

def extractIter(timeAndEnergy,iteration): # TODO refactor timeAndEnergy organization - this is too hardcoded
    baseContainer = {'energy':np.zeros((1,)), 'loadtime': np.zeros((1,))}
    byLoadType =    dict(zip(phases,[deepcopy(baseContainer) for phase in phases]))
    bySite =        dict(zip(sites,[deepcopy(byLoadType) for site in sites]))
    byGov =         dict(zip(govConfigs,[deepcopy(bySite) for config in govConfigs]))
    iterData =      dict(zip(coreConfigs,[deepcopy(byGov) for config in coreConfigs]))

    for coreConfig in coreConfigs:
        for phase in phases:
            for govConfig in govConfigs:
                for site in sites:
                    iterData[coreConfig][govConfig][site][phase]['energy'] = \
                    timeAndEnergy[coreConfig][govConfig][site][phase]['energy'][iteration]
                    iterData[coreConfig][govConfig][site][phase]['loadtime'] = \
                    timeAndEnergy[coreConfig][govConfig][site][phase]['loadtime'][iteration]
    return iterData

def writeData(data,filename):
    pj.writeData(data,filename)


def readData(filename):
    return pj.readData(filename)

if __name__ == "__main__":
    print("Processing data...")
    data,foundConfigs,maxIterations = parseAndCalcEnergy(filePrefix="sim-data-",iterations=27,cleanData=False)
    dataFilename = "sim-data/sim-data-processed.json"
    iter0 = extractIter(data,0)
    iter1 = extractIter(data,1)
    if sys.flags.interactive: # we are in an interactive shell
        print("Running in interactive mode: type 'data' to see values generated by this file")
    else:
        print("Writing data to file...")
        pj.writeData([data,foundConfigs,maxIterations],dataFilename,indent=1)
        print("Note: Running this file with python -i will allow you to interact directly with the data")
