"""
RISC-V Instruction Set Explorer
Entry point — runs Tier 1 (parsing), Tier 2 (cross-reference), and Tier 3 (graph).
"""
from src.parser import fetch_instruction_data, parse_instructions, print_summary
from src.cross_reference import (
    fetch_manual_extensions,
    build_manual_ext_set,
    cross_reference,
    print_cross_reference_report,
)
from src.graph import build_shared_graph, print_graph_report


def main():
    # --- Tier 1 ---
    print("=" * 60)
    print("Tier 1: Instruction Set Parsing")
    print("=" * 60)
    data = fetch_instruction_data()
    ext_map, multi_ext = parse_instructions(data)
    print_summary(ext_map, multi_ext)

    # --- Tier 2 ---
    print("\n" + "=" * 60)
    print("Tier 2: Cross-Reference with ISA Manual")
    print("=" * 60)
    raw_tokens = fetch_manual_extensions()
    manual_names = build_manual_ext_set(raw_tokens)
    result = cross_reference(set(ext_map.keys()), manual_names)
    print_cross_reference_report(result)

    # --- Tier 3: Bonus Graph ---
    print("\n" + "=" * 60)
    print("Tier 3: Extension Sharing Graph")
    print("=" * 60)
    G = build_shared_graph(multi_ext)
    print_graph_report(G)


if __name__ == "__main__":
    main()
