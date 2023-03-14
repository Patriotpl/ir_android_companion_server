import irsdk
import sched
import time
import socket
from env.settings import CLIENT_ADDRESS, LAPS_TO_CALC_AVG
from itertools import groupby

# scheduler set to check for a runnig ir instance every 10 seconds
# when instance is detected this changes to 30 times a second
IDLE_REFRESH_RATE = 10
IN_GAME_REFRESH_RATE = 1/30     #TODO: make the delays changable from the phone app

# flag indicating if global data pools were initiated
INITIATED = False
# drivers laps data pool
DRIVERS_AND_LAPS = []
# drivers lap times data pool
DRIVERS_AND_LAP_TIMES = []
# drivers pit laps data pool
DRIVERS_AND_PIT_LAPS = []
# drivers and positions data pool
DRIVERS_AND_POSITIONS = []
# CarIdx of tracked driver
TRACKED_DRIVER_ID = 0
# CarIdx of player
PLAYER_ID = 0

def all_equal(iterable) -> bool:
    g = groupby(iterable)
    return next(g, True) and not next(g, False)

def calculate_avg_lap_time() -> float:
    return 0.1

def initiate(drivers: int, player_ID: float) -> None:
    global DRIVERS_AND_LAP_TIMES
    global DRIVERS_AND_LAPS
    global DRIVERS_AND_PIT_LAPS
    global DRIVERS_AND_POSITIONS
    global PLAYER_ID
    DRIVERS_AND_LAP_TIMES = [[] * drivers]
    DRIVERS_AND_LAPS = [[] * drivers]
    DRIVERS_AND_PIT_LAPS = [[] * drivers]
    DRIVERS_AND_POSITIONS = [[] * drivers]
    PLAYER_ID = player_ID

"""
This function parses the data from irsdk and returns it as a string.
For now it also calculates all the additional data like when given competitor will be in striking distance, fuel required to finish the stint etc.
This will change when I learn some more about kotlin to lessen the computer load.
"""
def select_data(ir: irsdk.IRSDK) -> str:
    snapshot = ir

    if not INITIATED:
        initiate(len(ir["DriverInfo"]["Drivers"]), ir["PlayerCarIdx"]) # type: ignore
    
    global DRIVERS_AND_LAP_TIMES
    global DRIVERS_AND_PIT_LAPS
    global LAPS_TO_CALC_AVG
    global DRIVERS_AND_LAPS
    global DRIVERS_AND_POSITIONS
    global TRACKED_DRIVER_ID
    global PLAYER_ID

    # data to send:
    # -----------------------
    # standings:
    # -----------------------
    # notes:
    # this would be the main view of the mobile client once the game instance is detected
    # i think having 70-80% of the view dedicated to standings as a list and 20% to data about particular opponent should be fine here
    # tapping any opponent entry on the list should bring up data about that guys, incl. when he'll be in striking distance, what lap times are needed to catch him / run etc.
    # thus some data might be omitted until the opponents id is passed by the mobile client
    # -----------------------
    # list of competitors
    # their race position
    # their on track position - don't know if sdk does that
    # their class
    # their cars
    # their last laptime
    # their avg laptime (use only last 5 laps, or all race + last 5 laps separately?) - this must be stored inside the script
    # their tire type and age (the latter for later)
    # their pitstop counts (and when they took it?)
    # their predicted place after a pitstop?? probably crap idea
    # wether they're on track, in pits or practicing lawn mowing (when any other than on track maybe you should recalculate laptimes to catch them??)
    # if player's lapping quicker when given competitor will be in striking distance
    # what laptimes would player need to catch up to given competitor 1 lap before race end (maybe make the amount of laps settable from the app?)
    # if they're chasing the player - in how many laps they're in striking distance and what laptimes the player needs to avoid being caught untill the end of session
    # number of mandatory pitstops player and competitors have yet to have cleared (and what needs to be done it these pitstops??)

    drivers = []
    for driver in snapshot["DriverInfo"]["Drivers"]: # type: ignore
        pitting = False
        pos_status = "ok"
        if snapshot["CarIdxOnPitRoad"][driver["CarIdx"]]:
            pos_status = "pit_road"
        elif snapshot["CarIdxInGarage"][driver["CarIdx"]]:  #TODO: check if this means that the car is being serviced, or retired
            pos_status = "garage"
            if snapshot["CarIdxLap"][driver["CarIdx"]] not in DRIVERS_AND_PIT_LAPS[driver["CarIdx"]]:
                DRIVERS_AND_PIT_LAPS[driver["CarIdx"]].append(snapshot["CarIdxLap"][driver["CarIdx"]])
                pitting = True
        drivers.append({
            "number": driver["CarNumber"],
            "name": driver["UserName"],
            "pos_status": pos_status,
        })
        drivers[-1]["car"] = "same" if driver["CarIdx"] != 0 and driver["CarID"] == drivers[0]["CarID"] else driver["CarScreenName"][:3] # type: ignore

        # to do only on first loop or when refresh manually requested
        if snapshot["WeekendInfo"]["WeekendOptions"]["IsFixedSetup"] != 0: # type: ignore
            drivers[-1]["compound"] = snapshot["CarIdxTireCompound"][driver["CarIdx"]]
            if not all_equal(d["CarClassID"] for d in snapshot["Drivers"]):
                for driver in snapshot["DriverInfo"]["Drivers"]: # type: ignore
                    driver["class"] = driver["CarClassID"]

        # to do when driver's position changed
        if snapshot[snapshot["CarIdxPosition"][driver["CarIdx"]]] != DRIVERS_AND_POSITIONS[snapshot["CarIdxPosition"][driver["CarIdx"]]]:
            drivers[-1]["position"] = snapshot["CarIdxPosition"][driver["CarIdx"]]
        
        # to do when driver's pitting
        if pitting:
            drivers[-1]["pit_laps"] = DRIVERS_AND_PIT_LAPS[driver["CarIdx"]]
            drivers[-1]["pits_count"] = len(DRIVERS_AND_PIT_LAPS[driver["CarIdx"]])

        # to do when tracked driver or player completed a lap
        if snapshot["CarIdxLap"][driver["CarIdx"]] != DRIVERS_AND_LAPS[driver["CarIdx"]] and driver["CarIdx"] in [PLAYER_ID, TRACKED_DRIVER_ID]:
            avg_lap_time = round(sum(DRIVERS_AND_LAP_TIMES[driver["CarIdx"]]) / len(DRIVERS_AND_LAP_TIMES[driver["CarIdx"]]), 3)
            drivers[-1]["avg_lap_time"] = avg_lap_time
            drivers[-1]["tire_age"] = DRIVERS_AND_LAPS[driver["CarIdx"]] - DRIVERS_AND_PIT_LAPS[driver["CarIdx"]] if len(DRIVERS_AND_PIT_LAPS[driver["CarIdx"]]) > 0 else DRIVERS_AND_LAPS[driver["CarIdx"]]
            drivers[-1]["last_lap_time"] = snapshot["CarIdxLastLapTime"][driver["CarIdx"]]
            laps_to_strike = -1
            if avg_lap_time > DRIVERS_AND_LAP_TIMES[PLAYER_ID]:
                #laps_to_strike =   # maybe do this by summing up target drivers laptimes (all of them) and comparing to players?
                pass 

        # to do when any other driver completed a lap
        elif snapshot["CarIdxLap"][driver["CarIdx"]] != DRIVERS_AND_LAPS[driver["CarIdx"]] and driver["CarIdx"] not in [PLAYER_ID, TRACKED_DRIVER_ID]:
            # store data for later calculations
            DRIVERS_AND_LAP_TIMES[driver["CarIdx"]].append(snapshot["CarIdxLastLapTime"][driver["CarIdx"]])
            if len(DRIVERS_AND_LAP_TIMES[driver["CarIdx"]]) > LAPS_TO_CALC_AVG:
                DRIVERS_AND_LAP_TIMES[driver["CarIdx"]] = DRIVERS_AND_LAP_TIMES[driver["CarIdx"]][1:]

            # prep data for sending
            drivers[-1]["avg_lap_time"] = round(sum(DRIVERS_AND_LAP_TIMES[driver["CarIdx"]]) / len(DRIVERS_AND_LAP_TIMES[driver["CarIdx"]]), 3)
            drivers[-1]["tire_age"] = DRIVERS_AND_LAPS[driver["CarIdx"]] - DRIVERS_AND_PIT_LAPS[driver["CarIdx"]] if len(DRIVERS_AND_PIT_LAPS[driver["CarIdx"]]) > 0 else DRIVERS_AND_LAPS[driver["CarIdx"]]
            drivers[-1]["last_lap_time"] = snapshot["CarIdxLastLapTime"][driver["CarIdx"]]
    
    # session
    # -----------------------
    # notes:
    # some of the settings appearing here might change how much data is being sent for other views
    # most of the data here can be sent once at the beginning of the session and then stored (or tracked in case of time of day) on clientside
    # tho idk about weather data, if snapshot has random weather this might need to be tracked here and sent on change
    # refresh data button on the client's side will be helpful anyway
    # -----------------------
    # track name
    # time of day
    # weather data (wind, temp, rain - if it exists in ir)
    # lapped or timed?
    # if lapped current lap / laps total
    # if timed time untill the end of session and estimated total laps (use quali times, session best or session avg?)
    # fp, qual or race?
    # fixed of customizable setups?
    # if fixed data about opponents tire types can be omitted
    # mandatory pitstop or not?
    # if not data about opponenets pitstops can be omitted 

    # pitstop
    # -----------------------
    # notes:
    # most of this data can be omitted and only sent on changes to reduce payloads
    # -----------------------
    # tyre compound (is it even a thing in ir?)
    # tyre pressures
    # tyre (and brake??) temps
    # car state
    # car damage
    # estimated pit time??
    # fuel usage (overall and last lap or last x laps avg?)
    # fuel to add (with est how much fuel needed to the end of race / stint?)

    # laptimes
    # -----------------------
    # notes:
    # most of this data can be omitted and only sent on changes to reduce payloads
    # -----------------------
    # players laptimes
    # which players laps were invalid
    # players best and optimal laptime (both valid and invalid) in current session
    # overall session best laptime
    # players current laptime (can be tracked clientside i think?; this might actually be useless)
    # players all time best and optimal laptime?

    return str(ir["TrackName"])

"""
This is the function containing the basic loop of the application.
It simply tries to grab the data from api and preps the next scheduller event.
If trying to get the data fails the delay is set to 10 seconds.
Else delay is set to 1/30 of a second.
"""
def main_loop(scheduler: sched.scheduler, UDPServerSocket: socket.socket, ir: irsdk.IRSDK) -> None:
    msg = str.encode("")

    if not ir.is_connected:   
        #UDPServerSocket.sendto(str.encode("iR 404"), CLIENT_ADDRESS)    #blocked for testing without connection to client
        scheduler.enter(IDLE_REFRESH_RATE, 1, main_loop, (scheduler, UDPServerSocket, ir))
        return

    msg = str.encode(select_data(ir))
    UDPServerSocket.sendto(msg, CLIENT_ADDRESS)
    scheduler.enter(IN_GAME_REFRESH_RATE, 1, main_loop, (scheduler, UDPServerSocket, ir))    

if __name__ == "__main__":
    ir = irsdk.IRSDK()
    ir.startup()

    UDPServerSocket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
    UDPServerSocket.bind(("localhost", 20002))

    scheduler = sched.scheduler(time.time, time.sleep)
    scheduler.enter(0, 1, main_loop, (scheduler, UDPServerSocket, ir))
    scheduler.run()