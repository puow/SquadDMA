#!/usr/bin/env python3
"""
UE5 Offset Extractor for SquadDMA
Scans Dumper-7 SDK output and extracts all required offsets for UE5 compatibility.

Usage:
    python3 extract_ue5_offsets.py <path_to_dumper7_sdk_folder>

Example:
    python3 extract_ue5_offsets.py "./Dumper7_Output/SDK"
"""

import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple


class Color:
    """ANSI color codes for terminal output"""
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    BOLD = '\033[1m'
    END = '\033[0m'


class OffsetExtractor:
    def __init__(self, sdk_path: str):
        self.sdk_path = Path(sdk_path)
        self.found_offsets = {}
        self.missing_offsets = {}
        self.sdk_files = []

        # Define all offsets we need to find
        self.offset_definitions = {
            # Format: "display_name": (class_name, member_name, description)

            # UNetConnection offsets
            "OwningActorOffset": ("UNetConnection", "OwningActor", "UNetConnection::OwningActor"),
            "MaxPacketOffset": ("UNetConnection", "MaxPacket", "UNetConnection::MaxPacket"),

            # UWorld offsets
            "OwningGameInstance": ("UWorld", "OwningGameInstance", "UWorld::OwningGameInstance"),
            "PersistentLevel": ("UWorld", "PersistentLevel", "UWorld::PersistentLevel"),

            # UGameInstance offsets
            "LocalPlayers": ("UGameInstance", "LocalPlayers", "UGameInstance::LocalPlayers"),

            # UPlayer offsets
            "PlayerController": ("UPlayer", "PlayerController", "UPlayer::PlayerController"),

            # APlayerController offsets
            "AcknowledgedPawn": ("APlayerController", "AcknowledgedPawn", "APlayerController::AcknowledgedPawn"),
            "CameraManager": ("APlayerController", "PlayerCameraManager", "APlayerController::PlayerCameraManager"),

            # APawn offsets
            "PlayerState": ("APawn", "PlayerState", "APawn::PlayerState"),

            # APlayerCameraManager offsets
            "CameraCachePrivateOffset": ("APlayerCameraManager", "CameraCachePrivate", "APlayerCameraManager::CameraCachePrivate"),

            # AActor offsets
            "RootComponent": ("AActor", "RootComponent", "AActor::RootComponent"),

            # USceneComponent offsets
            "RelativeLocation": ("USceneComponent", "RelativeLocation", "USceneComponent::RelativeLocation"),

            # Squad-specific: ASQPlayerState offsets
            "TeamID": ("ASQPlayerState", "TeamID", "ASQPlayerState::TeamID"),

            # Squad-specific: ASQSoldier offsets
            "HealthOffset": ("ASQSoldier", "Health", "ASQSoldier::Health (game-specific!)"),
        }

        # Base addresses (these are usually in a separate file or need pattern scanning)
        self.base_addresses = {
            "GWorld": None,
            "GName": None,
        }

    def find_sdk_files(self):
        """Find all relevant SDK header files recursively"""
        print(f"\n{Color.CYAN}Scanning directory recursively: {self.sdk_path}{Color.END}")

        if not self.sdk_path.exists():
            print(f"{Color.RED}ERROR: Path does not exist: {self.sdk_path}{Color.END}")
            return False

        # Look for C++ header files recursively throughout entire directory tree
        patterns = ['*.hpp', '*.h']
        for pattern in patterns:
            self.sdk_files.extend(self.sdk_path.rglob(pattern))

        print(f"{Color.GREEN}Found {len(self.sdk_files)} header files{Color.END}")

        # Show directory structure
        unique_dirs = set(f.parent for f in self.sdk_files)
        print(f"{Color.CYAN}Scanning {len(unique_dirs)} subdirectories{Color.END}")

        return len(self.sdk_files) > 0

    def extract_class_members(self, file_path: Path, class_name: str) -> List[Tuple[str, str, int, str]]:
        """
        Extract all members from a class definition.
        Returns: List of (member_name, member_type, offset, full_line)
        """
        members = []

        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()

            # Find the class definition
            # Pattern: class CLASS_NAME : public ParentClass {
            class_pattern = rf'class\s+\w*\s*{re.escape(class_name)}\s*(?::\s*public\s+\w+\s*)?\{{'
            class_match = re.search(class_pattern, content)

            if not class_match:
                return members

            # Find the closing brace for this class
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

            # Extract members with offsets
            # Pattern: type MemberName; // 0xABCD(0xSIZE) or similar
            # Also handle: static void* MemberName(FMemory...); // 0xABCD
            member_patterns = [
                # Standard member: type Name; // 0xOffset
                r'^\s*(?:static\s+)?(\w+[\w\s\*&<>:,]*?)\s+(\w+)\s*(?:\[[\w\s]*\])?\s*;\s*//\s*0x([0-9A-Fa-f]+)',
                # Member with bit field: type Name : bits; // 0xOffset
                r'^\s*(\w+[\w\s\*&<>:,]*?)\s+(\w+)\s*:\s*\d+\s*;\s*//\s*0x([0-9A-Fa-f]+)',
                # Array member: type Name[size]; // 0xOffset
                r'^\s*(\w+[\w\s\*&<>:,]*?)\s+(\w+)\s*\[[\w\s]*\]\s*;\s*//\s*0x([0-9A-Fa-f]+)',
            ]

            for line_num, line in enumerate(class_body.split('\n'), 1):
                for pattern in member_patterns:
                    match = re.match(pattern, line)
                    if match:
                        member_type = match.group(1).strip()
                        member_name = match.group(2).strip()
                        offset_hex = match.group(3)
                        offset = int(offset_hex, 16)
                        members.append((member_name, member_type, offset, line.strip()))

        except Exception as e:
            print(f"{Color.YELLOW}Warning: Error reading {file_path}: {e}{Color.END}")

        return members

    def find_offset(self, class_name: str, member_name: str) -> Optional[Tuple[int, str, str]]:
        """
        Find a specific member offset in a class.
        Returns: (offset, file_path, full_line) or None
        """
        for sdk_file in self.sdk_files:
            # Skip if filename doesn't look relevant
            if '_structs.hpp' in str(sdk_file) or '_params.hpp' in str(sdk_file):
                continue

            members = self.extract_class_members(sdk_file, class_name)

            for mem_name, mem_type, offset, full_line in members:
                if mem_name == member_name:
                    return (offset, str(sdk_file), full_line)

        return None

    def find_base_addresses(self):
        """
        Try to find GWorld and GName base addresses.
        These are usually in GObjects-Dump.txt or similar files.
        """
        print(f"\n{Color.CYAN}Searching for base addresses (recursively in all .txt files)...{Color.END}")

        # Search for all .txt files recursively
        all_txt_files = list(self.sdk_path.rglob('*.txt'))

        if not all_txt_files:
            print(f"{Color.YELLOW}No .txt dump files found{Color.END}")
            return

        print(f"{Color.CYAN}Found {len(all_txt_files)} text files to search{Color.END}")

        for dump_path in all_txt_files:
            if dump_path.exists():
                try:
                    with open(dump_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()

                    # Look for GWorld address
                    gworld_pattern = r'GWorld[^\n]*?(?:0x|:)\s*([0-9A-Fa-f]+)'
                    match = re.search(gworld_pattern, content, re.IGNORECASE)
                    if match and not self.base_addresses["GWorld"]:
                        self.base_addresses["GWorld"] = int(match.group(1), 16)
                        print(f"{Color.GREEN}✓ Found GWorld: 0x{match.group(1)}{Color.END} in {dump_file}")

                    # Look for GName/FNamePool address
                    gname_pattern = r'(?:GName|FNamePool)[^\n]*?(?:0x|:)\s*([0-9A-Fa-f]+)'
                    match = re.search(gname_pattern, content, re.IGNORECASE)
                    if match and not self.base_addresses["GName"]:
                        self.base_addresses["GName"] = int(match.group(1), 16)
                        print(f"{Color.GREEN}✓ Found GName: 0x{match.group(1)}{Color.END} in {dump_file}")

                except Exception as e:
                    print(f"{Color.YELLOW}Warning: Error reading {dump_file}: {e}{Color.END}")

        if not self.base_addresses["GWorld"]:
            print(f"{Color.YELLOW}⚠ GWorld address not found in dump files{Color.END}")
        if not self.base_addresses["GName"]:
            print(f"{Color.YELLOW}⚠ GName address not found in dump files{Color.END}")

    def extract_all_offsets(self):
        """Extract all defined offsets"""
        print(f"\n{Color.CYAN}Extracting offsets...{Color.END}\n")

        for offset_name, (class_name, member_name, description) in self.offset_definitions.items():
            print(f"Searching for {Color.BOLD}{offset_name}{Color.END} ({description})...", end=' ')

            result = self.find_offset(class_name, member_name)

            if result:
                offset, file_path, full_line = result
                self.found_offsets[offset_name] = {
                    'offset': offset,
                    'file': file_path,
                    'line': full_line,
                    'class': class_name,
                    'member': member_name,
                    'description': description,
                }
                print(f"{Color.GREEN}✓ Found: 0x{offset:X}{Color.END}")
            else:
                self.missing_offsets[offset_name] = {
                    'class': class_name,
                    'member': member_name,
                    'description': description,
                }
                print(f"{Color.RED}✗ NOT FOUND{Color.END}")

    def print_results(self):
        """Print detailed results"""
        print(f"\n{Color.BOLD}{'='*80}{Color.END}")
        print(f"{Color.BOLD}EXTRACTION RESULTS{Color.END}")
        print(f"{Color.BOLD}{'='*80}{Color.END}\n")

        # Print found offsets
        if self.found_offsets:
            print(f"{Color.GREEN}{Color.BOLD}✓ FOUND OFFSETS ({len(self.found_offsets)}):{Color.END}\n")

            for name, data in sorted(self.found_offsets.items()):
                print(f"{Color.CYAN}{name:30s}{Color.END} = 0x{data['offset']:X}")
                print(f"  Class:  {data['class']}")
                print(f"  Member: {data['member']}")
                print(f"  File:   {Path(data['file']).name}")
                print(f"  Line:   {data['line'][:100]}")
                print()

        # Print base addresses
        print(f"{Color.GREEN}{Color.BOLD}BASE ADDRESSES:{Color.END}\n")
        for name, addr in self.base_addresses.items():
            if addr:
                print(f"{Color.CYAN}{name:30s}{Color.END} = 0x{addr:X}")
            else:
                print(f"{Color.CYAN}{name:30s}{Color.END} = {Color.RED}NOT FOUND{Color.END}")
        print()

        # Print missing offsets
        if self.missing_offsets:
            print(f"{Color.RED}{Color.BOLD}✗ MISSING OFFSETS ({len(self.missing_offsets)}):{Color.END}\n")

            for name, data in sorted(self.missing_offsets.items()):
                print(f"{Color.RED}{name:30s}{Color.END}")
                print(f"  Looking for: {data['class']}::{data['member']}")
                print(f"  Description: {data['description']}")
                print()

            print(f"{Color.YELLOW}DEBUGGING TIPS:{Color.END}")
            print("1. Check if the class name is correct (might be prefixed with 'U', 'A', 'F', etc.)")
            print("2. Search manually in the SDK files for similar class names")
            print("3. The member might have been renamed in UE5")
            print("4. Some Squad-specific classes might have changed")
            print()

    def generate_code_updates(self):
        """Generate code snippets for updating Engine.h and ActorEntity.h"""
        print(f"\n{Color.BOLD}{'='*80}{Color.END}")
        print(f"{Color.BOLD}CODE UPDATES{Color.END}")
        print(f"{Color.BOLD}{'='*80}{Color.END}\n")

        if not self.found_offsets and not any(self.base_addresses.values()):
            print(f"{Color.RED}No offsets found to generate code updates.{Color.END}")
            return

        print(f"{Color.CYAN}Copy these values into your code:{Color.END}\n")

        # Engine.h updates
        print(f"{Color.BOLD}=== Engine.h Base Addresses ==={Color.END}\n")
        if self.base_addresses["GWorld"]:
            print(f"uint64_t GWorld = 0x{self.base_addresses['GWorld']:X};  // [UE5] Updated")
        if self.base_addresses["GName"]:
            print(f"uint64_t GName = 0x{self.base_addresses['GName']:X};   // [UE5] Updated")
        print()

        print(f"{Color.BOLD}=== Engine.h Structure Offsets ==={Color.END}\n")
        engine_h_offsets = [
            "OwningActorOffset", "MaxPacketOffset", "OwningGameInstance", "PersistentLevel",
            "LocalPlayers", "PlayerController", "AcknowledgedPawn", "CameraManager",
            "PlayerState", "CameraCachePrivateOffset", "TeamID"
        ]
        for name in engine_h_offsets:
            if name in self.found_offsets:
                data = self.found_offsets[name]
                print(f"uint64_t {name} = 0x{data['offset']:X};  // {data['class']}::{data['member']}")
        print()

        print(f"{Color.BOLD}=== ActorEntity.h Structure Offsets ==={Color.END}\n")
        actor_h_offsets = [
            "PlayerState", "AcknowledgedPawn", "RootComponent", "RelativeLocation",
            "TeamID", "HealthOffset"
        ]
        for name in actor_h_offsets:
            if name in self.found_offsets:
                data = self.found_offsets[name]
                offset_type = "uint32_t" if "ID" in name or name == "HealthOffset" else "uint64_t"
                print(f"{offset_type} {name} = 0x{data['offset']:X};  // {data['class']}::{data['member']}")
        print()

    def save_to_file(self, output_file: str = "ue5_offsets_extracted.txt"):
        """Save results to a text file"""
        output_path = Path(output_file)

        with open(output_path, 'w') as f:
            f.write("UE5 Offset Extraction Results\n")
            f.write("="*80 + "\n\n")

            f.write("BASE ADDRESSES:\n")
            f.write("-"*80 + "\n")
            for name, addr in self.base_addresses.items():
                if addr:
                    f.write(f"{name:30s} = 0x{addr:X}\n")
                else:
                    f.write(f"{name:30s} = NOT FOUND\n")
            f.write("\n")

            f.write("FOUND OFFSETS:\n")
            f.write("-"*80 + "\n")
            for name, data in sorted(self.found_offsets.items()):
                f.write(f"\n{name}:\n")
                f.write(f"  Offset:      0x{data['offset']:X}\n")
                f.write(f"  Class:       {data['class']}\n")
                f.write(f"  Member:      {data['member']}\n")
                f.write(f"  Description: {data['description']}\n")
                f.write(f"  File:        {data['file']}\n")
                f.write(f"  Line:        {data['line']}\n")

            if self.missing_offsets:
                f.write("\n\nMISSING OFFSETS:\n")
                f.write("-"*80 + "\n")
                for name, data in sorted(self.missing_offsets.items()):
                    f.write(f"\n{name}:\n")
                    f.write(f"  Class:       {data['class']}\n")
                    f.write(f"  Member:      {data['member']}\n")
                    f.write(f"  Description: {data['description']}\n")

        print(f"\n{Color.GREEN}Results saved to: {output_path.absolute()}{Color.END}")


def main():
    print(f"{Color.BOLD}{Color.CYAN}")
    print("="*80)
    print("UE5 Offset Extractor for SquadDMA")
    print("="*80)
    print(f"{Color.END}")

    if len(sys.argv) < 2:
        print(f"{Color.YELLOW}Usage: python3 {sys.argv[0]} <path_to_dumper7_folder>{Color.END}")
        print(f"\nExample:")
        print(f"  python3 {sys.argv[0]} './5.5.4-546763+__Squad_v10.2-SquadGame'")
        print(f"  python3 {sys.argv[0]} 'C:\\Users\\Admin\\Desktop\\5.5.4-546763+__Squad_v10.2-SquadGame'")
        print(f"\nNote: The script will recursively scan all subdirectories for .hpp and .txt files")
        sys.exit(1)

    sdk_path = sys.argv[1]

    # Create extractor
    extractor = OffsetExtractor(sdk_path)

    # Find SDK files
    if not extractor.find_sdk_files():
        print(f"{Color.RED}No SDK files found. Please check the path.{Color.END}")
        sys.exit(1)

    # Extract base addresses
    extractor.find_base_addresses()

    # Extract all offsets
    extractor.extract_all_offsets()

    # Print results
    extractor.print_results()

    # Generate code updates
    extractor.generate_code_updates()

    # Save to file
    extractor.save_to_file()

    # Summary
    total = len(extractor.offset_definitions)
    found = len(extractor.found_offsets)
    missing = len(extractor.missing_offsets)

    print(f"\n{Color.BOLD}SUMMARY:{Color.END}")
    print(f"  Total offsets:   {total}")
    print(f"  Found:           {Color.GREEN}{found}{Color.END}")
    print(f"  Missing:         {Color.RED}{missing}{Color.END}")
    print(f"  Base addresses:  {sum(1 for v in extractor.base_addresses.values() if v)}/2")

    if missing == 0 and all(extractor.base_addresses.values()):
        print(f"\n{Color.GREEN}{Color.BOLD}✓ SUCCESS! All offsets found!{Color.END}")
        print(f"\nNext steps:")
        print(f"1. Review the extracted offsets above")
        print(f"2. Update SquadDMA/SDK/Engine.h with the new values")
        print(f"3. Update SquadDMA/SDK/ActorEntity.h with the new values")
        print(f"4. Compile and test the project")
    else:
        print(f"\n{Color.YELLOW}⚠ Some offsets are missing. Review the missing offsets above.{Color.END}")
        print(f"\nYou may need to:")
        print(f"1. Manually search the SDK files for similar class/member names")
        print(f"2. Check if Squad changed their class structure in UE5")
        print(f"3. Use pattern scanning for base addresses if not in dump files")


if __name__ == "__main__":
    main()
