<p align="center">
  <img src="Logo.png" alt="URLift logo" width="180">
</p>

# URLift

URLift is a Windows desktop app for downloading authorized or public media from supported platforms. Paste a URL, choose a platform hint, choose video or audio output, select a quality or format, pick an output folder, and download with progress tracking.

## Download

Download the latest Windows build from GitHub Releases:

[Download URLift.exe](https://github.com/HickoDev/URLift/releases/latest)

URLift uses:

- Python and PySide6 for the desktop interface
- yt-dlp for public media extraction
- FFmpeg for audio extraction and video/audio merging
- SQLite for local download history
- PyInstaller for Windows `.exe` packaging

## Legal And Safety Notice

URLift is intended only for downloading:

- your own content
- royalty-free content
- public content you have permission to download

Do not use URLift to bypass DRM, paid access, private accounts, login walls, or platform restrictions. URLift does not include credentials, DRM bypassing, private account access, or restriction bypass features.

## Supported Platform Hints

- YouTube
- TikTok
- Instagram
- Facebook
- Other / Auto-detect

The platform dropdown is mainly for UX validation and help text. Actual extraction is handled by yt-dlp whenever possible.

## Install

```bat
pip install -r requirements.txt
```

## Run In Development

```bat
python main.py
```

## Build Windows Executable

```bat
build.bat
```

The packaged app is created at:

```text
dist/URLift.exe
```

`build.bat` uses `assets\icon.ico` for the Windows app icon and bundles `Logo.png` for the in-app header.

## Build Windows Installer

URLift includes an optional Inno Setup script. First build the executable:

```bat
build.bat
```

Then install Inno Setup and run:

```bat
build_installer.bat
```

The installer is created at:

```text
dist/URLift-Setup.exe
```

To validate the installer files without Inno Setup:

```bat
build_installer.bat --check
```

## FFmpeg On Windows

URLift uses a portable FFmpeg dependency when installed from `requirements.txt` or packaged with `build.bat`. If you prefer to use your own FFmpeg installation, install FFmpeg and make it available on `PATH`.

One common setup:

1. Download a Windows FFmpeg build from https://ffmpeg.org/download.html.
2. Extract it to a stable folder such as `C:\ffmpeg`.
3. Add `C:\ffmpeg\bin` to your Windows `PATH`.
4. Open a new terminal and verify:

```bat
ffmpeg -version
```

If neither the bundled portable FFmpeg nor a system FFmpeg can be found, URLift will show `FFmpeg missing`.

## Download History

URLift stores local download history in SQLite under the current user's app data folder. History includes the platform, original URL, title, output type, selected quality or format, saved file path, extension, date/time, status, and any error message.

The History tab supports:

- Open file
- Open folder
- Copy original URL
- Remove item from history
- Clear all history

## Notes

Some platforms may fail if they change their systems, restrict access, require login, block automation, or remove public availability. URLift intentionally does not bypass those restrictions.
