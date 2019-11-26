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
import pandas as pd
import datetime


class Calibrate:

    def __init__(self, net_file=None):
        self.net_file = net_file
        self.id_pos_conf = False
        self.output_path = None

        # step sizes to generate in seconds
        self.step_size = 3600

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
        tree = et.parse(passenger_trips_path)
        root = tree.getroot()

        departs = []
        for trip in root.findall('trip'):
            departs.append(float(trip.get('depart')))
        simulation_length = round(max(departs))

        edge_pos = {}
        edge_sensor = {}
        # read from config, if specified: Lane_id whitespace position new line
        if self.id_pos_conf:
            file = open(self.id_pos_conf, "r")
            contents = file.read()
            contents = contents.split("\n")
            for i in contents:
                # continue if line is empty
                if not i:
                    continue
                edge_pos_sens_tmp = i.split()
                edge_pos[edge_pos_sens_tmp[0]] = edge_pos_sens_tmp[1]
                edge_sensor[edge_pos_sens_tmp[0]] = edge_pos_sens_tmp[2]

        else:
            # read edge ids for calibrator and route probe generation from input, the slow way
            edge_ids = []

            while True:
                tmp_input = input("Please input edge id's, one by one or separated by whitespaces possible. \n"
                                  "If finished Press Enter again to input an empty String: \n")
                # split by default separates whitespaced chars
                for id in tmp_input.split():
                    edge_ids.append(id)
                if not tmp_input or tmp_input.isspace():
                    break

            if not edge_ids:
                print(Fore.RED + "ERROR, no edge ids were input. Exiting")
                sys.exit(1)

            # next read positions of sensors/calibrators on each edge and write to dictionary
            for edge in edge_ids:
                pos = input("Please enter the position of the sensor on edge \"" + edge +
                            "\" . Enter nothing for default 0: \n")
                try:
                    pos = float(pos.replace(',', '.'))
                except ValueError():
                    print(Fore.RED + "No valid number, using 0")
                    pos = 0

                edge_pos[edge] = pos

            # loop for the edge id and sensor id matching
            for edge in edge_ids:
                tmp_input = input("Please input the fitting sensor id in the database for the edge:" + edge + ". \n"
                                  "If finished Press Enter again to input an empty String: \n")
                edge_sensor[edge] = int(tmp_input)

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

        # TODO: excuse me WTF, don't load everything at once.
        # read only min date for start values, pandas is not really required, but convenient
        df = pd.read_sql('SELECT MIN(time) FROM entity', con=self.db_connection)
        df = df["MIN(time)"][0]
        start_hour = df.hour
        start_date = df.date()

        # these are needed to select all entries of only this one day
        db_data_start = datetime.datetime(start_date.year, start_date.month, start_date.day, 0, 0, 0)
        # sql_time_end = datetime.datetime(start_date.year, start_date.month, start_date.day, 23, 59, 59)

        for edge, position in edge_pos.items():
            et_cali = et.SubElement(root, "calibrator",
                                    id="calibtest_edge", edge=edge, pos=position, output="detector.xml")
            begin = 0
            end = self.step_size

            sensor_id = edge_sensor[edge]
            for i in range(sim_h):

                db_fetch_start = db_data_start + self._tick_to_timedelta(begin)
                db_fetch_end = db_data_start + self._tick_to_timedelta(end)
                # TODO: add sensor id
                df = pd.read_sql("SELECT * FROM entity WHERE time BETWEEN {} AND {} AND sensor_id = {}"
                                 .format(db_data_start.strftime("%Y-%m-%d %H:%M:%S"),
                                         db_fetch_end.strftime("%Y-%m-%d %H:%M:%S"), sensor_id), con=self.db_connection)

                # df_hour = df.between_time(self._tick_to_time(begin), self._tick_to_time(end))

                # if df is empty database has no data for this hour, just skip
                if df.empty:
                    continue

                speed = df["speed"].mean()
                veh_per_hour = len(df.index)

                et.SubElement(et_cali, "flow", begin=begin, end=end, vehsPerHour=veh_per_hour, speed=speed, type="t0",
                              departPos="free", departSpeed="max")



                begin = end
                end = end + self.step_size


                # TODO: insert into the_doc


        et.write(calibrators_path, pretty_print=True)

    def _tick_to_timedelta(self, tick, tick_length=1, sim_start_hour=0) -> datetime.timedelta:
        """
        converts a sumo tick to a timedelta object
        :param tick: tick to be converted
        :param tick_length:  tick length in seconds, default: 1 second
        :param sim_start_hour: start of the sumo simulation, to use as start point for the time, default: 0
        :return datetime.timedelta:
        """
        tick = tick * tick_length
        # weird conversion of timedelta to time
        return datetime.timedelta(hours=sim_start_hour, seconds=tick)

if __name__ == "__main__":
    c = Calibrate()
    c.main()
