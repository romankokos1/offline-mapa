#!/usr/bin/env python3
"""
Stáhne dlaždice OSM/Freemap Outdoor pro zadaný výřez a rozsah zoomů
a uloží je do tiles/{z}/{x}/{y}.png (formát, který čeká index.html).

Spouští se z GitHub Actions — žádná instalace u tebe není potřeba.
Pro jinou trasu stačí upravit BBOX níže (nebo hodnoty přepsat proměnnými
prostředí BBOX_SOUTH/NORTH/WEST/EAST/ZOOM_MIN/ZOOM_MAX ve workflow souboru).
"""
import math
import os
import time
import urllib.request

TILE_URL = "https://outdoor.tiles.freemap.sk/{z}/{x}/{y}"
OUT_DIR = "tiles"

# Výchozí výřez — trasa Bohnice–Troja s malou rezervou.
BBOX_SOUTH = float(os.environ.get("BBOX_SOUTH", "50.144"))
BBOX_NORTH = float(os.environ.get("BBOX_NORTH", "50.162"))
BBOX_WEST = float(os.environ.get("BBOX_WEST", "14.351"))
BBOX_EAST = float(os.environ.get("BBOX_EAST", "14.401"))
ZOOM_MIN = int(os.environ.get("ZOOM_MIN", "12"))
ZOOM_MAX = int(os.environ.get("ZOOM_MAX", "17"))

HEADERS = {"User-Agent": "offline-mapa-tile-downloader/1.0 (osobni turisticka mapa)"}


def latlon_to_tile(lat, lon, z):
    lat_rad = math.radians(lat)
    n = 2 ** z
    x = int((lon + 180.0) / 360.0 * n)
    y = int((1.0 - math.log(math.tan(lat_rad) + 1 / math.cos(lat_rad)) / math.pi) / 2.0 * n)
    return x, y


def main():
    total = 0
    downloaded = 0
    skipped = 0

    for z in range(ZOOM_MIN, ZOOM_MAX + 1):
        x1, y1 = latlon_to_tile(BBOX_NORTH, BBOX_WEST, z)
        x2, y2 = latlon_to_tile(BBOX_SOUTH, BBOX_EAST, z)
        x_min, x_max = min(x1, x2), max(x1, x2)
        y_min, y_max = min(y1, y2), max(y1, y2)

        for x in range(x_min, x_max + 1):
            for y in range(y_min, y_max + 1):
                total += 1
                out_path = os.path.join(OUT_DIR, str(z), str(x), f"{y}.png")
                if os.path.exists(out_path):
                    skipped += 1
                    continue
                os.makedirs(os.path.dirname(out_path), exist_ok=True)
                url = TILE_URL.format(z=z, x=x, y=y)
                req = urllib.request.Request(url, headers=HEADERS)
                try:
                    with urllib.request.urlopen(req, timeout=15) as resp:
                        data = resp.read()
                    with open(out_path, "wb") as f:
                        f.write(data)
                    downloaded += 1
                    print(f"OK  z{z}/{x}/{y}")
                except Exception as e:
                    print(f"FAIL z{z}/{x}/{y}: {e}")
                # Slušné tempo, ať zbytečně nezatěžujeme veřejný tile server.
                time.sleep(0.1)

    print(f"\nHotovo. Celkem {total} dlaždic, staženo {downloaded}, přeskočeno (už existovaly) {skipped}.")


if __name__ == "__main__":
    main()
