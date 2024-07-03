
import sys, re, os, subprocess, math

args = list(sys.argv)
if args[0].endswith('.py'):
    del args[0]

path = args[0]
if not os.path.exists(path):
    print("'{0}' does not exist".format(path))
    sys.exit()

execute = args[-1] == '-e'

def duration_from_ffprobe(file_path):
    command = ['ffprobe', file_path]
    result = subprocess.run(command, capture_output=True, text=True)
    probe = result.stdout or result.stderr
    
    RE_DURATION = re.compile(r'Duration: (\d\d):(\d\d):(\d\d\.\d+)', re.S)
    
    match = RE_DURATION.search(probe)
    
    return float(match.group(3)) + (int(match.group(2)) + int(match.group(1)) * 60) * 60
 
pieces_duration = 30 * 60

duration = duration_from_ffprobe(path)
pieces_count = math.ceil(duration / float(pieces_duration))


output_dir = os.path.dirname(path)

zero_pad = max(len(str(pieces_count)), 2)
def output_file_path(n):
    global zero_pad
    return os.path.join(output_dir, ('-%%0%dd.mp3' % zero_pad) % n)

start = 0
offset = 0
while os.path.exists(output_file_path(1+offset)):
    offset += 1
for n in range(1, pieces_count+1):
    command = ['ffmpeg', '-ss', '%d' % start, '-i', path, '-vn', '-c:a', 'libmp3lame', '-q:a', '0']
    if n != pieces_count:
        command.extend(['-to', '%d' % pieces_duration])
    command.append(output_file_path(n + offset))
    print(' '.join(command))
    if execute:
        print(subprocess.run(command))
    start += pieces_duration
