# Cleanup Opportunities Summary

## Quick Overview

We can eliminate ~100 lines of redundant code now that we have proper state management and context-aware parsing.

```
BEFORE → AFTER CLEANUP

parser.py          249 lines → 180 lines (-69 lines, -27%)
commands.yaml      700 lines → 620 lines (-80 lines, -11%)
TOTAL              949 lines → 800 lines (-149 lines, -15%)

Code Quality: ⭐⭐⭐ → ⭐⭐⭐⭐⭐
Maintainability: High → Very High
Redundancy: High → None
```

---

## What's Redundant?

### 1. Mode Commands Dictionary (🔴 HIGH PRIORITY)

**Current State:**
```python
# parser.py - 20 lines wasted
self.mode_commands = {
    "dictation": {
        "enter": ["send"],
        "stop dictation": ["stop_dictation"],
        # ...
    },
    "manual": {
        "left": ["move_left"],
        # ...
    },
}

def _try_mode_match(self, ...):  # 16 lines of logic
    # Lookup in mode_commands dict
    # Return command if found
```

**Why It's Redundant:**
- `app_state.mode` already tracks mode
- Context commands handle start/stop/enter/etc
- Can just filter commands by mode in YAML

**After Cleanup:**
```python
# Gone! No mode_commands dict needed
# No _try_mode_match method
# Mode filtering happens via context groups and triggers
```

---

### 2. Duplicate Commands in YAML (🔴 HIGH PRIORITY)

**Current State:**
```yaml
# Individual mode commands (40 lines)
- id: "start_dictation"
  triggers: ["start dictation"]
  action: mode
  mode: dictation

- id: "stop_dictation"
  triggers: ["stop dictation"]
  action: mode
  mode: normal

# PLUS context commands (45 lines) doing the same thing
- id: "context_start_mode"
  action: "context_mode"
  primary_trigger: "start"
  modes:
    dictation: { triggers: ["dictation"], ... }
    
- id: "context_stop_mode"
  action: "context_mode"
  primary_trigger: "stop"
  modes:
    dictation: { triggers: ["dictation"], ... }
```

**Why It's Redundant:**
- Both achieve same result
- Old commands get matched by semantic/fuzzy anyway
- Context versions are cleaner and scalable

**After Cleanup:**
```yaml
# Keep ONLY context commands
# Old individual commands deleted
```

---

### 3. Old App Launch Commands (🔴 HIGH PRIORITY)

**Current State:**
```yaml
# Individual app commands (50 lines)
- id: "open_terminal"
  triggers: ["open terminal", "terminal"]
  action: launch
  app: "Terminal"

- id: "open_chrome"
  triggers: ["open chrome", "chrome", "browser"]
  action: launch
  app: "Google Chrome"

# PLUS context commands (45 lines) doing the same thing
- id: "context_open_app"
  action: "context_open"
  primary_trigger: "open"
  apps:
    terminal: { triggers: ["terminal"], ... }
    chrome: { triggers: ["chrome"], ... }
```

**Why It's Redundant:**
- Context version handles all variations
- Old commands just add bloat
- Context is extensible

**After Cleanup:**
```yaml
# Keep ONLY context_open_app
# Old open_terminal, open_chrome deleted
```

---

### 4. Unused Variables (🟡 MEDIUM PRIORITY)

**Current State:**
```python
# parser.py line 116
self.triggers_map = config.get_all_triggers()
```

**Why It's Unused:**
- Built but never referenced
- Semantic/fuzzy matching use trigger embeddings instead
- Just wasting memory

**After Cleanup:**
```python
# Deleted - 1 line saved
```

---

### 5. Overly Complex parse() Method (🔴 HIGH PRIORITY)

**Current State:**
```python
# ~130 lines of complex logic with mode handling
def parse(self, transcript):
    if not transcript:
        return None
    
    # 25 lines of mode checking
    if mode == "dictation":
        if transcript_clean == "enter":
            # Find and return
        elif transcript_clean == "stop dictation":
            # Find and return
        return None  # Ignore everything else
    
    # 25 lines of manual mode checking
    if mode == "manual":
        if transcript_clean == "left":
            # Find and return
        # ... many more elif statements
        return None
    
    # 80 lines of semantic/fuzzy matching
    # ...
```

**Why It's Overcomplicated:**
- Mode handling is now via app_state + context commands
- Could be simplified to just try context → semantic → fuzzy
- Easier to understand and maintain

**After Cleanup:**
```python
# ~80 lines, much simpler
def parse(self, transcript):
    if not transcript:
        return None
    
    # Try context parsing (handles keywords + modes via context)
    context_result = self.context_parser.parse_context(...)
    if context_result:
        return context_result
    
    # Try semantic/fuzzy matching
    # ...
```

---

## Cleanup Checklist

### Phase 1: YAML Cleanup (SAFE - Low Risk)
- [ ] Remove old start_dictation, stop_dictation commands
- [ ] Remove old start_manual_mode, stop_manual_mode commands  
- [ ] Remove old open_terminal, open_chrome, open_cursor commands
- [ ] Add context_close_app for "close" command
- [ ] Test: "start dictation", "stop dictation", "open chrome" still work

### Phase 2: Parser Cleanup (MEDIUM Risk - Needs Testing)
- [ ] Remove mode_commands dict
- [ ] Remove _try_mode_match method
- [ ] Remove _get_command_by_id method
- [ ] Remove triggers_map initialization
- [ ] Simplify parse() method
- [ ] Test: All parsing paths still work

### Phase 3: Context Parser Enhancement (LOW Risk)
- [ ] Add support for context_close action
- [ ] Test: "close chrome" works
- [ ] Future: support other contexts (focus, toggle, etc)

### Phase 4: Optional Polish (LOW Priority)
- [ ] Remove parse_interim if not used for UX
- [ ] Add better logging/debugging info
- [ ] Update documentation

---

## Impact Analysis

| Component | Before | After | Impact |
|-----------|--------|-------|--------|
| parser.py | 249 lines | 180 lines | -27% ✅ |
| commands.yaml | 700 lines | 620 lines | -11% ✅ |
| Code clarity | Complex | Simple | Better ✅ |
| Maintainability | Medium | High | Better ✅ |
| Redundancy | High | None | Eliminated ✅ |
| Extensibility | Medium | High | Better ✅ |
| Testing needed | N/A | Medium | ⚠️ |

---

## Testing Strategy

After cleanup, verify:

**Mode Commands:**
```
"start dictation" → mode = "dictation" ✓
"enter" in dictation → matches "send" ✓
"random text" in dictation → types as text ✓
"stop dictation" → mode = "normal" ✓

"start manual" → mode = "manual" ✓
"left" in manual → move cursor ✓
"stop manual" → mode = "normal" ✓
```

**App Launch:**
```
"open chrome" → launch Chrome ✓
"open ide" → launch Cursor ✓
"open music" → launch Spotify ✓
"open toggle focus" → IGNORED ✓
```

**Generic Commands:**
```
"click" → still works ✓
"undo" → still works ✓
"refresh" → still works ✓
```

---

## Recommended Order

1. **Update YAML first** (safe, can test each deletion)
2. **Update context_parser.py** (add close support)
3. **Simplify parser.py** (one method at a time)
4. **Comprehensive testing**
5. **Document changes**

---

## Questions for User

Before proceeding:

1. **Confidence Level:** Are you comfortable with this cleanup?
2. **Priority:** Should we do this now or later?
3. **Scope:** Want to include all 5 categories or just HIGH priority items?
4. **Close Command:** Should we add "close" context group in same cleanup?

Recommended: **Do HIGH priority items (#1-3) now, safe to do!**

