# File to simulate traffic demand using SUMO's randomTrips.py tool.

# Intended to be used for creation of a first model of a city's traffic demand until the output relatively
# matches the city's actual demand to determine where sensors should be placed. Calibration towards sensors data
# follows in *filename*

# author: Daniel Ostertag, Daniel Habermayr

import argparse
import os
import sys
from colorama import Fore

class Random_road_rage:

    def __init__(self):
        if __name__ == "__main__":
            pass
        else:
            sys.exit(1)

    def main(self):
        my_parser = argparse.ArgumentParser(prog='Random Road Rage',
                                            description="A wrapper for SUMO's randomTrips.py to simulate rush hours")

        # Add randomTrips arguments
        my_parser.add_argument('net_file', metavar='input_path to sumo net file', type=str,
                               help='define the net file (mandatory)')
        my_parser.add_argument('-o', '--output-trip-file', action='store', dest='tripfile',
                               help='define the output trip filename. ')
        my_parser.add_argument('-b', '--begin', action='store', dest='begin', default=0,
                               help='begin time. (Default 0)')
        my_parser.add_argument('-e', '--end', action='store', dest='end', default=86400,
                               help='end time (Default 86400, 1 day)')
        my_parser.add_argument('--fringe-factor', action='store', type=float, dest='fringe_factor', default=5,
                               help='traffic from outside will be <float> times more likely')
        my_parser.add_argument('-s', '--seed', action='store', type=int, dest='seed', default=1,
                               help='seed for the simulation')

        # Add RRR arguments
        my_parser.add_argument('--trk', action='store', type=float, dest='truck_rate', default=0,
                               help='percentage of trucks')
        my_parser.add_argument('--bus', action='store', type=float, dest='bus_rate', default=0,
                               help='percentage of busses')
        my_parser.add_argument('--mc', action='store', type=float, dest='mc_rate', default=0,
                               help='percentage of motorcycles')
        my_parser.add_argument('--ped', action='store', type=float, dest='ped_rate', default=0,
                               help='percentage of pedestrians')
        my_parser.add_argument('-a', '--amount', action='store', type=int, dest='amount', default=1000,
                               help='Generate <int> vehicles with equidistant departure times during simulation')


        args = my_parser.parse_args()
        input_path = args.net_file

        min_distance = 1000

        vehicle_types = {"car": 1}
        if args.truck_rate:
            vehicle_types["truck"] = args.truck_rate
            vehicle_types["car"] -= args.truck_rate
        if args.bus_rate:
            vehicle_types["bus"] = args.bus_rate
            vehicle_types["car"] -= args.bus_rate
        if args.mc_rate:
            vehicle_types["motorcycles"] = args.mc_rate
            vehicle_types["car"] -= args.mc_rate
        if args.ped_rate:
            vehicle_types["pedestrians"] = args.ped_rate
            vehicle_types["car"] -= args.ped_rate

        # converting "amount" to randomTrips.py's "period" value
        period = (args.end - args.begin) / args.amount



if __name__ == "__main__":
    x = Random_road_rage
    x.main()