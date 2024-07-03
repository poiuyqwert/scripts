
import sys, re, os, subprocess

args = list(sys.argv)
if args[0].endswith('.py'):
    del args[0]

path = args[0]
if not os.path.exists(path):
    print("'{0}' does not exist".format(path))
    sys.exit()

execute = args[-1] == '-e'

def tracks_from_cue(cue_path):
    with open(cue_path, 'r') as f:
        cue = f.read()

    RE_TRACK = re.compile(r'TRACK (\d+) AUDIO\s*TITLE "([^"]+)".+?(\d+):(\d+):(\d+)', re.S)

    tracks = []
    for match in RE_TRACK.finditer(cue):
        index, title, minutes, seconds, milliseconds = match.groups()
        # minutes, seconds, milliseconds = int(minutes), int(seconds), int(milliseconds)
        # hours = int(minutes / 60)
        # minutes = minutes % 60
        # print('%02d:%02d:%02d - %s' % (hours, minutes, seconds, title))
        start_seconds = int(minutes) * 60 + int(seconds)
        tracks.append({
            'index': int(index),
            'start': float(start_seconds),
            'end': None,
            'title': title
        })
    return tracks

def tracks_from_ffprobe(m4b_path):
    command = ['ffprobe', m4b_path]
    result = subprocess.run(command, capture_output=True, text=True)
    probe = result.stdout or result.stderr

    RE_TRACK = re.compile(r'Chapter #0:(\d+): start ([\d\.]+), end ([\d\.]+).+?title\s+:\s+([^\n]+)', re.S)

    tracks = []
    for match in RE_TRACK.finditer(probe):
        index, start_seconds, end_seconds, title = match.groups()
        tracks.append({
            'index': int(index),
            'start': float(start_seconds),
            'end': float(end_seconds),
            'title': title
        })
    return tracks

def sort(tracks):
    return sorted(tracks, key=lambda track: track['index'])

def fix_endings(only_empty=False):
    def fix_endings(tracks):
        for n in range(len(tracks)-1):
            tracks[n]['end'] = tracks[n+1]['start']
        tracks[-1]['end'] = None
        return tracks
    return fix_endings

def set_titles(titles):
    def set_titles_(tracks):
        for n, track in enumerate(tracks):
            track[n]['title'] = titles[n]
        return tracks  
    return set_titles_

def join_short(min_dur):
    def join_short_(tracks):
        n = 1
        while n < len(tracks):
            track = tracks[n]
            if not track['end']:
                    n += 1
                    continue
            if track['end'] - track['start'] < min_dur:
                    tracks[n-1]['end'] = track['end']
                    del tracks[n]
            else:
                    n += 1
        return tracks
    return join_short_

def concat_tracks(indexes):
    def concat_track_(tracks):
        o = 0
        for i in indexes:
            n = i - o
            tracks[n-1]['end'] = tracks[n]['end']
            del tracks[n]
            o += 1
        return tracks
    return concat_track_

def reindex(tracks):
    for n, track in enumerate(tracks):
        track['index'] = n
    return tracks

def secs(h,m,s):
    return s + (m + (h * 60)) * 60
def add_split(seconds: float, title1: str | None = None, title2: str | None = None):
    def add_split_(tracks):
        for n in range(len(tracks)):
            if seconds > tracks[n]['start'] and (tracks[n]['end'] is None or seconds < tracks[n]['end']):
                new_track = dict(tracks[n])
                new_track['end'] = seconds
                if title1:
                    new_track['title'] = title1
                tracks[n]['start'] = seconds
                if title2:
                    tracks[n]['title'] = title2
                tracks.insert(n, new_track)
                break
        return tracks
    return add_split_

class Titleizer:
    def match(self, track, count):
        return False
    def update(self, track):
        return track
class TSet(Titleizer):
    def __init__(self, title, index=None):
        self.title = title
        self.index = index
        self.matched = False
    def match(self, track, count):
        if self.index is None:
            if self.matched:
                return False
            self.matched = True
            return True
        if self.index < 0:
            self.index += count
        return track['index'] == self.index
    def update(self, track):
        track['title'] = self.title
        return track
class TNumber(Titleizer):
    def __init__(self, prefix='Chapter', number=1):
        self.prefix = prefix
        self.number = number
    def match(self, track, count):
        return True
    def update(self, track):
        track['title'] = f'{self.prefix} {self.number}'
        self.number += 1
        return track
def titleize(defs: list[Titleizer]):
    def titleize_(tracks):
        active: Titleizer | None = None
        next: Titleizer = defs.pop(0)
        for n in range(len(tracks)):
            track = tracks[n]
            if next and next.match(track, len(tracks)):
                active = next
                next = defs.pop(0) if defs else None
            if active:
                tracks[n] = active.update(track)
        return tracks
    return titleize_

def only_keep(indexes, offset=1):
    def only_keep_(tracks):
        return list(track for track in tracks if track['index']+offset in indexes)
    return only_keep_

def trim(seconds):
    def trim_(tracks):
        if seconds < 0:
            tracks[-1]['end'] += seconds
        else:
            tracks[0]['start'] += seconds
        return tracks
    return trim_

modifiers = [
    sort,
    # fix_endings(),
    add_split(26),
    trim(2)
    # add_split(36),
    # add_split(secs(5,51,45) - 52),
    # trim(4),
    # reindex,
    # titleize([
    #     TSet('Intro'),
    #     TSet('Preface'),
    #     TNumber(),
    #     TSet('Outro', -1)
    # ]),
    # only_keep([38])
]

tracks = tracks_from_ffprobe(path)
# tracks = tracks_from_cue(path)
for modifier in modifiers:
    tracks = modifier(tracks)

output_dir = os.path.dirname(path)

zero_pad = max(len(str(len(tracks))), 2)
for track in tracks:
    command = ['ffmpeg', '-ss', '%d' % track['start'], '-i', path, '-vn', '-c:a', 'libmp3lame', '-q:a', '0']
    if track['end'] != None:
        command.extend(['-to', '%d' % (track['end'] - track['start'])])
    command.append(os.path.join(output_dir, ('%%0%dd' % zero_pad + ' - %s.mp3') % (track['index'] + 1, track['title'])))
    print(' '.join(command))
    if execute:
        print(subprocess.run(command))
    # if n == 3:
    #     break

if not execute:
    print("WARNING: This was only a dry run, use the '-e' flag to execute")
