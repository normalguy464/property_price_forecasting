import re
import unicodedata

import pandas as pd


def normalize_text(value):
    if pd.isna(value):
        return "__missing__"
    text = unicodedata.normalize("NFC", str(value)).replace("\u00a0", " ")
    text = re.sub(r"[–—]", "-", text)
    text = re.sub(r"\s+", " ", text).strip().casefold()
    return text if text else "__missing__"


def strip_accents(value):
    text = normalize_text(value).replace("đ", "d")
    text = unicodedata.normalize("NFD", text)
    return "".join(character for character in text if unicodedata.category(character) != "Mn")


def canonical_shape(value):
    text = strip_accents(value)
    if "khong can doi" in text:
        return "khong_can_doi"
    if "kha can doi" in text:
        return "kha_can_doi"
    if "can doi" in text or "vuong vuc" in text:
        return "can_doi"
    if "no hau" in text:
        return "no_hau"
    if "top hau" in text:
        return "top_hau"
    if "chu l" in text or "hinh l" in text:
        return "hinh_chu_l"
    if "phuc tap" in text or "da giac" in text:
        return "phuc_tap"
    return "khac"


def canonical_land_use(value):
    text = strip_accents(value)
    if "nong thon" in text:
        return "dat_o_nong_thon"
    if "do thi" in text:
        return "dat_o_do_thi"
    if "dat o" in text:
        return "dat_o"
    return "khac"


def canonical_business_advantage(value):
    text = strip_accents(value)
    mapping = {"kem": "kem", "trung binh": "trung_binh", "kha": "kha", "tot": "tot"}
    return mapping.get(text, "khac")
