import subprocess
from os.path import join, isdir
import shutil
import logging
from collections import Counter

from convert import Dictionary, doubleform_signal
from pathlib import Path

import pymorphy2

from isv_nlp_utils.constants import DEFAULT_UNITS, ETM_DIACR_SUBS

REPEATED_FORMS = Counter()


def log_doubleform(sender, tags_signature):
    REPEATED_FORMS.update({tags_signature: 1})


DIR = "C:\\dev"
DEBUG = True
RUN_EXPORT = False
RUN_CONVERT = True
RUN_BUILD_DICTS = True

if RUN_EXPORT:
    subprocess.check_output(
        ["npm", "run", "generateParadigms"],
        cwd=join(DIR, "interslavic"), shell=True
    )


# dictionary_path = join(DIR, "interslavic", "static", "words_forms.txt")
dictionary_path = "tmp_dict.txt"

dictionary_out = join(DIR, "ISV_pymorphy2_dicts", "pymorphy2-dicts", "out_{}.xml")
DICTS_DIR = join(DIR, "ISV_pymorphy2_dicts", "pymorphy2-dicts")


if DEBUG:
    logging.basicConfig(level=logging.DEBUG)
    doubleform_signal.connect(log_doubleform)

if RUN_CONVERT:
    d = Dictionary(dictionary_path, mapping=join(DIR, "ISV_pymorphy2_dicts", "mapping_isv.tsv"))
    for lang in ['isv_cyr', 'isv_lat', 'isv_etm']:
        d.export_to_xml(join(DIR, "ISV_pymorphy2_dicts", "pymorphy2-dicts", f"out_{lang}.xml"), lang=lang)

        if DEBUG:
            logging.debug("=" * 50)
            for term, cnt in REPEATED_FORMS.most_common():
                logging.debug(u"%s: %s" % (term, cnt))

if RUN_BUILD_DICTS:
    for lang in ['isv_cyr', 'isv_lat', 'isv_etm']:
        out_dir = join(DIR, "ISV_pymorphy2_dicts", "pymorphy2-dicts", f"out_{lang}")
        if isdir(out_dir):
            shutil.rmtree(out_dir)
	
        subprocess.check_output(
            ["python", "build-dict.py", dictionary_out.format(lang), out_dir],
            cwd=join(DIR, "ISV_pymorphy2_dicts")
        )

        print('suffixes.json')
        print(Path(join(out_dir, 'suffixes.json')).stat().st_size)

        # print('suff.txt')
        # print(Path(join(DICTS_DIR, 'suff.txt')).stat().st_size)

        # print('paradigm.txt')
        # print(Path(join(DICTS_DIR, 'paradigm.txt')).stat().st_size)


out_dir_etm = join(DIR, "ISV_pymorphy2_dicts", "pymorphy2-dicts", "out_isv_etm")

etm_morph = pymorphy2.MorphAnalyzer(
    out_dir_etm,
    units=DEFAULT_UNITS,
    char_substitutes=ETM_DIACR_SUBS
)

print(etm_morph.parse("ljudij"))
print(etm_morph.parse("råzumějų"))
print(etm_morph.parse("razumeju"))

out_dir_cyr = join(DIR, "pymorphy2-dicts", "out_isv_cyr")
# morph = pymorphy2.MorphAnalyzer(out_dir_cyr)


out_dir_etm = join(DIR, "pymorphy2-dicts", "out_isv_etm")
morph = pymorphy2.MorphAnalyzer(
    out_dir_cyr,
    # units=[pymorphy2.units.DictionaryAnalyzer()],
    char_substitutes={'е': 'є'}
)
print(morph.parse("разумеју"))

print(morph.parse("фунгујут"))
print()

phrase = "Тутчас можем писати на прдачном језыковєдском нарєчју"

phrase = "нарєчје јест разумливо приблизно всим машинам без ученја"

phrase = "jа уже виджу нєколико проблемов буду чинити"

phrase = "писанйе jедним столбецем дозволjаjе додати информациjу односно двусмыслности"


phrase = "чи можем ли jа говорити на прдачном језыковєдском нарєчју в тутом каналу буде ли то добро"
phrase = "Jесм поправил нєкаке грєшкы од првого раза"
phrase = "понєктори користники сут измыслили нєколико прдачных нарєчиј"

phrase = "мене приjати же тутчас jест канал в ктором jа можем писати на прдачном језыковєдском нарєчју"

phrase = "хм jа трєбују измыслити нєкаку методу работы с заименниками прємного опциj анализа имаjут оне"

phrase = "Мой изкус односно фунгованйа всакоможных заименников чи имайут ли премного формов они и оне"

for i, word in enumerate(phrase.replace("й", "j").replace("j", "ј").split(" ")):

    parsings = morph.parse(word)
    desc = " | ".join(f"**{parsing.normal_form}** - {parsing.tag}" for parsing in parsings)
    if i % 2 == 0:
        desc = "> " + desc
    print(desc)
    # print(len(morph.parse(word)))
    # print(morph.parse(word)[0])
