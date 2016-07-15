'''
Module with demuxing functions
'''
import os
import sys
import subprocess
import logging
from constants import Constants

PARAM_FILE = Constants.PARAM_FILE
VSRIP_TEMPLATE = Constants.VSRIP_TEMPLATE
APP_NAME = Constants.APP_NAME
logger = logging.getLogger(APP_NAME)


def _run_pgcdemux(pgcdemux, source_ifo, dest_dir, type_, vid, pgc, cells):
    args = [pgcdemux, '-nolog', '-guism']
    args.extend(['-m2v', '-cellt'])
    args.append('-aud')
    args.append('-nosub')

    if type_ == 'vid':
        args.extend(['-vid', str(vid)])
    if type_ == 'pgc':
        args.extend(['-pgc', str(pgc)])
        if cells:
            args.extend(['-sc', str(cells[0]), '-ec', str(cells[1])])
    args.extend([source_ifo, dest_dir])
    proc = subprocess.run(args)


def _run_vsrip(vsrip, source_ifo, dest_dir, pgc, vid):
    '''
    Run VSRip to extract DVD subtitles as VobSub
    '''
    vid_seq_str = '1 '
    for v in vid:
        vid_seq_str += 'v{0} '.format(v)
    vid_seq_str = vid_seq_str.strip()
    out_file = os.path.join(dest_dir, 'Subtitle')
    param_file = os.path.join(dest_dir, PARAM_FILE)
    content = VSRIP_TEMPLATE.format(in_path=source_ifo,
                                    out_path=out_file,
                                    vid_sequence=vid_seq_str,
                                    pgc=pgc)
    with open(param_file, 'w') as param:
        param.write(content)
    subprocess.run([vsrip, param_file])


def files_index(dest_dir):
    video = os.path.join(dest_dir, 'VideoFile.m2v')
    aud_0 = os.path.join(dest_dir, 'AudioFile_80.ac3')
    aud_1 = os.path.join(dest_dir, 'AudioFile_81.ac3')
    aud_2 = os.path.join(dest_dir, 'AudioFile_82.ac3')
    chapters = os.path.join(dest_dir, 'Celltimes.txt')
    sub_idx = os.path.join(dest_dir, 'Subtitle.idx')
    sub_sub = os.path.join(dest_dir, 'Subtitle.sub')

    return {
        'video': [video],
        'audio': [aud_0, aud_1, aud_2],
        'subs': [sub_idx, sub_sub],
        'chapters': [chapters]
    }


def demux(episode, src_dir, dest_dir, demux_map, nosub=False, sub_only=False):
    '''
    Demux video, audio, subs
    Return an object with the filenames
    '''
    cells = demux_map['cells']
    type_ = demux_map['type']
    vid = demux_map['vid']
    pgc = demux_map['pgc']
    source_ifo = os.path.join(
        src_dir,
        demux_map['disc'],
        'VIDEO_TS',
        ('VTS_0%d_0.IFO' % demux_map['vts'])
    )
    if not sub_only:
        logger.info('Demuxing video and audio...')
        _run_pgcdemux(episode.pgcdemux, source_ifo, dest_dir,
                      type_, vid, pgc, cells)
        logger.info('Video & audio demux complete.')
    if not nosub:
        logger.info('Demuxing subtitles to VobSub...')
        _run_vsrip(episode.vsrip, source_ifo, dest_dir, pgc, vid)
        logger.info('Subtitle demux complete.')

    return files_index(dest_dir)
