chapter_names = {'op': 'Opening',
                 'prologue': 'Prologue',
                 'partA': 'Part A',
                 'partB': 'Part B',
                 'ED': 'Ending',
                 'NEP': 'Next Episode Preview'}


def run_mkvmerge():
    args = [mkvmerge, '-o', out_file,
            '--forced-track', '0:no', '-A', '-S', '-T', '--no-global-tags', '--no-chapters', video_file,
            '--language', '0:jpn', '--track-name', '0:Dragon Box', '--forced-track', '0:no', '-a', '0', '-D', '-S', '-T', '--no-global-tags', '--no-chapters', jp_audio,
            '--language', '0:eng', '--track-name', '0:Dub w/ Original Score', '--forced-track', '0:no', '-a', '0', '-D', '-S', '-T', '--no-global-tags', '--no-chapters', en_audio,
            '--language', '0:eng', '--track-name', '0:Dub w/ Replacement Score', '--forced-track', '0:no', '-a', '0', '-D', '-S', '-T', '--no-global-tags', '--no-chapters', us_audio,
            '--language', '0:eng', '--track-name', '0:Subtitles', '--forced-track', '0:no', 
            '--language', '1:eng', '--track-name', '0:Songs & Signs', '--forced-track', '1:no', '-s', '0,1', '-D', '-A', '-T', '--no-global-tags', '--no-chapters', sub_idx,
            '--track-order" "0:0,1:0,2:0,3:0,4:0,4:1',
            '--chapters', chap_file]


def _generate_chapters(episode):
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
    ctr = 1
    keys = ['op', 'prologue', 'partA', 'partB', 'ED', 'NEP']
    title_time = load_title_time(episode.number)
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
        chapters.append('CHAPTER%s=%s', num, time)
        chapters.append('CHAPTER%sNAME=%s', num, name)
        ctr = ctr + 1
    return chapters


