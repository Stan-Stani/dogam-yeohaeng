# 도감 여행

A small Korean vocabulary game: catch the core words of the first six areas of Pokémon LeafGreen (태초마을 → 회색시티),
spoiler-free, in short original sentences, then review them in the 풀숲 with spaced repetition. Tap any word for a Korean
definition; ? shows English.

Play: https://stan-stani.github.io/dogam-yeohaeng/

- `src/words.json`: the word list. It's derived locally from the Moneo project's assets by `tools/build_data.py`, and the game's text is never committed.
- `tools/sentences/out-*.json`: the original example sentences, reviewed. `tools/assemble.py` builds them into `src/data.json`.
- `python3 tools/assemble.py && python3 tools/build.py` builds `index.html`. `node tests/play.mjs ch1 flow` plays it in headless Chrome.

Pokémon is © Nintendo / Creatures / GAME FREAK. This is an unofficial fan-made study aid.
