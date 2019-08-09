# sim
import numpy as np
import gurobipy as gb # ILP Library

# Local files
import analyze
from analyze import sites,loadTypes

def getAveragedMatrix( site,phases,coreConfigs,websiteData,matrixType):
    arr = np.zeros((len(phases),len(coreConfigs)))
    for p,phase in enumerate(phases):
        for c,config in enumerate(coreConfigs):
            arr[p][c] = np.mean(websiteData[config]["ii"][site][phase][matrixType])
    return arr


def getMatrix(site,phases,coreConfigs,websiteData,matrixType,i):
    arr = np.zeros((len(phases),len(coreConfigs)))
    for p,phase in enumerate(phases):
        for c,config in enumerate(coreConfigs):
            arr[p][c] = websiteData[config]["ii"][site][phase][matrixType][i] # TODO: change iteration
    return arr

def main():
    phases = loadTypes[0:len(loadTypes)-1]
    gb.setParam("LogToConsole", 0)

    print("Gathering data...")
    websiteData,coreConfigs = analyze.analyzeData()

    numPhases = len(phases)
    numConfigs = len(coreConfigs)

    for site in sites:
        timeMatrix = getAveragedMatrix(site,phases,coreConfigs,websiteData,'loadtime')
        energyMatrix = getAveragedMatrix(site,phases,coreConfigs,websiteData,'energy')
        baseIndex = coreConfigs.index("4l-4b")
        baseTime = np.sum(timeMatrix[p][baseIndex] for p in range(numPhases))
        baseEnergy = np.sum(energyMatrix[p][baseIndex] for p in range(numPhases))
        # optimize a site
        try:
            model = gb.Model(site)


            decisionMatrix = [[ model.addVar(vtype=gb.GRB.BINARY,name=p+c) for c in coreConfigs] for p in phases]

            for p,phase in enumerate(phases):
                model.addConstr(gb.quicksum([decisionMatrix[p][c] for c in range(numConfigs)]) == 1, name=phase)

            timeSum = gb.quicksum(decisionMatrix[p][c]*timeMatrix[p][c] for c in range(numConfigs) for p in range(numPhases))
            model.addConstr(timeSum <= 3000, name='t') # time constraint

            energySum = gb.quicksum(decisionMatrix[p][c]*energyMatrix[p][c] for c in range(numConfigs) for p in range(numPhases))
            model.setObjective(energySum, gb.GRB.MINIMIZE) # obj function

            model.optimize()

            print("Site: %s" % site)
            numPhases = len(phases)
            numConfigs = len(coreConfigs)
            if model.status == gb.GRB.Status.OPTIMAL:
                print("Minimized Energy: %g mJ, over baseline: %g" % (model.objVal,baseEnergy/model.objVal))
                print("With time: %g ms, over baseline: %g" % (timeSum.getValue(),baseTime/timeSum.getValue()))
                sol= model.getAttr('X', model.getVars())
                finalSolution  = [[sol[c+numConfigs*p] for c in range(numConfigs)] for p in range(numPhases)]
                for p,phase in enumerate(phases):
                    print("For phase: %s " % phase)
                    for c,config in enumerate(coreConfigs):
                        if finalSolution[p][c] > 0.99:
                            print("\tConfig %s was chosen" % config)
            else:
                print("No solution, relaxing constraint %s and adding second objective function" % "time constraint")
        except gb.GurobiError as e:
            print("Error encountered: %d %s" % (e.errno,str(e)))

if __name__ == '__main__':
    main()
