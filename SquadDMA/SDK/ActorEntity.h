#pragma once
#include "EngineStructs.h"

/*
 * UE5 Actor Entity Offsets
 *
 * IMPORTANT: These offsets are for UE4 and MUST be updated for UE5!
 * Use Dumper-7 on Squad UE5 to find the new offsets
 */

class ActorEntity
{
private:
	uint64_t Class = 0;

	// =============================================================================
	// ENGINE STRUCTURE OFFSETS (May change in UE5!)
	// =============================================================================

	// APawn offsets (search Engine_Classes.hpp for "class APawn")
	uint64_t PlayerState = 0x248;        // APawn::PlayerState

	// APlayerController offsets (search for "class APlayerController")
	uint64_t AcknowledgedPawn = 0x2a8;   // APlayerController::AcknowledgedPawn

	// AActor offsets (search for "class AActor")
	uint64_t RootComponent = 0x138;      // AActor::RootComponent
	uint32_t EntityID = 0x18;            // AActor::InternalIndex or similar ID field

	// USceneComponent offsets (search for "class USceneComponent")
	uint64_t RelativeLocation = 0x11c;   // USceneComponent::RelativeLocation

	// =============================================================================
	// SQUAD-SPECIFIC OFFSETS (Likely to change in UE5!)
	// =============================================================================

	// ASQPlayerState offsets (search for "class ASQPlayerState" in Squad SDK dump)
	uint32_t TeamID = 0x400;             // ASQPlayerState::TeamID

	// ASQSoldier offsets (search for "class ASQSoldier" - this is Squad's player character class)
	uint32_t HealthOffset = 0x1df8;      // ASQSoldier::Health - CRITICAL: Game-specific, verify in UE5!
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