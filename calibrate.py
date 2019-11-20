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
        self.id_pos_conf = False
        self.output_path = None

    def main(self):
        my_parser = argparse.ArgumentParser(prog='Advanced Urban Calibrator',
                                            description="A program to automatically create calibrators for "
                                                        "SUMO simulations with traffic data from a database")

        my_parser.add_argument('net_file', metavar='input path to sumo net file', type=str,
                               help='define the net file (mandatory)')
        my_parser.add_argument('-o', '--output-path', action='store', dest='output_path', default=None,
                               help='define the output path. ')
        my_parser.add_argument('-c', '--id_pos_conf', action='store', dest='id_pos_conf', default=False,
                               help='define the output path. ')

        args = my_parser.parse_args()
        self.net_file = args.net_file
        self.output_path = args.output_path
        self.id_pos_conf = args.id_pos_conf if os.path.isfile(args.pos_conf) else False

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

        lane_pos = {}
        # read from config, if specified: Lane_id whitespace position new line
        if self.id_pos_conf:
            file = open(self.id_pos_conf, "r")
            contents = file.read()
            contents = contents.split("\n")
            for i in contents:
                # continue if line is empty
                if not i:
                    continue
                lane_pos_tmp = i.split()
                lane_pos[lane_pos_tmp[0]] = lane_pos_tmp[1]

        else:
            # read lane ids for calibrator and route probe generation from input, the slow way
            lane_ids = []
            # random 100 for a sensor cap
            for i in range(100):
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
            for lane_id in lane_ids:
                pos = input("Please enter the position of the sensor on lane" + lane_id)
                try:
                    pos = float(pos.replace(',', '.'))
                except ValueError():
                    print(Fore.RED + "No valid number, exiting")
                    sys.exit(1)

                lane_pos[lane_id] = pos





if __name__ == "__main__":
    c = Calibrate()
    c.main()
