#pragma once
#include "ActorEntity.h"
#include "EngineStructs.h"

/*
 * UE5 Offset Configuration
 *
 * IMPORTANT: These offsets are for UE4 and MUST be updated for UE5!
 * Use Dumper-7 (https://github.com/Encryqed/Dumper-7) on the UE5 version of Squad
 *
 * Instructions:
 * 1. Run Dumper-7 on Squad.exe (UE5 version)
 * 2. Open the generated SDK/Engine_Classes.hpp file
 * 3. Search for each class below and find the member offsets
 * 4. Update GWorld and GName base addresses from the dumper output
 *
 * See UE5_OFFSETS_GUIDE.md for detailed instructions
 */

class Engine
{

private:
	// =============================================================================
	// BASE ADDRESSES (Will change in UE5!)
	// =============================================================================
	// These are absolute addresses in the game binary and WILL be different in UE5
	// Find these in Dumper-7 output or use a pattern scanner
	uint64_t GWorld = 0x72aa2e0;      // [UE4] Global UWorld pointer - NEEDS UPDATE
	uint64_t GName = 0x7129580;       // [UE4] Global FNamePool - NEEDS UPDATE

	// =============================================================================
	// STRUCTURE OFFSETS (May change in UE5!)
	// =============================================================================
	// These are offsets within UE classes - search Engine_Classes.hpp for:

	// UNetConnection offsets (search for "class UNetConnection")
	uint64_t OwningActorOffset = 0x98;  // UNetConnection::OwningActor
	uint64_t MaxPacketOffset = 0xa0;    // UNetConnection::MaxPacket

	// Runtime variables
	uint64_t OwningActor;
	uint64_t MaxPacket;

	// UWorld offsets (search for "class UWorld")
	uint64_t OwningGameInstance = 0x180; // UWorld::OwningGameInstance
	uint64_t PersistentLevel = 0x30;     // UWorld::PersistentLevel

	// UGameInstance offsets (search for "class UGameInstance")
	uint64_t LocalPlayers = 0x38;        // UGameInstance::LocalPlayers

	// UPlayer offsets (search for "class UPlayer")
	uint64_t PlayerController = 0x30;    // UPlayer::PlayerController

	// APlayerController offsets (search for "class APlayerController")
	uint64_t AcknowledgedPawn = 0x2a8;   // APlayerController::AcknowledgedPawn
	uint64_t CameraManager = 0x2c0;      // APlayerController::PlayerCameraManager

	// APawn offsets (search for "class APawn")
	uint64_t PlayerState = 0x248;        // APawn::PlayerState

	// APlayerCameraManager offsets (search for "class APlayerCameraManager")
	uint64_t CameraCachePrivate = 0x0;
	uint64_t CameraCachePrivateOffset = 0x1af0; // APlayerCameraManager::CameraCachePrivate

	// Squad-specific: ASQPlayerState offsets (search for "class ASQPlayerState")
	uint64_t TeamID = 0x400;             // ASQPlayerState::TeamID
	CameraCacheEntry CameraEntry; // ScriptStruct Engine.CameraCacheEntry
	MinimalViewInfo CameraViewInfo; // ScriptStruct Engine.MinimalViewInfo
	std::vector<std::shared_ptr<ActorEntity>> Actors;
	std::string ResolveGName(const uint32_t& id);
	std::map<uint32_t, std::string> GNamesMap;

	std::mutex ActorMutex;
public:
	Engine();
	void Cache();
	void UpdatePlayers();
	std::vector<std::shared_ptr<ActorEntity>> GetActors();
	CameraCacheEntry GetCameraCache();
	void RefreshViewMatrix(VMMDLL_SCATTER_HANDLE handle);
	uint32_t GetActorSize();

};