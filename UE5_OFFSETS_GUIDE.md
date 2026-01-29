# UE5 Offset Update Guide

This guide provides detailed instructions for updating SquadDMA from UE4 to UE5 offsets.

## Overview

Squad has been updated to Unreal Engine 5, which changes many critical memory offsets. This guide will help you use Dumper-7 to find the new offsets and update the codebase.

## Prerequisites

1. **Dumper-7**: Download from [https://github.com/Encryqed/Dumper-7](https://github.com/Encryqed/Dumper-7)
2. **Squad (UE5 version)**: Ensure you have the latest UE5 version installed
3. **Text editor**: For searching through the generated SDK files

## Step 1: Run Dumper-7

1. Launch Squad (UE5 version)
2. Inject/run Dumper-7 on the Squad process
3. Wait for Dumper-7 to complete the dump
4. Locate the generated SDK folder (usually in the game directory or Dumper-7 output folder)

## Step 2: Find Base Addresses

### GWorld Address

**Location in code**: `SquadDMA/SDK/Engine.h` line 30

**How to find**:
- Look in Dumper-7's main output or log file for "GWorld" or "UWorld"
- Alternatively, use a pattern scanner on Squad.exe
- Common UE5 pattern: Look for global pointers in the `.data` or `.rdata` sections

**Current UE4 value**: `0x72aa2e0`

**Update in**: `Engine.h` line 30

### GName Address

**Location in code**: `SquadDMA/SDK/Engine.h` line 31

**How to find**:
- Look in Dumper-7's output for "GName" or "FNamePool"
- Should be near GWorld in the binary

**Current UE4 value**: `0x7129580`

**Update in**: `Engine.h` line 31

## Step 3: Find Structure Offsets

Open the generated `SDK/Engine_Classes.hpp` file from Dumper-7. Search for the following classes and their member offsets:

### UNetConnection Offsets

**File to update**: `Engine.h` lines 39-40

Search for: `class UNetConnection`

Find these members:
```cpp
class UNetConnection {
    // ...
    class AActor* OwningActor;    // Note the offset - update line 39
    int32 MaxPacket;              // Note the offset - update line 40
    // ...
};
```

**Current UE4 values**:
- `OwningActorOffset = 0x98`
- `MaxPacketOffset = 0xa0`

### UWorld Offsets

**File to update**: `Engine.h` lines 47-48

Search for: `class UWorld`

Find these members:
```cpp
class UWorld {
    // ...
    class ULevel* PersistentLevel;           // Note the offset - update line 48
    // ...
    class UGameInstance* OwningGameInstance; // Note the offset - update line 47
    // ...
};
```

**Current UE4 values**:
- `OwningGameInstance = 0x180`
- `PersistentLevel = 0x30`

### UGameInstance Offsets

**File to update**: `Engine.h` line 51

Search for: `class UGameInstance`

Find this member:
```cpp
class UGameInstance {
    // ...
    TArray<class UPlayer*> LocalPlayers;  // Note the offset - update line 51
    // ...
};
```

**Current UE4 value**:
- `LocalPlayers = 0x38`

### UPlayer Offsets

**File to update**: `Engine.h` line 54

Search for: `class UPlayer`

Find this member:
```cpp
class UPlayer {
    // ...
    class APlayerController* PlayerController;  // Note the offset - update line 54
    // ...
};
```

**Current UE4 value**:
- `PlayerController = 0x30`

### APlayerController Offsets

**File to update**: `Engine.h` lines 57-58

Search for: `class APlayerController`

Find these members:
```cpp
class APlayerController {
    // ...
    class APawn* AcknowledgedPawn;                    // Note the offset - update line 57
    // ...
    class APlayerCameraManager* PlayerCameraManager;  // Note the offset - update line 58
    // ...
};
```

**Current UE4 values**:
- `AcknowledgedPawn = 0x2a8`
- `CameraManager = 0x2c0`

### APawn Offsets

**File to update**: `Engine.h` line 61 AND `ActorEntity.h` line 19

Search for: `class APawn`

Find this member:
```cpp
class APawn {
    // ...
    class APlayerState* PlayerState;  // Note the offset - update both files
    // ...
};
```

**Current UE4 value**:
- `PlayerState = 0x248`

### APlayerCameraManager Offsets

**File to update**: `Engine.h` line 65

Search for: `class APlayerCameraManager`

Find this member:
```cpp
class APlayerCameraManager {
    // ...
    struct FCameraCacheEntry CameraCachePrivate;  // Note the offset - update line 65
    // ...
};
```

**Current UE4 value**:
- `CameraCachePrivateOffset = 0x1af0`

**IMPORTANT**: Also verify that `FCameraCacheEntry` structure in `EngineStructs.h` matches the UE5 definition!

### AActor Offsets

**File to update**: `ActorEntity.h` lines 25-26

Search for: `class AActor`

Find these members:
```cpp
class AActor {
    // ...
    // Some ID field - may be InternalIndex, NetIndex, or similar
    uint32 SomeIDField;                       // Find equivalent - update line 26
    // ...
    class USceneComponent* RootComponent;     // Note the offset - update line 25
    // ...
};
```

**Current UE4 values**:
- `RootComponent = 0x138`
- `EntityID = 0x18` (may need to find equivalent field)

### USceneComponent Offsets

**File to update**: `ActorEntity.h` line 29

Search for: `class USceneComponent`

Find this member:
```cpp
class USceneComponent {
    // ...
    struct FVector RelativeLocation;  // Note the offset - update line 29
    // ...
};
```

**Current UE4 value**:
- `RelativeLocation = 0x11c`

## Step 4: Find Squad-Specific Offsets

These are game-specific classes that may have different names or structures in UE5.

### ASQPlayerState Offsets

**File to update**: `Engine.h` line 68 AND `ActorEntity.h` line 32

Search for: `class ASQPlayerState` (or just search for "TeamID" in all Squad classes)

Find the TeamID member:
```cpp
class ASQPlayerState {
    // ...
    int32 TeamID;  // or TeamId, or Team - note the offset
    // ...
};
```

**Current UE4 value**:
- `TeamID = 0x400`

### ASQSoldier Offsets (CRITICAL!)

**File to update**: `ActorEntity.h` line 35

Search for: `class ASQSoldier` (this is Squad's main player character class)

Find the Health member:
```cpp
class ASQSoldier {
    // ...
    float Health;  // or CurrentHealth, HealthPoints, etc.
    // ...
};
```

**Current UE4 value**:
- `HealthOffset = 0x1df8`

**WARNING**: This offset is VERY likely to change in UE5. Make sure you find the correct health field!

## Step 5: Verify Structure Layouts

### Check FCameraCacheEntry

**File to update**: `EngineStructs.h` lines 20-25

In Dumper-7's SDK, search for: `struct FCameraCacheEntry`

Verify the structure matches:
```cpp
struct FCameraCacheEntry {
    float Timestamp;                    // 0x00
    // [Padding - verify size]
    struct FMinimalViewInfo POV;        // Should be at 0x10
};
```

Also search for `struct FMinimalViewInfo` and verify:
```cpp
struct FMinimalViewInfo {
    struct FVector Location;    // 0x00 (0xC size)
    struct FRotator Rotation;   // 0x0C (0xC size)
    float FOV;                  // 0x18
};
```

**IMPORTANT**: If the padding or structure layout changed, update `EngineStructs.h`!

## Step 6: Test and Verify

After updating all offsets:

1. Compile the project
2. Run SquadDMA and check the console output
3. Verify that GWorld, PersistentLevel, and other pointers are valid (not NULL, not garbage values)
4. Test ESP functionality - if positions are wrong, check:
   - RelativeLocation offset
   - RootComponent offset
   - Camera offsets
5. Test health display - if health is wrong, verify HealthOffset
6. Test team detection - if team colors are wrong, verify TeamID offset

## Common Issues

### Issue: All pointers are NULL
- **Cause**: GWorld or GName address is wrong
- **Fix**: Re-verify base addresses with Dumper-7

### Issue: Actors not detected
- **Cause**: PersistentLevel, OwningActor, or MaxPacket offsets are wrong
- **Fix**: Check UWorld and UNetConnection offsets

### Issue: Players show at (0,0,0)
- **Cause**: RootComponent or RelativeLocation offsets are wrong
- **Fix**: Check AActor and USceneComponent offsets

### Issue: Wrong health values
- **Cause**: HealthOffset is wrong
- **Fix**: Re-search for Health field in ASQSoldier class

### Issue: Wrong team colors
- **Cause**: TeamID offset is wrong
- **Fix**: Re-search for TeamID in ASQPlayerState class

### Issue: Camera/WorldToScreen not working
- **Cause**: CameraCachePrivateOffset or structure layout changed
- **Fix**: Verify APlayerCameraManager offset and FCameraCacheEntry structure

## Quick Reference: Files to Update

| File | Lines to Update | What to Find |
|------|----------------|--------------|
| `Engine.h` | 30-31 | GWorld, GName base addresses |
| `Engine.h` | 39-40 | UNetConnection offsets |
| `Engine.h` | 47-48 | UWorld offsets |
| `Engine.h` | 51 | UGameInstance offsets |
| `Engine.h` | 54 | UPlayer offsets |
| `Engine.h` | 57-58 | APlayerController offsets |
| `Engine.h` | 61 | APawn offsets |
| `Engine.h` | 65 | APlayerCameraManager offsets |
| `Engine.h` | 68 | ASQPlayerState offsets |
| `ActorEntity.h` | 19 | APawn offsets |
| `ActorEntity.h` | 22 | APlayerController offsets |
| `ActorEntity.h` | 25-26 | AActor offsets |
| `ActorEntity.h` | 29 | USceneComponent offsets |
| `ActorEntity.h` | 32 | ASQPlayerState offsets |
| `ActorEntity.h` | 35 | ASQSoldier offsets |
| `EngineStructs.h` | 20-25 | FCameraCacheEntry structure |

## Additional Notes for Security Researchers

When documenting this for EAC and game developers:

1. **Explain the detection vectors**:
   - DMA hardware bypasses kernel-level protection
   - Offsets need to be randomized or obfuscated
   - Structure padding can be randomized to break hardcoded offsets

2. **Mitigation recommendations**:
   - Implement ASLR for critical structures
   - Add integrity checks on camera and player data
   - Monitor for suspicious memory read patterns
   - Consider structure layout randomization per build

3. **Educational value**:
   - Shows how external tools can manipulate game memory
   - Demonstrates importance of memory protection
   - Highlights vulnerabilities in client-side data storage

## References

- [Dumper-7 GitHub](https://github.com/Encryqed/Dumper-7)
- [Unreal Engine Documentation](https://docs.unrealengine.com/)
- [SquadDMA Original Repository](https://github.com/puow/SquadDMA)
