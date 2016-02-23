'''
Functions to demux discs
'''
import os
import subprocess
import tempfile
import shutil
import logging
from utils import load_episode_disc_data
from constants import Constants

R1_DEMUX_DIR = Constants.R1_DEMUX_DIR
R1_DISC_DIR = Constants.R1_DISC_DIR
MIN_SIZE = Constants.MIN_SIZE
APP_NAME = Constants.APP_NAME

logger = logging.getLogger(APP_NAME)


class Demux(object):

    def __init__(self, config, series, season, disc):
        self.series = series
        self.season = season
        self.disc = disc
        self.working_dir = config.get(APP_NAME, 'working_dir')
        self.source_dir = config.get(APP_NAME, 'source_dir')
        self.pgcdemux = config.get(APP_NAME, 'pgcdemux')
        self.disc_episodes = load_episode_disc_data(series,
                                                    str(season),
                                                    str(disc))

    def _run_dgdecode(self, video):
        pass

    def _run_pgcdemux(self, source_file, dest_path, vid, pgc=None):
        logger.info('Demuxing %s to %s...' % source_file, dest_path)
        if pgc:
            p = pgc['pgc']
            s = pgc['start']
            e = pgc['end']
            os.system(
                '{pgcdemux} -pgc {p} -m2v -aud -nosub -cellt -nolog -guism '
                '-sc {s} -ec {e} \"{source}\" \"{dest}\"'.format(
                    pgcdemux=self.pgcdemux,
                    p=p,
                    s=s,
                    e=e,
                    source=source_file,
                    dest=dest_path))
        else:
            os.system(
                '{pgcdemux} -vid {v} -m2v -aud -nosub -cellt -nolog -guism '
                '{source} {dest}'.format(
                    pgcdemux=self.pgcdemux,
                    v=vid,
                    source=source_file,
                    dest=dest_path))

    def _translate_folder_to_episode(self, folder):
        vid = folder.split('V')[1]
        episodes = list(
            range(self.disc_episodes[0], self.disc_episodes[1] + 1))
        return str(episodes[int(vid)]).zfill(3)

    def _clean_up_files(self, dest_path, tmp_dir):
        '''
        Go through the demuxed files and pick out what we want,
        delete the rest
        '''
        logger.info('Inspecting output...')
        final_dest = os.path.join(self.working_dir, self.series, R1_DEMUX_DIR)
        for d in os.listdir(tmp_dir):
            m2v = os.path.join(tmp_dir, d, 'VideoFile.m2v')
            aud0 = os.path.join(tmp_dir, d, 'AudioFile_80.ac3')
            aud1 = os.path.join(tmp_dir, d, 'AudioFile_81.ac3')
            chap = os.path.join(tmp_dir, d, 'Celltimes.txt')
            if os.path.isfile(m2v):
                if os.path.getsize(m2v) < MIN_SIZE:
                    logger.info('Ripped something that\'s not an episode. '
                                'Ignoring.')
                else:
                    ep_num = self._translate_folder_to_episode(d)
                    logger.info('Ripped an episode.\t'
                                'Renaming to %s and moving...' % ep_num)
                    m2v_n = os.path.join(
                        tmp_dir, d, '{e}.m2v'.format(e=ep_num))
                    aud0_n = os.path.join(
                        tmp_dir, d, '{e}_en.ac3'.format(e=ep_num))
                    aud1_n = os.path.join(
                        tmp_dir, d, '{e}_us.ac3'.format(e=ep_num))
                    chap_n = os.path.join(
                        tmp_dir, d, '{e}.txt'.format(e=ep_num))

                    os.rename(m2v, m2v_n)
                    os.rename(aud0, aud0_n)
                    os.rename(aud1, aud1_n)
                    os.rename(chap, chap_n)

                    try:
                        shutil.move(m2v_n, final_dest)
                        shutil.move(aud0_n, final_dest)
                        shutil.move(aud1_n, final_dest)
                        shutil.move(chap_n, final_dest)
                    except shutil.Error as e:
                        logger.info(e)

                    logger.info('Move complete.')
            else:
                logger.info('%s does not exist' % m2v)
        logger.info('Deleting temporary files...')
        try:
            shutil.rmtree(tmp_dir)
        except OSError:
            logger.info('Problem deleting temp directory. '
                        'Please manually delete %s' % tmp_dir)

    def _detect_main_feature(self, source_folder):
        '''
        Detect which IFO has the most VOBs associated with it
        '''
        # look for VTS_XX_3.VOB
        files = os.listdir(source_folder)
        vob = [f for f in files if '_3.VOB' in f][0]
        ifo = vob.strip().split('_3.VOB')[0] + '_0.IFO'

        return ifo

    def _detect_episodes(self, series, season, disc):
        '''
        Figure out what episodes #s we are using
        '''
        return episodes

    def _generate_source_folder_name(self):
        if self.series == 'DB':
            return 'DRAGON_BALL_S{s}_D{d}'.format(s=self.season, d=self.disc)
        if self.series == 'DBZOB':
            if self.season > 1:
                return 'DBZ_SEASON{s}_D{d}'.format(s=str(self.season).zfill(2),
                                                   d=self.disc)
            else:
                return 'DBZ_SEASON{s}_DISC{d}'.format(
                    s=str(self.season).zfill(2),
                    d=self.disc)

    def _create_temp_dir(self, vid, tmp_dir):
        vid_dir = os.path.join(tmp_dir,
                               'S{s} D{d} V{v}'.format(s=self.season,
                                                       d=self.disc, v=vid))
        os.mkdir(vid_dir)
        return vid_dir

    def season_set_demux(self):
        '''
        Demux from blue brick, orange brick, green brick
        '''
        source_folder = os.path.join(self.source_dir,
                                     self.series,
                                     R1_DISC_DIR,
                                     self._generate_source_folder_name(),
                                     'VIDEO_TS')
        logging.debug('Source folder: %s' % source_folder)

        main_feature = self._detect_main_feature(source_folder)
        source_file = os.path.join(source_folder, main_feature)
        dest_path = os.path.join(self.working_dir, self.series, R1_DEMUX_DIR)
        tmp_dir = tempfile.mkdtemp()
        logging.debug('Temp folder: %s' % tmp_dir)

        if self.series in ['DB', 'DBGT']:
            # demux all VIDS
            for vid in xrange(1, 100):
                vid_dir = self._create_temp_dir(vid, tmp_dir)
                self._run_pgcdemux(source_file, dest_path, vid)

        elif self.series == 'DBZOB':
            no_of_eps = self.disc_episodes[1] - self.disc_episodes[0] + 1
            logger.debug('# of episodes: ' % no_of_eps)
            for ep in xrange(0, no_of_eps):
                vid_dir = self._create_temp_dir(ep, tmp_dir)
                # chapters based on season set PGC layout
                pgc = {'pgc': 1, 'start': ep * 9 + 1, 'end': (ep + 1) * 9}
                self._run_pgcdemux(source_file, vid_dir, 0, pgc=pgc)

        # go through and delete dummy files and rename based on episode
        self._clean_up_files(dest_path, tmp_dir)

        # if avisynth is req'd, run DGDecode on all m2vs

    def dbox_demux(self):
        '''
        Demux from R1 Dragon Box
        '''
        pass

    def r2_demux(self):
        '''
        Demux from R2 Dragon Box
        '''
        pass

    def subtitle_demux(self):
        '''
        Use VSRip to pull out the subtitles
        '''
        pass
