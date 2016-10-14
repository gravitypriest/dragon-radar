# Dragon Radar ![app icon](https://raw.githubusercontent.com/gravitypriest/dragon-radar/master/icon_readme.png "Dragon Radar")
In a world where the Dragon Ball series DVDs released in the U.S. have lousy video quality, Dragon Radar aims to take the much better video of the Japanese DVDs, and slap on the audio and subtitles from the U.S. DVDs.

#### [Click here to download](https://github.com/gravitypriest/dragon-radar/releases)

## Requirements

#### Software
<b>NOTE:</b> Pay attention to versions! If version number is listed, it means the program will not work unless you use the version specified. Clicking 'direct link' will get you the proper files direc.
- [PGCdemux m03 MOD](http://www.videohelp.com/software/PgcDemux) ([direct link](http://www.videohelp.com/download/PgcDemux_1205Mod_m03_bin.zip))
- [ReStream](http://www.videohelp.com/software/Restream) ([direct link](http://www.videohelp.com/download/ReStream_v090.zip))
- [VSRip](http://www.videohelp.com/software/VSRip) ([direct link](http://www.videohelp.com/download/VSRip_20030530.zip))
- [DelayCut 1.4.3.7](http://www.videohelp.com/software/delaycut) ([direct link](http://www.videohelp.com/download/delaycut1.4.3.7.7z))
- [DGMPGDec](http://www.videohelp.com/software/DGMPGDec) ([direct link](http://www.videohelp.com/download/dgmpgdec158.zip))
- [MKVToolnix](http://www.videohelp.com/software/MKVtoolnix) ([direct link](http://www.videohelp.com/download/mkvtoolnix-32bit-9.4.2-setup.exe)) (v9.4.2 latest as of this writing)

#### DVDs

- R1 DVDs:
    - Dragon Ball "Blue Brick" Season sets
    - Dragon Ball Z "Orange Brick" Season sets
    - Dragon Ball GT "Green Brick" Season sets
    - Dragon Ball Movie Complete Collection (4-pack)
    - Dragon Ball Z Double Features / Movie Collections
    - Funimation Dragon Box Z
    - Pioneer Uncut Movie DVDs
- R2 DVDs:
    - Dragon Box
    - Dragon Box Z
    - Dragon Box GT
    - Dragon Box The Movies

Rip these using [DVDFab](http://www.dvdfab.cn/) or similar.  <b>Rip to folders, not .ISOs!</b>  It's very important that the folders have the original names of the discs, e.g. `DRAGON_BALL_Z_S4_D2`

#### Directories

Once you have the DVDs ripped, create a folder structure like the following, with the ripped DVD folders inside:
```
Top folder (wherever you want, e.g. C:\dragonball)
│
├───DB
│   ├───R1
│   │   ├───DRAGON_BALL_S1_D1
│   │   └───etc...
│   └───R2
│       ├───DB_1
│       └───etc...
├──DBZ
│   ├───R1
│   │   ├───DBZ_SEASON01_DISC1
│   │   └───etc...
│   ├───R2
│   │   ├───DBZ1_1
│   │   └───etc..
│   └───R1_DBOX
│       ├───DRAGON_BOX_S1_D1
│       └───etc..
├───DBGT
│   ├───R1
│   │   ├───DRAGON_BALL_GT_S1_D1
│   │   └───etc...
│   └───R2
│       ├───DBGT_01
│       └───etc...
└───MOVIES
    ├───R1
    │   ├───DRAGON_BALL_Z_DEAD_ZONE
    │   └───etc...
    ├───R2
    │   ├───DSSD10371
    │   └───etc...
    └───PIONEER
        ├───DEAD_ZONE
        ├───WORLDS_STRONGEST
        └───TREE_OF_MIGHT
```
<b>NOTE:</b> For the Bardock and Trunks DVDs, even though they are part of the movie releases, put those in the `DBZ/R1` folder.

## Usage

#### Preparation / Configuration
1. Download and unzip Dragon Radar
2. Configure `dragon-radar.ini` with the appropriate values:
    - `source_dir` - path where your discs are located (see [Directories](#directories))
    - `output_dir` - path where you want your finished .mkv files to go
    - `pgcdemux` - path to PGCdemux
    - `vsrip` - path to VSRip
    - `delaycut` - path to DelayCut
    - `dgindex` - path to DGIndex.exe in the DGMPGDec package
    - `restream` - path to ReStream

<b>NOTE:</b> Dragon Radar makes extensive use of large (>1GB) temporary files. If your operating system is installed on a SSD, you may want to set your Windows temporary folder to a directory on another drive to lessen I/O to the SSD.

#### Running It
Open a command prompt in the Dragon Radar directory, and run

#### `dragon-radar --series <series> --episode <number>`

where `<series>` is the desired series (DB, DBZ, DBGT) and `<number>` is the episode number.

- Example command:
    - `dragon-radar --series DBZ --episode 75`
- You can do a range of episodes by doing `--episode <start>:<end>`, for example:
    - `dragon-radar --series DBZ --episode 75:107`
- Movies are done like this:
    - `dragon-radar --series DBZ --movie 6`
- The Z specials are specially labeled episodes `bardock` and `trunks`, and the GT special is `special`.  Run them using `--episode`. For example:
    - `dragon-radar --series DBGT --episode special`
    
Use `dragon-radar --help` for full usage instructions.

## How it works!
1. Demultiplex from DVD
    - Demultiplex audio &amp; video with PGCdemux
    - Demultiplex &amp; convert subtitles to VobSub format using VSRip
2. Retime subtitles and audio
    - Retime subtitles by changing the VobSub timestamps using frame differences between R1/R2
    - Retime audio with DelayCut using frame differences, retiming is lossless since Delaycut uses nearest AC3 frame
3. Multiplex to MKV
    - Use mkvmerge to multiplex R2 video, R2 audio, retimed R1 audio, and retimed R1 subtitles to an MKV file with chapters

## Thanks
- <b>Harry Price</b> & <b>dbzj14</b> for helping collect the R1 Dragon Box DVD structure info.
- <b>Clutchins</b> for basically being my QC guy, finding bugs & usability issues.

## Future Improvements & Maybes
- Web-based GUI
    - For the less technical folks
- Support to sync the early 2000s DBZ uncut single DVDs.
    - These are complex to demux because of their weird and crappy authoring.
- Reconstruct original edited DBZ Saiyan & Namek episodes with Dragon Box footage.
    - Probably not going to happen -- because so many scenes are sped-up, this would require either additional video encoding, or creating a weird mixture of DBox and single DVD footage.
