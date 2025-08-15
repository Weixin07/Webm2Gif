"""
WEBM → GIF (high quality) using ImageMagick + ffmpeg.

Requirements (Ubuntu):
  sudo apt update
  sudo apt install -y imagemagick   # provides `magick` (IM7) or `convert` (IM6)
  pip install imageio-ffmpeg        # we use its bundled ffmpeg

Usage:
  Run, pick a .webm, choose where to save .gif, set FPS and (optional) max width.
"""

import os
import sys
import subprocess
import tempfile
from shutil import which
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog
import imageio_ffmpeg as iioff


# Default directory for the file dialog
DEFAULT_DIR = os.path.expanduser("/home/faith/Videos/Screencasts")


def ask_number(title, prompt, initialvalue, minval, maxval, integer=False):
    """Ask for a number via Tk dialog; blank = None."""
    while True:
        val = simpledialog.askstring(title, prompt, initialvalue=str(initialvalue))
        if val is None:
            return None
        val = val.strip()
        if val == "":
            return None
        try:
            num = int(val) if integer else float(val)
            if num < minval or num > maxval:
                messagebox.showerror(
                    title, f"Enter a value between {minval} and {maxval}."
                )
                continue
            return int(num) if integer else num
        except ValueError:
            messagebox.showerror(title, "Please enter a valid number.")


def _find_imagemagick():
    """
    Prefer IM7 `magick`; fallback to IM6 `convert`.
    (We avoid GraphicsMagick on purpose.)
    """
    magick = which("magick")
    if magick:
        return magick
    convert = which("convert")
    if convert:
        return convert
    return None


def make_gif_im(in_path, out_path, fps, max_w=None, dither="FloydSteinberg"):
    """
    High-quality GIF via:
      1) ffmpeg → frames (fps/scale/rgba)
      2) ffmpeg → palette.png (global)
      3) ImageMagick → assemble frames with -remap palette and chosen dithering

    Notes:
      - `max_w` is optional. If provided, we *avoid upscaling* using a conditional scaler.
      - Good dithers for UI/text: "Riemersma" (smooth), "FloydSteinberg" (classic).
    """
    ffmpeg = iioff.get_ffmpeg_exe()
    im = _find_imagemagick()
    if not im:
        raise RuntimeError(
            "ImageMagick not found. Install it (e.g., `sudo apt install -y imagemagick`)."
        )

    # Build the video filter chain:
    # fps -> (optional) scale with no-upscale -> RGBA for consistent palette
    filters = [f"fps={int(fps)}"]
    if max_w:
        # Conditional scale to avoid upscaling:
        # width = if(iw > max_w) max_w else iw
        filters.append(
            f"scale=if(gt(iw\\,{int(max_w)})\\,{int(max_w)}\\,iw):-1:flags=lanczos"
        )
    filters.append("format=rgba")
    vf = ",".join(filters)

    # IM delay is in 1/100s per frame
    delay_cs = max(1, round(100 / float(fps)))

    # Run commands with captured stderr for nice error messages
    run_kwargs = dict(
        check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
    )

    with tempfile.TemporaryDirectory() as td:
        frames_pat = os.path.join(td, "f_%06d.png")
        frames_glob = os.path.join(td, "f_*.png")
        palette = os.path.join(td, "palette.png")

        # 1) Extract frames
        cmd1 = [ffmpeg, "-y", "-i", in_path, "-vf", vf, frames_pat]
        p1 = subprocess.run(cmd1, **run_kwargs)

        # 2) Build a global palette (reduces flicker)
        cmd2 = [
            ffmpeg,
            "-y",
            "-i",
            in_path,
            "-vf",
            f"{vf},palettegen=stats_mode=full",
            palette,
        ]
        p2 = subprocess.run(cmd2, **run_kwargs)

        # 3) Assemble with ImageMagick using the palette and nice dithering
        # Use shell so the f_*.png glob expands.
        # IM7 and IM6 accept: -delay, -loop, -remap, -dither, -layers OptimizeTransparency
        assemble_cmd = (
            f'"{im}" -delay {delay_cs} -loop 0 '
            f'"{frames_glob}" -remap "{palette}" -dither {dither} '
            f'-layers OptimizeTransparency "{out_path}"'
        )
        p3 = subprocess.run(assemble_cmd, shell=True, **run_kwargs)

        # If we reach here, success.


def main():
    root = tk.Tk()
    root.withdraw()

    messagebox.showinfo("WEBM → GIF", "Select a .webm video to convert to GIF.")

    # 1) Pick input
    in_path = filedialog.askopenfilename(
        title="Select a WEBM file",
        filetypes=[("WEBM video", "*.webm"), ("All files", "*.*")],
        initialdir=(
            DEFAULT_DIR if os.path.isdir(DEFAULT_DIR) else os.path.expanduser("~")
        ),
    )
    if not in_path:
        return

    if not in_path.lower().endswith(".webm"):
        if not messagebox.askyesno(
            "Continue?", "Selected file is not .webm. Continue anyway?"
        ):
            return

    # 2) Save target
    base = os.path.splitext(os.path.basename(in_path))[0]
    suggested = base + ".gif"
    out_path = filedialog.asksaveasfilename(
        title="Save GIF as...",
        defaultextension=".gif",
        initialfile=suggested,
        filetypes=[("GIF image", "*.gif")],
        initialdir=os.path.dirname(in_path),
    )
    if not out_path:
        return

    # 3) Settings
    fps = ask_number(
        "Frames per Second",
        "Enter GIF FPS (8–24). Higher = smoother and larger file.\n(Leave blank to use 15)",
        initialvalue=15,
        minval=1,
        maxval=60,
        integer=True,
    )
    if fps is None:
        fps = 15

    max_w = ask_number(
        "Max Width (optional)",
        "Enter a max width in pixels (e.g., 480 or 720).\nLeave blank to keep original size.",
        initialvalue="",
        minval=32,
        maxval=4096,
        integer=True,
    )

    # 4) Convert
    try:
        messagebox.showinfo(
            "Converting", "Conversion started. This may take a little while."
        )
        make_gif_im(
            in_path,
            out_path,
            fps=fps,
            max_w=max_w,  # conditional scaler avoids upscaling
            dither="Riemersma",  # try "FloydSteinberg" if you prefer
        )
        messagebox.showinfo("Done", f"GIF saved:\n{out_path}")

        # 5) Open folder?
        try:
            folder = os.path.dirname(out_path)
            if messagebox.askyesno("Open Folder?", "Open the output folder?"):
                if os.name == "nt":
                    os.startfile(folder)  # type: ignore[attr-defined]
                elif sys.platform == "darwin":
                    subprocess.run(["open", folder])
                else:
                    subprocess.run(["xdg-open", folder])
        except Exception:
            pass

    except subprocess.CalledProcessError as e:
        msg = e.stderr.strip() if e.stderr else str(e)
        messagebox.showerror("Error", f"Conversion failed:\n{msg}")
    except Exception as e:
        messagebox.showerror("Error", f"Conversion failed:\n{e}")


if __name__ == "__main__":
    main()
