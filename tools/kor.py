"""Shared Korean helpers for the build scripts: dictionary forms of the words in a text (Kiwi), and the later-game names
that must not appear before Pewter City."""
import re
from kiwipiepy import Kiwi

# Things from later in the game (names as they appear in the 2024 Korean translation)
LATER = ['무지개배지', '그린배지', '블루배지', '오렌지배지', '핑크배지', '진홍색배지', '골드배지',
         '이슬', '마티스', '민화', '독수', '초련', '강연', '비주기', '칸나', '시바', '국화', '목호', '챔피언',
         '뮤츠', '프리저', '썬더', '파이어', '사천왕', '전당', '실프', '사파리', '로켓단', '포켓몬타워',
         '기술머신', '비전머신', '자전거', '사이클링', '화석', '박물관', '달의돌', '블루시티', '석영고원']
LATER_TOKENS = {'뮤'}          # single-syllable names: only as whole tokens


def lemmatizer(user_words):
    """→ lemmas(text): the dictionary forms in text. user_words are kept whole (Kiwi otherwise splits names)."""
    kiwi = Kiwi()
    for w in user_words:
        if re.fullmatch('[가-힣]{2,}', w):
            kiwi.add_user_word(w, 'NNP', score=3)

    def lemmas(text):
        out, toks, i = set(), kiwi.tokenize(text), 0
        while i < len(toks):
            t, n = toks[i], toks[i + 1] if i + 1 < len(toks) else None
            if t.tag in ('NNG', 'XR', 'NNP') and n is not None and n.tag in ('XSV', 'XSA'):
                out.add(t.form + n.form + '다'); i += 2; continue
            if t.tag.startswith(('VV', 'VA', 'VX')):
                out.add(t.form + '다')
            elif t.tag in ('NNG', 'NNP', 'NNB', 'NR', 'NP', 'MAG', 'MAJ', 'MM', 'XR', 'IC'):
                out.add(t.form)
            i += 1
        return out
    return lemmas


def eojeol_key(eoj):
    """a space-separated word as written, without surrounding punctuation"""
    return re.sub(r'^[^가-힣]+|[^가-힣]+$', '', eoj)
