'''
Object to contain episode metadata
'''
import os
import logging
from utils import pad_zeroes, get_op_offset, load_series_frame_data
from constants import Constants

APP_NAME = Constants.APP_NAME
R2_DEMUX_DIR = Constants.R2_DEMUX_DIR

logger = logging.getLogger(APP_NAME)


class Episode(object):

    def __init__(self, config, number, series, series_frame_data):
        ep_str = str(number).zfill(pad_zeroes(series))
        self.number = ep_str
        self.series = series
        frame_data = load_series_frame_data(series)
        op_offset = get_op_offset(series, number, frame_data)
        offsets = series_frame_data[self.number]
        self.offsets = self.combine_framedata(offsets, op_offset)
        working_dir = config.get(APP_NAME, 'working_dir')
        self.r2_chapters = self.load_r2_chapters(series, ep_str, working_dir)

    def combine_framedata(self, offsets, op_offset):
        if op_offset or op_offset == 0:
            offsets['op'] = {'frame': 0, 'offset': op_offset}
        return offsets

    def load_r2_chapters(self, series, number, working_dir):
        logger.debug('Loading R2 chapter file...')
        r2_chap_file = os.path.join(working_dir,
                                    series,
                                    R2_DEMUX_DIR,
                                    number + '.txt')
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
