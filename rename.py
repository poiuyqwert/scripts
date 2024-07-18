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

def sort_adjust(start_names, end_names, key='name'):
	def sort_adjust_(files):
		start = []
		mid = []
		end = []
		for file in files:
			if file[key] in start_names:
				start.append(file)
			elif file[key] in end_names:
				end.append(file)
			else:
				mid.append(file)
		start = sorted(start, key=lambda file: start_names.index(file[key]))
		mid = sorted(mid, key=lambda file: file[key])
		end = sorted(end, key=lambda file: end_names.index(file[key]))
		return start + mid + end
	return sort_adjust_

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

def extract(regex, key, process=None, required=True):
	regex = re.compile(regex)
	def extract_(files):
		for file in files:
			match = regex.search(file['name'])
			if not match and required:
				raise Exception("Missing '%s' in '%s'" % (key, file['name']))
			file[key] = match.group(1)
			if process:
				file[key] = process(file[key])
		return files
	return extract_
def append_extracted(key, form='%s', required=True):
	def append_extracted_(files):
		for file in files:
			if not key in file:
				if required:
					raise Exception("Missing '%s' in '%s'" % (key, file['name']))
				continue
			file['name'] += form % file[key]
		return files
	return append_extracted_

RE_EPISODE = re.compile(r'(?:[sS]|Season)\s*(\d+)\s*(?:[eE]|Episode|Extra|Deleted Scenes)\s*(\d+)(?:(?:-e|\s*&\s*)(\d+))?')
def fix_episode(regex=RE_EPISODE, process=None, hyphenate=False):
	if isinstance(regex, str):
		regex = re.compile(regex)
	def fix_episode_(files):
		def replace_episode(match):
			season, episode, episode_end = int(match.group(1)), int(match.group(2)), None
			if match.group(3):
				episode_end = int(match.group(3))
			if process:
				season, episode, episode_end = process(season, episode, episode_end)
			return '%ss%02de%02d%s%s' % ('- ' if hyphenate else '', season, episode, ('-e%02d' % episode_end) if episode_end != None else '', ' -' if hyphenate else '')
		for file in files:
			file['name'] = regex.sub(replace_episode, file['name'])
		return files
	return fix_episode_
def extract_episode(regex=RE_EPISODE):
	if isinstance(regex, str):
		regex = re.compile(regex)
	def extract_episode_(files):
		for file in files:
			match = regex.search(file['name'])
			if not match:
				raise Exception("Missing episode in '%s'" % file['name'])
			file['season'] = int(match.group(1))
			file['episode'] = int(match.group(2))
			if match.group(3):
				file['episode_end'] = int(match.group(3))
		return files
	return extract_episode_
def append_episode(hyphenate=True):
	def append_episode_(files):
		for file in files:
			file['name'] += '%ss%02de%02d' % (' - ' if hyphenate else '', file['season'], file['episode'])
			if 'episode_end' in file:
				file['name'] += '-e%02d' % file['episode_end']
			if hyphenate:
				file['name'] += ' - '
		return files
	return append_episode_
def adjust_episode(process):
	def modify_episode_(files):
		for file in files:
			file['season'], file['episode'], file['episode_end'] = process(file['season'], file['episode'], file.get('episode_end'))
		return files
	return modify_episode_

def season_from_episode(episode_counts):
	def season_from_episode_(files):
		for file in files:
			for season, episode_count in enumerate(episode_counts, 1):
				if file['episode'] > episode_count:
					file['episode'] -= episode_count
					if 'episode_end' in file:
						file['episode_end'] -= episode_count
				else:
					file['season'] = season
					break
			else:
				raise Exception("Couldn't find season for '%s'" % file['name'])
		return files
	return season_from_episode_

RE_EPISODE_NAME = re.compile(r'.+?- (.+)$')
def extract_episode_name(regex=RE_EPISODE_NAME):
	if isinstance(regex, str):
		regex = re.compile(regex)
	def extract_episode_name_(files):
		for file in files:
			match = regex.search(file['name'])
			if not match:
				raise Exception("Missing episode name in '%s'" % file['name'])
			file['episode_name'] = match.group(1)
		return files
	return extract_episode_name_
def append_episode_name(hyphenate=True):
	def append_episode_name_(files):
		for file in files:
			file['name'] += '%s%s' % (' - ' if hyphenate else '', file['episode_name'])
		return files
	return append_episode_name_

def set_name(name):
	def set_(files):
		for file in files:
			file['name'] = name
		return files
	return set_

def check(file_condition, action):
	def check_(files):
		for file in files:
			if file_condition(file):
				action([file])
		return files
	return check_

def custom(files):
	for n, file in enumerate(files):
		file['episode'] = '%d%02d' % (file['season'], n)
	return files

modifiers = [
	filter_re(r'^\.', False),
	# filter_re(r'.+\.srt$', True),
	sort_names,
	split_ext,
	replace_re(r'\.', ' '),
	fix_episode(hyphenate=True),
	replace_re(r' 1080p.+', ''),
	join_ext,
]

files = dictize(file for file in os.listdir(path) if not os.path.isdir(os.path.join(path,file)))
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
