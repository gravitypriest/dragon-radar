import json
import os
import logging
import shutil
from constants import Constants

APP_NAME = Constants.APP_NAME
OFFSETS_JSON = Constants.OFFSETS_JSON
DISC_JSON = Constants.DISC_JSON
DEMUX_JSON = Constants.DEMUX_JSON
VALID_JSON = Constants.VALID_JSON

logger = logging.getLogger(APP_NAME)


def load_json(filename):
    try:
        json_data = json.load(open(filename))
    except OSError as o:
        logger.error(o)
    return json_data


def load_series_frame_data(series):
    '''
    Load the JSON data of frame offsets for one series
    '''
    series_frame_data = load_json(OFFSETS_JSON)[series]
    return series_frame_data


def load_episode_disc_data(series, season, disc):
    '''
    Load the JSON data of episode/disc layout
    '''
    disc_data = load_json(DISC_JSON)[series][season][disc]
    return disc_data


def load_demux_map(series, season):
    '''
    Load the JSON data of demux info
    '''
    demux_map = load_json(DEMUX_JSON)[series][season]
    return demux_map


def load_validate(series):
    '''
    Load the JSON data of demux info
    '''
    validate = load_json(VALID_JSON)[series]
    return validate


def get_op_offset(series, episode, frame_data):
    '''
    Get the initial frame offset of the beginning of the OP
    '''
    if series == "DBZ" or series == 'DBoxZ':
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


def delete_temp(tmp_dir):
    try:
        if os.path.isdir(tmp_dir):
            logger.info('Deleting temporary files...')
            shutil.rmtree(tmp_dir)
    except OSError:
        logger.info('Problem deleting temp directory. '
                    'Please manually delete %s' % tmp_dir)


def rename(fname, new_fname):
    try:
        os.rename(fname, new_fname)
    except OSError as e:
        logger.error('Could not rename %s: %s' (fname, e))


def move_file(fname, new_path):
    try:
        shutil.move(fname, new_path)
    except shutil.Error as e:
        logger.error(e)


def create_dir(newdir):
    try:
        os.makedirs(newdir)
    except OSError:
        if not os.path.isdir(newdir):
            self._delete_temp(tmp_dir)
            logger.debug('There was a problem creating %s' %
                         newdir)
            raise
        logger.debug('%s not created (already exists)' %
                     newdir)
