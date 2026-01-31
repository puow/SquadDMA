# How to Find the REAL GWorld and GName Offsets

## Problem
GWorld is reading as `0x0000000000000000`, which means offset `0xCA49DE8` is WRONG.

---

## Method 1: Check Dumper-7 Text Files

### Step 1: Open GObjects-Dump.txt
Look at the **HEADER** of the file (first 50 lines), NOT the object list.

You're looking for lines like:
```
GNames: 0x0C788078
GObjects: 0x0CA49DE8
```
OR
```
NamePoolData: 0x...
GWorld: 0x...
```

### Step 2: Check for Metadata Section
Some Dumper-7 versions put offsets at the TOP of the dump file:
```
// Offsets
// GWorld: 0x...
// GNames: 0x...
```

---

## Method 2: Check ALL JSON/Config Files

Look in your Dumper-7 folder for:
- `Offsets.json`
- `config.json`
- `metadata.json`
- Any `.json` file

Open each one and look for **HEXADECIMAL** values, not decimal:
```json
{
  "GWorld": "0x0CA49DE8",
  "GNames": "0x0C788078"
}
```

**IMPORTANT**: If you find DECIMAL values like `212061544`, they might be:
- RVA (Relative Virtual Address) - needs different calculation
- File offset - wrong type
- Incorrect format

---

## Method 3: Use CheatEngine or Pattern Scanner

### Option A: CheatEngine
1. Attach to SquadGame.exe
2. Search for "Array of Bytes": `48 8B 05 ?? ?? ?? ?? 48 8B 88 ?? ?? ?? ?? 48 85 C9`
3. This finds the instruction that loads GWorld
4. Look at the instruction, it will be something like:
   ```asm
   mov rax, [SquadGame.exe+0xCA49DE8]
   ```
5. The offset after `exe+` is your GWorld offset

### Option B: x64dbg
1. Attach to SquadGame.exe
2. Search for pattern: `48 8B 05 ? ? ? ? 48 8B 88`
3. Find the RIP-relative address
4. Calculate offset from module base

---

## Method 4: Check SDK Generation Logs

Look for files in Dumper-7 output:
- `Dumper-7.log`
- `Generation.log`
- `offsets.txt`

These might contain the actual hex offsets:
```
[+] GWorld: 0x0CA49DE8
[+] GNames: 0x0C788078
```

---

## Method 5: Pattern Scan from Memory Dump

If you have access to the game's memory dump:

### GWorld Pattern (UE5):
```
48 8B 05 ? ? ? ? 48 8B 88 ? ? ? ? 48 85 C9 74 ? 48 8B 01
```

### GNames Pattern (UE5):
```
48 8D 0D ? ? ? ? E8 ? ? ? ? C6 05 ? ? ? ? ? 0F
```

When you find the pattern, extract the **RIP-relative offset** and add it to the instruction address.

---

## What to Look For

### ❌ WRONG Format (These won't work):
```json
["OFFSET_GWORLD", 212061544]  // Decimal - might be wrong type!
```
```
[000012BA] {0x7ff4de062000} Class PCG.PCGWorldActor  // Class instance, not GWorld!
```

### ✅ RIGHT Format:
```
GWorld: 0x0CA49DE8
```
OR instruction in disassembly:
```asm
mov rax, qword ptr [SquadGame.exe+CA49DE8]
```

---

## Debug: Calculate What Address It's Reading

Your debug output shows:
- Base: `0x00007FF6263E0000`
- Current GWorld offset: `0xCA49DE8`
- Reading from: `0x00007FF6263E0000 + 0xCA49DE8 = 0x00007FF7331C9DE8`
- Value there: `0x0000000000000000` ❌

If you find a different offset, calculate:
```
0x00007FF6263E0000 + [YOUR_OFFSET] = Address to check in memory
```

Then use CheatEngine to check if that address contains a valid pointer (should start with 0x00007FF...)

---

## Quick Test

The GWorld offset for Squad UE4 was `0x72aa2e0`.

For UE5, it should be:
- Higher (more code = higher offset)
- In the `.data` section (static data)
- Typically between `0x5000000` - `0x15000000`

If your offset is `0xCA49DE8` (202MB), that seems **TOO HIGH** and might be wrong.

Expected range: **0x5000000 to 0x10000000** for most UE5 games.

---

## What to Do Next

1. **Check the Dumper-7 folder for ANY file containing hex offsets**
2. **Look at the header of GObjects-Dump.txt**
3. **Search for "GWorld" or "GUObjectArray" in ALL text files**
4. **Use CheatEngine to find the pattern and get the real offset**
5. **Paste here what you find**

The offset `0xCA49DE8` is likely INCORRECT. We need to find the real one.
