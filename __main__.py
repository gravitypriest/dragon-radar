'''
Dragon Radar
'''
import sys
import argparse
import ConfigParser
import logging
import subtitle
from constants import Constants
from episode import Episode
from demux import Demux
from utils import load_series_frame_data, get_op_offset, pad_zeroes

logger = None


def load_config_file():
    '''
    Load config from dragon-radar.conf
    '''
    config = ConfigParser.RawConfigParser(
        {'working_dir': Constants.WORKING_DIR,
         'source_dir': Constants.SOURCE_DIR,
         'pgcdemux': Constants.PGCDEMUX,
         'vsrip': Constants.VSRIP})
    try:
        config.read(Constants.CONF_FILE)
    except ConfigParser.Error:
        pass
    try:
        config.add_section(Constants.APP_NAME)
    except ConfigParser.Error:
        pass
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
                           help='Which disc to demux',
                           required=True)
    demux_cmd.add_argument('--video',
                           action='store_true',
                           help='Demux video in addition to audio')
    demux_cmd.add_argument('--subtitle',
                           action='store_true',
                           default=False,
                           help='Demux only subtitles')
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

    # add these args this way because help message looks fucky otherwise
    for cmd in [demux_cmd, subtitle_cmd, audio_cmd]:
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
    logger = logging.getLogger(Constants.APP_NAME)
    logger.setLevel(level)
    return logger


def pre_check():
    '''
    Make sure directories are correct
    and required programs are installed
    '''
    pass


def initial_setup():
    '''
    Create working directory structure
    '''
    pass


def split_args(argtype, arg):
    '''
    Split argument into start/end
    '''
    spread = arg.split(':', 1)
    try:
        start = int(spread[0])
        end = int(spread[1])
    except ValueError:
        logger.error('Bad argument for --%s' % argtype)
        sys.exit(1)
    except IndexError:
        logger.debug('No end %s specified.' % argtype)
        end = start
    return start, end


def main():
    print Constants.WELCOME_MSG
    global logger
    config = load_config_file()
    args = create_args().parse_args()
    logger = init_logging(args.verbose)

    if args.command == 'demux':
        # demux mode
        start_season, end_season = split_args('season', args.season)
        start_disc, end_disc = split_args('disc', args.disc)

        for season in xrange(start_season, end_season + 1):
            for disc in xrange(start_disc, end_disc + 1):
                logger.info('Launching demux mode for %s season %s  disc %s...'
                            % (args.series, season, disc))
                demux = Demux(config, args.series, season, disc, args.subtitle)
                if args.r1:
                    if args.series in ['DB', 'DBZ', 'DBGT']:
                        demux.season_set_demux()
                    if args.series in ['DBoxZ']:
                        demux.dbox_demux()
                if args.r2:
                    demux.r2_demux()
                # if args.subtitle:
                #     demux.subtitle_demux()

    elif args.command in ['subtitle', 'audio']:
        # per-episode modes
        series_frame_data = load_series_frame_data(args.series)
        start_ep, end_ep = split_args('episode', args.episode)

        for ep in xrange(start_ep, end_ep + 1):
            episode = Episode(ep, args.series, series_frame_data)
            if args.command == 'subtitle':
                # subtitle mode
                subtitle.retime_vobsub(episode, config)
            elif args.command == 'audio':
                # audio mode
                pass


if __name__ == "__main__":
    main()
