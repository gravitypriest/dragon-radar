import os
import logging
from constants import Constants
from utils import create_dir

AVS_DIR = Constants.AVS_DIR
R1_DEMUX_DIR = Constants.R1_DEMUX_DIR
R2_DEMUX_DIR = Constants.R2_DEMUX_DIR
APP_NAME = Constants.APP_NAME

logger = logging.getLogger(APP_NAME)


def load_r2_chapters(episode, working_dir):
    logger.debug('Loading R2 chapter file...')
    r2_chap_file = os.path.join(working_dir,
                                episode.series,
                                R2_DEMUX_DIR,
                                episode.number + '.txt')
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


def episode_edits(episode, r2_chaps):
    logger.debug('Generating edits...')
    offsets = episode.offsets
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


def generate_avs(episode, working_dir):
    r2_chaps = load_r2_chapters(episode, working_dir)
    r1_dir = os.path.join(working_dir,
                          episode.series,
                          R1_DEMUX_DIR)
    r2_dir = os.path.join(working_dir,
                          episode.series,
                          R2_DEMUX_DIR)
    # only use audio channels 2 and 3 because Virtualdub can't deal with 5.1
    import_section = ('r1_v = MPEG2Source(\"{r1_v}\")\n'
                      'r2_v = MPEG2Source(\"{r2_v}\")\n'
                      'r1_a = NicAC3Source(\"{r1_a}\").GetChannel(2,3)\n'
                      'r2_a = NicAC3Source(\"{r2_a}\")\n'.format(
                          r1_v=os.path.join(r1_dir, episode.number + '.d2v'),
                          r2_v=os.path.join(r2_dir, episode.number + '.d2v'),
                          r1_a=os.path.join(
                              r1_dir, episode.number + '_en.ac3'),
                          r2_a=os.path.join(r2_dir, episode.number + '.ac3')))
    prep_section = ('r1_v = AudioDub(r1_v, r1_a)\n'
                    'r2_v = AudioDub(r2_v, r2_a)\n'
                    'b=BlankClip(clip=r1_v, length=10000)\n')
    process_section = episode_edits(episode, r2_chaps)
    output_section = ('r1_v = r1_v.Telecide().Decimate()\n'
                      'r2_v = r2_v.Telecide().Decimate()\n'
                      'StackHorizontal(r1_v, r2_v)\n')
    return '\n'.join([import_section, prep_section,
                      process_section, output_section])


def write_avs_file(episode, config):
    working_dir = config.get(APP_NAME, 'working_dir')
    avs_fname = os.path.join(working_dir,
                             episode.series,
                             AVS_DIR,
                             episode.number + '.avs')
    create_dir(os.path.dirname(avs_fname))

    with open(avs_fname, 'w') as avs_file:
        logger.info('%s.avs opened for writing.' % episode.number)
        avs_file.write(generate_avs(episode, working_dir))
    logger.info('Generation complete. Script is at %s' % avs_fname)
