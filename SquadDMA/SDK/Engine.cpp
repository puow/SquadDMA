#include "Pch.h"
#include "Engine.h"
#include "ActorEntity.h"
#include "Globals.h"

Engine::Engine()
{
	printf("\n=== ENGINE INITIALIZATION & OFFSET VALIDATION ===\n");

	size_t base = TargetProcess.GetBaseAddress(ProcessName);
	size_t base_size = TargetProcess.GetBaseSize(ProcessName);
	size_t base_end = base + base_size;

	// Helper: check if pointer is a valid heap pointer (outside module range)
	auto isHeapPtr = [&](uint64_t ptr) -> bool {
		if (ptr == 0) return false;
		if (ptr < 0x10000) return false;            // Too low
		if (ptr > 0x7FFFFFFFFFFF) return false;     // Kernel space
		if (ptr >= base && ptr < base_end) return false; // Inside module = code/data, not heap UObject
		return true;
	};

	printf("  Module range: 0x%llX - 0x%llX (size: 0x%llX)\n",
		(uint64_t)base, (uint64_t)base_end, (uint64_t)base_size);

	// [1] Read GWorld
	printf("\n[1] Testing GWorld...\n");
	printf("  GWorld offset: 0x%llX\n", GWorld);
	uint64_t gworld_addr = base + GWorld;
	printf("  Base + GWorld: 0x%llX\n", gworld_addr);
	GWorld = TargetProcess.Read<uint64_t>(gworld_addr);
	printf("  GWorld value: 0x%llX\n", GWorld);

	// Check if GWorld is within module range (needs double-dereference)
	if (GWorld >= base && GWorld < base_end) {
		printf("  [!] GWorld (0x%llX) is INSIDE module range - trying double dereference...\n", GWorld);
		uint64_t gworld_deref = TargetProcess.Read<uint64_t>(GWorld);
		printf("  Double-deref GWorld: 0x%llX\n", gworld_deref);
		if (isHeapPtr(gworld_deref)) {
			printf("  [+] Double-deref succeeded! Using 0x%llX as UWorld\n", gworld_deref);
			GWorld = gworld_deref;
		} else {
			printf("  [!] Double-deref also invalid. GWorld may be wrong or game not in match.\n");
		}
	}

	if (!isHeapPtr(GWorld)) {
		printf("  [FAIL] GWorld 0x%llX is not a valid heap pointer!\n", GWorld);
		printf("  Possible causes:\n");
		printf("    - Player not in a match (main menu / loading screen)\n");
		printf("    - Game was updated and GWorld offset changed\n");
		printf("    - GWorld offset 0x%llX is incorrect\n", TargetProcess.Read<uint64_t>(gworld_addr));
		printf("=== INITIALIZATION FAILED - WILL RETRY ===\n\n");
		return;
	}
	printf("  GWorld: 0x%llX [OK - valid heap pointer]\n", GWorld);

	// [2] Read PersistentLevel
	printf("\n[2] Testing PersistentLevel...\n");
	printf("  Offset: 0x%llX\n", PersistentLevel);
	PersistentLevel = TargetProcess.Read<uint64_t>(GWorld + PersistentLevel);
	printf("  PersistentLevel value: 0x%llX %s\n", PersistentLevel,
		isHeapPtr(PersistentLevel) ? "[OK]" : "[FAIL - invalid pointer!]");
	if (!isHeapPtr(PersistentLevel)) {
		printf("  [FAIL] PersistentLevel chain broken. Aborting init.\n");
		printf("=== INITIALIZATION FAILED - WILL RETRY ===\n\n");
		return;
	}

	// [3] Read OwningGameInstance
	printf("\n[3] Testing OwningGameInstance...\n");
	printf("  Offset: 0x%llX\n", OwningGameInstance);
	OwningGameInstance = TargetProcess.Read<uint64_t>(GWorld + OwningGameInstance);
	printf("  OwningGameInstance value: 0x%llX %s\n", OwningGameInstance,
		isHeapPtr(OwningGameInstance) ? "[OK]" : "[FAIL - invalid pointer!]");
	if (!isHeapPtr(OwningGameInstance)) {
		printf("  [FAIL] OwningGameInstance chain broken. Aborting init.\n");
		printf("=== INITIALIZATION FAILED - WILL RETRY ===\n\n");
		return;
	}

	// [4] Read LocalPlayers
	printf("\n[4] Testing LocalPlayers (TArray)...\n");
	printf("  Offset: 0x%llX\n", LocalPlayers);
	LocalPlayers = TargetProcess.Read<uint64_t>(OwningGameInstance + LocalPlayers);
	printf("  LocalPlayers TArray data ptr: 0x%llX %s\n", LocalPlayers,
		isHeapPtr(LocalPlayers) ? "[OK]" : "[FAIL - invalid!]");
	if (!isHeapPtr(LocalPlayers)) {
		printf("  [FAIL] LocalPlayers chain broken. Aborting init.\n");
		printf("=== INITIALIZATION FAILED - WILL RETRY ===\n\n");
		return;
	}

	// Dereference TArray[0] to get first ULocalPlayer
	uint64_t localplayer = TargetProcess.Read<uint64_t>(LocalPlayers);
	printf("  ULocalPlayer (deref): 0x%llX %s\n", localplayer,
		isHeapPtr(localplayer) ? "[OK]" : "[FAIL - NULL!]");
	if (!isHeapPtr(localplayer)) {
		printf("  [FAIL] ULocalPlayer chain broken. Player may not be spawned yet.\n");
		printf("=== INITIALIZATION FAILED - WILL RETRY ===\n\n");
		return;
	}
	LocalPlayers = localplayer;

	// [5] Read PlayerController
	printf("\n[5] Testing PlayerController...\n");
	printf("  Offset: 0x%llX\n", PlayerController);
	PlayerController = TargetProcess.Read<uint64_t>(LocalPlayers + PlayerController);
	printf("  PlayerController: 0x%llX %s\n", PlayerController,
		isHeapPtr(PlayerController) ? "[OK]" : "[FAIL - invalid!]");
	if (!isHeapPtr(PlayerController)) {
		printf("  [FAIL] PlayerController chain broken. Aborting init.\n");
		printf("=== INITIALIZATION FAILED - WILL RETRY ===\n\n");
		return;
	}

	// [6] Read AcknowledgedPawn
	printf("\n[6] Testing AcknowledgedPawn...\n");
	printf("  Offset: 0x%llX\n", AcknowledgedPawn);
	AcknowledgedPawn = TargetProcess.Read<uint64_t>(PlayerController + AcknowledgedPawn);
	printf("  AcknowledgedPawn: 0x%llX %s\n", AcknowledgedPawn,
		isHeapPtr(AcknowledgedPawn) ? "[OK]" : "[FAIL - invalid!]");
	if (!isHeapPtr(AcknowledgedPawn)) {
		printf("  [FAIL] AcknowledgedPawn chain broken. Player may not have spawned.\n");
		printf("=== INITIALIZATION FAILED - WILL RETRY ===\n\n");
		return;
	}

	// [7] Read PlayerState
	printf("\n[7] Testing PlayerState...\n");
	printf("  Offset: 0x%llX\n", PlayerState);
	PlayerState = TargetProcess.Read<uint64_t>(AcknowledgedPawn + PlayerState);
	printf("  PlayerState: 0x%llX %s\n", PlayerState,
		isHeapPtr(PlayerState) ? "[OK]" : "[FAIL - invalid!]");
	if (!isHeapPtr(PlayerState)) {
		printf("  [FAIL] PlayerState chain broken. Aborting init.\n");
		printf("=== INITIALIZATION FAILED - WILL RETRY ===\n\n");
		return;
	}

	// [8] Read CameraManager
	printf("\n[8] Testing CameraManager...\n");
	printf("  Offset: 0x%llX\n", CameraManager);
	CameraManager = TargetProcess.Read<uint64_t>(PlayerController + CameraManager);
	printf("  CameraManager: 0x%llX %s\n", CameraManager,
		isHeapPtr(CameraManager) ? "[OK]" : "[FAIL - invalid!]");
	if (!isHeapPtr(CameraManager)) {
		printf("  [WARN] CameraManager not found at offset 0x380. Scanning...\n");
		// Quick scan for CameraManager by looking for valid FOV
		for (uint64_t scan = 0x300; scan <= 0x500; scan += 0x8) {
			uint64_t val = TargetProcess.Read<uint64_t>(PlayerController + scan);
			if (isHeapPtr(val)) {
				CameraCacheEntry test_entry = TargetProcess.Read<CameraCacheEntry>(val + CameraCachePrivateOffset);
				if (test_entry.POV.FOV > 1.0f && test_entry.POV.FOV < 180.0f) {
					printf("  [+] Found CameraManager at +0x%llX = 0x%llX (FOV=%.2f)\n",
						scan, val, test_entry.POV.FOV);
					CameraManager = val;
					break;
				}
			}
		}
		if (!isHeapPtr(CameraManager)) {
			printf("  [FAIL] Could not find CameraManager. Aborting init.\n");
			printf("=== INITIALIZATION FAILED - WILL RETRY ===\n\n");
			return;
		}
	}

	// [9] Test CameraCacheEntry
	printf("\n[9] Testing CameraCacheEntry...\n");
	CameraEntry = TargetProcess.Read<CameraCacheEntry>(CameraManager + CameraCachePrivateOffset);
	printf("  FOV: %.2f %s\n", CameraEntry.POV.FOV,
		(CameraEntry.POV.FOV > 0 && CameraEntry.POV.FOV < 180) ? "[OK]" : "[WARN - unusual FOV!]");
	printf("  Location: (%.2f, %.2f, %.2f)\n",
		CameraEntry.POV.Location.X, CameraEntry.POV.Location.Y, CameraEntry.POV.Location.Z);
	printf("  Rotation: (%.2f, %.2f, %.2f)\n",
		CameraEntry.POV.Rotation.Pitch, CameraEntry.POV.Rotation.Yaw, CameraEntry.POV.Rotation.Roll);

	printf("\n=== INITIALIZATION COMPLETE - ALL POINTERS VALID ===\n\n");
}

std::string Engine::ResolveGName(const uint32_t& id)
{
	static int debug_count = 0;
	char name[256];
	memset(name, 0, sizeof(name));

	uintptr_t gname = TargetProcess.GetBaseAddress(ProcessName) + GName;

	// UE5 FNamePool: Blocks are stored directly in the structure (not via pointer array)
	// Calculate block and offset using bit shifting (UE5 method)
	uint32_t block = id >> 16;
	uint32_t offset = (uint16_t)id;

	// Read block pointer directly from GName structure
	uintptr_t namepool = TargetProcess.Read<uintptr_t>(gname + (block * 8));

	if (debug_count < 3) {
		printf("\n[DEBUG GName #%d] ID=%u (0x%X), Block=%u, Offset=%u\n", debug_count + 1, id, id, block, offset);
		printf("  GName base: 0x%llX\n", gname);
		printf("  Block[%u] ptr addr (gname+%llu): 0x%llX\n", block, block * 8, gname + (block * 8));
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
	printf("LocalPlayerTeamID: %d\n", templocalplayerteamid);


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

		// Read Class pointer (UObject::Class at +0x10)
		uint64_t class_ptr = entity->GetClass() ?
			TargetProcess.Read<uint64_t>(entity->GetClass() + 0x10) : 0;
		printf("  Class pointer (at +0x10): 0x%llX\n", class_ptr);
	}
	printf("=== END ACTOR VALIDATION ===\n\n");

	// ===========================================================================
	// CLASS POINTER DETECTION PHASE
	// Since GName may not work, identify soldiers by their Class pointer
	// ===========================================================================
	printf("\n=== CLASS POINTER ANALYSIS ===\n");
	std::map<uint64_t, int> class_counts;
	std::map<uint64_t, std::vector<std::shared_ptr<ActorEntity>>> class_entities;

	for (std::shared_ptr<ActorEntity> entity : actors)
	{
		if (!entity->GetClass())
			continue;

		// Read UObject::Class pointer (at offset +0x10)
		uint64_t class_ptr = TargetProcess.Read<uint64_t>(entity->GetClass() + 0x10);
		if (!class_ptr)
			continue;

		class_counts[class_ptr]++;
		class_entities[class_ptr].push_back(entity);
	}

	// Print class analysis
	printf("Found %zu unique class pointers:\n", class_counts.size());
	int class_rank = 0;
	for (auto& pair : class_counts)
	{
		class_rank++;
		printf("  [%d] Class 0x%llX: %d instances\n", class_rank, pair.first, pair.second);

		// For top 3 classes, show properties of first instance
		if (class_rank <= 3 && !class_entities[pair.first].empty())
		{
			auto sample = class_entities[pair.first][0];
			printf("      Sample: TeamID=%d, Health=%.2f, Pos=(%.1f,%.1f,%.1f)\n",
				sample->GetTeamID(), sample->GetHealth(),
				sample->GetPosition().x, sample->GetPosition().y, sample->GetPosition().z);
		}
	}

	// Identify soldier class: most common class with valid PlayerState, Health, and position
	uint64_t soldier_class_ptr = 0;
	int max_valid_count = 0;

	for (auto& pair : class_counts)
	{
		uint64_t class_ptr = pair.first;
		int valid_count = 0;

		for (auto& entity : class_entities[class_ptr])
		{
			Vector3 pos = entity->GetPosition();
			float health = entity->GetHealth();
			int team = entity->GetTeamID();

			bool valid_pos = !(pos.x == 0.0f && pos.y == 0.0f && pos.z == 0.0f);
			bool valid_health = health > 0.0f && health <= 100.0f;  // Squad max HP is 100
			bool valid_team = team >= 1 && team <= 2;               // Squad has exactly 2 teams (1 and 2)

			if (valid_pos && valid_health && valid_team)
				valid_count++;
		}

		if (valid_count > max_valid_count)
		{
			max_valid_count = valid_count;
			soldier_class_ptr = class_ptr;
		}
	}

	printf("\nIdentified Soldier Class: 0x%llX (%d valid soldiers)\n", soldier_class_ptr, max_valid_count);

	// Team breakdown for the identified class
	if (soldier_class_ptr && class_entities.count(soldier_class_ptr)) {
		int team1_count = 0, team2_count = 0, team_other_count = 0;
		for (auto& entity : class_entities[soldier_class_ptr]) {
			int t = entity->GetTeamID();
			if (t == 1) team1_count++;
			else if (t == 2) team2_count++;
			else team_other_count++;
		}
		printf("Team breakdown: Team1=%d, Team2=%d, Other=%d\n", team1_count, team2_count, team_other_count);
	}
	printf("=== END CLASS ANALYSIS ===\n\n");

	// ===========================================================================
	// BUILD PLAYER LIST using class pointer matching
	// ===========================================================================
	std::vector<std::shared_ptr<ActorEntity>> playerlist;

	if (soldier_class_ptr)
	{
		for (std::shared_ptr<ActorEntity> entity : actors)
		{
			if (!entity->GetClass())
				continue;

			// Read class pointer and match against soldier class
			uint64_t class_ptr = TargetProcess.Read<uint64_t>(entity->GetClass() + 0x10);
			if (class_ptr != soldier_class_ptr)
				continue;

			entity->SetUp2();
			Vector3 pos = entity->GetPosition();

			// Filter out zero positions
			if(pos.x == 0.0f && pos.y == 0.0f && pos.z == 0.0f)
				continue;

			// Filter out extreme/invalid positions (garbage memory reads)
			if (abs(pos.x) > 1000000.0f || abs(pos.y) > 1000000.0f || abs(pos.z) > 100000.0f)
				continue;

			printf("Soldier at (%.2f, %.2f, %.2f), Health: %.2f, Team: %d\n",
				pos.x, pos.y, pos.z, entity->GetHealth(), entity->GetTeamID());
			playerlist.push_back(entity);
		}
	}

	printf("Total soldiers added to ESP list: %d\n", (int)playerlist.size());


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
		if (pos.x == 0.0f && pos.y == 0.0f && pos.z == 0.0f)
			continue;
		if (abs(pos.x) > 1000000.0f || abs(pos.y) > 1000000.0f || abs(pos.z) > 100000.0f)
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
