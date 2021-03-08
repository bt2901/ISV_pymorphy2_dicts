import subprocess
from os.path import join, isdir
import shutil
import logging
from collections import Counter

from convert import Dictionary, doubleform_signal


REPEATED_FORMS = Counter()


def log_doubleform(sender, tags_signature):
    REPEATED_FORMS.update({tags_signature: 1})


DIR = "C:\\dev\\"
DEBUG = True
RUN_EXPORT = False
RUN_CONVERT = True
RUN_BUILD_DICTS = True

if RUN_EXPORT:
    subprocess.check_output(
        ["npm", "run", "generateParadigms"],
        cwd=join(DIR,"interslavic")
    )


dictionary_path = join(DIR, "interslavic", "static", "words_forms.txt")
dictionary_out = join(DIR, "pymorphy2-dicts", "out_isv_new.xml")
out_dir = join(DIR, "pymorphy2-dicts", "out_isv")


if DEBUG:
    logging.basicConfig(level=logging.DEBUG)
    doubleform_signal.connect(log_doubleform)

if RUN_CONVERT:
    d = Dictionary(dictionary_path, mapping="mapping_isv.csv")
    d.export_to_xml(join(DIR, "pymorphy2-dicts", "out_isv_new.xml"))

    if DEBUG:
        logging.debug("=" * 50)
        for term, cnt in REPEATED_FORMS.most_common():
            logging.debug(u"%s: %s" % (term, cnt))

if RUN_BUILD_DICTS:
    if isdir(out_dir):
        shutil.rmtree(out_dir)

    subprocess.check_output(
        ["python", "build-dict.py", dictionary_out, out_dir],
        cwd=join(DIR, "pymorphy2-dicts")
    )

import pymorphy2
morph = pymorphy2.MorphAnalyzer(out_dir)
print(morph.parse("фунгујут"))
