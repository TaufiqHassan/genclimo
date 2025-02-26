import time
import argparse
from get_climoFiles import get_climo

def main():

    parser = argparse.ArgumentParser()
    
    parser.add_argument("-c", help="case name", required=True)
    parser.add_argument("-s", help="start year", required=True)
    parser.add_argument("-e", help="end year.", default=None)
    parser.add_argument("-dir", help="input directory", default=None)
    parser.add_argument("-dir2", help="climo output directory", default=None)
    parser.add_argument("-m", help="model name (eam or cam)", default='eam')
    parser.add_argument("-v", help="variable names", default=None)
    parser.add_argument("-t", help="time freq (sea=seasonal|mon=monthly)", default=None)
   
    args = parser.parse_args()
    cs = args.c
    strt = args.s
    end = args.e
    path = args.dir
    path2 = args.dir2
    tm = args.t
    model = args.m
    variable = args.v
    if path2 == None:
        path2 = path
        
    start = time.perf_counter()
    gc=get_climo(case=cs,start=strt,path=path,path2=path2,end=end,ts=tm,mod=model)
    if variable != None:
        gc.variable=variable
    gc.get_nc()
    finish = time.perf_counter()
    print(f'\nFinished in {round(finish-start, 2)} second(s)')

