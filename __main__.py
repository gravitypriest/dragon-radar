'''
Dragon Radar
'''
import argparse
import ConfigParser
import subtitle
from constants import Constants
from episode import Episode
from demux import Demux
from utils import load_series_frame_data, get_op_offset, pad_zeroes


def load_config_file():
    '''
    Load config from dragon-radar.conf
    '''
    config = ConfigParser.RawConfigParser(
        {'working_dir': Constants.WORKING_DIR,
         'source_dir': Constants.SOURCE_DIR,
         'pgcdemux': Constants.PGCDEMUX})
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
                           metavar='<season>',
                           type=int,
                           help='Which season/box to demux',
                           required=True)
    demux_cmd.add_argument('--disc',
                           metavar='<disc>',
                           type=int,
                           help='Which disc to demux',
                           required=True)
    demux_cmd.add_argument('--video',
                           action='store_true',
                           help='Demux video in addition to audio')
    group = demux_cmd.add_mutually_exclusive_group()
    group.add_argument('--r1',
                       action='store_true',
                       default=True,
                       help='Demux the R1 DVD (default)')
    group.add_argument('--r2',
                       action='store_true',
                       default=False,
                       help='Demux the R2 DVD')

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
            cmd.add_argument('--start',
                             metavar='<first>',
                             type=int,
                             help='The first episode to process')
            cmd.add_argument('--end',
                             metavar='<last>',
                             type=int,
                             help='The last episode to process')

    return parser


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


def subtitle_mode():
    pass


def demux_mode():
    pass


def audio_mode():
    pass


def main():
    config = load_config_file()
    args = create_args().parse_args()

    if args.command == 'demux':
        # demux mode
        demux = Demux(config, args.series, args.season, args.disc)
        if args.r1:
            if series in ['DB', 'DBZ', 'DBGT']:
                demux.season_set_demux()
            if series in ['DBoxZ']:
                demux.dbox_demux()
        if args.r2:
            demux.r2_demux()
    elif args.command == 'subtitle':
        # subtitle mode
        pass
    elif args.command == 'audio':
        # audio mode
        pass
    elif args.command == 'avisynth':
        # avisynth mode
        pass
    elif args.command == 'bluray':
        # blu-ray author mode
        pass
    # series_frame_data = load_series_frame_data(args.series)

    # for ep in xrange(args.start, args.end + 1):
    #     # create episode object
    #     episode = Episode(ep, args.series, series_frame_data)

    #     # subtitle mode
    #     if args.sub:
    #         subtitle.retime_vobsub(episode, config)


if __name__ == "__main__":
    main()
