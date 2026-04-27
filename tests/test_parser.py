"""
Unit tests for src/parser.py — covers instruction parsing, grouping,
multi-extension detection, and data loading logic.
"""
import json
import pytest
from pathlib import Path
from src.parser import load_instruction_data, parse_instructions


# ---------------------------------------------------------------------------
# Fixtures — minimal synthetic instruction data
# ---------------------------------------------------------------------------

@pytest.fixture
def single_ext_data():
    """Each instruction belongs to exactly one extension."""
    return {
        "add":  {"extension": ["rv_i"], "encoding": "0" * 32},
        "sub":  {"extension": ["rv_i"], "encoding": "0" * 32},
        "mul":  {"extension": ["rv_m"], "encoding": "0" * 32},
    }


@pytest.fixture
def multi_ext_data():
    """Some instructions appear in multiple extensions (crypto overlap pattern)."""
    return {
        "andn":       {"extension": ["rv_zbb", "rv_zbkb", "rv_zk"], "encoding": "0" * 32},
        "add":        {"extension": ["rv_i"],                         "encoding": "0" * 32},
        "clmul":      {"extension": ["rv_zbc", "rv_zbkc"],            "encoding": "0" * 32},
        "sha256sig0": {"extension": ["rv_zknh", "rv_zkn", "rv_zk"],   "encoding": "0" * 32},
    }


@pytest.fixture
def edge_case_data():
    """Edge cases: empty extension list, string instead of list, no entries."""
    return {
        "mystery":  {"encoding": "0" * 32},                     # missing 'extension' key
        "weird":    {"extension": [], "encoding": "0" * 32},     # empty list
        "lone":     {"extension": ["rv_x"], "encoding": "0" * 32},
    }


# ---------------------------------------------------------------------------
# Tests: data loading
# ---------------------------------------------------------------------------

class TestLoadInstructionData:

    def test_loads_valid_json(self, tmp_path):
        payload = {"add": {"extension": ["rv_i"], "encoding": "0" * 32}}
        f = tmp_path / "instr_dict.json"
        f.write_text(json.dumps(payload), encoding="utf-8")
        result = load_instruction_data(f)
        assert result == payload

    def test_raises_on_missing_file(self, tmp_path):
        with pytest.raises(FileNotFoundError, match="instr_dict.json not found"):
            load_instruction_data(tmp_path / "nonexistent.json")

    def test_returns_dict(self, tmp_path):
        f = tmp_path / "instr_dict.json"
        f.write_text("{}", encoding="utf-8")
        assert isinstance(load_instruction_data(f), dict)


# ---------------------------------------------------------------------------
# Tests: grouping
# ---------------------------------------------------------------------------

class TestGroupingByExtension:

    def test_basic_grouping(self, single_ext_data):
        ext_map, _ = parse_instructions(single_ext_data)
        assert "rv_i" in ext_map
        assert "rv_m" in ext_map
        assert set(ext_map["rv_i"]) == {"add", "sub"}
        assert ext_map["rv_m"] == ["mul"]

    def test_all_instructions_accounted_for(self, single_ext_data):
        ext_map, _ = parse_instructions(single_ext_data)
        all_grouped = [i for instrs in ext_map.values() for i in instrs]
        assert sorted(all_grouped) == sorted(single_ext_data.keys())

    def test_multi_extension_instruction_appears_in_each(self, multi_ext_data):
        ext_map, _ = parse_instructions(multi_ext_data)
        assert "andn" in ext_map["rv_zbb"]
        assert "andn" in ext_map["rv_zbkb"]
        assert "andn" in ext_map["rv_zk"]

    def test_returns_plain_dict(self, single_ext_data):
        ext_map, multi = parse_instructions(single_ext_data)
        assert isinstance(ext_map, dict)
        assert isinstance(multi, dict)


# ---------------------------------------------------------------------------
# Tests: multi-extension detection
# ---------------------------------------------------------------------------

class TestMultiExtensionDetection:

    def test_single_ext_not_in_multi(self, single_ext_data):
        _, multi = parse_instructions(single_ext_data)
        assert "add" not in multi
        assert "mul" not in multi

    def test_multi_ext_instructions_detected(self, multi_ext_data):
        _, multi = parse_instructions(multi_ext_data)
        assert "andn" in multi
        assert "clmul" in multi
        assert "sha256sig0" in multi

    def test_single_ext_instruction_excluded(self, multi_ext_data):
        _, multi = parse_instructions(multi_ext_data)
        assert "add" not in multi

    def test_correct_extensions_recorded(self, multi_ext_data):
        _, multi = parse_instructions(multi_ext_data)
        assert set(multi["clmul"]) == {"rv_zbc", "rv_zbkc"}
        assert set(multi["sha256sig0"]) == {"rv_zknh", "rv_zkn", "rv_zk"}

    def test_extension_list_is_sorted(self, multi_ext_data):
        """Extension lists must be sorted for deterministic, reproducible output."""
        _, multi = parse_instructions(multi_ext_data)
        for mnemonic, exts in multi.items():
            assert exts == sorted(exts), f"{mnemonic} extension list is not sorted"

    def test_no_duplicate_extensions_in_multi(self):
        duped = {
            "dup_instr": {"extension": ["rv_a", "rv_a", "rv_b"], "encoding": "0" * 32}
        }
        _, multi = parse_instructions(duped)
        assert "dup_instr" in multi
        assert len(multi["dup_instr"]) == len(set(multi["dup_instr"]))


# ---------------------------------------------------------------------------
# Tests: edge cases
# ---------------------------------------------------------------------------

class TestEdgeCases:

    def test_missing_extension_key_skipped(self, edge_case_data):
        ext_map, _ = parse_instructions(edge_case_data)
        all_grouped = [i for instrs in ext_map.values() for i in instrs]
        assert "mystery" not in all_grouped

    def test_empty_extension_list_skipped(self, edge_case_data):
        ext_map, _ = parse_instructions(edge_case_data)
        all_grouped = [i for instrs in ext_map.values() for i in instrs]
        assert "weird" not in all_grouped

    def test_empty_input(self):
        ext_map, multi = parse_instructions({})
        assert ext_map == {}
        assert multi == {}

    def test_non_list_extension_coerced(self):
        data = {"fence": {"extension": "rv_i", "encoding": "0" * 32}}
        ext_map, _ = parse_instructions(data)
        assert "fence" in ext_map.get("rv_i", [])
