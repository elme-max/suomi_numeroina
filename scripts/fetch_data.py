#!/usr/bin/env python3
"""Hakee dashboardin luvut Tilastokeskuksen avoimesta PxWeb-rajapinnasta.

Kirjoittaa tuloksen tiedostoon data/data.json. Ei ulkoisia riippuvuuksia.
Lähde: Tilastokeskus, StatFin-tietokanta (CC BY 4.0), https://pxdata.stat.fi
"""
import json
import sys
import time
import urllib.request
import webbrowser
from datetime import datetime, timezone
from pathlib import Path

API = "https://pxdata.stat.fi/PxWeb/api/v1/fi/StatFin/"
BROWSE = "https://pxdata.stat.fi/PXWeb/pxweb/fi/StatFin/StatFin__{db}/{table}.px/"
ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "data.json"
OUT_JS = ROOT / "data" / "data.js"  # sama data skriptinä, jotta sivu toimii myös file://-osoitteesta


def fetch(db, table, selections):
    """Palauttaa (sarjat, päivitysaika). sarjat[(koodit...)] = [(jakso, arvo), ...]."""
    query = [{"code": "contentscode" if c == "tiedot" else c,
              "selection": {"filter": "item", "values": v}}
             for c, v in selections.items()]
    body = json.dumps({"query": query, "response": {"format": "json-stat2"}}).encode()
    req = urllib.request.Request(
        f"{API}{db}/{table}.px", data=body,
        headers={"Content-Type": "application/json", "User-Agent": "suomi-numeroina-dashboard"})
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                ds = json.load(resp)
            break
        except Exception as exc:  # verkkovirhe tai 429 -> yritetään uudelleen
            if attempt == 3:
                raise
            print(f"  {table}: {exc}; uusi yritys", file=sys.stderr)
            time.sleep(5 * (attempt + 1))

    ids, sizes = ds["id"], ds["size"]
    codes = []
    for dim in ids:
        index = ds["dimension"][dim]["category"]["index"]
        codes.append(sorted(index, key=index.get))
    time_pos = next(i for i, d in enumerate(ids) if d.startswith("timeperiod"))

    series = {}
    values = ds["value"]
    for flat, value in enumerate(values):
        pos, rest = [], flat
        for size in reversed(sizes):
            pos.append(rest % size)
            rest //= size
        pos.reverse()
        key = tuple(codes[i][p] for i, p in enumerate(pos) if i != time_pos)
        if value is not None:
            series.setdefault(key, []).append((codes[time_pos][pos[time_pos]], value))
    time.sleep(1)  # ollaan kohteliaita rajapinnalle
    return series, ds.get("updated")


def pct(new, old):
    return (new / old - 1) * 100


def at(points, period):
    return dict(points)[period]


def prev_year(period):
    return str(int(period[:4]) - 1) + period[4:]


def rounded(points, digits):
    return [[p, round(v, digits)] for p, v in points]


def labour():
    s, updated = fetch("tyti", "135z", {"tiedot": [
        "Tyollaste_20_64_trendi", "tyottaste_trendi", "Tyottaste_15_24_trendi"]})
    out = []
    for key, id_, title, good, note in [
        ("Tyollaste_20_64_trendi", "tyollisyysaste", "Työllisyysaste", "up",
         "20–64-vuotiaat, trendi"),
        ("tyottaste_trendi", "tyottomyysaste", "Työttömyysaste", "down",
         "15–74-vuotiaat, trendi"),
        ("Tyottaste_15_24_trendi", "nuorisotyottomyys", "Nuorisotyöttömyysaste", "down",
         "15–24-vuotiaat, trendi"),
    ]:
        pts = s[(key,)]
        period, value = pts[-1]
        out.append({
            "id": id_, "title": title, "freq": "M", "period": period,
            "hero": {"value": round(value, 1), "unit": "%", "label": note},
            "deltas": [
                {"label": "edelliskuusta", "value": round(value - pts[-2][1], 1),
                 "unit": "%-yks.", "good": good},
                {"label": "vuodentakaisesta", "value": round(value - at(pts, prev_year(period)), 1),
                 "unit": "%-yks.", "good": good},
            ],
            "series": {"label": f"{title}, {note}", "unit": "%", "digits": 1,
                       "points": rounded(pts, 1)},
            "source": {"name": "Tilastokeskus, työvoimatutkimus", "table": "135z",
                       "url": BROWSE.format(db="tyti", table="135z"), "updated": updated},
        })
    return out


def national_accounts():
    gdp, gdp_updated = fetch("ntp", "132h", {
        "taloustoimi_1_20180101": ["B1GMH"],
        "tiedot": ["kausitvv2015", "vol_kk_kausitvv2015", "vol_vv_tyopvv2015"]})
    hours, hours_updated = fetch("ntp", "11tj", {
        "taloustoimi_1_20180101": ["E2"],
        "toimiala_79_20180101": ["SSS"],
        "tiedot": ["ntp-KAUSIT"]})

    level = gdp[("B1GMH", "kausitvv2015")]
    qoq = gdp[("B1GMH", "vol_kk_kausitvv2015")]
    yoy = gdp[("B1GMH", "vol_vv_tyopvv2015")]
    period = level[-1][0]
    bkt = {
        "id": "bkt", "title": "Bruttokansantuote", "freq": "Q", "period": period,
        "hero": {"value": round(at(yoy, period), 1), "unit": "%", "signed": True,
                 "label": "volyymin muutos vuodentakaisesta, työpäiväkorjattu"},
        "deltas": [
            {"label": "edellisneljänneksestä, kausitasoitettu",
             "value": round(at(qoq, period), 1), "unit": "%", "good": "up"},
        ],
        "series": {"label": "BKT:n volyymi, kausitasoitettu, viitevuoden 2015 hinnoin",
                   "unit": "mrd. €", "digits": 1,
                   "points": rounded([(p, v / 1000) for p, v in level], 2)},
        "source": {"name": "Tilastokeskus, neljännesvuositilinpito", "table": "132h",
                   "url": BROWSE.format(db="ntp", table="132h"), "updated": gdp_updated},
    }

    # Työn tuottavuus = BKT:n volyymi / tehdyt työtunnit (molemmat kausitasoitettuja).
    h = dict(hours[("E2", "SSS", "ntp-KAUSIT")])
    prod = [(p, v / h[p]) for p, v in level if p in h]
    p_period, p_value = prod[-1]
    tuottavuus = {
        "id": "tuottavuus", "title": "Työn tuottavuus", "freq": "Q", "period": p_period,
        "hero": {"value": round(p_value, 1), "unit": "€/h",
                 "label": "BKT tehtyä työtuntia kohti, viitevuoden 2015 hinnoin"},
        "deltas": [
            {"label": "edellisneljänneksestä", "value": round(pct(p_value, prod[-2][1]), 1),
             "unit": "%", "good": "up"},
            {"label": "vuodentakaisesta",
             "value": round(pct(p_value, at(prod, prev_year(p_period))), 1),
             "unit": "%", "good": "up"},
        ],
        "series": {"label": "BKT tehtyä työtuntia kohti, kausitasoitettu, viitevuoden 2015 hinnoin",
                   "unit": "€/h", "digits": 1, "points": rounded(prod, 2)},
        "source": {"name": "Laskettu Tilastokeskuksen neljännesvuositilinpidosta",
                   "table": "132h ja 11tj",
                   "url": BROWSE.format(db="ntp", table="11tj"),
                   "updated": max(gdp_updated, hours_updated)},
    }
    return bkt, tuottavuus


def orders():
    s, updated = fetch("teul", "14mi", {
        "toimiala_17_20220818": ["C"],
        "tiedot": ["teul-Trendi", "teul-muutosprosentti", "teul-alk_liuk_muutos"]})
    trend = s[("C", "teul-Trendi")]
    yoy = s[("C", "teul-muutosprosentti")]
    yoy3 = s[("C", "teul-alk_liuk_muutos")]
    period = yoy[-1][0]
    return {
        "id": "tilaukset", "title": "Teollisuuden uudet tilaukset", "freq": "M", "period": period,
        "hero": {"value": round(at(yoy, period), 1), "unit": "%", "signed": True,
                 "label": "arvon muutos vuodentakaisesta"},
        "deltas": [
            {"label": "kolmen kuukauden liukuva vuosimuutos",
             "value": round(yoy3[-1][1], 1), "unit": "%", "good": "up"},
        ],
        "series": {"label": "Uusien tilausten arvo, trendi, indeksi 2021 = 100",
                   "unit": "", "digits": 1, "points": rounded(trend, 1)},
        "source": {"name": "Tilastokeskus, teollisuuden uudet tilaukset", "table": "14mi",
                   "url": BROWSE.format(db="teul", table="14mi"), "updated": updated},
    }


def main():
    tyollisyys, tyottomyys, nuoriso = labour()
    bkt, tuottavuus = national_accounts()
    indicators = [tyollisyys, tyottomyys, nuoriso, bkt, tuottavuus, orders()]

    for ind in indicators:  # varmistus: ei julkaista tyhjää tai rikkinäistä dataa
        assert len(ind["series"]["points"]) > 24, ind["id"]

    # Tiedostot muuttuvat vain, kun Tilastokeskuksen data muuttuu.
    if OUT.exists() and OUT_JS.exists():
        old = json.loads(OUT.read_text(encoding="utf-8"))
        if old.get("indicators") == indicators:
            print("Ei muutoksia.")
            return
    OUT.parent.mkdir(exist_ok=True)
    payload = {"fetched": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
               "indicators": indicators}
    text = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    OUT.write_text(text + "\n", encoding="utf-8")
    OUT_JS.write_text(f"window.SUOMI_DATA={text};\n", encoding="utf-8")
    for ind in indicators:
        print(f'{ind["title"]}: {ind["hero"]["value"]} {ind["hero"]["unit"]} ({ind["period"]})')


if __name__ == "__main__":
    main()
    if "--avaa" in sys.argv:  # avaa dashboardin selaimeen päivityksen jälkeen
        webbrowser.open((ROOT / "index.html").as_uri())
