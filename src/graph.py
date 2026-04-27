"""
Tier 3 bonus: builds and renders a text-based graph showing which
RISC-V extensions share at least one instruction.

Each node is an extension. An edge between two nodes means they have
at least one instruction mnemonic in common.
"""
import networkx as nx
from collections import defaultdict


def build_shared_graph(multi_ext_instructions: dict) -> nx.Graph:
    """
    Builds an undirected graph from the multi-extension instruction map.

    Nodes  — extension names
    Edges  — two extensions are connected if they share >= 1 instruction,
             with an 'instructions' attribute listing the shared mnemonics.
    """
    G = nx.Graph()
    # Track which pairs share which instructions
    pair_to_instrs: dict[tuple, list] = defaultdict(list)

    for instr, exts in multi_ext_instructions.items():
        for i in range(len(exts)):
            for j in range(i + 1, len(exts)):
                pair = tuple(sorted([exts[i], exts[j]]))
                pair_to_instrs[pair].append(instr)

    for (ext_a, ext_b), shared in pair_to_instrs.items():
        G.add_edge(ext_a, ext_b, instructions=sorted(shared), weight=len(shared))

    return G


def print_graph_report(G: nx.Graph) -> None:
    """
    Prints a text-based summary of the extension-sharing graph.
    Lists connected components, then each edge with shared instruction count.
    """
    print("\n=== Extension Sharing Graph ===")
    print(f"  Nodes (extensions):  {G.number_of_nodes()}")
    print(f"  Edges (shared pairs): {G.number_of_edges()}")

    components = list(nx.connected_components(G))
    print(f"  Connected clusters:  {len(components)}")

    print("\n-- Shared-Instruction Edges (sorted by shared count desc) --")
    edges = sorted(
        G.edges(data=True),
        key=lambda e: e[2]["weight"],
        reverse=True,
    )
    for ext_a, ext_b, data in edges:
        count = data["weight"]
        sample = ", ".join(i.upper() for i in data["instructions"][:3])
        suffix = "..." if count > 3 else ""
        print(f"  {ext_a} <-> {ext_b}")
        print(f"    {count} shared instruction(s): {sample}{suffix}")

    print("\n-- Connected Clusters --")
    for idx, component in enumerate(
        sorted(components, key=len, reverse=True), start=1
    ):
        members = ", ".join(sorted(component))
        print(f"  Cluster {idx} ({len(component)} extensions): {members}")
