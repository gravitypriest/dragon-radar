import os
import shutil
import logging
import tempfile
import atexit
import subprocess
from constants import Constants
from utils import delete_temp, create_dir, move_file

APP_NAME = Constants.APP_NAME
FRAME_RATE = Constants.FRAME_RATE
DELAYCUT_CMD = '{delaycut} -i {i} -endcut {end} -startcut {begin} -o {o}'
AC3_DIR = Constants.AC3_DIR

logger = logging.getLogger(APP_NAME)


def frame_to_ms(frame, offset):
    if frame == 0:
        prev_chapter_end = 0
    else:
        prev_chapter_end = int(
            round(1000 * float(frame - 1) / FRAME_RATE, 0))
    if int(offset) > -1:
        chapter_begin = int(
            round(1000 * float(frame + offset) / FRAME_RATE, 0))
        delay = 0
    else:
        chapter_begin = int(round(1000 * float(frame) / FRAME_RATE, 0))
        delay = int(round(-1000 * float(offset) / FRAME_RATE, 0))
    return prev_chapter_end, chapter_begin, delay


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

def run_delaycut(delaycut, file_in, prev_ch_end, ch_begin, delay, bitrate):
    '''
    Run delaycut here.  Hide all output because it has a LOT of it.  Check
    return codes instead.
    '''
    file_out_1 = file_in + '.part1'
    file_out_2 = file_in + '.part2'
    file_out_3 = file_in + '.part3'
    try:
        if prev_ch_end == 0:
            # initial offset
            logger.debug('Cutting initial part...')
            proc = subprocess.run([delaycut, '-i', file_in, '-endcut',
                            str(prev_ch_end), '-startcut', str(ch_begin), '-o',
                            file_out_1], stdout=subprocess.DEVNULL,
                            stderr=subprocess.STDOUT)
            proc.check_returncode()
            # remove the initial file and begin again
            os.remove(file_in)
            os.rename(file_out_1, file_in)
        else:
            # episode up until chapter point
            logger.debug('Cutting first part...')
            proc = subprocess.run([delaycut, '-i', file_in, '-endcut',
                            str(prev_ch_end), '-startcut', '0', '-o',
                            file_out_1], stdout=subprocess.DEVNULL,
                            stderr=subprocess.STDOUT)
            proc.check_returncode()
            # episode from chapter until end with offset applied
            logger.debug('Cutting second part...')
            proc = subprocess.run([delaycut, '-i', file_in, '-endcut', '0',
                            '-startcut', str(ch_begin), '-o', file_out_3],
                            stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
            proc.check_returncode()
            if delay > 0:
                # bitrate = '51_448'
                # need to add blank space between cuts
                logger.debug('Cutting blank delay...')
                logger.debug('Using %s kbps blank ac3.', bitrate)
                blank_file = os.path.join(AC3_DIR, 'blank_' + bitrate + '.ac3')
                proc = subprocess.run([delaycut, '-i', blank_file, '-endcut',
                                str(delay), '-startcut', '0', '-o', file_out_2],
                                stdout=subprocess.DEVNULL,
                                stderr=subprocess.STDOUT)
                proc.check_returncode()
            file_combine = []
            file_combine.append(file_out_1)
            if os.path.isfile(file_out_2):
                file_combine.append(file_out_2)
            file_combine.append(file_out_3)

            logger.debug('Writing combined audio...')

            # delete file before re-creating it
            os.remove(file_in)
            combine_files(file_combine, file_in)

    except subprocess.SubprocessError:
        logger.error('Delaycut had non-zero exit code. Aborting.')
        sys.exit(1)


def retime_ac3(episode, src_file, dst_file, bitrate, offset_override=None):
    '''
    Retime an AC3 file based on offsets
    '''
    tmp_dir = tempfile.mkdtemp()
    # in the case of unexpected exit, we don't want to
    # keep temp files around
    atexit.register(delete_temp, tmp_dir)
    logging.debug('Audio temp folder: %s', tmp_dir)

    if os.path.isfile(src_file):
        logger.debug('%s found! Proceeding with retiming...', src_file)
    else:
        logger.error('%s not found. Skipping...', src_file)
        return

    try:
        # copy source to tempfile for surgery
        shutil.copy(src_file, tmp_dir)
        working_file = os.path.join(tmp_dir, os.path.basename(src_file))
    except IOError as e:
        logger.error("Unable to copy file. %s", e)
        return

    r2_chaps = episode.r2_chapters
    offsets = episode.offsets if not offset_override else offset_override

    if isinstance(offsets, list):
        # movies
        totalOffset = 0
        for o in offsets:
            if o['offset'] == 0:
                continue
            chapter = o['frame'] - totalOffset
            offset = o['offset']
            prev_chapter_end, chapter_begin, delay = frame_to_ms(chapter,
                                                                 offset)
            run_delaycut(episode.delaycut, working_file, prev_chapter_end,
                         chapter_begin, delay, bitrate)
            totalOffset += offset
    else:
        # TV
        for key in ['op', 'prologue', 'partB', 'ED', 'NEP']:
            if key in offsets.keys():
                # skip scenes with offset of 0
                if offsets[key]['offset'] == 0:
                    continue
                chapter = r2_chaps[key]
                offset = offsets[key]['offset']
                prev_chapter_end, chapter_begin, delay = frame_to_ms(chapter,
                                                                     offset)

                run_delaycut(episode.delaycut, working_file, prev_chapter_end,
                             chapter_begin, delay, bitrate)

    move_file(working_file, dst_file)
    delete_temp(tmp_dir)
