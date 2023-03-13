import irsdk
import sched
import time
import socket
from env.settings import CLIENT_ADDRESS

# scheduler set to check for a runnig ir instance every 10 seconds
# when instance is detected this changes to 30 times a second
IDLE_REFRESH_RATE = 10
IN_GAME_REFRESH_RATE = 1/30     #TODO: make the delays changable from the phone app

"""
This function parses the data from irsdk and returns it as a string.
For now it also calculates all the additional data like when given competitor will be in striking distance, fuel required to finish the stint etc.
This will change when I learn some more about kotlin to lessen the computer load.
"""
def select_data(ir: irsdk.IRSDK) -> str:
    # data to send

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
    # their on track position
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
    
    # session
    # -----------------------
    # notes:
    # some of the settings appearing here might change how much data is being sent for other views
    # most of the data here can be sent once at the beginning of the session and then stored (or tracked in case of time of day) on clientside
    # tho idk about weather data, if ir has random weather this might need to be tracked here and sent on change
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
def main_loop(scheduler: sched.scheduler, UDPServerSocket: socket.socket) -> None:
    msg = str.encode("")

    ir = irsdk.IRSDK()      # should this be in the main loop, or main function below?
    ir.startup()

    try:
        ir["TrackName"]         # this is what throws an error when the game client's not running
        scheduler.enter(IN_GAME_REFRESH_RATE, 1, main_loop, (scheduler, UDPServerSocket))
        msg = str.encode(select_data(ir))
    except AttributeError:
        scheduler.enter(IDLE_REFRESH_RATE, 1, main_loop, (scheduler, UDPServerSocket))
        msg = str.encode("iR 404")
    finally:
        UDPServerSocket.sendto(msg, CLIENT_ADDRESS)

    

if __name__ == "__main__":
    UDPServerSocket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
    UDPServerSocket.bind(("localhost", 20002))

    scheduler = sched.scheduler(time.time, time.sleep)
    scheduler.enter(0, 1, main_loop, (scheduler, UDPServerSocket))
    scheduler.run()