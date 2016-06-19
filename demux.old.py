'''
Functions to demux discs
'''
import os
import tempfile
import logging
import atexit
import subprocess
from utils import (load_episode_disc_data,
                   load_demux_map,
                   create_dir,
                   delete_temp,
                   move_file,
                   rename,
                   pad_zeroes)
from constants import Constants
from avisynth import run_dgindex

R1_DEMUX_DIR = Constants.R1_DEMUX_DIR
R1_DISC_DIR = Constants.R1_DISC_DIR
R2_DISC_DIR = Constants.R2_DISC_DIR
FUNI_SUB_DIR = Constants.FUNI_SUB_DIR
MIN_SIZE = Constants.MIN_SIZE
APP_NAME = Constants.APP_NAME
PARAM_FILE = Constants.PARAM_FILE
VSRIP_TEMPLATE = Constants.VSRIP_TEMPLATE

logger = logging.getLogger(APP_NAME)


class Demux(object):

    def __init__(self, config):
        # self.series = args.series
        # self.episode = args.episode
        # self.no_sub = args.no_sub
        # self.no_video = args.no_vid
        # self.no_audio = args.no_aud
        # self.avs = args.avs
        # self.tmp_dir = tmp_dir
        # self.working_dir = config.get(APP_NAME, 'working_dir')
        # self.source_dir = config.get(APP_NAME, 'source_dir')
        self.pgcdemux = config.get(APP_NAME, 'pgcdemux')
        # self.vsrip = config.get(APP_NAME, 'vsrip')
        # self.disc_episodes = load_episode_disc_data(self.series,
        #                                             str(self.season),
        #                                             str(self.disc))
        # source_folder = os.path.join(self.source_dir,
        #                              self.series,
        #                              R1_DISC_DIR if not args.r2 else R2_DISC_DIR,
        #                              self._generate_source_folder_name(),
        #                              'VIDEO_TS')
        # logging.debug('Source folder: %s' % source_folder)
        # main_feature = self._detect_main_feature(source_folder)
        # self.source_file = os.path.join(source_folder, main_feature)
        # logger.debug('Series: %s, Season: %s, Disc: %s' % (self.series,
        #              self.season, self.disc))

    # def _run_pgcdemux(self, dest_path, vid, pgc=None):
    #     '''
    #     Run PGCdemux to demux video & audio
    #     '''
    #     logger.info('Demuxing %s to %s...' % (self.source_file, dest_path))

    #     streams = []
    #     if self.no_video:
    #         streams.extend(['-nom2v', '-nocellt'])
    #     else:
    #         streams.extend(['-m2v', '-cellt'])
    #     if self.no_audio:
    #         streams.append('-noaud')
    #     else:
    #         streams.append('-aud')
    #     streams.append('-nosub')

    #     if pgc:
    #         p = pgc['pgc']
    #         s = pgc['start']
    #         e = pgc['end']
    #         args = [self.pgcdemux, '-pgc', p] + streams + ['-nolog', '-guism', '-sc', s,'-ec', e, self.source_file, dest_path]
    #     else:
    #         args = [self.pgcdemux, '-vid', str(vid)] + streams + ['-nolog', '-guism', self.source_file, dest_path]

    #     proc = subprocess.run(args)

    #     logger.info('Audio/video demux complete.')

    def _run_vsrip(self, vid_seq, vid_dir):
        '''
        Run VSRip to extract DVD subtitles as VobSub
        '''
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
        subprocess.run([self.vsrip, param_file])
        logger.info('Subtitle demux complete.')

    # def _translate_folder_to_episode(self, folder):
    #     '''
    #     Figure out how to rename the video based on the folder name
    #     '''
    #     vid = folder
    #     # DB S1D2 is weird
    #     if (self.series == 'DB' and self.season == 1 and self.disc == 2):
    #         vid = (vid + 3) % 7
    #     # vid = folder.split('V')[1]
    #     # should actually use the demux index for this...
    #     episodes = list(
    #         range(self.disc_episodes[0], self.disc_episodes[1] + 1))
    #     return str(episodes[int(vid)]).zfill(3)

    def _clean_up_files(self, dest_path, tmp_dir):
        '''
        Go through the demuxed files and pick out what we want,
        delete the rest
        '''
        logger.info('Inspecting output...')
        final_dest = os.path.join(self.working_dir, self.series, R1_DEMUX_DIR)
        sub_dest = os.path.join(self.working_dir, self.series, FUNI_SUB_DIR)
        # make the directories
        create_dir(sub_dest)
        create_dir(final_dest)
        # keep track of loop iteration
        count = 0

        for d in os.listdir(tmp_dir):
            m2v = os.path.join(tmp_dir, d, 'VideoFile.m2v')
            aud0 = os.path.join(tmp_dir, d, 'AudioFile_80.ac3')
            aud1 = os.path.join(tmp_dir, d, 'AudioFile_81.ac3')
            chap = os.path.join(tmp_dir, d, 'Celltimes.txt')
            subi = os.path.join(tmp_dir, d, 'Subtitle.idx')
            subs = os.path.join(tmp_dir, d, 'Subtitle.sub')

            if os.path.isfile(m2v) or os.path.isfile(aud0) or os.path.isfile(subi):
                if os.path.isfile(m2v) and os.path.getsize(m2v) < MIN_SIZE:
                    logger.debug('Ripped something that\'s not an episode. '
                                 'Ignoring.')
                    continue

                ep_num = self._translate_folder_to_episode(count)
                logger.info('Ripped an episode.\t'
                            'Renaming to %s and moving...', ep_num)
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

                rename(aud0, aud0_n)
                rename(aud1, aud1_n)
                move_file(aud0_n, final_dest)
                if (self.series != 'DB'):
                    # only one audio track for DB
                    move_file(aud1_n, final_dest)
                if not self.no_video:
                    rename(m2v, m2v_n)
                    rename(chap, chap_n)
                    move_file(m2v_n, final_dest)
                    move_file(chap_n, final_dest)
                if not self.no_sub:
                    rename(subi, subi_n)
                    rename(subs, subs_n)
                    move_file(subi_n, sub_dest)
                    move_file(subs_n, sub_dest)
                count = count + 1
            else:
                logger.debug('%s does not exist', m2v)
        logger.info('Demux complete.\n'
                    'See demuxed A/V files in %s.\n'
                    'See demuxed subs in %s.', final_dest, sub_dest)

        delete_temp(tmp_dir)

    # def _detect_main_feature(self, source_folder):
    #     '''
    #     Detect which IFO has the most VOBs associated with it
    #     '''
    #     # look for VTS_XX_3.VOB
    #     files = os.listdir(source_folder)
    #     vob = [f for f in files if '_3.VOB' in f][0]
    #     ifo = vob.strip().split('_3.VOB')[0] + '_0.IFO'
    #     print("Season %s Disc %s VTS: %s" % (self.season, self.disc, ifo)) 
    #     return ifo

    # def season_set_demux(self):
    #     '''
    #     Demux from blue brick, orange brick, green brick
    #     '''
    #     dest_path = os.path.join(self.working_dir, self.series, R1_DEMUX_DIR)
    #     tmp_dir = tempfile.mkdtemp()
    #     # in the case of unexpected exit, we don't want to
    #     # keep temp files around
    #     atexit.register(delete_temp, tmp_dir)
    #     logging.debug('Temp folder: %s' % tmp_dir)
    #     demux_map = load_demux_map(self.series,
    #                                str(self.season))

    #     if self.series in ['DB', 'DBGT']:
    #         # demux all VIDS
    #         for vid in demux_map[str(self.disc)]:
    #             vid_dir = self._create_temp_dir(vid, tmp_dir)
    #             if not (self.no_video and self.no_audio):
    #                 self._run_pgcdemux(vid_dir, vid)
    #             if not(self.no_sub):
    #                 self._run_vsrip([vid], vid_dir)

    #     elif self.series == 'DBZ':
    #         no_of_eps = self.disc_episodes[1] - self.disc_episodes[0] + 1
    #         logger.debug('# of episodes: %s' % no_of_eps)
    #         for ep in range(0, no_of_eps):
    #             vid_dir = self._create_temp_dir(ep, tmp_dir)
    #             if self.season > 1:
    #                 # S2 and up follow a pattern
    #                 start_chap = demux_map['pgcdemux'][0] + (
    #                     ep * demux_map['pgcdemux'][1])
    #                 end_chap = demux_map['pgcdemux'][1] + (
    #                     ep * demux_map['pgcdemux'][1])
    #             else:
    #                 # DBZ season 1 is the only weird one
    #                 current_ep = str(self.disc_episodes[0] + ep).zfill(3)
    #                 start_chap = demux_map['pgcdemux'][current_ep][0]
    #                 end_chap = demux_map['pgcdemux'][current_ep][1]

    #             vsrip_vid_seq = map(lambda v: (v + 6 * ep),
    #                                 demux_map['vsrip'])
    #             logger.debug('VSRip vid sequence: %s', vsrip_vid_seq)
    #             # chapters based on season set PGC layout
    #             pgc = {'pgc': 1, 'start': start_chap, 'end': end_chap}
    #             if not (self.no_video and self.no_audio):
    #                 self._run_pgcdemux(vid_dir, 0, pgc=pgc)
    #             if not(self.no_sub):
    #                 self._run_vsrip(vsrip_vid_seq, vid_dir)
    #     # go through and delete dummy files and rename based on episode
    #     self._clean_up_files(dest_path, tmp_dir)
    #     # if avisynth is req'd, run DGIndex on all m2vs
    #     if self.avs:
    #         run_dgindex(dest_path, self.disc_episodes, self.series)

    def demux(self, config, args, tmp_dir):
        '''
        Demux video, audio, subs
        Return an object with the filenames
        '''
        src_dir_top = config.get(APP_NAME, 'source_dir')
        src_dir_series = os.path.join(src_dir_top, args.series)
        ep_str = str(args.episode).zfill(pad_zeroes(args.series))

        for r in ['R1', 'R2']:
            if r == 'R1':
                src_dir = os.path.join(src_dir_series, R1_DISC_DIR)
            elif r == 'R2':
                src_dir = os.path.join(src_dir_series, R2_DISC_DIR)
            dest_dir = os.path.join(tmp_dir, ep_str, r)
            ep_demux_map = load_demux_map(args.series, ep_str)[r]
            self.__run_pgcdemux(ep_demux_map, src_dir, dest_dir)

        return {'video': '',
                'audio': [],
                'subs': ''}

    def _parse_streams(self):
        pass

    def _run_pgcdemux(self, demux_map, src_dir, dest_dir):
        '''
        Detect arguments and run PGCdemux
        '''
        args = [self.pgcdemux, '-nolog', '-guism']

        # if self.no_video:
        args.extend(['-nom2v', '-nocellt'])
        # else:
        #     args.extend(['-m2v', '-cellt'])
        # if self.no_audio:
        #     args.append('-noaud')
        # else:
        args.append('-aud')
        args.append('-nosub')

        vts_ifo = os.path.join(
            src_dir,
            demux_map['disc'],
            'VIDEO_TS',
            ('VTS_0%d_0.IFO' % demux_map['vts'])
        )

        type_ = demux_map['type']
        cells = demux_map['cells']

        if type_ == 'vid':
            args.extend(['-vid', str(demux_map['vid'])])
        if type_ == 'pgc':
            args.extend(['-pgc', str(demux_map['pgc'])])
            if cells:
                args.extend(['-sc', str(cells[0]), '-ec', str(cells[1])])
        args.extend([vts_ifo, dest_dir])
        print(args)
        # proc = subprocess.run(args)
