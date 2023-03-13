import irsdk
import sched
import time
import socket
from env.settings import CLIENT_ADDRESS

# scheduler set to check for a runnig ir instance every 10 seconds
# when instance is detected this changes to 30 times a second
IDLE_REFRESH_RATE = 10
IN_GAME_REFRESH_RATE = 1/30     #TODO: make the delays changable from the phone app

def select_data(ir: irsdk.IRSDK) -> str:
    #TODO: choose data to send
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