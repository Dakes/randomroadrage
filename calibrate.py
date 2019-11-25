"""
Advanced Urban Calibrator

Creates calibrators for SUMO simulations with traffic data from a database to make the simulation more accurate.

Author: Daniel Ostertag
Date: 19.11.2019

"""

import os
import sys
import argparse
import configparser
from sqlalchemy import create_engine
import pymysql
from colorama import Fore
import xml.etree.ElementTree as ET
import lxml.etree
import lxml.builder
import pandas as pd


class Calibrate:

    def __init__(self, net_file=None):
        self.net_file = net_file
        self.id_pos_conf = False
        self.output_path = None

        config = configparser.ConfigParser()
        config.read("config.cfg")

        # needed for pandas read_sql
        db_connection_str = "mysql+pymysql://" + config['mysql']['user'] + ":" + config['mysql']['password'] + "@" + \
                            config['mysql']['host'] + "/" + config['mysql']['database']
        self.db_connection = create_engine(db_connection_str)

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
        # TODO: change to lxml to delete one import
        tree = ET.parse(passenger_trips_path)
        root = tree.getroot()

        departs = []
        for trip in root.findall('trip'):
            departs.append(float(trip.get('depart')))
        simulation_length = round(max(departs))

        edge_pos = {}
        # read from config, if specified: Lane_id whitespace position new line
        if self.id_pos_conf:
            file = open(self.id_pos_conf, "r")
            contents = file.read()
            contents = contents.split("\n")
            for i in contents:
                # continue if line is empty
                if not i:
                    continue
                edge_pos_tmp = i.split()
                edge_pos[edge_pos_tmp[0]] = edge_pos_tmp[1]

        else:
            # read edge ids for calibrator and route probe generation from input, the slow way
            edge_ids = []
            # random 100 for a sensor cap
            for i in range(100):
                tmp_input = input("Please input edge id's, one by one or separated by whitespaces possible. \n"
                                  "If finished Press Enter again to input an empty String. ")
                # split by default separates whitespaced chars
                for id in tmp_input.split():
                    edge_ids.append(id)
                if not tmp_input or tmp_input.isspace():
                    break

            if not edge_ids:
                print(Fore.RED + "ERROR, no edge ids were input. Exiting")
                sys.exit(1)

            # next read positions of sensors/calibrators on each edge and write to dictionary
            for edge_id in edge_ids:
                pos = input("Please enter the position of the sensor on edge" + edge_id +
                            ". Enter nothing for default 0")
                try:
                    pos = float(pos.replace(',', '.'))
                except ValueError():
                    print(Fore.RED + "No valid number, using 0")
                    pos = 0

                edge_pos[edge_id] = pos

        calibrators_path = os.path.join(self.output_path, "calibrators.xml")
        E = lxml.builder.ElementMaker()

        the_doc = E.additional
        (
            E.vType(id="t0", speedDev="0.1", speedFactor="1.2", sigma="0"),
            E.routeProbe(id="probe_171130153#1", edge="171130153#1", freq="60", file="routeProbe_output.xml"),
            E.calibrator
            (
                E.flow(begin="0", end="1800", route="cali1_fallback", vehsPerHour="512", speed="27.8", type="t0",
                       departPos="free", departSpeed="max"),

                id='calibtest_edge', edge="171130153#1", pos="15", output="detector.xml"),
        )
        et = lxml.etree.ElementTree(the_doc)
        et.write(calibrators_path, pretty_print=True)

        # TODO: count data from database, for the moment assume the start is always at 0:00
        veh_per_hour = 666
        speed = 33.33

        # one flow element each hour
        sim_h = round(simulation_length / 3600)
        begin = 0
        end = "3600"
        for i in range(sim_h):
            E.flow(begin=begin, end=end, vehsPerHour=veh_per_hour, speed=speed, type="t0",
                   departPos="free", departSpeed="max")
            begin = end
            end = end + 3600

        # TODO remove both flows, replace with insert later, repeat for other stuff




if __name__ == "__main__":
    c = Calibrate()
    c.main()
