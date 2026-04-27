"""
Unit tests for src/cross_reference.py — covers normalization,
filtering, and cross-reference logic.
"""
import pytest
from src.cross_reference import (
    normalize_json_ext,
    normalize_manual_token,
    build_manual_ext_set,
    cross_reference,
)


# ---------------------------------------------------------------------------
# Tests: normalize_json_ext
# ---------------------------------------------------------------------------

class TestNormalizeJsonExt:

    def test_strips_rv_prefix(self):
        assert normalize_json_ext("rv_zba") == "zba"

    def test_strips_rv32_prefix(self):
        assert normalize_json_ext("rv32_zknd") == "zknd"

    def test_strips_rv64_prefix(self):
        assert normalize_json_ext("rv64_zbkb") == "zbkb"

    def test_no_prefix_unchanged(self):
        assert normalize_json_ext("zicsr") == "zicsr"

    def test_single_letter_ext(self):
        assert normalize_json_ext("rv_i") == "i"
        assert normalize_json_ext("rv_m") == "m"

    def test_case_insensitive(self):
        # Input might have uppercase; result should always be lowercase
        assert normalize_json_ext("RV_ZBA") == "zba"


# ---------------------------------------------------------------------------
# Tests: normalize_manual_token
# ---------------------------------------------------------------------------

class TestNormalizeManualToken:

    def test_lowercase_passthrough(self):
        assert normalize_manual_token("zba") == "zba"

    def test_uppercase_lowercased(self):
        assert normalize_manual_token("Zba") == "zba"
        assert normalize_manual_token("ZICSR") == "zicsr"

    def test_strips_whitespace(self):
        assert normalize_manual_token("  zba  ") == "zba"

    def test_svnapot(self):
        assert normalize_manual_token("Svnapot") == "svnapot"


# ---------------------------------------------------------------------------
# Tests: build_manual_ext_set
# ---------------------------------------------------------------------------

class TestBuildManualExtSet:

    def test_valid_z_extensions_kept(self):
        result = build_manual_ext_set({"zba", "zicsr", "zifencei"})
        assert "zba" in result
        assert "zicsr" in result

    def test_noise_tokens_removed(self):
        result = build_manual_ext_set({"zero", "zhang", "zabrocki"})
        assert len(result) == 0

    def test_known_single_letters_kept(self):
        result = build_manual_ext_set({"m", "f", "d", "a", "c", "h", "q", "v", "s"})
        assert "m" in result
        assert "f" in result

    def test_unknown_single_letters_removed(self):
        result = build_manual_ext_set({"x", "y", "z", "b", "e"})
        assert len(result) == 0

    def test_empty_token_skipped(self):
        result = build_manual_ext_set({""})
        assert "" not in result

    def test_sv_extensions_kept(self):
        result = build_manual_ext_set({"svnapot", "svpbmt"})
        assert "svnapot" in result
        assert "svpbmt" in result


# ---------------------------------------------------------------------------
# Tests: cross_reference
# ---------------------------------------------------------------------------

class TestCrossReference:

    def test_matched_set(self):
        json_tags = {"rv_zba", "rv_zicsr", "rv_m"}
        manual_names = {"zba", "zicsr", "svnapot"}
        result = cross_reference(json_tags, manual_names)
        assert "zba" in result["matched"]
        assert "zicsr" in result["matched"]

    def test_json_only(self):
        json_tags = {"rv_zba", "rv_zvabd"}
        manual_names = {"zba"}
        result = cross_reference(json_tags, manual_names)
        assert "zvabd" in result["json_only"]
        assert "zba" not in result["json_only"]

    def test_manual_only(self):
        json_tags = {"rv_zba"}
        manual_names = {"zba", "svnapot", "zicntr"}
        result = cross_reference(json_tags, manual_names)
        assert "svnapot" in result["manual_only"]
        assert "zicntr" in result["manual_only"]
        assert "zba" not in result["manual_only"]

    def test_empty_inputs(self):
        result = cross_reference(set(), set())
        assert result["matched"] == {}
        assert result["json_only"] == {}
        assert result["manual_only"] == []

    def test_no_overlap(self):
        json_tags = {"rv_zba"}
        manual_names = {"svnapot"}
        result = cross_reference(json_tags, manual_names)
        assert result["matched"] == {}
        assert "zba" in result["json_only"]
        assert "svnapot" in result["manual_only"]

    def test_prefix_variants_normalised_correctly(self):
        # rv32_zknd and rv64_zknd both normalise to 'zknd'
        # The dict will only keep one (last write wins on collision)
        json_tags = {"rv32_zknd", "rv64_zknd"}
        manual_names = {"zknd"}
        result = cross_reference(json_tags, manual_names)
        assert "zknd" in result["matched"]

    def test_result_keys_sorted(self):
        json_tags = {"rv_zicsr", "rv_zba", "rv_zifencei"}
        manual_names = {"zba", "zicsr", "zifencei"}
        result = cross_reference(json_tags, manual_names)
        keys = list(result["matched"].keys())
        assert keys == sorted(keys)
