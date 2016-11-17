import json
import os
import sys
import time
import logging
import shutil
import constants

APP_NAME = constants.APP_NAME
OFFSETS_JSON = constants.OFFSETS_JSON
DISC_JSON = constants.DISC_JSON
DEMUX_JSON = constants.DEMUX_JSON
VALID_JSON = constants.VALID_JSON
TITLE_TIMES_JSON = constants.TITLE_TIMES_JSON
TITLES_JSON = constants.TITLES_JSON
FRAME_RATE = constants.FRAME_RATE

logger = logging.getLogger(APP_NAME)


def load_json(filename):
    try:
        json_data = json.load(open(filename))
    except OSError as o:
        logger.error(o)
    return json_data


def load_frame_data(series, episode):
    '''
    Load the JSON data of frame offsets for one series
    '''
    series_frame_data = load_json(OFFSETS_JSON)[series]
    try:
        op_offset = get_op_offset(series, int(episode), series_frame_data)
    except ValueError:
        # string index (for the specials)
        op_offset = None
    return series_frame_data[episode], op_offset


def load_episode_disc_data(series, season, disc):
    '''
    Load the JSON data of episode/disc layout
    '''
    disc_data = load_json(DISC_JSON)[series][season][disc]
    return disc_data


def load_demux_map(series, episode):
    '''
    Load the JSON data of demux info
    '''
    demux_map = load_json(DEMUX_JSON)[series][episode]
    return demux_map


def load_validate(series):
    '''
    Load the JSON data of demux info
    '''
    validate = load_json(VALID_JSON)[series]
    return validate

def load_title_time(series, episode):
    '''
    Load the timestamps file for episode titles
    '''
    title_time = load_json(TITLE_TIMES_JSON)[series][episode]
    return title_time

def load_title(series, episode):
    '''
    Load the episode title
    '''
    title = load_json(TITLES_JSON)[series][episode]
    return title

def get_op_offset(series, episode, frame_data):
    '''
    Get the initial frame offset of the beginning of the OP
    '''
    if series == 'DBZ' or series == 'DBoxZ':
        if episode == 25:
            op = 'OP25'
        elif episode > 36 and episode < 43:
            op = 'OP37TO42'
        elif episode > 177 and episode < 184:
            op = 'OP178TO183'
        elif episode > 199:
            op = 'OP2'
            if episode > 219:
                op = 'OP220UP'
        else:
            op = 'OP1'
    elif series == 'DBGT':
        if episode > 34:
            op = 'op2'
        else:
            op = 'op'
    else:
        op = 'op'
    if series != 'MOVIES':
        op_offset = frame_data[op]['offset']
    else:
        op_offset = None

    return op_offset


def timestamp_to_seconds(timestamp):
    '''
    Represent timestamp in total seconds
    '''
    # separate vobsub timestamp
    time_parts = timestamp.split(':')
    h = int(time_parts[0])
    m = int(time_parts[1])
    s = int(time_parts[2])
    ms = int(time_parts[3])

    # convert timestamp to seconds
    frame = (3600 * h) + (60 * m) + s + float(ms) / 1000

    return frame


def _split_seconds(seconds):
    rounded_time = '%.3f' % round(seconds, 3)
    time_parts = rounded_time.split('.')
    s = time_parts[0]
    ms = time_parts[1]
    return s, ms


def to_timestamp(frame, ntsc_frame=None):
    '''
    Convert seconds to timestamp format
    '''
    delimiter = ':'
    if ntsc_frame is not None:
        frame = float(ntsc_frame) / FRAME_RATE
        delimiter = '.'
    seconds, ms = _split_seconds(frame)
    hms = time.strftime('%H:%M:%S',
                        time.gmtime(int(seconds)))
    return delimiter.join([hms, ms])


def frame_to_seconds(frame):
    '''
    Convert NTSC frame number to seconds
    '''
    return frame / FRAME_RATE


def pad_zeroes(series):
    '''
    Add leading zeroes for dictionary keys
    '''
    leading = 2
    if series == 'DB' or series == 'DBZ':
        leading = 3
    return leading


def delete_temp(tmp_dir):
    try:
        if os.path.isdir(tmp_dir):
            logger.debug('Deleting temp directory %s', tmp_dir)
            shutil.rmtree(tmp_dir)
    except OSError:
        logger.info('Problem deleting temp directory. '
                    'Please manually delete %s', tmp_dir)


def rename(fname, new_fname):
    try:
        os.rename(fname, new_fname)
    except (OSError, FileNotFoundError) as e:
        logger.error('Could not rename %s: %s', fname, e)


def move_file(fname, new_path):
    logger.debug('Moving %s to %s', fname, new_path)
    try:
        shutil.move(fname, new_path)
    except (shutil.Error, FileNotFoundError) as e:
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


def series_to_movie(series, movie):
    '''
    Translate a series & movie to an 'episode' in the MOVIES series
    e.g. series:DBZ movie:1 -> series:MOVIES episode:1
    '''
    if series == 'DB':
        if movie == 4:
            number = 14
        else:
            number = movie + 14
    if series == 'DBZ':
        number = movie
    if series == 'DBGT':
        logger.error('No DBGT movies!')
        sys.exit(1)
    return number


def check_abort(returncode, name):
    if returncode != 0:
        logger.error('%s had non-zero exit code (%s). Aborting.', name, returncode)
        sys.exit(1)
