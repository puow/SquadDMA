#include "Pch.h"
#include "Engine.h"
#include "ActorEntity.h"
#include "Globals.h"

Engine::Engine()
{
	printf("\n=== ENGINE INITIALIZATION & OFFSET VALIDATION ===\n");

	// Test GWorld
	printf("\n[1] Testing GWorld...\n");
	printf("  GWorld offset: 0x%llX\n", GWorld);
	printf("  Base + GWorld: 0x%llX\n", TargetProcess.GetBaseAddress(ProcessName) + GWorld);
	GWorld = TargetProcess.Read<uint64_t>(TargetProcess.GetBaseAddress(ProcessName) + GWorld);
	printf("  GWorld value: 0x%llX %s\n", GWorld, GWorld ? "[OK]" : "[FAIL - NULL!]");

	// Test PersistentLevel
	printf("\n[2] Testing PersistentLevel...\n");
	printf("  Offset: 0x%llX\n", PersistentLevel);
	printf("  Reading from: 0x%llX\n", GWorld + PersistentLevel);
	PersistentLevel = TargetProcess.Read<uint64_t>(GWorld + PersistentLevel);
	printf("  PersistentLevel value: 0x%llX %s\n", PersistentLevel, PersistentLevel ? "[OK]" : "[FAIL - NULL!]");

	// Test OwningGameInstance
	printf("\n[3] Testing OwningGameInstance...\n");
	printf("  Offset: 0x%llX\n", OwningGameInstance);
	printf("  Reading from: 0x%llX\n", GWorld + OwningGameInstance);
	OwningGameInstance = TargetProcess.Read<uint64_t>(GWorld + OwningGameInstance);
	printf("  OwningGameInstance value: 0x%llX %s\n", OwningGameInstance, OwningGameInstance ? "[OK]" : "[FAIL - NULL!]");

	// Test LocalPlayers
	printf("\n[4] Testing LocalPlayers (TArray)...\n");
	printf("  Offset: 0x%llX\n", LocalPlayers);
	printf("  Reading from: 0x%llX\n", OwningGameInstance + LocalPlayers);
	LocalPlayers = TargetProcess.Read<uint64_t>(OwningGameInstance + LocalPlayers);
	printf("  LocalPlayers[0] ptr: 0x%llX %s\n", LocalPlayers, LocalPlayers ? "[OK]" : "[FAIL - NULL!]");

	// Dereference to get first player
	printf("  Dereferencing to get ULocalPlayer...\n");
	LocalPlayers = TargetProcess.Read<uint64_t>(LocalPlayers);
	printf("  ULocalPlayer: 0x%llX %s\n", LocalPlayers, LocalPlayers ? "[OK]" : "[FAIL - NULL!]");

	// Test PlayerController
	printf("\n[5] Testing PlayerController...\n");
	printf("  Offset: 0x%llX\n", PlayerController);
	printf("  Reading from: 0x%llX\n", LocalPlayers + PlayerController);
	PlayerController = TargetProcess.Read<uint64_t>(LocalPlayers + PlayerController);
	printf("  PlayerController: 0x%llX %s\n", PlayerController, PlayerController ? "[OK]" : "[FAIL - NULL!]");

	// Test AcknowledgedPawn
	printf("\n[6] Testing AcknowledgedPawn...\n");
	printf("  Offset: 0x%llX\n", AcknowledgedPawn);
	printf("  Reading from: 0x%llX\n", PlayerController + AcknowledgedPawn);
	AcknowledgedPawn = TargetProcess.Read<uint64_t>(PlayerController + AcknowledgedPawn);
	printf("  AcknowledgedPawn: 0x%llX %s\n", AcknowledgedPawn, AcknowledgedPawn ? "[OK]" : "[FAIL - NULL!]");

	// Test PlayerState
	printf("\n[7] Testing PlayerState...\n");
	printf("  Offset: 0x%llX\n", PlayerState);
	printf("  Reading from: 0x%llX\n", AcknowledgedPawn + PlayerState);
	PlayerState = TargetProcess.Read<uint64_t>(AcknowledgedPawn + PlayerState);
	printf("  PlayerState: 0x%llX %s\n", PlayerState, PlayerState ? "[OK]" : "[FAIL - NULL!]");

	// Test CameraManager
	printf("\n[8] Testing CameraManager...\n");
	printf("  Offset: 0x%llX\n", CameraManager);
	printf("  Reading from: 0x%llX\n", PlayerController + CameraManager);
	CameraManager = TargetProcess.Read<uint64_t>(PlayerController + CameraManager);
	printf("  CameraManager: 0x%llX %s\n", CameraManager, CameraManager ? "[OK]" : "[FAIL - NULL!]");

	// Test CameraCacheEntry
	printf("\n[9] Testing CameraCacheEntry...\n");
	printf("  Offset: 0x%llX\n", CameraCachePrivateOffset);
	printf("  Reading from: 0x%llX\n", CameraManager + CameraCachePrivateOffset);
	CameraEntry = TargetProcess.Read<CameraCacheEntry>(CameraManager + CameraCachePrivateOffset);
	printf("  CameraCacheEntry FOV: %.2f %s\n", CameraEntry.POV.FOV,
		(CameraEntry.POV.FOV > 0 && CameraEntry.POV.FOV < 180) ? "[OK]" : "[WARN - unusual FOV!]");

	// Test GName/FNamePool
	printf("\n[10] Testing GName/FNamePool...\n");
	printf("  GName offset: 0x%llX\n", GName);
	uintptr_t gname = TargetProcess.GetBaseAddress(ProcessName) + GName;
	printf("  GName address: 0x%llX\n", gname);
	uintptr_t blocks_array = TargetProcess.Read<uintptr_t>(gname + 0x10);
	printf("  Blocks array ptr (at +0x10): 0x%llX %s\n", blocks_array, blocks_array ? "[OK]" : "[FAIL - NULL!]");

	if (blocks_array) {
		// Test reading block 0
		uintptr_t block0 = TargetProcess.Read<uintptr_t>(blocks_array);
		printf("  Block[0] ptr: 0x%llX %s\n", block0, block0 ? "[OK]" : "[FAIL - NULL!]");

		// Try to read a common FName (id 0 is usually "None")
		if (block0) {
			uint16_t entry0_header = TargetProcess.Read<uint16_t>(block0);
			uint32_t entry0_len = entry0_header >> 6;
			printf("  FName[0] length: %u %s\n", entry0_len,
				(entry0_len > 0 && entry0_len < 64) ? "[OK]" : "[WARN]");

			if (entry0_len > 0 && entry0_len < 64) {
				char testname[64] = {0};
				TargetProcess.Read(block0 + 0x2, &testname, entry0_len);
				printf("  FName[0] string: '%s'\n", testname);
			}
		}
	}

	printf("\n=== INITIALIZATION COMPLETE ===\n\n");
}

std::string Engine::ResolveGName(const uint32_t& id)
{
	static int debug_count = 0;
	char name[256];
	memset(name, 0, sizeof(name));

	uintptr_t gname = TargetProcess.GetBaseAddress(ProcessName) + GName;

	// UE5 FNamePool: Blocks array is at offset 0x10
	uintptr_t blocks_array = TargetProcess.Read<uintptr_t>(gname + 0x10);

	// UE5: Each block contains 16384 (0x4000) entries
	const uint32_t ENTRIES_PER_BLOCK = 0x4000;
	uint32_t block = id / ENTRIES_PER_BLOCK;
	uint32_t offset = id % ENTRIES_PER_BLOCK;

	if (debug_count < 3) {
		printf("\n[DEBUG GName #%d] ID=%u (0x%X), Block=%u, Offset=%u\n", debug_count + 1, id, id, block, offset);
		printf("  GName base: 0x%llX\n", gname);
		printf("  Blocks array ptr (gname+0x10): 0x%llX\n", blocks_array);
	}

	if (!blocks_array) {
		if (debug_count < 3) printf("  ERROR: Blocks array pointer is NULL!\n");
		debug_count++;
		return LIT("");
	}

	// Read the specific block pointer from the blocks array
	uintptr_t namepool = TargetProcess.Read<uintptr_t>(blocks_array + (block * 8));

	if (debug_count < 3) {
		printf("  Block[%u] ptr addr: 0x%llX\n", block, blocks_array + (block * 8));
		printf("  Block[%u] ptr value: 0x%llX\n", block, namepool);
	}

	if (!namepool) {
		if (debug_count < 3) printf("  ERROR: Block pointer is NULL!\n");
		debug_count++;
		return LIT("");
	}

	// Calculate entry address: block base + (offset * 2) for FNameEntry header
	uintptr_t entry = namepool + (offset * 2);

	uint16_t nameentry = TargetProcess.Read<uint16_t>(entry);
	uint32_t namelength = (nameentry >> 6);

	if (debug_count < 3) {
		printf("  Entry addr: 0x%llX\n", entry);
		printf("  Name header: 0x%X, Length: %u\n", nameentry, namelength);
	}

	if (namelength == 0 || namelength > 256) {
		if (debug_count < 3) printf("  ERROR: Invalid length!\n");
		debug_count++;
		return LIT("");
	}

	auto result = TargetProcess.Read(entry + 0x2, &name, namelength);

	if (debug_count < 3) {
		printf("  Name read: '%s'\n", name);
		debug_count++;
	}

	return std::string(name, namelength);
}

void Engine::Cache()
{

	OwningActor = TargetProcess.Read<uint64_t>(PersistentLevel + OwningActorOffset);
	if(!OwningActor)
	{
		MaxPacket = 0;
		return;
	}
	MaxPacket = TargetProcess.Read<uint32_t>(PersistentLevel + MaxPacketOffset);
	if (MaxPacket > 6000)
	{
		MaxPacket = 0;
		return;
	}
	printf(LIT("Actor Array: %p\n"), OwningActor);
	printf(LIT("Actor Array Size: %d\n"), MaxPacket);

	std::vector<uint64_t> entitylist;
	entitylist.resize(MaxPacket);
	std::unique_ptr<uint64_t[]> object_raw_ptr = std::make_unique<uint64_t[]>(MaxPacket);
	TargetProcess.Read(OwningActor, object_raw_ptr.get(), MaxPacket * sizeof(uint64_t));
	for (size_t i = 0; i < MaxPacket; i++)
	{
		entitylist[i] = object_raw_ptr[i];
	}
	int templocalplayerteamid = 0;
	std::list<std::shared_ptr<ActorEntity>> actors;
	auto handle = TargetProcess.CreateScatterHandle();
	for (uint64_t address : entitylist)
	{
		uintptr_t actor = address;
		if (!actor)
			continue;

			std::shared_ptr<ActorEntity> entity = std::make_shared<ActorEntity>(actor, handle);
			actors.push_back(entity);

	}
	TargetProcess.AddScatterReadRequest(handle, PlayerState + TeamID, reinterpret_cast<void*>(&templocalplayerteamid), sizeof(int));
	TargetProcess.ExecuteReadScatter(handle);
	TargetProcess.CloseScatterHandle(handle);
	LocalPlayerTeamID.store(templocalplayerteamid);


	handle = TargetProcess.CreateScatterHandle();
	for (std::shared_ptr<ActorEntity> entity : actors)
	{
		entity->SetUp1(handle);
	}
	TargetProcess.ExecuteReadScatter(handle);
	TargetProcess.CloseScatterHandle(handle);

	// DEBUG: Validate first 3 actors in detail
	printf("\n=== ACTOR OFFSET VALIDATION (First 3 actors) ===\n");
	int validation_count = 0;
	for (std::shared_ptr<ActorEntity> entity : actors)
	{
		if (validation_count >= 3) break;
		validation_count++;

		printf("\nActor #%d:\n", validation_count);
		printf("  Actor address: 0x%llX\n", entity->GetClass());
		printf("  EntityID (at +0x18): %u (0x%X)\n", entity->GetEntityID(), entity->GetEntityID());

		// Test RootComponent (this is critical for position)
		uint64_t test_root = entity->GetClass() ?
			TargetProcess.Read<uint64_t>(entity->GetClass() + 0x1C0) : 0;
		printf("  RootComponent (at +0x1C0): 0x%llX %s\n", test_root,
			test_root ? "[OK]" : "[NULL - can't read position!]");

		// Test position read if RootComponent valid
		if (test_root) {
			UEVector test_pos = TargetProcess.Read<UEVector>(test_root + 0x128);
			printf("  Position (RootComponent+0x128): (%.2f, %.2f, %.2f)\n",
				test_pos.X, test_pos.Y, test_pos.Z);
		}

		printf("  TeamID: %d\n", entity->GetTeamID());
		printf("  Health: %.2f\n", entity->GetHealth());
	}
	printf("=== END ACTOR VALIDATION ===\n\n");

	std::vector<std::shared_ptr<ActorEntity>> playerlist;
	int soldier_count = 0;
	int total_checked = 0;
	for (std::shared_ptr<ActorEntity> entity : actors)
	{
		std::string name = ResolveGName(entity->GetEntityID());
		total_checked++;

		// DEBUG: Print first 50 actor names to see what's in the game
		if(total_checked <= 50) {
			printf("Actor[%d]: %s\n", total_checked, name.c_str());
		}

		// UE5: Class name is "SQSoldier" (found in GObjects-Dump.txt)
		if(name.find(LIT("SQSoldier")) == std::string::npos)
			continue;
		soldier_count++;
		entity->SetUp2();
		Vector3 pos = entity->GetPosition();
		printf("Soldier found: %s at (%.2f, %.2f, %.2f)\n", name.c_str(), pos.x, pos.y, pos.z);
		// Filter out zero positions
		if(pos.x == 0.0f && pos.y == 0.0f && pos.z == 0.0f)
			continue;
		// Filter out extreme/invalid positions (garbage memory reads)
		if (abs(pos.x) > 1000000.0f || abs(pos.y) > 1000000.0f || abs(pos.z) > 100000.0f)
			continue;
		playerlist.push_back(entity);
	}
	printf("Total actors checked: %d, Soldiers found: %d, Soldiers added to list: %d\n", total_checked, soldier_count, (int)playerlist.size());


	ActorMutex.lock();
	Actors = playerlist;
	ActorMutex.unlock();
}
void Engine::UpdatePlayers()
{

	auto handle = TargetProcess.CreateScatterHandle();
	std::vector<std::shared_ptr<ActorEntity>> tempactors;
	ActorMutex.lock();
	tempactors = Actors;
	ActorMutex.unlock();

	for (std::shared_ptr<ActorEntity> entity : tempactors)
	{
		entity->UpdatePosition(handle);
		entity->UpdateHealth(handle);
	}
	TargetProcess.ExecuteReadScatter(handle);
	TargetProcess.CloseScatterHandle(handle);

	// Filter out invalid entities after update
	std::vector<std::shared_ptr<ActorEntity>> validactors;
	for (std::shared_ptr<ActorEntity> entity : tempactors)
	{
		Vector3 pos = entity->GetPosition();
		// Filter out zero positions
		if (pos.x == 0.0f && pos.y == 0.0f && pos.z == 0.0f)
			continue;
		// Filter out extreme/invalid positions (garbage memory reads)
		if (abs(pos.x) > 1000000.0f || abs(pos.y) > 1000000.0f || abs(pos.z) > 100000.0f)
			continue;
		// Filter out dead players
		if (entity->GetHealth() <= 0.0f)
			continue;
		validactors.push_back(entity);
	}

	ActorMutex.lock();
	Actors = validactors;
	ActorMutex.unlock();
}
void Engine::RefreshViewMatrix(VMMDLL_SCATTER_HANDLE handle)
{
	TargetProcess.AddScatterReadRequest(handle, CameraManager + CameraCachePrivateOffset,reinterpret_cast<void*>(&CameraEntry),sizeof(CameraCacheEntry));
}

CameraCacheEntry Engine::GetCameraCache()
{
	return CameraEntry;
}

std::vector<std::shared_ptr<ActorEntity>> Engine::GetActors()
{
	std::vector<std::shared_ptr<ActorEntity>> tempactors;
	ActorMutex.lock();
	tempactors = Actors;
	ActorMutex.unlock();
	return tempactors;
}

uint32_t Engine::GetActorSize()
{
	return MaxPacket;
}
