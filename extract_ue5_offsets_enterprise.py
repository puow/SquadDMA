#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                   ENTERPRISE UE5 OFFSET EXTRACTION SUITE                     ║
║                        SquadDMA - Dumper-7 Analyzer                          ║
║                                                                              ║
║  Professional-grade offset extraction with comprehensive scanning,          ║
║  intelligent pattern matching, and detailed reporting.                      ║
╚══════════════════════════════════════════════════════════════════════════════╝

Author: Claude Code Assistant
Version: 2.0 Enterprise Edition
License: Educational/Research Use

Features:
  • Recursive deep scan of all directories and file types
  • Multi-format parsing (HPP, H, TXT, dump files)
  • Intelligent fuzzy matching for class/member names
  • Pattern recognition for base addresses
  • Comprehensive validation and verification
  • Multiple export formats (JSON, C++, TXT)
  • Detailed progress reporting and statistics
  • Error recovery and logging
"""

import os
import re
import sys
import json
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Set
from dataclasses import dataclass, asdict
from collections import defaultdict
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed


# ═══════════════════════════════════════════════════════════════════════════
# ANSI COLOR CODES
# ═══════════════════════════════════════════════════════════════════════════

class Color:
    """ANSI color codes for beautiful terminal output"""
    # Basic colors
    BLACK = '\033[30m'
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'

    # Styles
    BOLD = '\033[1m'
    DIM = '\033[2m'
    ITALIC = '\033[3m'
    UNDERLINE = '\033[4m'
    BLINK = '\033[5m'
    REVERSE = '\033[7m'

    # Background colors
    BG_BLACK = '\033[40m'
    BG_RED = '\033[41m'
    BG_GREEN = '\033[42m'
    BG_YELLOW = '\033[43m'
    BG_BLUE = '\033[44m'
    BG_MAGENTA = '\033[45m'
    BG_CYAN = '\033[46m'
    BG_WHITE = '\033[47m'

    # Reset
    END = '\033[0m'

    # Presets
    SUCCESS = GREEN + BOLD
    ERROR = RED + BOLD
    WARNING = YELLOW + BOLD
    INFO = CYAN + BOLD
    HIGHLIGHT = MAGENTA + BOLD
    HEADER = BLUE + BOLD + UNDERLINE


# ═══════════════════════════════════════════════════════════════════════════
# DATA STRUCTURES
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class OffsetInfo:
    """Detailed information about a found offset"""
    name: str
    offset: int
    hex_offset: str
    class_name: str
    member_name: str
    member_type: str
    file_path: str
    file_name: str
    line_content: str
    line_number: int
    confidence: float  # 0.0 to 1.0
    description: str
    category: str  # 'engine', 'game', 'squad'

    def to_dict(self):
        return asdict(self)


@dataclass
class BaseAddressInfo:
    """Information about a base address"""
    name: str
    address: int
    hex_address: str
    file_path: str
    file_name: str
    context: str
    pattern_used: str
    confidence: float


@dataclass
class ScanStatistics:
    """Statistics about the scanning process"""
    total_files: int = 0
    files_scanned: int = 0
    hpp_files: int = 0
    txt_files: int = 0
    other_files: int = 0
    total_size_mb: float = 0.0
    scan_time_seconds: float = 0.0
    offsets_found: int = 0
    offsets_missing: int = 0
    base_addresses_found: int = 0
    classes_discovered: int = 0



# ═══════════════════════════════════════════════════════════════════════════
# ENTERPRISE OFFSET SCANNER
# ═══════════════════════════════════════════════════════════════════════════

class EnterpriseOffsetScanner:
    """
    Enterprise-grade offset scanner with comprehensive analysis capabilities.
    """

    def __init__(self, root_path: str, verbose: bool = True):
        self.root_path = Path(root_path)
        self.verbose = verbose
        self.stats = ScanStatistics()
        self.start_time = time.time()

        # Results storage
        self.found_offsets: Dict[str, OffsetInfo] = {}
        self.missing_offsets: Dict[str, dict] = {}
        self.base_addresses: Dict[str, BaseAddressInfo] = {}
        self.discovered_classes: Dict[str, List[str]] = {}  # class_name -> [file_paths]
        self.all_files: List[Path] = []

        # Thread safety
        self.lock = threading.Lock()

        # Offset definitions with multiple search strategies
        self.offset_targets = {
            # Engine Core
            "OwningActorOffset": {
                "class_names": ["UNetConnection"],
                "member_names": ["OwningActor", "Owner"],
                "description": "UNetConnection::OwningActor",
                "category": "engine",
                "type": "pointer"
            },
            "MaxPacketOffset": {
                "class_names": ["UNetConnection"],
                "member_names": ["MaxPacket", "MaxPacketSize"],
                "description": "UNetConnection::MaxPacket",
                "category": "engine",
                "type": "int32"
            },
            "OwningGameInstance": {
                "class_names": ["UWorld", "World"],
                "member_names": ["OwningGameInstance", "GameInstance", "GameInstancePtr"],
                "description": "UWorld::OwningGameInstance",
                "category": "engine",
                "type": "pointer"
            },
            "PersistentLevel": {
                "class_names": ["UWorld", "World"],
                "member_names": ["PersistentLevel", "Level"],
                "description": "UWorld::PersistentLevel",
                "category": "engine",
                "type": "pointer"
            },
            "LocalPlayers": {
                "class_names": ["UGameInstance", "GameInstance"],
                "member_names": ["LocalPlayers", "LocalPlayerArray"],
                "description": "UGameInstance::LocalPlayers",
                "category": "engine",
                "type": "array"
            },
            "PlayerController": {
                "class_names": ["UPlayer", "ULocalPlayer"],
                "member_names": ["PlayerController"],
                "description": "UPlayer::PlayerController",
                "category": "engine",
                "type": "pointer"
            },
            "AcknowledgedPawn": {
                "class_names": ["APlayerController"],
                "member_names": ["AcknowledgedPawn", "Pawn"],
                "description": "APlayerController::AcknowledgedPawn",
                "category": "engine",
                "type": "pointer"
            },
            "CameraManager": {
                "class_names": ["APlayerController"],
                "member_names": ["PlayerCameraManager", "CameraManager"],
                "description": "APlayerController::PlayerCameraManager",
                "category": "engine",
                "type": "pointer"
            },
            "PlayerState": {
                "class_names": ["APawn"],
                "member_names": ["PlayerState"],
                "description": "APawn::PlayerState",
                "category": "engine",
                "type": "pointer"
            },
            "CameraCachePrivateOffset": {
                "class_names": ["APlayerCameraManager"],
                "member_names": ["CameraCachePrivate", "CameraCache"],
                "description": "APlayerCameraManager::CameraCachePrivate",
                "category": "engine",
                "type": "struct"
            },
            "RootComponent": {
                "class_names": ["AActor"],
                "member_names": ["RootComponent"],
                "description": "AActor::RootComponent",
                "category": "engine",
                "type": "pointer"
            },
            "RelativeLocation": {
                "class_names": ["USceneComponent", "SceneComponent"],
                "member_names": ["RelativeLocation", "Location", "ComponentLocation"],
                "description": "USceneComponent::RelativeLocation",
                "category": "engine",
                "type": "vector"
            },

            # Squad-Specific
            "TeamID": {
                "class_names": ["ASQPlayerState", "SQPlayerState", "SquadPlayerState"],
                "member_names": ["TeamID", "TeamId", "Team", "TeamNumber"],
                "description": "ASQPlayerState::TeamID",
                "category": "squad",
                "type": "int32"
            },
            "HealthOffset": {
                "class_names": ["ASQSoldier", "SQSoldier", "SquadSoldier", "ASQCharacter"],
                "member_names": ["Health", "CurrentHealth", "HP"],
                "description": "ASQSoldier::Health",
                "category": "squad",
                "type": "float"
            },

            # Additional useful offsets
            "EntityID": {
                "class_names": ["AActor"],
                "member_names": ["InternalIndex", "NetIndex", "ActorID", "EntityID"],
                "description": "AActor::InternalIndex or ID field",
                "category": "engine",
                "type": "int32"
            },
        }

        # Base address patterns
        self.base_address_patterns = {
            "GWorld": [
                r'GWorld[^\n]*?(?:0x|:|\s)([0-9A-Fa-f]{6,16})',
                r'UWorld[^\n]*?(?:Address|Addr|Offset)[^\n]*?(?:0x|:)([0-9A-Fa-f]{6,16})',
                r'World\s*=\s*(?:0x)?([0-9A-Fa-f]{6,16})',
            ],
            "GName": [
                r'GName[^\n]*?(?:0x|:|\s)([0-9A-Fa-f]{6,16})',
                r'FNamePool[^\n]*?(?:0x|:|\s)([0-9A-Fa-f]{6,16})',
                r'NamePool[^\n]*?(?:Address|Addr|Offset)[^\n]*?(?:0x|:)([0-9A-Fa-f]{6,16})',
            ],
        }

    def print_header(self):
        """Print beautiful header"""
        print(f"\n{Color.CYAN}{'═'*80}{Color.END}")
        print(f"{Color.BOLD}{Color.CYAN}╔{'═'*78}╗{Color.END}")
        print(f"{Color.BOLD}{Color.CYAN}║{' '*20}ENTERPRISE UE5 OFFSET SCANNER{' '*28}║{Color.END}")
        print(f"{Color.BOLD}{Color.CYAN}║{' '*25}SquadDMA Edition{' '*35}║{Color.END}")
        print(f"{Color.BOLD}{Color.CYAN}╚{'═'*78}╝{Color.END}")
        print(f"{Color.CYAN}{'═'*80}{Color.END}\n")

    def log(self, message: str, level: str = "INFO"):
        """Thread-safe logging"""
        if not self.verbose and level == "DEBUG":
            return

        colors = {
            "INFO": Color.INFO,
            "SUCCESS": Color.SUCCESS,
            "WARNING": Color.WARNING,
            "ERROR": Color.ERROR,
            "DEBUG": Color.DIM,
        }

        color = colors.get(level, Color.WHITE)
        timestamp = time.strftime("%H:%M:%S")

        with self.lock:
            print(f"{Color.DIM}[{timestamp}]{Color.END} {color}[{level}]{Color.END} {message}")

    def discover_files(self):
        """Phase 1: Discover all files in the directory tree"""
        self.log("Phase 1: Discovering files...", "INFO")

        file_types = defaultdict(int)
        total_size = 0

        for file_path in self.root_path.rglob("*"):
            if file_path.is_file():
                self.all_files.append(file_path)
                ext = file_path.suffix.lower()
                file_types[ext] += 1

                try:
                    total_size += file_path.stat().st_size
                except:
                    pass

        self.stats.total_files = len(self.all_files)
        self.stats.total_size_mb = total_size / (1024 * 1024)

        # Count by type
        self.stats.hpp_files = file_types['.hpp'] + file_types['.h']
        self.stats.txt_files = file_types['.txt']
        self.stats.other_files = self.stats.total_files - self.stats.hpp_files - self.stats.txt_files

        print(f"\n{Color.SUCCESS}✓ File Discovery Complete{Color.END}")
        print(f"  {Color.CYAN}Total Files:{Color.END} {self.stats.total_files:,}")
        print(f"  {Color.CYAN}Header Files (.hpp/.h):{Color.END} {self.stats.hpp_files:,}")
        print(f"  {Color.CYAN}Text/Dump Files (.txt):{Color.END} {self.stats.txt_files:,}")
        print(f"  {Color.CYAN}Other Files:{Color.END} {self.stats.other_files:,}")
        print(f"  {Color.CYAN}Total Size:{Color.END} {self.stats.total_size_mb:.2f} MB")

        # Show directory structure
        print(f"\n{Color.CYAN}Directory Structure:{Color.END}")
        unique_dirs = sorted(set(f.parent.relative_to(self.root_path) for f in self.all_files))
        for i, dir_path in enumerate(unique_dirs[:10], 1):
            print(f"  {i}. {dir_path}")
        if len(unique_dirs) > 10:
            print(f"  ... and {len(unique_dirs) - 10} more directories")

    def scan_for_base_addresses(self):
        """Phase 2: Scan for GWorld and GName base addresses"""
        self.log("Phase 2: Scanning for base addresses (GWorld, GName)...", "INFO")

        txt_files = [f for f in self.all_files if f.suffix.lower() == '.txt']

        print(f"  Scanning {len(txt_files)} text files...")

        found_count = 0

        for txt_file in txt_files:
            try:
                with open(txt_file, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()

                # Search for each base address
                for base_name, patterns in self.base_address_patterns.items():
                    if base_name in self.base_addresses:
                        continue  # Already found

                    for pattern in patterns:
                        matches = list(re.finditer(pattern, content, re.IGNORECASE | re.MULTILINE))

                        for match in matches:
                            try:
                                address_hex = match.group(1)
                                address = int(address_hex, 16)

                                # Validate address (reasonable range)
                                if 0x1000000 < address < 0xFFFFFFFFFFFF:
                                    # Get context
                                    context_start = max(0, match.start() - 100)
                                    context_end = min(len(content), match.end() + 100)
                                    context = content[context_start:context_end].strip()

                                    confidence = 1.0 if 'GWorld' in context or 'GName' in context else 0.8

                                    self.base_addresses[base_name] = BaseAddressInfo(
                                        name=base_name,
                                        address=address,
                                        hex_address=f"0x{address:X}",
                                        file_path=str(txt_file),
                                        file_name=txt_file.name,
                                        context=context[:200],
                                        pattern_used=pattern,
                                        confidence=confidence
                                    )

                                    found_count += 1
                                    self.log(f"Found {base_name} = 0x{address:X} in {txt_file.name}", "SUCCESS")
                                    break
                            except (ValueError, IndexError):
                                continue

                        if base_name in self.base_addresses:
                            break

            except Exception as e:
                self.log(f"Error reading {txt_file.name}: {e}", "WARNING")

        self.stats.base_addresses_found = len(self.base_addresses)

        print(f"\n{Color.SUCCESS}✓ Base Address Scan Complete{Color.END}")
        print(f"  Found: {found_count}/2 base addresses")

        for name, info in self.base_addresses.items():
            print(f"  {Color.GREEN}✓{Color.END} {name}: {info.hex_address} (confidence: {info.confidence*100:.0f}%)")

        for name in ["GWorld", "GName"]:
            if name not in self.base_addresses:
                print(f"  {Color.RED}✗{Color.END} {name}: Not found")

    def extract_class_members(self, file_path: Path, class_name: str) -> List[Tuple[str, str, int, str, int]]:
        """
        Extract all members from a class with detailed information.
        Returns: List of (member_name, member_type, offset, full_line, line_number)
        """
        members = []

        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
                content = ''.join(lines)

            # Find the class definition with multiple patterns
            class_patterns = [
                rf'class\s+{re.escape(class_name)}\s*(?::\s*public\s+\w+\s*)?\{{',
                rf'struct\s+{re.escape(class_name)}\s*(?::\s*public\s+\w+\s*)?\{{',
            ]

            class_match = None
            for pattern in class_patterns:
                class_match = re.search(pattern, content)
                if class_match:
                    break

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

            # Count line numbers
            lines_before_class = content[:class_start].count('\n')

            # Extract members with multiple patterns
            member_patterns = [
                # Standard member with offset comment
                r'^\s*(.+?)\s+(\w+)\s*(?:\[.*?\])?\s*;\s*//\s*0x([0-9A-Fa-f]+)',
                # Member with bit field
                r'^\s*(.+?)\s+(\w+)\s*:\s*\d+\s*;\s*//\s*0x([0-9A-Fa-f]+)',
            ]

            for line_num, line in enumerate(class_body.split('\n'), lines_before_class + 1):
                for pattern in member_patterns:
                    match = re.match(pattern, line)
                    if match:
                        try:
                            member_type = match.group(1).strip()
                            member_name = match.group(2).strip()
                            offset_hex = match.group(3)
                            offset = int(offset_hex, 16)
                            members.append((member_name, member_type, offset, line.strip(), line_num))
                        except (ValueError, IndexError):
                            pass
                        break

        except Exception as e:
            pass

        return members

    def find_offset_multistrategy(self, target_name: str, target_info: dict) -> Optional[OffsetInfo]:
        """
        Find an offset using multiple strategies and class/member name variations.
        """
        class_names = target_info["class_names"]
        member_names = target_info["member_names"]

        best_match = None
        best_confidence = 0.0

        # Try all combinations of class and member names
        for class_name in class_names:
            # Find files that might contain this class
            candidate_files = [
                f for f in self.all_files
                if f.suffix.lower() in ['.hpp', '.h'] and
                ('_classes' in f.name.lower() or 'engine' in f.name.lower() or 'squad' in f.name.lower())
            ]

            for file_path in candidate_files:
                members = self.extract_class_members(file_path, class_name)

                for mem_name, mem_type, offset, full_line, line_num in members:
                    # Check if member name matches any of the target names
                    for target_member in member_names:
                        confidence = 0.0

                        # Exact match
                        if mem_name == target_member:
                            confidence = 1.0
                        # Case-insensitive match
                        elif mem_name.lower() == target_member.lower():
                            confidence = 0.95
                        # Contains match
                        elif target_member.lower() in mem_name.lower() or mem_name.lower() in target_member.lower():
                            confidence = 0.7

                        if confidence > best_confidence:
                            best_confidence = confidence
                            best_match = OffsetInfo(
                                name=target_name,
                                offset=offset,
                                hex_offset=f"0x{offset:X}",
                                class_name=class_name,
                                member_name=mem_name,
                                member_type=mem_type,
                                file_path=str(file_path),
                                file_name=file_path.name,
                                line_content=full_line,
                                line_number=line_num,
                                confidence=confidence,
                                description=target_info["description"],
                                category=target_info["category"]
                            )

        return best_match

    def scan_for_offsets(self):
        """Phase 3: Scan for all target offsets"""
        self.log("Phase 3: Scanning for structure offsets...", "INFO")

        total_targets = len(self.offset_targets)

        print(f"  Searching for {total_targets} target offsets...")
        print()

        for i, (target_name, target_info) in enumerate(self.offset_targets.items(), 1):
            progress = f"[{i}/{total_targets}]"
            print(f"  {Color.CYAN}{progress:8s}{Color.END} {target_name:30s} ", end='', flush=True)

            result = self.find_offset_multistrategy(target_name, target_info)

            if result and result.confidence >= 0.7:
                self.found_offsets[target_name] = result
                confidence_str = f"({result.confidence*100:.0f}%)"
                print(f"{Color.GREEN}✓ 0x{result.offset:X:>6s}{Color.END} {Color.DIM}{confidence_str}{Color.END}")
            else:
                self.missing_offsets[target_name] = target_info
                print(f"{Color.RED}✗ NOT FOUND{Color.END}")

        self.stats.offsets_found = len(self.found_offsets)
        self.stats.offsets_missing = len(self.missing_offsets)

        print(f"\n{Color.SUCCESS}✓ Offset Scan Complete{Color.END}")
        print(f"  Found: {self.stats.offsets_found}/{total_targets}")
        print(f"  Missing: {self.stats.offsets_missing}/{total_targets}")

    def discover_additional_classes(self):
        """Phase 4: Discover additional Squad-specific classes"""
        self.log("Phase 4: Discovering Squad-specific classes...", "INFO")

        hpp_files = [f for f in self.all_files if f.suffix.lower() in ['.hpp', '.h']]

        squad_patterns = [
            r'class\s+(ASQ\w+)\s*(?::\s*public\s+\w+\s*)?\{',
            r'class\s+(USQ\w+)\s*(?::\s*public\s+\w+\s*)?\{',
            r'class\s+(FSQ\w+)\s*(?::\s*public\s+\w+\s*)?\{',
            r'class\s+(Squad\w+)\s*(?::\s*public\s+\w+\s*)?\{',
        ]

        found_classes = set()

        for file_path in hpp_files:
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()

                for pattern in squad_patterns:
                    matches = re.finditer(pattern, content)
                    for match in matches:
                        class_name = match.group(1)
                        found_classes.add(class_name)

                        if class_name not in self.discovered_classes:
                            self.discovered_classes[class_name] = []
                        self.discovered_classes[class_name].append(str(file_path))

            except Exception:
                pass

        self.stats.classes_discovered = len(found_classes)

        print(f"\n{Color.SUCCESS}✓ Class Discovery Complete{Color.END}")
        print(f"  Found {len(found_classes)} Squad-specific classes")

        # Show interesting classes
        interesting = [c for c in found_classes if any(x in c for x in ['Soldier', 'Player', 'Vehicle', 'Weapon', 'Deploy'])]
        if interesting:
            print(f"\n{Color.CYAN}  Interesting Classes:{Color.END}")
            for cls in sorted(interesting)[:15]:
                print(f"    • {cls}")
            if len(interesting) > 15:
                print(f"    ... and {len(interesting) - 15} more")

    def generate_reports(self):
        """Phase 5: Generate detailed reports"""
        self.log("Phase 5: Generating reports...", "INFO")

        self.stats.scan_time_seconds = time.time() - self.start_time

        # Console report
        self.print_detailed_results()

        # Text file report
        self.save_text_report()

        # JSON report
        self.save_json_report()

        # C++ header file
        self.generate_cpp_header()

    def print_detailed_results(self):
        """Print beautiful detailed results to console"""
        print(f"\n{Color.BOLD}{Color.CYAN}{'═'*80}{Color.END}")
        print(f"{Color.BOLD}{Color.CYAN}SCAN RESULTS{Color.END}")
        print(f"{Color.BOLD}{Color.CYAN}{'═'*80}{Color.END}\n")

        # Statistics
        print(f"{Color.HEADER}STATISTICS{Color.END}")
        print(f"  Files Scanned:        {self.stats.total_files:,}")
        print(f"  Total Size:           {self.stats.total_size_mb:.2f} MB")
        print(f"  Scan Time:            {self.stats.scan_time_seconds:.2f} seconds")
        print(f"  Offsets Found:        {Color.GREEN}{self.stats.offsets_found}{Color.END}/{len(self.offset_targets)}")
        print(f"  Base Addresses:       {Color.GREEN}{self.stats.base_addresses_found}{Color.END}/2")
        print(f"  Classes Discovered:   {self.stats.classes_discovered}")

        # Base Addresses
        print(f"\n{Color.HEADER}BASE ADDRESSES{Color.END}")
        for name in ["GWorld", "GName"]:
            if name in self.base_addresses:
                info = self.base_addresses[name]
                print(f"  {Color.GREEN}✓{Color.END} {name:20s} = {info.hex_address:16s} (confidence: {info.confidence*100:.0f}%)")
                print(f"    {Color.DIM}Found in: {info.file_name}{Color.END}")
            else:
                print(f"  {Color.RED}✗{Color.END} {name:20s} = NOT FOUND")

        # Found Offsets
        if self.found_offsets:
            print(f"\n{Color.HEADER}FOUND OFFSETS ({len(self.found_offsets)}){Color.END}\n")

            # Group by category
            by_category = defaultdict(list)
            for name, info in self.found_offsets.items():
                by_category[info.category].append((name, info))

            for category in ['engine', 'squad', 'game']:
                if category in by_category:
                    print(f"  {Color.CYAN}[{category.upper()}]{Color.END}")
                    for name, info in sorted(by_category[category], key=lambda x: x[1].offset):
                        confidence_color = Color.GREEN if info.confidence >= 0.9 else Color.YELLOW
                        print(f"    {confidence_color}✓{Color.END} {name:30s} = {info.hex_offset:10s} ({info.class_name}::{info.member_name})")
                        print(f"      {Color.DIM}File: {info.file_name}  Line: {info.line_number}  Confidence: {info.confidence*100:.0f}%{Color.END}")
                    print()

        # Missing Offsets
        if self.missing_offsets:
            print(f"\n{Color.HEADER}MISSING OFFSETS ({len(self.missing_offsets)}){Color.END}\n")
            for name, info in sorted(self.missing_offsets.items()):
                print(f"  {Color.RED}✗{Color.END} {name:30s} ({info['description']})")
                print(f"    {Color.DIM}Searched for: {', '.join(info['class_names'])}::{', '.join(info['member_names'])}{Color.END}")

        # Code Generation
        print(f"\n{Color.HEADER}CODE GENERATION{Color.END}\n")
        print(f"  Generated files:")
        print(f"    • ue5_offsets_report.txt   (Detailed text report)")
        print(f"    • ue5_offsets_data.json    (JSON data export)")
        print(f"    • ue5_offsets_code.h       (C++ header file)")

    def save_text_report(self):
        """Save detailed text report"""
        output_path = self.root_path / "ue5_offsets_report.txt"

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("="*80 + "\n")
            f.write("ENTERPRISE UE5 OFFSET SCANNER - DETAILED REPORT\n")
            f.write("="*80 + "\n\n")

            f.write("STATISTICS\n")
            f.write("-"*80 + "\n")
            f.write(f"Scan Date:            {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Root Path:            {self.root_path}\n")
            f.write(f"Files Scanned:        {self.stats.total_files:,}\n")
            f.write(f"Total Size:           {self.stats.total_size_mb:.2f} MB\n")
            f.write(f"Scan Time:            {self.stats.scan_time_seconds:.2f} seconds\n")
            f.write(f"Offsets Found:        {self.stats.offsets_found}/{len(self.offset_targets)}\n")
            f.write(f"Base Addresses:       {self.stats.base_addresses_found}/2\n")
            f.write(f"Classes Discovered:   {self.stats.classes_discovered}\n\n")

            f.write("BASE ADDRESSES\n")
            f.write("-"*80 + "\n")
            for name, info in self.base_addresses.items():
                f.write(f"\n{name}:\n")
                f.write(f"  Address:     {info.hex_address}\n")
                f.write(f"  File:        {info.file_name}\n")
                f.write(f"  Confidence:  {info.confidence*100:.0f}%\n")
                f.write(f"  Pattern:     {info.pattern_used}\n")
                f.write(f"  Context:     {info.context[:100]}...\n")

            f.write("\n\nFOUND OFFSETS\n")
            f.write("-"*80 + "\n")
            for name, info in sorted(self.found_offsets.items(), key=lambda x: x[1].offset):
                f.write(f"\n{name}:\n")
                f.write(f"  Offset:      {info.hex_offset}\n")
                f.write(f"  Class:       {info.class_name}\n")
                f.write(f"  Member:      {info.member_name}\n")
                f.write(f"  Type:        {info.member_type}\n")
                f.write(f"  File:        {info.file_name}\n")
                f.write(f"  Line:        {info.line_number}\n")
                f.write(f"  Confidence:  {info.confidence*100:.0f}%\n")
                f.write(f"  Code:        {info.line_content}\n")

            if self.missing_offsets:
                f.write("\n\nMISSING OFFSETS\n")
                f.write("-"*80 + "\n")
                for name, info in sorted(self.missing_offsets.items()):
                    f.write(f"\n{name}:\n")
                    f.write(f"  Description: {info['description']}\n")
                    f.write(f"  Classes:     {', '.join(info['class_names'])}\n")
                    f.write(f"  Members:     {', '.join(info['member_names'])}\n")

            if self.discovered_classes:
                f.write("\n\nDISCOVERED SQUAD CLASSES\n")
                f.write("-"*80 + "\n")
                for cls_name in sorted(self.discovered_classes.keys()):
                    f.write(f"  {cls_name}\n")

        self.log(f"Saved text report: {output_path}", "SUCCESS")

    def save_json_report(self):
        """Save JSON data export"""
        output_path = self.root_path / "ue5_offsets_data.json"

        data = {
            "metadata": {
                "scan_date": time.strftime('%Y-%m-%d %H:%M:%S'),
                "root_path": str(self.root_path),
                "scanner_version": "2.0 Enterprise",
            },
            "statistics": asdict(self.stats),
            "base_addresses": {
                name: asdict(info) for name, info in self.base_addresses.items()
            },
            "found_offsets": {
                name: info.to_dict() for name, info in self.found_offsets.items()
            },
            "missing_offsets": self.missing_offsets,
            "discovered_classes": {
                name: files for name, files in list(self.discovered_classes.items())[:100]
            }
        }

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)

        self.log(f"Saved JSON report: {output_path}", "SUCCESS")

    def generate_cpp_header(self):
        """Generate C++ header file with all offsets"""
        output_path = self.root_path / "ue5_offsets_code.h"

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("// Auto-generated by Enterprise UE5 Offset Scanner\n")
            f.write(f"// Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("// SquadDMA - UE5 Offsets\n\n")
            f.write("#pragma once\n")
            f.write("#include <cstdint>\n\n")

            f.write("namespace UE5Offsets {\n\n")

            # Base addresses
            f.write("    // Base Addresses\n")
            for name, info in self.base_addresses.items():
                f.write(f"    constexpr uint64_t {name} = {info.hex_address};  // Found in {info.file_name}\n")
            f.write("\n")

            # Engine offsets
            f.write("    // Engine Structure Offsets\n")
            for name, info in sorted(self.found_offsets.items(), key=lambda x: x[1].offset):
                if info.category == 'engine':
                    f.write(f"    constexpr uint64_t {name} = {info.hex_offset};  // {info.class_name}::{info.member_name}\n")
            f.write("\n")

            # Squad offsets
            f.write("    // Squad-Specific Offsets\n")
            for name, info in sorted(self.found_offsets.items(), key=lambda x: x[1].offset):
                if info.category == 'squad':
                    offset_type = "uint32_t" if "ID" in name else "uint64_t"
                    f.write(f"    constexpr {offset_type} {name} = {info.hex_offset};  // {info.class_name}::{info.member_name}\n")

            f.write("\n}\n")

        self.log(f"Saved C++ header: {output_path}", "SUCCESS")

    def run(self):
        """Execute full scan pipeline"""
        self.print_header()

        try:
            self.discover_files()
            self.scan_for_base_addresses()
            self.scan_for_offsets()
            self.discover_additional_classes()
            self.generate_reports()

            print(f"\n{Color.SUCCESS}{'═'*80}{Color.END}")
            print(f"{Color.SUCCESS}✓ SCAN COMPLETE{Color.END}")
            print(f"{Color.SUCCESS}{'═'*80}{Color.END}\n")

            if self.stats.offsets_found == len(self.offset_targets) and self.stats.base_addresses_found == 2:
                print(f"{Color.GREEN}{Color.BOLD}🎉 SUCCESS! All offsets and base addresses found!{Color.END}\n")
            else:
                missing = len(self.offset_targets) - self.stats.offsets_found + (2 - self.stats.base_addresses_found)
                print(f"{Color.YELLOW}⚠ Scan complete with {missing} items missing. Review the report for details.{Color.END}\n")

        except KeyboardInterrupt:
            print(f"\n\n{Color.WARNING}Scan interrupted by user.{Color.END}")
            sys.exit(1)
        except Exception as e:
            print(f"\n\n{Color.ERROR}Fatal error: {e}{Color.END}")
            import traceback
            traceback.print_exc()
            sys.exit(1)


# ═══════════════════════════════════════════════════════════════════════════
# MAIN ENTRY POINT
# ═══════════════════════════════════════════════════════════════════════════

def main():
    if len(sys.argv) < 2:
        print(f"{Color.YELLOW}Usage: python {sys.argv[0]} <path_to_dumper7_folder>{Color.END}\n")
        print(f"Example:")
        print(f"  python {sys.argv[0]} \"C:\\Users\\Admin\\Desktop\\5.5.4-546763+__Squad_v10.2-SquadGame\"")
        print(f"  python {sys.argv[0]} \"/path/to/dumper7/output\"\n")
        print(f"The scanner will recursively scan all subdirectories and files.")
        sys.exit(1)

    root_path = sys.argv[1]

    scanner = EnterpriseOffsetScanner(root_path, verbose=True)
    scanner.run()


if __name__ == "__main__":
    main()
