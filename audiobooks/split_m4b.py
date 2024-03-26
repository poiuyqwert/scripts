
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

def set_names(names):
    def set_names_(tracks):
        for n, track in enumerate(tracks):
            track[n] = names[n]
        return tracks  
    return set_names_

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

modifiers = [
    sort,
    fix_endings(),
    # join_short(1000),
    # concat_tracks([5, 10, 12]),
    # reindex
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
