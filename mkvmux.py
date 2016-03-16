chapter_names = {'op': 'Opening',
                 'prologue': 'Prologue',
                 'partA': 'Part A',
                 'partB': 'Part B',
                 'ED': 'Ending',
                 'NEP': 'Next Episode Preview'}


def generate_chapters(episode):
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
