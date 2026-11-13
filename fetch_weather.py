#!/usr/bin/env python3
"""Fetches the latest METAR and TAF for the airports in airports.json and writes weather.json.
Run by a GitHub Action every half hour. Uses only the Python standard library."""
import datetime
import json
import re
import sys
import urllib.parse
import urllib.request

API = "https://aviationweather.gov/api/data"
UA = "FlightBriefing-weather/1.0 (GitHub Action)"


def get(url):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=40) as r:
            return r.read().decode("utf-8", "replace")
    except Exception as e:  # a failed request must not stop the other airports
        print("warning: %s -> %s" % (url, e), file=sys.stderr)
        return None


def obs_time(group, now):
    m = re.match(r"^(\d{2})(\d{2})(\d{2})Z$", group or "")
    if not m:
        return None
    day, hour, minute = int(m.group(1)), int(m.group(2)), int(m.group(3))
    for back in (0, 1):
        y, mo = now.year, now.month - back
        if mo == 0:
            y, mo = y - 1, 12
        try:
            c = datetime.datetime(y, mo, day, hour, minute, tzinfo=datetime.timezone.utc)
        except ValueError:
            continue
        if c <= now + datetime.timedelta(hours=2):
            return c
    return None


def parse_metar(text, now):
    best = {}
    for line in (text or "").splitlines():
        line = line.strip()
        if not line:
            continue
        line = re.sub(r"^(METAR|SPECI)\s+", "", line)
        tk = line.split()
        if len(tk) < 3 or not re.fullmatch(r"[A-Z]{4}", tk[0]):
            continue
        t = obs_time(tk[1], now)
        if t is None:
            continue
        if tk[0] not in best or t > best[tk[0]][0]:
            best[tk[0]] = (t, line)
    return {k: {"raw": v[1]} for k, v in best.items()}


def parse_taf(text):
    blocks, cur = [], None
    for line in (text or "").splitlines():
        if not line.strip():
            continue
        if not line[0].isspace() and re.match(r"^(TAF\s+)?(AMD\s+|COR\s+)?[A-Z]{4}\s+\d{6}Z", line.strip()):
            cur = [line.strip()]
            blocks.append(cur)
        elif cur is not None:
            cur.append(line.strip())
    out = {}
    for b in blocks:
        m = re.match(r"^(?:TAF\s+)?(?:AMD\s+|COR\s+)?([A-Z]{4})\s", b[0] + " ")
        if m and m.group(1) not in out:
            out[m.group(1)] = {"raw": "\n".join(b)}
    return out


def main(base="."):
    now = datetime.datetime.now(datetime.timezone.utc)
    airports = json.load(open(base + "/airports.json"))["airports"]
    icaos = sorted({v["icao"] for v in airports.values()})
    try:
        old = json.load(open(base + "/weather.json"))
    except Exception:
        old = {}
    metar, taf = dict(old.get("metar", {})), dict(old.get("taf", {}))
    got = 0
    for i in range(0, len(icaos), 40):
        ids = ",".join(icaos[i:i + 40])
        q = urllib.parse.urlencode({"ids": ids, "format": "raw", "hours": 3}, safe=",")
        t = get(API + "/metar?" + q)
        if t is not None:
            new = parse_metar(t, now)
            metar.update(new)
            got += len(new)
        q = urllib.parse.urlencode({"ids": ids, "format": "raw"}, safe=",")
        t = get(API + "/taf?" + q)
        if t is not None:
            taf.update(parse_taf(t))
    # drop reports older than 8 hours
    for k in list(metar):
        t = obs_time(metar[k]["raw"].split()[1] if len(metar[k]["raw"].split()) > 1 else "", now)
        if t is None or now - t > datetime.timedelta(hours=8):
            del metar[k]
    if got == 0 and not old:
        print("no weather data received, nothing written")
        return 0
    out = {"generated": now.strftime("%Y-%m-%dT%H:%M:%SZ"), "source": "aviationweather.gov", "metar": metar, "taf": taf}
    with open(base + "/weather.json", "w") as f:
        json.dump(out, f, indent=1, sort_keys=True)
    print("wrote weather.json: %d METAR, %d TAF" % (len(metar), len(taf)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
