import os
import re
import sys
import logging
import constants
import subprocess
from utils import load_autodetect, save_autodetect, load_episode_disc_data

APP_NAME = constants.APP_NAME

logger = logging.getLogger(APP_NAME)


def _detect_ifo(directory):
    files = os.listdir(directory)
    max_vobs = 0
    ifo_file = ''
    for f in files:
        fname, ext = os.path.splitext(f)
        if fname.upper().startswith('VTS') and ext.upper() == '.IFO':
            ifo_base = fname.rsplit('_', 1)[0]
            vobs = list(
                filter(
                    lambda v: v != f and v.startswith(ifo_base),
                    files)
                )
            if len(vobs) > max_vobs:
                max_vobs = len(vobs)
                ifo_file = f
    return ifo_file


def auto_detect(episode):
    '''
    Run PGCDemux for each VOB ID and check the logfile
    Also save this information for later use
    '''
    demux_map = load_autodetect(episode.number)
    if demux_map:
        return demux_map

    logger.info('Auto-detecting demux information for '
                'R1 DBox episode %s...', episode.number)
    disc_name = episode.demux_map['R1_DBOX']['disc']
    logger.debug('Disc: %s', disc_name)

    auto_demux_map = {}
    disc_dir = os.path.join(episode.src_dir_top,
                            episode.series,
                            'R1_DBOX',
                            disc_name,
                            'VIDEO_TS')

    # get list of episodes that are on the current disc
    m = re.match(r'DRAGON_BOX_S(\d)_D(\d)',
                 disc_name)
    disc_ep_range = load_episode_disc_data('DBoxZ', m.group(1), m.group(2))
    disc_eps = range(disc_ep_range[0], disc_ep_range[1] + 1)

    ifo_file = _detect_ifo(disc_dir)
    ifo_file_abspath = os.path.join(disc_dir, ifo_file)

    vts = int(re.match(r'VTS_(\d\d)_0\.IFO', ifo_file.upper()).group(1))

    logger.debug('Using detected IFO file %s', ifo_file_abspath)
    eps_detected = 0
    for v in range(1, 100):
        # only generate logfile
        if eps_detected == len(disc_eps):
            break
        args = [episode.pgcdemux, '-vid', str(v),
                '-nom2v', '-noaud', '-nosub',
                '-nocellt', '-log', '-nogui',
                ifo_file_abspath, episode.temp_dir]
        subprocess.call(args)
        logfile = os.path.join(episode.temp_dir, 'LogFile.txt')
        with open(logfile) as file_:
            for line in file_:
                if line.startswith('Number of Cells in Selected VOB='):
                    num_cells = int(line.strip().split('=')[1])
                    # always 5 cells per episode
                    if num_cells == 5:
                        episode_num = str(disc_eps[eps_detected]).zfill(3)
                        logger.debug('Detected episode: %s', episode_num)
                        auto_demux_map[episode_num] = {
                            'audio': ['en', 'jp'],
                            'cells': None,
                            'disc': disc_name,
                            'pgc': 1,
                            'type': 'vid',
                            'vid': [v],
                            'vts': vts
                        }
                        eps_detected = eps_detected + 1
                    break
    logger.debug('Saving detected information for disc %s.', disc_name)
    save_autodetect(auto_demux_map)
    return auto_demux_map[episode.number]
