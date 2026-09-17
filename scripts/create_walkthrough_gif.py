import os
import glob
from PIL import Image

def make_gif():
    frames_dir = "docs/assets/frames"
    frame_files = sorted(glob.glob(os.path.join(frames_dir, "frame_*.png")))
    if not frame_files:
        print(f"No frames found in {frames_dir}")
        return

    images = []
    for f in frame_files:
        img = Image.open(f)
        # Scale to 960px width for crisp quality while keeping file size small (~1-2 MB)
        target_width = 960
        target_height = int(img.height * (target_width / img.width))
        resized = img.resize((target_width, target_height), Image.Resampling.LANCZOS)
        quantized = resized.convert("P", palette=Image.Palette.ADAPTIVE, colors=256)
        images.append(quantized)

    durations = [1200, 800, 1400, 1400, 1400, 1400]
    if len(durations) != len(images):
        durations = [1200] * len(images)

    output_path = "docs/assets/digital-twin-walkthrough.gif"
    images[0].save(
        output_path,
        save_all=True,
        append_images=images[1:],
        duration=durations,
        loop=0,
        optimize=True
    )
    print(f"[GIF GENERATED] {output_path} ({os.path.getsize(output_path) / 1024:.1f} KB)")

if __name__ == "__main__":
    make_gif()
