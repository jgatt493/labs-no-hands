# Specific Cleanup Actions

## 1. DELETE from parser.py

### 1a. Remove mode_commands dictionary initialization
**Delete lines 125-144 from CommandParser.__init__:**
```python
# REMOVE THIS:
# Mode-specific command mappings for strict matching
self.mode_commands = {
    "dictation": {
        "enter": ["send"],
        "return": ["send"],
        "stop dictation": ["stop_dictation"],
        "end dictation": ["stop_dictation"],
        "done": ["stop_dictation"],
    },
    "manual": {
        "left": ["move_left"],
        "right": ["move_right"],
        "up": ["move_up"],
        "down": ["move_down"],
        "click": ["click_manual"],
        "stop manual mode": ["stop_manual_mode"],
        "exit manual mode": ["stop_manual_mode"],
        "done": ["stop_manual_mode"],
    },
}
```

### 1b. Remove triggers_map initialization
**Delete line 116:**
```python
# REMOVE THIS:
self.triggers_map = config.get_all_triggers()
```

### 1c. Remove _get_command_by_id method
**Delete lines 187-192:**
```python
# REMOVE THIS:
def _get_command_by_id(self, command_id: str) -> Optional[CommandAction]:
    """Get a command by its ID"""
    for cmd in self.config.commands:
        if cmd.id == command_id:
            return cmd
    return None
```

### 1d. Remove _try_mode_match method
**Delete lines 194-209:**
```python
# REMOVE THIS:
def _try_mode_match(self, transcript_clean: str, mode: str) -> Optional[Tuple[CommandAction, float]]:
    """Try to match using mode-specific strict matching"""
    if mode not in self.mode_commands:
        return None
    
    mode_map = self.mode_commands[mode]
    
    # Check if transcript matches any allowed command in this mode
    if transcript_clean in mode_map:
        command_ids = mode_map[transcript_clean]
        cmd = self._get_command_by_id(command_ids[0])
        if cmd:
            logger.info(f"✅ Matched: {cmd.id} (exact match in {mode} mode)")
            return cmd, 1.0
    
    return None
```

### 1e. Simplify parse method
**Replace entire parse() method (lines 211-343) with simplified version:**

```python
def parse(self, transcript: str, mode: str = "normal") -> Optional[Tuple[CommandAction, float]]:
    """
    Parse transcript using 4-path execution:
    1. Keyword context (open/start/stop)
    2. Mode-based filtering
    3. Semantic/fuzzy matching
    """
    if not transcript or not transcript.strip():
        return None

    transcript_clean = self._normalize_text(transcript)
    
    # PATH 1: Try context-aware parser first (handles keywords + aliases)
    logger.debug(f"Trying context-aware parser for: '{transcript}'")
    context_result = self.context_parser.parse_context(transcript, mode)
    if context_result:
        cmd, score = context_result
        logger.info(f"✅ Matched: {cmd.id} (context-aware, score: {score:.2f})")
        return cmd, score
    logger.debug(f"No context match for: '{transcript}' - trying semantic/fuzzy")
    
    # PATH 2: In special modes, only allow specific commands
    # (Mode filtering happens via triggers in YAML, not here)
    
    # PATH 3/4: Normal mode - Use semantic similarity if available
    best_match = None
    best_score = 0.0

    if self.semantic_model and self.trigger_embeddings:
        # Semantic matching (more robust)
        try:
            # Encode the transcript
            transcript_embedding = self.semantic_model.encode(transcript, convert_to_tensor=True)
            
            # Compare against all trigger embeddings
            for cmd in self.config.commands:
                for trigger in cmd.triggers:
                    if trigger in self.trigger_embeddings:
                        trigger_embedding = self.trigger_embeddings[trigger]
                        # Calculate cosine similarity (0-1 range)
                        similarity = util.pytorch_cos_sim(
                            transcript_embedding, trigger_embedding
                        ).item()
                        
                        if similarity > best_score:
                            best_score = similarity
                            best_match = (cmd, similarity)
        except Exception as e:
            logger.debug(f"Semantic matching error: {e}")
    
    # Check semantic match threshold
    if best_match and best_score >= self.config.app_config.match_threshold:
        cmd, score = best_match
        logger.info(f"✅ Matched: {cmd.id} (semantic score: {score:.2f})")
        return cmd, score
    
    # Fuzzy matching fallback
    for cmd in self.config.commands:
        for trigger in cmd.triggers:
            score = fuzz.token_set_ratio(transcript_clean, trigger.lower()) / 100.0
            
            if score >= self.config.app_config.match_threshold:
                if score > best_score:
                    best_score = score
                    best_match = (cmd, score)
    
    if best_match:
        cmd, score = best_match
        logger.info(f"✅ Matched: {cmd.id} (fuzzy score: {score:.2f})")
        return cmd, score
    
    return None
```

### 1f. OPTIONAL: Remove parse_interim method
**Delete lines (find and delete entire method)**

---

## 2. DELETE from config/commands.yaml

### 2a. Remove individual mode commands
**Delete these command blocks:**
```yaml
  - id: "start_dictation"
    triggers:
      - "start dictation"
      - "dictate"
    action: mode
    mode: dictation
    feedback: "Starting dictation mode"

  - id: "stop_dictation"
    triggers:
      - "stop dictation"
      - "end dictation"
      - "done"
    action: mode
    mode: normal
    feedback: "Stopping dictation mode"

  - id: "start_manual_mode"
    triggers:
      - "start manual mode"
      - "manual mode"
      - "enter manual mode"
    action: mode
    mode: manual
    feedback: "Starting manual mode"

  - id: "stop_manual_mode"
    triggers:
      - "stop manual mode"
      - "exit manual mode"
      - "done"
    action: mode
    mode: normal
    feedback: "Stopping manual mode"
```

### 2b. Remove individual app launch commands
**Delete these command blocks:**
```yaml
  - id: "open_terminal"
    triggers:
      - "open terminal"
      - "terminal"
      - "new terminal"
    action: launch
    app: "Terminal"
    feedback: "Opening terminal"

  - id: "open_chrome"
    triggers:
      - "open chrome"
      - "open browser"
      - "chrome"
      - "browser"
    action: launch
    app: "Google Chrome"
    feedback: "Opening Chrome"

  - id: "open_cursor"
    triggers:
      - "open cursor"
    action: launch
    app: "Cursor"
    feedback: "Opening Cursor"
```

### 2c. Add CLOSE context group
**Add after the STOP context group (around line 104):**
```yaml
  # CONTEXT-AWARE: Close applications
  # Usage: "close cursor", "close terminal", "close chrome"
  - id: "context_close_app"
    action: "context_close"
    primary_trigger: "close"
    apps:
      cursor:
        triggers: ["cursor", "ide", "code"]
        action: "close"
        app: "Cursor"
        feedback: "Closing Cursor"
      
      chrome:
        triggers: ["chrome", "browser"]
        action: "close"
        app: "Google Chrome"
        feedback: "Closing Chrome"
      
      slack:
        triggers: ["slack"]
        action: "close"
        app: "Slack"
        feedback: "Closing Slack"
      
      terminal:
        triggers: ["terminal", "shell"]
        action: "close"
        app: "Terminal"
        feedback: "Closing Terminal"
      
      spotify:
        triggers: ["spotify", "music"]
        action: "close"
        app: "Spotify"
        feedback: "Closing Spotify"
```

---

## 3. UPDATE context_parser.py

### 3a. Add support for context_close action
**In _build_context_map(), after the context_mode block, add:**

```python
elif action == "context_close":
    # App close context (e.g., "close cursor")
    context_key = cmd.primary_trigger
    
    # Build app map for this context
    items = {}
    if cmd.apps:
        for app_name, app_config in cmd.apps.items():
            # Store each trigger as a key pointing to the app
            for trigger in app_config.get("triggers", []):
                items[trigger.lower()] = {
                    "name": app_name,
                    "app": app_config.get("app"),
                    "action": app_config.get("action"),
                    "feedback": app_config.get("feedback"),
                }
    
    self.context_map[context_key] = {
        "cmd": cmd,
        "type": "app",
        "items": items,
    }
```

### 3b. Add close app action to config.py
**Add to CommandAction fields if not already present:**
```python
context_close_action: Optional[str] = None  # For close context
```

---

## Summary of Deletions

### parser.py
- **lines 116**: `self.triggers_map = ...`
- **lines 125-144**: `mode_commands` dict (~20 lines)
- **lines 187-192**: `_get_command_by_id()` method (~6 lines)
- **lines 194-209**: `_try_mode_match()` method (~16 lines)
- **lines 211-343**: `parse()` method (~133 lines), replace with simpler version (~80 lines)
- **parse_interim()** method (~40 lines, optional)

**Total: ~69 lines removed from parser.py (180 lines total after cleanup)**

### commands.yaml
- **start_dictation** command (~8 lines)
- **stop_dictation** command (~8 lines)
- **start_manual_mode** command (~8 lines)
- **stop_manual_mode** command (~8 lines)
- **open_terminal** command (~8 lines)
- **open_chrome** command (~8 lines)
- **open_cursor** command (~5 lines)

**Total: ~53 lines removed from YAML (restored via context groups)**

---

## Benefits After Cleanup

✅ **Cleaner code**: Remove ~100 lines of redundancy
✅ **Single source of truth**: Context groups handle everything
✅ **Easier to extend**: Add new commands to existing contexts
✅ **Better maintainability**: Less duplicated logic
✅ **Smaller files**: More focused, easier to understand
✅ **Path 2 built-in**: Mode filtering via context commands
✅ **Ready for Path 3**: App-scoped commands next

