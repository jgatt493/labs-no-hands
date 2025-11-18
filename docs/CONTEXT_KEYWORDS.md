# Context Keywords - First-Word Command Grouping

## Overview

Context keywords group related commands by their **first word**, allowing semantic grouping with strict alias validation.

```
Primary keyword → Valid aliases → Action
open            → chrome, ide, music, slack, terminal → Launch app
start           → dictation, manual → Enter mode
stop            → dictation, manual → Exit mode
```

## Implemented Contexts

### 1. OPEN Context - Launch Applications
**Primary Keyword:** `open`

```
open chrome         → Launch Google Chrome
open browser        → Launch Google Chrome (alias)
open ide            → Launch Cursor (alias)
open code           → Launch Cursor (alias)
open cursor         → Launch Cursor
open slack          → Launch Slack
open terminal       → Launch Terminal
open shell          → Launch Terminal (alias)
open spotify        → Launch Spotify
open music          → Launch Spotify (alias)
```

**Invalid examples (correctly ignored):**
```
open toggle focus   ✗ (toggle focus not an app)
open click          ✗ (click not an app)
open                ✗ (no alias provided)
```

### 2. START Context - Enter Modes
**Primary Keyword:** `start`

```
start dictation     → Enter dictation mode
start dictate       → Enter dictation mode (alias)
start manual        → Enter manual mode
start manual mode   → Enter manual mode (alias)
```

### 3. STOP Context - Exit Modes
**Primary Keyword:** `stop`

```
stop dictation      → Exit dictation mode (return to normal)
stop dictate        → Exit dictation mode (alias)
stop manual         → Exit manual mode
stop manual mode    → Exit manual mode (alias)
```

## Architecture

### Parsing Flow

```
Input: "start dictation"
        ↓
    Parse words: ["start", "dictation"]
        ↓
Context lookup: Is "start" a context? YES
        ↓
Alias lookup: Is "dictation" valid for "start"? YES
        ↓
Retrieve config: mode="dictation", action="mode"
        ↓
Execute: Enter dictation mode ✅
```

### YAML Structure

```yaml
- id: "context_open_app"
  action: "context_open"
  primary_trigger: "open"
  apps:
    cursor:
      triggers: ["cursor", "ide", "code"]
      action: launch
      app: "Cursor"
      feedback: "Opening Cursor"

- id: "context_start_mode"
  action: "context_mode"
  primary_trigger: "start"
  modes:
    dictation:
      triggers: ["dictation", "dictate"]
      action: mode
      mode: "dictation"
      feedback: "Starting dictation mode"
```

### Code Implementation

**ContextAwareParser** (`src/commands/context_parser.py`):
- Builds context maps on initialization
- Supports both `context_open` and `context_mode` actions
- Returns synthetic CommandAction with matching command

**CommandParser** (`src/commands/parser.py`):
- Imports ContextAwareParser
- Tries context-aware parsing BEFORE semantic/fuzzy matching
- Ensures context commands get priority

**Parsing Order:**
```
1. Mode-specific strict matching (dictation, manual modes)
2. Context-aware matching (open X, start X, stop X)
3. Semantic similarity matching
4. Fuzzy matching fallback
```

## Benefits

✅ **Strict Intent Matching**: Unknown aliases are ignored
✅ **No False Positives**: "open click" doesn't trigger app commands
✅ **Scalable**: Easy to add new contexts (focus, close, toggle, etc)
✅ **Clear Semantics**: First word determines command category
✅ **Extensible**: Each context can have unlimited aliases

## Adding New Contexts

To add a new context (e.g., "focus"):

```yaml
- id: "context_focus_app"
  action: "context_open"  # or "context_mode" for modes
  primary_trigger: "focus"
  apps:
    cursor:
      triggers: ["cursor", "ide"]
      action: focus
      app: "Cursor"
    slack:
      triggers: ["slack"]
      action: focus
      app: "Slack"
```

The parser will automatically handle it!

## Future Contexts

Planned:
- `focus [app]` - Bring app to foreground
- `close [app]` - Close an application
- `toggle [panel]` - Toggle various panels
- `play [media]` - Spotify controls
- `search [query]` - Search in various apps

All follow the same context-keyword pattern.

