import numpy as np
import json,sys
# from karlB @ https://stackoverflow.com/questions/26646362/numpy-array-is-not-json-serializable
class NumpyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return json.JSONEncoder.default(self, obj)

def dataToNumpy(data):
    length = 1
    for key in data:
        if type(data[key]) == type([]) and len(data[key]) > 0: # if it is a list
            data[key] = np.array(data[key]) # convert to np array
            length = len(data[key]) # update to new value of np array length for regularity
        elif type(data[key]) == type([]) and len(data[key]) == 0: # if it is an empty list
            data[key] = np.zeros(length)
        elif key == "iterations": # convert the iterations field
            data[key] = int(data[key])
    return data

#def readPMCData(filename):
#    jsonDict = dict()
#    with open(filename,"r") as jsonFile:
#        jsonData = json.load(jsonFile) # parse JSON
#        for jdict in jsonData:
#            jsonDict.update(jdict)
#    dataToNumpy(jsonDict)
#    return jsonDict

def readSeleniumData(filename):
    with open(filename,"r") as jsonFile:
        jsonData = json.load(jsonFile)
        return jsonData

def writeData(data,filename,indent=None):
    with open(filename,"w") as outputFile:
        json.dump(data,outputFile,indent=indent,cls=NumpyEncoder)

def readData(filename):
    with open(filename,"r") as inputFile:
        return json.load(inputFile,object_hook=dataToNumpy)

def main():
    if len(sys.argv) < 2:
        print("error: need a filename")
        return
    data = readData(sys.argv[1])
    print(data)
    return data

if __name__ == "__main__": # run the test to see if it works
    data = main()
