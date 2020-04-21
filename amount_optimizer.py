"""
Intended to find an amount of vehicles optimal to approximate the real world amount
Comparing database entries from data_generator and actual sensor data to update the total the amount

"""


import os
import numpy as np
import mysql.connector
import configparser

# TODO: EXCEPTION HANDLING
# TODO: TYPE HINTS
# TODO: PROPER DOCUMENTATION


class AmountOptimizer:

    def __init__(self):
        # TODO: make pretty + make db_connection to server, not to localhosts
        config_path = "/home/daniel/PycharmProjects/randomroadrage/config.cfg"

        config = configparser.ConfigParser()
        config.read(config_path)

        try:
            self.con = mysql.connector.connect(**config['mysql'])
        except mysql.connector.Error as err:
            print(err.msg)
            exit(1)

    def main(self):

        # TODO: make these params arguments, not hardcoded values
        amount = 100000
        ffactor = 15
        sim_dir = "/home/daniel/Sumo/sumo/tools/Dachau2/Dachau"
        gen_dir = "/home/daniel/PycharmProjects/data_generator"
        dbname_real_sensors = "dachau"
        dbname_sim_sensors = "simulated_dachau"
        # a list of sensors that distort the difference and therefore the calculation due to SUMO pathing weaknesses. -> will nevertheless be simulated through calibrators
        bad_sensors = []


        # TODO: make this value either argument or retrieve it through query
        num_sensors = 13
        new_amount = amount
        # the following param is not really used, it is an idea to improve this script in the future
        new_ffactor = ffactor
        last_change = int (amount / 2)

        real_amounts = self.get_sensor_amounts(num_sensors, dbname_real_sensors)
        print("Real amounts are: ", real_amounts)
        while(True):

            simulated_amounts = self.get_sensor_amounts(num_sensors, dbname_sim_sensors)
            print("Simulated amounts currently are: ", simulated_amounts)
            diff = self.calculate_differences(real_amounts, simulated_amounts)
            print("Current amount of %s with fringe-factor of %s leads to difference of %s" % (new_amount, new_ffactor, diff))

            # these numbers for edge cases have sadly been chosen randomly / intuitively
            if -2000 < diff & diff < 2000:
                print("Feierabend!")
                break
            if -100 < last_change & last_change < 100:
                print("Feierabend v2!")
                break
            if new_amount > 200001:
                print("Ab hier helfen die Calibratoren. Base amount über 200.000 für eine 70.000 Stadt scheint zu unrealistisch, besonders da das Aufkommen ja noch erhöht wird um was auch immer den Calibs fehlt. Fringe erhöhen?")
                break
            if diff < 0:
                if last_change < 0:
                    last_change = int (np.absolute(last_change) / 2)
                new_amount += last_change
            if diff > 0:
                if last_change > 0:
                    last_change = int ((- last_change) / 2)
                new_amount += last_change

            # clear old simulation
            print("Clearing entries of last simulation ...")
            cursor = self.con.cursor()
            cursor.execute("USE " + dbname_sim_sensors + ";")
            cursor.execute("DELETE FROM entity;")
            self.con.commit()
            cursor.close()

            # call random_road_rage
            print("Calling rrr ...")
            os.system("python random_road_rage.py /home/daniel/Sumo/sumo/tools/Dachau2/Dachau/osm.net.xml --fringe-factor %s --trk 0.01 --bus 0.005 --mc 0.1 --bic 0.01 -a %s" % (new_ffactor, new_amount))
            print("rrr finished successfully.")

            # start simulation
            print("starting simulation ...")
            os.system("sumo -c " + sim_dir + "/osm.sumocfg")
            print("Simulation has ended successfully.")

            # write sim output to database
            print("Writing simulation output into database ...")
            os.system("python " + gen_dir + "/generator.py /home/daniel/Sumo/sumo/tools/Dachau2/Dachau/sensor_output.xml -c simulated_dachau -s /home/daniel/Sumo/sumo/tools/Dachau2/Dachau/sensor_file.csv")
            print("Finished writing.")

        print("Ende Gelände!")

    def calculate_differences(self, real_amounts, simulated_amounts):
        """
        Purpousfully not with absolute differences, so that program knows whether amount is too big or too small
        Negative results suggest amount is too little and should be higher next iteration
        :arg
        """
        difference = 0
        for i in range(len(real_amounts)):
            difference += simulated_amounts[i] - real_amounts[i]
        return difference

    def get_sensor_amounts(self, num_sensors, dbname):
        """
        Since the databases for real & simulated sensor data are of equivalent structure, one function suffices
        Returns an array of amount of each sensor
        :arg num_sensors for easier iteration &
        :arg dbname to distinguish between real and simulated
        """
        amounts = []
        cursor = self.con.cursor()
        # TODO: make next line common case friendly
        cursor.execute("USE " + dbname + ";")
        for i in range(num_sensors):
            query = "SELECT COUNT(id) FROM entity WHERE sensor_id = %s" % (i+1)
            cursor.execute(query)
            tmp = cursor.fetchone()[0]
            amounts.append(tmp)
            self.con.commit()
            cursor.close()
        return amounts


if __name__ == "__main__":
    ao = AmountOptimizer()
    ao.main()


# gen params
# /home/daniel/Sumo/sumo/tools/Dachau2/Dachau/sensor_output.xml -c simulated_dachau -s /home/daniel/Sumo/sumo/tools/Dachau2/Dachau/sensor_file.csv