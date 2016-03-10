from distutils.core import setup
import py2exe

setup(zipfile=None,
      console=[
          {'script': '__main__.py',
           'dest_base': 'dragon-radar',
           'icon_resources': [(0, 'icon.ico')]
           }],
      data_files=[('params', ['params/episodes.json',
                              'params/demux.json',
                              'params/offsets.json',
                              'params/valid.json']),
                  ('ac3files', ['ac3files/blank_20_192.ac3',
                                'ac3files/blank_20_384.ac3',
                                'ac3files/blank_51_384.ac3',
                                'ac3files/blank_51_448.ac3']),
                  ('', ['dragon-radar.conf'])])
