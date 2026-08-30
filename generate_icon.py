"""
generate_icon.py - Luo korkearesoluutioisen modernin sovellusikonin (icon.ico ja icon.png)
"""

import math
import os
from PIL import Image, ImageDraw


def create_browser_icon():
    size = 512
    # Läpinäkyvä pohja
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # 1. Pyöristetty taustalaatikko / liukuväriheijastus
    margin = 24
    radius = 120
    
    # Liukuväri-tausta (syvä yönsininen -> violetti)
    for y in range(margin, size - margin):
        factor = (y - margin) / (size - 2 * margin)
        r = int(24 * (1 - factor) + 75 * factor)
        g = int(32 * (1 - factor) + 40 * factor)
        b = int(72 * (1 - factor) + 160 * factor)
        draw.line([(margin, y), (size - margin, y)], fill=(r, g, b, 255))

    # Maskataan pyöristetyksi neliöksi
    mask = Image.new("L", (size, size), 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.rounded_rectangle([margin, margin, size - margin, size - margin], radius=radius, fill=255)
    img.putalpha(mask)

    # Piirretään päälle grafiikka
    draw = ImageDraw.Draw(img)

    # 2. Ulkoreunus / hehku
    draw.rounded_rectangle(
        [margin, margin, size - margin, size - margin],
        radius=radius,
        outline=(110, 140, 255, 180),
        width=6,
    )

    center_x, center_y = size // 2, size // 2

    # 3. Hohtava pallo / maapallo (Sini-turkoosi liukuväri)
    globe_radius = 140
    for r_i in range(globe_radius, 0, -2):
        f = r_i / globe_radius
        # Keskusta vaaleampi turkoosi, reunat syvempi sininen
        cr = int(67 * f + 90 * (1 - f))
        cg = int(97 * f + 200 * (1 - f))
        cb = int(238 * f + 255 * (1 - f))
        draw.ellipse(
            [center_x - r_i, center_y - r_i, center_x + r_i, center_y + r_i],
            fill=(cr, cg, cb, 255),
        )

    # 4. Kiertoradat / renkaat (Orbit rings)
    ring_color = (255, 255, 255, 220)
    draw.arc(
        [center_x - 170, center_y - 80, center_x + 170, center_y + 80],
        start=20,
        end=200,
        fill=ring_color,
        width=8,
    )
    draw.arc(
        [center_x - 170, center_y - 80, center_x + 170, center_y + 80],
        start=220,
        end=360,
        fill=(255, 255, 255, 120),
        width=6,
    )

    # 5. Tyylikäs kompassi / salama / navigointikolmio keskelle
    triangle = [
        (center_x, center_y - 85),          # Yläkärki
        (center_x + 45, center_y + 55),     # Oikea alakulma
        (center_x, center_y + 25),          # Keskipainauma
    ]
    draw.polygon(triangle, fill=(255, 255, 255, 255))

    triangle_left = [
        (center_x, center_y - 85),          # Yläkärki
        (center_x, center_y + 25),          # Keskipainauma
        (center_x - 45, center_y + 55),     # Vasen alakulma
    ]
    draw.polygon(triangle_left, fill=(210, 225, 255, 240))

    # Tallenna PNG (512x512)
    png_path = os.path.join(os.path.dirname(__file__), "icon.png")
    img.save(png_path, format="PNG")
    print(f"Tallennettu: {png_path}")

    # Tallenna moniresoluutioinen ICO Windowsille
    ico_path = os.path.join(os.path.dirname(__file__), "icon.ico")
    icon_sizes = [(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)]
    img.save(ico_path, format="ICO", sizes=icon_sizes)
    print(f"Tallennettu moniresoluutioinen ICO: {ico_path}")


if __name__ == "__main__":
    create_browser_icon()
