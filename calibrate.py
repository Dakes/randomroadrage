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
from lxml import etree as et
# import xml.etree.ElementTree as et
import pandas as pd
import datetime


class Calibrate:

    def __init__(self, sumocfg=None):
        self.sumocfg = sumocfg
        self.id_pos_conf = False
        self.output_path = None
        self.start_date = None

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

        my_parser.add_argument('sumocfg', metavar='input path to sumocfg file', type=str,
                               help='define the net file (mandatory)')
        my_parser.add_argument('-o', '--output-path', action='store', dest='output_path', default=None,
                               help='define the output path. ')
        my_parser.add_argument('-c', '--id_pos_conf', action='store', dest='id_pos_conf', default=False,
                               help='The configuration file to quickly define edges with fitting position and sensor_id')
        my_parser.add_argument('-s', '--start_date', action='store', dest='start_date', default=False,
                               help='Override for the start date for the data base fetches. '
                                    'That way you can pick a specific date instead of using the default first in the db'
                                    'It needs to be given in the form YYYY-mm-dd')

        args = my_parser.parse_args()
        self.sumocfg = args.sumocfg
        self.output_path = args.output_path
        self.id_pos_conf = args.id_pos_conf if os.path.isfile(args.id_pos_conf) else False
        self.start_date = args.start_date if self.check_date(args.start_date) else None

        if not os.path.isfile(self.sumocfg):
            print(Fore.RED + "ERROR, path to net file is not valid. Exiting")
            sys.exit(1)

        # read file
        # get output path from net file, if not specified
        self.output_path = os.path.dirname(self.sumocfg) if not self.output_path else args.output_path
        passenger_trips_path = os.path.join(self.output_path, "osm.passenger.trips.xml")

        # get maximum depart time from passenger trips, to get the length of the simulation
        tree = et.parse(passenger_trips_path)
        root = tree.getroot()

        departs = []
        for trip in root.findall('trip'):
            departs.append(float(trip.get('depart')))
        simulation_length = round(max(departs))
        print("Length of simulation:", simulation_length)

        edge_pos = {}
        edge_sensor = {}
        edge_ids = []
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
                edge_ids.append(edge_pos_sens_tmp[0])

        else:
            # read edge ids for calibrator and route probe generation from input, the slow way
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

        calibrators_path = os.path.join(self.output_path, "calibrator.xml")

        root = et.Element('additional')
        et.SubElement(root, 'vType', id="t0", speedDev="0.1", speedFactor="1.2", sigma="0")
        for edge in edge_ids:
            et.SubElement(root, 'routeProbe', id="probe_" + edge, edge=edge, freq="60", file="routeProbe_output.xml")

        # TODO: for the moment assume the start is always at 0:00, Data in Database must fit

        # one flow element each hour, calculate number of hours
        sim_h = round(simulation_length / 3600)
        print(sim_h, "hour(s) simulated")

        # read only min date for start values, pandas is not really required, but convenient
        df = pd.read_sql('SELECT MIN(time) FROM entity', con=self.db_connection)
        df = df["MIN(time)"][0]
        # start_hour = df.hour
        start_date = df.date()

        # get the start date for the db fetch. By default the first date in db.
        if not self.start_date:
            db_data_start = datetime.datetime(start_date.year, start_date.month, start_date.day, 0, 0, 0)
        else:
            db_data_start = datetime.datetime.strptime(self.start_date, '%Y-%m-%d')

        for edge, position in edge_pos.items():
            et_cali = et.SubElement(root, "calibrator", id="calib_"+edge, edge=edge, pos=position,
                                    output="detector.xml", routeProbe="probe_"+edge)
            begin = 0
            end = self.step_size

            sensor_id = edge_sensor[edge]
            for i in range(sim_h):

                db_fetch_start = db_data_start + self._tick_to_timedelta(begin)
                db_fetch_end = db_data_start + self._tick_to_timedelta(end)

                sql_select = "SELECT * FROM entity WHERE time BETWEEN \"{}\" AND \"{}\" AND sensor_id = {}"\
                    .format(db_fetch_start.strftime("%Y-%m-%d %H:%M:%S"),
                            db_fetch_end.strftime("%Y-%m-%d %H:%M:%S"), sensor_id)
                df = pd.read_sql(sql_select, con=self.db_connection)

                # if df is empty database has no data for this hour, just skip
                # TODO: change so that calibrator has 0 cars
                if df.empty:
                    begin = end
                    end = end + self.step_size
                    continue

                speed = df["mean_velocity"].mean()
                veh_per_hour = len(df.index)

                et.SubElement(et_cali, "flow", begin=str(begin), end=str(end), vehsPerHour=str(veh_per_hour),
                              speed=str(speed), type="t0", departPos="free", departSpeed="max")

                begin = end
                end = end + self.step_size

        calibrator = et.ElementTree(root)
        calibrator.write(calibrators_path, pretty_print=True)

        # add calibrator.xml to osm.sumocfg

        tree = et.parse(self.sumocfg)
        root = tree.getroot()

        for i, tag in enumerate(root):
            if tag.tag == "input":
                for j, tag in enumerate(root[i]):
                    if tag.tag == "additional-files":
                        val = root[i][j].get("value")
                        if "calibrator.xml" in val:
                            break
                        else:
                            root[i][j].set("value", val + ",calibrator.xml")
        calibrator = et.ElementTree(root)
        calibrator.write(self.sumocfg, pretty_print=True)

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

    """
    Function to check dates for the format YYY-mm-dd
    """
    def check_date(self, date_text):
        try:
            datetime.datetime.strptime(date_text, '%Y-%m-%d')
        except ValueError:
            raise ValueError("Incorrect data format, should be YYYY-MM-DD")
        return date_text

if __name__ == "__main__":
    c = Calibrate()
    c.main()
