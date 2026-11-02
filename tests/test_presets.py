"""Presets: Vollständigkeit, gültige Werte, Standard-Preset = Standardeinstellungen, jedes Preset zeigt etwas anderes."""

import gvz_constants as C
import gvz_evaluation as ev
import gvz_presets as P


def test_every_preset_has_help_and_all_keys():
    assert set(C.PRESETS) == set(C.PRESET_HELP)
    for name, preset in C.PRESETS.items():
        assert set(preset) == set(P.PRESET_KEYS), name
        assert C.PRESET_HELP[name]


def test_preset_values_are_inside_the_regler_bounds():
    for name, preset in C.PRESETS.items():
        spec = P.SETTING_SPECS
        assert preset["family"] in C.FAMILIES and preset["method"] in C.AVAILABLE[preset["family"]], name
        for field, key in P.PRESET_KEYS.items():
            lo, hi = spec[key].lo, spec[key].hi
            if lo is not None:
                assert lo <= preset[field] <= hi, (name, field)
        assert preset["n"] <= C.N_CAP[preset["family"]], name


def test_default_preset_equals_default_settings_and_comes_first():
    first = next(iter(C.PRESETS.values()))
    for field, key in P.PRESET_KEYS.items():
        assert first[field] == P.SETTING_SPECS[key].default
    assert first["family"] == C.DEFAULT_FAMILY and first["method"] == C.DEFAULT_METHOD


def test_every_preset_passes_the_checker_without_notes_or_problems():
    for name, preset in C.PRESETS.items():
        a = ev.analyse(ev.Settings(**preset))
        assert a.problems == [] and a.notes == [] and a.n_eff == preset["n"] and a.draws_done == preset["draws"], name


def test_presets_differ_from_the_default_in_at_least_two_fields_and_from_each_other():
    default = next(iter(C.PRESETS.values()))
    seen = set()
    for name, preset in list(C.PRESETS.items())[1:]:
        assert sum(preset[f] != default[f] for f in preset) >= 2, name
    for preset in C.PRESETS.values():
        key = tuple(sorted(preset.items()))
        assert key not in seen
        seen.add(key)


def test_every_family_and_method_appears_in_a_preset():
    assert {p["family"] for p in C.PRESETS.values()} == set(C.FAMILIES)
    assert {p["method"] for p in C.PRESETS.values()} == set(C.METHODS)


def test_setting_specs_cover_every_preset_key():
    assert set(P.PRESET_KEYS.values()) == set(P.SETTING_SPECS)
    assert P.SETTING_SPECS["family_select"].choices == C.FAMILIES and P.SETTING_SPECS["method_select"].choices == C.METHODS
