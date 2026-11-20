#!/usr/bin/env python3
"""Vérifie et nettoie les données festivals renvoyées par les recherches."""
import json, re, sys, unicodedata
from pathlib import Path

REQ = ["slug", "name", "city", "country"]
OPT = {"short": "", "region": None, "venue": None, "maps_q": None, "genres": [], "mois": [], "dates": "À confirmer",
       "iso": None, "status": "Dates à confirmer", "status_note": "", "price_from": None,
       "price_label": "Tarifs non publiés", "prices": [], "prices_note": "", "last_label": "",
       "last_dates": "", "lineup": [], "lineup_note": "", "about": "", "access": [], "tips": [],
       "official": "", "sources": [], "liens": [], "visiteurs": None, "visiteurs_note": "", "geo": None}
MOIS = ["janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août",
        "septembre", "octobre", "novembre", "décembre"]
MOIS_N = {unicodedata.normalize("NFD", m).encode("ascii", "ignore").decode(): m for m in MOIS}


def slugify(s):
    s = unicodedata.normalize("NFD", s).encode("ascii", "ignore").decode().lower()
    return re.sub(r"-+", "-", re.sub(r"[^a-z0-9]+", "-", s)).strip("-")


def clean(f, problems):
    for k in REQ:
        if not f.get(k):
            problems.append(f"{f.get('name') or f.get('slug') or '?'} : champ obligatoire manquant -> {k}")
            return None
    out = dict(OPT)
    out.update({k: v for k, v in f.items() if k in OPT or k in REQ})
    out["slug"] = slugify(out["slug"] or out["name"])
    for k in ("genres", "mois", "lineup", "access", "tips"):
        out[k] = [str(x).strip() for x in (out.get(k) or []) if x]
    # normalise les mois (accents / casse)
    m2 = []
    for m in out["mois"]:
        key = unicodedata.normalize("NFD", m.strip().lower()).encode("ascii", "ignore").decode()
        if key in MOIS_N and MOIS_N[key] not in m2:
            m2.append(MOIS_N[key])
        else:
            problems.append(f"{out['name']} : mois non reconnu -> {m!r}")
    out["mois"] = m2
    # paires [libellé, valeur]
    for k in ("prices", "sources", "liens"):
        pairs = []
        for item in (out.get(k) or []):
            if isinstance(item, (list, tuple)) and len(item) == 2 and all(item):
                pairs.append([str(item[0]).strip(), str(item[1]).strip()])
            elif isinstance(item, dict):
                vals = list(item.values())
                if len(vals) == 2 and all(vals):
                    pairs.append([str(vals[0]).strip(), str(vals[1]).strip()])
            else:
                problems.append(f"{out['name']} : {k} mal formé -> {item!r}")
        out[k] = pairs
    out["sources"] = [[t, u] for t, u in out["sources"] if u.startswith("http")]
    # liens utiles du festival (plan du site, FAQ, appli...) : [libellé, url officielle]
    out["liens"] = [[t, u] for t, u in out["liens"] if u.startswith("http")]
    g = out.get("geo")
    if g is not None and not (isinstance(g, list) and len(g) == 2 and all(isinstance(x, (int, float)) for x in g)
                              and 41 < g[0] < 52 and -6 < g[1] < 10):
        problems.append(f"{out['name']} : geo invalide (attendu [latitude, longitude] en France ou Belgique) -> {g!r}")
        out["geo"] = None
    if not out["sources"]:
        problems.append(f"{out['name']} : aucune source valide")
    if out.get("official") and not str(out["official"]).startswith("http"):
        out["official"] = ""
    # dates ISO
    iso = out.get("iso")
    if iso:
        ok = (isinstance(iso, (list, tuple)) and len(iso) == 2
              and all(re.fullmatch(r"\d{4}-\d{2}-\d{2}", str(d)) for d in iso)
              and str(iso[0]) <= str(iso[1]) and str(iso[0]) >= "2026-11-13")
        if ok:
            out["iso"] = [str(iso[0]), str(iso[1])]
        else:
            problems.append(f"{out['name']} : dates ISO invalides ou passées -> {iso!r}, ignorées")
            out["iso"] = None
            out["status"] = "Dates à confirmer"
    if out["iso"] and out["status"] != "Dates annoncées":
        out["status"] = "Dates annoncées"
    if not out["iso"] and out["status"] == "Dates annoncées":
        problems.append(f"{out['name']} : statut 'Dates annoncées' sans dates ISO -> corrigé")
        out["status"] = "Dates à confirmer"
    if not out["mois"] and out["iso"]:
        out["mois"] = [MOIS[int(out["iso"][0][5:7]) - 1]]
    if not out["mois"]:
        problems.append(f"{out['name']} : aucun mois")
    try:
        out["visiteurs"] = int(out["visiteurs"]) if out["visiteurs"] else None
    except (TypeError, ValueError):
        out["visiteurs"] = None
    if out["visiteurs"] and not out["visiteurs_note"]:
        problems.append(f"{out['name']} : visiteurs sans visiteurs_note (précisez l'édition et la source)")
    try:
        out["price_from"] = float(out["price_from"]) if out["price_from"] is not None else None
    except (TypeError, ValueError):
        out["price_from"] = None
    return out


def main():
    fests, problems, seen = [], [], {}
    for path in sys.argv[1:-1]:
        raw = json.loads(Path(path).read_text(encoding="utf-8"))
        items = raw.get("festivals", raw) if isinstance(raw, dict) else raw
        for f in items:
            c = clean(f, problems)
            if not c:
                continue
            if c["slug"] in seen:
                problems.append(f"doublon ignoré : {c['name']} ({c['slug']})")
                continue
            seen[c["slug"]] = True
            fests.append(c)
    Path(sys.argv[-1]).write_text(json.dumps(fests, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{len(fests)} festivals retenus")
    annonces = sum(1 for f in fests if f["status"] == "Dates annoncées")
    print(f"  dates annoncées : {annonces} / à confirmer : {len(fests) - annonces}")
    print(f"  sans prix : {sum(1 for f in fests if not f['prices'])}")
    print(f"  sans line-up : {sum(1 for f in fests if not f['lineup'])}")
    if problems:
        print("\nPoints à signaler :")
        for p in problems:
            print("  -", p)


if __name__ == "__main__":
    main()
