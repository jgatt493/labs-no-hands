# Voice Command macOS - Quick Install

## **Auto-Start on Login (2 Steps)**

### **Step 1: Run the install script**
```bash
cd /Users/jeremygatt/Projects/voice-command-mac
bash install-launch-agent.sh
```

### **Step 2: Restart your computer**

That's it! On next login:
- ✅ App waits for Jabra to connect
- ✅ Automatically starts listening
- ✅ Keeps running in background

---

## **Verify it's working:**

**Check if it's running:**
```bash
launchctl list | grep voicecommand
```

**Watch the logs:**
```bash
tail -f ~/.voice-command/logs/startup.log
```

**Stop the service (if needed):**
```bash
launchctl stop com.voicecommand.listener
```

---

## **Full Documentation:**

See `SETUP_LAUNCH_AGENT.md` for:
- Detailed setup instructions
- Troubleshooting
- Manual commands
- How to view logs

---

## **That's it! 🎉**

Your voice command listener is now set up to run automatically on login!

When you restart your Mac and connect your Jabra headset, the app will automatically start listening for voice commands.

Check the logs to monitor what's happening:
```bash
tail -f ~/.voice-command/logs/startup.log
```

