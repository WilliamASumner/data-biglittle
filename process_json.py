import numpy as np
import json,sys

def data_to_numpy(data):
    for key in data:
        if type(data[key]) == type([]): # if it is a list
            data[key] = np.array(data[key]) # convert to np array
        elif key == "iterations": # convert the iterations field
            data[key] = int(data[key])
    return data


def read_data(filename):
    json_dict = dict()
    with open(filename) as json_file:
        json_data = json.load(json_file) # parse JSON
        for jdict in json_data:
            json_dict.update(jdict)
    data_to_numpy(json_dict)
    return json_dict

def read_selenium_data(filename):
    with open(filename) as json_file:
        json_data = json.load(json_file)
        return json_data

def main():
    if len(sys.argv) < 2:
        print("error: need a filename")
        return
    data = read_data(sys.argv[1])
    print(data)
    return data

if __name__ == "__main__": # run the test to see if it works
    data= main()
