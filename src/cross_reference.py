"""
Tier 2 — Cross-Reference with the ISA Manual

Scans the locally cloned riscv-isa-manual repository's src/ directory for
AsciiDoc files, extracts extension name mentions, and cross-references them
against the extension tags found in instr_dict.json.
"""
import re
import os
from pathlib import Path

# Default path to the locally cloned ISA manual repository
_DEFAULT_MANUAL_SRC = (
    Path(__file__).parent.parent / "data" / "riscv-isa-manual" / "src"
)

# Matches single-letter base ISA extensions when written as "M extension",
# "F extension", etc. — prevents matching stray uppercase letters.
_SINGLE_LETTER_EXT = re.compile(
    r"(?<![`\w])([MFDACHQVS])(?:-extension|\s+extension|\s+standard)(?![\w])",
    re.IGNORECASE,
)

# Matches multi-character extension names beginning with Z or Sv — the two
# naming conventions used in the RISC-V ISA (e.g. Zba, Zicsr, Svnapot).
_MULTI_CHAR_EXT = re.compile(
    r"(?<![`\w])([Zz][a-zA-Z][a-zA-Z0-9]{1,20}|[Ss]v[a-zA-Z][a-zA-Z0-9]{0,20})(?![\w])"
)

# Single-letter base ISA identifiers that are valid extension names
_KNOWN_SINGLE_LETTER = {"m", "f", "d", "a", "c", "h", "q", "v", "s"}

# Tokens that pass the regex but are not extension names (author names, words)
_NOISE = {"zero", "zeros", "zeroes", "zhang", "zabrocki", "zandijk"}


def scan_manual_src(src_dir: Path = _DEFAULT_MANUAL_SRC) -> set[str]:
    """
    Walks the ISA manual src/ directory and extracts raw extension name tokens
    from every .adoc file found (including subdirectories).

    Args:
        src_dir: Path to the src/ directory of a cloned riscv-isa-manual repo.

    Raises:
        FileNotFoundError: If src_dir does not exist.
    """
    src_dir = Path(src_dir)
    if not src_dir.is_dir():
        raise FileNotFoundError(
            f"ISA manual src/ directory not found at {src_dir}.\n"
            "Run: git clone --depth=1 "
            "https://github.com/riscv/riscv-isa-manual.git data/riscv-isa-manual"
        )

    found: set[str] = set()
    for adoc_file in src_dir.rglob("*.adoc"):
        try:
            content = adoc_file.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue

        for match in _SINGLE_LETTER_EXT.finditer(content):
            found.add(match.group(1).lower())
        for match in _MULTI_CHAR_EXT.finditer(content):
            found.add(match.group(1).lower())

    return found


def normalize_json_ext(tag: str) -> str:
    """
    Strips the rv_, rv32_, or rv64_ prefix from a JSON extension tag and
    returns the bare lowercase name for comparison.

    Examples:
        rv_zba    -> zba
        rv64_zbkb -> zbkb
        rv32_zknd -> zknd
        rv_i      -> i
    """
    tag = tag.lower()
    for prefix in ("rv32_", "rv64_", "rv_"):
        if tag.startswith(prefix):
            return tag[len(prefix):]
    return tag


def normalize_manual_token(token: str) -> str:
    """
    Normalises a raw AsciiDoc token to a bare lowercase extension name.
    """
    return token.lower().strip()


def build_manual_ext_set(raw_tokens: set[str]) -> set[str]:
    """
    Filters and normalises the raw token set from the AsciiDoc scan into a
    clean set of bare extension names, removing noise and invalid tokens.
    """
    cleaned = set()
    for tok in raw_tokens:
        normed = normalize_manual_token(tok)
        if not normed or normed in _NOISE:
            continue
        if len(normed) == 1 and normed not in _KNOWN_SINGLE_LETTER:
            continue
        cleaned.add(normed)
    return cleaned


def cross_reference(json_ext_tags: set[str], manual_ext_names: set[str]) -> dict:
    """
    Compares the normalised extension sets from the JSON and the manual.

    Returns a dict with keys:
        matched      - extensions present in both sources
        json_only    - in JSON but not mentioned in the manual
        manual_only  - mentioned in the manual but not in JSON
    """
    norm_json = {normalize_json_ext(t): t for t in json_ext_tags}

    matched_keys = norm_json.keys() & manual_ext_names
    json_only_keys = norm_json.keys() - manual_ext_names
    manual_only_keys = manual_ext_names - norm_json.keys()

    return {
        "matched": {k: norm_json[k] for k in sorted(matched_keys)},
        "json_only": {k: norm_json[k] for k in sorted(json_only_keys)},
        "manual_only": sorted(manual_only_keys),
    }


def print_cross_reference_report(result: dict) -> None:
    """
    Prints the Tier 2 cross-reference summary report.
    """
    matched = result["matched"]
    json_only = result["json_only"]
    manual_only = result["manual_only"]

    print("\n=== Cross-Reference Report ===")

    print(f"\n-- Extensions in both JSON and manual ({len(matched)}) --")
    for bare, original in matched.items():
        print(f"  {original:<25}  (normalised: {bare})")

    print(f"\n-- In JSON only — not found in manual ({len(json_only)}) --")
    if json_only:
        for bare, original in json_only.items():
            print(f"  {original:<25}  (normalised: {bare})")
    else:
        print("  None.")

    print(f"\n-- In manual only — not in JSON ({len(manual_only)}) --")
    if manual_only:
        for name in manual_only:
            print(f"  {name}")
    else:
        print("  None.")

    total_json = len(matched) + len(json_only)
    total_manual = len(matched) + len(manual_only)
    print(
        f"\nSummary: {len(matched)} matched, "
        f"{len(json_only)} in JSON only, "
        f"{len(manual_only)} in manual only "
        f"({total_json} unique JSON extensions, {total_manual} unique manual extensions)"
    )
