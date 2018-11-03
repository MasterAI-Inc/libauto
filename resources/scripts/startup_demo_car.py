from car.motors import set_steering
import time

time.sleep(3.5)

set_steering(-45.0)
time.sleep(1.0)

set_steering(45.0)
time.sleep(1.0)

set_steering(0.0)
time.sleep(2.0)

