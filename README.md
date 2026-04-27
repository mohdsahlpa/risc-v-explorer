# RISC-V Instruction Set Explorer

A Python tool that parses the RISC-V instruction set, groups instructions by extension, cross-references them against the official ISA manual, and visualises which extensions share instructions.

Built as part of the RISC-V Mentorship Coding Challenge.

---

## Project Structure

```
risc-v-explorer/
├── main.py                  # Unified entry point (runs all tiers)
├── requirements.txt
├── src/
│   ├── parser.py            # Tier 1 — instruction parsing and grouping
│   ├── cross_reference.py   # Tier 2 — ISA manual cross-reference
│   └── graph.py             # Tier 3 — extension sharing graph
└── tests/
    ├── test_parser.py
    └── test_cross_reference.py
```

---

## Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/mohdsahlpa/risc-v-explorer.git
cd risc-v-explorer
```

### 2. Set up a virtual environment (recommended)

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate
```

### 3. Install dependencies

This project uses [`uv`](https://github.com/astral-sh/uv) for fast, reliable package installation:

```bash
pip install uv
uv pip install -r requirements.txt
```

### 4. (Optional) Set a GitHub token

Tier 2 fetches files from the RISC-V ISA manual repository using the GitHub API.
The unauthenticated rate limit is 60 requests/hour. If you hit it, create a
[classic personal access token](https://github.com/settings/tokens) with no scopes
and export it before running:

```bash
# Windows PowerShell
$env:GITHUB_TOKEN = "ghp_your_token_here"

# macOS / Linux
export GITHUB_TOKEN="ghp_your_token_here"
```

---

## Running the Tool

```bash
python main.py
# or, using uv's runner
uv run main.py
```

This runs all three tiers in sequence:

- **Tier 1** — Fetches `instr_dict.json` and prints a summary table of extensions + multi-extension instructions
- **Tier 2** — Scans the ISA manual AsciiDoc sources and cross-references extension names
- **Tier 3** — Builds and prints the extension-sharing graph

---

## Running the Tests

```bash
python -m pytest tests/ -v
```

36 tests across two suites — no network calls, fully self-contained with synthetic fixtures.

---

## Sample Output

### Tier 1

```
=== Extension Summary ===
Extension Tag        | Count | Example Mnemonic
-------------------------------------------------------
rv_i                 | 37 instructions | e.g. ADD
rv_m                 | 8 instructions  | e.g. DIV
rv_zba               | 3 instructions  | e.g. SH1ADD
rv_zbb               | 17 instructions | e.g. ANDN
rv_v                 | 627 instructions| e.g. VAADD_VV
...

=== Instructions in Multiple Extensions ===
ANDN            : rv_zbb, rv_zbkb, rv_zk, rv_zkn, rv_zks
SHA256SIG0      : rv_zknh, rv_zkn, rv_zk
```

### Tier 2

```
=== Cross-Reference Report ===

-- Extensions in both JSON and manual (52) --
  rv_zba                     (normalised: zba)
  rv_zicsr                   (normalised: zicsr)
  ...

-- In JSON only — not found in manual (33) --
  rv_zvfbdot32f              (normalised: zvfbdot32f)
  ...

Summary: 52 matched, 33 in JSON only, 82 in manual only
```

### Tier 3

```
=== Extension Sharing Graph ===
  Nodes (extensions):   32
  Edges (shared pairs): 57
  Connected clusters:   4

-- Shared-Instruction Edges --
  rv64_zkn <-> rv64_zk  |  16 shared: AES64DS, AES64DSM, AES64ES...
  rv_zkn   <-> rv_zk    |  15 shared: ANDN, CLMUL, CLMULH...
  ...

-- Connected Clusters --
  Cluster 1 (11): rv_zbb, rv_zbc, rv_zbkb, rv_zbkc, rv_zbkx, rv_zk, ...
```

---

## Assumptions and Design Decisions

### Extension name normalisation (Tier 2)

The JSON file uses prefixed names (`rv_zba`, `rv64_zbkb`) while the ISA manual uses bare names (`Zba`, `Zbkb`). Normalisation strips the `rv_`, `rv32_`, and `rv64_` prefixes and lowercases both sides before comparison. This is the primary challenge the spec calls out and the main source of mismatches.

### Manual scanning approach

Rather than cloning the full repository, the tool fetches `.adoc` files remotely using the GitHub Git Trees API (a single API call for the file list, followed by concurrent raw content downloads). This avoids disk usage while keeping the scanning fast.

Two regex patterns are used:
- A strict `Z*` / `Sv*` pattern for multi-character extension names (e.g. `Zba`, `Svnapot`)
- An explicit phrasing pattern for single-letter base ISA extensions (e.g. `"M extension"`)

This keeps false positives low while capturing the real extension references in the spec.

### Shared-instruction graph (Tier 3)

The graph is built from the multi-extension instruction map produced in Tier 1. Nodes are extensions; edges are drawn between any two extensions that share at least one instruction mnemonic. The `networkx` library handles connected component analysis.

### AI-assisted development

This project was developed with the assistance of AI tooling to accelerate workflow, drafting, and iteration — under active human supervision throughout. All logic, design choices, and output were reviewed and validated manually to ensure correctness and that nothing spurious or inaccurate made it into the final submission.

---

## Dependencies

| Package    | Purpose                              |
|------------|--------------------------------------|
| `requests` | Fetching remote JSON and AsciiDoc    |
| `networkx` | Graph construction and analysis      |
| `pytest`   | Unit testing                         |
| `uv`       | Fast package installation (optional) |
