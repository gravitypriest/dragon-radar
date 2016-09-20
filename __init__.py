'''
Dragon Radar -- create MKVs from R2 video and R1 audio/subs
'''
import os
import sys
import argparse
import configparser
import tempfile
import logging
import atexit
from constants import Constants
import colorama
from episode import Episode
from utils import (get_op_offset,
                   pad_zeroes,
                   load_validate,
                   delete_temp)
from subtitle import detect_streams
WELCOME_MSG = Constants.WELCOME_MSG
WORKING_DIR = Constants.WORKING_DIR
SOURCE_DIR = Constants.SOURCE_DIR
CONF_FILE = Constants.CONF_FILE
APP_NAME = Constants.APP_NAME
logger = logging.getLogger(APP_NAME)


def load_config_file():
    '''
    Load config from dragon-radar.ini
    '''
    config = configparser.ConfigParser(
        {'working_dir': WORKING_DIR,
         'source_dir': SOURCE_DIR})
    try:
        config.read(CONF_FILE)
    except configparser.Error:
        pass
    try:
        config.add_section(APP_NAME)
    except configparser.Error:
        pass

    return config


def create_args():
    '''
    Set up command line options
    '''
    parser = argparse.ArgumentParser(description='Create multiplexed Dragon '
                                                 'Ball MKVs with Dragon Box '
                                                 'video, and English audio '
                                                 'and subtitles.')

    parser.add_argument('--series',
                        metavar='<series>',
                        help='Choose a series [DB, DBZ, DBGT, DBM]',
                        required=True)
    parser.add_argument('--episode',
                        metavar='<number>',
                        help='Episode to process. '
                             'Can also be used with a range, i.e. '
                             '--episode <first>:<last>',
                        required=True)
    parser.add_argument('--verbose',
                        action='store_true',
                        default=False,
                        help='More descriptive output')
    # for Z, get R1 assets from Dragon Box
    parser.add_argument('--r1-dbox',
                        action='store_true',
                        default=False,
                        help='For DBZ, use the audio and subtitle assets'
                             'from the Funimation Dragon Box')
    # the first 3 Z movies, get R1 assets from Pioneer DVDs
    parser.add_argument('--pioneer',
                        action='store_true',
                        default=False,
                        help='For the first 3 DBZ movies, use the audio and'
                             'subtitle assets from the Pioneer DVDs.')
    # don't use Funimation Remastered DVDs for the first 3 movies
    parser.add_argument('--no-funi',
                        action='store_true',
                        default=False,
                        help='Use in conjunction with --pioneer to ignore'
                             'assets from the Funimation remastered DVDs.')
    # shh, hidden options for debug use only
    # skip demux
    parser.add_argument('--no-demux',
                        action='store_true',
                        default=False,
                        help=argparse.SUPPRESS)
    # save demuxed files to destination directory
    parser.add_argument('--no-mux',
                        action='store_true',
                        default=False,
                        help=argparse.SUPPRESS)
    # skip retiming
    parser.add_argument('--no-retime',
                        action='store_true',
                        default=False,
                        help=argparse.SUPPRESS)
    # only demux subtitles
    parser.add_argument('--sub-only',
                        action='store_true',
                        default=False,
                        help=argparse.SUPPRESS)
    # create AVIsynth after demux
    parser.add_argument('--make-avs',
                        action='store_true',
                        default=False,
                        help=argparse.SUPPRESS)
    # demux r1 video in addition to audio/subs
    parser.add_argument('--r1-vid',
                        action='store_true',
                        default=False,
                        help=argparse.SUPPRESS)

    return parser


def init_logging(verbose):
    level = logging.INFO
    if verbose:
        level = logging.DEBUG
    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setLevel(level)
    logging.root.addHandler(stdout_handler)
    logger.setLevel(level)


def pre_check(args, config):
    '''
    Make sure directories are correct
    and required programs are installed
    '''
    def exe_check(name):
        try:
            exe = config.get(APP_NAME, name.lower())
        except configparser.Error:
            logger.error('Path to %s is not defined in dragon-radar.ini', name)
            return True
        logger.debug('%s path: %s', name, exe)
        if not os.path.isfile(exe):
            logger.error('Path to %s \"%s\" is invalid.', name, exe)
            return True
        return False

    logger.debug('Performing pre-check...')
    bad_conf = False
    bad_conf = exe_check('PGCDemux')
    bad_conf = exe_check('VSRip')
    bad_conf = exe_check('DelayCut')
    if args.make_avs:
        bad_conf = exe_check('DGIndex')
    if bad_conf:
        sys.exit(1)
    else:
        logger.debug('Pre-check finished.')


def bad_arg_exit(arg):
    logger.error('Bad argument for --%s' % arg)
    sys.exit(1)


def validate_args(argtype, arg, series):
    valid = load_validate(series)
    if not all((a - 1) in range(valid[argtype]) for a in arg):
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
    colorama.init()
    print(WELCOME_MSG)
    config = load_config_file()
    args = create_args().parse_args()
    init_logging(args.verbose)

    # don't proceed if paths aren't right/programs missing
    pre_check(args, config)

    tmp_dir = tempfile.mkdtemp()
    logger.debug('Episode temp folder: %s', tmp_dir)
    atexit.register(delete_temp, tmp_dir)

    start, end = split_args('episode', args.episode)

    for ep in range(start, end + 1):
        episode = Episode(ep, config, args, tmp_dir)

        if not args.no_demux:
            episode.demux()
        else:
            if args.sub_only:
                detect_streams(os.path.join(config.get(APP_NAME, 'output_dir'),
                               args.series,
                               str(ep).zfill(3), 'R1', 'Subtitle.idx'))
        if not args.no_retime:
            episode.retime_subs()
            episode.retime_audio()
        if not args.no_demux and args.no_mux:
            # move files to destination folder
            episode.move_demuxed_files()
        else:
            # retime subs & audio
            episode.make_mkv()

        if args.make_avs:
            # only works on files generated with --no-mux
            episode.make_avs()

        delete_temp(episode.temp_dir)

if __name__ == "__main__":
    main()
