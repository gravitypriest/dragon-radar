import os
import logging
from utils import (timestamp_to_seconds,
                   to_timestamp,
                   frame_to_seconds)
from constants import Constants

APP_NAME = Constants.APP_NAME

logger = logging.getLogger(APP_NAME)


def _adjust_timecode(episode, timestamp):
    '''
    Offset a timecode by the total number of offset frames
    '''
    frame = timestamp_to_seconds(timestamp)
    offsets = episode.offsets
    series = episode.series

    # part B on the orange bricks starts after the eyecatch, so
    #  pedal back a few frames just to be safe
    # if series == 'DBZ':
        # offsets['partB']['frame'] = offsets['partB']['frame'] - 100

    # calculate offset from frame data
    if isinstance(offsets, list):
        # for list-types (movies, not episodes), start with 0 offset
        total_offset = 0
        for o in offsets:
            if frame > frame_to_seconds(o['frame']):
                total_offset += frame_to_seconds(o['offset'])
    else:
        # for episodes, start with the OP offset
        total_offset = frame_to_seconds(offsets['op']['offset'])
        # orange bricks have a delay on the OP subs
        if (series == 'DBZ' and
           frame < frame_to_seconds(offsets['prologue']["frame"])):
            # episodes 1-20     +0.5 delay
            # episodes 21-34    +0.333 delay
            # episodes 35-39    -0.167 delay
            # episodes 40-?     +1.5 delay
            if int(episode.number) in range(1, 21):
                total_offset += 0.5
            if int(episode.number) in range(21, 35):
                total_offset += 0.333
            if int(episode.number) in range(35, 39):
                total_offset -= 0.167
        for key in offsets.keys():
            # also account for ED subs being +0.333 s early
            if frame > frame_to_seconds(offsets[key]["frame"]):
                total_offset += frame_to_seconds(
                    offsets[key]["offset"])
    # apply offset to subtitle timing
    frame -= total_offset

    return to_timestamp(frame)


def retime_vobsub(episode, config):
    orig_file = os.path.join(
        config.get(Constants.APP_NAME, 'working_dir'),
        episode.series,
        Constants.FUNI_SUB_DIR,
        episode.number + '.idx')
    logger.info('Opened %s for reading.' % (orig_file))
    fixed_file = os.path.join(
        config.get(Constants.APP_NAME, 'working_dir'),
        episode.series,
        Constants.RETIMED_SUB_DIR,
        episode.number + '.idx')
    logger.info('Opened %s for writing.' % (fixed_file))
    try:
        with open(
                orig_file, 'r') as file_in, open(
                fixed_file, 'w') as file_out:
            for line in file_in:
                if 'timestamp: ' in line:
                    sub_parts = line.split(',')
                    sub_time = sub_parts[0].split('timestamp: ')[1].strip()
                    retimed = _adjust_timecode(episode, sub_time)
                    sub_parts[0] = 'timestamp: ' + retimed
                    file_out.write(','.join(sub_parts))
                else:
                    file_out.write(line)
    except IOError as e:
        logger.error(e)
    logger.info('Subtitle retiming for %s %s is complete.' % (episode.series,
                                                              episode.number))
