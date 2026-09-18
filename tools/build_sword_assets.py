"""从透明飞剑原图生成游戏运行时使用的四方向 PNG 素材。"""

from pathlib import Path

from PIL import Image

PROJECT_ROOT = Path(__file__).resolve().parents[1]
ASSET_DIR = PROJECT_ROOT / "assets"
SOURCE = ASSET_DIR / "flying_sword_source.png"
TILE_SIZE = 76
CONTENT_SIZE = 72


def fit_to_tile(source: Image.Image) -> Image.Image:
    rgba = source.convert("RGBA")
    alpha_box = rgba.getchannel("A").getbbox()
    if alpha_box is None:
        raise ValueError("飞剑源图没有可见像素")
    cropped = rgba.crop(alpha_box)
    cropped.thumbnail((CONTENT_SIZE, CONTENT_SIZE), Image.Resampling.LANCZOS)
    tile = Image.new("RGBA", (TILE_SIZE, TILE_SIZE), (0, 0, 0, 0))
    tile.alpha_composite(cropped, ((TILE_SIZE - cropped.width) // 2, (TILE_SIZE - cropped.height) // 2))
    return tile


def main() -> None:
    down = fit_to_tile(Image.open(SOURCE))
    directions = {
        "down": down,
        "up": down.rotate(180, resample=Image.Resampling.BICUBIC),
        "right": down.rotate(90, resample=Image.Resampling.BICUBIC),
        "left": down.rotate(-90, resample=Image.Resampling.BICUBIC),
    }
    for name, image in directions.items():
        image.save(ASSET_DIR / f"sword_{name}.png", optimize=True)
    print("Generated:", ", ".join(f"sword_{name}.png" for name in directions))


if __name__ == "__main__":
    main()
