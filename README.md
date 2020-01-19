# The AutoAuto Device Library

## Introduction

Use Python & A.I. to program a self-driving car. AutoAuto is a fun way to learn bleeding-edge skills, intended for beginner and advanced engineers alike. Drive your wonder with AutoAuto.

This library runs on AutoAuto devices and exposes all the functionality the device has through a layered Python interface.

![AutoAuto Fleet 1 Car](https://static.autoauto.ai/uploads/d452293bcac14e65a3370c54e9027e79.JPG)

## Beginner or Advanced?

If you are a beginner programmer ("coder") you will want to follow along through the lessons on [AutoAuto Labs](https://labs.autoauto.ai/). After you've leveled-up through the beginner and intermediate lessons, you can come back here and explore this library's deeper implementation details.

If you are an advanced programmer, you are welcome to dive right into using this library! This library is already installed on your AutoAuto device. Have a look at the section [Connecting to Your Device](#connecting-to-your-device) and the section [Examples](#examples), then you will be off-to-the-races programming your device using this library.

## Library Overview

The library is segmented into four packages:

- [auto](./auto/): The "core" package. Contains the critical components for _every_ AutoAuto device, such as the camera interface and ML models.

- [cio](./cio/): A package whose only job is to talk to the on-board microcontroller. The name `cio` is short for "controller input/output".

- [cui](./cui/): A package whose only job is to run the AutoAuto console on the LCD screen. The name `cui` is short for "console UI".

- [car](./car/): The `car` package contains helper functions that are only useful for AutoAuto _cars_. E.g. `car.forward()`, `car.left()`, `car.right()`, `car.reverse()`. If you look at the implementations of these helper functions, you'll find they use the `auto` and `cio` packages under the hood (pun intended).

## Connecting to Your Device

Here are the ways you can connect to your device:

- **SSH:** SSH'ing into your device is the quickest way to gain privileged access (i.e. to get `sudo` powers; remember Uncle Ben's words: with great power comes great responsibility). You can log in to the device under the username `hacker` (in this context, "hacker" denotes a skilled computer expert!). You must obtain your device's default password from [AutoAuto Labs](https://labs.autoauto.ai/autopair/) (from the "My Devices" page, you can view your device's "Info for Advanced Users"). Every device has a different default system password. You are encouraged to change your device's system password (using the usual `passwd` command).

- **Jupyter:** Every device runs a Jupyter Notebook server on port 8888. You must obtain the password for Jupyter from [AutoAuto Labs](https://labs.autoauto.ai/autopair/) (from the "My Devices" page, you can view your device's "Info for Advanced Users"). Every device has a different Jupyter password. Note the Jupyter server does not run as a privileged user, although you are welcome to change the device so that it **does** run as a privileged user -- your call.

- **AutoAuto Labs:** AutoAuto Labs offers a simple editor where you can write and run programs. It is pleasant to use, but it is only good for small, basic programs.

## Examples

### Drive your car!

**Note:** Only applicable to AutoAuto _cars_, not other devices.

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

Many AutoAuto devices are equipped with an LCD screen which displays the "AutoAuto Console". You can print your own text to the console, example below:

```python
from auto import console

console.print("Hi, friend!")
console.print("How are you?")
```

The `car` package also has a print function which prints to `stdout` _and_ to the
AutoAuto console. (For those who use the `car` package, this is convenient.)

```python
import car

car.print("Hi, friend!")
car.print("How are you?")
```

### Use the camera

Capture a single frame:

```python
import car

frame = car.capture()
car.stream(frame, to_console=True, to_labs=True)
```

**Note:** The `car.capture()` and `car.stream()` functions are convenience functions. They use the `auto` package internally. E.g. The following code uses the next-layer-down interfaces to capture frames continuously.

```python
from auto.camera import global_camera
from auto.frame_streamer import stream

camera = global_camera()

for frame in camera.stream():
    # <process frame here>
    stream(frame, to_console=True, to_labs=True)
```

You can clear the frame from the AutoAuto Console like this:

```python
import car
car.stream(None, to_console=True, to_labs=True)

# --or--

from auto.frame_streamer import stream
stream(None, to_console=True, to_labs=True)
```

**Advanced Usage:** The most optimized way to access camera frames is to bypass the camera RPC server and get access to the camera directly. You can do this by using the `auto.camera_pi.CameraRGB` class. Two things must happen for this to work: (1) you must be running your process under a privileged account (`root` or `hacker`), and (2) no other process may be using the camera (e.g. you might have to kill the camera RPC server or at least wait for it to time-out and release the camera).

### Detect faces

```python
import car

while True:
    frame = car.capture()
    car.detect_faces(frame)
    car.stream(frame, to_labs=True)
```

The lower-level class-based interface for the face detector can be found in `auto.models.FaceDetector`. The face detector uses OpenCV under the hood.

### Detect people

We call this the "pedestrian detector" in the context of an AutoAuto _car_.

```python
import car

while True:
    frame = car.capture()
    car.detect_pedestrians(frame)
    car.stream(frame, to_labs=True)
```

The lower-level class-based interface for the people detector can be found in `auto.models.PedestrianDetector`. The people detector uses OpenCV under the hood.

### Detect stop signs

```python
import car

while True:
    frame = car.capture()
    car.detect_stop_signs(frame)
    car.stream(frame, to_labs=True)
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
car.stream(frame, to_labs=True)

location = car.object_location(rectangles, frame.shape)
size = car.object_size(rectangles, frame.shape)

car.print("Object location:", location)
car.print("Object size:", size)
```

### Raw OpenCV

In the example below, we'll use OpenCV to do edge-detection using the Canny edge filter.

```python
import cv2
import car

print("OpenCV version:", cv2.__version__)

while True:
    frame = car.capture(verbose=False)
    frame_gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
    frame_edges = cv2.Canny(frame_gray, 100, 200)
    car.stream(frame_edges, to_labs=True, verbose=False)
```

### Classify frame's center color

```python
import car

frame = car.capture()
color = car.classify_color(frame)
car.stream(frame, to_labs=True)
car.print("The detected color is", color)
```

The lower-level class-based interface for the color classifier can be found in `auto.models.ColorClassifier`.

### Precise steering

**Note:** Only applicable to AutoAuto _cars_, not other devices.

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

**Important Note:** The call to `set_steering()` is asynchronous; that is, the function returns immediately, very likely _before_ the wheels have actually had a chance to fully turn to the desired angle! Furthermore, the call only "lasts" for 1 second, then the angle will automatically revert back to _straight_. As a result you must call `set_steering()` in a loop to keep it "active". (This is a safety feature, allowing the car to revert to going straight if your program crashes or if the Pi loses communication with the microcontroller.)

### Precise throttle

**Note:** Only applicable to AutoAuto _cars_, not other devices.

**WARNING:** You can easily injure the car, yourself, or others by setting the throttle too high. Use this interface with extreme caution. These cars are VERY powerful and very fast.

```python
from car.motors import set_throttle
import time

set_throttle(0.0)     # CAR IN NEUTRAL
time.sleep(1.0)

set_throttle(20.0)   # 1/5 THROTTLE  (100 is max, don't try that though)
time.sleep(1.0)

set_throttle(50.0)    # HALF THROTTLE
time.sleep(0.4)

set_throttle(0.0)     # NEUTRAL
time.sleep(1.0)
```

**Important Note:** The call to `set_throttle()` is asynchronous; that is, the function returns immediately, very likely _before_ the car's speed actually changes! Furthermore, the call only "lasts" for 1 second, then the car will revert back to a throttle of zero. As a result you must call `set_throttle()` in a loop to keep it "active". (This is a safety feature, allowing the car to automatically **STOP** if your program crashes or if the Pi loses communication with the microcontroller.)

### Plot frames in Jupyter

The helper function `car.plot()` will both stream a single frame to your AutoAuto Labs account _and_ it returns a `PIL.Image` object, so you can conveniently use it from Jupyter. See the screenshot below:

![](https://static.autoauto.ai/uploads/abecaaf6d4d34146bd802be839f1f993.png)

### List the devices' capabilities

Different AutoAuto devices (and different versions of the same device) may have a different set of hardware capabilities. You can ask your device to list its capabilities like this:

```python
from auto.capabilities import list_caps, acquire, release

my_capabilities = list_caps()

print(my_capabilities)
```

**Note:** In the program above we also imported `acquire` and `release` (although we didn't use them). Those two functions will be used in many of the examples that follow to actually _use_ the capabilites that we listed above.

### Gyroscope

You can get _instantanious_ measurements from the gyroscope like this:

```python
from auto.capabilities import list_caps, acquire, release
import time

gyroscope = acquire('Gyroscope')

for i in range(100):
    x, y, z = gyroscope.read()
    print(' '.join("{:10.3f}".format(v) for v in (x, y, z)))
    time.sleep(0.05)

release(gyroscope)
```

Or you can get _accumulated_ (or _integrated_, if you prefer) measurements like this (which is likely what you actually want):

```python
from auto.capabilities import list_caps, acquire, release
import time

gyroscope = acquire('Gyroscope_accum')

for i in range(100):
    x, y, z = gyroscope.read()
    print(' '.join("{:10.3f}".format(v) for v in (x, y, z)))
    time.sleep(0.05)

release(gyroscope)
```

### Accelerometer

```python
from auto.capabilities import list_caps, acquire, release
import time

accelerometer = acquire('Accelerometer')

for i in range(100):
    x, y, z = accelerometer.read()
    print(' '.join("{:10.3f}".format(v) for v in (x, y, z)))
    time.sleep(0.05)

release(accelerometer)
```

### Buzzer

The `car` package has two helper functions:

```python
import car

car.buzz('!V10 O4 L16 c e g >c8')

car.honk()
```

Or you can use the underlying buzzer interface.

```python
from auto.capabilities import list_caps, acquire, release

buzzer = acquire("Buzzer")

buzzer.play('!V10 O4 L16 c e g >c8')  # <-- asynchronous call

buzzer.wait()   # <-- block the program until the buzzer finishes playing

release(buzzer)
```

See [Buzzer Language](#buzzer-language) to learn how to write notes as a string that the buzzer can interpret and play.

### Photoresistor

You can use the photoresistor as a very simple ambient light detector. Keep in mind that if you have, say, an AutoAuto _car_ with the car body on, the photoresistor will be covered up so its sensitivity will be much decreased. That said, it will still work but you'll have to experiment with it to get the proper threshold values for your application.

```python
from auto.capabilities import list_caps, acquire, release
import time

photoresistor = acquire('Photoresistor')

for i in range(100):
    millivolts, resistance = photoresistor.read()
    print(resistance)
    time.sleep(0.1)

release(photoresistor)
```

The program above prints the resistance of the photoresistor (in Ohms). You can play around with where a good threshold is for your application, and you can quickly see the value change by simply covering the light with your hand or by shining a flashlight at the photoresistor.

### Push Buttons

```python
from auto.capabilities import list_caps, acquire, release

buttons = acquire('PushButtons')

print("Press the buttons, and you'll see the events being printed below:")

while True:
    button, action = buttons.wait_for_action('any')
    print("The {}th button was {}.".format(button, action))
    if button == 2:
        break

release(buttons)
```

### Batter voltage

```python
from auto.capabilities import list_caps, acquire, release

battery = acquire('BatteryVoltageReader')

millivolts = battery.millivolts()
percentage, minutes = battery.estimate_remaining(millivolts)

print('The battery voltage is {} millivolts.'.format(millivolts))
print('It is at ~{}% and will last for ~{} more minutes.'.format(minutes, percentage))

release(battery)
```

**Note:** There's a background task that will monitor the battery voltage for you and will buzz the buzzer when the batter gets to 5% or lower.

### LEDs

The main PCB has three on-board LEDs that you can turn on/off programmatically.

```python
from auto.capabilities import list_caps, acquire, release
import time

buttons = acquire('PushButtons')
leds = acquire('LEDs')

led_ordering = ['red', 'green', 'blue']

print("Press the buttons to turn on/off the on-board LEDs:")

while True:
    button_index, action = buttons.wait_for_action('any')

    # We use the button
    led_identifier = led_ordering[button_index]

    # Turn on the LED when the button is pressed, and off
    # whent he button is released.
    led_value = (action == 'pressed')

    # We set the state of every led below:
    leds.set_led(led_identifier, led_value)

release(buttons)
release(leds)
```

### Calibration

Depending on the device you have, you can run the appropriate calibration script.

...

## Buzzer Language

The Buzzer Language<sup>[1](#buzzer-language-copyright)</sup> works as follows:

The notes are specified by the characters C, D, E, F, G, A, and B, and they are played by default as "quarter notes" with a length of 500 ms. This corresponds to a tempo of 120 beats/min. Other durations can be specified by putting a number immediately after the note. For example, C8 specifies C played as an eighth note, with half the duration of a quarter note. The special note R plays a rest (no sound). The sequence parser is case-insensitive and ignores spaces, which may be used to format your music nicely.

Various control characters alter the sound:

| Control character(s)        | Effect |
| --------------------------- | ------ |
| **A**–**G**                 | Specifies a note that will be played. |
| **R**                       | Specifies a rest (no sound for the duration of the note). |
| **+** or **#** after a note | Raises the preceding note one half-step. |
| **-** after a note          | Lowers the preceding note one half-step. |
| **1**–**2000** after a note | Determines the duration of the preceding note. For example, C16 specifies C played as a sixteenth note (1/16th the length of a whole note). |
| **.** after a note          | "Dots" the preceding note, increasing the length by 50%. Each additional dot adds half as much as the previous dot, so that "A.." is 1.75 times the length of "A". |
| **>** before a note         | Plays the following note one octave higher. |
| **<** before a note         | Plays the following note one octave lower. |
| **O** followed by a number  | Sets the octave. (default: O4) |
| **T** followed by a number  | Sets the tempo in beats per minute (BPM). (default: T120) |
| **L** followed by a number  | Sets the default note duration to the type specified by the number: 4 for quarter notes, 8 for eighth notes, 16 for sixteenth notes, etc. (default: L4) |
| **V** followed by a number  | Sets the music volume (0–15). (default: V15) |
| **MS**                      | Sets all subsequent notes to play play staccato – each note is played for 1/2 of its allotted time, followed by an equal period of silence. |
| **ML**                      | Sets all subsequent notes to play legato – each note is played for full length. This is the default setting. |
| **!**                       | Resets the octave, tempo, duration, volume, and staccato setting to their default values. These settings persist from one play() to the next, which allows you to more conveniently break up your music into reusable sections. |

Examples:
 - The C-major scale up and back down: "!L16 cdefgab&gt;cbagfedc"
 - The first few measures of Bach's fugue in D-minor: "!T240 L8 agafaea dac+adaea fa&lt;aa&lt;bac#a dac#adaea f4"

<a name="buzzer-language-copyright">1</a>: Pololu Corporation developed and holds the copyright for the Buzzer Language and its documentation. Further information about the Buzzer Language's license and copyright can be found in the [LICENSE](./LICENSE) file.

## Project Ideas

AutoAuto Labs has many projects you can do (all fun!). Here are a few other ideas
which haven't been built into AutoAuto Labs yet (but will be in the future).

- Collision detection
- Collaborative cars
- Light avoider

## TODO

- embed demo videos
- link to ReadTheDocs documentation
- add contribution instructions
- document PCB extension pins (e.g. aux PWM and encoders)

Also, the [Issues](https://github.com/AutoAutoAI/libauto/issues), of course.

