from utils import (timestamp_to_seconds,
                   seconds_to_timestamp,
                   frame_to_seconds)


class Subtitle(object):

    def __init__(self, series, episode_offsets, op_offset):
        self.series = series
        self.offsets = episode_offsets
        self.op_offset = op_offset
        self.orig_file = ''
        self.fixed_file = ''

    def _adjust_timecode(self, timestamp):
        '''
        Offset a timecode by the total number of offset frames
        '''
        frame = timestamp_to_seconds(timestamp)

        # calculate offset from frame data
        if isinstance(self.offsets, list):
            # for list-types (movies, not episodes), start with 0 offset
            total_offset = 0
            for o in self.offsets:
                if frame > frame_to_seconds(o['frame']):
                    total_offset += frame_to_seconds(o['offset'])
        else:
            # for episodes, start with the OP offset
            total_offset = frame_to_seconds(self.op_offset)
            for key in self.offsets.keys():
                # orange bricks have a 1.5 second delay on the OP subs
                if (self.series == 'DBZOB' and
                        key == 'prologue' and
                        frame < frame_to_seconds(self.offsets[key]["frame"])):
                    total_offset += 1.5
                if frame > frame_to_seconds(self.offsets[key]["frame"]):
                    total_offset += frame_to_seconds(
                        self.offsets[key]["offset"])
        # apply offset to subtitle timing
        frame -= total_offset

        return seconds_to_timestamp(frame)

    def retime_vobsub(self):
        try:
            with open(
                    self.orig_file, 'r') as file_in, open(
                    self.fixed_file, 'w') as file_out:
                for line in file_in:
                    if 'timestamp: ' in line:
                        sub_parts = line.split(',')
                        sub_time = sub_parts[0].split('timestamp: ')[1].strip()
                        retimed = self._adjust_timecode(sub_time)
                        sub_parts[0] = 'timestamp: ' + retimed
                        file_out.write(','.join(sub_parts))
                    else:
                        file_out.write(line)
        except IOError as e:
            print e

    def patch_substation(self):
        pass
