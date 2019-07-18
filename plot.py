# plot.py
# Creates a plot of the data from analyze.py
from __future import print_function
import matplotlib.pyplot as plt
import numpy as np

import analyze
import pmc

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

def max_point(x,y):
    maxVal = np.amax(y)
    i, = np.where(y == maxVal)
    return (x[i],y[i])

def main():
    fig, axs = plt.subplots(4,1, figsize=(8,8))
    #def define_graph(ax,data,
                     #depVar,title=None,
                     #unit=None,numTicks=8,
                     #varName="unknown")
    define_graph(axs[0],data,
                 'Core_0_Event_0x80',unit="Mops",
                 numTicks=8,varName=events['0x80'])

    fig.tight_layout()
    plt.show()

main()
