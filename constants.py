import os


class Constants(object):
    PACKAGE_DIR = os.path.dirname(os.path.abspath(__file__))
    DEMUX_JSON = os.path.join(PACKAGE_DIR, 'demux.json')
    DISC_JSON = os.path.join(PACKAGE_DIR, 'episodes.json')
    OFFSETS_JSON = os.path.join(PACKAGE_DIR, 'offsets.json')
    CONF_FILE = os.path.join(PACKAGE_DIR, 'dragon-radar.conf')
    WORKING_DIR = 'C:/dragon-radar'
    SOURCE_DIR = WORKING_DIR
    FUNI_SUB_DIR = 'Funi VobSubs'
    RETIMED_SUB_DIR = 'Retimed VobSubs'
    R1_DEMUX_DIR = 'R1 Demux'
    R2_DEMUX_DIR = 'R2 Demux'
    R1_DISC_DIR = 'R1 Discs'
    R2_DISC_DIR = 'R2 Discs'
    AVS_DIR = 'AVS Scripts'
    APP_NAME = 'dragon-radar'
    PGCDEMUX = 'C:\PGCDemux'
    VSRIP = 'C:\VSrip'
    DELAYCUT = 'C:\Delaycut'
    VSRIP_TEMPLATE = ('{in_path}\n'
                      '{out_path}\n'
                      '1\n'
                      '{vid_sequence}\n'
                      'ALL\n'
                      'CLOSE\n'
                      'RESETTIME\n')
    PARAM_FILE = 'param.lst'
    WELCOME_MSG = '''
       8888888b. 8888888b.        d8888 .d8888b.  .d88888b. 888b    888
       888  \"Y88b888   Y88b      d88888d88P  Y88bd88P\" \"Y88b8888b   888
       888    888888    888     d88P888888    888888     88888888b  888
       888    888888   d88P    d88P 888888       888     888888Y88b 888
       888    8888888888P\"    d88P  888888  88888888     888888 Y88b888
       888    888888 T88b    d88P   888888    888888     888888  Y88888
       888  .d88P888  T88b  d8888888888Y88b  d88PY88b. .d88P888   Y8888
       8888888P\" 888   T88bd88P     888 \"Y8888P88 \"Y88888P\" 888    Y888
            8888888b.        d88888888888b.        d88888888888b.
            888   Y88b      d88888888  \"Y88b      d88888888   Y88b
            888    888     d88P888888    888     d88P888888    888
            888   d88P    d88P 888888    888    d88P 888888   d88P
            8888888P\"    d88P  888888    888   d88P  8888888888P\"
            888 T88b    d88P   888888    888  d88P   888888 T88b
            888  T88b  d8888888888888  .d88P d8888888888888  T88b
            888   T88bd88P     8888888888P\" d88P     888888   T88b
    '''
    MIN_SIZE = 100000000
