"""
Unit tests for src/cross_reference.py — covers normalisation, noise filtering,
manual scanning, and cross-reference logic.
"""
import pytest
from pathlib import Path
from src.cross_reference import (
    normalize_json_ext,
    normalize_manual_token,
    build_manual_ext_set,
    cross_reference,
    scan_manual_src,
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
        result = build_manual_ext_set({"zero", "zhang", "zabrocki", "zeroed", "zeroing", "zext"})
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
# Tests: scan_manual_src
# ---------------------------------------------------------------------------

class TestScanManualSrc:

    def test_raises_on_missing_directory(self, tmp_path):
        with pytest.raises(FileNotFoundError, match="ISA manual src/"):
            scan_manual_src(tmp_path / "nonexistent")

    def test_finds_z_extensions_in_adoc(self, tmp_path):
        adoc = tmp_path / "test.adoc"
        adoc.write_text(
            "The Zba extension adds address generation instructions.\n"
            "See also Zicsr for CSR access.",
            encoding="utf-8"
        )
        result = scan_manual_src(tmp_path)
        assert "zba" in result
        assert "zicsr" in result

    def test_finds_single_letter_ext_phrasing(self, tmp_path):
        adoc = tmp_path / "base.adoc"
        adoc.write_text(
            "The M extension provides multiply and divide instructions.",
            encoding="utf-8"
        )
        result = scan_manual_src(tmp_path)
        assert "m" in result

    def test_ignores_non_adoc_files(self, tmp_path):
        txt = tmp_path / "notes.txt"
        txt.write_text("The Zba extension is great.", encoding="utf-8")
        result = scan_manual_src(tmp_path)
        assert "zba" not in result

    def test_scans_subdirectories(self, tmp_path):
        subdir = tmp_path / "unpriv"
        subdir.mkdir()
        adoc = subdir / "zba.adoc"
        adoc.write_text("Zba extension provides SH1ADD.\n", encoding="utf-8")
        result = scan_manual_src(tmp_path)
        assert "zba" in result

    def test_empty_directory_returns_empty_set(self, tmp_path):
        result = scan_manual_src(tmp_path)
        assert result == set()


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

    def test_manual_only_list_sorted(self):
        json_tags = {"rv_zba"}
        manual_names = {"zba", "svnapot", "zicntr", "zalrsc"}
        result = cross_reference(json_tags, manual_names)
        assert result["manual_only"] == sorted(result["manual_only"])
