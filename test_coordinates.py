#!/usr/bin/env python3
"""
Coordinate finder tool for multi-monitor setup.
Shows real-time mouse coordinates using the same system as MacOSControl.

Usage:
  python3 test_coordinates.py
  
Then move your mouse to the location you want (e.g., Cursor chat box)
and note the coordinates. Press Ctrl+C to stop.
"""

import time
from Quartz import CGEventGetLocation, CGEventCreate

print("=" * 60)
print("COORDINATE FINDER")
print("=" * 60)
print("\nMove your mouse to the Cursor chat box and note the coordinates.")
print("Press Ctrl+C to stop.\n")

try:
    while True:
        # Get current mouse position using Quartz (same as our automation)
        event = CGEventCreate(None)
        location = CGEventGetLocation(event)
        x = int(location.x)
        y = int(location.y)
        print(f"Current coordinates: X={x:5d}, Y={y:5d}", end='\r')
        time.sleep(0.1)
except KeyboardInterrupt:
    print("\n\n" + "=" * 60)
    print("Done! Use these coordinates in your config:")
    print(f"  coordinates: [{x}, {y}]")
    print("=" * 60)

