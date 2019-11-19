"""
Advanced Urban Calibrator

Creates calibrators for SUMO simulations with traffic data from a database to make the simulation more accurate.

Author: Daniel Ostertag
Date: 19.11.2019

"""

import os
import sys
import argparse
from colorama import Fore
import xml.etree.ElementTree as ET


class Calibrate:

    def __init__(self, net_file=None):
        self.net_file = net_file

    def main(self):
        my_parser = argparse.ArgumentParser(prog='Advanced Urban Calibrator',
                                            description="A program to automatically create calibrators for "
                                                        "SUMO simulations with traffic data from a database")

        my_parser.add_argument('net_file', metavar='input path to sumo net file', type=str,
                               help='define the net file (mandatory)')
        my_parser.add_argument('-o', '--output-path', action='store', dest='output_path',
                               help='define the output path. ')

        args = my_parser.parse_args()
        self.net_file = args.net_file
        self.output_path = args.output_path

        if not os.path.isfile(self.net_file):
            print(Fore.RED + "ERROR, path to net file is not valid. Exiting")
            sys.exit(1)

        # read file
        # get output path from net file, if not specified
        self.output_path = os.path.dirname(self.net_file) if not self.output_path else args.output_path
        passenger_trips_path = os.path.join(self.output_path, "osm.passenger.trips.xml")

        # get maximum depart time from passenger trips, to get the length of the simulation
        tree = ET.parse(passenger_trips_path)
        root = tree.getroot()

        departs = []
        for trip in root.findall('trip'):
            departs.append(float(trip.get('depart')))
        simulation_length = round(max(departs))

        # read lane ids for calibrator and route probe generation from input

        lane_ids = []
        for i in 100:
            tmp_input = input("Please input lane id's, one by one or separated by whitespaces possible. \n"
                           "If finished Press Enter again to input an empty String. ")
            # split by default separates whitespaced chars
            for id in tmp_input.split():
                lane_ids.append(id)
            if not tmp_input or tmp_input.isspace():
                break

        if not lane_ids:
            print(Fore.RED + "ERROR, no lane ids were input. Exiting")
            sys.exit(1)

        # next read positions of sensors/calibrators on each lane and write to dictionary
        for id in lane_ids:
            pos = input("Please enter the position of the sensor on lane" + id)
            try:
                pos = float(pos)
            except ValueError():
                print(Fore.RED + "No valid number, exiting")
                sys.exit(1)





if __name__ == "__main__":
    c = Calibrate()
    c.main()
