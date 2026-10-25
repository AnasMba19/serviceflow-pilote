"""Relief de Paris et de la petite couronne (ombrage) a partir des Terrain Tiles (AWS Open Data, Mapzen).
Produit data/relief.webp (ombres en transparence, a poser sur un fond sombre) et data/relief.json (coins geographiques).
Execute par la GitHub Action, qui a acces a Internet."""
import io, json, math, urllib.request
import numpy as np
from PIL import Image

Z = 13
LON = (2.19, 2.47)
LAT = (48.78, 48.93)
URL = 'https://s3.amazonaws.com/elevation-tiles-prod/terrarium/{z}/{x}/{y}.png'

def tile_x(lon): return int((lon + 180) / 360 * 2 ** Z)
def tile_y(lat):
    r = math.radians(lat)
    return int((1 - math.log(math.tan(r) + 1 / math.cos(r)) / math.pi) / 2 * 2 ** Z)
def lon_of(x): return x / 2 ** Z * 360 - 180
def lat_of(y): return math.degrees(math.atan(math.sinh(math.pi * (1 - 2 * y / 2 ** Z))))

x0, x1 = tile_x(LON[0]), tile_x(LON[1])
y0, y1 = tile_y(LAT[1]), tile_y(LAT[0])
rows = []
for y in range(y0, y1 + 1):
    row = []
    for x in range(x0, x1 + 1):
        with urllib.request.urlopen(URL.format(z=Z, x=x, y=y), timeout=30) as r:
            a = np.asarray(Image.open(io.BytesIO(r.read())).convert('RGB'), dtype=np.float64)
        row.append(a[:, :, 0] * 256 + a[:, :, 1] + a[:, :, 2] / 256 - 32768)
    rows.append(np.hstack(row))
elev = np.vstack(rows)

# Taille d'un pixel au sol (metres) a la latitude moyenne, puis ombrage classique (soleil au nord-ouest, 45 degres).
lat_mid = math.radians((LAT[0] + LAT[1]) / 2)
px = 40075016.686 * math.cos(lat_mid) / (2 ** Z * 256)
exag = 6.0
dzdy, dzdx = np.gradient(elev * exag, px)
slope = np.arctan(np.hypot(dzdx, dzdy))
aspect = np.arctan2(-dzdx, dzdy)
az, alt = math.radians(315), math.radians(45)
shade = np.sin(alt) * np.cos(slope) + np.cos(alt) * np.sin(slope) * np.cos(az - aspect)
shade = np.clip(shade, 0, 1)
flat = math.sin(alt)
dark = np.clip((flat - shade) / flat, 0, 1)          # versants a l'ombre
light = np.clip((shade - flat) / (1 - flat), 0, 1)   # versants au soleil
rgba = np.zeros(elev.shape + (4,), dtype=np.uint8)
rgba[..., 0:3] = np.where(light[..., None] > dark[..., None], 255, 0)
rgba[..., 3] = (np.maximum(dark * 200, light * 90)).astype(np.uint8)
Image.fromarray(rgba, 'RGBA').save('data/relief.webp', 'WEBP', quality=72, method=6)

west, east = lon_of(x0), lon_of(x1 + 1)
north, south = lat_of(y0), lat_of(y1 + 1)
json.dump({
    'source': 'Terrain Tiles, AWS Open Data (Mapzen ; SRTM, EU-DEM et autres sources publiques)',
    'zoom': Z, 'exageration': exag, 'altitude_min': round(float(elev.min()), 1), 'altitude_max': round(float(elev.max()), 1),
    'coordinates': [[west, north], [east, north], [east, south], [west, south]],
}, open('data/relief.json', 'w'), indent=1)
print('relief', elev.shape, round(float(elev.min()), 1), round(float(elev.max()), 1))
