# Resources & References

## Deepgram

**API & Keys:**
- [Deepgram Console](https://console.deepgram.com) - Manage API keys and usage
- [Get API Keys](https://console.deepgram.com/keys) - Create/view your API keys
- [Free Tier](https://console.deepgram.com/signup) - Sign up for free account

**Documentation:**
- [Deepgram API Docs](https://developers.deepgram.com) - Complete reference
- [Speech-to-Text API](https://developers.deepgram.com/reference/speech-to-text) - STT docs
- [WebSocket Connection](https://developers.deepgram.com/docs/getting-started-with-pre-recorded-audio) - WebSocket guide
- [Python SDK](https://github.com/deepgram/deepgram-python-sdk) - Official Python SDK
- [Supported Models](https://developers.deepgram.com/reference/speech-to-text#model) - Model list

## Python Libraries

**Voice & Audio:**
- [PyAudio](https://people.csail.mit.edu/hubert/pyaudio/) - Audio I/O
- [websockets](https://websockets.readthedocs.io/) - WebSocket client
- [deepgram-sdk](https://github.com/deepgram/deepgram-python-sdk) - Deepgram SDK

**macOS Automation:**
- [PyObjC](https://pyobjc.readthedocs.io/) - Python-Objective C bridge
- [PyObjC Quartz](https://pyobjc.readthedocs.io/frameworks/Quartz.html) - Quartz framework

**Command Processing:**
- [FuzzyWuzzy](https://github.com/seatgeek/fuzzywuzzy) - Fuzzy string matching
- [python-Levenshtein](https://github.com/ztane/python-Levenshtein) - Fast string matching

**Configuration & CLI:**
- [Click](https://click.palletsprojects.com/) - CLI framework
- [Pydantic](https://docs.pydantic.dev/) - Data validation
- [PyYAML](https://pyyaml.org/) - YAML parser
- [python-dotenv](https://github.com/theskumar/python-dotenv) - Environment variables

**Utilities:**
- [colorama](https://github.com/tartley/colorama) - Colored terminal output
- [numpy](https://numpy.org/) - Numerical computing

## macOS Resources

**System Programming:**
- [macOS Automation Overview](https://support.apple.com/guide/automator/welcome/mac) - Automator guide
- [launchd Documentation](https://www.launchd.info/) - Daemon configuration
- [Keyboard Events](https://developer.apple.com/documentation/coregraphics/cgevent) - CGEvent API
- [Mouse Events](https://developer.apple.com/documentation/coregraphics/cgevent) - Mouse control

**Permissions:**
- [System Preferences Security](https://support.apple.com/en-us/HT202491) - Privacy settings
- [Microphone Access](https://support.apple.com/guide/mac-help/allow-an-app-to-access-your-mic-mchla1b08e68/mac) - Grant mic access
- [Accessibility](https://support.apple.com/guide/mac-help/change-privacy-settings-on-mac-mh35902/mac) - Accessibility permissions

## Development Tools

**Python:**
- [Python 3.9+ Download](https://www.python.org/downloads/) - Official Python
- [venv Documentation](https://docs.python.org/3/library/venv.html) - Virtual environments
- [pip Documentation](https://pip.pypa.io/) - Package manager

**Git & Version Control:**
- [Git Documentation](https://git-scm.com/doc) - Version control
- [GitHub Guides](https://guides.github.com/) - Git tutorials

## Keyboard Key Codes

Reference for macOS key codes used in the application:

```
Modifier Keys:
  cmd/command:  0x37
  ctrl:         0x3B
  shift:        0x38
  alt/option:   0x3A

Letters:
  a-z: 0x00-0x19

Numbers:
  0-9: 0x1D, 0x12-0x19

Special:
  space:     0x31
  tab:       0x30
  return:    0x24
  backspace: 0x33
  escape:    0x35
  delete:    0x33
```

## Common Issues & Solutions

### Microphone Not Working
- [Grant Terminal Microphone Access](https://support.apple.com/guide/mac-help/allow-an-app-to-access-your-mic-mchla1b08e68/mac)
- [Check Audio Input Settings](https://support.apple.com/guide/mac-help/change-sound-settings-mac-mchlp2a6e59f/mac)

### PyObjC Installation Issues
- [PyObjC Installation Guide](https://pyobjc.readthedocs.io/en/latest/intro.html)
- [Xcode Command Line Tools](https://developer.apple.com/download/all/) - May be required

### Deepgram API Issues
- [Deepgram Status Page](https://status.deepgram.com/) - Check service status
- [API Rate Limits](https://developers.deepgram.com/reference/rate-limits) - Rate limiting info
- [Support](https://support.deepgram.com/) - Help center

## Example Code References

**Speech-to-Text (WebSocket):**
```python
# See: src/deepgram/client.py
# Uses websockets library to connect to Deepgram
# Streams audio chunks and receives transcriptions
```

**Keyboard Control:**
```python
# See: src/automation/macos_control.py
# Uses Quartz framework for low-level keyboard events
# Supports modifier keys and special keys
```

**Command Matching:**
```python
# See: src/commands/parser.py
# Uses FuzzyWuzzy for fuzzy string matching
# Handles variations in spoken commands
```

## Community & Support

**Deepgram Community:**
- [Deepgram Discord](https://discord.gg/xWRyCt94PR) - Community chat
- [Deepgram GitHub](https://github.com/deepgram) - Open source repos
- [Stack Overflow](https://stackoverflow.com/questions/tagged/deepgram) - Q&A

**Python Community:**
- [Python Discord](https://discord.gg/python) - Python community
- [Stack Overflow (Python)](https://stackoverflow.com/questions/tagged/python) - Q&A
- [Python Forum](https://discuss.python.org/) - Discussion board

**macOS Development:**
- [Apple Developer](https://developer.apple.com/) - Official docs
- [macOS Automation Sub](https://www.reddit.com/r/MacOS/) - Reddit community

## Further Learning

**Voice Recognition:**
- [Speech Recognition Basics](https://en.wikipedia.org/wiki/Speech_recognition) - Overview
- [WebSocket Protocol](https://en.wikipedia.org/wiki/WebSocket) - Protocol info
- [Fuzzy Matching](https://en.wikipedia.org/wiki/Approximate_string_matching) - String matching

**macOS Automation:**
- [Keyboard Simulation](https://developer.apple.com/documentation/coregraphics/cgevent) - CGEvent
- [Process Management](https://developer.apple.com/documentation/foundation/nsworkspace) - App control
- [File Handling](https://developer.apple.com/documentation/foundation/filemanager) - File ops

**DevOps & Deployment:**
- [launchd Configuration](https://www.launchd.info/) - Daemon setup
- [Log Management](https://support.apple.com/guide/system-log-utility/welcome/mac) - Logging
- [Environment Variables](https://en.wikipedia.org/wiki/.bashrc) - Env setup

## Troubleshooting Resources

- **Audio Issues**: Check System Preferences → Sound
- **Microphone Access**: System Preferences → Security & Privacy → Microphone
- **API Issues**: Check [Deepgram Status](https://status.deepgram.com/)
- **Code Issues**: Check GitHub issues or Stack Overflow
- **macOS Issues**: Check Apple Support

## License & Attribution

This project uses:
- **Deepgram API** - Speech-to-text service
- **PyAudio** - Audio I/O (MIT/PSF)
- **PyObjC** - Python-Objective C bridge (MIT)
- **FuzzyWuzzy** - String matching (MIT)
- **Click** - CLI framework (BSD)
- **Pydantic** - Data validation (MIT)
- **PyYAML** - YAML parser (MIT)

See individual project pages for detailed licensing information.

---

**Have a question?** Check the relevant documentation section above or open an issue on GitHub.

**Found a bug?** Check if it's already reported or open a new issue.

**Want to contribute?** Pull requests are welcome!

