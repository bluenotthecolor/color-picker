# ColorPicker

A small, lightweight screen color picker for Windows. Pick any pixel on any monitor and instantly get its HEX, RGB, and HSL values, ready to copy.

## Features

- **Pick any pixel** on any connected monitor, with correct handling of mixed display scaling across monitors
- **Live magnifier** — a zoomed loupe follows your cursor while picking, with the exact pixel highlighted, so you can aim precisely
- **HEX / RGB / HSL** values shown at once
- **One-click copy** of the hex code (copied without the `#`, ready to paste anywhere a bare color code is expected)
- **Lives in the system tray** — stays out of the way until you need it
- **Movable, frameless popup window** — drag it anywhere on screen

## Download

Grab the latest installer from the [Releases](../../releases) page — `ColorPicker-Setup.exe`. It's a standard Windows installer (built with [Inno Setup](https://jrsoftware.org/isinfo.php)): pick a folder, optionally add a desktop shortcut, and you're done. No Python installation required — everything needed is bundled inside.

To uninstall, use **Settings → Apps** like any other Windows program.

## Running from source

If you'd rather run it directly instead of using the installer:

```bash
pip install -r requirements.txt
python main.py
```

Requires Python 3.10+ on Windows.

## Building it yourself

The app is packaged with [PyInstaller](https://pyinstaller.org/) into a single standalone `.exe`, then wrapped in an Inno Setup installer.

**1. Build the executable:**

```bash
pip install -r requirements.txt
python build.py
```

This produces `dist\ColorPicker.exe` using the settings in `ColorPicker.spec`.

**2. Build the installer** (optional — only needed if you want a proper `Setup.exe` rather than the raw executable):

Install [Inno Setup](https://jrsoftware.org/isinfo.php), then open `ColorPicker.iss` in it and click **Compile** (or run `iscc ColorPicker.iss` from the command line). The finished installer lands in `installer-output\ColorPicker-Setup.exe`.

## Project structure

| File               | What it is                                                      |
| ------------------ | --------------------------------------------------------------- |
| `main.py`          | The application itself (PySide6 GUI, mss for screen capture)    |
| `build.py`         | PyInstaller build script                                        |
| `ColorPicker.spec` | PyInstaller build configuration                                 |
| `ColorPicker.iss`  | Inno Setup script that packages the built exe into an installer |
| `icon.ico`         | App icon                                                        |
| `requirements.txt` | Python dependencies (`PySide6`, `mss`)                          |

## Built with

- [PySide6](https://pypi.org/project/PySide6/) — GUI
- [mss](https://pypi.org/project/mss/) — fast, accurate screen capture across monitors

## License

MIT — see [LICENSE](LICENSE).
