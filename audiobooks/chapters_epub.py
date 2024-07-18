
import xml.etree
import xml.etree.ElementTree
import sys, os, zipfile, xml, re

args = list(sys.argv)
if args[0].endswith('.py'):
    del args[0]

path = args[0]
if not os.path.exists(path):
    print("'{0}' does not exist".format(path))
    sys.exit()

epub = zipfile.ZipFile(path)
try:
    toc = epub.read('toc.ncx')
except:
    toc = epub.read('OEBPS/toc.ncx')

root = xml.etree.ElementTree.fromstring(toc.decode('utf-8'))
m = re.match(r'\{[^\}]+\}', root.tag)
if m:
    namespace = m.group(0)
else:
    namespace = ''

navpoints = sorted(root.findall(f'.//{namespace}navPoint'), key=lambda np: int(np.attrib['playOrder']))
names = list(navpoint.find(f'.//{namespace}text').text for navpoint in navpoints)

def drop(indexes):
    def drop_(names):
        ids = sorted([i if i > 0 else len(names) + i for i in indexes], reverse=True)
        for i in ids:
            del names[i]
    return drop_

modifiers = [

]
for modifier in modifiers:
    names = modifier(names)

for name in names:
    print(f'"{name}",')
