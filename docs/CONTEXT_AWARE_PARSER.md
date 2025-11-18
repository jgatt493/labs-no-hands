# Context-Aware Parser Design

## What We're Building

Instead of individual commands like:
- "open chrome"
- "open cursor"
- "open terminal"

We group them by **first-word context**:
- **"open"** → followed by app alias
  - "open chrome" → Launch Chrome
  - "open cursor" → Launch Cursor
  - "open ide" → Launch Cursor (alias)
  - "open music" → Launch Spotify (alias)
  - "open toggle focus" → **IGNORED** (toggle focus not valid alias)

## The Magic

**Semantic Parser + Context Awareness:**

1. Extract first word: "open"
2. Find matching context group
3. Check remaining words against valid aliases
4. If no valid alias found → IGNORE

## Example YAML Structure

```yaml
commands:
  - id: "context_open_app"
    action: "context_open"  # new action type
    primary_trigger: "open"
    
    apps:
      cursor:
        triggers: ["cursor", "ide", "code"]
        action: launch
        app: "Cursor"
      
      chrome:
        triggers: ["chrome", "browser", "google"]
        action: launch
        app: "Google Chrome"
      
      slack:
        triggers: ["slack"]
        action: launch
        app: "Slack"
      
      terminal:
        triggers: ["terminal", "shell"]
        action: launch
        app: "Terminal"
      
      spotify:
        triggers: ["spotify", "music"]
        action: launch
        app: "Spotify"
```

## How It Works in Parser

```python
# User says: "open chrome"
transcript = "open chrome"
words = transcript.split()
primary = "open"  # First word
alias = "chrome"  # Second word

# Find the app that has "chrome" as trigger
app = find_app_with_alias(alias)  # Returns: cursor app with "Chrome" alias
# Execute: Launch Chrome

# ---

# User says: "open toggle focus"
transcript = "open toggle focus"
words = transcript.split()
primary = "open"
alias = "toggle focus"

# Find the app that has "toggle focus" as trigger
app = find_app_with_alias("toggle focus")  # Returns: None
# Result: IGNORED - no valid alias found
```

## Benefits

✅ **Strict Intent Matching**: "open toggle focus" is ignored (toggle focus not app)
✅ **Semantic Understanding**: "open ide" = "open cursor" (same app)
✅ **No False Positives**: Unknown aliases don't trigger anything
✅ **Scalable**: Easy to add more aliases or app groups
✅ **Context Isolation**: Commands don't bleed between contexts

