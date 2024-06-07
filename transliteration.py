import unicodedata
from string import whitespace


# TODO: move this to normalizacija.py or constants.py
diacr_letters = "žčšěйćżęųœ"
plain_letters = "жчшєjчжеуо"

lat_alphabet = "abcčdeěfghijjklmnoprsštuvyzž"
cyr_alphabet = "абцчдеєфгхийьклмнопрсштувызж"


save_diacrits = str.maketrans(diacr_letters, plain_letters)
cyr2lat_trans = str.maketrans(cyr_alphabet, lat_alphabet)
lat2cyr_trans = str.maketrans(lat_alphabet, cyr_alphabet)

nms_alphabet = "ęėåȯųćđřŕľńťďśźìóáýéíĵœ"
std_alphabet = "eeaoučđrrlntdszioayeijo"

nms2std_trans = str.maketrans(nms_alphabet, std_alphabet)

extended_nms_alphabet = "áàâāíìîīĭıąǫũéēĕëèœóôŏöòȯĵĺļǉýłçʒřťďśńź"
regular_etym_alphabet = "aaaaiiiiiiųųųeeėėėoooȯȯȯȯjľľľylczŕťďśńź"

ext_nms2std_nms_trans = str.maketrans(extended_nms_alphabet, regular_etym_alphabet)


def lat2cyr(thestring):

    # "e^" -> "ê"
    # 'z\u030C\u030C\u030C' -> 'ž\u030C\u030C'
    thestring = unicodedata.normalize(
        'NFKC',
        thestring
    ).lower().replace("\n", " ")

    # remove all diacritics beside haceks/carons
    thestring = unicodedata.normalize(
        'NFKD',
        thestring.translate(save_diacrits)
    )
    filtered = "".join(c for c in thestring if c in whitespace or c.isalpha())
    # cyrillic to latin
    filtered = filtered.replace(
        "đ", "dž").replace(
        # Serbian and Macedonian
        "љ", "ль").replace("њ", "нь").replace(
        # Russian
        "я", "йа").replace("ю", "йу").replace("ё", "йо")

    return filtered.translate(lat2cyr_trans).replace("й", "ј").replace("ь", "ј").strip()


def lat2etm(thestring):
    # hack with dʒ
    return thestring.translate(ext_nms2std_nms_trans).replace("đ", "dʒ").strip()


def lat2std(thestring):
    return thestring.translate(nms2std_trans).replace("đ", "dž").strip()


translation_functions = {
    "isv_cyr": lat2cyr,
    "isv_lat": lat2std,
    "isv_etm": lat2etm,
}

