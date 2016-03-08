'''
Dragon Radar
'''
import os
import sys
import argparse
import ConfigParser
import logging
from constants import Constants
from episode import Episode
from demux import Demux
from avisynth import write_avs_file
from subtitle import retime_vobsub
from audio import retime_audio
from utils import (load_series_frame_data,
                   get_op_offset,
                   pad_zeroes,
                   load_validate)

WELCOME_MSG = Constants.WELCOME_MSG
WORKING_DIR = Constants.WORKING_DIR
SOURCE_DIR = Constants.SOURCE_DIR
PGCDEMUX = Constants.PGCDEMUX
VSRIP = Constants.VSRIP
DELAYCUT = Constants.DELAYCUT
CONF_FILE = Constants.CONF_FILE
APP_NAME = Constants.APP_NAME


def load_config_file():
    '''
    Load config from dragon-radar.conf
    '''
    config = ConfigParser.RawConfigParser(
        {'working_dir': WORKING_DIR,
         'source_dir': SOURCE_DIR,
         'pgcdemux': PGCDEMUX,
         'vsrip': VSRIP,
         'delaycut': DELAYCUT})
    try:
        config.read(CONF_FILE)
    except ConfigParser.Error:
        pass
    try:
        config.add_section(APP_NAME)
    except ConfigParser.Error:
        pass
    # normalize paths
    for c in config.keys():
        config[c] = os.path.normpath(config[c])
    return config


def create_args():
    '''
    Set up command line options
    '''
    parser = argparse.ArgumentParser(description='Generate English subtitles '
                                                 'or audio for the R2 Dragon '
                                                 'Ball DVDs from an R1 '
                                                 'source.')

    subparser = parser.add_subparsers(dest='command',
                                      help='Run Dragon Radar '
                                           'with one of these commands:')

    # the demux command
    demux_cmd = subparser.add_parser('demux',
                                     help='Demux audio from a DVD '
                                          'VIDEO_TS folder')
    demux_cmd.add_argument('--season',
                           metavar='<first>:<last>',
                           help='Which season(s)/box(es) to demux, '
                                'from first to last',
                           required=True)
    demux_cmd.add_argument('--disc',
                           metavar='<first>:<last>',
                           help='Which disc(s) to demux, from first to last',
                           required=True)

    vid_group = demux_cmd.add_mutually_exclusive_group()
    vid_group.add_argument('--vid',
                           action='store_true',
                           default=True,
                           help='Demux video (default)')
    vid_group.add_argument('--no-vid',
                           action='store_true',
                           default=False,
                           help='Don\'t demux video')

    aud_group = demux_cmd.add_mutually_exclusive_group()
    aud_group.add_argument('--aud',
                           action='store_true',
                           default=True,
                           help='Demux audio (default)')
    aud_group.add_argument('--no-aud',
                           action='store_true',
                           default=False,
                           help='Don\'t demux audio')
    sub_group = demux_cmd.add_mutually_exclusive_group()

    demux_cmd.add_argument('--sub',
                           action='store_true',
                           default=True,
                           help='Demux subtitles (default)')
    demux_cmd.add_argument('--no-sub',
                           action='store_true',
                           default=False,
                           help='Do not demux subtitles')
    demux_cmd.add_argument('--avs',
                           action='store_true',
                           default=False,
                           help='Generate .d2v file')

    group = demux_cmd.add_mutually_exclusive_group()
    group.add_argument('--r1',
                       action='store_true',
                       default=True,
                       help='Demux the audio/video from R1 DVD (default)')
    group.add_argument('--r2',
                       action='store_true',
                       default=False,
                       help='Demux the audio/video from R2 DVD')

    # process subtitles
    subtitle_cmd = subparser.add_parser('subtitle',
                                        help='Sync an R1 VobSub subtitle file '
                                             'to the R2 Dragon Box')

    # process audio
    audio_cmd = subparser.add_parser('audio',
                                     help='Sync an R1 English AC3 audio file '
                                          'to the R2 Dragon Box')

    avisynth_cmd = subparser.add_parser('avisynth',
                                        help='Generate an AVS script for '
                                             'side-by-side R1 vs R2 '
                                             'comparison')

    # add these args this way because help message looks fucky otherwise
    for cmd in [demux_cmd, subtitle_cmd, audio_cmd, avisynth_cmd]:
        cmd.add_argument('--series',
                         metavar='<series>',
                         help='Choose a series [DB, DBZ, DBoxZ, DBGT, DBM]',
                         required=True)
        if cmd is not demux_cmd:
            cmd.add_argument('--episode',
                             metavar='<first>:<last>',
                             help='Episodes to process, from first to last',
                             required=True)
        cmd.add_argument('--verbose',
                         action='store_true',
                         default=False,
                         help='More descriptive output')

    return parser


def init_logging(verbose):
    level = logging.INFO
    if verbose:
        level = logging.DEBUG
    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setLevel(level)
    logging.root.addHandler(stdout_handler)
    logger = logging.getLogger(APP_NAME)
    logger.setLevel(level)
    return logger


def pre_check(args, config):
    '''
    Make sure directories are correct
    and required programs are installed
    '''
    def dgdecode_check():
        dgdecode = config.get(APP_NAME, 'dgdecode')
        logger.debug('DGDecode path: %s' % dgdecode)
        if not os.path.isfile(dgdecode):
            logger.error('Path to DGDecode \"%s\" is invalid.' % dgdecode)
            return True
        return False

    logger.debug('Performing pre-check...')
    bad_conf = False
    if args.command is 'demux':
        if not (args.no_vid and args.no_aud):
            pgcdemux = config.get(APP_NAME, 'pgcdemux')
            logger.debug('PGCDemux path: %s' % pgcdemux)
            if not os.path.isfile(pgcdemux):
                logger.error('Path to PGCDemux \"%s\" is invalid.' % pgcdemux)
                bad_conf = True
        if not args.no_sub:
            vsrip = config.get(APP_NAME, 'vsrip')
            logger.debug('VSRip path: %s' % vsrip)
            if not os.path.isfile(vsrip):
                logger.error('Path to VSRip \"%s\" is invalid.' % vsrip)
                bad_conf = True
        if args.avs:
            bad_conf = dgdecode_check()
    if args.command is 'avisynth':
        bad_conf = dgdecode_check()
    if args.command is 'audio':
        pass
    if bad_conf:
        sys.exit(1)
    else:
        logger.debug('Pre-check finished.')


def bad_arg_exit(arg):
    logger.error('Bad argument for --%s' % arg)
    sys.exit(1)


def validate_args(argtype, arg, series):
    valid = load_validate(series)
    if not all((a - 1) in xrange(valid[argtype]) for a in arg):
        bad_arg_exit(argtype)


def split_args(argtype, arg):
    '''
    Split argument into start/end
    '''
    spread = arg.split(':', 1)
    try:
        start = int(spread[0])
        end = int(spread[1])
    except ValueError:
        bad_arg_exit(argtype)
    except IndexError:
        logger.debug('No end %s specified.' % argtype)
        end = start
    return start, end


def main():
    global logger
    config = load_config_file()
    args = create_args().parse_args()
    logger = init_logging(args.verbose)

    # don't proceed if paths aren't right/programs missing
    pre_check(args, config)

    print WELCOME_MSG

    if args.command == 'demux' and not (args.no_vid and args.no_aud and
                                        args.no_sub):
        # demux mode
        start_season, end_season = split_args('season', args.season)
        validate_args('season', [start_season, end_season], args.series)
        start_disc, end_disc = split_args('disc', args.disc)
        validate_args('disc', [start_disc, end_disc], args.series)

        for season in xrange(start_season, end_season + 1):
            for disc in xrange(start_disc, end_disc + 1):
                logger.info('Launching demux mode for %s season %s disc %s...'
                            % (args.series, season, disc))
                demux = Demux(config, args, season, disc)
                if args.r1:
                    if args.series in ['DB', 'DBZ', 'DBGT']:
                        demux.season_set_demux()
                    if args.series in ['DBoxZ']:
                        demux.dbox_demux()
                if args.r2:
                    demux.r2_demux()

    elif args.command in ['subtitle', 'audio', 'avisynth']:
        # per-episode modes
        start_ep, end_ep = split_args('episode', args.episode)

        for ep in xrange(start_ep, end_ep + 1):
            episode = Episode(ep, args.series)
            if args.command == 'avisynth':
                # avisynth mode
                write_avs_file(episode, config)
            if args.command == 'subtitle':
                # subtitle mode
                retime_vobsub(episode, config)
            elif args.command == 'audio':
                # audio mode
                retime_audio(episode, config)


if __name__ == "__main__":
    main()
