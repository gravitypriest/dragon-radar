'''
Dragon Radar
'''
import argparse
import ConfigParser
import subtitle
from constants import Constants
from episode import Episode
from utils import load_series_frame_data, get_op_offset, pad_zeroes


def load_config_file():
    '''
    Load config from dragon-radar.conf
    '''
    config = ConfigParser.RawConfigParser(
        {'working_dir': Constants.WORKING_DIR})
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
    parser = argparse.ArgumentParser(description='Generate English subtitles '
                                                 'or audio for the R2 Dragon '
                                                 'Ball DVDs from an R1 '
                                                 'source.',
                                     epilog='Example: DragonRadar.py'
                                            '-series DBZ -start 55 '
                                            '-end 80 --aud')
    parser.add_argument('--series',
                        metavar='<series>',
                        help='Choose a series [DB, DBZ, DBGT, DBM]',
                        required=True)
    parser.add_argument('--start',
                        metavar='<first>',
                        type=int,
                        help='The first episode to process',
                        required=True)
    parser.add_argument('--end',
                        metavar='<last>',
                        type=int,
                        help='The last episode to process',
                        required=True)
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--sub',
                       action='store_true',
                       help='Process subtitles')
    group.add_argument('--aud',
                       action='store_true',
                       help='Process audio')
    return parser


def main():
    args = create_args().parse_args()
    config = load_config_file()
    series_frame_data = load_series_frame_data(args.series)

    for ep in xrange(args.start, args.end + 1):

        # create episode object
        episode = Episode(ep, args.series, series_frame_data)

        # subtitle mode
        if args.sub:
            subtitle.retime_vobsub(episode, config)


if __name__ == "__main__":
    main()
