"""Build local dictionary from OpenCorpora; source and license in dist/vendor/NAMES-LICENSE.txt."""
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).parent / '.names-deps'))
import pymorphy3
m=pymorphy3.MorphAnalyzer()
tags={}
for pid,p in enumerate(m.dictionary.paradigms):
    for idx in range(len(p)//3):
        tag=m.dictionary.build_tag_info(pid,idx)
        kind='surname' if 'Surn' in tag else 'given' if 'Name' in tag else None
        if kind and 'nomn' in tag: tags[(pid,idx)]=kind
result={'surname':set(),'given':set()}
for word,pair in m.dictionary.words.iteritems():
    kind=tags.get(pair)
    if kind: result[kind].add(word.replace('ё','е'))
result['unambiguous']={w for w in result['surname'] if all('Surn' in m.dictionary.build_tag_info(*pair) for pair in m.dictionary.words.get(w,[]))}
Path('dist/vendor/names.json').write_text(json.dumps({k:sorted(v) for k,v in result.items()},ensure_ascii=False),encoding='utf-8')
print({k:len(v) for k,v in result.items()})
