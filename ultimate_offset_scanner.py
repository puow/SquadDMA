#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    ULTIMATE UE5 OFFSET SCANNER v3.0                          ║
║                    Handles Huge Files (36MB+) Efficiently                    ║
╚══════════════════════════════════════════════════════════════════════════════╝

Built specifically for large Dumper-7 outputs with better memory management.
"""

import os
import re
import sys
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
import time


class Color:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    BOLD = '\033[1m'
    DIM = '\033[2m'
    END = '\033[0m'


@dataclass
class OffsetResult:
    name: str
    offset: int
    hex_offset: str
    class_name: str
    member_name: str
    file_name: str
    line_content: str
    confidence: float = 1.0


@dataclass
class BaseAddress:
    name: str
    address: int
    hex_address: str
    file_name: str
    line_content: str
    confidence: float = 1.0


class UltimateOffsetScanner:
    """Handles massive dump files efficiently"""

    def __init__(self, root_path: str):
        self.root_path = Path(root_path)
        self.found_offsets: Dict[str, OffsetResult] = {}
        self.base_addresses: Dict[str, BaseAddress] = {}
        self.missing = []

        # Offset targets with multiple search strategies
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
            "CameraCachePrivateOffset": (["APlayerCameraManager"], ["CameraCachePrivate", "CameraCache"]),
            "RootComponent": (["AActor"], ["RootComponent"]),
            "RelativeLocation": (["USceneComponent"], ["RelativeLocation", "ComponentLocation"]),
            "TeamID": (["ASQPlayerState"], ["TeamID", "TeamId", "Team"]),
            "HealthOffset": (["ASQSoldier", "ASQCharacter"], ["Health", "CurrentHealth"]),
        }

    def print_header(self):
        print(f"\n{Color.CYAN}{'═'*80}{Color.END}")
        print(f"{Color.BOLD}  ULTIMATE UE5 OFFSET SCANNER - Large File Handler{Color.END}")
        print(f"{Color.CYAN}{'═'*80}{Color.END}\n")

    def scan_base_addresses_chunked(self):
        """Scan huge dump files in chunks to avoid memory issues"""
        print(f"{Color.CYAN}[1/3] Scanning for Base Addresses (GWorld, GName)...{Color.END}\n")

        # Find dump files
        dump_files = list(self.root_path.glob("*.txt"))
        dump_files.extend(self.root_path.glob("**/*.txt"))

        print(f"Found {len(dump_files)} text files:\n")
        for f in dump_files:
            size_mb = f.stat().st_size / (1024*1024)
            print(f"  • {f.name:45s} {size_mb:>8.2f} MB")

        print()

        for dump_file in dump_files:
            size_mb = dump_file.stat().st_size / (1024*1024)
            print(f"Scanning: {dump_file.name} ({size_mb:.2f} MB)...")

            try:
                # Read in chunks for large files
                chunk_size = 1024 * 1024  # 1MB chunks

                with open(dump_file, 'r', encoding='utf-8', errors='ignore') as f:
                    line_num = 0

                    while True:
                        lines = []
                        # Read chunk of lines
                        for _ in range(10000):  # ~10k lines per chunk
                            line = f.readline()
                            if not line:
                                break
                            lines.append(line)
                            line_num += 1

                        if not lines:
                            break

                        chunk = ''.join(lines)

                        # Search for GWorld
                        if 'GWorld' not in self.base_addresses:
                            patterns = [
                                r'GWorld\s*[=:]\s*(?:0x)?([0-9A-Fa-f]{7,16})',
                                r'(?:^|\s)GWorld.*?(?:0x)([0-9A-Fa-f]{7,16})',
                            ]

                            for pattern in patterns:
                                match = re.search(pattern, chunk, re.IGNORECASE)
                                if match:
                                    try:
                                        addr = int(match.group(1), 16)
                                        if 0x100000 < addr < 0xFFFFFFFFFFFF:
                                            # Find the actual line
                                            for i, line in enumerate(lines):
                                                if match.group(0) in line:
                                                    self.base_addresses["GWorld"] = BaseAddress(
                                                        name="GWorld",
                                                        address=addr,
                                                        hex_address=f"0x{addr:X}",
                                                        file_name=dump_file.name,
                                                        line_content=line.strip()
                                                    )
                                                    print(f"  {Color.GREEN}✓ Found GWorld = 0x{addr:X}{Color.END}")
                                                    break
                                            break
                                    except:
                                        pass

                        # Search for GName
                        if 'GName' not in self.base_addresses:
                            patterns = [
                                r'GName\s*[=:]\s*(?:0x)?([0-9A-Fa-f]{7,16})',
                                r'FNamePool\s*[=:]\s*(?:0x)?([0-9A-Fa-f]{7,16})',
                                r'(?:^|\s)GName.*?(?:0x)([0-9A-Fa-f]{7,16})',
                            ]

                            for pattern in patterns:
                                match = re.search(pattern, chunk, re.IGNORECASE)
                                if match:
                                    try:
                                        addr = int(match.group(1), 16)
                                        if 0x100000 < addr < 0xFFFFFFFFFFFF:
                                            for i, line in enumerate(lines):
                                                if match.group(0) in line:
                                                    self.base_addresses["GName"] = BaseAddress(
                                                        name="GName",
                                                        address=addr,
                                                        hex_address=f"0x{addr:X}",
                                                        file_name=dump_file.name,
                                                        line_content=line.strip()
                                                    )
                                                    print(f"  {Color.GREEN}✓ Found GName = 0x{addr:X}{Color.END}")
                                                    break
                                            break
                                    except:
                                        pass

                        # Stop if we found both
                        if len(self.base_addresses) >= 2:
                            break

            except Exception as e:
                print(f"  {Color.RED}Error reading {dump_file.name}: {e}{Color.END}")

        print()

    def extract_class_offsets(self, class_name: str, member_names: List[str]) -> Optional[OffsetResult]:
        """Extract offset from class definition"""

        # Find SDK files
        sdk_files = list(self.root_path.glob("**/Engine_classes.hpp"))
        sdk_files.extend(self.root_path.glob("**/Squad_classes.hpp"))
        sdk_files.extend(self.root_path.glob("**/*_classes.hpp"))

        for sdk_file in sdk_files:
            try:
                with open(sdk_file, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()

                # Find class definition
                class_pattern = rf'class\s+{re.escape(class_name)}\s*(?::\s*public\s+\w+)?\s*\{{'
                class_match = re.search(class_pattern, content)

                if not class_match:
                    continue

                # Extract class body
                start = class_match.end()
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
                    # Pattern to match member with offset comment
                    pattern = rf'^\s*(.+?)\s+{re.escape(member_name)}\s*.*?;\s*//\s*0x([0-9A-Fa-f]+)'

                    for line in class_body.split('\n'):
                        match = re.match(pattern, line, re.IGNORECASE)
                        if match:
                            try:
                                offset = int(match.group(2), 16)
                                return OffsetResult(
                                    name=class_name,
                                    offset=offset,
                                    hex_offset=f"0x{offset:X}",
                                    class_name=class_name,
                                    member_name=member_name,
                                    file_name=sdk_file.name,
                                    line_content=line.strip()
                                )
                            except:
                                pass

            except Exception as e:
                pass

        return None

    def scan_offsets(self):
        """Scan for all structure offsets"""
        print(f"{Color.CYAN}[2/3] Scanning for Structure Offsets...{Color.END}\n")

        total = len(self.targets)

        for i, (name, (classes, members)) in enumerate(self.targets.items(), 1):
            print(f"  [{i}/{total}] {name:30s} ", end='', flush=True)

            found = False
            for class_name in classes:
                result = self.extract_class_offsets(class_name, members)
                if result:
                    self.found_offsets[name] = result
                    print(f"{Color.GREEN}✓ 0x{result.offset:X}{Color.END}")
                    found = True
                    break

            if not found:
                print(f"{Color.RED}✗ NOT FOUND{Color.END}")
                self.missing.append(name)

        print()

    def generate_reports(self):
        """Generate output files"""
        print(f"{Color.CYAN}[3/3] Generating Reports...{Color.END}\n")

        # Console summary
        print(f"{Color.BOLD}{'='*80}{Color.END}")
        print(f"{Color.BOLD}RESULTS{Color.END}")
        print(f"{Color.BOLD}{'='*80}{Color.END}\n")

        print(f"{Color.CYAN}Base Addresses:{Color.END}")
        for name in ["GWorld", "GName"]:
            if name in self.base_addresses:
                info = self.base_addresses[name]
                print(f"  {Color.GREEN}✓{Color.END} {name:20s} = {info.hex_address}")
                print(f"    {Color.DIM}Found in: {info.file_name}{Color.END}")
            else:
                print(f"  {Color.RED}✗{Color.END} {name:20s} = NOT FOUND")

        print(f"\n{Color.CYAN}Offsets Found: {len(self.found_offsets)}/{len(self.targets)}{Color.END}\n")

        for name, info in sorted(self.found_offsets.items(), key=lambda x: x[1].offset):
            print(f"  {Color.GREEN}✓{Color.END} {name:30s} = {info.hex_offset:10s} ({info.class_name}::{info.member_name})")

        if self.missing:
            print(f"\n{Color.YELLOW}Missing: {len(self.missing)}{Color.END}")
            for name in self.missing:
                print(f"  {Color.RED}✗{Color.END} {name}")

        # Generate C++ header
        output_h = self.root_path / "ue5_offsets.h"
        with open(output_h, 'w') as f:
            f.write("// Auto-generated UE5 Offsets\n")
            f.write("// Generated by Ultimate Offset Scanner\n\n")
            f.write("#pragma once\n")
            f.write("#include <cstdint>\n\n")

            f.write("// Base Addresses\n")
            for name, info in self.base_addresses.items():
                f.write(f"constexpr uint64_t {name} = {info.hex_address};  // {info.file_name}\n")

            f.write("\n// Structure Offsets\n")
            for name, info in sorted(self.found_offsets.items(), key=lambda x: x[1].offset):
                f.write(f"constexpr uint64_t {name} = {info.hex_offset};  // {info.class_name}::{info.member_name}\n")

        print(f"\n{Color.GREEN}✓ Generated: ue5_offsets.h{Color.END}")

        # Generate JSON
        output_json = self.root_path / "ue5_offsets.json"
        data = {
            "base_addresses": {k: asdict(v) for k, v in self.base_addresses.items()},
            "offsets": {k: asdict(v) for k, v in self.found_offsets.items()},
            "missing": self.missing
        }

        with open(output_json, 'w') as f:
            json.dump(data, f, indent=2)

        print(f"{Color.GREEN}✓ Generated: ue5_offsets.json{Color.END}")

        print(f"\n{Color.BOLD}{'='*80}{Color.END}\n")

    def run(self):
        """Execute full scan"""
        self.print_header()

        start_time = time.time()

        self.scan_base_addresses_chunked()
        self.scan_offsets()
        self.generate_reports()

        elapsed = time.time() - start_time
        print(f"Scan completed in {elapsed:.2f} seconds")

        if len(self.base_addresses) == 2 and len(self.missing) == 0:
            print(f"\n{Color.GREEN}{Color.BOLD}🎉 SUCCESS! All offsets found!{Color.END}\n")
        elif len(self.missing) > 0:
            print(f"\n{Color.YELLOW}⚠ Complete with {len(self.missing)} missing offsets{Color.END}\n")


def main():
    if len(sys.argv) < 2:
        print("Usage: python ultimate_offset_scanner.py <dumper7_folder>")
        print("\nExample:")
        print('  python ultimate_offset_scanner.py "C:\\Users\\Admin\\Desktop\\5.5.4-546763+__Squad_v10.2-SquadGame"')
        sys.exit(1)

    scanner = UltimateOffsetScanner(sys.argv[1])
    scanner.run()


if __name__ == "__main__":
    main()
