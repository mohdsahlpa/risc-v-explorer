"""
Tier 1 — Instruction Set Parsing

Reads instr_dict.json from the locally cloned riscv-extensions-landscape
repository, groups instructions by extension tag, and identifies instructions
that belong to more than one extension.
"""
import json
import os
from collections import defaultdict
from pathlib import Path

# Path to instr_dict.json relative to the project root
_DEFAULT_JSON = Path(__file__).parent.parent / "data" / "riscv-extensions-landscape" / "src" / "instr_dict.json"


def load_instruction_data(path: Path = _DEFAULT_JSON) -> dict:
    """
    Loads and returns the instruction dictionary from disk.

    Args:
        path: Absolute or relative path to instr_dict.json.

    Raises:
        FileNotFoundError: If the file does not exist at the given path.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(
            f"instr_dict.json not found at {path}.\n"
            "Run: git clone --depth=1 "
            "https://github.com/rpsene/riscv-extensions-landscape.git data/riscv-extensions-landscape"
        )
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def parse_instructions(data: dict) -> tuple[dict, dict]:
    """
    Parses the instruction dictionary and groups instructions by extension tag.

    Args:
        data: The raw instruction dictionary from instr_dict.json.

    Returns:
        extensions_map:
            Maps each extension tag to the list of mnemonic strings it contains.
        multi_ext_instructions:
            Maps each mnemonic to its list of extension tags, but only for
            mnemonics that appear in more than one extension.
    """
    extensions_map: dict[str, list] = defaultdict(list)
    multi_ext_instructions: dict[str, list] = {}

    for mnemonic, details in data.items():
        extensions = details.get("extension", [])

        # Coerce bare string to list (defensive — JSON spec uses lists)
        if isinstance(extensions, str):
            extensions = [extensions]

        for ext in extensions:
            extensions_map[ext].append(mnemonic)

        unique_exts = list(set(extensions))
        if len(unique_exts) > 1:
            multi_ext_instructions[mnemonic] = unique_exts

    return dict(extensions_map), multi_ext_instructions


def print_summary(extensions_map: dict, multi_ext_instructions: dict) -> None:
    """
    Prints the Tier 1 summary table and multi-extension instruction list.
    """
    print("=== Extension Summary ===")
    print(f"{'Extension Tag':<20} | {'Count':<5} | {'Example Mnemonic'}")
    print("-" * 55)

    for ext, instrs in sorted(extensions_map.items()):
        count = len(instrs)
        example = instrs[0] if instrs else "N/A"
        label = "instruction" if count == 1 else "instructions"
        print(f"{ext:<20} | {count} {label} | e.g. {example.upper()}")

    print("\n=== Instructions in Multiple Extensions ===")
    if not multi_ext_instructions:
        print("None found.")
        return

    for mnemonic, exts in sorted(multi_ext_instructions.items()):
        print(f"{mnemonic.upper():<15} : {', '.join(sorted(exts))}")
