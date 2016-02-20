'''
Dragon Radar
'''
import argparse
from utils import load_series_frame_data, get_op_offset


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
    series_frame_data = load_series_frame_data(args.series)
    op_offset = get_op_offset(args.series, '1', series_frame_data)

if __name__ == "__main__":
    main()
