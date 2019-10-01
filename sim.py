# sim
import numpy as np
import gurobipy as gb # ILP Library

# Local files
import preprocess
from preprocess import sites,loadTypes,phases,coreConfigs
from preprocess import avgMatrix,parseAndCalcEnergy

import os,time

def extractMatrix(site,timeAndEnergy,matrixType):
    arr = np.zeros((len(phases),len(coreConfigs)))
    for p,phase in enumerate(phases):
        for c,config in enumerate(coreConfigs):
            arr[p][c] = timeAndEnergy[config]["ii"][site][phase][matrixType]
    return arr


def getMatrix(site,phases,coreConfigs,timeAndEnergy,matrixType,i):
    arr = np.zeros((len(phases),len(coreConfigs)))
    for p,phase in enumerate(phases):
        for c,config in enumerate(coreConfigs):
            arr[p][c] = timeAndEnergy[config]["ii"][site][phase][matrixType][i] # TODO: change iteration
    return arr

def solveConfigModel(timeAndEnergySet,coreConfigs,filePrefix="sim-data",verbose=False,logFilename=None):
    phasesToOptVals = dict(zip(sites,[ dict(zip(phases,[None for i in range(len(phases))])) for site in sites])) # maps phases to [energy, time, optimal coreconfig]


    if verbose:
        print("Gathering data...")
    if not(logFilename is None):
        gb.setParam("LogToConsole", 0) # save output to log file

    numPhases = len(phases)
    numConfigs = len(coreConfigs)

    for site in sites:
        timeMatrix   = extractMatrix(site,timeAndEnergySet,'loadtime')
        energyMatrix = extractMatrix(site,timeAndEnergySet,'energy')

        baseIndex    = coreConfigs.index("4l-4b") # calculate time/energ from normal operation
        baseTime     = np.sum(timeMatrix[p][baseIndex] for p in range(numPhases))
        baseEnergy   = np.sum(energyMatrix[p][baseIndex] for p in range(numPhases))

        # optimize a site
        try:

            #### timing model construction
            start = time.time()
            model = gb.Model(site)

            decisionMatrix = [[ model.addVar(vtype=gb.GRB.BINARY,name=p+c) for c in coreConfigs] for p in phases]

            for p,phase in enumerate(phases):
                model.addConstr(gb.quicksum([decisionMatrix[p][c] for c in range(numConfigs)]) == 1, name=phase)

            timeSum = gb.quicksum(decisionMatrix[p][c]*timeMatrix[p][c] for c in range(numConfigs) for p in range(numPhases))
            model.addConstr(timeSum <= 3000, name='t') # time constraint

            energySum = gb.quicksum(decisionMatrix[p][c]*energyMatrix[p][c] for c in range(numConfigs) for p in range(numPhases))
            model.setObjective(energySum, gb.GRB.MINIMIZE) # obj function

            constructionTime = time.time()-start
            ####

            model.optimize() # call upon the old magic

            if verbose:
                print("Site: %s" % site)

            numPhases = len(phases)
            numConfigs = len(coreConfigs)
            if model.status == gb.GRB.Status.OPTIMAL:
                sol= model.getAttr('X', model.getVars())
                siteSolution  = [[sol[c+numConfigs*p] for c in range(numConfigs)] for p in range(numPhases)]

                if verbose:
                    print("Minimized Energy: %g mJ, over baseline %g mJ: %g" % (model.objVal,baseEnergy,model.objVal/baseEnergy))
                    print("With time: %g ms, over baseline %g ms: %g" % (timeSum.getValue(),baseTime,baseTime/timeSum.getValue()))

                for p,phase in enumerate(phases):
                    if verbose:
                        print("For phase: %s " % phase)
                    for c,config in enumerate(coreConfigs):
                        if siteSolution[p][c] > 0.99:
                            phasesToOptVals[site][phase] = [timeMatrix[p][c],energyMatrix[p][c],config,model.runTime,constructionTime] # save the results we found
                            if verbose:
                                print("\tConfig %s was chosen" % config)

            elif model.status == gb.GRB.INFEASIBLE:
                if verbose:
                    print("Unable to find feasible solution... relaxing constraints and optimizing...")
                # feasRelaxS ( #  - relax constraints a bit to find a solution
                # relaxobjtyp - 1 = minimize squares of the bound and constraint violations
                # minrelax - whether to minimize objective function (false) or objective function AND violation (true, our case)
                # vrelax - whether to variable bounds can be relaxed (false in our case)
                # crelax - whether constraints can be relaxed (true, we can increase our cutoff time a bit...)
                model.feasRelaxS(1,True,False,True)
                model.optimize()

                if model.status == gb.GRB.Status.OPTIMAL:
                    sol= model.getAttr('X', model.getVars())
                    siteSolution  = [[sol[c+numConfigs*p] for c in range(numConfigs)] for p in range(numPhases)]

                    if verbose:
                        print("Minimized Energy: %g mJ, over baseline %g mJ: %g" % (model.objVal,baseEnergy,model.objVal/baseEnergy))
                        print("With time: %g ms, over baseline %g ms: %g" % (timeSum.getValue(),baseTime,baseTime/timeSum.getValue()))

                    for p,phase in enumerate(phases):
                        if verbose:
                            print("For phase: %s " % phase)
                        for c,config in enumerate(coreConfigs):
                            if siteSolution[p][c] > 0.99:
                                phasesToOptVals[site][phase] = [timeMatrix[p][c],energyMatrix[p][c],config,model.runTime,constructionTime] # save the results we found
                                if verbose:
                                    print("\tConfig %s was chosen" % config)
                elif verbose: print("No feasible solution possible, even with relaxation")


            elif verbose: print("No feasible solution") # , relaxing constraint %s and adding second objective function" % "time constraint")

        except gb.GurobiError as e:
            if verbose: print("Error encountered: %d %s" % (e.errno,str(e)))

    if not(logFilename is None):
        os.rename('gurobi.log',logFilename)

    return phasesToOptVals

if __name__ == '__main__':
    timeAndEnergy,coreConfigs = parseAndCalcEnergy("sim-data",iterations=20)
    timeAndEnergySet = avgMatrix(timeAndEnergy) # avg all iterations
    solution = solveConfigModel(timeAndEnergy,coreConfigs,logFilename='model_solve.log')

    with open("model-output-sim-data-avg.txt","w") as outFile: # Write out results
        outFile.write("phase: [solution time, solution energy, configuration, run time, and construction time]\n")
        for site in sites:
            outFile.write(site+"\n")
            for phase in phases:
                outFile.write(phase + ":" + str(solution[site][phase]) + "\n")
