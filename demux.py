'''
Functions to demux discs
'''
import subprocess


def _run_dgdecode(video):
    pass


def _run_pgcdemux():
    pass


def _detect_main_feature(series, season, disc):
    '''
    Detect which IFO has the most VOBs associated with it
    '''
    # look for VTS_XX_3.VOB
    files = os.listdir('.')
    vob = [f for f in files if '_3.VOB' in f][0]
    ifo = vob.strip().split('_3.VOB')[0] + '_0.IFO'

    return ifo


def demux_video_audio(series, start_season, end_season, start_disc, end_disc):
    '''
    Demux video and audio from the VIDEO_TS folders
    '''
    for season in xrange(start_season, end_season + 1):
        for disc in xrange(start_disc, end_disc + 1):
            main_feature = _detect_main_feature(series, season, disc)

            for vid in xrange(1, 100):
                # demux all VIDs
                # go through and delete dummy files and rename based on episode
                # run DGDecode on all m2vs
                pass


def demux_subtitles():
    '''
    Use VSRip to pull out the subtitles
    '''
    pass
