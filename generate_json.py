'''
Some jank-ass code for creating demux_by_episode.json, dev use only
'''

import json

new_info = {"DBZ": {}, "DB":{}, "DBGT":{}, "MOVIES":{}}

with open("./params/demux.json", "r") as demuxfile:
    demux_info = json.load(demuxfile)

with open("./params/episodes.json", "r") as epfile:
    ep_info = json.load(epfile)


def r2disc(i):
    b = 1 if i < 147 else 2
    if b == 1 and i < 132:
        d = int(i / 6) + 1
        disc_eps = list(range(d * 6 - 5, d * 6 + 1))
    elif b == 1 and i >= 132:
        d = int((i - 132) / 5) + 23
        disc_eps = list(map(lambda e: e + 132, list(range((d-22) * 5 - 4, (d-22) * 5 + 1))))
    elif b == 2:
        d = int((i - 147) / 6) + 1
        disc_eps = list(map(lambda e: e + 147, list(range(d * 6 - 5, d * 6 + 1))))

    return int(b), int(d), disc_eps.index(i+1)


def r1disc(i, series):
    for b in ep_info[series]:
        for d in ep_info[series][b]:
            disc = ep_info[series][b][d]
            if (i + 1) in range(disc[0], disc[1] + 1):
                disc_eps = list(range(disc[0], disc[1] + 1))
                return int(b), int(d), disc_eps.index(i+1)

def _generate_source_folder_name(series, box, disc):

    if series == 'DB':
        return 'DRAGON_BALL_S{s}_D{d}'.format(s=box, d=disc)
    if series == 'DBGT':
        return 'DRAGON_BALL_GT_S{s}_D{d}'.format(s=box, d=disc)
    if series == 'DBZ':
        if box > 1 and box < 4:
            return 'DBZ_SEASON{s}_D{d}'.format(s=str(box).zfill(2),
                                               d=disc)
        elif box == 1:
            return 'DBZ_SEASON{s}_DISC{d}'.format(
                s=str(box).zfill(2),
                d=disc)
        elif box == 6:
            return 'DRAGONBALL_Z_S{s}_D{d}'.format(
                s=str(box),
                d=disc)
        else:
            return 'DRAGON_BALL_Z_S{s}_D{d}'.format(
                s=box, d=disc)

# S1
for i in range(0, 291):
    ep = str(i + 1).zfill(3)
    box, disc, ep_on_r1disc = r1disc(i, 'DBZ')

    # S1 weird, already documented
    if box == 1:
        cells = demux_info["DBZ"]["1"]["pgcdemux"][ep]
        vid = list(map(lambda v: (v + 6 * ep_on_r1disc), ([2, 3, 5, 6])))
        vts = 2

    # S2 1, 9 / 1, 2, 4, 5 pattern checks out
    # S3 1, 9 / 1, 2, 4, 5 pattern checks out
    if box == 2 or box == 3:
        cells = list(map(lambda v: (v + 9 * ep_on_r1disc), [1, 9]))
        vid = list(map(lambda v: (v + 6 * ep_on_r1disc), ([1, 2, 4, 5])))
        vts = 2
    # S4 -- S4 has US audio as track 0
    # D1
    # 1, 11     /   2, 3, 5, 6, 8
    # 12, 23    /   9, 10, 12, 13, 15
    # 24, 34    /   16, 17, 19, 20, 22
    # 35, 45    /   23, 24, 26, 27, 29
    # 46, 56    /   30, 31, 33, 34, 36
    # 57, 67    /   37, 38, 40, 41, 43
    # D2, D3, D4, D5, D6
    # 1, 11     /   2, 3, 5, 6, 8
    # 12, 22    /   9, 10, 12, 13, 15
    # 23, 33    /   16, 17, 19, 20, 22
    # 34, 44    /   23, 24, 26, 27, 29
    # 45, 55    /   30, 31, 33, 34, 36
    # 56, 66    /   37, 38, 40, 41, 43
    if box == 4:
        dmx = {
            "1": {
                "cells": [[1, 11], [12, 23], [24, 34], [35, 45], [46, 56], [57, 67]],
                "vid": [[2, 3, 5, 6, 8],
                        [9, 10, 12, 13, 15],
                        [16, 17, 19, 20, 22],
                        [23, 24, 26, 27, 29],
                        [30, 31, 33, 34, 36],
                        [37, 38, 40, 41, 43]]
            },
            "2-6": {
                "cells": [[1, 11], [12, 22], [23, 33], [34, 44], [45, 55], [56, 66]],
                "vid": [[2, 3, 5, 6, 8],
                        [9, 10, 12, 13, 15],
                        [16, 17, 19, 20, 22],
                        [23, 24, 26, 27, 29],
                        [30, 31, 33, 34, 36],
                        [37, 38, 40, 41, 43]]
            }
        }
        if disc == 1:
            disckey = "1"
        else:
            disckey = "2-6"
        cells = dmx[disckey]['cells'][ep_on_r1disc]
        vid = dmx[disckey]['vid'][ep_on_r1disc]
        vts = 1

    # S5 -- S5 has US audio as track 0
    # D1, D2
    # 1, 10     /   2, 3, 5, 6
    # 11, 20    /   8, 9, 11, 12
    # 21, 30    /   14, 15, 17, 18
    # 32, 41    /   21, 22, 24, 25
    # 42, 51    /   27, 28, 30, 31
    # 52, 61    /   33, 34, 36, 37
    # D3, D4, D5, D6
    # 1, 10     /   2, 3, 5, 6
    # 11, 20    /   8, 9, 11, 12
    # 21, 30    /   14, 15, 17, 18
    # 31, 40    /   20, 21, 23, 24
    # 41, 50    /   26, 27, 29, 30
    if box == 5:
        dmx = {
            "1-2": {
                "cells": [[1, 10], [11, 20], [21, 30], [32, 41], [42, 51], [52, 61]],
                "vid": [[2, 3, 5, 6],
                        [8, 9, 11, 12],
                        [14, 15, 17, 18],
                        [21, 22, 24, 25],
                        [27, 28, 30, 31],
                        [33, 34, 36, 37]]
            },
            "3-6": {
                "cells": [[1, 10], [11, 20], [21, 30], [31, 40], [41, 50]],
                "vid": [[2, 3, 5, 6],
                        [8, 9, 11, 12],
                        [14, 15, 17, 18],
                        [20, 21, 23, 24],
                        [26, 27, 29, 30]]
            }
        }
        if disc == 1 or disc == 2:
            disckey = "1-2"
        else:
            disckey = "3-6"
        cells = dmx[disckey]['cells'][ep_on_r1disc]
        vid = dmx[disckey]['vid'][ep_on_r1disc]
        vts = 1

    # S6
    # D1, D2, D3
    # 1, 10     /   2, 3, 5, 6
    # 11, 20    /   8, 9, 11, 12
    # 21, 30    /   14, 15, 17, 18
    # 32, 41    /   21, 22, 24, 25
    # 42, 51    /   27, 28, 30, 31
    # 52, 61    /   33, 34, 36, 37
    # D4, D5, D6
    # 1, 10     /   2, 3, 5, 6
    # 11, 20    /   8, 9, 11, 12
    # 21, 30    /   14, 15, 17, 18
    # 31, 40    /   20, 21, 23, 24
    # 41, 50    /   26, 27, 29, 30
    if box == 6:
        dmx = {
            "1-3": {
                "cells": [[1, 10], [11, 20], [21, 30], [32, 41], [42, 51], [52, 61]],
                "vid": [[2, 3, 5, 6],
                        [8, 9, 11, 12],
                        [14, 15, 17, 18],
                        [21, 22, 24, 25],
                        [27, 28, 30, 31],
                        [33, 34, 36, 37]]
            },
            "4-6": {
                "cells": [[1, 10], [11, 20], [21, 30], [31, 40], [41, 50]],
                "vid": [[2, 3, 5, 6],
                        [8, 9, 11, 12],
                        [14, 15, 17, 18],
                        [20, 21, 23, 24],
                        [26, 27, 29, 30]]
            }
        }
        if disc == 1 or disc == 2 or disc == 3:
            disckey = "1-3"
        else:
            disckey = "4-6"
        cells = dmx[disckey]['cells'][ep_on_r1disc]
        vid = dmx[disckey]['vid'][ep_on_r1disc]
        vts = 1

    # S7
    # D1, D2
    # 1, 10     /   2, 3, 5, 6, 8
    # 11, 20    /   9, 10, 12, 13, 15
    # 21, 30    /   16, 17, 19, 20, 22
    # 33, 42    /   25, 26, 28, 29, 31
    # 43, 52    /   32, 33, 35, 36, 38
    # 53, 62    /   39, 40, 42, 43, 45
    # D3
    # 1, 10     /   2, 3, 5, 6, 8
    # 11, 20    /   9, 10, 12, 13, 15
    # 23, 32    /   18, 19, 21, 22, 24
    # 33, 42    /   25, 26, 28, 29, 31
    # D4, D5, D6
    # 1, 10     /   2, 3, 5, 6, 8
    # 11, 20    /   9, 10, 12, 13, 15
    # 21, 30    /   16, 17, 19, 20, 22
    if box == 7:
        dmx = {
            "1-2": {
                "cells": [[1, 10 ], [11, 20], [21, 30], [33, 42], [43, 52], [53, 62]],
                "vid": [[2, 3, 5, 6, 8],
                        [9, 10, 12, 13, 15],
                        [16, 17, 19, 20, 22],
                        [25, 26, 28, 29, 31],
                        [32, 33, 35, 36, 38],
                        [39, 40, 42, 43, 45]]
            },
            "3": {
                "cells": [[1, 10], [11, 20], [23, 32], [33, 42]],
                "vid": [[2, 3, 5, 6, 8],
                        [9, 10, 12, 13, 15],
                        [18, 19, 21, 22, 24],
                        [25, 26, 28, 29, 31]]
            },
            "4-6": {
                "cells": [[1, 10], [11, 20], [21, 30]],
                "vid": [[2, 3, 5, 6, 8],
                        [9, 10, 12, 13, 15],
                        [16, 17, 19, 20, 22]]
            }
        }
        if disc == 1 or disc == 2:
            disckey = "1-2"
        elif disc == 3:
            disckey = "3"
        else:
            disckey = "4-6"
        cells = dmx[disckey]['cells'][ep_on_r1disc]
        vid = dmx[disckey]['vid'][ep_on_r1disc]
        vts = 5

    # S8
    # D1
    # 1, 10     /   2, 3, 5, 6, 8
    # 12, 21    /   10, 11, 13, 14, 16
    # 23, 32    /   18, 19, 21, 22, 24
    # 34, 43    /   26, 27, 29, 30, 32
    # 45, 54    /   34, 35, 37, 38, 40
    # 56, 65    /   42, 43, 45, 46, 48
    # D2, D3, D4, D5, D6
    # 1, 10     /   2, 4, 5, 7
    # 12, 21    /   9, 11, 12, 14
    # 23, 32    /   16, 18, 19, 21
    # 34, 43    /   23, 25, 26, 28
    # 45, 54    /   30, 32, 33, 35
    # 56, 65    /   37, 39, 40, 42
    if box == 8:
        dmx = {
            "1": {
                "cells": [[1, 10 ], [12, 21], [23, 32], [34, 43], [45, 54], [56, 65]],
                "vid": [[2, 3, 5, 6, 8],
                        [10, 11, 13, 14, 16],
                        [18, 19, 21, 22, 24],
                        [26, 27, 29, 30, 32],
                        [34, 35, 37, 38, 40],
                        [42, 43, 45, 46, 48]]
            },
            "2-6": {
                "cells": [[1, 10], [12, 21], [23, 32], [34, 43], [45, 54], [56, 65]],
                "vid": [[2, 4, 5, 7],
                        [9, 11, 12, 14],
                        [16, 18, 19, 21],
                        [23, 25, 26, 28],
                        [30, 32, 33, 35],
                        [37, 39, 40, 42]]
            }
        }
        if disc == 1:
            disckey = "1"
        else:
            disckey = "2-6"
        cells = dmx[disckey]['cells'][ep_on_r1disc]
        vid = dmx[disckey]['vid'][ep_on_r1disc]
        vts = 5

    # S9
    # D1, D2, D3, D4, D5, D6
    # 1, 10     /   2, 4, 5, 7
    # 12, 21    /   9, 11, 12, 14
    # 23, 32    /   16, 18, 19, 21
    # 34, 43    /   23, 25, 26, 28
    # 45, 54    /   30, 32, 33, 35
    # 56, 65    /   37, 39, 40, 42
    # 67, 76    /   44, 46, 47, 49
    if box == 9:
        dmx = {
            "cells": [[1, 10 ], [12, 21], [23, 32], [34, 43], [45, 54], [56, 65], [67, 76]],
            "vid": [[2, 4, 5, 7],
                    [9, 11, 12, 14],
                    [16, 18, 19, 21],
                    [23, 25, 26, 28],
                    [30, 32, 33, 35],
                    [37, 39, 40, 42],
                    [44, 46, 47, 49]]
        }
        cells = dmx['cells'][ep_on_r1disc]
        vid = dmx['vid'][ep_on_r1disc]
        vts = 5

    audio = ["en", "us", "jp"]
    if box == 4 or box == 5:
        audio = ["us", "jp", "en"]

    r1_ep_obj = {
        "type": "pgc",
        "disc": _generate_source_folder_name("DBZ", box, disc),
        "pgc": 1,
        "cells": cells,
        "vid": vid,
        "vts": vts,
        "audio": audio
    }

    box, disc, ep_on_r2disc = r2disc(i)
    r2_ep_obj = {
        "disc": "DBZ" +str(box) +"_"+str(disc),
        "type": "pgc",
        "pgc": ep_on_r2disc + 3,
        "vid": None,
        "cells": None,
        "vts": 1,
        "audio": ["jp"]
    }
    # DBOX Z R1
    box, disc, ep_on_dbox = r1disc(i, 'DBoxZ')

    # BOX 1: - [en, jp]
    # D1 - VTS 11 - PGC 1 - VID 1, 4, 7, 10, 13, 17, 20
    # D2 - VTS 11 - PGC 1 - VID 1, 5, 8, 12, 16, 19, 23
    # D3 - VTS 13 - PGC 1 - VID 1, 5, 9, 12, 15, 19, 23
    # D4 - VTS 10 - PGC 1 - VID 1, 5, 8, 12, 16, 19, 23
    # D5 - VTS 13 - PGC 1 - VID 1, 5, 9, 13, 16, 20, 24
    # D6 - VTS 13 - PGC 1 - VID 1, 4, 8, 12, 15, 18, 22
    if box == 1:
        if disc == 1:
            vts = 11
            dmx = [1, 4, 7, 10, 13, 17, 20]
        if disc == 2:
            vts = 11
            dmx = [1, 5, 8, 12, 16, 19, 23]
        if disc == 3:
            vts = 13
            dmx = [1, 5, 9, 12, 15, 19, 23]
        if disc == 4:
            vts = 10
            dmx = [1, 5, 8, 12, 16, 19, 23]
        if disc == 5:
            vts = 13
            dmx = [1, 5, 9, 13, 16, 20, 24]
        if disc == 6:
            vts = 13
            dmx = [1, 4, 8, 12, 15, 18, 22]

    # BOX 2: - [en, jp]
    # D1 - VTS 13 - PGC 1 - VID 5, 8, 11, 14, 17, 20, 23
    # D2 - VTS 11 - PGC 1 - VID 4, 7, 10, 13, 17, 21, 24
    # D3 - VTS 13 - PGC 1 - VID 4, 7, 10, 14, 18, 22, 25
    # D4 - VTS 11 - PGC 1 - VID 5, 9, 12, 15, 18, 21, 24
    # D5 - VTS 9  - PGC 1 - VID 4, 7, 10, 13, 17, 20, 23
    # D6 - VTS 13 - PGC 1 - VID 4, 7, 11, 15, 18, 22, 25
    if box == 2:
        if disc == 1:
            vts = 13
            dmx = [5, 8, 11, 14, 17, 20, 23]
        if disc == 2:
            vts = 11
            dmx = [4, 7, 10, 13, 17, 21, 24]
        if disc == 3:
            vts = 13
            dmx = [4, 7, 10, 14, 18, 22, 25]
        if disc == 4:
            vts = 11
            dmx = [5, 9, 12, 15, 18, 21, 24]
        if disc == 5:
            vts = 9
            dmx = [4, 7, 10, 13, 17, 20, 23]
        if disc == 6:
            vts = 13
            dmx = [4, 7, 11, 15, 18, 22, 25]

    # BOX 3: - [en, jp]
    # D1 - VTS 12 - PGC 1 - VID 5, 8, 11, 14, 18, 21, 25
    # D2 - VTS 11 - PGC 1 - VID 4, 8, 11, 15, 18, 21, 24
    # D3 - VTS 11 - PGC 1 - VID 5, 9, 12, 16, 20, 24, 27
    # D4 - VTS 12 - PGC 1 - VID 1, 5, 9, 13, 17, 21, 24
    # D5 - VTS 12 - PGC 1 - VID 1, 5, 8, 11, 14, 17, 21
    # D6 - VTS 12 - PGC 1 - VID 1, 4, 8, 12, 15, 19, 23
    if box == 3:
        if disc == 1:
            vts = 12
            dmx = [5, 8, 11, 14, 18, 21, 25]
        if disc == 2:
            vts = 11
            dmx = [4, 8, 11, 15, 18, 21, 24]
        if disc == 3:
            vts = 11
            dmx = [5, 9, 12, 16, 20, 24, 27]
        if disc == 4:
            vts = 12
            dmx = [1, 5, 9, 13, 17, 21, 24]
        if disc == 5:
            vts = 12
            dmx = [1, 5, 8, 11, 14, 17, 21]
        if disc == 6:
            vts = 12
            dmx = [1, 4, 8, 12, 15, 19, 23]

    # BOX 4: - en.jp
    # D1,2,3,4,5,6 - VTS 7 - PGC 1 - VID 1, 2, 3, 4, 5, 6, 7
    if box == 4:
        vts = 7
        dmx = [1, 2, 3, 4, 5, 6, 7]

    # BOX 5 - []
    # D1,2,4,5,6 - VTS 6 - PGC 1 - VID 9, 10, 11, 12, 13, 14, 15
    if box == 5:
        vts = 6
        dmx = [9, 10, 11, 12, 13, 14, 15]

    # BOX 6 - []
    # D1,2,4,5,6 - VTS 6 - PGC 1 - VID 1, 2, 3, 4, 5, 6, 7
    # D3 - VTS 6 - PGC 1 - VID 11, 1, 2, 3, 4, 5, 6
    if box == 6:
        if disc == 3:
            vts = 6
            dmx = [11, 1, 2, 3, 4, 5, 6]
        else:
            vts = 6
            dmx = [1, 2, 3, 4, 5, 6, 7]

    # BOX 7 - []
    # D1,2,3,4,5,6 - VTS 6 - PGC 1 - VID 1, 2, 3, 4, 5, 6, 7
    if box == 7:
        vts = 6
        dmx = [1, 2, 3, 4, 5, 6, 7]

    r1_dbox_obj = {
        "disc": "DRAGON_BOX_S%d_D%d" % (box, disc),
        "type": "vid",
        "pgc": 1,
        "cells": None,
        "vid": [dmx[ep_on_dbox]],
        "vts": vts,
        "audio": ['en', 'jp']
    }

    ep_obj = {"R1": r1_ep_obj, "R2": r2_ep_obj, "R1_DBOX": r1_dbox_obj}
    new_info["DBZ"][ep] = ep_obj

with open('new_info.json', 'w') as outfil:
    json.dump(new_info, outfil, sort_keys=True)

# S1 weird, already documented
# S2 1, 9 / 1, 2, 4, 5 pattern checks out
# S3 1, 9 / 1, 2, 4, 5 pattern checks out

# S4 -- S4 has US audio as track 0
# D1
# 1, 11     /   2, 3, 5, 6, 8
# 12, 23    /   9, 10, 12, 13, 15
# 24, 34    /   16, 17, 19, 20, 22
# 35, 45    /   23, 24, 26, 27, 29
# 46, 56    /   30, 31, 33, 34, 36
# 57, 67    /   37, 38, 40, 41, 43
# D2, D3, D4, D5, D6
# 1, 11     /   2, 3, 5, 6, 8
# 12, 22    /   9, 10, 12, 13, 15
# 23, 33    /   16, 17, 19, 20, 22
# 34, 44    /   23, 24, 26, 27, 29
# 45, 55    /   30, 31, 33, 34, 36
# 56, 66    /   37, 38, 40, 41, 43

# S5 -- S5 has US audio as track 0
# D1, D2
# 1, 10     /   2, 3, 5, 6
# 11, 20    /   8, 9, 11, 12
# 21, 30    /   14, 15, 17, 18
# 32, 41    /   21, 22, 24, 25
# 42, 51    /   27, 28, 30, 31
# 52, 61    /   33, 34, 36, 37
# D3, D4, D5, D6
# 1, 10     /   2, 3, 5, 6
# 11, 20    /   8, 9, 11, 12
# 21, 30    /   14, 15, 17, 18
# 31, 40    /   20, 21, 23, 24
# 41, 50    /   26, 27, 29, 30

# S6
# D1, D2, D3
# 1, 10     /   2, 3, 5, 6
# 11, 20    /   8, 9, 11, 12
# 21, 30    /   14, 15, 17, 18
# 32, 41    /   21, 22, 24, 25
# 42, 51    /   27, 28, 30, 31
# 52, 61    /   33, 34, 36, 37
# D4, D5, D6
# 1, 10     /   2, 3, 5, 6
# 11, 20    /   8, 9, 11, 12
# 21, 30    /   14, 15, 17, 18
# 31, 40    /   20, 21, 23, 24
# 41, 50    /   26, 27, 29, 30

# (angle 2 from now on)
# S7
# D1, D2
# 1, 10     /   2, 3, 4, 6, 7
# 11, 20    /   9, 10, 11, 13, 14
# 21, 30    /   16, 17, 18, 20, 21
# 33, 42    /   25, 26, 27, 29, 30
# 43, 52    /   32, 33, 34, 36, 37
# 53, 62    /   39, 40, 41, 43, 44
# D3
# 1, 10     /   2, 3, 4, 6, 7
# 11, 20    /   9, 10, 11, 13, 14
# 23, 32    /   18, 19, 20, 22, 23
# 33, 42    /   25, 26, 27, 29, 30
# D4, D5, D6
# 1, 10     /   2, 3, 4, 6, 7
# 11, 20    /   9, 10, 11, 13, 14
# 21, 30    /   16, 17, 18, 20, 21

# S8
# D1
# 1, 10     /   2, 3, 4, 6, 7
# 12, 21    /   10, 11, 12, 14, 15
# 23, 32    /   18, 19, 20, 22, 23
# 34, 43    /   26, 27, 28, 30, 31
# 45, 54    /   34, 35, 36, 38, 39
# 56, 65    /   42, 43, 44, 46, 47
# D2, D3, D4, D5, D6
# 1, 10     /   2, 3, 5, 6
# 12, 21    /   9, 10, 12, 13
# 23, 32    /   16, 17, 19, 20
# 34, 43    /   23, 24, 26, 27
# 45, 54    /   30, 31, 33, 34
# 56, 65    /   37, 38, 40, 41

# S9
# D1, D2, D3, D4, D5, D6
# 1, 10     /   2, 3, 5, 6
# 12, 21    /   9, 10, 12, 13
# 23, 32    /   16, 17, 19, 20
# 34, 43    /   23, 24, 26, 27
# 45, 54    /   30, 31, 33, 34
# 56, 65    /   37, 38, 40, 41
# 67, 76    /   44, 45, 47, 48


#---adjusted for angle 2---
# S7
# D1, D2
# 1, 10     /   2, 3, 5, 6, 8
# 11, 20    /   9, 10, 12, 13, 15
# 21, 30    /   16, 17, 19, 20, 22
# 33, 42    /   25, 26, 28, 29, 31
# 43, 52    /   32, 33, 35, 36, 38
# 53, 62    /   39, 40, 42, 43, 45
# D3
# 1, 10     /   2, 3, 5, 6, 8
# 11, 20    /   9, 10, 12, 13, 15
# 23, 32    /   18, 19, 21, 22, 24
# 33, 42    /   25, 26, 28, 29, 31
# D4, D5, D6
# 1, 10     /   2, 3, 5, 6, 8
# 11, 20    /   9, 10, 12, 13, 15
# 21, 30    /   16, 17, 19, 20, 22

# S8
# D1
# 1, 10     /   2, 3, 5, 6, 8
# 12, 21    /   10, 11, 13, 14, 16
# 23, 32    /   18, 19, 21, 22, 24
# 34, 43    /   26, 27, 29, 30, 32
# 45, 54    /   34, 35, 37, 38, 40
# 56, 65    /   42, 43, 45, 46, 48
# D2, D3, D4, D5, D6
# 1, 10     /   2, 4, 5, 7
# 12, 21    /   9, 11, 12, 14
# 23, 32    /   16, 18, 19, 21
# 34, 43    /   23, 25, 26, 28
# 45, 54    /   30, 32, 33, 35
# 56, 65    /   37, 39, 40, 42

# S9
# D1, D2, D3, D4, D5, D6
# 1, 10     /   2, 4, 5, 7
# 12, 21    /   9, 11, 12, 14
# 23, 32    /   16, 18, 19, 21
# 34, 43    /   23, 25, 26, 28
# 45, 54    /   30, 32, 33, 35
# 56, 65    /   37, 39, 40, 42
# 67, 76    /   44, 46, 47, 49

# DBGT
# S1 - VTS: 1
# D1: VID 4-10
# D2: VID 2-8
# D3: VID 2-8
# D4: VID 2-8
# D5: VID 2-7
# S2 - VTS: 5
# D1: VID 2-8
# D2: VID 2-8
# D3: VID 2-7
# D4: VID 2-7
# D5: VID 2-5
# DBGT SPECIAL: S2D5 VTS 8, VID 2

'''
        "bardock": {
            "R1": {
                "cells": null,
                "disc": "BARDOCK_THE_FATHER_OF_GOKU",
                "pgc": 1,
                "type": "pgc",
                "vid": [2, 4, 5, 7, 8],
                "vts": 1,
                "audio": ["us", "jp", "en"]
            },
            "R2": {
                "cells": null,
                "disc": "DBZ1_SP",
                "pgc": null,
                "type": "vid",
                "vid": 2,
                "vts": 1,
                "audio": ["jp"]
            },
        },
        "trunks": {         
            "R1": {
                "cells": null,
                "disc": "DBZ2_SP1",
                "pgc": 1,
                "type": "pgc",
                "vid": [2, 4, 5, 7, 8],
                "vts": 1,
                "audio": ["us", "jp", "en"]
            },
            "R2": {
                "cells": null,
                "disc": "DBZ2_SP1",
                "pgc": null,
                "type": "vid",
                "vid": 1,
                "vts": 1,
                "audio": ["jp"]
            },
        }
        # GT
        "special": {         
            "R1": {
                "cells": null,
                "disc": "DRAGON_BALL_GT_S2_D5",
                "pgc": null,
                "type": "vid",
                "vid": 2,
                "vts": 8
            },
            "R2": {
                "cells": null,
                "disc": "DBGT_SP",
                "pgc": null,
                "type": "vid",
                "vid": 2,
                "vts": 1
            },
        }
'''

