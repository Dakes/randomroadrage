# File to simulate traffic demand using SUMO's randomTrips.py tool.

# Intended to be used for creation of a first model of a city's traffic demand until the output relatively
# matches the city's actual demand to determine where sensors should be placed. Calibration towards sensors data
# follows in *filename*

# author: Daniel Ostertag, Daniel Habermayr

import argparse
import os
import sys
from lxml import etree
from colorama import Fore


class RandomRoadRage:

    def __init__(self, net_file=None, output_path=None, begin=0, end=86400, fringe=5, seed=None,
                 vehicle_types=None, amount=1000):

        self.net_file = net_file
        self.output_path = output_path
        self.begin = begin
        self.end = end
        self.fringe = fringe
        self.seed = seed
        self.vehicle_types = vehicle_types if vehicle_types is not None else {"car": 1}
        self.amount = amount

        self.period = (end - begin) / amount

        # hardcoded rush hours:
        # 0-5, 5-9, 9-17, 17-20, 20-0
        self.intervals = [
            [0, 18000, 0.063],
            [18000, 32400, 0.258],
            [32400, 61200, 0.464],
            [61200, 72000, 0.138],
            [72000, 86400, 0.076]
        ]

    def main(self):
        my_parser = argparse.ArgumentParser(prog='Random Road Rage',
                                            description="A wrapper for SUMO's randomTrips.py to simulate rush hours")

        # Add randomTrips arguments
        my_parser.add_argument('net_file', metavar='input path to sumo net file', type=str,
                               help='define the net file (mandatory)')
        my_parser.add_argument('-b', '--begin', action='store', dest='begin', default=0,
                               help='begin time. (Default 0)')
        my_parser.add_argument('-e', '--end', action='store', dest='end', default=86400,
                               help='end time (Default 86400, 1 day)')
        my_parser.add_argument('--fringe-factor', action='store', type=float, dest='fringe_factor', default=5,
                               help='traffic from outside will be <float> times more likely')
        my_parser.add_argument('-s', '--seed', action='store', type=int, dest='seed', default=1,
                               help='seed for the simulation')

        # Add RRR arguments
        my_parser.add_argument('-o', '--output-path', action='store', dest='output_path',
                               help='define the output path. ')
        my_parser.add_argument('--trk', action='store', type=float, dest='truck_rate', default=0,
                               help='percentage of trucks')
        my_parser.add_argument('--bus', action='store', type=float, dest='bus_rate', default=0,
                               help='percentage of busses')
        my_parser.add_argument('--mc', action='store', type=float, dest='mc_rate', default=0,
                               help='percentage of motorcycles')
        my_parser.add_argument('--ped', action='store', type=float, dest='ped_rate', default=0,
                               help='percentage of pedestrians')
        my_parser.add_argument('--bic', action='store', type=float, dest='bic_rate', default=0,
                               help='percentage of bicycles')
        my_parser.add_argument('-a', '--amount', action='store', type=int, dest='amount', default=1000,
                               help='Generate <int> vehicles with equidistant departure times during simulation')


        args = my_parser.parse_args()
        self.net_file = args.net_file

        min_distance = 1000

        if args.truck_rate:
            self.vehicle_types["truck"] = args.truck_rate
            self.vehicle_types["car"] -= args.truck_rate
        else:
            self.vehicle_types["truck"] = 0
        if args.bus_rate:
            self.vehicle_types["bus"] = args.bus_rate
            self.vehicle_types["car"] -= args.bus_rate
        else:
            self.vehicle_types["bus"] = 0
        if args.mc_rate:
            self.vehicle_types["motorcycle"] = args.mc_rate
            self.vehicle_types["car"] -= args.mc_rate
        else:
            self.vehicle_types["motorcycle"] = 0
        if args.ped_rate:
            self.vehicle_types["pedestrian"] = args.ped_rate
            self.vehicle_types["car"] -= args.ped_rate
        else:
            self.vehicle_types["pedestrian"] = 0
        if args.bic_rate:
            self.vehicle_types["bicycle"] = args.bic_rate
            self.vehicle_types["car"] -= args.bic_rate
        else:
            self.vehicle_types["bicycle"] = 0

        # converting "amount" to randomTrips.py's "period" value
        self.period = (args.end - args.begin) / args.amount

        self.generate()

    def generate(self):
        """

        :return:
        """
        self.output_path = os.path.dirname(self.net_file) if not self.output_path else "Readable code is overrated"
        print(self.output_path)



        # first loop through vehicles, to generate a new file for each type
        for vehicle in self.vehicle_types:
            # set vehicle to passenger, if name is car, for compatibility and easier usage
            vehicle = "passenger" if vehicle == "car" else vehicle
            id = "aua_" + vehicle

            # create xml
            # routes = etree.Element("routes")
            # routes.append(etree.Element("vType"))
            # s = etree.tostring(routes, pretty_print=True)
            # print(routes)

            routes = "<routes>\n\t<vType id=\"" + id + "\" vClass=\"" + vehicle + "\"/>\n</routes>"
            print(routes)
            trips_path = "osm.pedestrian.trips.xml"

            file = open(trips_path)


            for i in self.intervals:
                pass
                


    def set_parameters(self, net_file=None, output_path=None, begin=0, end=86400, fringe=5, seed=None,
                       vehicle_types=None, amount=1000):
        self.net_file = net_file
        self.output_path = output_path
        self.begin = begin
        self.end = end
        self.fringe = fringe
        self.seed = seed
        self.vehicle_types = vehicle_types if vehicle_types is not None else {"car": 1}
        self.amount = amount

if __name__ == "__main__":
    x = RandomRoadRage()
    x.main()