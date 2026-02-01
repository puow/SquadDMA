#!/usr/bin/env python3
"""
═══════════════════════════════════════════════════════════════════════════════
                        SQUAD UE5 OFFSET FINDER
                    The Ultimate All-In-One Scanner
═══════════════════════════════════════════════════════════════════════════════

Scans Dumper-7 output to extract ALL offsets needed for SquadDMA UE5.

Usage:
    python squad_offset_finder.py "C:\path\to\dumper7\output"

Output:
    - ue5_offsets.h (C++ header file)
    - ue5_offsets.json (JSON data)
    - Console output with all findings

Requirements:
    - Python 3.6+
    - Dumper-7 output folder containing:
        • GObjects-Dump.txt or GObjects-Dump-WithProperties.txt
        • CppSDK/SDK/*.hpp files
"""

import re
import sys
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict


# ═══════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════

# What we're looking for
OFFSET_TARGETS = {
    # Format: "offset_name": (["ClassName1", "ClassName2"], ["memberName1", "memberName2"])

    # Engine Offsets
    "OwningActorOffset": (["UNetConnection"], ["OwningActor"]),
    "MaxPacketOffset": (["UNetConnection"], ["MaxPacket"]),
    "OwningGameInstance": (["UWorld"], ["OwningGameInstance", "GameInstance"]),
    "PersistentLevel": (["UWorld"], ["PersistentLevel", "Level"]),
    "LocalPlayers": (["UGameInstance"], ["LocalPlayers"]),
    "PlayerController": (["UPlayer", "ULocalPlayer"], ["PlayerController"]),
    "AcknowledgedPawn": (["APlayerController"], ["AcknowledgedPawn"]),
    "CameraManager": (["APlayerController"], ["PlayerCameraManager", "CameraManager"]),
    "PlayerState": (["APawn"], ["PlayerState"]),
    "CameraCachePrivateOffset": (["APlayerCameraManager"], ["CameraCachePrivate", "CameraCache"]),
    "RootComponent": (["AActor"], ["RootComponent"]),
    "RelativeLocation": (["USceneComponent"], ["RelativeLocation", "ComponentLocation"]),

    # Squad-Specific Offsets
    "TeamID": (["ASQPlayerState"], ["TeamID", "TeamId", "Team"]),
    "HealthOffset": (["ASQSoldier", "ASQCharacter"], ["Health", "CurrentHealth", "HP"]),
}


# ═══════════════════════════════════════════════════════════════════════════
# DATA STRUCTURES
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class Offset:
    name: str
    value: int
    hex_value: str
    class_name: str
    member: str
    file: str


@dataclass
class BaseAddress:
    name: str
    value: int
    hex_value: str
    file: str
    line: str


# ═══════════════════════════════════════════════════════════════════════════
# SCANNER
# ═══════════════════════════════════════════════════════════════════════════

class SquadOffsetFinder:
    def __init__(self, root_path: str):
        self.root = Path(root_path)
        self.base_addresses: Dict[str, BaseAddress] = {}
        self.offsets: Dict[str, Offset] = {}
        self.missing: List[str] = []

    def run(self):
        """Execute the full scan"""
        print("\n" + "="*80)
        print("SQUAD UE5 OFFSET FINDER")
        print("="*80 + "\n")

        # Step 1: Find base addresses
        self._scan_base_addresses()

        # Step 2: Find offsets
        self._scan_offsets()

        # Step 3: Generate outputs
        self._generate_outputs()

        # Step 4: Show summary
        self._show_summary()

    def _scan_base_addresses(self):
        """Find GWorld and GName in dump files"""
        print("[1/3] Scanning for Base Addresses (GWorld, GName)...")

        # Find dump files
        dump_files = [
            self.root / "GObjects-Dump.txt",
            self.root / "GObjects-Dump-WithProperties.txt"
        ]

        for dump_file in dump_files:
            if not dump_file.exists():
                continue

            size_mb = dump_file.stat().st_size / (1024*1024)
            print(f"  • Scanning {dump_file.name} ({size_mb:.1f} MB)...")

            try:
                # Read line-by-line for huge files
                with open(dump_file, 'r', encoding='utf-8', errors='ignore') as f:
                    for line_num, line in enumerate(f, 1):
                        # Look for GWorld
                        if 'GWorld' not in self.base_addresses and 'gworld' in line.lower():
                            addr = self._extract_address(line)
                            if addr:
                                self.base_addresses['GWorld'] = BaseAddress(
                                    name='GWorld',
                                    value=addr,
                                    hex_value=f'0x{addr:X}',
                                    file=dump_file.name,
                                    line=line.strip()
                                )
                                print(f"    ✓ Found GWorld = 0x{addr:X} (line {line_num})")

                        # Look for GName
                        if 'GName' not in self.base_addresses:
                            if any(k in line.lower() for k in ['gname', 'fnamepool']):
                                addr = self._extract_address(line)
                                if addr:
                                    self.base_addresses['GName'] = BaseAddress(
                                        name='GName',
                                        value=addr,
                                        hex_value=f'0x{addr:X}',
                                        file=dump_file.name,
                                        line=line.strip()
                                    )
                                    print(f"    ✓ Found GName = 0x{addr:X} (line {line_num})")

                        # Stop if both found
                        if len(self.base_addresses) >= 2:
                            break

            except Exception as e:
                print(f"    Error: {e}")

            if len(self.base_addresses) >= 2:
                break

        print()

    def _extract_address(self, line: str) -> Optional[int]:
        """Extract a valid memory address from a line"""
        # Try to find any hex number
        hex_nums = re.findall(r'[0-9A-Fa-f]{7,16}', line)
        for hex_num in hex_nums:
            try:
                addr = int(hex_num, 16)
                # Validate range
                if 0x100000 < addr < 0xFFFFFFFFFFFF:
                    return addr
            except:
                pass
        return None

    def _scan_offsets(self):
        """Find all structure offsets"""
        print("[2/3] Scanning for Structure Offsets...")

        # Find all .hpp files
        hpp_files = list(self.root.rglob('*.hpp'))
        print(f"  • Found {len(hpp_files)} .hpp files to scan\n")

        total = len(OFFSET_TARGETS)
        for i, (name, (classes, members)) in enumerate(OFFSET_TARGETS.items(), 1):
            print(f"  [{i:2d}/{total}] {name:30s} ", end='', flush=True)

            found = False
            for class_name in classes:
                for hpp_file in hpp_files:
                    offset_info = self._find_offset_in_file(hpp_file, class_name, members)
                    if offset_info:
                        self.offsets[name] = offset_info
                        print(f"✓ 0x{offset_info.value:X}")
                        found = True
                        break
                if found:
                    break

            if not found:
                print("✗ NOT FOUND")
                self.missing.append(name)

        print()

    def _find_offset_in_file(self, file_path: Path, class_name: str, member_names: List[str]) -> Optional[Offset]:
        """Find an offset in a specific file"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()

            # Find class definition
            class_pattern = rf'class\s+{re.escape(class_name)}\s*(?::\s*public\s+\w+)?\s*\{{'
            match = re.search(class_pattern, content)
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

            # Search for members
            for member_name in member_names:
                pattern = rf'^\s*(.+?)\s+{re.escape(member_name)}\s*.*?;\s*//\s*0x([0-9A-Fa-f]+)'

                for line in class_body.split('\n'):
                    m = re.match(pattern, line, re.IGNORECASE)
                    if m:
                        try:
                            offset = int(m.group(2), 16)
                            return Offset(
                                name=class_name,
                                value=offset,
                                hex_value=f'0x{offset:X}',
                                class_name=class_name,
                                member=member_name,
                                file=str(file_path.relative_to(self.root))
                            )
                        except:
                            pass

        except:
            pass

        return None

    def _generate_outputs(self):
        """Generate output files"""
        print("[3/3] Generating Output Files...")

        # C++ Header
        output_h = self.root / "ue5_offsets.h"
        with open(output_h, 'w') as f:
            f.write("// Auto-generated UE5 Offsets for SquadDMA\n")
            f.write("// Generated by Squad Offset Finder\n\n")
            f.write("#pragma once\n")
            f.write("#include <cstdint>\n\n")

            f.write("// Base Addresses\n")
            for name, info in self.base_addresses.items():
                f.write(f"constexpr uint64_t {name} = {info.hex_value};\n")

            f.write("\n// Structure Offsets\n")
            for name, info in sorted(self.offsets.items(), key=lambda x: x[1].value):
                f.write(f"constexpr uint64_t {name} = {info.hex_value};  // {info.class_name}::{info.member}\n")

        print(f"  ✓ Generated: ue5_offsets.h")

        # JSON
        output_json = self.root / "ue5_offsets.json"
        data = {
            'base_addresses': {k: asdict(v) for k, v in self.base_addresses.items()},
            'offsets': {k: asdict(v) for k, v in self.offsets.items()},
            'missing': self.missing
        }

        with open(output_json, 'w') as f:
            json.dump(data, f, indent=2)

        print(f"  ✓ Generated: ue5_offsets.json\n")

    def _show_summary(self):
        """Show final summary"""
        print("="*80)
        print("RESULTS")
        print("="*80 + "\n")

        print("Base Addresses:")
        for name in ['GWorld', 'GName']:
            if name in self.base_addresses:
                info = self.base_addresses[name]
                print(f"  ✓ {name:10s} = {info.hex_value}")
            else:
                print(f"  ✗ {name:10s} = NOT FOUND")

        print(f"\nOffsets: {len(self.offsets)}/{len(OFFSET_TARGETS)} found")

        if self.missing:
            print(f"\nMissing ({len(self.missing)}):")
            for name in self.missing:
                print(f"  ✗ {name}")

        print("\n" + "="*80)

        if len(self.base_addresses) == 2 and not self.missing:
            print("✓ SUCCESS! All offsets found!")
        elif self.missing:
            print(f"⚠ Partial success - {len(self.missing)} offsets missing")
        else:
            print("⚠ Base addresses not found")

        print("="*80 + "\n")


# ═══════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════

def main():
    if len(sys.argv) < 2:
        print("\nUsage: python squad_offset_finder.py <dumper7_folder>")
        print("\nExample:")
        print('  python squad_offset_finder.py "C:\\Users\\Admin\\Desktop\\5.5.4-546763+__Squad_v10.2-SquadGame"')
        print()
        sys.exit(1)

    finder = SquadOffsetFinder(sys.argv[1])
    finder.run()


if __name__ == "__main__":
    main()
