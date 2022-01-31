
import sys, os, re

args = list(sys.argv)
if args[0].endswith('.py'):
	del args[0]

path = args[0]
if not os.path.exists(path):
	print("'{0}' does not exist".format(path))
	sys.exit()

execute = args[-1] == '-e'

p, book = os.path.split(path.rstrip(os.path.sep))
_, series = os.path.split(p)

def tupleize(names):
	return [(name, name) for name in names]

def remove_dotfiles(names):
	return [(o, name) for o,name in names if not o.startswith('.')]

def keep_mp3s(names):
	return [(o, name) for o,name in names if o.endswith('.mp3')]

def sort_names(names):
	return sorted(names, key=lambda e: e[1])

def remove_ext(names):
	return [(o, os.path.splitext(name)[0]) for o,name in names]

RE_HYPHEN = re.compile(r'\s*-\s*')
def extract_name(names):
	return [(o, RE_HYPHEN.split(name)[-1]) for o,name in names]

modifiers = [
	tupleize,
	remove_dotfiles,
	keep_mp3s,
	sort_names,
	remove_ext,
	extract_name
]

names = os.listdir(path)
for modifier in modifiers:
	names = modifier(names)

tracks = len(names)

for track,(filename,name) in enumerate(names, 1):
	command = 'id3tag --artist="{0}" --album="{1}" --song="{2}" --track={3} --total={4} "{5}"'.format(series, book, name, track, tracks, os.path.join(path, filename))
	print(command)
	if execute:
		os.system(command)

if not execute:
	print("WARNING: This was only a dry run, use the '-e' flag to execute")