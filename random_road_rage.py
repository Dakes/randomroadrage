# File to simulate traffic demand using SUMO's randomTrips.py tool.

# Intended to be used for creation of a first model of a city's traffic demand until the output relatively
# matches the city's actual demand to determine where sensors should be placed. Calibration towards sensors data
# follows in *filename*

# author: Daniel Ostertag, Daniel Habermayr

import argparse
import os
import sys
from xml.dom import minidom
from random import randint
from colorama import Fore


class RandomRoadRage:

    def __init__(self, net_file=None, output_path=None, begin=0, end=86400, fringe=5, seed=None,
                 vehicle_types=None, amount=1000):

        self.net_file = net_file
        self.output_path = os.path.dirname(self.net_file) if not "output_path" in locals() else output_path
        self.begin = begin
        self.end = end
        self.fringe = fringe
        self.seed = randint(0, 999999) if seed is None else seed
        self.vehicle_types = vehicle_types if vehicle_types is not None else {"car": 1}
        self.amount = amount

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

        # get relative output path from net file, if not specified
        self.output_path = os.path.dirname(self.net_file) if not self.output_path else args.output_path

        # set vehicle rates and reduce car ratio
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

        self.seed = args.seed
        self.amount = args.amount

        self.begin = int(args.begin)
        self.end = int(args.end)

        self.adjust_intervals()

        self.generate()

    def generate(self):
        """
        actual function to generate and write the files
        :return:
        """

        # first loop through vehicles, to generate a new file for each type
        for vehicle in self.vehicle_types:
            # set vehicle to passenger, if name is car, for compatibility and easier usage
            v_class = "passenger" if vehicle == "car" else vehicle
            id = "aua_" + vehicle

            routes = "<routes>\n\t<vType id=\"" + id + "\" vClass=\"" + v_class + "\"/>"
            # generate blank xml files, closing xml tag will be writte later
            trips_file_name = "osm." + v_class + ".trips.xml"
            file_path = os.path.join(self.output_path, trips_file_name)
            file = open(file_path, "w+")
            file.write(routes)
            file.close()

            # close xml tag and continue, if no vehicles were specified
            if not self.vehicle_types[vehicle]:
                file = open(file_path, "a")
                file.write("\n</routes>")
                file.close()
                continue

            # open file again in append mode
            file = open(file_path, "a")
            file.write("\n")

            # calculate each vehicle_amount with the current fraction
            vehicle_amount = self.amount * self.vehicle_types[vehicle]

            for idx, item in enumerate(self.intervals):
                # calculate period with ((end - start) / veh.amount ) but first multiply with rush hours
                period = (item[1] - item[0]) / (vehicle_amount * item[2])

                os.system(
                    "python randomTrips.py -n %s -o .tmp.xml -b %s -e %s -p %s --fringe-factor %s -s %s --prefix %s" %
                    (self.net_file, item[0], item[1], period, self.fringe, self.seed, (vehicle[:3]+"_"+str(idx)+"_")))

                # After use increment seed, so cars start on different edges
                self.seed += 1
                tmp_xml = minidom.parse('.tmp.xml')
                element_list = tmp_xml.getElementsByTagName("trip")
                # write trip tags to file
                [file.write("\t" + i.toprettyxml(indent='\t', newl='\n', encoding=None)) for i in element_list]

            # close xml file with closing tag
            file.write("\n</routes>")
            file.close()

    def set_parameters(self, net_file=None, output_path=None, begin=0, end=86400, fringe=5, seed=None,
                       vehicle_types=None, amount=1000):
        self.net_file = net_file
        self.output_path = output_path
        self.begin = begin
        self.end = end
        self.fringe = fringe
        self.seed = randint(0, 999999) if seed is None else seed
        self.vehicle_types = vehicle_types if vehicle_types is not None else {"car": 1}
        self.amount = amount

    def adjust_intervals(self) -> list:
        """
        needed for intervals smaller than [0; 86,400]
        :return: a new list of lists containing percentage values relative to the original hardcoded ones for one day
        """
        print("in adjust intervals")
        print(self.begin, self.end)

        if self.begin == 0 and self.end == 86400:
            return self.intervals
        if self.begin >= 86399 or self.end <= 1 or self.begin >= self.end:
            print("inadequate parameters, try again.")
            return []
        new_intervals = []

        # determine first to last relevant interval
        # interval: [begin, end, percentage]
        for interval in self.intervals:
            print(new_intervals)
            if interval[0] <= self.begin < interval[1]:
                temp = [self.begin, interval[1], interval[2]]
                new_intervals.append(temp)
            elif self.begin < interval[0] and interval[1] < self.end:
                new_intervals.append(interval)
            elif interval[0] < self.end <= interval[1]:
                temp = [interval[0], self.end, interval[2]]
                new_intervals.append(temp)
                print("breaking")
                break

        # adjusting the demand percentages of the new intervals to interval length and demand of the entire simulation
        entire_demand = 0
        for interval in new_intervals:
            entire_demand = entire_demand + ((interval[1] - interval[0]) * interval[2])
        for interval in new_intervals:
            interval[2] = ((interval[1] - interval[0]) * interval[2]) / entire_demand
        print("new intervals: \n", new_intervals)
        print(entire_demand)



if __name__ == "__main__":
    rrr = RandomRoadRage()
    rrr.main()
