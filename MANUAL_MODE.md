# Manual Mode - Voice Cursor Control

## Overview

Manual Mode allows you to manually control your cursor using voice commands when the automatic voice command system gets stuck or doesn't work as expected. This is a failsafe mechanism that lets you escape any situation.

## How It Works

### Entering Manual Mode

Say any of these commands in normal mode:
- **"manual mode"**
- **"start manual mode"**
- **"enter manual mode"**

Once activated, you'll hear: *"Manual mode started - use left, right, up, down, click"*

### Manual Mode Operations

In manual mode, **only these exact commands are recognized**. Any other speech is ignored:

#### Cursor Movement (15px per command)
- **"left"** - Move cursor 15 pixels left
- **"right"** - Move cursor 15 pixels right
- **"up"** - Move cursor 15 pixels up
- **"down"** - Move cursor 15 pixels down

#### Clicking
- **"click"** - Click at the current cursor position

#### Exiting Manual Mode
- **"stop manual mode"**
- **"exit manual mode"**
- **"done"**

Once you exit, you'll hear: *"Manual mode stopped"*

## Important Notes

### Strict Exact Matching
In manual mode, commands must be **exact**:
- ✓ Saying "left" alone → works
- ✗ Saying "go left" → ignored
- ✗ Saying "move left please" → ignored
- ✗ Saying "left click" → ignored (only matches if you say "click" separately)

### Movement Distance
Each movement command moves your cursor by **15 pixels**. To move further, repeat the command multiple times:
- Say "left" 3 times to move 45 pixels left
- Say "up" twice to move 30 pixels up

### Screen Boundaries
The cursor will not move beyond your screen boundaries. If you're at the edge and say "right", the cursor stays at the screen edge.

## Use Cases

### Example 1: Unstick from Command Recognition

```
You: "manual mode"
System: "Manual mode started - use left, right, up, down, click"

You: "left"
System: "Moving cursor left"

You: "left"
System: "Moving cursor left"

You: "down"
System: "Moving cursor down"

You: "click"
System: "Clicked"

You: "stop manual mode"
System: "Manual mode stopped"
```

### Example 2: Fine-Tuning Cursor Position

If the automatic command system positioned your cursor slightly off:

```
You: "manual mode"
You: "up"      # Move up 15px
You: "right"   # Move right 15px
You: "click"   # Click at fine-tuned position
You: "done"    # Exit manual mode
```

## Technical Details

### Implementation

- **Parser** (`src/commands/parser.py`): Filters input for exact matches in manual mode
- **Executor** (`src/commands/executor.py`): Handles `move_cursor` action type
- **MacOS Control** (`src/automation/macos_control.py`):
  - `get_mouse_position()`: Gets current cursor coordinates
  - `move_cursor(direction, distance)`: Moves cursor relative to current position
- **Config** (`src/commands/config.py`): Stores direction and distance properties

### Movement Precision

- Movement increments: 15 pixels (configurable in `commands.yaml`)
- Minimum position: (0, 0) - top-left corner
- Maximum position: Screen width and height
- Direction options: left, right, up, down

### Command Structure

Manual mode commands in `config/commands.yaml`:

```yaml
- id: "start_manual_mode"
  triggers: ["manual mode", "start manual mode", "enter manual mode"]
  action: mode
  mode: "manual"

- id: "move_left"
  triggers: ["left"]
  action: move_cursor
  direction: "left"
  distance: 15
  
- id: "click_manual"
  triggers: ["click"]
  action: click
  coordinates: [0, 0]  # Uses current cursor position
```

## Troubleshooting

### Cursor Not Moving
1. Make sure you're in manual mode (you should hear the confirmation)
2. Verify you're saying the exact word (just "left", not "move left")
3. Check that your app has permission to control the cursor

### Can't Exit Manual Mode
Say "done" or "stop manual mode" - these are failsafe exit commands that work from anywhere

### Movement Too Slow
You can increase the `distance` value in `commands.yaml` from 15 to a higher number (e.g., 30, 50)

## Future Enhancements

Potential improvements to manual mode:
- Variable distance movement (e.g., "left fast", "left slow")
- Hold and drag (e.g., "drag left 100")
- Screen edge detection with audio feedback
- Position indicators

