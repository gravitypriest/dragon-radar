import os
import sys
import logging
import subprocess
import constants
from subtitle import detect_streams
from utils import load_title_time, to_timestamp, check_abort

APP_NAME = constants.APP_NAME

logger = logging.getLogger(APP_NAME)
chapter_names = {'op': 'Opening',
                 'prologue': 'Prologue',
                 'partA': 'Part A',
                 'partB': 'Part B',
                 'ED': 'Ending',
                 'NEP': 'Next Episode Preview'}


def _run_mkvmerge(episode, video, audio, subtitles, chapter_file):
    args = [episode.mkvmerge, '--output', episode.mkv_file]
    # video
    args.extend(['--language', '0:und', '(', video, ')'])
    tracks = ['0:0']
    current_track_len = len(tracks)
    for a in audio:
        args.extend(['--language', '0:' + a['lang'], '--track-name', '0:' + a['name'], '(', a['file'], ')'])
        tracks.append(str(audio.index(a) + current_track_len) + ':' + '0')
    # en audio
    current_track_len = len(tracks)
    for sub in subtitles:
        for s in sub['streams']:
            if len(sub['streams']) == 1 and s['idx'] == 1:
                args.extend(['--subtitle-tracks', '1'])
            args.extend(['--language', str(s['idx']) + ':eng', '--track-name', str(s['idx']) + ':' + s['name']])
            tracks.append(str(subtitles.index(sub) + current_track_len) + ':' + str(s['idx']))
        args.extend(['(', sub['file'], ')'])

    # track order
    args.extend(['--track-order', ','.join(tracks)])

    # chapters
    args.extend(['--chapters', chapter_file])

    # suppress MKVmerge output
    args.append('-q')

    logger.debug('MKVmerge args:')
    logger.debug(args)

    mergeproc = subprocess.call(args)
    check_abort(mergeproc, 'MKVmerge')



def _generate_mkv_chapters(episode):
    '''
    MKV chapter format:
    CHAPTER01=00:00:00.000
    CHAPTER01NAME=Intro
    CHAPTER02=00:01:00.000
    CHAPTER02NAME=Act 1
    CHAPTER03=00:05:30.000
    CHAPTER03NAME=Act 2
    CHAPTER04=00:12:20.000
    CHAPTER04NAME=Credits
    '''
    chapters = []
    if episode.series == 'MOVIES' or episode.is_special:
        # different from the episodes, just a list of chapters
        for c, chapter in enumerate(episode.r2_chapters):
            c_str = str(c + 1)
            time = to_timestamp(None, ntsc_frame=chapter)
            name = 'Chapter ' + c_str
            chapters.append('CHAPTER{0}={1}'.format(c_str.zfill(2), time))
            chapters.append('CHAPTER{0}NAME={1}'.format(c_str.zfill(2), name))
        return '\n'.join(chapters)

    ctr = 1
    keys = ['op', 'prologue', 'partA', 'partB', 'ED', 'NEP']
    title_time = load_title_time(episode.series, episode.number)
    if title_time is None:
        # sometimes the title time is null because there's no recap
        keys.remove('partA')

    for k in keys:
        if k != 'partA':
            chap = episode.r2_chapters[k]
            time = to_timestamp(None, ntsc_frame=chap)
        else:
            time = title_time
        num = str(ctr).zfill(2)
        name = chapter_names[k]
        if k == 'prologue' and not title_time:
            name = chapter_names['partA']
        chapters.append('CHAPTER{0}={1}'.format(num, time))
        chapters.append('CHAPTER{0}NAME={1}'.format(num, name))
        ctr = ctr + 1
    return '\n'.join(chapters)

def make_mkv(episode, streams=None):
    '''
    Make the MKV file
    '''
    # put the stream with most subpictures first
    video = episode.files['R2']['video'][0]
    audio = [{
        'file': episode.files['R2']['audio'][0],
        'name': 'Dragon Box',
        'lang': 'jpn'
    }]
    subtitles = []

    reg = 'R1_DBOX' if episode.is_r1dbox else 'R1'
    if not episode.no_funi:
        if 'retimed_subs' not in episode.files[reg]:
            logger.error('No retimed subs found.  Run again without --no-retime')
            sys.exit(1)
        streams = detect_streams(episode.files[reg]['retimed_subs'][0])
        streams.sort(key=lambda s: s['total'], reverse=True)
        streams_ = [{'name': 'Subtitles',
                     'idx': streams[0]['id']}]
        if len(streams) > 1:
            streams_.append({'name': 'Signs',
                             'idx': streams[1]['id']})
        subtitles.append(
            {'streams': streams_,
             'file': episode.files[reg]['retimed_subs'][0]})

    if episode.is_pioneer:
        if 'retimed_subs' not in episode.files['PIONEER']:
            logger.error('No retimed subs found.  Run again without --no-retime')
            sys.exit(1)
        audio.append({
            'file': episode.files['PIONEER']['retimed_audio'][0],
            'name': 'Pioneer Dub',
            'lang': 'eng'
        })
        subtitles.append({
            'streams':[{
                'name': 'Pioneer Subtitles',
                'idx': 0 if episode.number == '03' else 1
            },
            {
                'name': 'Pioneer Dub CC',
                'idx': 1 if episode.number == '03' else 0
            }],
            'file': episode.files['PIONEER']['retimed_subs'][0]
        })


    if not episode.no_funi:
        audio.append({
            'file': episode.files[reg]['retimed_audio'][0],
            'name': 'Dub w/ Original Score',
            'lang': 'eng'
        })
        if len(episode.files[reg]['retimed_audio']) > 1:
            audio.append({
                'file': episode.files[reg]['retimed_audio'][1],
                'name': 'Dub w/ Replacement Score',
                'lang': 'eng'
            })

    chapter_file = os.path.join(episode.temp_dir, 'mkv_chapters.txt')
    with open(chapter_file, 'w') as file_:
        file_.write(_generate_mkv_chapters(episode))    

    _run_mkvmerge(episode, video, audio, subtitles, chapter_file)
