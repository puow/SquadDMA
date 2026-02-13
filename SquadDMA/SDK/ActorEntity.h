#pragma once
#include "EngineStructs.h"

/*
 * UE5 Actor Entity Offsets
 *
 * Updated for Squad v10.2 (Unreal Engine 5)
 * Generated from Dumper-7 output
 * All offsets marked [UE5] have been verified
 */

class ActorEntity
{
private:
	uint64_t Class = 0;

	// =============================================================================
	// ENGINE STRUCTURE OFFSETS (Updated for UE5!)
	// =============================================================================

	// APawn offsets (search Engine_Classes.hpp for "class APawn")
	uint64_t PlayerState = 0x2D0;        // APawn::PlayerState [UE5]

	// APlayerController offsets (search for "class APlayerController")
	uint64_t AcknowledgedPawn = 0x370;   // APlayerController::AcknowledgedPawn [UE5]

	// AActor offsets (search for "class AActor")
	uint64_t RootComponent = 0x1C0;      // AActor::RootComponent [UE5]
	uint32_t EntityID = 0x18;            // AActor::InternalIndex or similar ID field

	// USceneComponent offsets (search for "class USceneComponent")
	uint64_t RelativeLocation = 0x128;   // USceneComponent::RelativeLocation [UE5]

	// =============================================================================
	// SQUAD-SPECIFIC OFFSETS (Updated for UE5!)
	// =============================================================================

	// ASQPlayerState offsets (search for "class ASQPlayerState" in Squad SDK dump)
	uint32_t TeamID = 0x500;             // ASQPlayerState::TeamId [UE5]

	// ASQSoldier offsets (search for "class ASQSoldier" - this is Squad's player character class)
	uint32_t HealthOffset = 0x26D0;      // ASQSoldier::Health [UE5]
	float Health = 0;
	std::wstring Name = LIT(L"Enemy");
	UEVector UEPosition;
	Vector3 Position;
public:
	ActorEntity(uint64_t address, VMMDLL_SCATTER_HANDLE handle);
	void SetUp1(VMMDLL_SCATTER_HANDLE handle);
	void SetUp2();
	uint64_t GetClass();
	std::wstring GetName();
	Vector3 GetPosition();
	void UpdatePosition(VMMDLL_SCATTER_HANDLE handle);
	void UpdateHealth(VMMDLL_SCATTER_HANDLE handle);
	uint32_t GetEntityID();
	int GetTeamID();
	float GetHealth();
};
