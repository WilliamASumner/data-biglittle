import numpy as np

import sys
import data_plot

import sim

import preprocess as preproc
from preprocess import parseAndCalcEnergy,avgMatrix
from preprocess import loadTypes,phases,phasesSimple,sites,phaseMap

verbose = True

def printv(string):
    if verbose:
        print(string)


def modelConstrTables(solMatrix,outputPrefix="tables/",timeParam='optimize',writeOut=False):
        if timeParam not in ['optimize','construct']:
            raise Exception('Invalid time parameter: \"{}\" either optimize or construct'.format(timeParam))
        if timeParam == 'optimize':
            ind = 3
        else:
            ind = 4

        tableStr = "\\begin{table}\n\\begin{center}\n\\begin{tabular}{| c | c |}\n\\hline\n"

        for s,site in enumerate(sites):
            if not(solMatrix[site][phases[0]] is None):
                valMs = round(solMatrix[site][phases[0]][ind]*1000,3)
                tableStr += site + " & " + str(valMs) + "ms \\\\\n\hline\n" # only need one time for whole site



        if timeParam == 'optimize':
            tableStr += "\\end{tabular}\n\\end{center}\n\\caption{Site Model Optimization Times}\\label{table:model-" + timeParam + "-time}\n\\end{table}"
        else:
            tableStr += "\\end{tabular}\n\\end{center}\n\\caption{Site Model Construction Times}\\label{table:model-" + timeParam + "-time}\n\\end{table}"


        if writeOut:
            with open(outputPrefix+"model-"+timeParam+"table.txt","w") as outFile:
                outFile.write(tableStr)
        else: 
            print(tableStr)

def main():
    dataPrefix = "sim-data"
    try:
        printv("Attempting to load data...")
        timeAndEnergy,coreConfigs,maxIterations = preproc.readData(dataPrefix + "-processed.json")
    except IOError: # file does not exist
        printv("Failed to load existing data")
        printv("Parsing data and calculating energy...")
        timeAndEnergy,coreConfigs,maxIterations = preproc.parseAndCalcEnergy(filePrefix=dataPrefix,cleanData=False,iterations=27)
        printv("Writing data to disk...")
        preproc.writeData([timeAndEnergy,coreConfigs,maxIterations],dataPrefix + "-processed.json")

    printv("Cleaning data...")
    preproc.cleanupData(timeAndEnergy,maxStds=3)

    printv("Averaging data across iterations...")
    preproc.avgMatrix(timeAndEnergy) # avg all iterations

    printv("Creating and solving ILP model...")
    solMatrix = sim.solveConfigModel(timeAndEnergy,coreConfigs,logFilename='gurobi_sol_plot.log') # optimize model

    modelConstrTables(solMatrix)
    modelConstrTables(solMatrix,timeParam='construct')

if __name__ == "__main__":
    main()
