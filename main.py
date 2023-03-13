import irsdk
import sched
import time

# scheduler set to check for a runnig ir instance every 10 seconds
# when instance is detected this changes to 30 times a second
IDLE_REFRESH_RATE = 10
IN_GAME_REFRESH_RATE = 1/300


def main_loop(scheduler):
    try:
        ir = irsdk.IRSDK()
        ir.startup()

        print(ir['Speed'])
    except AttributeError:
        scheduler.enter(IDLE_REFRESH_RATE, 1, main_loop, (scheduler,))
        print("iRacing is not running.")
    else:
        scheduler.enter(IN_GAME_REFRESH_RATE, 1, main_loop, (scheduler,))
        print("iRacing is running.")

if __name__ == "__main__":
    scheduler = sched.scheduler(time.time, time.sleep)
    scheduler.enter(0, 1, main_loop, (scheduler,))
    scheduler.run()