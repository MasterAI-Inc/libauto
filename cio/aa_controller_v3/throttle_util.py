import time
import math
import asyncio
import numpy as np


"""
The throttle function is an exponential decay designed to (roughly) reach
its target value over the span of 1 second. See the code below for a demo:

    import matplotlib.pyplot as plt
    import numpy as np

    t = np.linspace(start=0, stop=3, num=1000)
    t_zero = 0.0

    start_val = 30
    end_val = 15

    k = 5  # <-- tuned so that we roughly reach the target at t=(t_zero + 1.0)

    vals = end_val + (start_val - end_val) * np.exp(-k*(t - t_zero))

    plt.plot(t, vals)

    plt.ylim(0, 40)

    plt.hlines(15, 0, 3, color='red', linestyles='--')

    plt.vlines([0, 1.0], 0, 40, color='red', linestyles='--')
"""


def make_throttle_func(set_throttle, start_val, end_val, t_zero):
    def calc_throttle(t):
        k = 10
        val = end_val + (start_val - end_val) * np.exp(-k*(t - t_zero))
        return int(math.trunc(val))

    async def timed_throttle_vals():
        start_time = time.time()
        while time.time() - start_time < 1.0:
            val = calc_throttle(time.time())
            await set_throttle(val)
            await asyncio.sleep(0.05)

    return timed_throttle_vals()
