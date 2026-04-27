import re
import os
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

# Single-call Git Trees API — returns the full repo tree in one request,
# avoiding unauthenticated rate limits that hit per directory traversal.
_TREES_API = (
    "https://api.github.com/repos/riscv/riscv-isa-manual/git/trees/main?recursive=1"
)
_RAW_BASE = "https://raw.githubusercontent.com/riscv/riscv-isa-manual/main"

# Pattern 1: Explicit "X Extension" phrasing for single-letter base ISA
# e.g. "M extension", "F extension"
_SINGLE_LETTER_EXT = re.compile(
    r"(?<![`\w])([MFDACHQVS])(?:-extension|\s+extension|\s+standard)(?![\w])",
    re.IGNORECASE,
)

# Pattern 2: Multi-char extension names starting with Z or Sv (real extension names)
# e.g. Zba, Zicsr, Zifencei, Svnapot — must be at a word boundary, 3+ chars
_MULTI_CHAR_EXT = re.compile(
    r"(?<![`\w])([Zz][a-zA-Z][a-zA-Z0-9]{1,20}|[Ss]v[a-zA-Z][a-zA-Z0-9]{0,20})(?![\w])"
)


def _get_adoc_file_urls(token: str | None = None) -> list[str]:
    """
    Uses the Git Trees API (one request) to enumerate all .adoc files
    under src/ in the ISA manual repository, then builds raw content URLs.

    Accepts an optional GitHub personal access token to raise the rate limit
    from 60 to 5000 requests/hour (set the GITHUB_TOKEN env var).
    """
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    resp = requests.get(_TREES_API, headers=headers)
    resp.raise_for_status()

    tree = resp.json().get("tree", [])
    urls = []
    for item in tree:
        path: str = item.get("path", "")
        if item.get("type") == "blob" and path.startswith("src/") and path.endswith(".adoc"):
            urls.append(f"{_RAW_BASE}/{path}")
    return urls


def _fetch_and_scan(url: str) -> set[str]:
    """
    Downloads one .adoc file and returns all raw extension name
    strings found in it (unprocessed).
    """
    resp = requests.get(url)
    resp.raise_for_status()
    content = resp.text
    found = set()
    for match in _SINGLE_LETTER_EXT.finditer(content):
        found.add(match.group(1).lower())
    for match in _MULTI_CHAR_EXT.finditer(content):
        found.add(match.group(1).lower())
    return found


def fetch_manual_extensions(max_workers: int = 10) -> set[str]:
    """
    Fetches all .adoc files from the ISA manual concurrently and
    returns the raw set of extension name tokens found across all files.

    Reads GITHUB_TOKEN from the environment if set, which raises the
    API rate limit from 60 to 5000 req/hr for the initial tree lookup.
    Raw file downloads are not rate-limited regardless.
    """
    token = os.environ.get("GITHUB_TOKEN")
    print("Fetching file list from ISA manual repository...")
    urls = _get_adoc_file_urls(token=token)
    print(f"  Found {len(urls)} .adoc file(s). Scanning...")

    all_tokens: set[str] = set()
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(_fetch_and_scan, u): u for u in urls}
        for future in as_completed(futures):
            try:
                all_tokens |= future.result()
            except Exception:
                pass  # skip files that fail to fetch

    return all_tokens


def normalize_json_ext(tag: str) -> str:
    """
    Strips the 'rv_', 'rv32_', 'rv64_' prefix from a JSON extension tag
    and returns the bare name in lowercase for comparison.

    Examples:
        rv_zba      -> zba
        rv64_zbkb   -> zbkb
        rv32_zknd   -> zknd
        rv_i        -> i
    """
    tag = tag.lower()
    for prefix in ("rv32_", "rv64_", "rv_"):
        if tag.startswith(prefix):
            return tag[len(prefix):]
    return tag


def normalize_manual_token(token: str) -> str:
    """
    Normalises a raw token from the AsciiDoc source to a bare lowercase name
    suitable for comparison with normalised JSON tags.

    Examples:
        zba         -> zba
        zicsr       -> zicsr
        svnapot     -> svnapot
        m           -> m  (single-letter base ISA)
    """
    return token.lower().strip()


# Single-letter base ISA extensions that are valid RISC-V extension names
_KNOWN_SINGLE_LETTER = {"m", "f", "d", "a", "c", "h", "q", "v", "s"}

# Hard deny-list: tokens that match the regex but are definitely not extensions
_NOISE = {
    "zero", "zeros", "zeroes", "zhang", "zabrocki", "zandijk",  # author names / words
}


def build_manual_ext_set(raw_tokens: set[str]) -> set[str]:
    """
    Filters and normalises the raw token set from the AsciiDoc scan
    into a clean set of bare extension names.
    Single-letter entries are only kept if they're known base ISA letters.
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
        matched         - extensions present in both
        json_only       - in JSON but not in manual
        manual_only     - in manual but not in JSON
    """
    norm_json = {normalize_json_ext(t): t for t in json_ext_tags}
    norm_manual = manual_ext_names

    matched_keys = norm_json.keys() & norm_manual
    json_only_keys = norm_json.keys() - norm_manual
    manual_only_keys = norm_manual - norm_json.keys()

    return {
        "matched": {k: norm_json[k] for k in sorted(matched_keys)},
        "json_only": {k: norm_json[k] for k in sorted(json_only_keys)},
        "manual_only": sorted(manual_only_keys),
    }


def print_cross_reference_report(result: dict):
    """
    Prints the cross-reference summary report.
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
