# RISC-V Instruction Set Explorer

A Python tool built for the RISC-V Mentorship Coding Challenge. It parses the RISC-V instruction set, cross-references extensions against the official ISA manual, and visualises which extensions share instructions — all from locally cloned data, with no runtime network calls.

---

## Project Structure

```
risc-v-explorer/
├── main.py                   # Unified entry point (runs all tiers)
├── requirements.txt
├── src/
│   ├── parser.py             # Tier 1 — instruction parsing and grouping
│   ├── cross_reference.py    # Tier 2 — ISA manual cross-reference
│   └── graph.py              # Tier 3 — extension sharing graph
├── tests/
│   ├── test_parser.py        # 47 unit tests, zero network calls
│   └── test_cross_reference.py
└── data/                     # Local clones (git-ignored, set up manually)
    ├── riscv-extensions-landscape/
    └── riscv-isa-manual/
```

---

## Setup

### 1. Clone the repository

```bash
git clone https://github.com/mohdsahlpa/risc-v-explorer.git
cd risc-v-explorer
```

### 2. Create and activate a virtual environment

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate
```

### 3. Install dependencies

This project uses [`uv`](https://github.com/astral-sh/uv) for fast installation:

```bash
pip install uv
uv pip install -r requirements.txt
```

### 4. Clone the data repositories

Both repositories are read from disk at runtime. Clone them once into `data/`:

```bash
git clone --depth=1 https://github.com/rpsene/riscv-extensions-landscape.git data/riscv-extensions-landscape
git clone --depth=1 https://github.com/riscv/riscv-isa-manual.git data/riscv-isa-manual
```

The `data/` directory is git-ignored and never committed.

---

## Running

```bash
python main.py
# or
uv run main.py
```

Runs all three tiers in sequence. No environment variables or network access required.

---

## Running the Tests

```bash
python -m pytest tests/ -v
```

**47 tests**, all self-contained using `pytest`'s `tmp_path` fixture — no network calls, no data/ dependency.

---

## Sample Output

### Tier 1 — Extension Summary

```
=== Extension Summary ===
Extension Tag        | Count | Example Mnemonic
-------------------------------------------------------
rv_i                 | 37 instructions | e.g. ADD
rv_m                 | 8 instructions  | e.g. DIV
rv_zba               | 3 instructions  | e.g. SH1ADD
rv_v                 | 627 instructions | e.g. VAADD_VV
...

=== Instructions in Multiple Extensions ===
ANDN            : rv_zbkb, rv_zk, rv_zkn, rv_zks, rv_zbb
SHA256SIG0      : rv_zk, rv_zkn, rv_zknh
```

### Tier 2 — Cross-Reference Report

```
=== Cross-Reference Report ===

-- Extensions in both JSON and manual (52) --
  rv_zba                     (normalised: zba)
  rv_zicsr                   (normalised: zicsr)
  ...

-- In JSON only — not found in manual (33) --
  rv_zvfbdot32f              (normalised: zvfbdot32f)
  ...

-- In manual only — not in JSON (77) --
  svnapot
  svpbmt
  ...

Summary: 52 matched, 33 in JSON only, 77 in manual only
(85 unique JSON extensions, 129 unique manual extensions)
```

### Tier 3 — Extension Sharing Graph

```
=== Extension Sharing Graph ===
  Nodes (extensions):   32
  Edges (shared pairs): 57
  Connected clusters:   4

-- Shared-Instruction Edges (sorted by shared count desc) --
  rv64_zk <-> rv64_zkn  |  16 shared: AES64DS, AES64DSM, AES64ES...
  rv_zkn  <-> rv_zk     |  15 shared: ANDN, CLMUL, CLMULH...

-- Connected Clusters --
  Cluster 1 (11): rv_zbb, rv_zbc, rv_zbkb, rv_zbkc, rv_zbkx, rv_zk, rv_zkn, rv_zknh, rv_zks, rv_zksed, rv_zksh
  Cluster 2 (8):  rv64_zbb, rv64_zbkb, rv64_zk, rv64_zkn, rv64_zknd, rv64_zkne, rv64_zknh, rv64_zks
  Cluster 3 (8):  rv_zvbb, rv_zvkn, rv_zvkned, rv_zvknha, rv_zvknhb, rv_zvks, rv_zvksed, rv_zvksh
  Cluster 4 (5):  rv32_zk, rv32_zkn, rv32_zknd, rv32_zkne, rv32_zknh
```

---

## Assumptions and Design Decisions

### Extension name normalisation (Tier 2)

The JSON file uses prefixed names (`rv_zba`, `rv64_zbkb`) while the ISA manual uses bare names (`Zba`, `Zbkb`). Both sides are normalised to lowercase bare names by stripping the `rv_`, `rv32_`, and `rv64_` prefixes before comparison. This is the primary data mismatch the spec calls out and requires careful handling.

### AsciiDoc scanning approach

Two regex patterns are used:
- **`Z*` / `Sv*` pattern**: matches multi-character extension names (e.g. `Zba`, `Svnapot`) at word boundaries, covering both heading and inline references.
- **Single-letter pattern**: only matches base ISA letters (`M`, `F`, `D`, etc.) when explicitly followed by `extension` or `standard` — prevents matching stray uppercase letters in prose.

A noise deny-list filters out author names and English words that start with `z` and pass the regex (e.g. `zeroed`, `zeroing`, `zext`).

### Data locality

Both source repositories are cloned once under `data/` and read from disk. This eliminates GitHub API rate limits, removes the `requests` dependency entirely, and makes the tool fully reproducible offline.

### Deterministic output

Extension lists in `multi_ext_instructions` are stored in `sorted()` order, and shared instruction lists on graph edges are also sorted. This ensures identical output on every run regardless of Python's internal set/dict ordering.

### Extension sharing graph (Tier 3)

Built from the multi-extension instruction map produced in Tier 1. Two extensions are connected if they share at least one instruction mnemonic. Edges carry the full sorted list of shared mnemonics and a weight (count). Connected component analysis reveals four distinct extension clusters, all within the cryptography and vector ISA sub-families.

### AI-assisted development

This project was developed with the assistance of AI tooling to accelerate workflow, drafting, and iteration — under active human supervision throughout. All logic, design choices, normalisation decisions, and output were reviewed and validated manually to ensure correctness and that nothing spurious made it into the final submission.

---

## Dependencies

| Package    | Purpose                                   |
|------------|-------------------------------------------|
| `networkx` | Graph construction and cluster analysis   |
| `pytest`   | Unit testing framework                    |
| `uv`       | Fast package installation (optional)      |
