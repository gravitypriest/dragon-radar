'''
Object to contain episode metadata
'''
from utils import pad_zeroes, get_op_offset, load_series_frame_data


class Episode(object):

    def __init__(self, number, series):
        self.number = str(number).zfill(pad_zeroes(series))
        self.series = series
        frame_data = load_series_frame_data(series)
        op_offset = get_op_offset(series, number, frame_data)
        offsets = series_frame_data[self.number]
        self.offsets = self.combine_framedata(offsets, op_offset)

    def combine_framedata(self, offsets, op_offset):
        if op_offset or op_offset == 0:
            offsets['op'] = {'frame': 0, 'offset': op_offset}
        return offsets
