'''
Functions to demux discs
'''
import os
import subprocess
import tempfile
import shutil
import logging
import atexit
from utils import load_episode_disc_data, load_demux_map
from constants import Constants

R1_DEMUX_DIR = Constants.R1_DEMUX_DIR
R1_DISC_DIR = Constants.R1_DISC_DIR
FUNI_SUB_DIR = Constants.FUNI_SUB_DIR
MIN_SIZE = Constants.MIN_SIZE
APP_NAME = Constants.APP_NAME
PARAM_FILE = Constants.PARAM_FILE
VSRIP_TEMPLATE = Constants.VSRIP_TEMPLATE

logger = logging.getLogger(APP_NAME)


class Demux(object):

    def __init__(self, config, series, season, disc, sub_only):
        self.series = series
        self.season = season
        self.disc = disc
        self.working_dir = config.get(APP_NAME, 'working_dir')
        self.source_dir = config.get(APP_NAME, 'source_dir')
        self.pgcdemux = config.get(APP_NAME, 'pgcdemux')
        self.vsrip = config.get(APP_NAME, 'vsrip')
        self.disc_episodes = load_episode_disc_data(series,
                                                    str(season),
                                                    str(disc))
        source_folder = os.path.join(self.source_dir,
                                     self.series,
                                     R1_DISC_DIR,
                                     self._generate_source_folder_name(),
                                     'VIDEO_TS')
        logging.debug('Source folder: %s' % source_folder)

        main_feature = self._detect_main_feature(source_folder)
        self.source_file = os.path.join(source_folder, main_feature)
        self.sub_only = sub_only
        logger.debug('Series: %s, Season: %s, Disc: %s' % (self.series,
                     self.season, self.disc))

    def _run_dgdecode(self, video):
        pass

    def _run_pgcdemux(self, dest_path, vid, pgc=None):
        logger.info('Demuxing %s to %s...' % (self.source_file, dest_path))
        if pgc:
            p = pgc['pgc']
            s = pgc['start']
            e = pgc['end']
            # this call needs quotes around the paths because
            #  fuck consistency right?
            os.system(
                '{pgcdemux} -pgc {p} -m2v -aud -nosub -cellt -nolog -guism '
                '-sc {s} -ec {e} \"{source}\" \"{dest}\"'.format(
                    pgcdemux=self.pgcdemux,
                    p=p,
                    s=s,
                    e=e,
                    source=self.source_file,
                    dest=dest_path))
        else:
            os.system(
                '{pgcdemux} -vid {v} -m2v -aud -nosub -cellt -nolog -guism '
                '\"{source}\" \"{dest}\"'.format(
                    pgcdemux=self.pgcdemux,
                    v=vid,
                    source=self.source_file,
                    dest=dest_path))
        logger.info('Audio/video demux complete.')

    def _run_vsrip(self, vid_seq, vid_dir):
        vid_seq_str = '1 '
        for v in vid_seq:
            vid_seq_str += 'v{0} '.format(v)
        vid_seq_str = vid_seq_str.strip()
        out_file = os.path.join(vid_dir, 'Subtitle')
        param_file = os.path.join(vid_dir, PARAM_FILE)
        content = VSRIP_TEMPLATE.format(in_path=self.source_file,
                                        out_path=out_file,
                                        vid_sequence=vid_seq_str)
        with open(param_file, 'w') as param:
            param.write(content)

        logger.info('Demuxing subtitles to VobSub...')
        os.system('{vsrip} {param}'.format(vsrip=self.vsrip,
                                           param=param_file))
        logger.info('Subtitle demux complete.')

    def _translate_folder_to_episode(self, folder):
        vid = folder.split('V')[1]
        episodes = list(
            range(self.disc_episodes[0], self.disc_episodes[1] + 1))
        return str(episodes[int(vid)]).zfill(3)

    def _delete_temp(self, tmp_dir):
        logger.info('Deleting temporary files...')
        try:
            shutil.rmtree(tmp_dir)
        except OSError:
            logger.info('Problem deleting temp directory. '
                        'Please manually delete %s' % tmp_dir)

    def _clean_up_files(self, dest_path, tmp_dir):
        '''
        Go through the demuxed files and pick out what we want,
        delete the rest
        '''
        logger.info('Inspecting output...')
        final_dest = os.path.join(self.working_dir, self.series, R1_DEMUX_DIR)
        sub_dest = os.path.join(self.working_dir, self.series, FUNI_SUB_DIR)
        for d in os.listdir(tmp_dir):
            m2v = os.path.join(tmp_dir, d, 'VideoFile.m2v')
            aud0 = os.path.join(tmp_dir, d, 'AudioFile_80.ac3')
            aud1 = os.path.join(tmp_dir, d, 'AudioFile_81.ac3')
            chap = os.path.join(tmp_dir, d, 'Celltimes.txt')
            subi = os.path.join(tmp_dir, d, 'Subtitle.idx')
            subs = os.path.join(tmp_dir, d, 'Subtitle.sub')

            if os.path.isfile(m2v) or os.path.isfile(subi):
                if os.path.isfile(m2v) and os.path.getsize(m2v) < MIN_SIZE:
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
                    subi_n = os.path.join(
                        tmp_dir, d, '{e}.idx'.format(e=ep_num))
                    subs_n = os.path.join(
                        tmp_dir, d, '{e}.sub'.format(e=ep_num))

                    try:
                        os.rename(m2v, m2v_n)
                        os.rename(aud0, aud0_n)
                        os.rename(aud1, aud1_n)
                        os.rename(chap, chap_n)
                    except:
                        # ignore when there are missing files, might have only
                        #  one audio stream or be in sub-only mode
                        pass
                    try:
                        os.rename(subi, subi_n)
                        os.rename(subs, subs_n)
                    except:
                        pass

                    # make the directory
                    try:
                        os.makedirs(final_dest)
                    except OSError:
                        if not os.path.isdir(final_dest):
                            self._delete_temp(tmp_dir)
                            logger.debug('There was a problem creating %s' %
                                         final_dest)
                            raise
                        logger.debug('%s not created (already exists)' %
                                     final_dest)
                    try:
                        os.makedirs(sub_dest)
                    except OSError:
                        if not os.path.isdir(sub_dest):
                            self._delete_temp(tmp_dir)
                            logger.debug('There was a problem creating %s' %
                                         sub_dest)
                            raise
                        logger.debug('%s not created (already exists)' %
                                     sub_dest)
                    try:
                        shutil.move(m2v_n, final_dest)
                        shutil.move(aud0_n, final_dest)
                        shutil.move(aud1_n, final_dest)
                        shutil.move(chap_n, final_dest)
                    except shutil.Error as e:
                        logger.info(e)
                    try:
                        shutil.move(subi_n, sub_dest)
                        shutil.move(subs_n, sub_dest)
                    except shutil.Error as e:
                        logger.info(e)
            else:
                logger.info('%s does not exist' % m2v)
        logger.info('Demux complete.\n'
                    'See demuxed A/V files in %s.\n'
                    'See demuxed subs in %s.\n' % (final_dest, sub_dest))

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
        if self.series == 'DBZ':
            if self.season > 1:
                return 'DBZ_SEASON{s}_D{d}'.format(s=str(self.season).zfill(2),
                                                   d=self.disc)
            else:
                return 'DBZ_SEASON{s}_DISC{d}'.format(
                    s=str(self.season).zfill(2),
                    d=self.disc)

    def _create_temp_dir(self, vid, tmp_dir):
        vid_dir = os.path.join(tmp_dir,
                               'S{s}_D{d}_V{v}'.format(s=self.season,
                                                       d=self.disc, v=vid))
        os.mkdir(vid_dir)
        return vid_dir

    def season_set_demux(self):
        '''
        Demux from blue brick, orange brick, green brick
        '''
        dest_path = os.path.join(self.working_dir, self.series, R1_DEMUX_DIR)
        tmp_dir = tempfile.mkdtemp()
        # in the case of unexpected exit, we don't want to
        # keep temp files around
        atexit.register(self._delete_temp, tmp_dir)
        logging.debug('Temp folder: %s' % tmp_dir)

        if self.series in ['DB', 'DBGT']:
            # demux all VIDS
            for vid in xrange(1, 100):
                vid_dir = self._create_temp_dir(vid, tmp_dir)
                if not self.sub_only:
                    self._run_pgcdemux(dest_path, vid)

        elif self.series == 'DBZ':
            demux_map = load_demux_map(self.series,
                                       str(self.season))
            no_of_eps = self.disc_episodes[1] - self.disc_episodes[0] + 1
            logger.debug('# of episodes: %s' % no_of_eps)
            for ep in xrange(0, no_of_eps):
                vid_dir = self._create_temp_dir(ep, tmp_dir)
                if self.season > 1:
                    # S2 and up follow a pattern
                    start_chap = demux_map['pgcdemux'][0] + (ep * demux_map[1])
                    end_chap = demux_map['pgcdemux'][1] + (ep * demux_map[1])
                else:
                    # DBZ season 1 is the only weird one
                    current_ep = str(self.disc_episodes[0] + ep).zfill(3)
                    start_chap = demux_map['pgcdemux'][current_ep][0]
                    end_chap = demux_map['pgcdemux'][current_ep][1]

                vsrip_vid_seq = map(lambda v: (v + 6 * ep),
                                    demux_map['vsrip'])
                logger.debug('VSRip vid sequence: %s', vsrip_vid_seq)
                # chapters based on season set PGC layout
                pgc = {'pgc': 1, 'start': start_chap, 'end': end_chap}
                if not self.sub_only:
                    self._run_pgcdemux(vid_dir, 0, pgc=pgc)
                self._run_vsrip(vsrip_vid_seq, vid_dir)
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
