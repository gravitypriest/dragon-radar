import os
import subprocess
from utils import load_title_time, to_timestamp

chapter_names = {'op': 'Opening',
                 'prologue': 'Prologue',
                 'partA': 'Part A',
                 'partB': 'Part B',
                 'ED': 'Ending',
                 'NEP': 'Next Episode Preview'}


def _run_mkvmerge(mkvmerge, video, jp_audio, en_audio, us_audio, subs, sub_id, signs_id, chapter_file, episode):
    args = [mkvmerge, '--output', episode.mkv_file]
    # video
    args.extend(['--language', '0:und', '(', video, ')'])
    # jp audio
    args.extend(['--language', '0:jpn', '--track-name', '0:Dragon Box', '(', jp_audio, ')'])
    # en audio
    args.extend(['--language', '0:eng', '--track-name', '0:Dub w/ Original Score', '(', en_audio, ')'])
    if us_audio:
        # us broadcast audio
        args.extend(['--language', '0:eng', '--track-name', '0:Dub w/ Replacement Score', '(', us_audio, ')'])
    # subs
    args.extend(['--language', '{0}:eng'.format(sub_id), '--track-name', '{0}:Subtitles'.format(sub_id),
                 '--language', '{0}:eng'.format(signs_id), '--track-name', '{0}:Signs'.format(signs_id), '(', subs, ')']) 
    # track order
    args.append('--track-order')
    if us_audio and signs_id is not None:
        args.append('0:0,1:0,2:0,3:0,4:{0},4:{1}'.format(sub_id, signs_id))
    if us_audio and signs_id is None:
        args.append('0:0,1:0,2:0,3:0,4:0')
    if not us_audio and signs_id is not None:
        args.append('0:0,1:0,2:0,3:{0},3:{1}'.format(sub_id, signs_id))
    if not us_audio and signs_id is None:
        args.append('0:0,1:0,2:0,3:0')
    # chapters
    args.extend(['--chapters', chapter_file])
    args.append('-q')
    subprocess.run(args)

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
    if episode.series == 'MOVIES':
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

def make_mkv(episode, streams):
    '''
    Make the MKV file
    '''
    # put the stream with most subpictures first
    streams.sort(key=lambda s: s['total'], reverse=True)
    video = episode.files['R2']['video'][0]
    jp_audio = episode.files['R2']['audio'][0]
    en_audio = episode.files['R1']['retimed_audio'][0]
    if len(episode.files['R1']['retimed_audio']) > 1:
        us_audio = episode.files['R1']['retimed_audio'][1]
    else:
        us_audio = None
    subs = episode.files['R1']['retimed_subs'][0]
    sub_id = streams[0]['id']
    if len(streams) > 1:
        signs_id = streams[1]['id']
    else:
        signs_id = None

    chapter_file = os.path.join(episode.temp_dir, 'mkv_chapters.txt')
    with open(chapter_file, 'w') as file_:
        file_.write(_generate_mkv_chapters(episode))    

    _run_mkvmerge(episode.mkvmerge, video, jp_audio, en_audio, us_audio, subs, sub_id, signs_id, chapter_file, episode)
