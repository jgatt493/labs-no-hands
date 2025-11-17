from typing import List
from Quartz import (
    CGEventCreateMouseEvent,
    CGEventPost,
    kCGEventLeftMouseDown,
    kCGEventLeftMouseUp,
    kCGEventRightMouseDown,
    kCGEventRightMouseUp,
    kCGMouseButtonLeft,
    kCGMouseButtonRight,
    kCGHIDEventTap,
    CGEventCreateKeyboardEvent,
    kCGEventKeyDown,
    kCGEventKeyUp,
    CGEventSetFlags,
)
from Cocoa import NSEvent
from AppKit import NSWorkspace
from logger import logger


class MacOSControl:
    """Control macOS keyboard and mouse via PyObjC"""

    # Key code mapping
    KEY_CODES = {
        "cmd": 0x37,
        "command": 0x37,
        "ctrl": 0x3B,
        "control": 0x3B,
        "shift": 0x38,
        "alt": 0x3A,
        "option": 0x3A,
        "a": 0x00,
        "b": 0x0B,
        "c": 0x08,
        "d": 0x02,
        "e": 0x0E,
        "f": 0x03,
        "g": 0x05,
        "h": 0x04,
        "i": 0x22,
        "j": 0x26,
        "k": 0x28,
        "l": 0x25,
        "m": 0x2E,
        "n": 0x2D,
        "o": 0x1F,
        "p": 0x23,
        "q": 0x0C,
        "r": 0x0F,
        "s": 0x01,
        "t": 0x11,
        "u": 0x20,
        "v": 0x09,
        "w": 0x0D,
        "x": 0x07,
        "y": 0x10,
        "z": 0x06,
        "0": 0x1D,
        "1": 0x12,
        "2": 0x13,
        "3": 0x14,
        "4": 0x15,
        "5": 0x17,
        "6": 0x16,
        "7": 0x1A,
        "8": 0x1C,
        "9": 0x19,
        "tab": 0x30,
        "space": 0x31,
        "enter": 0x24,
        "return": 0x24,
        "backspace": 0x33,
        "delete": 0x33,
        "escape": 0x35,
        "esc": 0x35,
        "up": 0x7E,
        "down": 0x7D,
        "left": 0x7B,
        "right": 0x7C,
        "plus": 0x18,
        "minus": 0x1B,
        "equal": 0x18,
        "slash": 0x2C,
        "backslash": 0x2A,
        "comma": 0x2B,
        "period": 0x2F,
        "f1": 0x7A,
        "f2": 0x78,
        "f3": 0x63,
        "f4": 0x76,
        "f5": 0x60,
        "f6": 0x61,
        "f7": 0x62,
        "f8": 0x64,
        "f9": 0x65,
        "f10": 0x6D,
        "f11": 0x67,
        "f12": 0x6F,
        "pageup": 0x74,
        "pagedown": 0x79,
        "home": 0x73,
        "end": 0x77,
    }

    def __init__(self):
        self.modifier_keys = {"cmd": 0x100000, "ctrl": 0x40000, "shift": 0x20000, "alt": 0x80000}

    def get_active_app(self) -> str:
        """Get the name of the currently active application"""
        try:
            active_app = NSWorkspace.sharedWorkspace().activeApplication()
            app_name = active_app.get("NSApplicationName", "Unknown")
            logger.debug(f"Active app: {app_name}")
            return app_name
        except Exception as e:
            logger.error(f"Error getting active app: {e}")
            return "Unknown"

    def click(self, x: int, y: int, button: str = "left"):
        """Click at coordinates"""
        try:
            if button.lower() == "left":
                mouse_down = kCGEventLeftMouseDown
                mouse_up = kCGEventLeftMouseUp
                button_code = kCGMouseButtonLeft
            else:
                mouse_down = kCGEventRightMouseDown
                mouse_up = kCGEventRightMouseUp
                button_code = kCGMouseButtonRight

            # Mouse down
            down_event = CGEventCreateMouseEvent(
                None, mouse_down, (x, y), button_code
            )
            CGEventPost(kCGHIDEventTap, down_event)

            # Mouse up
            up_event = CGEventCreateMouseEvent(
                None, mouse_up, (x, y), button_code
            )
            CGEventPost(kCGHIDEventTap, up_event)

            logger.debug(f"Clicked at ({x}, {y}) with {button} button")

        except Exception as e:
            logger.error(f"Error clicking: {e}")

    def keystroke(self, keys: List[str]):
        """Execute keyboard shortcut"""
        try:
            # Map key names to codes and modifiers
            modifiers = 0
            key_code = None

            for key in keys:
                key_lower = key.lower()

                if key_lower in self.modifier_keys:
                    # Accumulate modifier flags
                    modifiers |= self.modifier_keys[key_lower]
                elif key_lower in self.KEY_CODES:
                    key_code = self.KEY_CODES[key_lower]

            if key_code is None:
                logger.error(f"Unknown key in keystroke: {keys}")
                return

            # Key down with modifiers
            down_event = CGEventCreateKeyboardEvent(None, key_code, True)
            CGEventSetFlags(down_event, modifiers)
            CGEventPost(kCGHIDEventTap, down_event)

            # Key up with modifiers
            up_event = CGEventCreateKeyboardEvent(None, key_code, False)
            CGEventSetFlags(up_event, modifiers)
            CGEventPost(kCGHIDEventTap, up_event)

            logger.debug(f"Executed keystroke: {'+'.join(keys)}")

        except Exception as e:
            logger.error(f"Error executing keystroke: {e}")

    def type_text(self, text: str):
        """Type text using pasteboard for better compatibility"""
        try:
            import subprocess
            # Use pbcopy and then Cmd+V for more reliable text input
            process = subprocess.Popen(['pbcopy'], stdin=subprocess.PIPE)
            process.communicate(text.encode('utf-8'))
            
            # Simulate Cmd+V to paste
            self.keystroke(['cmd', 'v'])
            
            logger.debug(f"Typed text via paste: {text}")

        except Exception as e:
            logger.error(f"Error typing text: {e}")

