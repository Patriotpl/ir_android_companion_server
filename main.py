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

        ir["TrackName"]         # this is needed for checking if ir object is NoneType
    except AttributeError:
        scheduler.enter(IDLE_REFRESH_RATE, 1, main_loop, (scheduler,))
        print("iRacing is not running.")
        return
    
    else:
        # the below part was meant to check if the iR process has been closed
        # but the WMI().Win32_Process() takes ~3seconds to execute
        # which makes the refreshrate f itself

        # # if the game client closes api keeps on return data from the last moment in the session
        # # therefore to limit number of requests when game is not running the script checks for client's process
        # if "iRacingSim64DX11.exe" not in [p.Name for p in wmi.WMI().Win32_Process()]:
        #     scheduler.enter(IDLE_REFRESH_RATE, 1, main_loop, (scheduler,))
        #     print("iRacing is not running.")
        #     return

        # prev_ir not existing means that the script has just been turned on
        # the following code reruns the loop to get new data
        if prev_ir is None:
            scheduler.enter(0, 1, main_loop, (scheduler, ir))
            return
        
        # this checks if previous data snapshot is identical to current one
        # which would mean that the game client is not running
        # and thus data refresh rate can be returned to idle value
        if prev_ir == ir:
            scheduler.enter(IDLE_REFRESH_RATE, 1, main_loop, (scheduler,))
            print("iRacing is not running.")
            return

        scheduler.enter(IN_GAME_REFRESH_RATE, 1, main_loop, (scheduler, ir))
        print("iRacing is running.")

if __name__ == "__main__":
    scheduler = sched.scheduler(time.time, time.sleep)
    scheduler.enter(0, 1, main_loop, (scheduler,))
    scheduler.run()