# App-Specific Commands Architecture

## Vision

**Hot-swappable command sets** that load based on active app context.

```
Global Commands (always available)
├─ open, close, start, stop, click, etc.
└─ Generic: undo, redo, refresh, help

+ App-Specific Commands (only when app is active)
├─ Cursor App
│  ├─ chat (cmd+option+b)
│  ├─ edit (cmd+i)
│  ├─ composer (cmd+shift+l)
│  ├─ toggle terminal (cmd+j)
│  └─ toggle files (cmd+b)
│
├─ Terminal App
│  ├─ clear (cmd+k or clear)
│  └─ (can add more terminal-specific)
│
└─ Chrome App
   ├─ search (cmd+l)
   └─ (can add more browser-specific)
```

---

## File Structure

```
config/
├── commands.yaml              (Global commands - always available)
└── app_commands/
    ├── cursor.yaml            (Cursor app specific)
    ├── terminal.yaml          (Terminal app specific)
    ├── chrome.yaml            (Chrome app specific)
    └── slack.yaml             (Slack app specific)
```

---

## How It Works

### 1. INITIALIZATION

```python
# main.py
app = VoiceCommandApp()

# Loads global commands
app.global_commands = CommandConfig('config/commands.yaml')

# Pre-load app configs (lazy or eager)
app.app_configs = {
    'Cursor': CommandConfig('config/app_commands/cursor.yaml'),
    'Terminal': CommandConfig('config/app_commands/terminal.yaml'),
    'Chrome': CommandConfig('config/app_commands/chrome.yaml'),
}
```

### 2. STATE CHANGE

```python
# When user says "open cursor"
executor.execute(open_cursor_command)
  ↓
app_state.set_app("Cursor")  # Update state
  ↓
parser.load_app_commands("Cursor")  # Load Cursor-specific commands
```

### 3. PARSING WITH APP CONTEXT

```python
# User says: "toggle chat"
transcript = "toggle chat"

# Parser tries:
1. Global commands (context, semantic, fuzzy)
   └─ No match
2. App-specific commands (if app is set)
   ├─ Check: is app == "Cursor"?
   ├─ Load: cursor.yaml commands
   ├─ Parse: "toggle chat" → cursor_toggle_chat ✓
   └─ Execute
3. Generic fallback
   └─ N/A
```

---

## CommandParser Updates

### Current Flow
```python
def parse(self, transcript: str, mode: str = "normal"):
    # 1. Context parsing
    # 2. Semantic matching
    # 3. Fuzzy matching
    return match
```

### New Flow
```python
def parse(self, transcript: str, mode: str = "normal", app: str = None):
    # 1. Context parsing (global only)
    context_result = self.context_parser.parse_context(transcript, mode)
    if context_result:
        return context_result
    
    # 2. App-specific parsing (if app is set)
    if app and self.app_commands.get(app):
        app_result = self._parse_app_commands(transcript, app)
        if app_result:
            return app_result
    
    # 3. Global semantic/fuzzy
    global_result = self._parse_global_commands(transcript)
    if global_result:
        return global_result
    
    return None
```

---

## Implementation Steps

### Step 1: Create App Command Configs

**config/app_commands/cursor.yaml**
```yaml
config:
  # Same structure as main commands.yaml
  deepgram_model: "nova-3"
  # ...

commands:
  # Cursor-specific commands
  - id: "toggle_chat"
    triggers:
      - "toggle chat"
      - "chat toggle"
    action: keystroke
    keys: ["cmd", "option", "b"]
    feedback: "Toggling chat"
  
  - id: "toggle_files"
    triggers:
      - "toggle files"
      - "files toggle"
      - "show files"
    action: keystroke
    keys: ["cmd", "b"]
    feedback: "Toggling files panel"
  
  - id: "toggle_terminal_cursor"
    triggers:
      - "toggle terminal"
      - "terminal toggle"
      - "show terminal"
    action: keystroke
    keys: ["cmd", "j"]
    feedback: "Toggling terminal"
  
  # Cursor-specific features
  - id: "cursor_edit"
    triggers:
      - "edit"
      - "inline edit"
    action: keystroke
    keys: ["cmd", "i"]
    feedback: "Opening inline edit"
  
  - id: "cursor_composer"
    triggers:
      - "composer"
      - "multi edit"
    action: keystroke
    keys: ["cmd", "shift", "l"]
    feedback: "Opening composer"
```

### Step 2: Update App State

**src/app_state.py**
```python
class AppState:
    def __init__(self):
        self.mode: str = "normal"
        self.app: Optional[str] = None
        self.last_app: Optional[str] = None  # Track previous app
    
    def set_app(self, app_name: str) -> None:
        self.last_app = self.app
        self.app = app_name
        logger.info(f"📱 Active app: {app_name}")
    
    def switch_app(self, from_app: str, to_app: str) -> bool:
        """Check if app switch is valid"""
        if self.app == from_app:
            self.set_app(to_app)
            return True
        return False
```

### Step 3: Update CommandParser

**src/commands/parser.py**
```python
class CommandParser:
    def __init__(self, config: CommandConfig):
        self.global_config = config
        self.global_commands = config.commands
        self.app_commands = {}  # Dict of app-specific configs
        self.current_app_config = None
        
        # ... existing init ...
    
    def load_app_commands(self, app_name: str) -> bool:
        """Load app-specific commands"""
        if app_name not in self.app_commands:
            # Lazy load
            app_config_path = Path(f"config/app_commands/{app_name.lower()}.yaml")
            if app_config_path.exists():
                self.app_commands[app_name] = CommandConfig(app_config_path)
        
        self.current_app_config = self.app_commands.get(app_name)
        return self.current_app_config is not None
    
    def parse(self, transcript: str, mode: str = "normal", app: str = None) -> ...:
        # ... existing context parsing ...
        
        # Try app-specific commands FIRST (higher priority)
        if app and self.load_app_commands(app):
            app_result = self._parse_commands(
                transcript, 
                self.current_app_config.commands
            )
            if app_result:
                return app_result
        
        # Fallback to global commands
        global_result = self._parse_commands(
            transcript,
            self.global_commands
        )
        return global_result
    
    def _parse_commands(self, transcript: str, commands: List[CommandAction]) -> ...:
        """Parse against a specific command set"""
        # Semantic matching
        # Fuzzy matching
        # etc.
```

### Step 4: Update Main

**src/main.py**
```python
class VoiceCommandApp:
    async def _on_transcript(self, result):
        # Get current app from state
        current_app = self.app_state.app
        
        # Parse with app context
        match = self.parser.parse(
            result.transcript, 
            mode=self.app_state.mode,
            app=current_app  # Pass app context!
        )
        
        if match:
            command, confidence = match
            success = await self.executor.execute(command)
            
            if success and command.state_update:
                self.executor._apply_state_update(command.state_update)
```

---

## Benefits

✅ **Command Isolation**
  - Cursor commands don't interfere with Terminal commands
  - No accidental matches across apps

✅ **Cleaner Matching**
  - Fewer commands to search through per app
  - Better accuracy (fewer false positives)

✅ **Hot-Swappable**
  - Add/remove app configs without restart
  - Easy to update specific app features

✅ **Scalable**
  - Add new apps just by creating new yaml files
  - No code changes needed

✅ **Maintainable**
  - App commands grouped logically
  - Easy to find and edit per-app features

---

## Example Flow

### User Journey

```
1. "open cursor"
   ├─ Match: context_open_cursor
   ├─ Execute: Launch Cursor
   └─ State: app = "Cursor"
          Parser loads: config/app_commands/cursor.yaml

2. "toggle chat"
   ├─ Try: Global commands → No match
   ├─ Try: Cursor commands → MATCH: toggle_chat
   ├─ Execute: CMD+Option+B
   └─ Result: Chat toggled! ✓

3. "toggle terminal"
   ├─ Try: Global commands → No match
   ├─ Try: Cursor commands → MATCH: toggle_terminal_cursor
   ├─ Execute: CMD+J
   └─ Result: Terminal toggled! ✓

4. "open terminal"
   ├─ Match: context_open_terminal
   ├─ Execute: Launch Terminal
   └─ State: app = "Terminal"
          Parser loads: config/app_commands/terminal.yaml

5. "toggle chat"
   ├─ Try: Global commands → No match
   ├─ Try: Terminal commands → No match
   ├─ Try: Global fallback → No match
   └─ Result: "No command matched" (correct!)

6. "open cursor"
   ├─ Match: context_open_cursor
   ├─ Execute: Focus/Launch Cursor
   └─ State: app = "Cursor"
          Parser reloads: config/app_commands/cursor.yaml

7. "toggle chat"
   ├─ Try: Global commands → No match
   ├─ Try: Cursor commands → MATCH: toggle_chat
   ├─ Execute: CMD+Option+B
   └─ Result: Chat toggled! ✓
```

---

## File Organization

```
project/
├── config/
│   ├── commands.yaml              # Global commands
│   └── app_commands/
│       ├── cursor.yaml            # Cursor-specific
│       ├── terminal.yaml          # Terminal-specific
│       ├── chrome.yaml            # Chrome-specific
│       └── slack.yaml             # Slack-specific
│
├── src/
│   ├── app_state.py
│   ├── commands/
│   │   ├── parser.py              # Updated for app context
│   │   ├── executor.py
│   │   └── config.py
│   └── main.py                    # Updated to pass app context
│
└── docs/
    └── APP_SPECIFIC_COMMANDS.md   # This file
```

---

## Migration Path

### Phase 1: Setup (Now)
- Create `config/app_commands/` directory
- Create `cursor.yaml` with Cursor-specific commands
- Update CommandParser to load app configs

### Phase 2: Integration (Next)
- Update main.py to pass app context
- Test Cursor-specific commands
- Verify no regressions

### Phase 3: Expansion
- Add Terminal-specific commands
- Add Chrome-specific commands
- Add Slack-specific commands

### Phase 4: Polish
- Optimize loading strategy
- Cache app configs
- Add config reloading for app commands

