import os
import sys

VERSION = '1.1.1'
CODENAME = 'Gogeta'

if hasattr(sys, 'frozen') and sys.frozen in ('windows_exe', 'console_exe'):
    _file = os.path.abspath(sys.argv[0])
    PACKAGE_PATH = os.path.dirname(_file)
else:
    PACKAGE_PATH = os.path.dirname(os.path.realpath(__file__))
PARAMS_PATH = os.path.join(PACKAGE_PATH, 'params')
DEMUX_JSON = os.path.join(PARAMS_PATH, 'demux.json')
DISC_JSON = os.path.join(PARAMS_PATH, 'episodes.json')
OFFSETS_JSON = os.path.join(PARAMS_PATH, 'offsets.json')
VALID_JSON = os.path.join(PARAMS_PATH, 'valid.json')
TITLE_TIMES_JSON = os.path.join(PARAMS_PATH, 'title-times.json')
TITLES_JSON = os.path.join(PARAMS_PATH, 'titles.json')
CONF_FILE = os.path.join(PACKAGE_PATH, 'dragon-radar.ini')
AC3_DIR = os.path.join(PACKAGE_PATH, 'ac3files')
LOG_FILE = os.path.join(PACKAGE_PATH, 'dragon-radar.log')
AUTODETECT_JSON = os.path.join(PARAMS_PATH, '.autodetect.json')
APP_NAME = 'dragon-radar'
VSRIP_TEMPLATE = ('{in_path}\n'
                  '{out_path}\n'
                  '{pgc}\n'
                  '{vid_sequence}\n'
                  'ALL\n'
                  'CLOSE\n'
                  'RESETTIME\n')
PARAM_FILE = 'param.lst'
WELCOME_MSG = ('----------------------------\n' +
               '\033[93mDragon' + '\033[39m ' +
               '\033[91mRadar' + '\033[39m' + ' v' + VERSION +
               ' \"' + CODENAME + '\"' +
               '\n----------------------------')
MIN_SIZE = 100000000
FRAME_RATE = float(30000) / float(1001)

if __name__ == '__main__':
    print(VERSION)
