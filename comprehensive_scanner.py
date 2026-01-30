#!/usr/bin/env python3
"""
COMPREHENSIVE UE5 OFFSET SCANNER - Scans EVERYTHING
Shows exactly what files are being scanned in each directory
"""

import os
import re
import sys
import json
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict


class Color:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    CYAN = '\033[96m'
    BOLD = '\033[1m'
    END = '\033[0m'


@dataclass
class FoundOffset:
    name: str
    offset: int
    hex_offset: str
    class_name: str
    member_name: str
    file: str


@dataclass
class BaseAddr:
    name: str
    address: int
    hex_address: str
    file: str
    line: str


class ComprehensiveScanner:
    def __init__(self, root: str):
        self.root = Path(root)
        self.base_addresses = {}
        self.offsets = {}
        self.missing = []

        # All directories we MUST scan
        self.required_dirs = ['Dumpspace', 'IDAMappings', 'Mappings', 'CppSDK']

        # Targets
        self.targets = {
            "OwningActorOffset": (["UNetConnection"], ["OwningActor"]),
            "MaxPacketOffset": (["UNetConnection"], ["MaxPacket"]),
            "OwningGameInstance": (["UWorld"], ["OwningGameInstance", "GameInstance"]),
            "PersistentLevel": (["UWorld"], ["PersistentLevel", "Level"]),
            "LocalPlayers": (["UGameInstance"], ["LocalPlayers"]),
            "PlayerController": (["UPlayer", "ULocalPlayer"], ["PlayerController"]),
            "AcknowledgedPawn": (["APlayerController"], ["AcknowledgedPawn"]),
            "CameraManager": (["APlayerController"], ["PlayerCameraManager", "CameraManager"]),
            "PlayerState": (["APawn"], ["PlayerState"]),
            "CameraCachePrivateOffset": (["APlayerCameraManager"], ["CameraCachePrivate"]),
            "RootComponent": (["AActor"], ["RootComponent"]),
            "RelativeLocation": (["USceneComponent"], ["RelativeLocation", "ComponentLocation"]),
            "TeamID": (["ASQPlayerState"], ["TeamID", "TeamId", "Team"]),
            "HealthOffset": (["ASQSoldier", "ASQCharacter"], ["Health", "CurrentHealth"]),
        }

    def print_header(self):
        print(f"\n{Color.BOLD}{'='*80}{Color.END}")
        print(f"{Color.BOLD}COMPREHENSIVE SCANNER - Scans EVERYTHING{Color.END}")
        print(f"{Color.BOLD}{'='*80}{Color.END}\n")

    def show_directory_structure(self):
        """Show EVERY file in EVERY directory"""
        print(f"{Color.CYAN}[1/4] Scanning Directory Structure...{Color.END}\n")

        # Check required directories exist
        print(f"Required directories:")
        for dir_name in self.required_dirs:
            dir_path = self.root / dir_name
            if dir_path.exists():
                file_count = len(list(dir_path.rglob('*')))
                print(f"  {Color.GREEN}✓{Color.END} {dir_name:20s} ({file_count} files)")
            else:
                print(f"  {Color.RED}✗{Color.END} {dir_name:20s} NOT FOUND")

        print()

        # Show ALL files in root
        print(f"Root directory files:")
        for item in sorted(self.root.iterdir()):
            if item.is_file():
                size_mb = item.stat().st_size / (1024*1024)
                print(f"  • {item.name:45s} {size_mb:>8.2f} MB")

        print()

    def scan_base_addresses_aggressive(self):
        """Ultra-aggressive base address scanning"""
        print(f"{Color.CYAN}[2/4] Scanning for Base Addresses (GWorld, GName)...{Color.END}\n")

        # Find the two big dump files
        dump_files = [
            self.root / "GObjects-Dump.txt",
            self.root / "GObjects-Dump-WithProperties.txt"
        ]

        for dump_file in dump_files:
            if not dump_file.exists():
                print(f"{Color.YELLOW}⚠ {dump_file.name} not found{Color.END}")
                continue

            size_mb = dump_file.stat().st_size / (1024*1024)
            print(f"\n{Color.BOLD}Scanning: {dump_file.name} ({size_mb:.2f} MB){Color.END}")

            try:
                # Read file line by line to handle huge files
                with open(dump_file, 'r', encoding='utf-8', errors='ignore') as f:
                    line_count = 0
                    found_in_this_file = []

                    # Show first 20 lines to understand format
                    print(f"{Color.DIM}First 20 lines to understand format:{Color.END}")
                    f.seek(0)
                    for i in range(20):
                        line = f.readline()
                        if not line:
                            break
                        print(f"{Color.DIM}  {i+1:3d}: {line.rstrip()[:100]}{Color.END}")

                    # Now scan for addresses
                    f.seek(0)
                    for line_num, line in enumerate(f, 1):
                        line_count = line_num

                        # ULTRA AGGRESSIVE: Any line with these keywords
                        if 'GWorld' not in self.base_addresses:
                            if 'GWorld' in line or 'gworld' in line.lower():
                                # Try to extract ANY hex number from this line
                                hex_nums = re.findall(r'[0-9A-Fa-f]{7,16}', line)
                                for hex_num in hex_nums:
                                    try:
                                        addr = int(hex_num, 16)
                                        if 0x100000 < addr < 0xFFFFFFFFFFFF:
                                            self.base_addresses['GWorld'] = BaseAddr(
                                                name='GWorld',
                                                address=addr,
                                                hex_address=f'0x{addr:X}',
                                                file=dump_file.name,
                                                line=line.strip()
                                            )
                                            found_in_this_file.append(f"GWorld = 0x{addr:X} (line {line_num})")
                                            print(f"{Color.GREEN}✓ Found GWorld = 0x{addr:X} at line {line_num}{Color.END}")
                                            print(f"  {Color.DIM}Line: {line.strip()[:80]}{Color.END}")
                                            break
                                    except:
                                        pass

                        if 'GName' not in self.base_addresses:
                            if any(k in line.lower() for k in ['gname', 'fnamepool', 'namepool']):
                                hex_nums = re.findall(r'[0-9A-Fa-f]{7,16}', line)
                                for hex_num in hex_nums:
                                    try:
                                        addr = int(hex_num, 16)
                                        if 0x100000 < addr < 0xFFFFFFFFFFFF:
                                            self.base_addresses['GName'] = BaseAddr(
                                                name='GName',
                                                address=addr,
                                                hex_address=f'0x{addr:X}',
                                                file=dump_file.name,
                                                line=line.strip()
                                            )
                                            found_in_this_file.append(f"GName = 0x{addr:X} (line {line_num})")
                                            print(f"{Color.GREEN}✓ Found GName = 0x{addr:X} at line {line_num}{Color.END}")
                                            print(f"  {Color.DIM}Line: {line.strip()[:80]}{Color.END}")
                                            break
                                    except:
                                        pass

                        # Stop if we found both
                        if len(self.base_addresses) >= 2:
                            break

                        # Progress indicator every 100k lines
                        if line_num % 100000 == 0:
                            print(f"  {Color.DIM}Scanned {line_num:,} lines...{Color.END}", end='\r')

                    print(f"\n  {Color.CYAN}Scanned {line_count:,} total lines{Color.END}")
                    if found_in_this_file:
                        print(f"  {Color.GREEN}Found in this file:{Color.END}")
                        for item in found_in_this_file:
                            print(f"    • {item}")

            except Exception as e:
                print(f"  {Color.RED}Error: {e}{Color.END}")

        print(f"\n{Color.BOLD}Base Address Results:{Color.END}")
        for name in ['GWorld', 'GName']:
            if name in self.base_addresses:
                info = self.base_addresses[name]
                print(f"  {Color.GREEN}✓{Color.END} {name:10s} = {info.hex_address:16s} in {info.file}")
            else:
                print(f"  {Color.RED}✗{Color.END} {name:10s} = NOT FOUND")
        print()

    def scan_offsets_all_dirs(self):
        """Scan for offsets in ALL required directories"""
        print(f"{Color.CYAN}[3/4] Scanning for Offsets in All Directories...{Color.END}\n")

        # Collect ALL .hpp files from ALL directories
        all_hpp_files = []

        print(f"Collecting .hpp files from:")
        for dir_name in self.required_dirs:
            dir_path = self.root / dir_name
            if dir_path.exists():
                hpp_files = list(dir_path.rglob('*.hpp'))
                all_hpp_files.extend(hpp_files)
                print(f"  • {dir_name:20s} {len(hpp_files):>6,} .hpp files")

        print(f"\n{Color.BOLD}Total .hpp files to scan: {len(all_hpp_files):,}{Color.END}\n")

        # Scan for each target
        total = len(self.targets)
        for i, (name, (classes, members)) in enumerate(self.targets.items(), 1):
            print(f"  [{i:2d}/{total}] {name:30s} ", end='', flush=True)

            found = False
            for class_name in classes:
                for hpp_file in all_hpp_files:
                    result = self._extract_offset(hpp_file, class_name, members)
                    if result:
                        self.offsets[name] = result
                        print(f"{Color.GREEN}✓ 0x{result.offset:X}{Color.END} ({hpp_file.parent.name}/{hpp_file.name})")
                        found = True
                        break
                if found:
                    break

            if not found:
                print(f"{Color.RED}✗ NOT FOUND{Color.END}")
                self.missing.append(name)

        print()

    def _extract_offset(self, file_path: Path, class_name: str, member_names: List[str]) -> Optional[FoundOffset]:
        """Extract offset from a class"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()

            # Find class
            class_pat = rf'class\s+{re.escape(class_name)}\s*(?::\s*public\s+\w+)?\s*\{{'
            match = re.search(class_pat, content)
            if not match:
                return None

            # Extract class body
            start = match.end()
            brace_count = 1
            end = start
            for i, char in enumerate(content[start:], start):
                if char == '{':
                    brace_count += 1
                elif char == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        end = i
                        break

            class_body = content[start:end]

            # Find members
            for member_name in member_names:
                pattern = rf'^\s*(.+?)\s+{re.escape(member_name)}\s*.*?;\s*//\s*0x([0-9A-Fa-f]+)'
                for line in class_body.split('\n'):
                    m = re.match(pattern, line, re.IGNORECASE)
                    if m:
                        try:
                            offset = int(m.group(2), 16)
                            return FoundOffset(
                                name=class_name,
                                offset=offset,
                                hex_offset=f'0x{offset:X}',
                                class_name=class_name,
                                member_name=member_name,
                                file=str(file_path.relative_to(self.root))
                            )
                        except:
                            pass
        except:
            pass
        return None

    def generate_outputs(self):
        """Generate output files"""
        print(f"{Color.CYAN}[4/4] Generating Output Files...{Color.END}\n")

        # Summary
        print(f"{Color.BOLD}FINAL RESULTS:{Color.END}")
        print(f"  Base Addresses: {len(self.base_addresses)}/2")
        print(f"  Offsets Found:  {len(self.offsets)}/{len(self.targets)}")
        print(f"  Missing:        {len(self.missing)}")
        print()

        # Generate C++ header
        output_h = self.root / "ue5_offsets.h"
        with open(output_h, 'w') as f:
            f.write("// Auto-generated UE5 Offsets\n\n")
            f.write("#pragma once\n")
            f.write("#include <cstdint>\n\n")

            f.write("// Base Addresses\n")
            for name, info in self.base_addresses.items():
                f.write(f"constexpr uint64_t {name} = {info.hex_address};\n")

            f.write("\n// Offsets\n")
            for name, info in sorted(self.offsets.items(), key=lambda x: x[1].offset):
                f.write(f"constexpr uint64_t {name} = {info.hex_offset};  // {info.class_name}::{info.member_name}\n")

        print(f"{Color.GREEN}✓ Generated: ue5_offsets.h{Color.END}")

        # Generate JSON
        output_json = self.root / "ue5_offsets.json"
        data = {
            'base_addresses': {k: asdict(v) for k, v in self.base_addresses.items()},
            'offsets': {k: asdict(v) for k, v in self.offsets.items()},
            'missing': self.missing
        }
        with open(output_json, 'w') as f:
            json.dump(data, f, indent=2)

        print(f"{Color.GREEN}✓ Generated: ue5_offsets.json{Color.END}\n")

    def run(self):
        """Execute full scan"""
        self.print_header()
        self.show_directory_structure()
        self.scan_base_addresses_aggressive()
        self.scan_offsets_all_dirs()
        self.generate_outputs()

        if len(self.base_addresses) == 2 and len(self.missing) == 0:
            print(f"{Color.GREEN}{Color.BOLD}🎉 SUCCESS! All offsets found!{Color.END}\n")
        else:
            print(f"{Color.YELLOW}⚠ Complete - Review results above{Color.END}\n")


def main():
    if len(sys.argv) < 2:
        print("Usage: python comprehensive_scanner.py <dumper7_folder>")
        print("\nExample:")
        print('  python comprehensive_scanner.py "C:\\Users\\Admin\\Desktop\\5.5.4-546763+__Squad_v10.2-SquadGame"')
        sys.exit(1)

    scanner = ComprehensiveScanner(sys.argv[1])
    scanner.run()


if __name__ == "__main__":
    main()
