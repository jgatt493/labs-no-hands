# Cleanup Analysis - What Can Be Removed/Refactored

## Current Redundancies

### 1. Mode-Specific Command Matching (REMOVABLE)

**Current Code in `parser.py`:**
```python
self.mode_commands = {
    "dictation": {
        "enter": ["send"],
        "return": ["send"],
        "stop dictation": ["stop_dictation"],
        # ...
    },
    "manual": {
        "left": ["move_left"],
        "right": ["move_right"],
        # ...
    },
}

def _try_mode_match(self, transcript_clean: str, mode: str) -> Optional[...]:
    # 30 lines of repetitive matching logic
```

**Why Removable:**
- `app_state.mode` now tracks the mode
- Mode commands can just check if they have mode-specific triggers
- Can be handled via simple flag in parse() instead

**What to Replace With:**
```python
# Instead of mode_commands dict, just check:
if self.app_state.mode in ("dictation", "manual"):
    match = self._find_strict_command(transcript_clean)
    if match:
        return match
    else:
        return None  # Ignore everything else in special modes
```

---

### 2. Redundant Command Definitions in YAML (REMOVABLE)

**Current YAML has BOTH:**

1. Old individual commands:
```yaml
- id: "start_dictation"
  triggers: ["start dictation", "dictate"]
  action: mode
  mode: dictation
  feedback: "Starting dictation mode"

- id: "stop_dictation"
  triggers: ["stop dictation"]
  action: mode
  mode: normal
  feedback: "Stopping dictation mode"

- id: "start_manual_mode"
  triggers: ["start manual mode", "manual mode"]
  action: mode
  mode: manual
  
- id: "stop_manual_mode"
  triggers: ["stop manual mode", "done"]
  action: mode
  mode: normal
```

2. New context commands:
```yaml
- id: "context_start_mode"
  action: "context_mode"
  primary_trigger: "start"
  modes:
    dictation: { triggers: [...], ... }
    manual: { triggers: [...], ... }

- id: "context_stop_mode"
  action: "context_mode"
  primary_trigger: "stop"
  modes:
    dictation: { triggers: [...], ... }
    manual: { triggers: [...], ... }
```

**Issue:** Both approaches work, but old commands will be matched by semantic matching and are now redundant.

**Solution:** Remove the old individual commands, keep only context versions.

---

### 3. Redundant App Launch Commands (REMOVABLE)

**Current YAML has BOTH:**

1. Old commands:
```yaml
- id: "open_terminal"
  triggers: ["open terminal", "terminal"]
  action: launch
  app: "Terminal"

- id: "open_chrome"
  triggers: ["open chrome", "chrome", "browser"]
  action: launch
  app: "Google Chrome"
```

2. New context command:
```yaml
- id: "context_open_app"
  action: "context_open"
  primary_trigger: "open"
  apps:
    cursor: { triggers: ["cursor", "ide"], ... }
    chrome: { triggers: ["chrome", "browser"], ... }
    terminal: { triggers: ["terminal"], ... }
```

**Issue:** Old commands will still match via semantic/fuzzy matching.

**Solution:** Remove old individual launch commands, keep only context version.

---

### 4. Unused Variables (REMOVABLE)

**In `parser.py`:**
```python
self.triggers_map = config.get_all_triggers()  # Built but never used!
```

**Used for:**
- Nothing currently - semantic/fuzzy matching use other approaches

**Solution:** Remove the line and the `get_all_triggers()` call

---

### 5. Interim Matching (POTENTIALLY REMOVABLE)

**In `parser.py`:**
```python
def parse_interim(self, transcript: str) -> Optional[Tuple[CommandAction, float]]:
    """Parse interim results (shows potential matches)"""
    # Complex logic that's not used in current flow
```

**Used in:**
```python
# main.py
match = self.parser.parse_interim(result.transcript)
# Logged but doesn't execute anything
```

**Status:** Could remove if interim feedback isn't needed. Currently just for logging.

---

## Cleanup Priority

### HIGH PRIORITY (Major Simplification)

1. **Remove `mode_commands` dict and `_try_mode_match()` method**
   - ~50 lines reduced
   - Simpler mode handling via app_state
   - Impact: Medium complexity reduction

2. **Remove old mode commands from YAML**
   - start_dictation, stop_dictation, start_manual_mode, stop_manual_mode
   - Keep context versions only
   - Impact: ~40 lines reduced, cleaner YAML

3. **Remove old app launch commands from YAML**
   - open_terminal, open_chrome, etc.
   - Keep context_open_app only
   - Impact: ~80 lines reduced, cleaner YAML

### MEDIUM PRIORITY (Code Quality)

4. **Remove unused `self.triggers_map`**
   - 1 line removed
   - Cleaner init

5. **Simplify parse() method**
   - Remove mode-specific logic blocks
   - Let context/semantic/fuzzy handle everything
   - Add simple app_state check at start
   - Impact: Cleaner, more maintainable code

### LOW PRIORITY (Polish)

6. **Remove interim matching or integrate properly**
   - Optional - only if not needed for UX

---

## Files to Modify

1. **src/commands/parser.py**
   - Remove: `mode_commands` dict
   - Remove: `_try_mode_match()` method
   - Simplify: `parse()` method
   - Remove: `triggers_map` initialization
   - Remove: `parse_interim()` if not needed

2. **config/commands.yaml**
   - Remove: start_dictation, stop_dictation
   - Remove: start_manual_mode, stop_manual_mode
   - Remove: open_terminal, open_chrome
   - (and other old app launch commands)

3. **Optional: src/main.py**
   - Could simplify parsing flow

---

## Before/After Comparison

### BEFORE (Current)
```
parser.py: 249 lines
  - ContextAwareParser: ~50 lines
  - CommandParser: ~199 lines
    - mode_commands dict: ~20 lines
    - _try_mode_match: ~30 lines
    - parse: ~70 lines (with mode handling)
    - parse_interim: ~40 lines
    - semantic/fuzzy: ~40 lines

commands.yaml: 700 lines
  - Individual mode commands: ~40 lines
  - Individual app launch: ~50 lines
  - Context commands: ~45 lines
```

### AFTER (Proposed)
```
parser.py: ~180 lines (-69)
  - ContextAwareParser: ~50 lines (stays)
  - CommandParser: ~130 lines (-69)
    - No mode_commands dict
    - No _try_mode_match
    - parse: ~40 lines (simpler)
    - parse_interim: (removed if not needed)
    - semantic/fuzzy: ~40 lines

commands.yaml: ~620 lines (-80)
  - No individual mode commands
  - No individual app launch
  - Context commands: ~45 lines (stays)
```

---

## Implementation Order

1. Update YAML first (remove old commands)
2. Simplify parser.py (remove mode handling)
3. Test everything still works
4. Remove parse_interim if safe
5. Update documentation

---

## Risk Assessment

**Low Risk:**
- Removing old YAML commands (context versions handle everything)
- Removing unused triggers_map

**Medium Risk:**
- Removing mode_commands dict and _try_mode_match (need to ensure mode filtering still works)
- Simplifying parse method (need careful testing)

**High Risk:**
- None identified if done correctly

---

## Testing Needed

After cleanup, verify:
- ✓ "start dictation" → enters dictation mode
- ✓ "enter" in dictation → only matches send command
- ✓ "stop dictation" → exits dictation mode
- ✓ "open chrome" → launches Chrome
- ✓ "open music" → launches Spotify
- ✓ Normal commands still match
- ✓ Dictation mode still types unmatched text
- ✓ Manual mode still works

