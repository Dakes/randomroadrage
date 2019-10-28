# File to simulate traffic demand using SUMO's randomtrips.py tool.

# Intended to be used for creation of a first model of a city's traffic demand until the output relatively
# matches the city's actual demand to determine where sensors should be placed. Calibration towards sensors data
# follows in *filename*

# author: Daniel Ostertag, Daniel Habermayr

import argparse
import os
import sys
from colorama import Fore


def main():
    my_parser = argparse.ArgumentParser(prog='Random Road Rage',
                                        description="A wrapper for SUMO's randomTrips.py to simulate rush hours")

    # Add randomTrips arguments
    my_parser.add_argument('net-file', metavar='input_path', type=str, dest="netfile",
                           help='define the net file (mandatory)')
    my_parser.add_argument('-o', '--output-trip-file', action='store', dest='tripfile',
                           help='define the output trip filename. ')
    my_parser.add_argument('-b', '--begin', action='store', dest='begin', default=0,
                           help='begin time. (Default 0)')
    my_parser.add_argument('-e', '--end', action='store', dest='end', default=3600,
                           help='end time (Default 3600, 1 hour)')
    my_parser.add_argument('--prefix', action='store_true', dest='tripprefix', default='',
                           help='prefix for the trip ids')
    my_parser.add_argument('-p', '--period', action='store', dest='period', default=1,
                           help='Generate vehicles with equidistant departure times and period=FLOAT (default 1.0). ')
                                # 'If option --binomial is used, the expected arrival rate is set to 1/period.')\
    # Add RRR arguments
    my_parser.add_argument('--prefix', action='store_true', dest='tripprefix', default='',
                           help='prefix for the trip ids')
    my_parser.add_argument('--truck', action='store', type=float, dest='truck_rate', default=0,
                           help='percentage of trucks')
    my_parser.add_argument('--bus', action='store', type=float, dest='bus_rate', default=0,
                           help='percentage of busses')
    my_parser.add_argument('--mc', action='store', type=float, dest='mc_rate', default=0,
                           help='percentage of motorcycles')
    my_parser.add_argument('--ped', action='store', type=float, dest='ped_rate', default=0,
                           help='percentage of pedestrians')
    my_parser.add_arguments('-s', '--seed', action='store', type=int, dest='seed', default=1,
                            help='seed for the simulation')
    my_parser.add_arguments('--fringe-factor', action='store', type=float, dest='fringe_factor', default=0.5,
                            help='seed for the simulation')

    args = my_parser.parse_args()

    input_path = args.input_path








if __name__ == "__main__":
    main()
