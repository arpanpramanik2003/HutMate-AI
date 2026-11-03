import pytest
from core.i18n import detect_message_language, normalize_item_name, get_item_localized_display

def test_detect_language_script():
    # Bengali script detection
    res_bn = detect_message_language("আমাদের কাছে কি আলু আছে?")
    assert res_bn["language"] == "bn"
    assert res_bn["detected_script"] == "bengali"

    # Devanagari script detection
    res_hi = detect_message_language("क्या हमारे पास पनीर है?")
    assert res_hi["language"] == "hi"
    assert res_hi["detected_script"] == "devanagari"

def test_detect_explicit_commands():
    # Explicit Bengali
    res_bn1 = detect_message_language("speak in bengali from now on")
    assert res_bn1["language"] == "bn"
    assert res_bn1["is_explicit_switch"] is True

    res_bn2 = detect_message_language("বাংলায় কথা বলুন")
    assert res_bn2["language"] == "bn"
    assert res_bn2["is_explicit_switch"] is True

    # Explicit Hindi
    res_hi = detect_message_language("now switch to hindi please")
    assert res_hi["language"] == "hi"
    assert res_hi["is_explicit_switch"] is True

    # Explicit English
    res_en = detect_message_language("speak in english please")
    assert res_en["language"] == "en"
    assert res_en["is_explicit_switch"] is True

def test_detect_banglish_and_hinglish():
    # Banglish keywords
    res_banglish = detect_message_language("amader kache ki alu ache?")
    assert res_banglish["language"] == "bn"

    res_banglish2 = detect_message_language("5 packet alu add koro")
    assert res_banglish2["language"] == "bn"

    # Hinglish keywords
    res_hinglish = detect_message_language("kya hamare paas paneer hai?")
    assert res_hinglish["language"] == "hi"

def test_fuzzy_and_typos():
    norm1 = normalize_item_name("potto")
    assert norm1["canonical"] == "Potatoes"

    norm2 = normalize_item_name("cheez")
    assert norm2["canonical"] == "Cheese"

    norm3 = normalize_item_name("chikn")
    assert norm3["canonical"] == "Chicken Breast"

