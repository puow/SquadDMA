#!/usr/bin/env python3
"""
Find Missing UE5 Offsets - Enhanced Search
Searches for missing offsets with fuzzy matching and detailed output.
"""

import os
import re
from pathlib import Path


def search_class_fuzzy(sdk_path: Path, class_pattern: str):
    """Search for classes matching a pattern"""
    print(f"\n{'='*80}")
    print(f"Searching for classes matching: {class_pattern}")
    print(f"{'='*80}\n")

    found_classes = {}

    for sdk_file in sdk_path.rglob("*.hpp"):
        try:
            with open(sdk_file, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()

            # Find all class definitions
            pattern = rf'class\s+(\w*{class_pattern}\w*)\s*(?::\s*public\s+\w+\s*)?\{{'
            matches = re.finditer(pattern, content, re.IGNORECASE)

            for match in matches:
                class_name = match.group(1)
                if class_name not in found_classes:
                    found_classes[class_name] = sdk_file.name

        except Exception:
            pass

    if found_classes:
        print(f"Found {len(found_classes)} matching classes:\n")
        for class_name, file_name in sorted(found_classes.items()):
            print(f"  {class_name:40s} in {file_name}")
    else:
        print(f"No classes found matching pattern: {class_pattern}")

    return found_classes


def show_class_members(sdk_path: Path, class_name: str, keyword: str = None):
    """Show all members of a specific class, optionally filtered by keyword"""
    print(f"\n{'='*80}")
    print(f"Members of class: {class_name}")
    if keyword:
        print(f"Filtering by keyword: {keyword}")
    print(f"{'='*80}\n")

    for sdk_file in sdk_path.rglob("*.hpp"):
        try:
            with open(sdk_file, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()

            # Find the class definition
            class_pattern = rf'class\s+\w*\s*{re.escape(class_name)}\s*(?::\s*public\s+\w+\s*)?\{{'
            class_match = re.search(class_pattern, content)

            if not class_match:
                continue

            print(f"Found in: {sdk_file.name}\n")

            # Extract class body
            class_start = class_match.end()
            brace_count = 1
            class_end = class_start

            for i, char in enumerate(content[class_start:], class_start):
                if char == '{':
                    brace_count += 1
                elif char == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        class_end = i
                        break

            class_body = content[class_start:class_end]

            # Extract all members with offsets
            member_pattern = r'^\s*(.+?)\s+(\w+)\s*(?:\[.*?\])?\s*;\s*//\s*0x([0-9A-Fa-f]+)'

            members = []
            for line in class_body.split('\n'):
                match = re.match(member_pattern, line)
                if match:
                    member_type = match.group(1).strip()
                    member_name = match.group(2).strip()
                    offset = match.group(3)

                    # Filter by keyword if provided
                    if keyword and keyword.lower() not in member_name.lower():
                        continue

                    members.append((member_name, member_type, offset, line.strip()))

            if members:
                print(f"Found {len(members)} members:\n")
                for name, mtype, offset, full_line in members:
                    print(f"0x{offset:>4s}  {name:30s}  {mtype}")
            else:
                if keyword:
                    print(f"No members found matching keyword: {keyword}")
                else:
                    print("No members found")

            return True

        except Exception as e:
            pass

    print(f"Class not found: {class_name}")
    return False


def find_base_addresses(parent_path: Path):
    """Search for GWorld and GName in dump files"""
    print(f"\n{'='*80}")
    print(f"Searching for Base Addresses (GWorld, GName)")
    print(f"{'='*80}\n")

    dump_files = list(parent_path.rglob("*.txt"))

    if not dump_files:
        print("No .txt dump files found in parent directory")
        return

    print(f"Searching in {len(dump_files)} text files...\n")

    found_gworld = False
    found_gname = False

    for dump_file in dump_files:
        try:
            with open(dump_file, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()

            # Search for GWorld
            if not found_gworld:
                patterns = [
                    r'GWorld[^\n]*?(?:0x|:)\s*([0-9A-Fa-f]+)',
                    r'UWorld.*?(?:0x|:)\s*([0-9A-Fa-f]+)',
                ]
                for pattern in patterns:
                    match = re.search(pattern, content, re.IGNORECASE)
                    if match:
                        print(f"✓ GWorld = 0x{match.group(1)}")
                        print(f"  Found in: {dump_file.name}")
                        print(f"  Context: {content[max(0, match.start()-50):match.end()+50]}")
                        print()
                        found_gworld = True
                        break

            # Search for GName
            if not found_gname:
                patterns = [
                    r'GName[^\n]*?(?:0x|:)\s*([0-9A-Fa-f]+)',
                    r'FNamePool[^\n]*?(?:0x|:)\s*([0-9A-Fa-f]+)',
                ]
                for pattern in patterns:
                    match = re.search(pattern, content, re.IGNORECASE)
                    if match:
                        print(f"✓ GName = 0x{match.group(1)}")
                        print(f"  Found in: {dump_file.name}")
                        print(f"  Context: {content[max(0, match.start()-50):match.end()+50]}")
                        print()
                        found_gname = True
                        break

        except Exception:
            pass

    if not found_gworld:
        print("✗ GWorld not found in dump files")
    if not found_gname:
        print("✗ GName not found in dump files")


def main():
    if len(os.sys.argv) < 2:
        print("Usage: python find_missing_offsets.py <path_to_dumper7_folder>")
        print("\nExample:")
        print("  python find_missing_offsets.py \"C:\\Users\\Admin\\Desktop\\5.5.4-546763+__Squad_v10.2-SquadGame\"")
        os.sys.exit(1)

    root_path = Path(os.sys.argv[1])

    print("="*80)
    print("Enhanced Offset Finder - Recursive Full Scan")
    print("="*80)
    print(f"\nScanning entire directory tree: {root_path}")

    # Find all .hpp files recursively
    hpp_files = list(root_path.rglob("*.hpp"))
    print(f"Found {len(hpp_files)} .hpp files to scan\n")

    if not hpp_files:
        print("ERROR: No .hpp files found. Check the path.")
        os.sys.exit(1)

    sdk_path = root_path  # Use the root as SDK path for recursive search
    parent_path = root_path

    # 1. Find base addresses
    find_base_addresses(parent_path)

    # 2. Search for UWorld and its members
    print("\n" + "="*80)
    print("Searching for UWorld class...")
    print("="*80)
    world_classes = search_class_fuzzy(sdk_path, "World")

    if "UWorld" in world_classes:
        show_class_members(sdk_path, "UWorld", "Game")  # Show members with "Game"
        show_class_members(sdk_path, "UWorld", "Level")  # Show members with "Level"

    # 3. Search for USceneComponent and RelativeLocation
    print("\n" + "="*80)
    print("Searching for USceneComponent::RelativeLocation...")
    print("="*80)
    show_class_members(sdk_path, "USceneComponent", "Location")
    show_class_members(sdk_path, "USceneComponent", "Transform")

    # 4. Search for ASQPlayerState
    print("\n" + "="*80)
    print("Searching for Squad-specific classes...")
    print("="*80)
    sq_classes = search_class_fuzzy(sdk_path, "SQPlayer")

    if "ASQPlayerState" in sq_classes:
        show_class_members(sdk_path, "ASQPlayerState", "Team")

    # 5. Search for ASQSoldier
    soldier_classes = search_class_fuzzy(sdk_path, "SQSoldier")

    if "ASQSoldier" in soldier_classes:
        show_class_members(sdk_path, "ASQSoldier", "Health")

    # 6. Additional searches
    print("\n" + "="*80)
    print("ADDITIONAL HELPFUL SEARCHES")
    print("="*80)

    print("\nSearching for all Squad soldier classes:")
    search_class_fuzzy(sdk_path, "Soldier")

    print("\nSearching for all Squad player state classes:")
    search_class_fuzzy(sdk_path, "PlayerState")


if __name__ == "__main__":
    main()
