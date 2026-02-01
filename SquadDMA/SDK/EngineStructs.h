#pragma once
// ScriptStruct CoreUObject.Vector
// UE5 uses double precision for FVector (24 bytes total)
struct UEVector {
	double X; // 8 bytes (UE5 changed from float to double)
	double Y; // 8 bytes
	double Z; // 8 bytes
}; // Total: 24 bytes (0x18) in UE5
// ScriptStruct CoreUObject.Rotator
struct UERotator {
	float Pitch;
	float Yaw;
	float Roll;
};
struct MinimalViewInfo
{
	struct UEVector Location; // 0x0(0x18) - UE5: 24 bytes (double precision)
	struct UERotator Rotation; // 0x18(0xc) - 12 bytes
	float FOV; // 0x24(0x4) - 4 bytes
};
struct CameraCacheEntry
{
	float Timestamp; // 0x00(0x04)
	char pad_4[0xc]; // 0x04(0x0c)
	MinimalViewInfo POV; // 0x10(0x5e0)
};