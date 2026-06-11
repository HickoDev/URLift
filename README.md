<p align="center">
  <img src="Logo.png" alt="URLift logo" width="180">
</p>

# URLift

URLift is a Windows desktop app for downloading authorized or public media from supported platforms. Paste a URL, choose a platform hint, choose video or audio output, select a quality or format, pick an output folder, and download with progress tracking.

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

`build.bat` uses `assets\icon.ico` when that file exists. If it is missing, the script builds without a custom icon. To add a custom app icon, place a Windows `.ico` file at `assets\icon.ico` and run `build.bat` again.

## FFmpeg On Windows

FFmpeg must be installed and available on `PATH` for MP3 extraction, M4A extraction, and MP4 merging.

One common setup:

1. Download a Windows FFmpeg build from https://ffmpeg.org/download.html.
2. Extract it to a stable folder such as `C:\ffmpeg`.
3. Add `C:\ffmpeg\bin` to your Windows `PATH`.
4. Open a new terminal and verify:

```bat
ffmpeg -version
```

If FFmpeg is missing, URLift will show `FFmpeg missing`.

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

