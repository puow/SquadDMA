# Manual UE5 Offset Verification Guide

This guide shows **exactly** where to find each offset in your Dumper-7 output.

## Your Dumper-7 Directory
```
C:\Users\Admin\Desktop\5.5.4-546763+__Squad_v10.2-SquadGame\
```

---

## BASE ADDRESSES (2 offsets)

### 1. GWorld
- **Current Value**: `0xCA49DE8`
- **Where to Find**: Look in the **JSON metadata file** or **GObjects-Dump.txt** header
- **Format**: Usually appears as:
  ```
  ["OFFSET_GWORLD", 212061544]  // Decimal - convert to hex = 0xCA49DE8
  ```
  OR search for "GWorld" in the dump file (but be careful - class instances are wrong!)

### 2. GName (FName Pool)
- **Current Value**: `0xC788078`
- **Where to Find**: Same JSON metadata file
- **Format**:
  ```
  ["OFFSET_GNAMES", 209152632]  // Decimal - convert to hex = 0xC788078
  ```

---

## ENGINE OFFSETS (Open: CppSDK\SDK\Engine_classes.hpp)

### 3. UWorld::OwningGameInstance
- **Current Value**: `0x1E0`
- **Search For**: `class UWorld :`
- **Then Find Line**: `class UGameInstance* OwningGameInstance;`
- **Format Example**:
  ```cpp
  class UGameInstance* OwningGameInstance;  // 0x01E0(0x0008)
                                               ^^^^^^
                                               THIS IS THE OFFSET!
  ```

### 4. UWorld::PersistentLevel
- **Current Value**: `0x30`
- **Search In**: Same `class UWorld :`
- **Find Line**: `class ULevel* PersistentLevel;`
- **Format**: `// 0x0030(0x0008)`

### 5. UGameInstance::LocalPlayers
- **Current Value**: `0x38`
- **Search For**: `class UGameInstance :`
- **Find Line**: `TArray<class ULocalPlayer*> LocalPlayers;`
- **Format**: `// 0x0038(0x0010)` (TArray offset)

### 6. UPlayer::PlayerController
- **Current Value**: `0x30`
- **Search For**: `class UPlayer :`
- **Find Line**: `class APlayerController* PlayerController;`
- **Format**: `// 0x0030(0x0008)`

### 7. APlayerController::AcknowledgedPawn
- **Current Value**: `0x370`
- **Search For**: `class APlayerController :`
- **Find Line**: `class APawn* AcknowledgedPawn;`
- **Format**: `// 0x0370(0x0008)`

### 8. APlayerController::PlayerCameraManager
- **Current Value**: `0x380`
- **Search In**: Same `class APlayerController :`
- **Find Line**: `class APlayerCameraManager* PlayerCameraManager;`
- **Format**: `// 0x0380(0x0008)`

### 9. APawn::PlayerState
- **Current Value**: `0x2D0`
- **Search For**: `class APawn :`
- **Find Line**: `class APlayerState* PlayerState;`
- **Format**: `// 0x02D0(0x0008)`

### 10. APlayerCameraManager::CameraCachePrivate (or CameraCacheEntry)
- **Current Value**: `0x1460`
- **Search For**: `class APlayerCameraManager :`
- **Find Line**: Look for `struct FCameraCacheEntry CameraCachePrivate;` OR `CameraCacheEntry`
- **Format**: `// 0x1460(0x0010)` or similar

### 11. AActor::RootComponent
- **Current Value**: `0x1C0`
- **Search For**: `class AActor :`
- **Find Line**: `class USceneComponent* RootComponent;`
- **Format**: `// 0x01C0(0x0008)`

### 12. USceneComponent::RelativeLocation
- **Current Value**: `0x128`
- **Search For**: `class USceneComponent :`
- **Find Line**: `struct FVector RelativeLocation;`
- **Format**: `// 0x0128(0x000C)`

---

## SQUAD-SPECIFIC OFFSETS (Open: CppSDK\SDK\Squad_classes.hpp)

### 13. ASQPlayerState::TeamId
- **Current Value**: `0x500`
- **Search For**: `class ASQPlayerState :`
- **Find Line**: `int32 TeamId;` OR `int32_t TeamId;` OR `int32 TeamID;`
- **Format**: `// 0x0500(0x0004)`
- **Note**: Could be called TeamId, TeamID, Team, etc.

### 14. ASQSoldier::Health
- **Current Value**: `0x26D0`
- **Search For**: `class ASQSoldier :`
- **Find Line**: `float Health;` OR look for health-related members
- **Format**: `// 0x26D0(0x0004)`
- **Note**: This is the BIGGEST change from UE4!

---

## HOW TO READ THE OFFSET FORMAT

When you find a line like:
```cpp
class UGameInstance* OwningGameInstance;  // 0x01E0(0x0008)(ZeroConstructor, Transient, ...)
```

Breaking it down:
- `class UGameInstance*` = Type
- `OwningGameInstance` = Member name
- `0x01E0` = **THE OFFSET YOU NEED** ← This is what goes in Engine.h/ActorEntity.h
- `0x0008` = Size (8 bytes for a pointer on 64-bit)
- Everything else = Flags (ignore these)

---

## VERIFICATION CHECKLIST

For each offset, verify:

1. ✅ **GWorld** from metadata JSON (decimal to hex)
2. ✅ **GName** from metadata JSON (decimal to hex)
3. ✅ **UWorld::OwningGameInstance** from Engine_classes.hpp
4. ✅ **UWorld::PersistentLevel** from Engine_classes.hpp
5. ✅ **UGameInstance::LocalPlayers** from Engine_classes.hpp
6. ✅ **UPlayer::PlayerController** from Engine_classes.hpp
7. ✅ **APlayerController::AcknowledgedPawn** from Engine_classes.hpp
8. ✅ **APlayerController::PlayerCameraManager** from Engine_classes.hpp
9. ✅ **APawn::PlayerState** from Engine_classes.hpp
10. ✅ **APlayerCameraManager::CameraCachePrivate** from Engine_classes.hpp
11. ✅ **AActor::RootComponent** from Engine_classes.hpp
12. ✅ **USceneComponent::RelativeLocation** from Engine_classes.hpp
13. ✅ **ASQPlayerState::TeamId** from Squad_classes.hpp
14. ✅ **ASQSoldier::Health** from Squad_classes.hpp

---

## COMMON MISTAKES TO AVOID

### ❌ Wrong: Class Instance Addresses
```
[000012BA] {0x7ff4de062000} Class PCG.PCGWorldActor
```
This is a **class instance address** in memory, NOT the global GWorld offset!

### ✅ Right: Metadata Offset
```json
["OFFSET_GWORLD", 212061544]  // Convert to hex: 0xCA49DE8
```

### ❌ Wrong: Looking at wrong class
If searching for PlayerState offset, make sure you're in `class APawn :`, not `class APlayerState :`

### ✅ Right: Member inside correct class
```cpp
class APawn : public AActor
{
    // ... other members ...
    class APlayerState* PlayerState;  // 0x02D0(0x0008) ← This is correct!
}
```

---

## QUICK SEARCH COMMANDS (Windows)

If using Visual Studio Code or Notepad++:

1. Open `Engine_classes.hpp`
2. Press `Ctrl+F` to search
3. Search for exact class names:
   - `class UWorld :`
   - `class APawn :`
   - `class APlayerController :`
   - etc.

4. Within that class, find the member name
5. Read the hex value after `//`

---

## FILES YOU NEED

```
CppSDK\SDK\Engine_classes.hpp    ← Most engine offsets here
CppSDK\SDK\Squad_classes.hpp     ← TeamId and Health here
GObjects-Dump.txt                 ← May contain base addresses
[Some JSON file]                  ← Has decimal base addresses (find this!)
```

---

## EXAMPLE: Finding RelativeLocation

1. Open `Engine_classes.hpp`
2. Search for: `class USceneComponent`
3. Find the full class definition starting with `class USceneComponent :`
4. Scroll through members until you find:
   ```cpp
   struct FVector RelativeLocation;  // 0x0128(0x000C)(Edit, BlueprintVisible, ...)
   ```
5. The offset is **0x0128** = **0x128** (you can drop leading zero)

---

## NEED HELP?

If you find different values:
1. Note the exact line from the .hpp file
2. Note which class it's in
3. Note the offset value you see
4. We can verify if it's correct

The scanner might have issues with:
- Multi-line class definitions
- Comments interfering with parsing
- Different naming conventions (TeamId vs TeamID)
- Inherited members vs direct members
