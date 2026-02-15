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

	// If CameraManager is NULL, scan nearby offsets to find it
	if (!CameraManager) {
		printf("\n  [!] CameraManager NULL at 0x328 - scanning PlayerController memory...\n");
		printf("  PlayerController base: 0x%llX\n", PlayerController);

		// Dump raw memory from 0x300 to 0x400 to find the CameraManager pointer
		printf("\n  === MEMORY DUMP: PlayerController + 0x300 to 0x400 ===\n");
		for (uint64_t scan_offset = 0x300; scan_offset <= 0x400; scan_offset += 0x8) {
			uint64_t val = TargetProcess.Read<uint64_t>(PlayerController + scan_offset);
			if (val != 0) {
				printf("  +0x%03llX: 0x%llX", scan_offset, val);

				// Check if this looks like a valid UObject pointer (heap address range)
				// Valid pointers are typically > 0x10000 and < 0x7FFFFFFFFFFF
				if (val > 0x10000 && val < 0x7FFFFFFFFFFF) {
					// Try reading its class pointer (UObject::ClassPrivate at +0x10)
					uint64_t maybe_class = TargetProcess.Read<uint64_t>(val + 0x10);
					if (maybe_class > 0x10000 && maybe_class < 0x7FFFFFFFFFFF) {
						// Try to read CameraCacheEntry from this potential CameraManager
						CameraCacheEntry test_entry = TargetProcess.Read<CameraCacheEntry>(val + CameraCachePrivateOffset);
						if (test_entry.POV.FOV > 1.0f && test_entry.POV.FOV < 180.0f) {
							printf(" <-- LIKELY CAMERA MANAGER! FOV=%.2f, Loc=(%.1f,%.1f,%.1f)",
								test_entry.POV.FOV,
								test_entry.POV.Location.X, test_entry.POV.Location.Y, test_entry.POV.Location.Z);
							CameraManager = val;
						} else {
							printf(" [UObject, class=0x%llX]", maybe_class);
						}
					}
				}
				printf("\n");
			}
		}

		if (CameraManager) {
			printf("\n  [+] Found CameraManager at offset +0x???  -> 0x%llX\n", CameraManager);
		} else {
			printf("\n  [!] Could not find CameraManager in range 0x300-0x400\n");
			printf("  Expanding search to 0x200-0x600...\n");
			for (uint64_t scan_offset = 0x200; scan_offset <= 0x600; scan_offset += 0x8) {
				uint64_t val = TargetProcess.Read<uint64_t>(PlayerController + scan_offset);
				if (val > 0x10000 && val < 0x7FFFFFFFFFFF) {
					uint64_t maybe_class = TargetProcess.Read<uint64_t>(val + 0x10);
					if (maybe_class > 0x10000 && maybe_class < 0x7FFFFFFFFFFF) {
						CameraCacheEntry test_entry = TargetProcess.Read<CameraCacheEntry>(val + CameraCachePrivateOffset);
						if (test_entry.POV.FOV > 1.0f && test_entry.POV.FOV < 180.0f) {
							printf("  +0x%03llX: 0x%llX <-- CAMERA MANAGER FOUND! FOV=%.2f\n",
								scan_offset, val, test_entry.POV.FOV);
							CameraManager = val;
							break;
						}
					}
				}
			}
		}
	}

	// Test CameraCacheEntry
	printf("\n[9] Testing CameraCacheEntry...\n");
	printf("  Offset: 0x%llX\n", CameraCachePrivateOffset);
	printf("  Reading from: 0x%llX\n", CameraManager + CameraCachePrivateOffset);
	CameraEntry = TargetProcess.Read<CameraCacheEntry>(CameraManager + CameraCachePrivateOffset);
	printf("  CameraCacheEntry FOV: %.2f %s\n", CameraEntry.POV.FOV,
		(CameraEntry.POV.FOV > 0 && CameraEntry.POV.FOV < 180) ? "[OK]" : "[WARN - unusual FOV!]");
	printf("  Camera Location: (%.2f, %.2f, %.2f)\n",
		CameraEntry.POV.Location.X, CameraEntry.POV.Location.Y, CameraEntry.POV.Location.Z);
	printf("  Camera Rotation: (%.2f, %.2f, %.2f)\n",
		CameraEntry.POV.Rotation.Pitch, CameraEntry.POV.Rotation.Yaw, CameraEntry.POV.Rotation.Roll);

	// Test GObjects (FUObjectArray)
	printf("\n[10] Testing GObjects (FUObjectArray)...\n");
	printf("  GObjects offset: 0x%llX\n", GObjects);
	uintptr_t gobjects_addr = TargetProcess.GetBaseAddress(ProcessName) + GObjects;
	printf("  GObjects address: 0x%llX\n", gobjects_addr);

	// FUObjectArray structure (UE5):
	// +0x00: TArray ObjObjects (pointer to object array)
	// +0x08: int32 MaxElements
	// +0x0C: int32 NumElements
	uintptr_t objects_array = TargetProcess.Read<uintptr_t>(gobjects_addr);
	int32_t max_elements = TargetProcess.Read<int32_t>(gobjects_addr + 0x8);
	int32_t num_elements = TargetProcess.Read<int32_t>(gobjects_addr + 0xC);

	printf("  Objects array ptr: 0x%llX %s\n", objects_array, objects_array ? "[OK]" : "[FAIL - NULL!]");
	printf("  MaxElements: %d\n", max_elements);
	printf("  NumElements: %d %s\n", num_elements,
		(num_elements > 0 && num_elements < 500000) ? "[OK]" : "[WARN - unusual count!]");

	// Test reading first few object entries
	if (objects_array && num_elements > 0 && num_elements < 500000) {
		printf("  Testing first 5 objects:\n");
		for (int i = 0; i < 5 && i < num_elements; i++) {
			// Each FUObjectItem is typically 24 bytes (0x18)
			// +0x00: UObject* Object
			// +0x08: int32 Flags
			// +0x0C: int32 ClusterRootIndex
			// +0x10: int32 SerialNumber
			uintptr_t item_addr = objects_array + (i * 0x18);
			uintptr_t object_ptr = TargetProcess.Read<uintptr_t>(item_addr);
			int32_t flags = TargetProcess.Read<int32_t>(item_addr + 0x8);

			printf("    [%d] Object: 0x%llX, Flags: 0x%X\n", i, object_ptr, flags);

			// If object is valid, try to read its Class pointer
			if (object_ptr) {
				// UObject::Class is typically at +0x10 in UE5
				uintptr_t class_ptr = TargetProcess.Read<uintptr_t>(object_ptr + 0x10);
				printf("         Class: 0x%llX\n", class_ptr);
			}
		}
	}

	printf("\n[11] GName Status (FNamePool)...\n");
	printf("  GName offset: 0x%llX\n", GName);
	uintptr_t gname_addr = TargetProcess.GetBaseAddress(ProcessName) + GName;
	uintptr_t gname_value = TargetProcess.Read<uintptr_t>(gname_addr);
	printf("  GName value: 0x%llX %s\n", gname_value,
		gname_value ? "[Available]" : "[NULL - Will use class pointer matching instead]");

	printf("\n=== INITIALIZATION COMPLETE ===\n\n");
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
			bool valid_health = health > 0.0f && health <= 200.0f;
			bool valid_team = team >= 0 && team <= 10;

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
