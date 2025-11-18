# Context-Aware Parser - Complete Explanation

## What We Built

A **two-layer command matching system** that recognizes commands by their first word and validates the remaining words as valid aliases.

```
User says: "open chrome"
           ↓
Parser extracts: "open" (context) + "chrome" (alias)
           ↓
Context lookup: Does "open" group exist? YES
           ↓
Alias lookup: Is "chrome" a valid app alias in "open"? YES
           ↓
Action: Launch Google Chrome ✅
```

---

## How It Differs from Fuzzy Matching

### ❌ Old Fuzzy Matching (Text-based)
```python
# "open toggle focus" vs all known triggers
"open toggle focus" → 87% match to "focus toggle"
Result: INCORRECT! Executes focus_toggle command
```

### ✅ New Context-Aware + Semantic (Meaning-based)
```python
# "open toggle focus"
primary = "open"
alias = "toggle focus"

# Check: Is "open" a context? YES
# Check: Is "toggle focus" a valid app? NO
Result: IGNORED ✅
```

---

## Current Implementation: "Open" Context

### Valid Aliases
```yaml
open chrome        → Launch Google Chrome
open browser       → Launch Google Chrome (alias)
open ide          → Launch Cursor (alias)
open code         → Launch Cursor (alias)
open cursor       → Launch Cursor
open slack        → Launch Slack
open terminal     → Launch Terminal
open shell        → Launch Terminal (alias)
open spotify      → Launch Spotify
open music        → Launch Spotify (alias)
```

### Invalid Examples (Ignored)
```
open toggle focus     ✗ (toggle focus not an app)
open click           ✗ (click not an app)
open enter           ✗ (enter not an app)
open                 ✗ (no alias provided)
```

---

## How the Parser Works (Under the Hood)

### Step 1: Parse YAML Structure
The YAML defines a context group:

```yaml
- id: "context_open_app"
  action: "context_open"           # Special action type
  primary_trigger: "open"          # Context keyword
  apps:
    cursor:
      triggers: ["cursor", "ide", "code"]
      action: launch
      app: "Cursor"
      feedback: "Opening Cursor"
```

### Step 2: Build Context Map
On initialization, the parser builds:

```python
context_map = {
    "open": {
        "apps": {
            "chrome": {"app": "Google Chrome", "action": "launch", ...},
            "browser": {"app": "Google Chrome", "action": "launch", ...},
            "ide": {"app": "Cursor", "action": "launch", ...},
            "code": {"app": "Cursor", "action": "launch", ...},
            "cursor": {"app": "Cursor", "action": "launch", ...},
            "slack": {"app": "Slack", "action": "launch", ...},
            "terminal": {"app": "Terminal", "action": "launch", ...},
            "shell": {"app": "Terminal", "action": "launch", ...},
            "spotify": {"app": "Spotify", "action": "launch", ...},
            "music": {"app": "Spotify", "action": "launch", ...},
        }
    }
}
```

### Step 3: Match Against Context Map
```python
def parse_context(self, transcript: str):
    words = "open chrome".split()  # → ["open", "chrome"]
    
    primary = "open"
    alias = "chrome"
    
    # Is "open" a valid context?
    if "open" in self.context_map:  # YES
        apps = self.context_map["open"]["apps"]
        
        # Is "chrome" a valid alias in this context?
        if "chrome" in apps:  # YES
            return apps["chrome"]  # → Launch Chrome
        else:  # NO
            return None  # Ignore
```

---

## Execution Flow in Main Parser

```
parse(transcript, mode="normal")
         ↓
[Check if dictation mode] → No
         ↓
[Check if manual mode] → No
         ↓
⭐ [Try context-aware parser] ← NEW!
   ├─ "open chrome" → ✅ Returns Chrome launch command
   ├─ "open toggle focus" → ✅ Returns None (ignored)
   └─ Falls through to semantic/fuzzy if no match
         ↓
[Semantic similarity matching]
   ├─ "click" → Matches "click_current"
   └─ "toggle terminal" → Matches "toggle_terminal"
         ↓
[Fuzzy matching fallback]
         ↓
Return best match or None
```

---

## Demo Results

```
✅ 'open chrome'          → context_open_chrome (launch action)
✅ 'open browser'         → context_open_browser (launch action)
✅ 'open ide'            → context_open_ide (launch action)
✅ 'open music'          → context_open_music (launch action)
✅ 'open slack'          → context_open_slack (launch action)
✅ 'open terminal'       → context_open_terminal (launch action)
❌ 'open toggle focus'    → IGNORED ✓✓✓ (what we wanted!)
❌ 'open click'           → Falls back to "click" command
❌ 'open'                 → Falls back to fuzzy matching
✅ 'click'               → click_current
✅ 'toggle terminal'     → toggle_terminal
```

---

## Why This is Better

### Problem with Fuzzy Matching
- "open toggle focus" gets 87% match to "focus toggle"
- **Result:** Executes wrong command

### Solution with Context
- First word "open" = scope/context
- Second word must be valid app alias
- Unknown aliases are **explicitly rejected**
- **Result:** Only valid commands execute

### Semantic + Context
- Combines **meaning understanding** with **strict intent validation**
- "open browser" understands "browser" = Chrome (semantic)
- But also validates "browser" is allowed in "open" context (context)
- **Result:** Robust AND precise

---

## Next Steps You Wanted

**"I want to group commands via the first word"**

This is exactly what context-aware parsing does! We can extend it:

```yaml
# FUTURE: Focus commands
- id: "context_focus_app"
  action: "context_focus"
  primary_trigger: "focus"
  apps:
    cursor: { triggers: ["cursor", "ide"], ... }
    slack: { triggers: ["slack"], ... }
    # etc

# FUTURE: Close commands
- id: "context_close_app"
  action: "context_close"
  primary_trigger: "close"
  apps:
    cursor: { triggers: ["cursor", "app"], ... }
    # etc
```

All work with the same context-aware matching logic! 🎯

