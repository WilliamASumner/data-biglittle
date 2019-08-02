# analyze.py
# Takes json data from BBench and PMC data from Powmon
# and generates a machine-learning friendly output file
# that summarizes the data
# Written by Will Sumner
import numpy as np
import matplotlib.pyplot as plt
import sys

import pmc
import process_json as pj

def index_timestamp(timestamp,timestampArr):
    count = 0
    while(count < len(timestampArr) and timestampArr[count] < timestamp):
        count +=1
    return count

def timestamp_interval(start,end,timestampArr):
    start = index_timestamp(start,timestampArr)
    end = index_timestamp(end,timestampArr)
    return (start,end+1) # plus 1 for python indexing

def main():
    if len(sys.argv) < 3:
        print("error: not enough arguments")
        print("usage: " + sys.argv[0] + " pmc-datafile json-datafile")
        return
    pmcFile = sys.argv[1]
    jsonFile = sys.argv[2]

    pmcData=pmc.read_data(sys.argv[1]) # ndarray
    jsonData=pj.read_data(sys.argv[2]) # dict of ndarrays and other values

    startTimestamp = np.amin([jsonData["start_timestamp"],
                              np.amin(pmcData["Time_Milliseconds"])])
    endTimestamp = jsonData["end_timestamp"]

    jsonData["timestamps"] -= startTimestamp.astype(np.int64)
    pmcData["Time_Milliseconds"] -= startTimestamp # subtract both to start at the same time

    numSites = len(jsonData["sites"])
    iterations = jsonData["iterations"]
    siteTimestamps = dict(zip(jsonData["sites"],
        [np.zeros((2,iterations)) for x in range(numSites)]))

    # get timestamp intervals for each page
    count = 0
    for i in range(iterations):
        for site in jsonData['sites']: # for each site
            siteTimestamps[site][0][i] = jsonData["timestamps"][count]
            siteTimestamps[site][1][i] = jsonData["timestamps"][count+1]
            count += 1

    siteTimestamps[site][1][i] = endTimestamp

    loadPMCAvgs = dict(zip(jsonData["sites"],[[[] for y in range(iterations)] for x in range(numSites)]))
    pmcColumns = pmcData.dtype.names[pmcData.dtype.names.index("Power_GPU")+1:
                                 pmcData.dtype.names.index("Average_Utilisation")]

    # diff the columns
    for column in pmcColumns:
        diffs =  np.diff(pmcData[column])
        #diffs /= 1e6

        pmcData[column][:diffs.shape[0]] = diffs
        pmcData[column][0] = pmcData[column][1] # pad first entry with next val

        # correct negative entries (due to overflow)
        pmcData[column][pmcData[column] < 0] += (2**32 + 1)

    # compile stats for each site
    for i in range(iterations):
        for site in jsonData['sites']:
            start,end = timestamp_interval(siteTimestamps[site][0][i],
                                           siteTimestamps[site][1][i],
                                           pmcData["Time_Milliseconds"])
            #print("(start,end) : ("+str(start) + "," + str(end) + ")")
            energy = pmc.calc_energy(pmcData["Power_A7"][start:end],
                                 pmcData["Time_Milliseconds"][start:end])
            energy += pmc.calc_energy(pmcData["Power_A15"][start:end],
                                 pmcData["Time_Milliseconds"][start:end])
            loadPMCAvgs[site][i].append(energy)
            for column in pmcColumns:
                dataSlice = pmcData[column][start:end]
                loadPMCAvgs[site][i] += (np.mean(dataSlice))

    # average across iterations now
    siteAvgs = dict(zip(jsonData["sites"],[[[] for y in range(iterations)] for x in range(numSites)]))
    for site in jsonData['sites']:
        siteAvgs[site] = np.mean([loadPMCAvgs[site][i] for i in range(iterations)],axis=0)

    features = ["avg","med","min","max","stddev"]

    mlDataHeaders = ["Core_Config","Load_Time(ms)","Energy(J)"]
    mlDataHeaders += [column + "(count)-" + features[i]
                          for x in range(len(features))
                          for column in pmcColumns]



    # creating two graphs
    # graph 1
    # page, config, load time, energy

    # graph 2
    # config, avg counter a15, avg counter a7, load time, energy

    with open(sys.argv[1] + "-ml-output.txt","w") as mlOutFile:
        for index,header in enumerate(mlDataHeaders): # write headers
            if index:
                mlOutFile.write("\t")
            mlOutFile.write(header)
        mlOutFile.write("\n")

        for siteIndex,site in enumerate(jsonData['sites']): # write data
            mlOutFile.write("1") #FIXME add core config
            mlOutFile.write("\t" + str(jsonData["avg_times"][siteIndex]))
            for ind,field in enumerate(mlDataHeaders[2:]):
                mlOutFile.write("\t" + str(siteAvgs[site][ind]))
            mlOutFile.write("\n")

if __name__ == "__main__":
    main()
