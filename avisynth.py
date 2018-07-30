import os
import logging
import subprocess
import constants
from utils import create_dir, pad_zeroes

APP_NAME = constants.APP_NAME

logger = logging.getLogger(APP_NAME)


def make_string(ch_begin, ch_end, offset, first=False):
    if first:
        if offset < 0:
            return ('r1_v = Trim(b, 1, {offset}) ++ '
                    'Trim(r1_v, 0, 999999)'.format(
                        offset=offset))
        else:
            return 'r1_v = Trim(r1_v, {offset}, 999999)'.format(
                       offset=offset)
    else:
        if offset < 0:
            return ('r1_v = Trim(r1_v, 0, {ch_end}) ++ '
                    'Trim(b, 1, {offset}) ++ '
                    'Trim(r1_v, {ch_begin}, 999999)'.format(
                        ch_end=ch_end,
                        offset=(offset * (-1)),
                        ch_begin=ch_begin))
        else:
            return ('r1_v = Trim(r1_v, 0, {ch_end}) ++ '
                    'Trim(r1_v, {off_begin}, 999999)'.format(
                        ch_end=ch_end,
                        off_begin=ch_begin + offset))


def episode_edits(episode):
    logger.debug('Generating edits...')
    r2_chaps = episode.r2_chapters
    if episode.is_pioneer:
        offsets = episode.pioneer_offsets
    else:
        offsets = episode.offsets
    edits = []

    if isinstance(offsets, list):
        totalOffset = 0
        for o in offsets:
            if o['offset'] == 0:
                continue
            ch_begin = o['frame'] - totalOffset
            ch_end = ch_begin - 1
            offset = o['offset']
            edit_str = make_string(ch_begin, ch_end, offset, first=offsets.index(o) == 0)
            edits.append(edit_str)
    else:
        for key in ['op', 'prologue', 'partB', 'ED', 'NEP']:
            if key in offsets.keys():
                ch_begin = r2_chaps[key]        # JP chapter point
                ch_end = ch_begin - 1           # frame just before chapter
                offset = offsets[key]['offset']
                if key == 'op':
                    edit_str = make_string(ch_begin, ch_end, offset, first=True)
                else:
                    edit_str = make_string(ch_begin, ch_end, offset)
                edits.append(edit_str)
    return '\n'.join(edits) + '\n'


def generate_avs(episode):
    # only use audio channels 2 and 3 because Virtualdub can't deal with 5.1
    r1_version = 'R1_DBOX' if episode.is_r1dbox else 'R1'
    r1_version = 'PIONEER' if episode.is_pioneer else 'R1'
    r1_v = os.path.join('.', r1_version, 'VideoFile.d2v')
    r2_v = os.path.join('.', 'R2', 'VideoFile.d2v')
    r1_a = os.path.join('.', r1_version, 'AudioFile_80.ac3')
    r2_a = os.path.join('.', 'R2', 'AudioFile_80.ac3')
    import_section = ('r1_v = MPEG2Source(\"{r1_v}\")\n'
                      'r2_v = MPEG2Source(\"{r2_v}\")\n'
                      'r1_a = NicAC3Source(\"{r1_a}\")\n'
                      'r2_a = NicAC3Source(\"{r2_a}\")\n'.format(
                          r1_v=r1_v,
                          r2_v=r2_v,
                          r1_a=r1_a,
                          r2_a=r2_a))
    prep_section = ('r1_v = AudioDub(r1_v, r1_a)\n'
                    'r2_v = AudioDub(r2_v, r2_a)\n'
                    'b=BlankClip(clip=r1_v, length=10000)\n')
    process_section = episode_edits(episode)
    output_section = ('r1_v = r1_v.Telecide().Decimate().LanczosResize(640, 480).Subtitle("US",10,10)\n'
                      'r2_v = r2_v.Telecide().Decimate().LanczosResize(640, 480).Subtitle("JP",10,10)\n'
                      'StackHorizontal(r1_v, r2_v)\n')
    return '\n'.join([import_section, prep_section,
                      process_section, output_section])


def run_dgindex(dir_, episode):
    m2vfile = os.path.join(dir_, 'VideoFile.m2v')
    outfile = os.path.join(dir_, 'VideoFile')
    args = [episode.dgindex,
            '-IF=[' + m2vfile + ']',
            '-OF=[' + outfile + ']',
            '-MINIMIZE', '-EXIT']
    subprocess.call(args)


def check_for_d2v(dir_, episode):
    logger.debug('Checking that .d2v file exists for episode %s...' %
                 episode.number)
    d2v_file = os.path.join(dir_, 'VideoFile.d2v')
    if not os.path.isfile(d2v_file):
        logger.debug('.d2v file not found. Creating...')
        run_dgindex(os.path.dirname(d2v_file), episode)


def write_avs_file(dir_, episode):
    regions = ['R2']
    if episode.is_pioneer:
        regions.append('PIONEER')
    elif episode.is_r1dbox:
        regions.append('R1_DBOX')
    else:
        regions.append('R1')
    for r in regions:
        region_dir = os.path.join(dir_, r)
        check_for_d2v(region_dir, episode)
    return
    dst_file = os.path.join(dir_,
                            episode.number + '.avs')
    with open(dst_file, 'w') as avs_file:
        logger.info('%s.avs opened for writing.' % episode.number)
        avs_file.write(generate_avs(episode))
    logger.info('Generation complete. Script is at %s' % dst_file)
