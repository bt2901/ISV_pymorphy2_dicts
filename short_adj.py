import re

SOFT_CONSONANTS = "jcćčšž" + "ŕĺľťśď"
VOWELS = "aeiouųåėęěȯy"
CONSONANTS = "bcdfghjklmnprstvzćčďľńŕśšťźžʒđ"


from itertools import takewhile

def get_consonants_ending(word):
    if word[-3:] in [" na", " od", " za"]:
        word = word[:-3]
    if word[-1] not in 'yi':
        return word
    word = word[:-1]
    cons = "".join(takewhile(lambda c: c in CONSONANTS, reversed(word)))
    return cons[::-1]

def make_short_adj(long_adj):
    simplest_form = long_adj[:-1]
    cons_ending = get_consonants_ending(long_adj)
    if long_adj in ['lěnji', 'ranji', 'sinji', 'povsednji']:
        return simplest_form
    if long_adj == 'dȯlgy':
        return "dȯlȯg"
    for ending in ['ov', 'ev', 'in', 'ji', 'en', 'rad']:
        if long_adj.endswith(ending):
            return long_adj
        # or  long_adj.endswith("ev") or long_adj.endswith("in") or long_adj.endswith("ji"):
    for ending in ['ši', 'ći']:
        if long_adj.endswith(ending):
            return long_adj
    if (
        re.match(f".*[{VOWELS}][{CONSONANTS}][yi]$", long_adj) 
        or re.match(f".*[{VOWELS}]st[rl]?y$", long_adj)
        or re.match(f".*[{VOWELS}][{CONSONANTS}][rl]y$", long_adj)
        or cons_ending in ['tvŕd', 'lst', 'čŕstv', 'črstv', 'mŕtv', 'brz']
    ):
        return simplest_form
    if len(cons_ending) == 2 and "č" not in cons_ending:
        return simplest_form

    if long_adj.endswith("ny"):
        if long_adj[:-3] == "l":
            return long_adj[:-2] + "ȯn"
        return long_adj[:-2] + "ėn"
    if long_adj.endswith("zly") or long_adj.endswith("mly"):
        return long_adj[:-2] + "ȯl"
    if long_adj.endswith("ky"):
        if long_adj[-3] in SOFT_CONSONANTS:
            return long_adj[:-2] + "ėk"
        else:
            return long_adj[:-2] + "ȯk"
    return None