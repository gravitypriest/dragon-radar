import os

class Constants(object):
    VERSION = '0.1'
    DEMUX_JSON = 'params/demux.json'
    DISC_JSON = 'params/episodes.json'
    OFFSETS_JSON = 'params/offsets.json'
    VALID_JSON = 'params/valid.json'
    CONF_FILE = 'dragon-radar.ini'
    AC3_DIR = 'ac3files'
    WORKING_DIR = 'C:/dragon-radar'
    SOURCE_DIR = WORKING_DIR
    APP_NAME = 'dragon-radar'
    VSRIP_TEMPLATE = ('{in_path}\n'
                      '{out_path}\n'
                      '{pgc}\n'
                      '{vid_sequence}\n'
                      'ALL\n'
                      'CLOSE\n'
                      'RESETTIME\n')
    PARAM_FILE = 'param.lst'
    WELCOME_MSG = ('-----------------\n' +
                   '\033[93mDragon' + '\033[39m ' +
                   '\033[91mRadar v{0}'.format(VERSION) + '\033[39m' +
                   '\n-----------------')
    MIN_SIZE = 100000000
    FRAME_RATE = float(30000) / float(1001)
