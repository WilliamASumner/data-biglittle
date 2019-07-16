# analyze
# Written by Will Sumner
import numpy as np
import matplotlib.pyplot as plt
import sys

import pmc
import process_json as pj

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

def index_timestamp(timestamp,timestampArr):
    count = 0
    while(timestampArr[count] <= timestamp):
        count +=1
    return count

def timestamp_interval(start,end,timestampArr):
    start = index_timestamp(start,timestampArr)
    end = index_timestamp(end,timestampArr)
    return (start,end)

def main():
    if len(sys.argv) < 3:
        print("error: not enough arguments")
        print("usage: " + sys.argv[0] + " pmc-datafile json-datafile")
        return
    pmcFile = sys.argv[1]
    jsonFile = sys.argv[2]

    pmcData=pmc.read_data(sys.argv[1]) # ndarray
    jsonData=pj.read_data(sys.argv[2]) # dict of ndarrays and other values

    start_timestamp = np.amin([jsonData["start_timestamp"],
                              np.amin(pmcData["Time_Milliseconds"])])
    jsonData["timestamps"] -= start_timestamp.astype(np.int64)
    pmcData["Time_Milliseconds"] -= start_timestamp # subtract both to start at the same time



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

    loadPMCAvgs = dict(zip(jsonData["sites"],[[[] for y in range(iterations)] for x in range(numSites)]))
    pmcColumns = pmcData.dtype.names[pmcData.dtype.names.index("Power_GPU")+1:
                                 pmcData.dtype.names.index("Average_Utilisation")]

    # diff the columns
    for column in pmcColumns:
        diffs =  np.diff(pmcData[column])

        diffs /= 1e6
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
                loadPMCAvgs[site][i] += (np.mean(dataSlice),
                                         np.median(dataSlice),
                                         np.amin(dataSlice),
                                         np.amax(dataSlice),
                                         np.std(dataSlice))
    # average across iterations now
    siteAvgs = dict(zip(jsonData["sites"],[[[] for y in range(iterations)] for x in range(numSites)]))
    for site in jsonData['sites']:
        siteAvgs[site] = np.mean([loadPMCAvgs[site][i] for i in range(iterations)],axis=0)

    features = ["avg","med","min","max","stddev"]
    dataHeaders = ["Core_Config","Load_Time(ms)","Energy(J)"] + \
                  [column + "(Mops/sec)-" + features[i]
                          for x in range(len(features)) for column in pmcColumns]

    with open("ml-output.txt","w") as outFile:
        for index,header in enumerate(dataHeaders): # write headers
            if index:
                outFile.write("\t")
            outFile.write(header)
        outFile.write("\n")

        for siteIndex,site in enumerate(jsonData['sites']): # write data
            outFile.write("1") #FIXME add core config
            outFile.write("\t" + str(jsonData["avg_times"][siteIndex]))
            for ind,field in enumerate(dataHeaders[2:]):
                outFile.write("\t" + str(siteAvgs[site][ind]))
            outFile.write("\n")



    fig, axs = plt.subplots(4,1, figsize=(8,8))
#def define_graph(ax,data,depVar,title=None,unit=None,numTicks=8,varName="unknown
    #define_graph(axs[0],data,'Core

    fig.tight_layout()
    #plt.show()



if __name__ == "__main__":
    main()
