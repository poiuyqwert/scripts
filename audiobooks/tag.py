
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

def dictize(files):
	return [{'filename': name, 'name': name} for name in files]

def remove_dotfiles(files):
	return [file for file in files if not file['filename'].startswith('.')]

def keep_mp3s(files):
	return [file for file in files if file['filename'].endswith('.mp3')]

def sort_names(files):
	return sorted(files, key=lambda file: file['name'])

def remove_ext(files):
	for file in files:
		file['name'] = os.path.splitext(file['name'])[0]
	return files

RE_NAME = re.compile(r'(\d+)\s*-\s*(.+)')
def split_name(files):
	for file in files:
		match = RE_NAME.match(file['name'])
		if not match:
			raise Exception('Name not in "id - name" format')
		file['index'] = int(match.group(1))
		file['name'] = match.group(2)
	return files

def sort_indexes(files):
	return sorted(files, key=lambda file: file['index'])

def check_missing_or_dupes(files):
	ids = set()
	next_index = 1
	for file in files:
		if file['index'] in ids:
			raise Exception(f'Index {file["index"]} exists twice')
		if file['index'] != next_index:
			raise Exception(f'Skipped index {next_index}')
		next_index += 1
	return files

modifiers = [
	remove_dotfiles,
	keep_mp3s,
	remove_ext,
	split_name,
	sort_indexes,
	check_missing_or_dupes,
]

files = dictize(os.listdir(path))
for modifier in modifiers:
	files = modifier(files)

tracks = len(files)

for file in files:
	command = 'id3tag --artist="{0}" --album="{1}" --song="{2}" --track={3} --total={4} "{5}"'.format(series, book, file['name'], file['index'], tracks, os.path.join(path, file['filename']))
	print(command)
	if execute:
		os.system(command)

if not execute:
	print("WARNING: This was only a dry run, use the '-e' flag to execute")