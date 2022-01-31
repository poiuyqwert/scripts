
import sys, os, re

args = list(sys.argv)
if args[0].endswith('.py'):
	del args[0]

path = args[0]
if not os.path.exists(path):
	print("'{0}' does not exist".format(path))
	sys.exit()

execute = args[-1] == '-e'

def dictize(names):
	return [{'orig': name, 'name': name} for name in names]

def split_ext(files):
	for file in files:
		file['name'],file['ext'] = os.path.splitext(file['name'])
	return files
def join_ext(files):
	for file in files:
		file['name'] += file['ext']
		del file['ext']
	return files

def filter_re(regexp, keep):
	regex = re.compile(regexp)
	def should_keep(name):
		match = regex.match(name)
		return (match and keep) or (not match and not keep)
	def filter_re_(files):
		return [file for file in files if should_keep(file['name'])]
	return filter_re_

def sort_names(files):
	return sorted(files, key=lambda file: file['name'])

def numerate(files):
	size = len(str(len(files)))
	def num(n):
		return '0' * (size-len(str(n))) + str(n)
	for n,file in enumerate(files):
		file['name'] = num(n) + ' - ' + file['name']
	return files

def replace_re(regexp, sub):
	regex = re.compile(regexp)
	def remove_re_(files):
		for file in files:
			file['name'] = regex.sub(sub, file['name'])
		return files
	return remove_re_

def append(string):
	def append_(files):
		for file in files:
			file['name'] += string
		return files
	return append_
def append_from(names, sep=''):
	def append_from_(files):
		for file,name in zip(files, names):
			file['name'] += sep + name
		return files
	return append_from_

RE_EPISODE = re.compile(r'[sS](\d+)[eE](\d+)')
def fix_episode(hyphenate=False):
	def fix_episode_(files):
		for file in files:
			file['name'] = RE_EPISODE.sub(lambda m: '%ss%02de%02d%s' % ('- ' if hyphenate else '', int(m.group(1)), int(m.group(2)), ' -' if hyphenate else ''), file['name'])
		return files
	return fix_episode_
def extract_episode(files):
	for file in files:
		match = RE_EPISODE.search(file['name'])
		if not match:
			raise Exception("Missing episode in '%s'" % file['name'])
		file['season'] = int(match.group(1))
		file['episode'] = int(match.group(2))
	return files
def append_episode(hyphenate=True):
	def append_episode_(files):
		for file in files:
			file['name'] += '%ss%02de%02d%s' % ('- ' if hyphenate else '', file['season'], file['episode'], ' -' if hyphenate else '')
		return files
	return append_episode_

def set_name(name):
	def set_(files):
		for file in files:
			file['name'] = name
		return files
	return set_

modifiers = [
	filter_re(r'^\.', False),
	filter_re(r'.+\.srt$', True),
	split_ext,
	extract_episode,
	set_name('Game of Thrones '),
	append_episode(),
	append(' '),
	sort_names,
	append_from(["Winterfell", "A Knight of the Seven Kingdoms", "The Long Night", "The Last of the Starks", "The Bells", "The Iron Throne"]),
	# replace_re(r'1080p WEBRip DD 5\.1-LOKI-M2Tv', ''),
	# fix_episode(True),
	# sort_names,
	# replace_re(r'\.', ' '),
	# append_from(["Dragonstone", "Stormborn", "The Queen's Justice", "The Spoils of War", "Eastwatch", "Beyond the Wall", "The Dragon and the Wolf"]),
	append('.eng'),
	join_ext,
]

files = dictize(os.listdir(path))
for modifier in modifiers:
	files = modifier(files)

for file in files:
	print("""Rename
	{0}
To
	{1}
""".format(file['orig'], file['name']))
	if file['name'] != file['orig'] and execute:
		os.rename(os.path.join(path, file['orig']), os.path.join(path, file['name']))

if not execute:
	print("WARNING: This was only a dry run, use the '-e' flag to execute")
