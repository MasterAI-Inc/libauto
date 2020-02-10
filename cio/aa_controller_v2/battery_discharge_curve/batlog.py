from auto.capabilities import list_caps, acquire
from itertools import count
import time

b = acquire('BatteryVoltageReader')

start_time = time.time()

with open('batlog.csv', 'wt') as f:
    f.write('index,time,millivolts\n')

    for i in count():
        v = b.millivolts()
        line = '{},{},{}'.format(i, time.time() - start_time, v)
        print(line)
        f.write(line + '\n')
        f.flush()
        wait_time = start_time + i + 1 - time.time()
        time.sleep(wait_time)

