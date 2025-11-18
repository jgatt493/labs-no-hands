#!/usr/bin/env python3
"""
Demo script to test the context-aware parser

Run with: python3 demo_context_parser.py
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from commands.config import CommandConfig
from commands.parser import CommandParser

# Load config
config = CommandConfig(Path(__file__).parent / "config" / "commands.yaml")
parser = CommandParser(config)

# Test cases
test_cases = [
    # OPEN context - Valid matches
    ("open chrome", "Should launch Chrome"),
    ("open browser", "Should launch Chrome (alias)"),
    ("open ide", "Should launch Cursor (alias)"),
    ("open music", "Should launch Spotify (alias)"),
    ("open slack", "Should launch Slack"),
    ("open terminal", "Should launch Terminal"),
    
    # OPEN context - Invalid matches (should return None)
    ("open toggle focus", "Should IGNORE (toggle focus not valid alias)"),
    ("open click", "Should IGNORE (click not valid app alias)"),
    ("open", "Should IGNORE (no alias provided)"),
    
    # START context - Valid matches
    ("start dictation", "Should enter dictation mode"),
    ("start dictate", "Should enter dictation mode (alias)"),
    ("start manual", "Should enter manual mode"),
    ("start manual mode", "Should enter manual mode (alias)"),
    
    # STOP context - Valid matches
    ("stop dictation", "Should exit dictation mode"),
    ("stop dictate", "Should exit dictation mode (alias)"),
    ("stop manual", "Should exit manual mode"),
    ("stop manual mode", "Should exit manual mode (alias)"),
    
    # STOP context - Invalid matches
    ("stop something", "Should IGNORE (something not valid mode)"),
    
    # Other commands (should use normal matching)
    ("click", "Should click at current position"),
    ("toggle terminal", "Should toggle terminal in IDE"),
]

print("=" * 70)
print("🎯 CONTEXT-AWARE PARSER DEMO")
print("=" * 70)
print()

for transcript, expected in test_cases:
    result = parser.parse(transcript, mode="normal")
    
    if result:
        cmd, score = result
        print(f"✅ '{transcript}'")
        print(f"   └─ Command: {cmd.id}")
        print(f"   └─ Action: {cmd.action}")
        print(f"   └─ Expected: {expected}")
    else:
        print(f"❌ '{transcript}'")
        print(f"   └─ IGNORED")
        print(f"   └─ Expected: {expected}")
    
    print()

print("=" * 70)

