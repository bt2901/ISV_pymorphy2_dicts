from __future__ import unicode_literals
import re
import os.path
import logging
import ujson

import sys
sys.path.append("C:\\dev\\ISV_pymorphy2_dicts")
from short_adj import make_short_adj
from transliteration import translation_functions
from xml_stuff import export_grammemes_description_to_xml, TagSet, Lemma, WordForm


import xml.etree.cElementTree as ET


# To add stats collection in inobstrusive way (that can be simply disabled)
from blinker import signal

doubleform_signal = signal('doubleform-found')


def getArr(details_string):
    return [
        x for x in details_string
        .replace("./", '/')
        .replace(" ", '')
        .split('.')
        if x != ''
    ]



VERB_AUX_WORDS = {'(je)', 'sę', '(sųt)', 'ne'}
INDECLINABLE_POS = {'adverb', 'conjunction', 'preposition', 'interjection', 'particle', 'pronoun', 'numeral'}


def infer_pos(arr):
    if '#v' in arr:  # TODO: this should be fixed elsewhere
        return 'verb'
    if '#adj' in arr:  # TODO: this should be fixed elsewhere
        return 'adjective'
    if 'adj' in arr:
        return 'adjective'
    if set(arr) & {'f', 'n', 'm', 'm/f'}:
        return 'noun'
    if 'adv' in arr:
        return 'adverb'
    if 'conj' in arr:
        return 'conjunction'
    if 'prep' in arr:
        return 'preposition'
    if 'pron' in arr:
        return 'pronoun'
    if 'num' in arr:
        return 'numeral'
    if 'intj' in arr:
        return 'interjection'
    if 'v' in arr:
        return 'verb'




def yield_all_simple_adj_forms(forms_obj, pos):
    if "casesSingular" in forms_obj:
        forms_obj['singular'] = forms_obj['casesSingular']
        forms_obj['plural'] = forms_obj['casesPlural']
    for num in ['singular', 'plural']:
        for case, content in forms_obj[num].items():
            for i, animatedness in enumerate(["anim", "inan"]):
                if case == "nom":
                    if num == 'singular':
                        yield content[0], {case, "sing", "masc", animatedness} | pos
                        yield content[1], {case, "sing", "neut", animatedness} | pos
                        yield content[2], {case, "sing", "femn", animatedness} | pos
                    if num == 'plural':
                        masc_form = content[0].split("/")
                        if len(masc_form) == 1:
                            if i == 1:
                                continue
                            else:
                                animatedness = ''
                        yield masc_form[i], {case, "plur", "masc", animatedness} | pos
                        yield content[1], {case, "plur", "neut", animatedness} | pos
                        yield content[1], {case, "plur", "femn", animatedness} | pos
                elif case == "acc":
                    masc_form = content[0].split("/")
                    if len(masc_form) == 1:
                        if i == 1:
                            continue
                        else:
                            animatedness = ''
                    if num == 'singular':
                        yield masc_form[i], {case, "sing", "masc", animatedness} | pos
                        yield content[1], {case, "sing", "neut", animatedness} | pos
                        yield content[2], {case, "sing", "femn", animatedness} | pos
                    if num == 'plural':
                        yield masc_form[i], {case, "plur", "masc", animatedness} | pos
                        yield content[1], {case, "plur", "neut", animatedness} | pos
                        yield content[1], {case, "plur", "femn", animatedness} | pos
                else:
                    animatedness = ''
                    if i == 1:
                        continue
                    if num == 'singular':
                        yield content[0], {case, "sing", "masc", animatedness} | pos
                        yield content[0], {case, "sing", "neut", animatedness} | pos
                        yield content[1], {case, "sing", "femn", animatedness} | pos
                    if num == 'plural':
                        yield content[0], {case, "plur", "masc", animatedness} | pos
                        yield content[0], {case, "plur", "neut", animatedness} | pos
                        yield content[0], {case, "plur", "femn", animatedness} | pos


def yield_all_noun_forms(forms_obj, pos, columns):
    for case, data in forms_obj.items():
        for (form, form_name) in zip(data, columns):
            if form is not None:
                if form_name == "singular (m./f.)":
                    form_name = "sing"
                if form_name == "plural (m./f.)":
                    form_name = "plur"
                if form_name == "masculine":
                    form_name = 'masc'
                # TODO:
                if form_name == "feminine/neuter":
                    yield form, {case, 'femn'} | pos
                    yield form, {case, 'neut'} | pos
                    continue

                if form_name == "Word Form" or form_name == "wordForm":
                    form_name = ''
                if "(" in form:
                    all_subforms = [form]
                    if (" (" in form or ") " in form):
                        all_subforms = form.split(" ")
                    for subform in all_subforms:
                        if subform.strip("()") == subform[1:-1]:
                            yield subform[1:-1], {case, form_name, "form-short"} | pos
                        else:
                            yield re.sub(r'\(.*?\)', '', subform), {case, form_name, "form-regl"} | pos
                            yield subform.replace("(", "").replace(")", ""), {case, form_name, "form-full"} | pos

                else:
                    yield form, {case, form_name} | pos


def yield_all_verb_forms(forms_obj, pos, base):

    is_byti = forms_obj['infinitive'] == 'bytì'

    # ====== Infinitive ======
    yield forms_obj['infinitive'], pos | {"INFN"}

    # ====== L-particle ======
    # ['pluperfect', 'perfect', 'conditional']:
    tags = [
        {'m', 'past', 'sing'},
        {'f', 'past', 'sing'},
        {'n', 'past', 'sing'},
        {'past', 'plur'},
    ]
    forms_person = forms_obj['perfect']
    base_forms = forms_person[2:5] + forms_person[7:8]
    for form, meta in zip(base_forms, tags):
        parts = " ".join([p for p in form.split(" ") if p not in VERB_AUX_WORDS])
        yield parts, meta | pos | {'past'}

    # ====== Conditional ======
    # ['conditional']:
    if is_byti:
        tags = [
            {'1per', 'sing'},
            {'2per', 'sing'},
            {'3per', 'sing'},

            {'1per', 'plur'},
            {'2per', 'plur'},
            {'3per', 'plur'},
        ]
        time = 'conditional'
        different_forms = forms_obj[time][:3] + forms_obj[time][5:8]
        for entry, one_tag in zip(different_forms, tags):
            subentry = entry.split(" ")[0]
            yield subentry, pos | {time} | one_tag

    # ====== Future ======
    # ['future']
    # future uses infinitive and aux verbs

    # ====== Present and Imperfect ======
    # ['present', 'imperfect']
    tags = [
        {'1per', 'sing'},
        {'2per', 'sing'},
        {'3per', 'sing'},
        {'1per', 'plur'},
        {'2per', 'plur'},
        {'3per', 'plur'},
    ]
    relevant_times = ['present', 'imperfect']
    if is_byti:
        relevant_times += ['future']
    for time in relevant_times:
        for entry, one_tag in zip(forms_obj[time], tags):
            if entry.endswith(" (je)"):
                entry = entry[:-5] + "," + "je"

            subentries = entry.split(",")
            subentry_tags = [{"V-ju"}, {'V-m'}]
            if len(subentries) == 1:
                subentry_tags = [set()]
            for subentry, add_tag in zip(subentries, subentry_tags):
                yield subentry, pos | {time} | add_tag | one_tag

    # ====== Imperative ======
    imperatives = forms_obj['imperative'].split(',')
    tags = [
        {'2per'}, {'1per', 'plur'}, {'2per', 'plur'}
    ]
    for subentry, add_tag in zip(imperatives, tags):
        yield subentry, pos | {'impr'} | add_tag

    # ====== Participles ======
    tags = [
        {'m'}, {'f'}, {'n'}
    ]
    for time, meta_tag in zip(
        ['prap', 'prpp', 'pfap', 'pfpp'],
        [{'actv', 'present'}, {'pasv', 'present'}, {'actv', 'past'}, {'pasv', 'past'}]
    ):
        # TODO: will fuck up if multi-word verb
        parts = (
            forms_obj[time]
            .replace("ne ", "")
            .replace("ši sá", "ša sę").replace("ši sé", "še sę")  # THIS IS A CHANGE FROM ORIGINAL LOGIC
            .replace(" sę", "")
            .replace(",", "").replace("(", "") .replace(")", "")
            .split(" ")
        )

        subentry_tags = [{"V-ju"}, {'V-m'}]
        if len(parts) == 1:
            subentry_tags = [set()]

        for i, entry in enumerate(parts):
            if i >= 6:
                print(forms_obj)
                raise AssertionError

            current_tag = tags[i % 3] | subentry_tags[i >= 3]
            if i % 3 == 0:
                base_part = entry
                yield entry, pos | meta_tag | current_tag
            else:
                if "-" in entry:
                    full_entry = base_part[:-1] + entry[1:]
                else:
                    full_entry = entry
                yield full_entry, pos | meta_tag | current_tag

    # ====== Gerund ======
    yield forms_obj['gerund'], pos | {"noun", "vnoun"}


def iterate_json(forms_obj, pos_data, base):
    pos = infer_pos(pos_data)
    pos_data = {x for x in pos_data if x != "m/f"}
    if isinstance(forms_obj, str) or pos is None:
        return base, pos_data

    if "adj" in pos:
        yield from yield_all_simple_adj_forms(forms_obj, pos_data)
        content = forms_obj['comparison']
        #if content['positive']:
        #    yield content['positive'][0], {"positive"} | pos_data

        if content['comparative']:
            comp_form = content['comparative'][0]
            if " " not in comp_form:
                yield comp_form, {"cmpr"} | pos_data

        # TODO: is it right to treat it as adjective??
        if content['positive']:
            yield content['positive'][1], {"adv", "compb"} | pos_data
        if content['comparative']:
            comp_form = content['comparative'][1]
            if " " not in comp_form:
                yield comp_form, {"adv", "cmpr"} | pos_data
        if content['superlative']:
            comp_form = content['superlative'][0]
            if " " not in comp_form:
                yield comp_form, {"adj", "sprl"} | pos_data
                #print(pos_data)
                #raise NameError
            comp_form = content['superlative'][1]
            if " " not in comp_form:
                yield comp_form, {"adv", "sprl"} | pos_data
        # additionaly: short adjective form
        if True:  # TODO: some condition here, not all adjs allow for 
            yield make_short_adj(base), {"brev"} | pos_data


    elif "numeral" in pos or 'pronoun' in pos:
        if forms_obj['type'] == 'adjective':
            for form, pos_data in yield_all_simple_adj_forms(forms_obj, pos_data):
                if "(" in form:
                    # TODO: will fuck up on stuff like "dati (n)jemu (mu)"
                    all_subforms = [form]
                    if (" (" in form or ") " in form):
                        all_subforms = form.split(" ")
                    for subform in all_subforms:
                        if subform.strip("()") == subform[1:-1]:
                            yield subform[1:-1], {"form-short"} | pos_data
                        else:
                            yield re.sub(r'\(.*?\)', '', subform), {"form-regl"} | pos_data
                            yield subform.replace("(", "").replace(")", ""), {"form-full"} | pos_data
                else:
                    yield form, pos_data

        elif forms_obj['type'] == 'noun':
            columns = forms_obj['columns']
            yield from yield_all_noun_forms(forms_obj['cases'], pos_data, columns)
        else:
            print("1, smth else", forms_obj['type'])
            raise AssertionError
    elif "verb" in pos:
        error = False
        for entry, tag in yield_all_verb_forms(forms_obj, pos_data, base):
            if "ERROR" in entry:
                error = True
            if entry.endswith(" sę"):
                entry = entry[:-3]
            if base.startswith("ne "):
                entry = entry[3:]
            yield entry, tag
        if error:
            print(forms_obj, pos_data, base)
    elif "noun" in pos:
        yield from yield_all_noun_forms(forms_obj, pos_data, ['singular', 'plural'])
    return base, pos_data


class Dictionary(object):
    def __init__(self, fname, mapping):
        if not mapping:
            mapping = os.path.join(os.path.dirname(__file__), "mapping_isv.tsv")

        self.mapping = mapping
        self.lemmas = {}

        counter_multiword = 0
        counter_multiword_verb = 0
        counter_se = 0
        with open(fname, "r", encoding="utf8") as fp:
            for i, line in enumerate(fp):
                    isv_lemma_current, forms, pos, addition, pos_formatted = line.split("\t")
                    pos_formatted = pos_formatted.strip()
                    forms_obj = ujson.loads(forms)
                    isv_lemma_current = isv_lemma_current.strip()
                    add_tag = set()
                    details_set = set(getArr(pos)) | add_tag
                    # if infer_pos is None, then fallback to the first form
                    local_pos = infer_pos(details_set) or pos
                    # temporary check: if everything is OK, I can get rid of `infer_pos` function
                    if (local_pos != pos_formatted.split(" ")[0]):
                        print(isv_lemma_current)
                        print([local_pos, pos_formatted])
                        assert(local_pos == pos_formatted)
                    if local_pos == "noun":
                        details_set |= {'noun'}
                    if pos == "m./f.":
                        pos = "m" if "masc" in pos_formatted else "f"
                        details_set -= {"m/f"}

                    if not isinstance(forms_obj, dict):
                        if forms_obj != '':
                            # add isolated lemma

                            if local_pos in INDECLINABLE_POS and " " not in isv_lemma_current:
                                current_lemma = Lemma(
                                    isv_lemma_current,
                                    lemma_form_tags=details_set,
                                )
                                current_lemma.add_form(WordForm(
                                    isv_lemma_current,
                                    tags=details_set,
                                ))
                                self.add_lemma(current_lemma)
                            continue
                    if " " in isv_lemma_current and isinstance(forms_obj, dict):
                        splitted = isv_lemma_current.split()
                        if len(splitted) == 2 and "sę" in splitted:
                            counter_se += 1
                        else:
                            counter_multiword += 1
                            # TODO TODO XXX
                            if "verb" not in pos_formatted:
                                counter_multiword_verb += 1
                                #print(isv_lemma_current.split(), pos_formatted)
                                #print(forms_obj)
                            else:
                                #print(isv_lemma_current.split(), pos_formatted, forms_obj['infinitive'])
                                pass
                        # continue

                    current_lemma = Lemma(
                        isv_lemma_current,
                        lemma_form_tags=details_set,
                        exact_pos=local_pos,
                    )
                    number_forms = set()
                    for current_form, tag_set in iterate_json(forms_obj, details_set, isv_lemma_current):
                        if current_form is None:
                            print(isv_lemma_current, tag_set)
                            continue
                        #if " , " in current_form:
                        #    all_forms = current_form.split(" , ")
                        if "/" in current_form:
                            # print(current_form)
                            all_forms = current_form.split("/")
                        else:
                            all_forms = [current_form]
                        if len(all_forms) > 2:
                            print(isv_lemma_current, all_forms)
                            raise NameError
                        all_tags = [
                            {f"V-flex-{form_num+1}"} for form_num, _ in enumerate(all_forms)
                        ]

                        if len(all_forms) == 1:
                            all_tags = [set()]
                        for single_form, add_tag in zip(all_forms, all_tags):
                            current_lemma.add_form(WordForm(
                                single_form,
                                tags=tag_set | add_tag,
                                exact_pos=local_pos,
                            ))
                        if local_pos in {"noun", "numeral"}:
                            number_forms |= {
                                one_tag for one_tag in tag_set if one_tag in ['singular', 'plural']
                            }
                    if len(number_forms) == 1:
                        if number_forms != {"singular"} and number_forms != {"plural"}:
                            print(number_forms, current_lemma.lemma_form.form)
                            raise AssertionError
                        numeric = {"Sgtm"} if number_forms == {"singular"} else {"Pltm"}
                        current_lemma.common_tags |= numeric
                    if local_pos == "verb":
                        if forms_obj['infinitive'].replace("ì", "i") != isv_lemma_current:
                            current_lemma.lemma_form.form = forms_obj['infinitive']
                    if local_pos == "pronoun":
                        # this will be processed later
                        pass
                    self.add_lemma(current_lemma)
        print(counter_multiword)
        print(counter_multiword_verb)
        print(counter_se)

    def add_lemma(self, lemma):
        if lemma is not None:
            self.lemmas[lemma.lemma_signature] = lemma

    def export_to_xml(self, fname, lang="isv_cyr"):
        tag_set_full = TagSet(self.mapping)
        root = ET.Element("dictionary", version="0.2", revision="1")
        tree = ET.ElementTree(root)
        root.append(export_grammemes_description_to_xml(tag_set_full))
        lemmata = ET.SubElement(root, "lemmata")
        known_pronouns = {}

        translate_func = translation_functions[lang]

        for i, lemma in enumerate(self.lemmas.values()):
            lemma_xml = lemma.export_to_xml(i + 1, tag_set_full, translate_func)
            if lemma_xml is not None:
                if "pron" in lemma.lemma_form.tags:
                    signature = "|".join(
                        f"{k}: {v[0].form}" for i, (k, v) in enumerate(lemma.forms.items())
                        if i != 0
                    )

                    if signature:
                        if signature in known_pronouns:
                            # print(known_pronouns[signature], "<-", lemma.lemma_form.form)
                            continue
                        else:
                            known_pronouns[signature] = lemma.lemma_form.form
                            # print(f"=> SAVING: {lemma.lemma_form.form}")
                lemmata.append(lemma_xml)

        tree.write(fname, encoding="utf-8")
