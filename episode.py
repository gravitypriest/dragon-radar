import os
import sys
import shutil
import logging
import constants
from utils import (pad_zeroes, get_op_offset, load_frame_data,
                   load_demux_map, create_dir, move_file, series_to_movie)
from demux import demux, files_index
from subtitle import retime_vobsub, detect_streams
from audio import retime_ac3
from avisynth import write_avs_file
from mkvmux import make_mkv

APP_NAME = constants.APP_NAME

logger = logging.getLogger(APP_NAME)


def _combine_framedata(offsets, op_offset):
    if op_offset or op_offset == 0:
        offsets['op'] = {'frame': 0, 'offset': op_offset}
    return offsets


def _load_r2_chapters(r2_chap_file, series, is_special):
    logger.debug('Loading R2 chapter file...')
    with open(r2_chap_file) as r2_chaps:
        chap_list = r2_chaps.readlines()
    if series == 'MOVIES' or is_special:
        chap_list.insert(0, 0)
        return map(lambda c: int(c), chap_list)
    chapters = {
        'op': 0,
        'prologue': int(chap_list[0]),
        'partB': int(chap_list[1]),
        'ED': int(chap_list[2])
    }
    if len(chap_list) > 3:
        chapters['NEP'] = int(chap_list[3])
    return chapters


def _retimed_fname(fname):
    '''
    Generate the filename for a retimed subtitle or audio track
    '''
    splitpath = os.path.splitext(fname)
    return '.retimed'.join(splitpath)


class Episode(object):
    '''
    Object for an episode, call all functionality by episode
    '''
    def __init__(self, number, config, args, tmp_dir, special):
        series = args.series
        self.is_movie = False
        if args.movie:
            series = 'MOVIES'
            number = series_to_movie(args.series, number)
            self.is_movie = True
        if special:
            ep_str = special
            self.is_special = True
        else:
            ep_str = str(number).zfill(pad_zeroes(series))
            self.is_special = False
        if args.r1_dbox:
            frame_data, op_offset = load_frame_data('DBoxZ', ep_str)
        else:
            frame_data, op_offset = load_frame_data(series, ep_str)

        # config stuff
        self.pgcdemux = config.get(APP_NAME, 'pgcdemux')
        self.vsrip = config.get(APP_NAME, 'vsrip')
        self.delaycut = config.get(APP_NAME, 'delaycut')
        self.dgindex = config.get(APP_NAME, 'dgindex')
        self.mkvmerge = config.get(APP_NAME, 'mkvmerge')
        self.restream = config.get(APP_NAME, 'restream')
        self.src_dir_top = config.get(APP_NAME, 'source_dir')
        self.output_dir = config.get(APP_NAME, 'output_dir')

        # special flags
        self.is_r1dbox = args.series == 'DBZ' and args.r1_dbox
        self.is_pioneer = args.pioneer
        self.no_funi = args.no_funi
        self.demux_r1_vid = args.r1_vid
        self.verbose = args.verbose

        # options
        self.no_mux = args.no_mux
        self.sub_only = args.sub_only

        self.temp_dir = os.path.join(tmp_dir, ep_str)
        create_dir(self.temp_dir)

        self.number = ep_str
        self.series = series
        self.offsets = _combine_framedata(frame_data, op_offset)
        self.pioneer_offsets = None if not self.is_pioneer else load_frame_data(series, str(number+50))[0]
        self.r2_chapters = {}
        if not args.no_demux:
            self.demux_map = load_demux_map(series, ep_str)
        else:
            self.demux_map = {'R1': {'audio': ['en', 'jp']}}
        self.files = self._init_files() if args.no_demux else {}

    def _init_files(self):
        '''
        Create file dictionary with locations of demuxed files
        Only used if not demuxing
        '''
        _files = {}
        episode_dir = os.path.join(self.output_dir, self.series, self.number)

        for r in self._regions():
            _files[r] = files_index(os.path.join(episode_dir, r))

            if r == 'R2':
                if not os.path.isfile(_files['R2']['chapters'][0]):
                    logger.error('Could not find the demuxed R2 chapters file at %s. '
                                 'This probably means that either you haven\'t demuxed '
                                 'yet, or the `output_dir` setting in dragon-radar.ini '
                                 'is incorrect.',
                                 _files['R2']['chapters'][0])
                    sys.exit(1)
                self.r2_chapters = _load_r2_chapters(_files['R2']['chapters'][0],
                                                     self.series, self.is_special)
            else:
                retimed_sub_idx_path = _retimed_fname(_files[r]['subs'][0])
                retimed_sub_sub_path = _retimed_fname(_files[r]['subs'][1])
                if os.path.isfile(retimed_sub_idx_path):
                    _files[r]['retimed_subs'] = [retimed_sub_idx_path, retimed_sub_sub_path]
                for a in _files[r]['audio']:
                    retimed = _retimed_fname(a)
                    if os.path.isfile(retimed):
                        if 'retimed_audio' not in _files[r]:
                            _files[r]['retimed_audio'] = []
                        _files[r]['retimed_audio'].append(retimed)

        return _files

    def _regions(self):
        regions = ['R2', 'R1']
        if self.is_r1dbox:
            regions = ['R2', 'R1_DBOX']
        if self.is_pioneer:
            regions = ['R2', 'PIONEER']
            if not self.no_funi:
                regions.append('R1')
        return regions

    def demux(self):
        '''
        Demux video, audio, subs
        Return an object with the filenames
        '''
        src_dir_series = os.path.join(self.src_dir_top, self.series)

        for r in self._regions():
            if r not in self.demux_map:
                continue
            src_dir = os.path.join(src_dir_series, r)
            dest_dir = os.path.join(self.temp_dir, r)
            create_dir(dest_dir)
            logger.info('Demuxing %s %s %s...', self.series, self.number, r)
            self.files[r] = demux(self, src_dir, dest_dir,
                                  self.demux_map[r],
                                  novid=((r == 'R1' or r == 'PIONEER') and
                                         not self.demux_r1_vid),
                                  nosub=(r == 'R2'), sub_only=self.sub_only,
                                  orange_brick=(
                                    r == 'R1' and
                                    self.series == 'DBZ' and
                                    not self.is_special))
        if not self.sub_only and 'R2' in self.files:
            self.r2_chapters = _load_r2_chapters(
                self.files['R2']['chapters'][0], self.series,
                self.is_special)

    def retime_subs(self):
        '''
        Retime .idx file, rename .sub file to match
        new .idx filename, then save to episode.files
        '''
        logger.info('Retiming subtitles...')
        for r in self._regions():
            if r == 'R2':
                continue
            sub_idx = self.files[r]['subs'][0]
            sub_sub = self.files[r]['subs'][1]
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
            shutil.copy(sub_sub, retimed_subs[1])
            self.files[r]['retimed_subs'] = retimed_subs
        logger.info('Subtitle retime complete.')

    def retime_audio(self):
        '''
        Retime audio tracks
        '''
        logger.info('Retiming audio...')
        for r in self._regions():
            if r == 'R2':
                continue
            en_idx = self.demux_map[r]['audio'].index('en')
            en_audio = self.files[r]['audio'][en_idx]
            retimed_audio = [os.path.join(os.path.dirname(en_audio),
                                          os.path.basename(en_audio).replace(
                                          '.ac3', '.retimed.ac3'))]
            bitrate = '51_448'
            if r == 'R1_DBOX':
                bitrate = '51_384'
            if r == 'PIONEER':
                bitrate = '20_384'
                if self.number == '03':
                    bitrate = '20_192'
            retime_ac3(self, en_audio, retimed_audio[0], bitrate, region=r)
            if 'us' in self.demux_map[r]['audio']:
                # get track with US replacement music
                us_idx = self.demux_map[r]['audio'].index('us')
                us_audio = self.files[r]['audio'][us_idx]
                retimed_audio.append(os.path.join(os.path.dirname(us_audio),
                                     os.path.basename(us_audio).replace(
                                     '.ac3', '.retimed.ac3')))
                bitrate = '51_448' if (self.is_movie or
                                       (self.is_special and
                                        self.series == 'DBGT')) else '20_192'
                retime_ac3(self, us_audio, retimed_audio[1], bitrate)
            self.files[r]['retimed_audio'] = retimed_audio
        logger.info('Audio retime complete.')

    def mux(self):
        '''
        Create the MKV for this episode
        '''
        self.mkv_file = self.mkv_filename()
        logger.info('Multiplexing to \"%s\",\nplease wait a few moments...', self.mkv_file)
        make_mkv(self)
        logger.info('Multiplex of %s %s complete.', self.series, self.number)

    def move_demuxed_files(self):
        dest_dir = os.path.join(self.output_dir, self.series, self.number)
        logger.info('Moving files from %s to %s, please wait a moment...',
                    self.temp_dir, dest_dir)
        new_files = {}
        for r in self.files:
            region_dir = os.path.join(dest_dir, r)
            create_dir(region_dir)
            new_files[r] = {}
            for type_ in ['video', 'audio', 'subs', 'chapters',
                          'retimed_subs', 'retimed_audio']:
                if type_ in self.files[r]:
                    new_files[r][type_] = []
                    for file_ in self.files[r][type_]:
                        if os.path.isfile(file_):
                            dest_fname = os.path.join(
                                region_dir, os.path.basename(file_))
                            logger.debug('Moving %s...', file_)
                            move_file(file_, dest_fname)
                            new_files[r][type_].append(dest_fname)
                            logger.debug('Complete.')
        self.files = new_files
        logger.info('Move complete! Demuxed files in %s', dest_dir)

    def make_avs(self):
        if self.is_pioneer:
            r = 'PIONEER'
        elif self.is_r1dbox:
            r = 'R1_DBOX'
        else:
            r = 'R1'
        print(self.is_pioneer)
        detect_streams(self.files[r]['subs'][0])
        dest_dir = os.path.join(self.output_dir, self.series, self.number)
        if os.path.isdir(dest_dir):
            if not self.r2_chapters:
                if 'R2' not in self.demux_map:
                    self.r2_chapters = {}
                else:
                    chapters_file = os.path.join(dest_dir, 'R2', 'Celltimes.txt')
                    self.r2_chapters = _load_r2_chapters(chapters_file, self.series, self.is_special)
            write_avs_file(dest_dir, self)
        else:
            logger.error('%s not found', dest_dir)
            sys.exit(1)

    def mkv_filename(self):
        from utils import load_title
        if self.is_movie or self.is_special:
            base_fname = '{0}.mkv'.format(load_title(self.series, self.number))
        else:
            base_fname = '{0} ~ {1}.mkv'.format(self.number, load_title(self.series, self.number))
        return os.path.join(self.output_dir, base_fname)
