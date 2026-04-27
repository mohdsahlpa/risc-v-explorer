import requests
from collections import defaultdict

# URL to the raw instr_dict.json file in the repository
DATA_URL = "https://raw.githubusercontent.com/rpsene/riscv-extensions-landscape/main/src/instr_dict.json"

def fetch_instruction_data(url: str = DATA_URL) -> dict:
    """
    Fetches the instr_dict.json file from the specified URL.
    """
    response = requests.get(url)
    response.raise_for_status()
    return response.json()

def parse_instructions(data: dict):
    """
    Parses the instructions and groups them by extension tags.
    
    Returns:
        extensions_map: Dictionary mapping extension names to lists of instruction mnemonics.
        multi_ext_instructions: Dictionary mapping instruction mnemonics to lists of extension names 
                                for instructions belonging to >1 extension.
    """
    extensions_map = defaultdict(list)
    multi_ext_instructions = {}
    
    for instr, details in data.items():
        extensions = details.get("extension", [])
        
        if not isinstance(extensions, list):
            extensions = [extensions]
            
        for ext in extensions:
            extensions_map[ext].append(instr)
            
        # Identify instructions that belong to more than one extension
        # We need to ensure uniqueness in case the JSON has duplicates in the list
        unique_exts = list(set(extensions))
        if len(unique_exts) > 1:
            multi_ext_instructions[instr] = unique_exts
            
    return dict(extensions_map), multi_ext_instructions

def print_summary(extensions_map: dict, multi_ext_instructions: dict):
    """
    Prints the summary table and the list of multi-extension instructions.
    """
    print("=== Extension Summary ===")
    print(f"{'Extension Tag':<20} | {'Count':<5} | {'Example Mnemonic'}")
    print("-" * 55)
    
    for ext, instrs in sorted(extensions_map.items()):
        count = len(instrs)
        example = instrs[0] if count > 0 else "N/A"
        label = "instruction" if count == 1 else "instructions"
        print(f"{ext:<20} | {count} {label} | e.g. {example.upper()}")
        
    print("\n=== Instructions in Multiple Extensions ===")
    if not multi_ext_instructions:
        print("None found.")
    else:
        for instr, exts in sorted(multi_ext_instructions.items()):
            print(f"{instr.upper():<15} : {', '.join(exts)}")

def main():
    print("Fetching instruction data...")
    data = fetch_instruction_data()
    print("Parsing data...")
    ext_map, multi_ext = parse_instructions(data)
    print_summary(ext_map, multi_ext)

if __name__ == "__main__":
    main()
