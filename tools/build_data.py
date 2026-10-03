#!/usr/bin/env python3
"""Build src/data.json for 도감 여행 from the Moneo project's assets.

Spoiler-free by construction:
  * a word belongs to the area where Moneo says you first meet it, and only POC areas are included;
  * example sentences come only from ROM dialogue attributed to an area the player has reached
    (the client also filters by the player's progress);
  * on top of Moneo's coarse area attribution, a line or word is dropped if it mentions anything from
    later in the game: later place names, other gyms' badges/leaders, the Elite Four, legendaries,
    or a Pokémon species first met in a later area.

Writes src/words.json (no game text). Usage: python3 tools/build_data.py [--moneo ~/Developer/moneo]
"""
import collections, json, pathlib, re, sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
MONEO = pathlib.Path(sys.argv[sys.argv.index('--moneo') + 1] if '--moneo' in sys.argv else '/var/home/stan/Developer/moneo')
A = MONEO / 'app/src/main/assets/moneo'
POC = ['pallet_town', 'route_1', 'viridian_city', 'route_2', 'viridian_forest', 'pewter_city']

areas_meta = {a['id']: a for a in json.load(open(A / 'areas.json', encoding='utf-8'))['areas']}
story = json.load(open(A / 'area_lemma_counts.json', encoding='utf-8'))['storyOrder']
later_places = [areas_meta[a]['koreanLabel'].replace(' ', '') for a in story if a not in POC and a in areas_meta]

from kor import LATER, LATER_TOKENS, lemmatizer, eojeol_key

# ---- words from all four decks ----
DECKS = [('topik', 'word'), ('mined', None), ('etymology', 'root'), ('species', 'mon')]
TECH = {'pokemon_move', 'pokemon_ability', 'item_description', 'trainer_class_name'}
words = {}
species_area = {}
for deck, forced in DECKS:
    for e in json.load(open(A / f'seed-vocab-ko-{deck}.json', encoding='utf-8'))['entries']:
        w = e['korean'].strip()
        a = e.get('firstAreaEncountered')
        if deck == 'species':
            species_area[w] = a
        if not w or w in words:
            continue
        cat = forced or ('mon' if e.get('primarySourceType') == 'pokemon_species'
                         else 'tech' if e.get('primarySourceType') in TECH else 'word')
        words[w] = {'w': w, 'g': e.get('gloss', ''), 'pos': e.get('partOfSpeech', ''), 'cat': cat,
                    'deck': deck, 'note': e.get('notes', '') if deck == 'etymology' else ''}
later_species = {s for s, a in species_area.items() if a not in POC}

def spoils(text, tokens):
    t = text.replace(' ', '')
    if any(p in t for p in later_places) or any(x in t for x in LATER) or LATER_TOKENS & tokens:
        return True
    return any(s in t for s in later_species if len(s) >= 2)

words = {w: d for w, d in words.items() if not spoils(w, {w})}

# ---- hanja ----
hj = json.load(open(A / 'hanja.json', encoding='utf-8'))
for w, d in words.items():
    if w in hj['words']:
        d['hj'] = hj['words'][w]['hanja']
chars = {c: m for c, m in hj['chars'].items()}

# ---- dialogue lines, per area, cleaned and split into sentences ----
recs = {}
for p in [MONEO / 'tools/moneo/corpus.ko.live.json', A / 'corpus.ko.json']:
    for r in json.load(open(p, encoding='utf-8'))['records']:
        recs.setdefault(r['id'], r)
area_recs = json.load(open(MONEO / 'tools/moneo/map_area_index.json', encoding='utf-8'))['resolved_areas']

lemmas = lemmatizer(words)

def clean(text):
    text = text.replace('{PLAYER}', '레드').replace('{RIVAL}', '그린').replace('(이)', '이')
    if re.search(r'[{}\[\]·]|STR_VAR', text):
        return []
    text = re.sub(r'\s*\n\s*', ' ', text).strip()
    parts = re.split(r'(?<=[.!?…])\s+', text)
    return [p.strip() for p in parts if 6 <= len(p.strip()) <= 70 and re.search('[가-힣]', p)]

lines, seen = [], set()
for ai, area in enumerate(POC):
    for rid in area_recs.get(area, {}).get('recIds', []):
        r = recs.get(rid)
        if not r or r.get('unknown'):
            continue
        for s in clean(r.get('text', '')):
            if s in seen:
                continue
            seen.add(s)
            lem = lemmas(s)
            if spoils(s, lem):
                continue
            lines.append({'t': s, 'a': ai, 'lem': lem})

# ---- spoiler review (tools/spoilers.json, from a reviewer who knows the game): drop flagged lines/words ----
sp_path = ROOT / 'tools/rom/spoilers.json'
if sp_path.exists():
    sp = json.load(open(sp_path, encoding='utf-8'))
    # flagged ids refer to tools/review-lines.tsv (the list the reviewer saw); match by text so ids can't drift
    reviewed = dict(ln.rstrip('\n').split('\t')[::2] for ln in open(ROOT / 'tools/rom/review-lines.tsv', encoding='utf-8'))
    drop_lines = {reviewed[x] for x in sp.get('lines', [])}
    unreviewed = [l['t'] for l in lines if l['t'] not in reviewed.values()]
    if unreviewed:
        print(f'WARNING: {len(unreviewed)} lines were never spoiler-reviewed and are left out, e.g.', unreviewed[:3])
    lines = [l for l in lines if l['t'] in reviewed.values() and l['t'] not in drop_lines]
    for w in sp.get('words', []):
        words.pop(w, None)
    print('spoiler review: dropped', len(drop_lines), 'lines and', len(sp.get('words', [])), 'words')

# ---- tap-a-word: every word as written in a line → dictionary form(s) ----
tapmap = {}
for l in lines:
    for eoj in l['t'].split():
        key = eojeol_key(eoj)
        if key and key not in tapmap:
            tapmap[key] = sorted(lemmas(key) | ({key} if key in words else set()), key=lambda x: -len(x))[:3]

# ---- link words to example lines (the same per-word lemmas tap-a-word uses, so every linked word can glow) ----
# Moneo's per-area word attribution rides on coarse record tags (a "Route 2" bucket holds Silph Co.), so a word's
# area is instead the first area where a reviewed, kept line uses it; words no kept line uses are left out.
# f = how many of that area's lines use it — the most frequent become the area's 길잡이 (guide) words.
ex = collections.defaultdict(list)
for li, l in enumerate(lines):
    hits = {x for eoj in l['t'].split() for x in tapmap.get(eojeol_key(eoj), [])}
    for w in hits:
        if w in words:
            ex[w].append(li)
words = {w: d for w, d in words.items() if ex.get(w)}
for w, d in words.items():
    d['area'] = min(lines[i]['a'] for i in ex[w])
    d['f'] = sum(1 for i in ex[w] if lines[i]['a'] == d['area'])
    d['ex'] = ex[w][:12]

# ---- output: the word list only. The game's own lines never leave this script (src/words.json is committed;
# example sentences are original ones, tools/sentences/*.json, joined in by tools/assemble.py) ----
out = {
    'areas': [{'id': a, 'ko': areas_meta[a]['koreanLabel'], 'en': areas_meta[a]['englishName']} for a in POC],
    'words': [{k: v for k, v in d.items() if k != 'ex'} for d in sorted(words.values(), key=lambda d: (d['area'], -d['f'], d['w']))],
    'hanja': {c: chars[c] for d in words.values() for c in d.get('hj', '') if c in chars},
    # Pokémon a player can have met by Pewter (Moneo's species areas share the attribution problem above)
    'species_ok': ['꼬부기', '이상해씨', '파이리', '구구', '꼬렛', '캐터피', '단데기', '뿔충이', '딱충이', '피카츄'],
}
(ROOT / 'src/words.json').write_text(json.dumps(out, ensure_ascii=False, indent=0), encoding='utf-8')
cats = collections.Counter(d['cat'] for d in words.values())
print(f"words {len(words)} {dict(cats)} · from {len(lines)} reviewed lines · per area",
      collections.Counter(d['area'] for d in words.values()))
