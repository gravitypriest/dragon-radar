import os
import shutil
import logging
import tempfile
import atexit
import subprocess
import re
import constants
from utils import delete_temp, create_dir, move_file, check_abort, rename

APP_NAME = constants.APP_NAME
FRAME_RATE = constants.FRAME_RATE
AC3_DIR = constants.AC3_DIR

logger = logging.getLogger(APP_NAME)

def some_maths(frame):
    return round(1000 * float(frame) / FRAME_RATE, 0)

def frame_to_ms(frame, offset):
    if frame == 0:
        prev_chapter_end = 0
    else:
        prev_chapter_end = frame - 1
    if int(offset) < 0:
        chapter_begin = frame - offset
        delay = 0
    else:
        chapter_begin = frame
        delay = offset
    return (some_maths(prev_chapter_end),
           some_maths(chapter_begin),
           some_maths(delay))


def fix_audio(delaycut, file_in):
    '''
    Attempt to fix broken AC3 files
    '''
    logger.info('Fixing %s', file_in)
    file_out = os.path.join(os.path.dirname(file_in),
                            os.path.basename(file_in).replace(
                            '.ac3', '.fixed.ac3'))
    file_in_old = os.path.join(os.path.dirname(file_in),
                               os.path.basename(file_in).replace(
                              '.ac3', '.old.ac3'))
    _run_delaycut([delaycut,
                   '-i', file_in,
                   '-o', file_out,
                   '-fixcrc', 'silence'])
    rename(file_in, file_in_old)
    rename(file_out, file_in)
    logger.info('Fix complete.')


def combine_files(file_list, final_file):
    '''
    Merge multiple audio files into one
    '''
    with open(final_file, 'wb') as output:
        for fname in file_list:
            with open(fname, 'rb') as f:
                shutil.copyfileobj(f, output)
    for f in file_list:
        os.remove(f)


def _run_delaycut(args):
    '''
    Run delaycut here.  Hide all output because it has a LOT of it.  Check
    return codes instead.
    '''
    logger.debug('Delaycut args:')
    logger.debug(args)
    with open(os.devnull, 'w') as devnull:
        dcut = subprocess.call(args, stdout=devnull,
                               stderr=subprocess.STDOUT)
    check_abort(dcut, 'Delaycut')


def correct_ac3_delay(delaycut, file_in, file_out, delay, bitrate):
    '''
    Just correct a single delay
    '''
    file_out_1 = file_in + '.part1'
    file_out_2 = file_in + '.part2'

    do_ = ['-startcut', str(-delay)]
    args = [delaycut, '-i', file_in]
    args.extend(do_)
    args.extend(['-o', file_out_1])
    _run_delaycut(args)

    rename(file_out_1,  file_out)


def delaycut_chain(delaycut, file_in, prev_ch_end, ch_begin, delay, bitrate):
    '''
    3-stage audio correction
    '''

    file_out_1 = file_in + '.part1'
    file_out_2 = file_in + '.part2'
    file_out_3 = file_in + '.part3'

    if prev_ch_end != 0:
        # episode up until chapter point
        logger.debug('Cutting first part...')
        _run_delaycut([delaycut, '-i', file_in,
                       '-endcut', str(prev_ch_end), '-startcut', '0',
                       '-o', file_out_1])

    if delay > 0:
        # need to add blank space between cuts
        logger.debug('Cutting blank delay...')
        logger.debug('Using %s kbps blank ac3.', bitrate)
        blank_file = os.path.join(AC3_DIR, 'blank_' + bitrate + '.ac3')
        _run_delaycut([delaycut, '-i', blank_file,
                       '-endcut', str(delay), '-startcut', '0',
                       '-o', file_out_2])

    # episode from chapter until end with offset applied
    logger.debug('Cutting second part...')
    _run_delaycut([delaycut, '-i', file_in,
                   '-endcut', '0', '-startcut', str(ch_begin),
                   '-o', file_out_3])

    file_combine = []
    if os.path.isfile(file_out_1):
        file_combine.append(file_out_1)
    if os.path.isfile(file_out_2):
        file_combine.append(file_out_2)
    if os.path.isfile(file_out_3):
        file_combine.append(file_out_3)

    if len(file_combine) > 1:
        logger.debug('Writing combined audio...')

        # delete file before re-creating it
        os.remove(file_in)
        combine_files(file_combine, file_in)
    else:
        os.remove(file_in)
        os.rename(file_out_3, file_in)


def get_bitrate(config, src_file):
    # run ffprobe to determine bitrate
    ff = subprocess.run([config.get(APP_NAME, 'ffprobe'), src_file], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    check_abort(ff.returncode, 'ffprobe')
    m = re.search(r'bitrate: (\d+).*Hz, ([^,(]+)(?:\(.*\))?,', str(ff.stderr))
    bitrate = m.group(1)
    channel = m.group(2)

    if channel == '5.1':
        return '51_' + bitrate
    elif channel == 'stereo':
        return '20_' + bitrate
    else:
        logger.error('Unknown channel/bitrate combination: %s/%s', channel, bitrate)

def retime_ac3(config, offsets, src_file, dst_file, frame_basis_source=True):
    '''
    Retime an AC3 file based on offsets

    Offsets should be a list of objects, formatted as such:
    [{
        "frame": 0
        "offset": 124
    },{
        "frame": 47282
        "offset": -6
    }]
    '''
    if not os.path.isfile(src_file):
        logger.error('ERROR: %s not found. Skipping.', src_file)
        return

    bitrate = get_bitrate(config, src_file)

    logger.debug('Detected bitrate : %s', bitrate)

    tmp_dir = tempfile.mkdtemp()
    # in the case of unexpected exit, we don't want to
    # keep temp files around
    atexit.register(delete_temp, tmp_dir)
    logger.debug('Audio temp folder: %s', tmp_dir)

    logger.debug('Retiming %s', src_file)
    try:
        # copy source to tempfile for surgery
        shutil.copy(src_file, tmp_dir)
        working_file = os.path.join(tmp_dir, os.path.basename(src_file))
    except IOError as e:
        logger.error("Unable to copy file. %s", e)
        return 
    totalOffset = 0
    for o in offsets:
        if o['offset'] == 0:
            continue
        # "frame" is based on the source video, so maintain
        # total offset to match the same frame in destination video
        chapter = o['frame'] + totalOffset
        offset = o['offset']

        if frame_basis_source:
            # if frame_basis_source is False, we are basing our "cuts"
            # on predetermined chapter points from the destination video,
            # so don't maintain shifts aggregately
            totalOffset += offset
        if 'soften' in o:
            # "soften" is an optional offset that shifts the
            # frame in case the audio transitions slightly
            # differently than the video, in order to avoid jarring cuts
            chapter = chapter + o['soften']

        prev_chapter_end, chapter_begin, delay = frame_to_ms(chapter,
                                                             offset)
        delaycut_chain(config.get(APP_NAME, 'delaycut'), working_file, prev_chapter_end,
                       chapter_begin, delay, bitrate)
    move_file(working_file, dst_file)
    delete_temp(tmp_dir)

if __name__ == '__main__':
    config = {
        'delaycut': 'F:/Pogroms/delaycut1.4.3.7/delaycut.exe',
        'ffprobe': 'F:/Pogroms/ffmpeg-20161208-3ab1311-win32-static/bin/ffprobe.exe'
    }
    offsets = [{
            "frame": 0,
            "offset": 20
        }, {
            "frame": 26097,
            "offset": 2
        }]
    src_file = 'E:/output/MOVIES/01/R1/AudioFile_80.ac3'
    dst_file = 'E:/output/MOVIES/01/R1/AudioFile_80.retimed.ac3'
    retime_ac3(config, offsets, src_file, dst_file)