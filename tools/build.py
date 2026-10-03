#!/usr/bin/env python3
"""Assemble index.html = src/app.html + src/data.json + the shared learner dictionary (lexicon/defs.json)."""
import json, pathlib
root = pathlib.Path(__file__).resolve().parents[1]
data = json.loads((root / 'src/data.json').read_text(encoding='utf-8'))
defs = json.loads((root / 'lexicon/defs.json').read_text(encoding='utf-8'))
need = {w['w'] for w in data['words']} | {l for ls in data['tap'].values() for l in ls}
lex = {'defs': {k: v for k, v in defs.items() if v and k in need}}
html = (root / 'src/app.html').read_text(encoding='utf-8')
html = html.replace('__DATA__', json.dumps(data, ensure_ascii=False, separators=(',', ':'))).replace('__LEX__', json.dumps(lex, ensure_ascii=False, separators=(',', ':')))
(root / 'index.html').write_text(html, encoding='utf-8')
missing = sorted(w['w'] for w in data['words'] if w['w'] not in lex['defs'] and w['cat'] != 'mon')
print(f"built index.html · {len(lex['defs'])} Korean definitions · {len(missing)} deck words still without one")
(root / 'tools/missing-defs.txt').write_text('\n'.join(missing) + '\n', encoding='utf-8')
