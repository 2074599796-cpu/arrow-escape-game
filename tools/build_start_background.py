"""把用户提供的竖版海报处理为 860×760 的游戏开始页背景。"""

from pathlib import Path

from PIL import Image, ImageEnhance, ImageFilter, ImageOps

PROJECT_ROOT = Path(__file__).resolve().parents[1]
ASSET_DIR = PROJECT_ROOT / "assets"
SOURCE = ASSET_DIR / "start_background_source.jpg"
OUTPUT = ASSET_DIR / "start_background.png"
SIZE = (860, 760)


def main() -> None:
    source = Image.open(SOURCE).convert("RGB")

    # 用暗化、模糊的同图填满横屏两侧，避免拉伸人物。
    backdrop = ImageOps.fit(source, SIZE, method=Image.Resampling.LANCZOS, centering=(0.5, 0.38))
    backdrop = backdrop.filter(ImageFilter.GaussianBlur(18))
    backdrop = ImageEnhance.Brightness(backdrop).enhance(0.42).convert("RGBA")

    # 中央完整保留竖版海报，不裁掉人物与书法。
    poster = source.copy()
    poster.thumbnail((SIZE[0], SIZE[1]), Image.Resampling.LANCZOS)
    x = (SIZE[0] - poster.width) // 2
    y = (SIZE[1] - poster.height) // 2
    backdrop.alpha_composite(poster.convert("RGBA"), (x, y))

    # 底部渐暗，为游戏标题、说明和按钮留出清晰区域。
    gradient = Image.new("RGBA", SIZE, (0, 0, 0, 0))
    pixels = gradient.load()
    start_y = 430
    for row in range(start_y, SIZE[1]):
        alpha = round(70 + 185 * (row - start_y) / (SIZE[1] - start_y))
        for col in range(SIZE[0]):
            pixels[col, row] = (5, 10, 8, alpha)
    backdrop = Image.alpha_composite(backdrop, gradient)
    backdrop.save(OUTPUT, optimize=True)
    print(f"Generated: {OUTPUT}")


if __name__ == "__main__":
    main()
