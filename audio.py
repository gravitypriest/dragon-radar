import os
import shutil
import logging
import tempfile
import atexit
from constants import Constants
from utils import delete_temp, create_dir, move_file

APP_NAME = Constants.APP_NAME
R1_DEMUX_DIR = Constants.R1_DEMUX_DIR
RETIMED_AUDIO_DIR = Constants.RETIMED_AUDIO_DIR
FRAME_RATE = Constants.FRAME_RATE
DELAYCUT_CMD = '{delaycut} -i {i} -endcut {end} -startcut {begin} -o {o}'

logger = logging.getLogger(APP_NAME)


def frame_to_ms(frame, offset):
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


def run_delaycut(delaycut, file_in, prev_ch_end, ch_begin, delay, series):
    file_out_1 = file_in + '.part1'
    file_out_2 = file_in + '.part2'
    file_out_3 = file_in + '.part3'
    if prev_ch_end == 0:
        # initial offset
        logger.debug('Cutting initial part...')
        os.system(DELAYCUT_CMD.format(
                  delaycut=delaycut,
                  i=file_in,
                  end=prev_ch_end,
                  begin=ch_begin,
                  o=file_out_1))
        # remove the initial file and begin again
        os.remove(file_in)
        shutil.rename(file_out_1, file_in)

    else:
        # episode up until chapter point
        logger.debug('Cutting first part...')
        os.system(DELAYCUT_CMD.format(
            delaycut=delaycut,
            i=file_in,
            end=prev_ch_end,
            begin=0,
            o=file_out_1))
        # episode from chapter until end with offset applied
        logger.debug('Cutting second part...')
        os.system(DELAYCUT_CMD.format(
            delaycut=delaycut,
            i=file_in,
            end=0,
            begin=ch_begin,
            o=file_out_3))
        if delay > 0:
            # need to add blank space between cuts
            logger.debug('Cutting blank delay...')
            if series in ['DBZ', 'DBGT']:
                if file_in.endswith('_us.ac3'):
                    bitrate = '20_192'
            elif series is 'DBoxZ':
                    bitrate = '51_384'
            else:
                bitrate = '51_448'
            logger.debug('Using %s kbps blank ac3.' % bitrate)
            blank_file = os.path.join(PACKAGE_DIR, 'blank_' + bitrate + '.ac3')
            os.system(DELAYCUT_CMD.format(
                delaycut=delaycut,
                i=blank_file,
                end=delay,
                begin=0,
                o=file_out_2))

        file_combine = []
        file_combine.append(file_out_1)
        if os.path.isfile(file_out_2):
            file_combine.append(file_out_2)
        file_combine.append(file_out_3)

        logger.debug('Writing combined audio...')

        # delete file before re-creating it
        os.remove(file_in)
        with open(file_in, 'wb') as final_file:
            for fname in file_combine:
                with open(fname, 'rb') as f:
                    shutil.copyfileobj(f, final_file)
        for f in file_combine:
            os.remove(f)


def retime_audio(episode, config):
    logger.info('Retiming audio for episode %s...' % episode.number)
    working_dir = config.get(APP_NAME, 'working_dir')
    delaycut = config.get(APP_NAME, 'delaycut')
    tmp_dir = tempfile.mkdtemp()
    # in the case of unexpected exit, we don't want to
    # keep temp files around
    atexit.register(delete_temp, tmp_dir)
    logging.debug('Temp folder: %s' % tmp_dir)

    for suffix in ['en', 'us']:
        fname = episode.number + '_' + suffix + '.ac3'
        src_file = os.path.join(working_dir,
                                episode.series,
                                R1_DEMUX_DIR,
                                fname)
        dst_path = os.path.join(working_dir,
                                episode.series,
                                RETIMED_AUDIO_DIR.format(suffix.upper()))
        if os.path.isfile(src_file):
            logger.debug('%s found! Proceeding with retiming...' % src_file)
        else:
            logger.error('%s not found. Skipping...' % src_file)
            continue

        try:
            # copy source to tempfile for surgery
            shutil.copy(src_file, tmp_dir)
            working_file = os.path.join(tmp_dir, fname)
        except IOError as e:
            logger.error("Unable to copy file. %s" % e)
            continue

        r2_chaps = episode.r2_chapters
        offsets = episode.offsets

        for key in ['op', 'prologue', 'partB', 'ED', 'NEP']:
            if key in offsets.keys():
                # skip scenes with offset of 0
                if offsets[key]['offset'] == 0:
                    continue
                chapter = r2_chaps[key]
                offset = offsets[key]['offset']
                prev_chapter_end, chapter_begin, delay = frame_to_ms(chapter,
                                                                     offset)

                run_delaycut(delaycut, working_file, prev_chapter_end,
                             chapter_begin, delay, episode.series)

        create_dir(dst_path)
        move_file(working_file, dst_path)
    delete_temp(tmp_dir)
