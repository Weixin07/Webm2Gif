# WebM → GIF (High-Quality GUI Converter)

Small, cross-platform Python utility that converts `.webm` screen recordings to high-quality animated GIFs using **FFmpeg** (via `imageio-ffmpeg`) and **ImageMagick**. Includes single-file mode and an optional **batch folder** mode.

---

## Features

- **High-quality pipeline**: two-pass global palette + good dithering (Riemersma / Floyd-Steinberg) for crisp UI text.
- **Batch folder mode**: convert all `.webm` in a directory in one go.
- **No-upscale scaling**: conditionally resizes (Lanczos) while avoiding blur from upscaling.
- **GUI prompts**: file/folder pickers, FPS & max-width dialogs, and clear error popups.
- ** sensible defaults**: infinite loop, RGBA palette generation, and a configurable default start directory.

---

## Requirements

- **OS**: Ubuntu 22.04+ (others likely fine)
- **System tools**: ImageMagick (`magick` or `convert`)
- **Python**: 3.10+ with Tk (for dialogs)
- **Python packages**: `imageio-ffmpeg` (bundled FFmpeg binary)

Install prerequisites (Ubuntu):

```bash
sudo apt update
sudo apt install -y imagemagick python3 python3-pip python3-tk python3-venv
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install imageio-ffmpeg
```
