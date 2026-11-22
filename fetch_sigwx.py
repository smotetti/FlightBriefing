#!/usr/bin/env python3
"""Downloads the newest Europe high-level SIGWX chart (SWH, EGRR PGDE15) from Meteo Aeronautica
and saves it as sigwx-eur.<ext> plus sigwx.json. Run by the GitHub Action after fetch_weather.py.
Standard library only. It never fails the Action: on any problem it prints a diagnosis and exits 0.
Test with:  python3 fetch_sigwx.py --seed   (downloads the one known chart, to test the download only)"""
import datetime
import json
import os
import re
import sys
import urllib.parse
import urllib.request

BASE = "https://cm.meteoam.it/content/published/api/v1.1"
TOKEN = "a41b6ce975f141c2859c6202515b13fd"
UA = "FlightBriefing-sigwx/1.0 (GitHub Action)"
MUST = ("AreaEUR", "PGDE15")          # words that must be in the chart file name
SEED = ("51963803-8fe0-4c5f-b9b6-26dc22c2cffd", "SWM-AreaEUR-PGDE15-EGRR-191800.gif")


def get(url, binary=False):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=60) as r:
            data = r.read()
        return data if binary else data.decode("utf-8", "replace")
    except Exception as e:
        print("warning: %s -> %s" % (url.split("?")[0], e))
        return None


def kind(data):
    if data[:4] == b"GIF8":
        return "gif"
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        return "png"
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "webp"
    if data[:3] == b"\xff\xd8\xff":
        return "jpg"
    return None


def list_charts():
    """Returns [(sortkey, id, name)] for all matching charts found in the channel."""
    found = {}
    for q in ('(name co "PGDE15")', '(name co "AreaEUR")'):
        url = BASE + "/items?" + urllib.parse.urlencode(
            {"channelToken": TOKEN, "q": q, "limit": 100, "fields": "all"}, quote_via=urllib.parse.quote)
        text = get(url)
        if not text:
            continue
        try:
            items = json.loads(text).get("items", [])
        except Exception:
            print("warning: answer was not JSON, first 300 characters:", text[:300])
            continue
        print("query %s -> %d items" % (q, len(items)))
        for it in items:
            name = it.get("name") or ""
            if all(w in name for w in MUST) and it.get("id"):
                upd = it.get("updatedDate") or it.get("createdDate") or {}
                upd = upd.get("value", "") if isinstance(upd, dict) else str(upd)
                found[it["id"]] = (upd, it["id"], name)
        if found:
            break
    return sorted(found.values())


def download(asset_id, name):
    q = "channelToken=" + TOKEN
    tries = [
        "%s/assets/%s/native/%s?%s" % (BASE, asset_id, urllib.parse.quote(name), q),
        "%s/assets/%s/Medium/SWH/%s?format=webp&type=responsiveimage&%s" % (BASE, asset_id, urllib.parse.quote(name), q),
        "%s/assets/%s/Medium/%s?%s" % (BASE, asset_id, urllib.parse.quote(name), q),
    ]
    for u in tries:
        data = get(u, binary=True)
        if data and kind(data):
            print("downloaded %d bytes from %s" % (len(data), u.split("?")[0]))
            return data
        if data:
            print("not an image (%d bytes) from %s, starts with %r" % (len(data), u.split("?")[0], data[:80]))
    return None


def label(name):
    m = re.search(r"-(\d{2})(\d{2})(\d{2})\.\w+$", name)
    return "%s, day %s, %s:%s UTC" % ("SWH Europe", m.group(1), m.group(2), m.group(3)) if m else name


def main(base="."):
    meta_path = base + "/sigwx.json"
    try:
        old = json.load(open(meta_path))
    except Exception:
        old = {}
    if "--seed" in sys.argv:
        asset_id, name = SEED
    else:
        charts = list_charts()
        if not charts:
            print("no chart found: the list could not be read. Nothing changed.")
            return 0
        print("newest charts:", [c[2] for c in charts[-3:]])
        _, asset_id, name = charts[-1]
    if old.get("name") == name and old.get("file") and os.path.exists(base + "/" + old["file"]):
        print("already up to date:", name)
        return 0
    data = download(asset_id, name)
    if not data:
        print("could not download", name, "- nothing changed.")
        return 0
    for f in os.listdir(base):
        if f.startswith("sigwx-eur."):
            os.remove(base + "/" + f)
    fname = "sigwx-eur." + kind(data)
    with open(base + "/" + fname, "wb") as f:
        f.write(data)
    meta = {"name": name, "label": label(name), "file": fname,
            "fetched": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")}
    with open(meta_path, "w") as f:
        json.dump(meta, f, indent=1)
    print("saved", fname, "-", meta["label"])
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        print("unexpected problem:", e)
        sys.exit(0)
