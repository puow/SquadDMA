# Current UE5 Offset Values - Quick Reference

## Verify Each Value Against Dumper-7 Output

| # | Offset Name | File | Current Value | Class to Search | Member Name | Where to Look |
|---|-------------|------|---------------|-----------------|-------------|---------------|
| 1 | **GWorld** | Engine.h | `0xCA49DE8` | N/A | N/A | JSON metadata (decimal: 212061544) |
| 2 | **GName** | Engine.h | `0xC788078` | N/A | N/A | JSON metadata (decimal: 209152632) |
| 3 | **OwningGameInstance** | Engine.h | `0x1E0` | `class UWorld :` | `OwningGameInstance` | Engine_classes.hpp |
| 4 | **PersistentLevel** | Engine.h | `0x30` | `class UWorld :` | `PersistentLevel` | Engine_classes.hpp |
| 5 | **LocalPlayers** | Engine.h | `0x38` | `class UGameInstance :` | `LocalPlayers` | Engine_classes.hpp |
| 6 | **PlayerController** | Engine.h | `0x30` | `class UPlayer :` | `PlayerController` | Engine_classes.hpp |
| 7 | **AcknowledgedPawn** | Engine.h & ActorEntity.h | `0x370` | `class APlayerController :` | `AcknowledgedPawn` | Engine_classes.hpp |
| 8 | **CameraManager** | Engine.h | `0x380` | `class APlayerController :` | `PlayerCameraManager` | Engine_classes.hpp |
| 9 | **PlayerState** | Engine.h & ActorEntity.h | `0x2D0` | `class APawn :` | `PlayerState` | Engine_classes.hpp |
| 10 | **CameraCachePrivateOffset** | Engine.h | `0x1460` | `class APlayerCameraManager :` | `CameraCachePrivate` | Engine_classes.hpp |
| 11 | **RootComponent** | ActorEntity.h | `0x1C0` | `class AActor :` | `RootComponent` | Engine_classes.hpp |
| 12 | **RelativeLocation** | ActorEntity.h | `0x128` | `class USceneComponent :` | `RelativeLocation` | Engine_classes.hpp |
| 13 | **TeamID** | Engine.h & ActorEntity.h | `0x500` | `class ASQPlayerState :` | `TeamId` (or TeamID) | Squad_classes.hpp |
| 14 | **HealthOffset** | ActorEntity.h | `0x26D0` | `class ASQSoldier :` | `Health` | Squad_classes.hpp |

---

## How You Manually Found These (Your Exact Lines)

### RelativeLocation = 0x128
```cpp
struct FVector RelativeLocation; // 0x0128(0x000C)(Edit, BlueprintVisible, ZeroConstructor, DisableEditOnInstance, IsPlainOldData, NoDestructor, HasGetValueTypeHash, NativeAccessSpecifierPublic)
```

### TeamID = 0x500
```cpp
int32 TeamId; // 0x0500(0x0004)(Net, ZeroConstructor, Transient, IsPlainOldData, RepNotify, NoDestructor, HasGetValueTypeHash, NativeAccessSpecifierPublic)
```

### Health = 0x26D0
```cpp
float Health; // 0x26D0(0x0004)(BlueprintVisible, BlueprintReadOnly, Net, ZeroConstructor, IsPlainOldData, RepNotify, NoDestructor, HasGetValueTypeHash, NativeAccessSpecifierPublic)
```

---

## Offsets Changed From UE4 to UE5

| Offset | UE4 Value | UE5 Value | Difference | Change |
|--------|-----------|-----------|------------|--------|
| GWorld | 0x72aa2e0 | 0xCA49DE8 | +0x579EB08 | +91 MB |
| GName | 0x7129580 | 0xC788078 | +0x565EAF8 | +89 MB |
| OwningGameInstance | 0x180 | 0x1E0 | +0x60 | +96 bytes |
| AcknowledgedPawn | 0x2a8 | 0x370 | +0xC8 | +200 bytes |
| CameraManager | 0x2c0 | 0x380 | +0xC0 | +192 bytes |
| PlayerState | 0x248 | 0x2D0 | +0x88 | +136 bytes |
| CameraCachePrivateOffset | 0x1af0 | 0x1460 | -0x690 | -1680 bytes (DECREASED!) |
| RootComponent | 0x138 | 0x1C0 | +0x88 | +136 bytes |
| RelativeLocation | 0x11c | 0x128 | +0xC | +12 bytes |
| TeamID | 0x400 | 0x500 | +0x100 | +256 bytes |
| **Health** | **0x1df8** | **0x26D0** | **+0x8D8** | **+2264 bytes (HUGE!)** |

---

## Verification Steps

1. **Base Addresses**: Find the JSON metadata file with decimal values, convert to hex
2. **Engine Offsets**: Open `CppSDK\SDK\Engine_classes.hpp`, search for each class, find member
3. **Squad Offsets**: Open `CppSDK\SDK\Squad_classes.hpp`, search for ASQPlayerState and ASQSoldier

---

## What to Tell Me

If you find different values, paste the **exact line** like:

```
RelativeLocation:
struct FVector RelativeLocation; // 0x0128(0x000C)(flags...)
From file: Engine_classes.hpp
Inside class: USceneComponent
```

Then I can verify if the offset is correct or if the scanner made a mistake.

---

## Most Critical Offsets

These are the most important for ESP functionality:

1. ✅ **GWorld** - Without this, nothing works
2. ✅ **AcknowledgedPawn** - Needed to get local player
3. ✅ **PlayerState** - Needed for team detection
4. ✅ **TeamID** - Team differentiation (friend/foe)
5. ✅ **Health** - Health display (biggest UE4→UE5 change!)
6. ✅ **RelativeLocation** - Player positions for ESP boxes

If these 6 are correct, the ESP should at least show basic info.
