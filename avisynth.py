import os
import logging
from constants import Constants
from utils import create_dir, pad_zeroes

AVS_DIR = Constants.AVS_DIR
R1_DEMUX_DIR = Constants.R1_DEMUX_DIR
R2_DEMUX_DIR = Constants.R2_DEMUX_DIR
APP_NAME = Constants.APP_NAME

logger = logging.getLogger(APP_NAME)


def run_dgdecode(path, episodes, series, dgdecode):
    start = int(episodes[0])
    end = int(episodes[1])
    for e in xrange(start, end + 1):
        ep_str = str(e).zfill(pad_zeroes(series))
        full_path = os.path.join(path, ep_str)
        if (os.path.isfile(full_path + '.m2v') and
           not os.path.isfile(full_path + '.d2v')):
            logger.info('Generating %s.d2v...' % ep_str)
            os.system(
                '{dgdecode} -IF=[{inf}] -OF=[{outf}] -MINIMIZE -EXIT'.format(
                    dgdecode=dgdecode,
                    inf=full_path + '.m2v',
                    outf=full_path))


class Avisynth(object):

    def __init__(self, episode, config):
        self.dgdecode = config.get(APP_NAME, 'dgdecode')
        self.episode = episode
        working_dir = config.get(APP_NAME, 'working_dir')
        self.dst_file = os.path.join(working_dir,
                                     episode.series,
                                     AVS_DIR,
                                     episode.number + '.avs')
        self.r1_fname = os.path.join(working_dir, episode.series,
                                     Constants.R1_DEMUX_DIR, episode.number)
        self.r2_fname = os.path.join(working_dir, episode.series,
                                     Constants.R2_DEMUX_DIR, episode.number)

    def check_for_d2v(self):
        logger.debug('Checking that %s.d2v files (R1 and R2) exist...' %
                     self.episode.number)
        r2_d2v_file = self.r2_fname + '.d2v'
        r1_d2v_file = self.r1_fname + '.d2v'
        if not os.path.isfile(r2_d2v_file):
            logger.debug('R2 %s.d2v file not found. Creating...' %
                         self.episode.number)
            run_dgdecode(os.path.dirname(r2_d2v_file),
                         [self.episode.number, self.episode.number],
                         self.episode.series, self.dgdecode)
        if not os.path.isfile(r1_d2v_file):
            logger.debug('R1 %s.d2v file not found. Creating...' %
                         self.episode.number)
            run_dgdecode(os.path.dirname(r1_d2v_file),
                         [self.episode.number, self.episode.number],
                         self.episode.series, self.dgdecode)

    def episode_edits(self):
        logger.debug('Generating edits...')
        r2_chaps = self.episode.r2_chapters
        offsets = self.episode.offsets
        edits = []
        for key in ['op', 'prologue', 'partA', 'partB', 'ED', 'NEP']:
            if key in offsets.keys():
                if key == 'partA':
                    # no part A in r2_chaps so improvise
                    r2_chaps[key] = offsets[key]['frame']
                ch_begin = r2_chaps[key]        # JP chapter point
                ch_end = ch_begin - 1           # frame just before chapter
                offset = offsets[key]['offset']
                if key == 'op':
                    if offset < 0:
                        edit_str = ('r1_v = Trim(b, 1, {offset} ++ '
                                    'Trim(r1_v, 0, 999999)'.format(
                                        offset=offset))
                    else:
                        edit_str = 'r1_v = Trim(r1_v, {offset}, 999999)'.format(
                            offset=offset)
                else:
                    if offset < 0:
                        edit_str = ('r1_v = Trim(r1_v, 0, {ch_end}) ++ '
                                    'Trim(b, 1, {offset}) ++ '
                                    'Trim(r1_v, {ch_begin}, 999999)'.format(
                                        ch_end=ch_end,
                                        offset=(offset * (-1)),
                                        ch_begin=ch_begin))
                    else:
                        edit_str = ('r1_v = Trim(r1_v, 0, {ch_end}) ++ '
                                    'Trim(r1_v, {off_begin}, 999999)'.format(
                                        ch_end=ch_end,
                                        off_begin=ch_begin + offset))
                edits.append(edit_str)
        return '\n'.join(edits) + '\n'

    def generate_avs(self):
        # only use audio channels 2 and 3 because Virtualdub can't deal with 5.1
        import_section = ('r1_v = MPEG2Source(\"{r1_v}\")\n'
                          'r2_v = MPEG2Source(\"{r2_v}\")\n'
                          'r1_a = NicAC3Source(\"{r1_a}\").GetChannel(2,3)\n'
                          'r2_a = NicAC3Source(\"{r2_a}\")\n'.format(
                              r1_v=self.r1_fname + '.d2v',
                              r2_v=self.r2_fname + '.d2v',
                              r1_a=self.r1_fname + '_en.ac3',
                              r2_a=self.r2_fname + '.ac3'))
        prep_section = ('r1_v = AudioDub(r1_v, r1_a)\n'
                        'r2_v = AudioDub(r2_v, r2_a)\n'
                        'b=BlankClip(clip=r1_v, length=10000)\n')
        process_section = self.episode_edits()
        output_section = ('r1_v = r1_v.Telecide().Decimate()\n'
                          'r2_v = r2_v.Telecide().Decimate()\n'
                          'StackHorizontal(r1_v, r2_v)\n')
        return '\n'.join([import_section, prep_section,
                          process_section, output_section])

    def write_avs_file(self):
        self.check_for_d2v()
        create_dir(os.path.dirname(self.dst_file))

        with open(self.dst_file, 'w') as avs_file:
            logger.info('%s.avs opened for writing.' % self.episode.number)
            avs_file.write(self.generate_avs())
        logger.info('Generation complete. Script is at %s' % self.dst_file)
