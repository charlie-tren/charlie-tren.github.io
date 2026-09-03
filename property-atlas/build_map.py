"""Turn Natural Earth's 110m topology into a compact world geojson for the map.

Downloaded once at build time rather than fetched by the page: the page is
static and a runtime CDN call is a dependency it does not need. The output is a
grey basemap of every country plus an `id` on the thirty-four the screener
covers, so the map can colour them without a second file.

Coordinates are rounded to two decimals, which is about a kilometre at the
equator. At the size this map is drawn a finer coordinate is invisible, and
rounding is most of the size saving.

    python build_map.py            # expects world-110m.json beside it
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).parent
TOPO = HERE / "source" / "world-110m.json"
OUT = HERE / "world.json"
DATA = HERE / "data.json"

# Natural Earth's names against the workbook's. Only the ones that differ.
ALIAS = {
    "United States of America": "United States",
    "Bosnia and Herz.": "Bosnia and Herzegovina",
    "Dominican Rep.": "Dominican Republic",
    "Macedonia": "North Macedonia",
    "North Macedonia": "North Macedonia",
    "Czechia": "Czech Republic",
    "United Arab Emirates": "United Arab Emirates",
    "Italy": "Italy (South)",
}


# Natural Earth's 110m set leaves out microstates, so two markets have no
# polygon at any resolution this file uses. They get a marker instead of being
# silently absent from a map that claims to show every market.
POINTS = {
    "Bahrain": [50.55, 26.03],
    "Mauritius": [57.57, -20.27],
}


def decode(topo):
    """topojson -> {name: [rings]} in lon/lat. Quantised deltas, so arcs
    accumulate; a negative arc index means traverse that arc backwards."""
    tr = topo["transform"]
    sx, sy = tr["scale"]
    tx, ty = tr["translate"]

    arcs = []
    for arc in topo["arcs"]:
        x = y = 0
        out = []
        for dx, dy in arc:
            x += dx
            y += dy
            out.append([round(x * sx + tx, 2), round(y * sy + ty, 2)])
        arcs.append(out)

    def ring(idxs):
        pts = []
        for i in idxs:
            a = arcs[~i][::-1] if i < 0 else arcs[i]
            pts.extend(a[1:] if pts else a)
        return pts

    shapes = {}
    for g in topo["objects"]["countries"]["geometries"]:
        name = (g.get("properties") or {}).get("name")
        if not name:
            continue
        polys = []
        if g["type"] == "Polygon":
            polys = [g["arcs"]]
        elif g["type"] == "MultiPolygon":
            polys = [p for p in g["arcs"]]
        else:
            continue
        rings = []
        for poly in polys:
            for r in poly:
                pts = ring(r)
                # Drop specks. At this scale an island under ~0.35 square
                # degrees of bounding box is a pixel or less and only costs
                # bytes; the mainland of every country here survives it.
                xs = [p[0] for p in pts]
                ys = [p[1] for p in pts]
                span = max(xs) - min(xs)
                # A ring spanning more than half the globe has wrapped the
                # antimeridian. Drawn flat it becomes a band straight across the
                # map, which is what Russia's eastern tip and Fiji did. Each
                # ring is separate, so dropping the wrapped one costs a far
                # island, not the country.
                if span > 180:
                    continue
                if len(pts) < 4 or span * (max(ys) - min(ys)) < 0.35:
                    continue
                rings.append(pts)
        if rings:
            shapes[name] = rings
    return shapes


def main():
    if not TOPO.exists():
        sys.exit(f"missing {TOPO}. Download countries-110m.json into source/ first.")
    shapes = decode(json.loads(TOPO.read_text(encoding="utf-8")))
    wanted = {c["country"] for c in json.loads(DATA.read_text(encoding="utf-8"))["countries"]}

    feats = []
    matched = set()
    for name, rings in sorted(shapes.items()):
        market = ALIAS.get(name, name)
        hit = market in wanted
        if hit:
            matched.add(market)
        feats.append({"n": name, "m": market if hit else None, "r": rings})

    points = [{"m": k, "p": v} for k, v in POINTS.items() if k in wanted]
    matched.update(p["m"] for p in points)

    OUT.write_text(json.dumps({"features": feats, "points": points}, separators=(",", ":")), encoding="utf-8")
    print(f"{len(feats)} shapes -> {OUT.name} ({OUT.stat().st_size // 1024}KB)")
    print(f"matched {len(matched)} of {len(wanted)} markets")
    missing = sorted(wanted - matched)
    if missing:
        print("NOT ON THE MAP:", ", ".join(missing))


if __name__ == "__main__":
    main()
