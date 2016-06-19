'''
Object for an episode, call all functionality by episode
'''
import os
import sys
import logging
from utils import pad_zeroes, get_op_offset, load_frame_data, load_demux_map, create_dir
from constants import Constants
from demux_2 import demux
from subtitle import retime_vobsub
from audio import retime_ac3

APP_NAME = Constants.APP_NAME
R1_DISC_DIR = Constants.R1_DISC_DIR
R2_DISC_DIR = Constants.R2_DISC_DIR

logger = logging.getLogger(APP_NAME)


def _combine_framedata(offsets, op_offset):
    if op_offset or op_offset == 0:
        offsets['op'] = {'frame': 0, 'offset': op_offset}
    return offsets


def _load_r2_chapters(r2_chap_file):
    logger.debug('Loading R2 chapter file...')
    with open(r2_chap_file) as r2_chaps:
        chap_list = r2_chaps.readlines()
    chapters = {
        'op': 0,
        'prologue': int(chap_list[0]),
        'partB': int(chap_list[1]),
        'ED': int(chap_list[2]),
        'NEP': int(chap_list[3])
    }
    return chapters


class Episode(object):

    def __init__(self, config, args, tmp_dir):
        ep_str = str(args.episode).zfill(pad_zeroes(args.series))
        frame_data, op_offset = load_frame_data(args.series, ep_str)
        self.dest_dir = os.path.join(tmp_dir, ep_str)
        self.number = ep_str
        self.series = args.series
        self.offsets = _combine_framedata(frame_data, op_offset)
        self.r2_chapters = {}
        self.demux_map = load_demux_map(args.series, ep_str)
        self.files = {}
        # special flags
        self.is_r1dbox = False
        self.is_pioneer = False
        self.is_movie = False

    def demux(self, config):
        '''
        Demux video, audio, subs
        Return an object with the filenames
        '''
        pgcdemux = config.get(APP_NAME, 'pgcdemux')
        vsrip = config.get(APP_NAME, 'vsrip')
        src_dir_top = config.get(APP_NAME, 'source_dir')
        src_dir_series = os.path.join(src_dir_top, self.series)
        for r in ['R1', 'R2']:
            if r == 'R1':
                src_dir = os.path.join(src_dir_series, R1_DISC_DIR)
            elif r == 'R2':
                src_dir = os.path.join(src_dir_series, R2_DISC_DIR)
            dest_dir = os.path.join(self.dest_dir, r)
            create_dir(dest_dir)
            logger.info('Demuxing %s %s %s...', self.series, self.number, r)
            self.files[r] = demux(pgcdemux, vsrip, src_dir, dest_dir,
                                  self.demux_map[r], nosub=(r == 'R2'))
        print(self.files)
        self.r2_chapters = _load_r2_chapters(self.files['R2']['chapters'])
        return self.files

    def retime_subs(self):
        '''
        Retime .idx file, rename .sub file to match
        new .idx filename, then save to episode.files
        '''
        logger.info('Retiming subtitles...')
        sub_idx = self.files['R1']['subs'][0]
        sub_sub = self.files['R1']['subs'][1]
        for file_ in [sub_idx, sub_sub]:
            if not os.path.isfile(file_):
                logger.error('ERROR! %s not found! Exiting...', file_)
                sys.exit(1)
        retimed_subs = [os.path.join(os.path.dirname(sub_idx),
                                     os.path.basename(sub_idx).replace(
                                     '.idx', '.retimed.idx')),
                        os.path.join(os.path.dirname(sub_sub),
                                     os.path.basename(sub_sub).replace(
                                     '.sub', '.retimed.sub'))]
        retime_vobsub(sub_idx, retimed_subs[0], self)
        os.rename(sub_sub, retimed_subs[1])
        self.files['R1']['retimed_subs'] = retimed_subs
        # delete original sub.idx
        del self.files['R1']['subs']
        os.remove(sub_idx)
        logger.info('Subtitle retime complete.')

    def retime_audio(self, config):
        '''
        Retime audio tracks
        '''
        logger.info('Retiming audio...')
        delaycut = config.get(APP_NAME, 'delaycut')
        en_idx = self.demux_map['R1']['audio'].index('en')
        en_audio = self.files['R1']['audio'][en_idx]
        retimed_audio = [os.path.join(os.path.dirname(en_audio),
                                      os.path.basename(en_audio).replace(
                                      '.ac3', '.retimed.ac3'))]
        bitrate = '51_448'
        if self.is_r1dbox:
            bitrate = '51_384'
        if self.is_pioneer:
            bitrate = '20_384'
            if self.episode == 'movie_3':
                bitrate = '20_192'
        retime_ac3(en_audio, retimed_audio[0], delaycut, bitrate, self)
        if len(self.demux_map['R1']['audio']) == 3:
            # 3 tracks, so this episode has US music
            # get track with US replacement music
            us_idx = self.demux_map['R1']['audio'].index('us')
            us_audio = self.files['R1']['audio'][us_idx]
            retimed_audio.append(os.path.join(os.path.dirname(us_audio),
                                 os.path.basename(us_audio).replace(
                                 '.ac3', '.retimed.ac3')))
            bitrate = '51_448' if self.is_movie else '20_192'
            retime_ac3(us_audio, retimed_audio[1], delaycut, bitrate, self)
        logger.info('Audio retime complete.')

    def make_mkv(self, config):
        pass