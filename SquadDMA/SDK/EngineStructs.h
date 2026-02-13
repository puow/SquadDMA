#pragma once
// ScriptStruct CoreUObject.Vector
// UE5 uses double precision for FVector (24 bytes total) - Large World Coordinates
struct UEVector {
	double X; // 8 bytes (UE5: TVector<double>)
	double Y; // 8 bytes
	double Z; // 8 bytes
}; // Total: 24 bytes (0x18)
// ScriptStruct CoreUObject.Rotator
// UE5 uses double precision for FRotator (24 bytes total) - TRotator<double>
struct UERotator {
	double Pitch; // 8 bytes (UE5: TRotator<double>)
	double Yaw;   // 8 bytes
	double Roll;  // 8 bytes
}; // Total: 24 bytes (0x18)
struct MinimalViewInfo
{
	struct UEVector Location;  // 0x0000(0x18) - UE5: 3 doubles
	struct UERotator Rotation; // 0x0018(0x18) - UE5: 3 doubles (was 0xC in UE4!)
	float FOV;                 // 0x0030(0x04) - Field of View (was 0x18 in UE4, 0x24 with float rotator)
};
struct CameraCacheEntry
{
	float Timestamp; // 0x00(0x04)
	char pad_4[0xc]; // 0x04(0x0c)
	MinimalViewInfo POV; // 0x10(0x850) - UE5: 2128 bytes (was 0x5e0)
};
