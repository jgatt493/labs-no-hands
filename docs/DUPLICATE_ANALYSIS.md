# Duplicate Commands Analysis - Cursor Specific

## Summary

Found **duplicate commands** between global `commands.yaml` and `app_commands/cursor.yaml`.

These duplicates create **ambiguity and potential matching conflicts**:
- When app=Cursor, both might match
- Priority confusion (which one executes?)
- Inconsistent behavior

---

## Duplicates Found

### 1. ⚠️ EXACT DUPLICATE: cursor_chat / cursor_ask_ai

**Global (`commands.yaml` line 332):**
```yaml
- id: "cursor_chat"
  triggers:
    - "chat"
    - "cursor chat"
    - "ask cursor"
    - "open chat"
  action: keystroke
  keys: ["cmd", "k"]
  feedback: "Opening Cursor chat"
```

**App-Specific (`app_commands/cursor.yaml` line 84):**
```yaml
- id: "cursor_ask_ai"
  triggers:
    - "ask cursor"
    - "ask ai"
    - "cursor help"
    - "ask"
  action: keystroke
  keys: ["cmd", "k"]
  feedback: "Opening Cursor chat"
```

**Problem:** 
- "ask cursor" appears in BOTH
- Same action (cmd+k)
- When app=Cursor, parser loads app config BUT global also matches!
- **Result:** Unpredictable which one executes

**Triggers in Common:**
- "ask cursor" ← DUPLICATE!

---

### 2. ⚠️ EXACT DUPLICATE: cursor_edit

**Global (`commands.yaml` line 342):**
```yaml
- id: "cursor_edit"
  triggers:
    - "edit"
    - "cursor edit"
    - "inline edit"
  action: keystroke
  keys: ["cmd", "i"]
  feedback: "Opening cursor edit"
```

**App-Specific (`app_commands/cursor.yaml` line 62):**
```yaml
- id: "cursor_inline_edit"
  triggers:
    - "edit"
    - "inline edit"
    - "cursor edit"
    - "edit here"
  action: keystroke
  keys: ["cmd", "i"]
  feedback: "Opening inline edit"
```

**Problem:**
- All 3 common triggers in BOTH
- Same action (cmd+i)
- **Triggers in Common:**
  - "edit"
  - "cursor edit"
  - "inline edit"

---

### 3. ⚠️ EXACT DUPLICATE: cursor_composer

**Global (`commands.yaml` line 351):**
```yaml
- id: "cursor_composer"
  triggers:
    - "composer"
    - "multi edit"
    - "open composer"
  action: keystroke
  keys: ["cmd", "shift", "l"]
  feedback: "Opening Cursor composer"
```

**App-Specific (`app_commands/cursor.yaml` line 73):**
```yaml
- id: "cursor_composer"
  triggers:
    - "composer"
    - "multi edit"
    - "open composer"
    - "cursor composer"
  action: keystroke
  keys: ["cmd", "shift", "l"]
  feedback: "Opening composer"
```

**Problem:**
- ALL 3 common triggers in BOTH
- Same action (cmd+shift+l)
- Identical ID
- **Triggers in Common:**
  - "composer"
  - "multi edit"
  - "open composer"

---

### 4. ⚠️ POTENTIAL CONFLICT: toggle_terminal

**Global (`commands.yaml` line 181):**
```yaml
- id: "toggle_terminal"
  triggers:
    - "toggle terminal"
    - "show terminal"
    - "hide terminal"
    - "terminal toggle"
  action: keystroke
  keys: ["cmd", "j"]
  feedback: "Toggling terminal"
```

**App-Specific (`app_commands/cursor.yaml` line 38):**
```yaml
- id: "toggle_terminal_cursor"
  triggers:
    - "toggle terminal"
    - "terminal toggle"
    - "show terminal"
    - "hide terminal"
  action: keystroke
  keys: ["cmd", "j"]
  feedback: "Toggling integrated terminal"
```

**Problem:**
- Same triggers!
- Same action (cmd+j)
- When app=Cursor, both could match
- **Triggers in Common:**
  - "toggle terminal"
  - "terminal toggle"
  - "show terminal"
  - "hide terminal"

**Note:** Global version is generic (works in any app). App version is Cursor-specific.
This is intentional but DOES create conflict.

---

## Recommended Solution

### Option A: REMOVE FROM GLOBAL (Recommended)

**Rationale:**
- Cursor-specific commands belong in app config
- Global should only have truly global commands
- App config is loaded FIRST in parse flow, so it wins anyway

**Actions:**
1. Delete from `commands.yaml`:
   - `cursor_chat` (line 332)
   - `cursor_edit` (line 342)
   - `cursor_composer` (line 351)
   - `toggle_terminal` (line 181) ← Only if it's Cursor-specific

2. Keep in `app_commands/cursor.yaml`:
   - All Cursor-specific commands stay

3. Result: No conflicts, cleaner separation

---

### Option B: KEEP GLOBAL (Backup)

**Rationale:**
- Global commands work when NOT in Cursor mode
- If user doesn't have app context, commands still available
- "edit" command could work in Terminal too

**Risk:**
- Defeats the purpose of app-specific commands
- Creates ambiguity

**Not Recommended**

---

## Analysis of Each Command

| Command | Global | App | Recommendation | Reason |
|---------|--------|-----|-----------------|--------|
| cursor_chat | ✅ | ✅ | Remove from global | Cursor-specific |
| cursor_edit | ✅ | ✅ | Remove from global | Cursor-specific |
| cursor_composer | ✅ | ✅ | Remove from global | Cursor-specific |
| toggle_terminal | ✅ | ✅ | Remove from global | Cursor-specific |
| go_to_file | ❌ | ✅ | Keep in app | Cursor-only |
| command_palette | ❌ | ✅ | Keep in app | Cursor-only |
| format_code | ❌ | ✅ | Keep in app | Cursor-only |
| quick_fix | ❌ | ✅ | Keep in app | Cursor-only |
| etc. | ❌ | ✅ | Keep in app | Cursor-only |

---

## Commands to Delete from Global

**File:** `config/commands.yaml`

Lines to delete:
- **181-189**: `toggle_terminal` command
- **332-340**: `cursor_chat` command
- **342-349**: `cursor_edit` command
- **351-358**: `cursor_composer` command

**Total:** 32 lines to remove

---

## Impact Analysis

### Before Cleanup
- Global has 62 commands
- Cursor app has 18 commands
- **4 commands duplicated**
- Parser has to disambiguate when app=Cursor

### After Cleanup
- Global has 58 commands (62 - 4 duplicates)
- Cursor app has 18 commands
- **0 duplicates**
- Clear separation of concerns
- Parser behavior is deterministic

---

## Parsing Behavior Comparison

### BEFORE (With Duplicates)

```
User: "edit" (app=Cursor)
  ↓
1. Context parsing → No match
  ↓
2. App-specific parsing (Cursor)
   - Load cursor.yaml
   - Find: cursor_inline_edit (trigger: "edit")
   - Match score: 1.00
   ↓
3. Return: cursor_inline_edit ✓

BUT THEN:
4. If parser didn't find in app, falls through to global
5. Global has: cursor_edit (trigger: "edit")
6. Would also match!

⚠️ CONFLICT: Which one wins?
```

### AFTER (Cleaned Up)

```
User: "edit" (app=Cursor)
  ↓
1. Context parsing → No match
  ↓
2. App-specific parsing (Cursor)
   - Load cursor.yaml
   - Find: cursor_inline_edit (trigger: "edit")
   - Match score: 1.00
   - Return immediately ✓
   ↓
3. No fallback needed
4. Deterministic behavior ✓
```

---

## Recommendation

✅ **EXECUTE OPTION A:**

Remove these commands from `commands.yaml`:
1. `toggle_terminal` (lines 181-189)
2. `cursor_chat` (lines 332-340)
3. `cursor_edit` (lines 342-349)
4. `cursor_composer` (lines 351-358)

**Benefits:**
- Clean separation (global vs app-specific)
- No conflicts or ambiguity
- Parser behavior is predictable
- Smaller global command set
- Better performance (fewer global commands to search)

**Risks:**
- None identified
- App config has all necessary commands
- Global fallback available if needed

---

## Action Items

- [ ] Review and approve this analysis
- [ ] Delete 4 duplicate commands from commands.yaml
- [ ] Test that Cursor commands still work
- [ ] Verify no other app-specific commands in global
- [ ] Document the cleaning
- [ ] Consider: Should we scan Terminal/Chrome/Slack similarly?


