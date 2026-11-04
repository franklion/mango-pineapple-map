#!/usr/bin/env python3
"""
芒果鳳梨散步地圖：地圖資料打包工具

用法：
  python3 build_map_data.py region <key> <minLon,minLat,maxLon,maxLat> [更多 bbox ...]
  python3 build_map_data.py fonts

- region：下載 OpenFreeMap 向量圖磚（z12–14），只保留地圖樣式會用到的圖層與 POI 類別，
  gzip + base64 後寫入 map/<key>.json。同一地區的多趟旅程共用同一個 key。
- fonts：下載拉丁字形（中文由瀏覽器本機字型繪製），寫入 map/fonts.json，所有旅程共用。
需要網域 tiles.openfreemap.org 在允許清單中。
"""
import base64, gzip, json, math, os, sys, urllib.request

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "public", "map")
KEEP_LAYERS = {"water", "waterway", "landuse", "landcover", "park", "building",
               "transportation", "transportation_name", "water_name", "poi", "place"}
POI_CLASSES = {b"park", b"school", b"college", b"railway", b"attraction", b"zoo",
               b"library", b"town_hall", b"stadium"}
PLACE_CLASSES = {b"city", b"town", b"village", b"hamlet", b"suburb", b"neighbourhood", b"quarter"}
FONT_RANGES = ["0-255", "8192-8447", "12288-12543", "65280-65535"]
FONTS = {"NotoSansRegular": "Noto Sans Regular", "NotoSansBold": "Noto Sans Bold"}


# ---- 最小化的 protobuf 讀寫，用來在不重新編碼幾何的情況下過濾圖層與要素 ----
def varint(buf, i):
    shift = res = 0
    while True:
        b = buf[i]; i += 1
        res |= (b & 0x7F) << shift
        if b < 0x80: return res, i
        shift += 7

def enc_varint(n):
    out = bytearray()
    while True:
        b = n & 0x7F; n >>= 7
        out.append(b | (0x80 if n else 0))
        if not n: return bytes(out)

def fields(buf):
    """逐一回傳 (欄位編號, wire type, 值, 原始位元組)"""
    i = 0
    while i < len(buf):
        start = i
        key, i = varint(buf, i)
        fn, wt = key >> 3, key & 7
        if wt == 0: val, i = varint(buf, i)
        elif wt == 2:
            ln, i = varint(buf, i); val = buf[i:i + ln]; i += ln
        elif wt == 5: val = buf[i:i + 4]; i += 4
        elif wt == 1: val = buf[i:i + 8]; i += 8
        else: raise ValueError("unsupported wire type")
        yield fn, wt, val, buf[start:i]

def packed(buf):
    i, out = 0, []
    while i < len(buf):
        v, i = varint(buf, i); out.append(v)
    return out

def filter_layer(layer):
    parts = list(fields(layer))
    name = next(v for f, _, v, _ in parts if f == 1).decode()
    if name not in KEEP_LAYERS: return None
    allow = {"poi": POI_CLASSES, "place": PLACE_CLASSES}.get(name)
    if allow is None: return layer
    keys = [v for f, _, v, _ in parts if f == 3]
    values = []
    for f, _, v, _ in parts:
        if f == 4:
            s = next((vv for ff, _, vv, _ in fields(v) if ff == 1), None)
            values.append(s)
    cls_idx = keys.index(b"class") if b"class" in keys else -1
    out = bytearray()
    for f, _, v, raw in parts:
        if f == 2:
            tags = next((packed(vv) for ff, _, vv, _ in fields(v) if ff == 2), [])
            cls = None
            for k, val in zip(tags[::2], tags[1::2]):
                if k == cls_idx: cls = values[val]
            if cls not in allow: continue
        out += raw
    return bytes(out)

def slim_tile(data):
    out = bytearray()
    for f, _, v, raw in fields(data):
        if f == 3:
            layer = filter_layer(v)
            if layer is None: continue
            out += enc_varint((3 << 3) | 2) + enc_varint(len(layer)) + layer
        else:
            out += raw
    return bytes(out)


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "mango-pineapple-map/1.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        data = r.read()
    return gzip.decompress(data) if data[:2] == b"\x1f\x8b" else data

def tile_xy(lon, lat, z):
    n = 2 ** z
    x = int((lon + 180) / 360 * n)
    y = int((1 - math.asinh(math.tan(math.radians(lat))) / math.pi) / 2 * n)
    return x, y

def b64gz(b): return base64.b64encode(gzip.compress(b, 9)).decode()

def build_region(key, bboxes):
    tpl = json.loads(get("https://tiles.openfreemap.org/planet"))["tiles"][0]
    need = set()
    for b in bboxes:
        for z in (12, 13, 14):
            x0, y1 = tile_xy(b[0], b[1], z); x1, y0 = tile_xy(b[2], b[3], z)
            need |= {(z, x, y) for x in range(x0, x1 + 1) for y in range(y0, y1 + 1)}
    out, raw_total, slim_total = {}, 0, 0
    for z, x, y in sorted(need):
        data = get(tpl.format(z=z, x=x, y=y))
        slim = slim_tile(data)
        raw_total += len(data); slim_total += len(slim)
        out[f"{z}/{x}/{y}"] = b64gz(slim)
    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, f"{key}.json")
    json.dump(out, open(path, "w"), separators=(",", ":"))
    print(f"{key}: {len(out)} tiles, raw {raw_total//1024} KB -> slim {slim_total//1024} KB, file {os.path.getsize(path)//1024} KB")

def build_fonts():
    out = {}
    for short, full in FONTS.items():
        for r in FONT_RANGES:
            out[f"{short}/{r}"] = b64gz(get(f"https://tiles.openfreemap.org/fonts/{full.replace(' ', '%20')}/{r}.pbf"))
    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, "fonts.json")
    json.dump(out, open(path, "w"), separators=(",", ":"))
    print(f"fonts: {os.path.getsize(path)//1024} KB")

if __name__ == "__main__":
    if sys.argv[1] == "fonts": build_fonts()
    else: build_region(sys.argv[2], [tuple(map(float, b.split(","))) for b in sys.argv[3:]])
