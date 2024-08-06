from __future__ import annotations
import sys, re, os, subprocess, hashlib, json
from typing import Callable, TypedDict

args = list(sys.argv)
if args[0].endswith('.py'):
    del args[0]

path = args[0]
if not os.path.exists(path):
    print("'{0}' does not exist".format(path))
    sys.exit()

execute = args[-1] == '-e'

class Track(TypedDict):
    index: int
    title: str
    start: float
    end: float

def fix_endings(tracks: list[Track], duration: float):
    for n in range(len(tracks)-1):
        tracks[n]['end'] = tracks[n+1]['start']
    tracks[-1]['end'] = duration
    return tracks

def parse_cue(cue) -> list[Track]:
    RE_TRACK = re.compile(r'TRACK (\d+) AUDIO\s+(?:: +)?TITLE "([^"]+)"\s+(?:: +)?INDEX \d+ (\d+):(\d+):(\d+)', re.S)

    tracks: list[Track] = []
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

def tracks_from_cue(cue_path) -> list[Track]:
    with open(cue_path, 'r') as f:
        cue = f.read()

    return parse_cue(cue)

def tracks_from_m4b(m4b_path) -> list[Track]:
    command = ['ffprobe', m4b_path]
    result = subprocess.run(command, capture_output=True, text=True)
    probe = result.stdout or result.stderr

    RE_TRACK = re.compile(r'Chapter #0:(\d+): start ([\d\.]+), end ([\d\.]+)[^:]+?:\s+title +: +([^\n]+)?', re.S)

    tracks: list[Track] = []
    for match in RE_TRACK.finditer(probe):
        index, start_seconds, end_seconds, title = match.groups()
        tracks.append({
            'index': int(index),
            'start': float(start_seconds),
            'end': float(end_seconds),
            'title': title or 'NA'
        })
    return tracks

def tracks_from_mp3(mp3_path) -> list[Track]:
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
    if not match:
        raise Exception("Couldn't find mp3 duration")
    duration = (int(match.group(1)) * 60 + int(match.group(2))) * 60 + int(match.group(3))

    if len(tracks):
        tracks = fix_endings(tracks, duration)
    else:
        tracks.append({
            'index': 0,
            'start': 0,
            'end': duration,
            'title': os.path.splitext(os.path.basename(path))[0]
        })
    return tracks

def sort(tracks: list[Track]) -> list[Track]:
    return sorted(tracks, key=lambda track: track['index'])

def set_titles(titles):
    def set_titles_(tracks) -> list[Track]:
        for n, track in enumerate(tracks):
            track[n]['title'] = titles[n]
        return tracks  
    return set_titles_

def join_short(min_dur):
    def join_short_(tracks: list[Track]) -> list[Track]:
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
    def join_track_(tracks: list[Track]) -> list[Track]:
        end_index = start_index + count - 1
        tracks[start_index]['end'] = tracks[end_index]['end']
        for n in range(end_index, start_index, -1):
            del tracks[n]
        return tracks
    return join_track_

def reindex(base: int):
    def reindex_(tracks: list[Track]) -> list[Track]:
        for n, track in enumerate(tracks):
            track['index'] = base + n
        return tracks
    return reindex_

def secs(h,m,s):
    return s + (m + (h * 60)) * 60
def add_split(seconds: float, title1: str | None = None, title2: str | None = None):
    def add_split_(tracks: list[Track]) -> list[Track]:
        for n in range(len(tracks)):
            if seconds > tracks[n]['start'] and (tracks[n]['end'] is None or seconds < tracks[n]['end']):
                new_track: Track = tracks[n].copy()
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
    def match(self, track: Track, count: int) -> bool:
        return False
    def update(self, track: Track) -> Track:
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
    def titleize_(tracks: list[Track]) -> list[Track]:
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
    def only_keep_(tracks: list[Track]) -> list[Track]:
        return list(track for track in tracks if track['index']+offset in indexes)
    return only_keep_

def drop(indexes, offset=1):
    def drop_(tracks: list[Track]) -> list[Track]:
        ids = list((i if i > 0 else i + len(tracks)) for i in indexes)
        return list(track for track in tracks if track['index']+offset not in ids)
    return drop_

def trim(seconds):
    def trim_(tracks: list[Track]) -> list[Track]:
        if seconds < 0:
            tracks[-1]['end'] += seconds
        else:
            tracks[0]['start'] += seconds
        return tracks
    return trim_

def trim_track(track_n: int, seconds: float):
    def trim_track_(tracks: list[Track]) -> list[Track]:
        if seconds < 0:
            tracks[track_n]['end'] += seconds
        else:
            tracks[track_n]['start'] += seconds
        return tracks
    return trim_track_

def trim_track_to(track_n: int, seconds: float):
    def trim_track_(tracks: list[Track]) -> list[Track]:
        tracks[track_n]['end'] = tracks[track_n]['start'] + seconds
        return tracks
    return trim_track_

def split_track(track_n: int, seconds: float, title1: str | None = None, title2: str | None = None):
    def split_track_(tracks: list[Track]) -> list[Track]:
        new_track = tracks[track_n].copy()
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

def shift_forward(track_n: int, split_at_seconds: float):
    def shift_(tracks: list[Track]) -> list[Track]:
        tracks[track_n-1]['end'] += split_at_seconds
        tracks[track_n]['start'] += split_at_seconds
        return tracks
    return shift_

def shift_back(track_n: int, split_at_seconds: float):
    def shift_(tracks: list[Track]) -> list[Track]:
        duration = tracks[track_n]['end'] - tracks[track_n]['start'] - split_at_seconds
        tracks[track_n+1]['start'] -= duration
        tracks[track_n]['end'] -= duration
        return tracks
    return shift_

def rename(regex, repl: str | Callable[[re.Match[str]], str]):
    def rename_(tracks: list[Track]) -> list[Track]:
        regex_compiled = re.compile(regex)
        for track in tracks:
            track['title'] = regex_compiled.sub(repl, track['title'])
        return tracks
    return rename_

def set_title(track_n: int, title: str):
    def set_title_(tracks: list[Track]) -> list[Track]:
        tracks[track_n]['title'] = title
        return tracks
    return set_title_

counter = Counter()
modifiers: list[Callable[[list[Track]], list[Track]]] = [
    # trim(3),
    # set_title(0, 'Intro'),
    # split_track(0, 11, title2='Dedications'),
    # split_track(1, 7, title2='Chapter 1'),
    # reindex,
    split_track(0, secs(0, 13, 56), 'Chapter 30', 'Outro'),
    reindex(32),
    trim_track(-1, -5),
    # 15,56
]

if path.endswith('m4b'):
    tracks = tracks_from_m4b(path)
else:
    tracks = tracks_from_mp3(path)

for modifier in modifiers:
    tracks = modifier(tracks)

output_dir = os.path.dirname(path)


BUF_SIZE = 65536
def hash_file(path: str) -> hashlib._Hash:
    sha1 = hashlib.sha1()
    with open(path, 'rb') as f:
        while True:
            data = f.read(BUF_SIZE)
            if not data:
                break
            sha1.update(data)
    return sha1

def hash_track(track: Track) -> hashlib._Hash:
    sha1 = hashlib.sha1()
    for (key, value) in sorted(track.items(), key=lambda kv: kv[0]):
        sha1.update(key.encode())
        sha1.update(str(value).encode())
    return sha1

class PastInput(TypedDict):
    path: str
    hash: str
class Past(TypedDict):
    input: PastInput
    tracks: list[Track]

past: Past | None = None
try:
    past_path = os.path.join(output_dir, '.past')
    if os.path.exists(past_path):
        with open(past_path, 'r') as f:
            past = json.load(f)
except:
    print("INFO: Couldn't load `.past` file")
    pass

input_changed = True
input_hash = hash_file(path)
if past is not None:
    input_changed = input_hash.hexdigest() != past['input']['hash']

zero_pad = max(len(str(len(tracks))), 2)
for track in tracks:
    output_name = ('%%0%dd' % zero_pad + ' - %s.mp3') % (track['index'] + 1, track['title'])
    output_path = os.path.join(output_dir, output_name)

    track_changed = True
    if os.path.exists(output_path) and past is not None:
        past_track: Track | None = next(filter(lambda t: t['index'] == track['index'], past['tracks']))
        if past_track is not None:
            track_hash = hash_track(track)
            past_hash = hash_track(past_track)
            if track_hash.digest() == past_hash.digest():
                track_changed = False

    if not input_changed and not track_changed:
        print(f"\t'{output_name}' unchanged")
        continue

    command = ['ffmpeg', '-ss', '%.2f' % track['start'], '-i', path, '-vn', '-c:a', 'libmp3lame', '-q:a', '0']
    if track['end'] != None:
        command.extend(['-to', '%.2f' % (track['end'] - track['start'])])
    command.append(output_path)
    print(' '.join(command))
    if execute:
        if os.path.exists(output_path):
            os.unlink(output_path)
        print(subprocess.run(command))

if not execute:
    print("WARNING: This was only a dry run, use the '-e' flag to execute")
else:
    past = {
        'input': {
            'path': path,
            'hash': input_hash.hexdigest()
        },
        'tracks': tracks
    }
    try:
        with open(past_path, 'w') as f:
            json.dump(past, f, indent=2)
    except:
        print("INFO: Couldn't save `.past` file")
        pass
