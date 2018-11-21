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

Each of these servers has corresponding RCP clients that make their usages easy and transparent.

## Examples

TODO

## TODO

- embed demo videos
- link to ReadTheDocs documentation
- add contribution instructions

Also, the [Issues](https://github.com/AutoAutoAI/libauto/issues), of course.

