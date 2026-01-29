# Squad DMA
Player ESP For Squad (UE5 Version)

> **Note**: This project has been upgraded for Unreal Engine 5. See [UE5_OFFSETS_GUIDE.md](./UE5_OFFSETS_GUIDE.md) for detailed update instructions.

## Showcase

<a href="https://youtu.be/tgMuXgZvYRg">
<p align="Left">
  <img src="Images/3.jpg"
    style="width: 100%;" />
</p>
</a>
<p align="Left">
  <img src="Images/1.png"
    style="width: 35%;" />
</p>

## Instructions
* [Installation Guide](./Instructions.md)
* [UE5 Offset Update Guide](./UE5_OFFSETS_GUIDE.md) - **Required for UE5 compatibility**

### Updating Offsets for UE5

Squad has been updated to Unreal Engine 5, which requires updating memory offsets. Follow these steps:

1. **Quick Start**: See [UE5_OFFSETS_GUIDE.md](./UE5_OFFSETS_GUIDE.md) for comprehensive instructions
2. **Use Dumper-7**: Download from [https://github.com/Encryqed/Dumper-7](https://github.com/Encryqed/Dumper-7)
3. **Run on Squad UE5**: Generate the SDK for the UE5 version
4. **Update offsets in**:
   - `SquadDMA/SDK/Engine.h` - Base addresses (GWorld, GName) and engine offsets
   - `SquadDMA/SDK/ActorEntity.h` - Actor and Squad-specific offsets
   - `SquadDMA/SDK/EngineStructs.h` - Verify structure layouts if needed

**Important**: All current offsets are from UE4 and marked with `[UE4]` comments. They MUST be updated for UE5!


## Features
* Player ESP
  * Name
  * Distance
  * Health
  * Font Size
  * Max Distance
* Overlay
  * Custom W2S Resolution
* Config
  * Load
  * Save

## Educational & Security Research Purpose

This project is maintained for **educational and security research purposes**. It serves to:

- **Demonstrate DMA-based memory manipulation techniques** to game developers and anti-cheat teams
- **Document vulnerabilities** in client-side game security for defensive improvements
- **Provide research material** for understanding external memory access patterns
- **Assist anti-cheat development** by showing attack vectors that need mitigation

### For Security Researchers

This codebase demonstrates several important security concepts:

1. **DMA Attack Vectors**: How hardware-based memory access bypasses kernel protection
2. **Memory Structure Exploitation**: How hardcoded offsets enable external manipulation
3. **Engine Structure Analysis**: Understanding Unreal Engine's internal memory layout
4. **Detection Challenges**: Why DMA-based cheats are difficult to detect

### Mitigation Recommendations

For game developers and anti-cheat teams:

- Implement structure layout randomization
- Add integrity checks on critical game data
- Monitor for suspicious memory access patterns
- Consider ASLR for game-specific structures
- Obfuscate or encrypt sensitive player data

See [UE5_OFFSETS_GUIDE.md](./UE5_OFFSETS_GUIDE.md) for detailed security analysis.

## Credits
* [PCILeech](https://github.com/ufrisk/pcileech)
* [MemProcFS](https://github.com/ufrisk/MemProcFS)
* [DMALibrary](https://github.com/Metick/DMALibrary/tree/Master)
* [Dumper-7](https://github.com/Encryqed/Dumper-7)
