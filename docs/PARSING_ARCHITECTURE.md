# Proposed Parsing Architecture - Four Execution Paths

## Overview

Clean separation of concerns with context-aware app state management.

```
Input: "open cursor"
    ↓
    ├─ PATH 1: Is it a keyword? (open/start/stop/focus/close)
    │   ├─ YES → Parse remainder
    │   │   ├─ Execute action
    │   │   └─ UPDATE APP STATE (cursor is now active)
    │   └─ NO → Continue to PATH 2
    │
    ├─ PATH 2: Are we in a mode? (dictation/manual)
    │   ├─ YES → Execute mode commands only
    │   │        Return OR ignore
    │   └─ NO → Continue to PATH 3
    │
    ├─ PATH 3: Is there an OPENED APP? (cursor/terminal/chrome)
    │   ├─ YES → Execute app-scoped commands
    │   │        e.g., "focus" means different things per app
    │   └─ NO → Continue to PATH 4
    │
    └─ PATH 4: Generic command matching
        └─ Execute generic commands
```

---

## PATH 1: Keyword Routing

### Structure
```
Keyword (open/start/stop/focus/close/toggle/etc)
    ↓
Parse remainder into alias
    ↓
Lookup in keyword context
    ↓
Execute + UPDATE STATE
```

### Examples

#### OPEN Keyword
```
"open cursor"      → Launch Cursor
                   → STATE: app = "Cursor"

"open terminal"    → Launch Terminal
                   → STATE: app = "Terminal"

"open chrome"      → Launch Chrome
                   → STATE: app = "Chrome"
```

#### START Keyword
```
"start dictation"  → Enter dictation mode
                   → STATE: mode = "dictation"

"start manual"     → Enter manual mode
                   → STATE: mode = "manual"
```

#### STOP Keyword
```
"stop dictation"   → Exit dictation mode
                   → STATE: mode = "normal"

"stop manual"      → Exit manual mode
                   → STATE: mode = "normal"
```

#### CLOSE Keyword (Future)
```
"close cursor"     → Close Cursor app
                   → STATE: app = None

"close"            → Close currently opened app
                   → STATE: app = None
```

---

## PATH 2: Mode-Based Execution

### Structure
```
Check: if app.state.mode == "dictation" or "manual"
    ↓
YES → Execute ONLY mode-specific commands
      (enter/clear/stop dictation, left/right/up/down/click/stop manual)
    ↓
NO → Continue to PATH 3
```

### Examples

```
STATE: mode = "dictation"
Input: "enter"         → Execute send (allowed)
Input: "hello world"   → Ignore (typed as text in dictation mode)
Input: "stop dictation" → Exit mode → Continue to PATH 3/4

STATE: mode = "manual"
Input: "left"          → Move cursor left (allowed)
Input: "click"         → Click (allowed)
Input: "random text"   → Ignore (not allowed in manual mode)
```

---

## PATH 3: App-Scoped Commands

### Structure
```
Check: if app.state.app == "Cursor" or "Terminal" or "Chrome"
    ↓
YES → Execute app-specific command variants
    ↓
NO → Continue to PATH 4
```

### Examples

**In Cursor context:**
```
"focus"            → Focus Cursor chat (coordinates: [1449, 912])

"comment"          → Comment line in Cursor
                   → CMD+/

"toggle terminal"  → Toggle Cursor terminal
                   → CMD+J
```

**In Terminal context:**
```
"focus"            → Focus Terminal input area
                   → (different coordinates than Cursor)

"clear"            → Clear terminal
                   → CMD+K (or clear command)

"comment"          → IGNORED (not applicable to terminal)
```

**In Chrome context:**
```
"focus"            → Focus Chrome address bar
                   → coordinates: [2116, 87]

"comment"          → IGNORED (not a Chrome feature)

"toggle"           → Toggle dev tools?
                   → (app-specific behavior)
```

### How It Works

```yaml
# Command definition
- id: "focus_chat"
  action: "focus"
  app_contexts:
    Cursor:
      coordinates: [1449, 912]
      feedback: "Focusing Cursor chat"
    Chrome:
      coordinates: [2116, 87]
      feedback: "Focusing Chrome address bar"
    Terminal:
      coordinates: [100, 300]
      feedback: "Focusing Terminal"
```

When "focus" is spoken:
1. Check PATH 1: Not a keyword ✗
2. Check PATH 2: Not in mode ✗
3. Check PATH 3: app.state.app = "Cursor" ✓
   - Get Cursor-specific config
   - Use coordinates: [1449, 912]
   - Execute click

---

## PATH 4: Generic Commands

### Structure
```
Check: Keyword? NO
       Mode active? NO
       App context? NO
    ↓
YES → Execute generic commands
      (no app-specific variants)
```

### Examples
```
"click"            → Click at current mouse position
"help"             → Show help
"refresh"          → CMD+R (generic refresh)
"search"           → CMD+F (generic search)
"undo"             → CMD+Z (generic undo)
```

---

## App State Management

### State Structure
```python
class AppState:
    mode: str = "normal"      # dictation, manual
    app: Optional[str] = None # Cursor, Terminal, Chrome, Slack, Spotify
    
    def set_app(self, app_name: str):
        """Called when user says 'open X'"""
        self.app = app_name
        logger.info(f"Active app: {app_name}")
    
    def clear_app(self):
        """Called when user says 'close' or app exits"""
        self.app = None
        logger.info("No active app")
    
    def set_mode(self, mode: str):
        """Called when user says 'start/stop X'"""
        self.mode = mode
        logger.info(f"Mode: {mode}")
```

### State Transitions

```
NORMAL mode:
    "open cursor" ──→ app = "Cursor"
    "start manual" ──→ mode = "manual"
    
CURSOR app active:
    "focus" ──→ click at [1449, 912]
    "comment" ──→ CMD+/
    "toggle terminal" ──→ CMD+J
    
MANUAL mode:
    "left" ──→ move cursor left
    "stop manual" ──→ mode = "normal"
    
DICTATION mode:
    "enter" ──→ send/return
    "stop dictation" ──→ mode = "normal"
```

---

## Comparison: Old vs New

### OLD (Current)
```
Input → Normalize
      → Try context parser
      → Try semantic matching
      → Try fuzzy matching
      → Return command
      → Execute
      (No state management)
```

### NEW (Proposed)
```
Input → Normalize
    ↓
    ├─ PATH 1: Keyword?
    │   ├─ YES: Parse + Execute + UPDATE STATE
    │   └─ NO: Continue
    ↓
    ├─ PATH 2: Mode active?
    │   ├─ YES: Execute mode command or IGNORE
    │   └─ NO: Continue
    ↓
    ├─ PATH 3: App active?
    │   ├─ YES: Execute app-scoped command
    │   └─ NO: Continue
    ↓
    └─ PATH 4: Generic command
        └─ Execute generic command
```

---

## Implementation Priorities

### Phase 1: Foundation
- [x] Keyword routing (open/start/stop)
- [ ] App state management
- [ ] Extend context parser for PATH 1

### Phase 2: App Scoping
- [ ] App-specific command variants
- [ ] Context-aware coordinates
- [ ] PATH 3 execution

### Phase 3: Polish
- [ ] Generic fallback (PATH 4)
- [ ] State persistence (optional)
- [ ] Enhanced logging/feedback

---

## Code Structure

```
src/
├── app_state.py           (NEW - state management)
├── commands/
│   ├── parser.py          (UPDATE - route to 4 paths)
│   ├── context_parser.py  (KEEP - PATH 1)
│   └── executor.py        (UPDATE - app-scoped execution)
└── automation/
    └── macos_control.py   (KEEP)
```

