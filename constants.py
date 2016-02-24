import os


class Constants(object):
    PACKAGE_DIR = os.path.dirname(os.path.abspath(__file__))
    DEMUX_JSON = os.path.join(PACKAGE_DIR, 'demux.json')
    DISC_JSON = os.path.join(PACKAGE_DIR, 'episodes.json')
    OFFSETS_JSON = os.path.join(PACKAGE_DIR, 'DB.json')
    CONF_FILE = os.path.join(PACKAGE_DIR, 'dragon-radar.conf')
    WORKING_DIR = 'C:/dragon-radar'
    SOURCE_DIR = WORKING_DIR
    FUNI_SUB_DIR = 'Funi VobSubs'
    RETIMED_SUB_DIR = 'Retimed VobSubs'
    R1_DEMUX_DIR = 'R1 Demux'
    R2_DEMUX_DIR = 'R2 Demux'
    R1_DISC_DIR = 'R1 Discs'
    R2_DISC_DIR = 'R2 Discs'
    APP_NAME = 'dragon-radar'
    PGCDEMUX = ''
    VSRIP = ''
    DELAYCUT = ''
    VSRIP_TEMPLATE = ('{in_path}\n'
                      '{out_path}\n'
                      '1\n'
                      '{vid_sequence}\n'
                      'ALL\n'
                      'CLOSE\n'
                      'RESETTIME\n')
    PARAM_FILE = 'param.lst'
    WELCOME_MSG = ('.__ .__ .__..__ .__..  .  .__ .__..__ .__..__ \n'
                   '|  \\[__)[__][ __|  ||\\ |  [__)[__]|  \\[__][__)\n'
                   '|__/|  \\|  |[_./|__|| \\|  |  \\|  ||__/|  ||  \\')
    MIN_SIZE = 100000000
