import xml.etree.cElementTree as ET
from unicodecsv import DictReader
import functools


def export_grammemes_description_to_xml(tag_set):
    grammemes = ET.Element("grammemes")
    for tag in tag_set.full.values():
        grammeme = ET.SubElement(grammemes, "grammeme")
        if tag["parent"] != "aux":
            grammeme.attrib["parent"] = tag["parent"]
        name = ET.SubElement(grammeme, "name")
        name.text = tag["native tags"]

        alias = ET.SubElement(grammeme, "alias")
        alias.text = tag["name"]

        description = ET.SubElement(grammeme, "description")
        description.text = tag["description"]

    return grammemes


class TagSet(object):
    """
    Class that represents LanguageTool tagset
    Can export it to OpenCorpora XML
    Provides some shorthands to simplify checks/conversions
    """
    def __init__(self, fname):
        self.all = []
        self.full = {}
        self.groups = []
        self.lt2opencorpora = {}

        with open(fname, 'rb') as fp:
            r = DictReader(fp, delimiter='\t')

            for tag in r:
                ## lemma form column represents set of tags that wordform should
                ## have to be threatened as lemma.
                #tag["lemma form"] = filter(None, [s.strip() for s in
                #                           tag["lemma form"].split(",")])

                #tag["divide by"] = filter(
                #    None, [s.strip() for s in tag["divide by"].split(",")])

                # opencopropra tags column maps LT tags to OpenCorpora tags
                # when possible
                tag["native tags"] = (
                    tag["native tags"] or tag["name"])

                # Helper mapping
                self.lt2opencorpora[tag["name"]] = tag["native tags"]

                # Parent column links tag to it's group tag.
                # For example parent tag for noun is POST tag
                # Parent for m (masculine) is gndr (gender group)
                if not hasattr(self, tag["parent"]):
                    setattr(self, tag["parent"], [])

                attr = getattr(self, tag["parent"])
                attr.append(tag["name"])

                # aux is our auxiliary tag to connect our group tags
                if tag["parent"] != "aux":
                    self.all.append(tag["name"])

                # We are storing order of groups that appears here to later
                # sort tags by their groups during export
                if tag["parent"] not in self.groups:
                    self.groups.append(tag["parent"])

                self.full[tag["name"]] = tag

    def _get_group_no(self, tag_name):
        """
        Takes tag name and returns the number of the group to which tag belongs
        """

        if tag_name in self.full:
            return self.groups.index(self.full[tag_name]["parent"])
        else:
            return len(self.groups)

    def sort_tags(self, tags):
        # TODO: just define key to be `a_group * 100 + a`
        def inner_cmp(a, b):
            a_group = self._get_group_no(a)
            b_group = self._get_group_no(b)

            # cmp is a built-in python function
            if a_group == b_group:
                return a > b  
            return a_group > b_group
        
        return sorted(tags, key=functools.cmp_to_key(inner_cmp))


class WordForm(object):
    """
    Class that represents single word form.
    Initialized out of form and tags strings from LT dictionary.
    """
    def __init__(self, form, tags, exact_pos, is_lemma=False):
        if ":&pron" in tags:
            tags = re.sub(
                "([a-z][^:]+)(.*):&pron((:pers|:refl|:pos|:dem|:def|:int" +
                "|:rel|:neg|:ind|:gen)+)(.*)", "pron\\3\\2\\4", tags)
        self.form, self.tags = form, tags

        # self.tags = map(strip_func, self.tags.split(","))
        self.tags = {s.strip() for s in self.tags}
        self.is_lemma = is_lemma

        # tags signature is string made out of sorted list of wordform tags
        # This is a workout for rare cases when some wordform has
        # noun:m:v_naz and another has noun:v_naz:m
        self.tags_signature = ",".join(sorted(self.tags))

        # Here we are trying to determine exact part of speech for this
        # wordform
        self.pos = exact_pos

    def __str__(self):
        return "<%s: %s>" % (self.form, self.tags_signature)

    def __unicode__(self):
        return self.__str__()


class Lemma(object):
    def __init__(self, word, lemma_form_tags, exact_pos):
        self.word = word

        self.lemma_form = WordForm(word, lemma_form_tags, exact_pos, True)
        self.pos = self.lemma_form.pos
        self.forms = {}
        self.common_tags = None

        self.add_form(self.lemma_form)

    def __str__(self):
        return "%s" % self.lemma_form

    @property
    def lemma_signature(self):
        return (self.word,) + tuple(self.common_tags)

    def add_form(self, form):
        if self.common_tags is not None:
            self.common_tags = self.common_tags.intersection(form.tags)
        else:
            self.common_tags = set(form.tags)

        if (form.tags_signature in self.forms and
                form.form != self.forms[form.tags_signature][0].form):
            doubleform_signal.send(self, tags_signature=form.tags_signature)

            self.forms[form.tags_signature].append(form)

            logging.debug(
                "lemma %s got %s forms with same tagset %s: %s" %
                (self, len(self.forms[form.tags_signature]),
                 form.tags_signature,
                 ", ".join(map(lambda x: x.form,
                               self.forms[form.tags_signature]))))
        else:
            self.forms[form.tags_signature] = [form]

    def _add_tags_to_element(self, el, tags, tag_set_full):
        tags = tag_set_full.sort_tags(tags)

        for one_tag in tags:
            if one_tag != '':
                if  one_tag not in tag_set_full.lt2opencorpora and one_tag not in tag_set_full.lt2opencorpora.values():
                    raise KeyError(f"{(self.word, self.pos)} has unrecognized tag {one_tag}!")
                else:
                    ET.SubElement(el, "g", v=tag_set_full.lt2opencorpora.get(one_tag, one_tag))

    def export_to_xml(self, i, tag_set_full, translate_func, rev=1):
        lemma = ET.Element("lemma", id=str(i), rev=str(rev))
        common_tags = list(self.common_tags or set())

        if not common_tags:
            logging.debug(
                "Lemma %s has no tags at all" % self.lemma_form)

            return None

        output_lemma_form = self.lemma_form.form.lower()
        output_lemma_form = translate_func(output_lemma_form)
        l_form = ET.SubElement(lemma, "l", t=output_lemma_form)

        self._add_tags_to_element(l_form, common_tags, tag_set_full)

        for forms in self.forms.values():
            for form in forms:
                output_form = form.form.lower()
                output_form = translate_func(output_form)
                el = ET.Element("f", t=output_form)
                if form.is_lemma:
                    if len(self.forms) == 1:
                        lemma.insert(1, el)
                else:
                    lemma.append(el)

                self._add_tags_to_element(el,
                                          set(form.tags) - set(common_tags),
                                          tag_set_full)

        return lemma
