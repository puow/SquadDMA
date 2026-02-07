#include "Pch.h"
#include "Engine.h"
#include "ActorEntity.h"
#include "Globals.h"

Engine::Engine()
{
	GWorld = TargetProcess.Read<uint64_t>(TargetProcess.GetBaseAddress(ProcessName) + GWorld);
	printf(LIT("GWorld: %p\n"), GWorld);
	PersistentLevel = TargetProcess.Read<uint64_t>(GWorld + PersistentLevel);
	printf(LIT("PersistentLevel: %p\n"), PersistentLevel);
	OwningGameInstance = TargetProcess.Read<uint64_t>(GWorld + OwningGameInstance);
	printf(LIT("OwningGameInstance: %p\n"), OwningGameInstance);
	LocalPlayers = TargetProcess.Read<uint64_t>(OwningGameInstance + LocalPlayers);
	printf(LIT("LocalPlayers: %p\n"), LocalPlayers);
	LocalPlayers = TargetProcess.Read<uint64_t>(LocalPlayers);
	printf(LIT("LocalPlayers: %p\n"), LocalPlayers);
	PlayerController = TargetProcess.Read<uint64_t>(LocalPlayers + PlayerController);
	printf(LIT("PlayerController: %p\n"), PlayerController);
	AcknowledgedPawn = TargetProcess.Read<uint64_t>(PlayerController + AcknowledgedPawn);
	printf(LIT("AcknowledgedPawn: %p\n"), AcknowledgedPawn);
	PlayerState = TargetProcess.Read<uint64_t>(AcknowledgedPawn + PlayerState);
	printf(LIT("PlayerState: %p\n"), PlayerState);
	CameraManager = TargetProcess.Read<uint64_t>(PlayerController + CameraManager);
	printf(LIT("CameraManager: %p\n"), CameraManager);
	CameraEntry = TargetProcess.Read<CameraCacheEntry>(CameraManager + CameraCachePrivateOffset);
	printf(LIT("CameraCacheEntry: %p\n"), CameraEntry);

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
