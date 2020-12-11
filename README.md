# randomroadrage
A wrapper for SUMO's randomTrips.py to simulate rush hours

## random_road_rage.py
Wrapper for SUMO's randomTrips.py. It will run randomTrips.py multiple times with different settings in order to create approximated rush hours and stitch the results together.  
Takes some of the same options of randomTrips.py and forwards them. Can take percentages of different vehicles and total amount.  
The distribution for the rush hours are hard coded, but can be changed.  
Use `-h` for help message

## calibrate.py
Creates Calibrator elements in the simulation, using traffic data from a data base, to match the traffic from the database more accurately. 
It will ask via command line for the fitting edge, position and sensor id. Or you can use a config file via `'-c', '--id_pos_conf'` that is formatted like this:  

```
edge       pos_on_edge  sensor_id
136101305#1     48      1
493367243#2     5       2
528972756#1     75      3
-139293970      40      4
188642770       42      5
```  
Use `-h` for help message

## config.cfg
Stores the Database connection
