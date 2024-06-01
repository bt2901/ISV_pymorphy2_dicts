import glob
import json5


from isv_nlp_utils import constants, slovnik

import subprocess
from os.path import join, isdir
import shutil
import logging
from collections import Counter

from pathlib import Path

import tqdm
import pymorphy2

from isv_nlp_utils.constants import DEFAULT_UNITS, ETM_DIACR_SUBS

mslovnik = slovnik.get_slovnik()['words']
mslovnik = mslovnik.set_index('id')
mslovnik.addition = mslovnik.addition.astype(str)


data = []
for e in glob.glob(r"C:\dev\js-utils\src\**\*", recursive=1):
	if "ts.snap" in e:
		with open(e, "r", encoding='utf8') as f:
			scan_tick = False
			collected = []
			for line in f:
				if line.strip().startswith("exports") and "null" not in line:
					scan_tick = True
				if scan_tick:
					collected.append(line.strip("\n"))
				if line.strip() == '`;':
					scan_tick = False
					data.append(collected)
					collected = []

doubleforms = set()

for e in data:
    if e[0].startswith("exports") and "-" in e[0]:
        pos, sl_id = get_slovnik_id(e[0])
        if sl_id is not None:
            doubleforms.add(e[0].replace("-1 ", " "))



def get_slovnik_id(e):
    inside_parens = e.split("`")[1].split()
    pos = " ".join([x for x in inside_parens if x.isalpha()])
    sl_id = [x for x in inside_parens if x.replace("-", "").isdigit()]
    sl_id = sl_id[0]

    if inside_parens[0] not in ('transliterate', 'renderers'):
        return pos, sl_id
    return None, None

[
    get_slovnik_id('exports[`noun feminine 3 1`] = `'), 
    get_slovnik_id('exports[`noun miscellaneous 6181 (as masculine): masculine 1`] = `'),
    get_slovnik_id('exports[`adjective 93-1 1`] = `')
]

errors = []

dictionary_path = "tmp_dict.txt"

with open(dictionary_path, "w", encoding="utf8") as f:

    for e in tqdm.tqdm(data):
        pos, sl_id = get_slovnik_id(e[0])
        if sl_id is None: 
            continue
            
        if "-" in sl_id or e[0] in doubleforms:
            sl_id, _, sl_subid = sl_id.partition("-")
            if sl_subid:
                sl_subid = int(sl_subid)
            else:
                sl_subid = 0
            sl_id = int(sl_id)
            
            if sl_id not in mslovnik.index:
                errors.append(e[0])
                continue
            item, partOfSpeech, addition = mslovnik.loc[sl_id, ['isv', 'partOfSpeech', 'addition']]
            item = item.split(", ")[sl_subid]
        else:
            sl_id = int(sl_id)
            if sl_id not in mslovnik.index:
                errors.append(e[0])
                continue
            item, partOfSpeech, addition = mslovnik.loc[sl_id, ['isv', 'partOfSpeech', 'addition']]

        jsonline = "".join(e[1:-1])#.replace("`", '"')
        paradigm = json5.dumps(
            json5.loads(jsonline),
            quote_keys=True, ensure_ascii=False
        )
        metadata = ", ".join([partOfSpeech, addition]) 
        f.write("\t".join([item, paradigm, partOfSpeech, addition, pos]) + "\n")
