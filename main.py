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
    # track name
    # time of day
    # lapped or timed?
    # if lapped current lap / laps total
    # if timed time untill the end of session and estimated total laps (use quali times, session best or session avg?)
    # fp, qual or race?
    # fixed of customizable setups?
    # if fixed data about opponents tire types can be omitted
    # mandatory pitstop or not?
    # if not data about opponenets pitstops can be omitted 
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