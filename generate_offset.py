import json

new_info = {"DBZ": {}}

with open("./params/offsets.json", "r") as demuxfile:
    offsets = json.load(demuxfile)

old_obj = offsets['DBZ']
new_obj = {}

for ep in range(254, 292):
    episode = str(ep).zfill(3)
    with open('H:/output/DBZ/' + episode + '/R1/Celltimes.txt') as cellfile:
        chaps = cellfile.readlines()

    plg = chaps[0]
    # pta = chaps[2]
    ptb = chaps[4]
    ed = chaps[6]

    new_obj[episode] = {}
    new_obj[episode]['A_prologue'] = {}
    new_obj[episode]['A_prologue']['frame'] = int(plg)
    # new_obj[episode]['A_prologue']['offset'] = old_obj[episode]['prologue']['offset']
    new_obj[episode]['A_prologue']['offset'] = 5
    # new_obj[episode]['Aa_partA'] = {}
    # new_obj[episode]['Aa_partA']['frame'] = int(pta)
    # new_obj[episode]['Aa_partA']['offset'] = -1
    #new_obj[episode]['Aa_partA']['offset'] = old_obj[episode]['partA']['offset']
    new_obj[episode]['B_partB'] = {}
    new_obj[episode]['B_partB']['frame'] = int(ptb)
    # new_obj[episode]['B_partB']['offset'] =  old_obj[episode]['partB']['offset']
    new_obj[episode]['B_partB']['offset'] =  0
    new_obj[episode]['C_ED'] = {}
    new_obj[episode]['C_ED']['frame'] = int(ed)
    # new_obj[episode]['C_ED']['offset'] =  old_obj[episode]['ED']['offset']
    new_obj[episode]['C_ED']['offset'] = 0

    with open('new_info2.json', 'w') as outfil:
        json.dump(new_obj, outfil, sort_keys=True)
