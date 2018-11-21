# The AutoAuto Device Library

## Introduction

This library runs on AutoAuto devices and exposes all the functionality the device has through an easy Python interface.

## Beginner or Advanced?

If you are a beginner programmer ("coder") you will want to follow along through the lessons on [AutoAuto Labs](https://labs.autoauto.ai/). After you've leveled-up through the beginning and intermediate lessons, you can come back here and explore the more advanced usage.

If you are an advanced programmer, you are welcome to dive right into using this library! This library is already installed on your AutoAuto device. You can either SSH into your device to gain command-line access (with `sudo`-powers), or you can access the Jupyter Notebook server (which runs by default in the background on every AutoAuto device), or you can use [AutoAuto Labs](https://labs.autoauto.ai/)'s programming interface (which is simple, yet pleasant to use).

If you choose to SSH, you'll want to SSH into the account named `hacker`. I.e. Use the command: `ssh hacker@<ip_of_your_device>`. You must obtain your device's default password from [AutoAuto Labs](https://labs.autoauto.ai/autopair/) (from the "My Devices" page, you can view your device's "Info for Advanced Users"). Every device has a different default system password. You are encouraged to change your device's system password (using the usual `passwd` command).

If you choose to use Jupyter, connect to the Jupyter server running on your device on port 8888. I.e. You should navigate in your browser to `http://<ip_of_your_device>:8888/`. You must obtain the password for Jupyter from [AutoAuto Labs](https://labs.autoauto.ai/autopair/) (from the "My Devices" page, you can view your device's "Info for Advanced Users"). Every device has a different Jupyter password.

## Library Overview

The library is segmented into three packages:

- `auto`: The "core" package (if you will). Contains critial components for _every_ AutoAuto device, such as the camera interface and ML models.

- `cio`: A package whose only job is to know how to talk to the on-board microcontroller. The communication protocol is agnostic to the details of the microcontroller (such as the instruction set, clock rate, etc). The `cio` package can talk to any microcontroller that speaks the correct protocol. The name `cio` represents "controller input/output".

- `car`: The `car` package contains helper functions that are only useful for AutoAuto _cars_. E.g. `car.forward()`, `car.left()`, `car.right()`, `car.reverse()`. If you look at the implementations of these helper functions, you'll find they use the `auto` and `cio` packages under the hood (pun intended).

## RPC Everywhere

You'll quickly notice that we do a lot of RPCs inside of this library. The nature of the beast is that we have limited, shared resources (there is only one microcontroller, only one camera, only one connection to AutoAuto Labs, only one LCD screen). But, we have many processes that need to access these shared resources (e.g. one process wants to talk to the microcontroller to monitor the battery level continually and another process wants to talk to the microcontroller to drive the device (i.e. run the motors); or maybe two processes both need to read frames from the camera to do unrelated computer vision things, or maybe two processes would like to write information to the LCD screen (to the _console_) and have it be interlaced for the user to see; and the list goes on).

Currently, there are four RPC servers:

- The CIO RPC server: If you want to talk to the microcontroller, go through him. He is the microcontroller broker/gatekeeper.

- The camera RPC server: Same story, if you want frame(s) from the camera, talk to him. (Note: This server will keep the camera "open" for 60 seconds after the last RCP client disconnects, because a common usage-pattern while developing your program is to immediately re-run your code, and having the camera stay open speeds up the second run tremendously).

- The Console UI RPC server: Same story, if you want to display something on the LCD screen, you know who to ask.

- The CDP RPC server: If you want to send data to your AutoAuto Labs account, you go through this guy.

Each of these servers has corresponding RCP clients that make their usages easy and transparent. See:
 - each client linked here

## Examples

### Drive your car!

**Note:**: Only applicable to AutoAuto _cars_, not other devices.

```python
import car

# Each line below defaults to driving for 1 second (results in, 4 seconds total driving).
car.forward()
car.left()
car.right()
car.reverse()

# You can also specify the duration (in seconds), for example:
car.forward(2.5)
```

### Print to the AutoAuto Console

AutoAuto devices are equipped with an LCD screen which displays the "AutoAuto Console". You can print your own text to the console, example below:

```python
from auto import console

console.print("Hi, friend!")
console.print("How are you?")
```

The `car` package also has a print function which prints to `stdout` _and_ to the
AutoAuto console. (For those who use the `car` package, this is convenient.)

```python
import car

car.print("¡Hola, amigo!")
car.print("¿Como estas?")
```

### Use the camera

Capture a single frame:

```python
import car

frame = car.capture()
car.stream(frame)
```

**Note:** The `car.capture()` and `car.stream()` functions are convenience functions. They use the `auto` package internally. E.g. To most efficiently acquire camera frames continuously, use the next snippet (below). This bypasses the camera RPC server, thus it will not work if other processes are currently using the camera (including the camera RPC server itself).

```python
from auto.camera_pi import CameraRGB
from auto import frame_streamer

camera = CameraRGB(width=320, height=240, fps=8)

for frame in camera.stream():
    # <process frame here>
    frame_streamer.stream(frame, to_console=True)
```

You can clear the frame from the AutoAuto Console like this:

```python
import car
car.stream(None)

# --or--

from auto import frame_streamer
frame_streamer.stream(None, to_console=True)
```

### Detect faces

```python
import car

while True:
    frame = car.capture()
    car.detect_faces(frame)
    car.stream(frame)
```

The lower-level class-based interface for the face detector can be found in `auto.models.FaceDetector`. The face detector uses OpenCV under the hood (pun _always_ intended!).

### Detect people

We call this the "pedestrian detector" in the context of an AutoAuto _car_.

```python
import car

while True:
    frame = car.capture()
    car.detect_pedestrians(frame)
    car.stream(frame)
```

The lower-level class-based interface for the people detector can be found in `auto.models.PedestrianDetector`. The people detector uses OpenCV under the hood.

### Detect stop signs

```python
import car

while True:
    frame = car.capture()
    car.detect_stop_signs(frame)
    car.stream(frame)
```

The lower-level class-based interface for the stop sign detector can be found in `auto.models.StopSignDetector`. The stop sign detector uses OpenCV under the hood.

### Helper functions: object location & size

The following works with the returned value from:
 - `car.detect_faces()` (shown in example below)
 - `car.detect_pedestrians()`
 - `car.detect_stop_signs()`

```python
import car

frame = car.capture()
rectangles = car.detect_faces(frame)
car.stream(frame)

location = car.object_location(rectangles, frame.shape)
size = car.object_size(rectangles, frame.shape)

car.print("Object location:", location)
car.print("Object size:", size)
```

### Raw OpenCV

In the example below, we'll use OpenCV to do edge-detection using the Canny edge filter.

```python
import cv2

print(cv2.__version__)

TODO
```

### Classify frame's center color

```python
import car

frame = car.capture()
color = car.classify_color(frame)
car.stream(frame)
car.print("The detected color is", color)
```

The lower-level class-based interface for the color classifier can be found in `auto.models.ColorClassifier`. **We would love someone to make it work better!** We will fix it ourselves someday where there is time, but if someone in the community is interested, have at it.

### Precise steering

**Note:**: Only applicable to AutoAuto _cars_, not other devices.

```python
from car.motors import set_steering
import time

for angle in range(-45, 46):       # goes from -45 to +45
    set_steering(angle)
    time.sleep(0.05)

for angle in range(45, -46, -1):   # goes from +45 to -45
    set_steering(angle)
    time.sleep(0.05)

time.sleep(0.5)
set_steering(0.0)  # STRAIGHT
time.sleep(1.0)
```

**Important Note:** The call to `set_steering()` is asynchronous; that is, the function returns immediately, very likely _before_ the wheels have actually had a change to fully turn to the desired angle! Furthermore, the call only "lasts" for 1 second, then the angle will automatically revert back to "straight". As a result you must call `set_steering()` in a loop to keep it "active". (This is a safety feature, allowing the car to revert to going straight if your program crashes or if the Pi loses communication with the microcontroller.)

### Precise throttle

**Note:**: Only applicable to AutoAuto _cars_, not other devices.

**WARNING:** You can easily injure the car by setting the throttle too high. Use this interface with great caution. These cars are wicked fast.

```python
from car.motors import set_throttle
import time

set_throttle(0.0)     # CAR IN NEUTRAL
time.sleep(1.0)

set_throttle(20.0)   # CAR'S MAX THROTTLE
time.sleep(0.3)

set_throttle(50.0)    # HALF THROTTLE
time.sleep(0.3)

set_throttle(0.0)     # NEUTRAL
time.sleep(1.0)
```

**Important Note:** The call to `set_throttle()` is asynchronous; that is, the function returns immediately, very likely _before_ the car's speed actually changes! Furthermore, the call only "lasts" for 1 second, then the car will revert back to a throttle of zero. As a result you must call `set_throttle()` in a loop to keep it "active". (This is a safety feature, allowing the car to automatically **STOP** if your program crashes or if the Pi loses communication with the microcontroller.)

### Stream frames to AutoAuto Labs

... and we'll detect faces as well to make the demo cooler.

```python
import car

while True:
    frame = car.capture()
    car.detect_faces(frame)
    car.stream(frame, to_labs=True)   # <-- Note the new param `to_labs=True`
```

### Plot frames in Jupyter

(also works to stream a single frame to AutoAuto Labs)
TODO

### Gyroscope

TODO

### Accelerometer

TODO

### Buzzer

TODO

### Photoresistor

TODO

### Push Buttons

TODO

### Batter voltage

TODO

### LEDs

Internal and external.
TODO

### PID loop for steering

TODO

### Calibration

TODO

## Project Ideas

AutoAuto Labs has many projects you can do (all fun!). Here are a few other ideas
which haven't been built into AutoAuto Labs yet (but will be in the future).

- Colision detection


## TODO

- embed demo videos
- link to ReadTheDocs documentation
- add contribution instructions
- document PCB extension pins (e.g. aux PWM and encoders)

Also, the [Issues](https://github.com/AutoAutoAI/libauto/issues), of course.

