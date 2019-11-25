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
from colorama import Fore
import xml.etree.ElementTree as et
import lxml.etree
import lxml.builder
import pandas as pd
import datetime


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
        self.id_pos_conf = args.id_pos_conf if os.path.isfile(args.id_pos_conf) else False

        if not os.path.isfile(self.net_file):
            print(Fore.RED + "ERROR, path to net file is not valid. Exiting")
            sys.exit(1)

        # read file
        # get output path from net file, if not specified
        self.output_path = os.path.dirname(self.net_file) if not self.output_path else args.output_path
        passenger_trips_path = os.path.join(self.output_path, "osm.passenger.trips.xml")

        # get maximum depart time from passenger trips, to get the length of the simulation
        # TODO: change to lxml to delete one import
        tree = et.parse(passenger_trips_path)
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
                                  "If finished Press Enter again to input an empty String. \n")
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
                pos = input("Please enter the position of the sensor on edge \"" + edge_id +
                            "\" . Enter nothing for default 0: \n")
                try:
                    pos = float(pos.replace(',', '.'))
                except ValueError():
                    print(Fore.RED + "No valid number, using 0")
                    pos = 0

                edge_pos[edge_id] = pos

        calibrators_path = os.path.join(self.output_path, "calibrators.xml")
        # E = lxml.builder.ElementMaker()

        root = et.Element('additional')
        et.SubElement(root, 'vType', id="t0", speedDev="0.1", speedFactor="1.2", sigma="0")
        # TODO: automate generation
        et.SubElement(root, 'routeProbe', id="probe_171130153#1", edge="171130153#1", freq="60",
                      file="routeProbe_output.xml")

        # TODO: for the moment assume the start is always at 0:00, Data in Database must fit
        # TODO: count data from database and calculate

        # one flow element each hour, calculate number of hours
        sim_h = round(simulation_length / 3600)
        begin = 0
        end = 3600

        # TODO: excuse me WTF, don't load everything at once.
        df = pd.read_sql('SELECT * FROM entity', con=self.db_connection)
        df = df.sort_values(by=['time'])
        start_hour = df['time'][0].hour
        start_date = df['time'][0].date()

        # these are needed to select all entries of only this one day
        sql_time_start = datetime.datetime(start_date.year, start_date.month, start_date.day, 0, 0, 0)
        sql_time_end = datetime.datetime(start_date.year, start_date.month, start_date.day, 23, 59, 59)

        df_day = df.loc[sql_time_start:sql_time_end]

        for edge, position in edge_pos.items():
            et_cali = et.SubElement(root, "calibrator",
                                    id="calibtest_edge", edge=edge, pos=position, output="detector.xml")

            for i in range(sim_h):

                df_hour = df.between_time(self._tick_to_time(begin), self._tick_to_time(end))

                speed = df_hour["speed"].mean()
                veh_per_hour = len(df_hour.index)

                et.SubElement(et_cali, "flow", begin=begin, end=end, vehsPerHour=veh_per_hour, speed="27.8", type="t0",
                              departPos="free", departSpeed="max")



                # if df is empty database has no data for this hour, just skip
                if df_hour.empty:
                    continue


                begin = end
                end = end + 3600


                # TODO: insert into the_doc

        # TODO remove both flows, replace with insert later, repeat for other stuff

        et.write(calibrators_path, pretty_print=True)

    def _tick_to_time(self, tick, tick_length=1, sim_start_hour=0) -> datetime.time:
        """
        converts a sumo tick to a time object
        :param tick: tick to be converted
        :param tick_length:  tick length in seconds, default: 1 second
        :param sim_start_hour: start of the sumo simulation, to use as start point for the time, default: 0
        :return datetime.time:
        """
        tick = tick * tick_length
        # weird conversion of timedelta to time
        return (datetime.datetime.min + datetime.timedelta(hours=sim_start_hour, seconds=tick)).time()

if __name__ == "__main__":
    c = Calibrate()
    c.main()
