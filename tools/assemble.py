#!/usr/bin/env python3
"""Assemble src/data.json = src/words.json + the original example sentences in tools/sentences/out-*.json.

Every sentence is checked: it must use its word (as Kiwi reads it, or the word/stem written in it), stay short, and
name nothing from after Pewter City (later names, Pokémon outside species_ok). Failures are listed and left out.
Usage: python3 tools/assemble.py
"""
import collections, glob, json, pathlib, re, sys
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from kor import LATER, LATER_TOKENS, lemmatizer, eojeol_key

ROOT = pathlib.Path(__file__).resolve().parents[1]
WJ = json.loads((ROOT / 'src/words.json').read_text(encoding='utf-8'))
W = {d['w']: d for d in WJ['words']}
sent = {}
for p in sorted(glob.glob(str(ROOT / 'tools/sentences/out-*.json'))):
    sent.update(json.loads(pathlib.Path(p).read_text(encoding='utf-8')))

# Pokémon names that must not appear (every species Moneo knows, minus the ones met by Pewter)
MONEO = pathlib.Path('/var/home/stan/Developer/moneo/app/src/main/assets/moneo/seed-vocab-ko-species.json')
species = {e['korean'].strip() for e in json.loads(MONEO.read_text(encoding='utf-8'))['entries']} if MONEO.exists() else set()
later_species = {s for s in species - set(WJ['species_ok']) if len(s) >= 2}

lemmas = lemmatizer(W)
problems, lines, seen = collections.defaultdict(list), [], set()
for w, d in W.items():
    for s in sent.get(w, []):
        s = s.strip()
        flat, hang = s.replace(' ', ''), len(re.findall('[가-힣]', s))
        lem = lemmas(s)
        stem = w[:-1] if w.endswith('다') else w
        # Kiwi misses some conjugations (아는 → 알다, 계세요 → 계시다): then a word starting like the stem will do
        if not (w in lem or stem in s or any(eojeol_key(e).startswith(stem[0]) for e in s.split())):
            problems['word not found'].append((w, s)); continue
        if not 5 <= hang <= 40 or re.search('[A-Za-z一-鿿]', s):
            problems['length / non-Hangul'].append((w, s)); continue
        bad = [x for x in LATER if x in flat and x != w] + sorted(LATER_TOKENS & lem) + [x for x in later_species if x != w and (x in lem or any(eojeol_key(e).startswith(x) for e in s.split()))]
        if bad:
            problems['later-game name ' + '/'.join(bad)].append((w, s)); continue
        if s in seen:
            continue
        seen.add(s)
        lines.append({'t': s, 'a': d['area'], 'for': w})
    if not sent.get(w):
        problems['no sentences'].append((w, ''))

# tap-a-word: every word as written → dictionary form(s); a line's own word is always findable in it
tap = {}
for l in lines:
    for eoj in l['t'].split():
        k = eojeol_key(eoj)
        if k and k not in tap:
            tap[k] = sorted(lemmas(k) | ({k} if k in W else set()), key=lambda x: -len(x))[:3]
for l in lines:
    w = l['for']
    keys = [eojeol_key(e) for e in l['t'].split()]
    if not any(w in tap.get(k, []) for k in keys):
        stem = w[:-1] if w.endswith('다') else w
        k = next((k for k in keys if stem in k), None) or next((k for k in keys if k.startswith(stem[0])), None)
        if k:
            tap[k] = [w] + [x for x in tap[k] if x != w][:2]

# example lines per word: its own sentences first, then other sentences that use it
ex = collections.defaultdict(list)
for i, l in enumerate(lines):
    ex[l['for']].append(i)
for i, l in enumerate(lines):
    for k in {eojeol_key(e) for e in l['t'].split()}:
        for x in tap.get(k, []):
            if x in W and x != l['for'] and i not in ex[x]:
                ex[x].append(i)
words = []
for w, d in W.items():
    if ex.get(w):
        words.append({**d, 'ex': ex[w][:12]})

out = {'areas': WJ['areas'], 'words': words, 'lines': [{'t': l['t'], 'a': l['a']} for l in lines],
       'hanja': WJ['hanja'], 'tap': tap}
(ROOT / 'src/data.json').write_text(json.dumps(out, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')
print(f"{len(lines)} sentences for {len(words)}/{len(W)} words · per area", dict(sorted(collections.Counter(l['a'] for l in lines).items())))
for why, xs in problems.items():
    print(f'  {why}: {len(xs)}', '; '.join(f'{w}: {s}' for w, s in xs[:8]))
