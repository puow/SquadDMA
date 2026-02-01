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
	// UE5 FName Resolution
	static int debug_count = 0;
	char name[256];

	// FNamePool base address
	uintptr_t gname = TargetProcess.GetBaseAddress(ProcessName) + GName;

	bool should_debug = (debug_count < 3);

	// Debug: Dump first 128 bytes of FNamePool structure to understand layout
	if(should_debug) {
		printf("\nDEBUG UE5 GName Resolution #%d:\n", debug_count + 1);
		printf("  Base Address: 0x%llX\n", TargetProcess.GetBaseAddress(ProcessName));
		printf("  GName Offset: 0x%llX\n", GName);
		printf("  GName Address: 0x%llX\n", gname);
		printf("  ID to resolve: %u (0x%X)\n", id, id);

		printf("\n  FNamePool Structure Dump (first 128 bytes):\n");
		for(int i = 0; i < 16; i++) {
			uint64_t value = TargetProcess.Read<uint64_t>(gname + (i * 8));
			printf("    +0x%02X: 0x%016llX\n", i * 8, value);
		}
	}

	// Try different possible offsets for Blocks pointer
	uintptr_t blocks_ptr_0x00 = TargetProcess.Read<uintptr_t>(gname + 0x00);
	uintptr_t blocks_ptr_0x08 = TargetProcess.Read<uintptr_t>(gname + 0x08);
	uintptr_t blocks_ptr_0x10 = TargetProcess.Read<uintptr_t>(gname + 0x10);
	uintptr_t blocks_ptr_0x18 = TargetProcess.Read<uintptr_t>(gname + 0x18);
	uintptr_t blocks_ptr_0x20 = TargetProcess.Read<uintptr_t>(gname + 0x20);

	if(should_debug) {
		printf("\n  Trying different Blocks offsets:\n");
		printf("    +0x00: 0x%llX\n", blocks_ptr_0x00);
		printf("    +0x08: 0x%llX\n", blocks_ptr_0x08);
		printf("    +0x10: 0x%llX\n", blocks_ptr_0x10);
		printf("    +0x18: 0x%llX\n", blocks_ptr_0x18);
		printf("    +0x20: 0x%llX\n", blocks_ptr_0x20);
	}

	debug_count++;
	return LIT("");  // Return empty for now while debugging structure
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
		if(pos == Vector3::Zero())
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
	ActorMutex.lock();
	Actors = tempactors;
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
