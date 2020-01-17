import os
import numpy as np


CURR_DIR = os.path.dirname(os.path.realpath(__file__))
DATA_FILE_PATH = os.path.join(CURR_DIR, "battery_percentage_map.npz")


def battery_map_millivolts_to_percentage(millivolts_single_point):
    global millivolts_data, percentages_data

    try:
        millivolts_data
    except NameError:
        f = np.load(DATA_FILE_PATH)
        millivolts_data, percentages_data = f['millivolts'], f['percentages']
        f.close()

    return float(np.interp(millivolts_single_point, millivolts_data, percentages_data))

