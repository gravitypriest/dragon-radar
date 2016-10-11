'''
Module with demuxing functions
'''
import os
import sys
import subprocess
import logging
import constants
from utils import rename
from audio import retime_ac3, combine_files, check_abort

PARAM_FILE = constants.PARAM_FILE
VSRIP_TEMPLATE = constants.VSRIP_TEMPLATE
APP_NAME = constants.APP_NAME
logger = logging.getLogger(APP_NAME)


def _run_pgcdemux(pgcdemux, source_ifo, dest_dir, type_, vid, pgc, cells, novid=False, noaud=False):
    '''
    Construct PGCDemux call and run it
    '''
    args = [pgcdemux, '-nolog', '-guism']
    if novid:
        args.append('-nom2v')
    else:
        args.append('-m2v')
    args.append('-cellt')
    if noaud:
        args.append('-noaud')
    else:
        args.append('-aud')
    args.append('-nosub')
    if type_ == 'vid':
        args.extend(['-vid', str(vid[0])])
    if type_ == 'pgc':
        args.extend(['-pgc', str(pgc)])
        if cells:
            args.extend(['-sc', str(cells[0]), '-ec', str(cells[1])])
    if type_ == 'cell':
        args.extend(['-cid', str(vid[0]), str(cells[0])])
    args.extend([source_ifo, dest_dir])
    logger.debug('PGCDemux args:')
    logger.debug(args)
    proc = subprocess.call(args)


def _run_vsrip(vsrip, source_ifo, dest_dir, pgc, vid):
    '''
    Run VSRip to extract DVD subtitles as VobSub
    '''
    vid_seq_str = '1 '
    for v in vid:
        vid_seq_str += 'v{0} '.format(v)
    vid_seq_str = vid_seq_str.strip()
    out_file = os.path.join(dest_dir, 'Subtitle')
    param_file = os.path.join(dest_dir, PARAM_FILE)
    content = VSRIP_TEMPLATE.format(in_path=source_ifo,
                                    out_path=out_file,
                                    vid_sequence=vid_seq_str,
                                    pgc=pgc)
    logger.debug('VSRip params file:\n%s', content)
    with open(param_file, 'w') as param:
        param.write(content)
    subprocess.call([vsrip, param_file])


def files_index(dest_dir):
    '''
    Create dictionary of file locations
    '''
    video = os.path.join(dest_dir, 'VideoFile.m2v')
    aud_0 = os.path.join(dest_dir, 'AudioFile_80.ac3')
    aud_1 = os.path.join(dest_dir, 'AudioFile_81.ac3')
    aud_2 = os.path.join(dest_dir, 'AudioFile_82.ac3')
    chapters = os.path.join(dest_dir, 'Celltimes.txt')
    sub_idx = os.path.join(dest_dir, 'Subtitle.idx')
    sub_sub = os.path.join(dest_dir, 'Subtitle.sub')

    return {
        'video': [video],
        'audio': [aud_0, aud_1, aud_2],
        'subs': [sub_idx, sub_sub],
        'chapters': [chapters]
    }


def complex_demux(episode, source_ifo, src_dir, dest_dir, demux_map, novid=False):
    '''
    Weird demux patterns required for:
    DB 26, DB 41, DBZ 24
        Parts of these episodes are encoded interlaced, but flagged progressive.
        Need to rip each piece one at a time, correct the flag, then combine.
    DB 138
        DB 137 and 138 are on the same VID. 137 plays properly, but 138 has
        an audio delay if the episode is ripped by PGC.  Need to rip the
        audio from the VID, trim it, then combine it with the OP for proper
        audio.    
    '''
    # interlacing correction
    if (episode.series == 'DB' and episode.number in ['026', '041'] or
       episode.series == 'DBZ' and episode.number == '024'):
        cells = demux_map['complex']['cells']
        output_files = []

        for cell in cells:
            # demux cell
            logger.debug('Ripping cell %s...', cell)
            _run_pgcdemux(episode.pgcdemux, source_ifo, dest_dir, 'cell', [cell['vid']], None, [cell['cell']], noaud=True)
            output = files_index(dest_dir)['video'][0]
            renamed = os.path.join(dest_dir, str(cell['vid']) + '_' + str(cell['cell']) + '.m2v')
            rename(output, renamed)

            # fix the messed up cell
            # need to open ReStream GUI for this, ugh
            if cell['fix']:
                logger.info('Launching ReStream...')
                proc = subprocess.Popen(episode.restream)
                proc.poll()
                # user prompt
                print('\n1. In the ReStream window, copy & paste\n\n'
                      '   {0}\n\n'
                      '   into "MPEG-2 Source" box at the top.\n\n'
                      '   NOTE: If you are using standard Windows command prompt (not PowerShell),\n' 
                      '   double left-click the line to highlight it, then right-click to copy it.\n\n'
                      '2. Uncheck the checkbox which says '
                      '\"Frametype progressive.\"\n'
                      '3. Click the button which says \"Write!\"\n'
                      '4. When finished, you may close the '
                      'ReStream window.\n'.format(renamed))
                input('Once completed, press enter to continue...')

                # take the fixed one and run with it
                fixed_cell = ('%s.0%s' % os.path.splitext(renamed))
                logger.debug('Looking for fixed cell...')
                if not os.path.isfile(fixed_cell):
                    logger.error('%s not found! Please follow the ReStream instructions.', fixed_cell)
                    sys.exit(1)
                logger.debug('Fixed cell found! Continuing.')
                output_files.append(fixed_cell)
            else:
                output_files.append(renamed)

        # use dgindex to merge the files
        logger.info('Combining cells...')
        final_file = os.path.join(dest_dir, 'VideoFile.m2v')

        # dgindex adds .demuxed to the file so we have to rename it
        final_dgd = os.path.join(dest_dir, 'VideoFile.demuxed.m2v')
        args = [episode.dgindex, '-i']
        args.extend(output_files)
        args.extend(['-od', os.path.splitext(final_file)[0], '-minimize', '-exit'])
        with open(os.devnull, 'w') as devnull:
            dcut = subprocess.call(args, stdout=devnull,
                                   stderr=subprocess.STDOUT)
        check_abort(dcut, 'Delaycut')
        logger.info('Cell combination finished.')
        rename(final_dgd, final_file)
        # normal demux
        logger.debug('Demuxing normally from now on.')
        _run_pgcdemux(episode.pgcdemux, source_ifo, dest_dir,
                      'pgc', None, demux_map['pgc'], None, novid=True)


    # audio delay
    if episode.series == 'DB' and episode.number == '138':        
        op_vid, ep_vid = demux_map['complex']['vid']
        start_frame = demux_map['complex']['start']

        # get OP audio
        logger.debug('Ripping OP audio...')
        _run_pgcdemux(episode.pgcdemux, source_ifo, dest_dir, 'vid', op_vid, None, None, novid=True)

        # rename the file
        op_audio = files_index(dest_dir)['audio'][0]
        op_newfname = os.path.join(dest_dir, 'op_audio.ac3')
        rename(op_audio, op_newfname)

        # get episode audio
        logger.debug('Ripping episode audio...')
        _run_pgcdemux(episode.pgcdemux, source_ifo, dest_dir, 'vid', ep_vid, None, None, novid=True)
        ep_audio = files_index(dest_dir)['audio'][0]

        # trim the audio
        logger.debug('Trimming audio...')
        ep_newfname = os.path.join(dest_dir, 'ep_audio.ac3')
        retime_ac3(episode, ep_audio, ep_newfname, 448, offset_override=[{'frame': 0, 'offset': start_frame}])

        # smash them together
        logger.debug('Combining audio...')
        final_file = os.path.join(dest_dir, 'AudioFile_80.ac3')
        combine_files([op_newfname, ep_newfname], final_file)
        logger.debug('Audio processing complete.')

        # normal demux
        logger.debug('Demuxing normally from now on.')
        _run_pgcdemux(episode.pgcdemux, source_ifo, dest_dir,
                      'pgc', None, demux_map['pgc'], None, novid=novid, noaud=True)


def demux(episode, src_dir, dest_dir, demux_map, novid=False, nosub=False, sub_only=False):
    '''
    Demux video, audio, subs
    Return an object with the filenames
    '''
    cells = demux_map['cells']
    type_ = demux_map['type']
    vid = demux_map['vid']
    pgc = demux_map['pgc']
    source_ifo = os.path.join(
        src_dir,
        demux_map['disc'],
        'VIDEO_TS',
        ('VTS_%s_0.IFO' % str(demux_map['vts']).zfill(2))
    )
    if not os.path.exists(source_ifo):
        logger.error('Source IFO %s not found! Please check the `source_dir` '
                     'setting in dragon-radar.ini, and follow the README '
                     'on how to organize your files.', source_ifo)
        sys.exit(1)

    if not sub_only:
        if type_ == 'complex':
            logger.debug('Starting complex demux...')
            complex_demux(episode, source_ifo, src_dir, dest_dir, demux_map, novid=novid)
        else:
            logger.info('Demuxing video and audio...')
            _run_pgcdemux(episode.pgcdemux, source_ifo, dest_dir,
                          type_, vid, pgc, cells, novid=novid)
            logger.info('Video & audio demux complete.')

    if not nosub:
        logger.info('Demuxing subtitles to VobSub. Please don\'t close the VSRip window!')
        _run_vsrip(episode.vsrip, source_ifo, dest_dir, pgc, vid)
        logger.info('Subtitle demux complete.')

    return files_index(dest_dir)
