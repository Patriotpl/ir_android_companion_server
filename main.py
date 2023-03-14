import irsdk
import sched
import time

# scheduler set to check for a runnig ir instance every 10 seconds
# when instance is detected this changes to 30 times a second
IDLE_REFRESH_RATE = 10
IN_GAME_REFRESH_RATE = 1/30     #TODO: make the delays changable from the phone app

"""
This is the main function containing the basic loop of the application.
It simply tries to grab the data from api and preps the next scheduller event.
If trying to get the data fails the delay is set to 10 seconds.
Else delay is set to 1/30 of a second.
"""
def main_loop(scheduler: sched.scheduler, prev_ir: irsdk.IRSDK | None = None) -> None:
    try:
        ir = irsdk.IRSDK()      # should this be in the main loop, or main function below?
        ir.startup()

        ir["TrackName"]         # this is what throws an error when the game client's not running
    except AttributeError:
        scheduler.enter(IDLE_REFRESH_RATE, 1, main_loop, (scheduler,))
        print("iRacing is not running.")
        return

    scheduler.enter(IN_GAME_REFRESH_RATE, 1, main_loop, (scheduler, ir))
    print("iRacing is running.")

if __name__ == "__main__":
    scheduler = sched.scheduler(time.time, time.sleep)
    scheduler.enter(0, 1, main_loop, (scheduler,))
    scheduler.run()