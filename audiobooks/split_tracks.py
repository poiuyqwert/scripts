
import sys, re, os, subprocess
from typing import Callable

args = list(sys.argv)
if args[0].endswith('.py'):
    del args[0]

path = args[0]
if not os.path.exists(path):
    print("'{0}' does not exist".format(path))
    sys.exit()

execute = args[-1] == '-e'

def fix_endings(tracks, duration):
    for n in range(len(tracks)-1):
        tracks[n]['end'] = tracks[n+1]['start']
    tracks[-1]['end'] = duration
    return tracks

def parse_cue(cue):
    RE_TRACK = re.compile(r'TRACK (\d+) AUDIO\s+(?:: +)?TITLE "([^"]+)"\s+(?:: +)?INDEX \d+ (\d+):(\d+):(\d+)', re.S)

    tracks = []
    for match in RE_TRACK.finditer(cue):
        index, title, minutes, seconds, frames = match.groups()
        start_seconds = int(minutes) * 60 + int(seconds) #+ int(frames) / 75.0
        tracks.append({
            'index': int(index),
            'start': float(start_seconds),
            'end': None,
            'title': title
        })
    return tracks

def tracks_from_cue(cue_path):
    with open(cue_path, 'r') as f:
        cue = f.read()

    return parse_cue(cue)

def tracks_from_m4b(m4b_path):
    command = ['ffprobe', m4b_path]
    result = subprocess.run(command, capture_output=True, text=True)
    probe = result.stdout or result.stderr

    RE_TRACK = re.compile(r'Chapter #0:(\d+): start ([\d\.]+), end ([\d\.]+)[^:]+?:\s+title +: +([^\n]+)?', re.S)

    tracks = []
    for match in RE_TRACK.finditer(probe):
        index, start_seconds, end_seconds, title = match.groups()
        tracks.append({
            'index': int(index),
            'start': float(start_seconds),
            'end': float(end_seconds),
            'title': title or 'NA'
        })
    return tracks

def tracks_from_mp3(mp3_path):
    command = ['ffprobe', mp3_path]
    result = subprocess.run(command, capture_output=True, text=True)
    probe = result.stdout or result.stderr

    cue_path = os.path.splitext(path)[0] + os.extsep + 'cue'
    if os.path.exists(cue_path):
        tracks = tracks_from_cue(cue_path)
    else:
        tracks = parse_cue(probe)

    RE_DURATION = re.compile(r'^ +Duration: (\d+):(\d+):(\d+)', re.M)
    match = RE_DURATION.search(probe)
    duration = (int(match.group(1)) * 60 + int(match.group(2))) * 60 + int(match.group(3))

    tracks = fix_endings(tracks, duration)
    return tracks

def sort(tracks):
    return sorted(tracks, key=lambda track: track['index'])

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

def join_tracks(start_index: int, count: int = 2):
    def join_track_(tracks):
        end_index = start_index + count - 1
        tracks[start_index]['end'] = tracks[end_index]['end']
        for n in range(end_index, start_index, -1):
            del tracks[n]
        return tracks
    return join_track_

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
class Counter:
    def __init__(self, number=1):
        self.number = number
    def touch(self):
        number = self.number
        self.number += 1
        return number
class TNumber(Titleizer):
    def __init__(self, prefix='Chapter', counter=Counter(), names: list[str] | None = None):
        self.prefix = prefix
        self.counter = counter
        self.names = names
    def match(self, track, count):
        return True
    def update(self, track):
        n = self.counter.touch()
        track['title'] = f'{self.prefix} {n}'
        if self.names and n <= len(self.names):
            track['title'] += f' - {self.names[n-1]}'
        return track
class TTransform(Titleizer):
    def __init__(self, title_transform: Callable[[str], str] | None = None, index: int | None = None):
        self.title_transform = title_transform
        self.index = index
    def match(self, track, count):
        if self.index == None:
            return True
        if self.index < 0:
            self.index += count
        return track['index'] == self.index
    def update(self, track):
        if self.title_transform:
            track['title'] = self.title_transform(track['title'])
        return track
def titleize(defs: list[Titleizer]):
    def titleize_(tracks: list[dict]) -> list[dict]:
        active: Titleizer | None = None
        next: Titleizer | None = defs.pop(0)
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

def drop(indexes, offset=1):
    def drop_(tracks):
        ids = list((i if i > 0 else i + len(tracks)) for i in indexes)
        return list(track for track in tracks if track['index']-offset not in ids)
    return drop_

def trim(seconds):
    def trim_(tracks):
        if seconds < 0:
            tracks[-1]['end'] += seconds
        else:
            tracks[0]['start'] += seconds
        return tracks
    return trim_

def trim_track(track_n: int, seconds: float):
    def trim_track_(tracks):
        if seconds < 0:
            tracks[track_n]['end'] += seconds
        else:
            tracks[track_n]['start'] += seconds
        return tracks
    return trim_track_

def split_track(track_n: int, seconds: float, title1: str | None = None, title2: str | None = None):
    def split_track_(tracks):
        new_track = dict(tracks[track_n])
        if seconds < 0:
            new_track['end'] += seconds
        else:
            new_track['end'] = new_track['start'] + seconds
        if title1:
            new_track['title'] = title1
        if seconds < 0:
            tracks[track_n]['start'] = tracks[track_n]['end'] + seconds
        else:
            tracks[track_n]['start'] += seconds
        if title2:
            tracks[track_n]['title'] = title2
        tracks.insert(track_n, new_track)
        return tracks
    return split_track_

def shift(track_n: int, seconds: float):
    def shift_(tracks):
        if seconds < 0:
            tracks[track_n+1]['start'] += seconds
            tracks[track_n]['end'] += seconds
        else:
            tracks[track_n-1]['end'] += seconds
            tracks[track_n]['start'] += seconds
        return tracks
    return shift_

counter = Counter()
modifiers = [
    sort,
    trim(3),
    trim(-2),
    shift(3, 1),
    shift(28, 1),
    only_keep([28,29])
]

if path.endswith('m4b'):
    tracks = tracks_from_m4b(path)
else:
    tracks = tracks_from_mp3(path)

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

if not execute:
    print("WARNING: This was only a dry run, use the '-e' flag to execute")
