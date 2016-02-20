import json
import os
from constants import DragonConstants


def load_series_frame_data(series):
    '''
    Load the JSON data of frame offsets for one series
    '''
    try:
        series_frame_data = json.load(
            open(DragonConstants.JSON_FILE))[series]
    except OSError as o:
        print k
    except KeyError as k:
        print k

    return series_frame_data


def get_op_offset(series, episode, frame_data):
    '''
    Get the initial frame offset of the beginning of the OP
    '''
    if series == "DBZ" or series == 'DBZOB':
        if episode == 25:
            op = "OP25"
        elif episode > 36 and episode < 43:
            op = "OP37TO42"
        elif episode > 177 and episode < 184:
            op = "OP178TO183"
        elif episode > 199:
            op = "OP2"
        else:
            op = "OP1"
    elif series == "DBGT":
        if episode > 34:
            op = 'op2'
        else:
            op = 'op'
    else:
        op = "op"
    if series != "DBM":
        op_offset = frame_data[op]["offset"]
    else:
        op_offset = None

    return op_offset


def timestamp_to_seconds(timestamp):
    '''
    Represent timestamp in total seconds
    '''
    # separate vobsub timestamp
    time_parts = timestamp.split(":")
    h = int(time_parts[0])
    m = int(time_parts[1])
    s = int(time_parts[2])
    ms = int(time_parts[3])

    # convert timestamp to seconds
    frame = (3600 * h) + (60 * m) + s + float(ms) / 1000

    return frame


def seconds_to_timestamp(frame):
    '''
    Convert seconds to timestamp format
    '''
    rounded_time = '%.3f' % round(frame, 3)
    total_seconds = int(float(rounded_time))
    frames = rounded_time.split(".")[1]
    seconds = total_seconds % 60
    minutes = (total_seconds / 60) % 60
    hours = (total_seconds / 60) / 60
    time_code =\
        str(hours).zfill(2) + ":" +\
        str(minutes).zfill(2) + ":" +\
        str(seconds).zfill(2) + ":" +\
        str(frames).zfill(3)
    return time_code


def frame_to_seconds(frame):
    '''
    Convert NTSC frame number to seconds
    '''
    return float(frame * 1001) / 30000


def pad_zeroes(series):
    '''
    Add leading zeroes for dictionary keys
    '''
    leading = 3
    if series == 'DBM' or series == 'DBGT':
        leading = 2
    return leading
