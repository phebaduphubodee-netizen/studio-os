import trade_dress as td


def test_cartier_by_material_name_and_image():
    mats = {"Rose Gold": [], "Cartier Gold.001": ["Cartier-logo.001"], "Tray.001": ["wicker_Roughness"]}
    s = td.scan(mats)
    assert list(s) == ["Cartier Gold.001"]
    assert "Cartier-logo.001" in s["Cartier Gold.001"]


def test_lv_texture_caught_by_separator_not_bare_letters():
    assert td.hits("LV_texture")
    assert td.hits("bag_LV")
    assert not td.hits("shelving")          # 'lv' inside a word is not a mark
    assert not td.hits("velvet_blue")


def test_substitute_prefers_flat_sibling_and_refuses_when_none():
    mats = {"Cartier Gold.001": ["Cartier-logo.001"], "Rose Gold": [], "Leather": ["leather_alb.png"]}
    assert td.pick_substitute("Cartier Gold.001", mats) == "Rose Gold"
    assert td.pick_substitute("Cartier Gold.001", {"Cartier Gold.001": ["Cartier-logo.001"]}) is None
    assert td.pick_substitute("A_logo", {"A_logo": [], "B_monogram": []}) is None


def test_clean_import_is_clean():
    assert td.scan({"wood": ["oak_alb.png", "oak_nrm.png"], "metal": []}) == {}
