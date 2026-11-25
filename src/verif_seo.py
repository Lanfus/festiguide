#!/usr/bin/env python3
"""Contrôle SEO des pages générées, à lancer depuis la racine du dépôt après build.py :
    python src/verif_seo.py
Parcourt toutes les URL de sitemap.xml et vérifie title, meta description, h1, canonical, noindex,
JSON-LD et les balises de vérification Search Console. Code de sortie 1 s'il y a une erreur."""
import html, json, re, sys
from pathlib import Path

BASE = "https://lefestiguide.fr/"
LEGALES = {"mentions-legales.html", "conditions-utilisation.html", "confidentialite.html", "cookies.html"}
VERIF = ["-dZV6mVuMr0xR11z0I5KrbklOmMtcFE7X_o8ikekrAo", "5xCTOPiFWbg2MLwQC0pUDpysYnz3dnjGqJgbENc3qoE"]
root = Path(sys.argv[1] if len(sys.argv) > 1 else ".")

urls = re.findall(r"<loc>(.*?)</loc>", (root / "sitemap.xml").read_text(encoding="utf-8"))
erreurs, avert, titres = [], [], {}
for u in urls:
    fichier = u[len(BASE):] or "index.html"
    h = (root / fichier).read_text(encoding="utf-8")
    t = re.search(r"<title>(.*?)</title>", h, re.S)
    t = html.unescape(t.group(1).strip()) if t else ""
    if not t:
        erreurs.append(f"{fichier} : title absent")
    elif len(t) > 60:
        erreurs.append(f"{fichier} : title de {len(t)} caractères")
    titres.setdefault(t, []).append(fichier)
    d = re.search(r'<meta name="description" content="(.*?)"', h)
    d = html.unescape(d.group(1)) if d else ""
    if not d:
        erreurs.append(f"{fichier} : meta description absente")
    elif len(d) > 160 or len(d) < 120:
        (avert if fichier in LEGALES and len(d) <= 160 else erreurs).append(f"{fichier} : description de {len(d)} caractères")
    n_h1 = len(re.findall(r"<h1[\s>]", h))
    if n_h1 != 1:
        erreurs.append(f"{fichier} : {n_h1} h1")
    c = re.search(r'<link rel="canonical" href="(.*?)"', h)
    attendu = BASE if fichier == "index.html" else BASE + fichier
    if not c or c.group(1) != attendu:
        erreurs.append(f"{fichier} : canonical {c.group(1) if c else 'absente'} au lieu de {attendu}")
    if re.search(r'<meta name="robots" content="[^"]*noindex', h):
        erreurs.append(f"{fichier} : noindex")
    for bloc in re.findall(r'<script type="application/ld\+json">(.*?)</script>', h, re.S):
        try:
            data = json.loads(bloc)
        except ValueError as e:
            erreurs.append(f"{fichier} : JSON-LD invalide ({e})")
            continue
        for item in data if isinstance(data, list) else data.get("@graph", [data]):
            if item.get("@type") in ("Festival", "Event", "MusicEvent") and not item.get("startDate"):
                erreurs.append(f"{fichier} : schéma {item['@type']} sans startDate")
    if fichier == "index.html":
        for v in VERIF:
            if f'<meta name="google-site-verification" content="{v}"' not in h:
                erreurs.append(f"index.html : balise google-site-verification {v[:8]}… absente")
for t, fs in titres.items():
    if len(fs) > 1:
        erreurs.append(f"title en double « {t} » : {', '.join(fs)}")

print(f"{len(urls)} URL du sitemap contrôlées")
for a in avert:
    print("  avertissement :", a)
for e in erreurs:
    print("  ERREUR :", e)
print("Aucune erreur." if not erreurs else f"{len(erreurs)} erreur(s).")
sys.exit(1 if erreurs else 0)
