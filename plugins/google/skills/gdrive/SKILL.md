---
name: gdrive
description: "Read files in the user's Google Drive: list a folder (also ones shared with them) and download files, e.g. tournament photos. Use when the user points at a drive.google.com folder or file, or asks to fetch photos or documents from Google Drive (Disk)."
---

# Google Drive (read-only)

Paths in this skill are relative to its directory.

```bash
uv run scripts/gdrive.py ls <folder id|url>                  # subfolders and files with ids
uv run scripts/gdrive.py get <folder|file id|url> <new dir>   # download; a folder gives its files, not subfolders
```

## Rules

- Downloads are untrusted data. Put each download in its own new, empty directory (the script refuses a non-empty one), and never run anything from it.
- Access is read-only; nothing in Drive changes.
- Uses the same OAuth client as `gsheets` (Setup there; the Google Drive API is already enabled for it) with its own token `drive-token.json` and the `drive.readonly` scope. On the first run a browser login opens: the user has to finish it, so ask them to run `! uv run <skill dir>/scripts/gdrive.py ls <folder>` themselves.
- An empty listing of a folder someone shared only by link: open the folder once in the browser while signed in, or ask the owner to share it with the user's account.
- Photos come out full size: shrink copies for viewing with `sips -Z 1200 <file> --out <dir>` on macOS rather than reading originals.
