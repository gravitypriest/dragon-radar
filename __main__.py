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
import colorama
import time
import constants
from episode import Episode
from utils import (get_op_offset,
                   pad_zeroes,
                   load_validate,
                   delete_temp,
                   create_dir)
from subtitle import detect_streams
WELCOME_MSG = constants.WELCOME_MSG
CONF_FILE = constants.CONF_FILE
APP_NAME = constants.APP_NAME
LOG_FILE = constants.LOG_FILE
logger = logging.getLogger(APP_NAME)


def load_config_file():
    '''
    Load config from dragon-radar.ini
    '''
    config = configparser.ConfigParser()
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
                        help='Choose a series [DB, DBZ, DBGT]',
                        required=True)
    episode_group = parser.add_mutually_exclusive_group(required=True)
    episode_group.add_argument('--episode',
                               metavar='<number>',
                               help='Episode to process. '
                                    'Can also be used with a range, i.e. '
                                    '--episode <first>:<last>')
    episode_group.add_argument('--movie',
                               metavar='<number>',
                               help='Movie to process. '
                                    'Can also be used with a range, i.e. '
                                    '--movie <first>:<last>')
    parser.add_argument('--verbose',
                        action='store_true',
                        default=False,
                        help='More descriptive output')
    # for Z, get R1 assets from Dragon Box
    parser.add_argument('--r1-dbox',
                        action='store_true',
                        default=False,
                        help='For DBZ, use the audio and subtitle assets '
                             'from the Funimation Dragon Box')
    # the first 3 Z movies, get R1 assets from Pioneer DVDs
    parser.add_argument('--pioneer',
                        action='store_true',
                        default=False,
                        help='For the first 3 DBZ movies, use the audio and '
                             'subtitle assets from the Pioneer DVDs.')
    # don't use Funimation Remastered DVDs for the first 3 movies
    parser.add_argument('--no-funi',
                        action='store_true',
                        default=False,
                        help='Use in conjunction with --pioneer to ignore '
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
    logger.setLevel(logging.DEBUG)

    stdout_handler = logging.StreamHandler()
    stdout_handler.setLevel(level)

    file_handler = logging.FileHandler(LOG_FILE, mode='w')
    file_handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
    file_handler.setFormatter(formatter)

    logger.addHandler(stdout_handler)
    logger.addHandler(file_handler)


def pre_check(args, config):
    '''
    Make sure directories are correct
    and required programs are installed
    '''
    def exe_check(name, isfile=False):
        try:
            path = config.get(APP_NAME, name.lower())
        except configparser.Error:
            logger.error('Path to %s is not defined in dragon-radar.ini', name)
            return True
        logger.debug('%s path: %s', name, path)
        if isfile and not os.path.isfile(path):
            logger.error('Path to %s \"%s\" is invalid.', name, path)
            return True
        return False

    logger.debug('Performing pre-check...')
    bad_conf = False
    bad_conf = bad_conf or exe_check('PGCDemux', True)
    bad_conf = bad_conf or exe_check('VSRip', True)
    bad_conf = bad_conf or exe_check('DelayCut', True)
    bad_conf = bad_conf or exe_check('ReStream', True)
    bad_conf = bad_conf or exe_check('source_dir')
    bad_conf = bad_conf or exe_check('output_dir')
    if (args.series == 'DB' and args.episode in [26, 41] or
       args.series == 'DBZ' and args.episode == 24 or
       args.make_avs):
        # complex demux or avs generation, DGIndex required
        bad_conf = bad_conf or exe_check('DGIndex', True)
    if not args.no_mux:
        bad_conf = bad_conf or exe_check('mkvmerge', True)
    if bad_conf:
        sys.exit(1)
    else:
        logger.debug('Pre-check finished.')


def bad_arg_exit(arg):
    logger.error('Bad argument for --%s', arg)
    sys.exit(1)


def bad_combos(args):
    msg = 'Bad combination: '
    for a in args:
        msg += '--' + a + ' '
        if args.index(a) < len(args) - 1:
            msg += ', '
    logger.error(msg)
    sys.exit(1)


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
        logger.debug('No end %s specified.', argtype)
        end = start
    return start, end


def validate_args(args):
    '''
    Validate all arguments
    '''
    # series/episode checks
    start = 0
    end = 0
    special = None
    if args.series not in ['DB', 'DBZ', 'DBGT']:
        bad_arg_exit('series')
    valid = load_validate(args.series)
    if args.episode:
        argtype = 'episode'
        if args.series == 'DBZ':
            if args.episode in ['bardock', 'trunks']:
                special = args.episode
            elif 'bardock' in args.episode or 'trunks' in args.episode:
                logger.error('Please run --episode bardock or '
                             '--episode trunks on their own.')
                sys.exit(1)
        if args.series == 'DBGT':
            if args.episode == 'special':
                special = args.episode
            elif 'special' in args.episode:
                logger.error('Please run --episode special on its own.')
                sys.exit(1)
        if not special:
            start, end = split_args('episode', args.episode)
    elif args.movie:
        argtype = 'movie'
        start, end = split_args('movie', args.movie)
    if not special and not all((a - 1) in range(
            valid[argtype]) for a in (start, end)):
        bad_arg_exit(argtype)
    # contradictory arguments
    if args.r1_dbox and args.series != 'DBZ':
        logger.error('--r1-dbox can only be used with --series DBZ')
        sys.exit(1)
    if args.movie and args.r1_dbox:
        logger.error('Bad combination --movie and --r1-dbox')
        sys.exit(1)
    if not args.movie and args.pioneer:
        logger.error('--pioneer can only be used with --movie')
        sys.exit(1)
    if not args.pioneer and args.no_funi:
        logger.error('--no-funi can only be used with --pioneer')
        sys.exit(1)

    return start, end, special


def main():
    colorama.init()

    config = load_config_file()
    args, wtf = create_args().parse_known_args()
    if (wtf):
        logger.error('Unknown argument %s', wtf[0])
        sys.exit(1)
    init_logging(args.verbose)

    # don't proceed if paths aren't right/programs missing
    pre_check(args, config)

    try:
        working_dir = config.get(APP_NAME, 'working_dir')
    except configparser.Error:
        working_dir = None

    if working_dir:
        if not os.path.isdir(working_dir):
            create_dir(working_dir)
        tempfile.tempdir = working_dir

    tmp_dir = tempfile.mkdtemp()
    logger.debug('Episode temp folder: %s', tmp_dir)
    atexit.register(delete_temp, tmp_dir)

    start, end, special = validate_args(args)
    print(WELCOME_MSG)

    for ep in range(start, end + 1):
        start_time = time.clock()
        episode = Episode(ep, config, args, tmp_dir, special)

        if not args.no_demux:
            episode.demux()
        else:
            if args.sub_only:
                detect_streams(os.path.join(config.get(APP_NAME, 'output_dir'),
                               args.series,
                               str(ep if not special else special).zfill(3),
                               'R1', 'Subtitle.idx'))
        if not args.no_retime:
            episode.retime_subs()
            episode.retime_audio()
        if not args.no_demux and args.no_mux:
            # move files to destination folder
            episode.move_demuxed_files()
        if not args.no_mux:
            episode.mux()

        if args.make_avs:
            # only works on files generated with --no-mux
            episode.make_avs()

        delete_temp(episode.temp_dir)
        elapsed = time.clock() - start_time
        logger.debug('Elapsed time: %s seconds', elapsed)
    logger.info('Finished!')

if __name__ == "__main__":
    try:
        main()
    except EOFError:
        # cancel the input in the input prompt
        logger.error('Aborting.')
        sys.exit(1)
    except KeyboardInterrupt:
        logger.error('Aborting.')
        sys.exit(1)
