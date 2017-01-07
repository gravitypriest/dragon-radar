import os
import logging
from utils import (timestamp_to_seconds,
                   to_timestamp,
                   frame_to_seconds)
import constants

APP_NAME = constants.APP_NAME

logger = logging.getLogger(APP_NAME)


def _op_subtitle_delay(episode):
    '''
    OP on the orange bricks are out of sync, retime them here
    to a reference of 00:00:12:512 for the first subtitle
    '''
    if (int(episode.number) in range(1, 6) or
       int(episode.number) in range(11, 21)):
        # 00:00:13:013
        delay = 15
    if (int(episode.number) in [6, 10] or
       int(episode.number) == 35):
        # 00:00:12:345
        delay = -5
    if int(episode.number) == 7:
        # 00:00:13:380
        delay = 26
    if (int(episode.number) == 8 or
       int(episode.number) in range(21, 35) or
       int(episode.number) in range(36, 43)):
        # 00:00:12:846 -OR-
        # 00:00:14:014 & delay on DBox
        delay = 10
    if int(episode.number) == 9:
        # 00:00:12:679
        delay = 5
    if int(episode.number) in range(43, 47):
        # 00:00:14:014
        delay = 45
    if int(episode.number) in range(47, 140):
        # 00:00:13:847
        delay = 40
    if int(episode.number) in range(140, 292):
        # 00:00:12:512
        # 00:00:20:353 (op 2)
        delay = 0

    return frame_to_seconds(delay)


def _adjust_timecode(episode, timestamp):
    '''
    Offset a timecode by the total number of offset frames
    '''
    frame = timestamp_to_seconds(timestamp)
    offsets = episode.offsets
    if episode.is_pioneer:
        offsets = episode.pioneer_offsets
    series = episode.series
    total_offset = 0
    # calculate offset from frame data
    if isinstance(offsets, list):
        # for list-types (movies, not episodes), start with 0 offset
        for o in offsets:
            if frame > frame_to_seconds(o['frame']):
                total_offset += frame_to_seconds(o['offset'])
    else:
        # episodes are map-based, with a key for each chapter
        # orange bricks have a delay on the OP subs
        if (series == 'DBZ' and not episode.is_r1dbox and
           frame < frame_to_seconds(offsets['prologue']["frame"])):
            total_offset += _op_subtitle_delay(episode)
        for key in offsets.keys():
            # also account for ED subs being +0.333 s early
            if frame > frame_to_seconds(offsets[key]["frame"]):
                total_offset += frame_to_seconds(
                    offsets[key]["offset"])
    # apply offset to subtitle timing
    frame -= total_offset

    return to_timestamp(frame)


def retime_vobsub(orig_file, fixed_file, episode):
    '''
    Parse the file and retime the sub
    '''
    try:
        with open(
                orig_file, 'r') as file_in, open(
                fixed_file, 'w') as file_out:
            logger.debug('Opened %s for reading.' % (orig_file))
            logger.debug('Opened %s for writing.' % (fixed_file))
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


def detect_streams(fname):
    streams = []
    vob_id = -1
    filtered_streams = []
    previous_empty = False
    with open(fname, 'r') as subfile:
        for line in subfile:
            if 'id:' in line and 'index' in line:
                # if 'id: --' in line:
                #     continue
                firstline = True
                stream_idx = int(line.split('index:')[1].strip())
                streams.append([])
                streams[stream_idx] = {'vobs': [], 'first': None}
                vob_id = -1
            if 'Vob/Cell ID' in line:
                new_vob_id = int(line.split('Vob/Cell ID: ')[1].split(',')[0])
                if new_vob_id != vob_id:
                    vob_id = new_vob_id
                    streams[stream_idx]['vobs'].append(
                        {'vob_id': vob_id, 'subs': 0})
            if 'timestamp:' in line:
                if firstline:
                    if '00:00:00:000' not in line:
                        # ignore fucky empty streams
                        firstline = False
                        streams[stream_idx]['first'] = line.strip()
                streams[stream_idx]['vobs'][-1]['subs'] += 1
    for s, stream in enumerate(streams):
        filtered_stream = {}
        logger.debug('Subs in stream %d: ', s)
        total = 0
        logger.debug(' - First subtitle: %s', stream['first'])
        for vob in stream['vobs']:
            total += vob['subs']
            logger.debug(' - VOB %d: %d', vob['vob_id'], vob['subs'])
        logger.debug(' - TOTAL: %d', total)
        if total == 1 and not stream['first']:
            # try to detect fucky empty streams
            continue
        filtered_stream['id'] = s

        # mkvmerge ignores empty subtitle tracks and
        #  treats the first non-empty as idx 0, so
        #  remember if the first track is empty to
        #  adjust the next
        if previous_empty:
            filtered_stream['id'] = s - 1
            previous_empty = False
        if total == 0:
            previous_empty = True
            continue
        filtered_stream['total'] = total
        filtered_streams.append(filtered_stream)
    return filtered_streams
