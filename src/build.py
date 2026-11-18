#!/usr/bin/env python3
"""Génère le site FestiGuide à partir de festivals.json."""
import hashlib, html, json, shutil, sys, unicodedata
from pathlib import Path

esc = lambda s: html.escape(str(s), quote=True)

ICONS = {
    "pin": '<path d="M12 21s-7-6.2-7-11a7 7 0 0 1 14 0c0 4.8-7 11-7 11z"/><circle cx="12" cy="10" r="2.5"/>',
    "cal": '<rect x="3" y="5" width="18" height="16" rx="2"/><path d="M3 10h18M8 3v4M16 3v4"/>',
    "ticket": '<path d="M4 7h16v3a2 2 0 0 0 0 4v3H4v-3a2 2 0 0 0 0-4z"/>',
    "users": '<circle cx="9" cy="8" r="3"/><path d="M3 20a6 6 0 0 1 12 0"/><circle cx="17" cy="9" r="2.5"/><path d="M16 14a5 5 0 0 1 6 5"/>',
    "map": '<path d="M9 4 3 6v14l6-2 6 2 6-2V4l-6 2z"/><path d="M9 4v14M15 6v14"/>',
    "check": '<path d="M5 12.5l4.5 4.5L19 7.5"/>',
    "alert": '<path d="M12 4 2.5 20h19z"/><path d="M12 10v4.5M12 17.5v.01"/>',
    "share": '<path d="M12 15V4M8 8l4-4 4 4M5 13v6h14v-6"/>',
}


def ic(name):
    """Icône en trait fin (une seule taille et une seule épaisseur pour tout le site)."""
    return f'<svg class="i" viewBox="0 0 24 24" aria-hidden="true">{ICONS[name]}</svg>'
SITE = "FestiGuide"
UPDATED = "17 novembre 2026"
BASE_URL = "https://lanfus.github.io/festiguide"
EDITEUR = "Florent H."
CONTACT = "contact.festiguide@gmail.com"
# ---------- à remplir par Florent (vide = fonctionnalité désactivée, rien n'est chargé ni affiché) ----------
# Mesure d'audience GoatCounter, sans cookie : le code choisi à l'inscription sur goatcounter.com
# (ex. "festiguide" pour https://festiguide.goatcounter.com).
GOATCOUNTER = "lanfus"
# Newsletter Brevo : l'adresse « action » du formulaire Brevo (…sibforms.com/serve/…), voir README.
NEWSLETTER_ACTION = "https://f9bc5982.sibforms.com/serve/MUIFAN7XhHdaCARXq_hbErklvqlHojt6KVsEGk9pAfHIdxAeHpZuvTdeJl3twijdmE8ry9LNXFVB0R_ibEULP-AJvoT9WSxcF1dJWmc8LVv0Z0dcp7_zinNWfSWmOuyPFlN5MQGgweDZI_Z4sJKoPU9nrzo5jQbeixDYv9KmRWjIiDtukogwtEaohiL2dX0SBPNkVy3PpOc0daQ1_A=="
# Témoignage personnel affiché en tête du guide sécurité (expérience terrain). Vide = bloc masqué.
GUIDE_TEMOIGNAGE = ""

LEGAL_PAGES = ["mentions-legales.html", "conditions-utilisation.html", "confidentialite.html", "cookies.html"]
OUT = Path(sys.argv[2] if len(sys.argv) > 2 else ".")

MOIS_ORDRE = ["janvier", "février", "mars", "avril", "mai", "juin", "juillet",
              "août", "septembre", "octobre", "novembre", "décembre"]


ABBR = {"janvier": "janv.", "février": "févr.", "avril": "avr.", "juillet": "juil.", "septembre": "sept.",
        "octobre": "oct.", "novembre": "nov.", "décembre": "déc."}


MOIS_COURT = {"janvier": "janv.", "février": "févr.", "mars": "mars", "avril": "avr.", "mai": "mai", "juin": "juin",
              "juillet": "juil.", "août": "août", "septembre": "sept.", "octobre": "oct.", "novembre": "nov.", "décembre": "déc."}


def date_block(f):
    """Colonne de dates de la liste (style programme imprimé).
    Dates confirmées : jour(s) en gros + mois et année. Sinon : mois habituel + « à confirmer » (rien d'inventé)."""
    if f.get("iso"):
        a, b = f["iso"]
        ma, mb = MOIS_ORDRE[int(a[5:7]) - 1], MOIS_ORDRE[int(b[5:7]) - 1]
        d1, d2 = int(a[8:10]), int(b[8:10])
        if ma == mb:
            big = str(d1) if a == b else f"{d1}–{d2}"
            sub = f"{MOIS_COURT[ma]} {a[:4]}"
        else:
            big = str(d1)
            sub = f"{MOIS_COURT[ma]} → {d2} {MOIS_COURT[mb]}"
        return f'<div class="when"><b>{big}</b><span>{esc(sub)}</span></div>'
    m = f.get("mois") or []
    big = MOIS_COURT.get(m[0], m[0]) if m else "—"
    return f'<div class="when tbc"><b>{esc(big)}</b><span>à confirmer</span></div>'


def norm(s):
    s = unicodedata.normalize("NFD", str(s))
    return "".join(c for c in s if unicodedata.category(c) != "Mn").lower()


def tri_key(f):
    if f.get("iso"):
        return (0, f["iso"][0])
    mois = f.get("mois") or []
    i = MOIS_ORDRE.index(mois[0]) if mois and mois[0] in MOIS_ORDRE else 99
    return (1, f"{i:02d}")


def is_free(f):
    """Entrée libre : seulement si le libellé de prix le dit (Cannes a price_from 0 mais reste sur accréditation)."""
    return norm(f.get("price_label") or "").startswith(("gratuit", "entree libre"))


def prix_num(f):
    p = f.get("price_from")
    if p is None or (p == 0 and not is_free(f)):
        return None
    return p


def fmt_n(n):
    return f"{int(n):,}".replace(",", "\u202f")


def duree(f):
    from datetime import date
    if not f.get("iso"):
        return None
    a, b = (date.fromisoformat(x) for x in f["iso"])
    return (b - a).days + 1


def ics(f):
    """Fichier agenda (.ics) généré pour les festivals aux dates confirmées. Aucun service tiers."""
    from datetime import date, timedelta
    a, b = (date.fromisoformat(x) for x in f["iso"])
    e = lambda s: str(s).replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,")
    lines = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//FestiGuide//FR", "CALSCALE:GREGORIAN", "BEGIN:VEVENT",
             f"UID:{f['slug']}-{a:%Y%m%d}@lanfus.github.io", "DTSTAMP:20261113T000000Z",
             f"DTSTART;VALUE=DATE:{a:%Y%m%d}", f"DTEND;VALUE=DATE:{(b + timedelta(days=1)):%Y%m%d}",
             f"SUMMARY:{e(f['name'])}", f"LOCATION:{e(f.get('venue') or f.get('city') or '')}",
             f"DESCRIPTION:{e('Fiche FestiGuide : ' + BASE_URL + '/' + f['slug'] + '.html')}",
             f"URL:{f.get('official') or BASE_URL + '/' + f['slug'] + '.html'}", "END:VEVENT", "END:VCALENDAR"]
    return "\r\n".join(lines) + "\r\n"


def make_title(f):
    """Titre de page de 60 caractères maximum (au-delà, Google le coupe)."""
    n = f.get("short") or f["name"]
    for t in (f"{n} : dates, prix, line-up et accès | {SITE}", f"{n} : dates, prix et line-up | {SITE}",
              f"{n} : dates, prix, line-up", f"{n} : dates et prix"):
        if len(t) <= 60:
            return t
    return f"{n} | {SITE}"


def related(f, fests, n=4):
    """Festivals proches par région, mois et genre, pour le maillage interne.
    À score égal, on prend les voisins dans l'ordre chronologique pour varier les liens."""
    pos = {g["slug"]: i for i, g in enumerate(fests)}

    def score(g):
        s = 3 if g.get("region") and g.get("region") == f.get("region") else 0
        s += 2 if set(g.get("mois") or []) & set(f.get("mois") or []) else 0
        return s + len(set(g.get("genres") or []) & set(f.get("genres") or []))

    cands = [g for g in fests if g["slug"] != f["slug"]]
    cands.sort(key=lambda g: (-score(g), (pos[g["slug"]] - pos[f["slug"]]) % len(fests)))
    return cands[:n]


# ---------- pages de regroupement (mois, style, région) ----------
MIN_MOIS, MIN_REGION, MIN_GENRE = 3, 5, 5
GENRE_PAGES = {
    "Électro": ("festivals-electro", "Festivals électro"),
    "Pop": ("festivals-pop", "Festivals pop"),
    "Rock": ("festivals-rock", "Festivals rock"),
    "Rap": ("festivals-rap", "Festivals rap"),
    "Jazz": ("festivals-jazz", "Festivals de jazz"),
    "Musique classique": ("festivals-musique-classique", "Festivals de musique classique"),
    "Musiques du monde": ("festivals-musiques-du-monde", "Festivals de musiques du monde"),
    "Techno": ("festivals-techno", "Festivals techno"),
    "Hip-hop": ("festivals-hip-hop", "Festivals hip-hop"),
    "Musiques actuelles": ("festivals-musiques-actuelles", "Festivals de musiques actuelles"),
    "Chanson": ("festivals-chanson", "Festivals de chanson"),
    "Indie": ("festivals-indie", "Festivals indie"),
    "Soul": ("festivals-soul", "Festivals soul"),
    "Festival en montagne": ("festivals-musique-en-montagne", "Festivals de musique en montagne"),
    "Metal": ("festivals-metal", "Festivals metal"),
    "House": ("festivals-house", "Festivals house"),
}
REGION_PREP = {"Grand Est": "dans le Grand Est", "Pays de la Loire": "dans les Pays de la Loire",
               "Bruxelles-Capitale": "à Bruxelles"}


def slugify(s):
    import re
    return re.sub(r"[^a-z0-9]+", "-", norm(s)).strip("-")


def group_defs(fests):
    """Pages de listes (par mois, style, région, pays), uniquement quand elles ont assez de festivals pour ne pas être creuses."""
    defs = []
    for m in MOIS_ORDRE:
        lst = [f for f in fests if m in (f.get("mois") or [])]
        if len(lst) >= MIN_MOIS:
            defs.append({"slug": f"festivals-musique-{slugify(m)}", "h1": f"Festivals de musique en {m}",
                         "kind": "mois", "label": m.capitalize(), "list": lst, "ou": f"en {m}"})
    counts = {}
    for f in fests:
        for g in (f.get("genres") or []):
            counts[g] = counts.get(g, 0) + 1
    for g, (slug, h1) in GENRE_PAGES.items():
        lst = [f for f in fests if g in (f.get("genres") or [])]
        if len(lst) >= MIN_GENRE:
            defs.append({"slug": slug, "h1": h1, "kind": "style", "label": h1.replace("Festivals de ", "").replace("Festivals ", "").capitalize(),
                         "list": lst, "ou": f"dans le style « {g} »"})
    lst = [f for f in fests if f.get("country") == "Belgique"]
    if len(lst) >= MIN_REGION:
        defs.append({"slug": "festivals-musique-belgique", "h1": "Festivals de musique en Belgique", "kind": "lieu",
                     "label": "Belgique", "list": lst, "ou": "en Belgique"})
    for r in sorted({f.get("region") for f in fests if f.get("region")}, key=norm):
        lst = [f for f in fests if f.get("region") == r]
        if len(lst) >= MIN_REGION:
            ou = REGION_PREP.get(r, f"en {r}")
            defs.append({"slug": f"festivals-musique-{slugify(r)}", "h1": f"Festivals de musique {ou}", "kind": "lieu",
                         "label": r, "list": lst, "ou": ou})
    return defs


def group_title(h1):
    for t in (f"{h1} : dates, prix | {SITE}", f"{h1} | {SITE}", h1):
        if len(t) <= 60:
            return t
    return h1[:60]


def nav_groups(defs, current=None):
    blocs = [("mois", "Par mois"), ("style", "Par style"), ("lieu", "Par lieu")]
    out = ""
    for kind, titre in blocs:
        items = [d for d in defs if d["kind"] == kind]
        if not items:
            continue
        lis = "".join(
            (f'<li><span class="cur">{esc(d["label"])} <b>{len(d["list"])}</b></span></li>' if d["slug"] == current
             else f'<li><a href="{d["slug"]}.html">{esc(d["label"])} <b>{len(d["list"])}</b></a></li>') for d in items)
        out += f'<h3>{titre}</h3><ul class="chips-nav">{lis}</ul>\n'
    return out


def voir_aussi(f, defs):
    by_slug = {d["slug"]: d for d in defs}
    want = []
    for m in (f.get("mois") or [])[:1]:
        want.append(f"festivals-musique-{slugify(m)}")
    n = 0
    for g in (f.get("genres") or []):
        if g in GENRE_PAGES and GENRE_PAGES[g][0] in by_slug and n < 2:
            want.append(GENRE_PAGES[g][0])
            n += 1
    if f.get("region"):
        want.append(f"festivals-musique-{slugify(f['region'])}")
    if f.get("country") == "Belgique":
        want.append("festivals-musique-belgique")
    seen, links = set(), []
    for s in want:
        if s in by_slug and s not in seen:
            seen.add(s)
            links.append(f'<a href="{s}.html">{esc(by_slug[s]["h1"])}</a>')
    return ("<p class=\"small see\">Voir aussi : " + " · ".join(links) + "</p>") if links else ""


def group_page(d, defs, fests):
    lst = sorted(d["list"], key=lambda f: (-(f.get("visiteurs") or 0), tri_key(f)))
    n = len(lst)
    conf = [f for f in lst if f.get("status") == "Dates annoncées"]
    gros = [f for f in lst if f.get("visiteurs")][:3]
    prix = [(prix_num(f), f) for f in lst if prix_num(f) is not None]
    free = [f for f in lst if is_free(f)]
    p1 = f"{n} festivals de musique sont référencés {d['ou']} sur {SITE}, dont {len(conf)} aux dates de la prochaine édition déjà confirmées par une source officielle."
    if gros:
        p1 += " Les plus gros d'après la fréquentation publiée de leur dernière édition : " + ", ".join(
            f"{g['name']} (environ {fmt_n(g['visiteurs'])} visiteurs)" for g in gros) + "."
    bits = []
    if prix:
        pm, fm = min(prix, key=lambda x: x[0])
        bits.append(f"Le ticket d'entrée le plus bas relevé : {fm.get('price_label') or str(pm) + ' €'}, au {fm['name']}, d'après la dernière grille tarifaire publiée.")
    if free:
        bits.append(f"{len(free)} festival{'s' if len(free) > 1 else ''} à entrée libre.")
    if d["kind"] != "mois":
        cnt = {}
        for f in lst:
            for m in (f.get("mois") or []):
                cnt[m] = cnt.get(m, 0) + 1
        if cnt:
            top = max(MOIS_ORDRE, key=lambda m: cnt.get(m, 0))
            bits.append(f"Le mois le plus chargé est {top} ({cnt[top]} festivals).")
    p2 = " ".join(bits)
    rows = ""
    for f in lst:
        badge = "ok" if f.get("status") == "Dates annoncées" else "warn"
        tags = "".join(f'<span class="tag">{esc(g)}</span>' for g in (f.get("genres") or [])[:3])
        visit = f' · environ {fmt_n(f["visiteurs"])} visiteurs' if f.get("visiteurs") else ""
        rows += (f'<li class="gl"><a class="gl-name" href="{f["slug"]}.html">{esc(f["name"])}</a>'
                 f'<span class="gl-meta">{esc(f.get("city") or "")}{(", " + esc(f["region"])) if f.get("region") else ""} · {esc(f.get("dates") or "À confirmer")}{visit}</span>'
                 f'<span class="gl-meta"><span class="badge {badge}">{esc(f.get("status") or "")}</span> {esc(f.get("price_label") or "Tarifs non publiés")}</span>'
                 f'<span class="tags">{tags}</span></li>\n')
    desc = f"{n} festivals de musique {d['ou']} : dates, lieu, prix et line-up. {len(conf)} aux dates confirmées, classés des plus gros aux plus petits."
    desc = desc if len(desc) <= 160 else desc[:157] + "…"
    url = f"{BASE_URL}/{d['slug']}.html"
    ld = '<script type="application/ld+json">' + json.dumps({"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": 1, "name": "Accueil", "item": f"{BASE_URL}/index.html"},
        {"@type": "ListItem", "position": 2, "name": d["h1"], "item": url}]}, ensure_ascii=False) + "</script>\n"
    ld += '<script type="application/ld+json">' + json.dumps({"@context": "https://schema.org", "@type": "ItemList", "name": d["h1"],
        "numberOfItems": n, "itemListElement": [{"@type": "ListItem", "position": i + 1, "name": f["name"], "url": f'{BASE_URL}/{f["slug"]}.html'} for i, f in enumerate(lst)]}, ensure_ascii=False) + "</script>\n"
    page = head(group_title(d["h1"]), desc, url, ld)
    page += f'''<main id="contenu" class="wrap fiche groupe">
<nav class="crumb" aria-label="Fil d'Ariane"><a href="index.html">Accueil</a> › <span>{esc(d["h1"])}</span></nav>
<h1>{esc(d["h1"])}</h1>
<p class="lead">{esc(p1)}</p>
{('<p>' + esc(p2) + '</p>') if p2 else ""}
<ul class="glist">
{rows}</ul>
<section class="box explore"><h2>Explorer d'autres festivals</h2>
{nav_groups(defs, d["slug"])}<p><a href="index.html">Voir tous les festivals, avec filtres par budget et tri</a></p></section>
<p class="small">Les dates marquées « à confirmer » n'ont pas encore été annoncées par une source officielle : vérifiez toujours sur le site du festival avant d'acheter un billet.</p>
</main>
{foot()}</body></html>
'''
    return page


FAVICON = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">
<defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#b0304f"/><stop offset=".55" stop-color="#e8506a"/><stop offset="1" stop-color="#f58a4e"/></linearGradient></defs>
<rect width="64" height="64" rx="14" fill="url(#g)"/>
<path d="M32 10l5.5 16.5L54 32l-16.5 5.5L32 54l-5.5-16.5L10 32l16.5-5.5z" fill="#fff"/>
</svg>
"""


def head(title, desc, canonical, extra=""):
    return f'''<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="google-site-verification" content="-dZV6mVuMr0xR11z0I5KrbklOmMtcFE7X_o8ikekrAo" />
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<link rel="canonical" href="{esc(canonical)}">
<link rel="icon" href="favicon.svg" type="image/svg+xml">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:type" content="website">
<meta property="og:locale" content="fr_FR">
<meta property="og:site_name" content="{SITE}">
<meta property="og:url" content="{esc(canonical)}">
<meta property="og:image" content="{BASE_URL}/og-image.png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="{SITE} : dates, lieux, prix et line-up des grands festivals">
<meta name="twitter:card" content="summary_large_image">
<link rel="preload" href="fonts/big-shoulders-display.woff2" as="font" type="font/woff2" crossorigin>
<link rel="stylesheet" href="style.css?v={CSS_V}">
{extra}</head>
<body>
<a class="skip" href="#contenu">Aller au contenu</a>
<header class="top"><div class="wrap"><a class="brand" href="index.html">Festi<span>Guide</span></a><nav><a href="index.html">Festivals</a><a href="guide-securite-festival.html">Guide sécurité</a></nav></div></header>
'''


def foot():
    return f'''<footer><div class="wrap">
<p>Informations rassemblées le {UPDATED} depuis des sources publiques, citées en bas de chaque fiche. Dates, prix et programmations changent souvent : vérifiez toujours sur le site officiel avant d'acheter un billet. {SITE} n'est affilié à aucun festival et ne vend aucun billet.</p>
<nav class="foot-nav" aria-label="Informations légales">
<a href="index.html">Accueil</a><a href="guide-securite-festival.html">Guide sécurité</a><a href="mentions-legales.html">Mentions légales</a><a href="conditions-utilisation.html">Conditions d'utilisation</a><a href="confidentialite.html">Confidentialité</a><a href="cookies.html">Cookies</a>
</nav>
<p class="foot-copy">© 2026 {SITE} — Éditeur : {EDITEUR}</p>
</div></footer>
''' + (f'<script data-goatcounter="https://{GOATCOUNTER}.goatcounter.com/count" async src="goatcounter.js"></script>\n' if GOATCOUNTER else "")


def newsletter_form(f=None, genres=()):
    """Formulaire d'alerte Brevo, en HTML simple : aucun script tiers, rien n'est envoyé avant le clic sur « S'inscrire ».
    Brevo envoie ensuite un e-mail de confirmation (double opt-in, à activer dans Brevo)."""
    if not NEWSLETTER_ACTION:
        return ""
    if f:
        titre = (f"Préviens-moi quand les dates de {f['name']} sont confirmées" if not f.get("iso")
                 else f"Reçois les nouvelles de {f['name']} : line-up, billetterie, infos pratiques")
        extra = f'<input type="hidden" name="FESTIVAL" value="{esc(f["slug"])}">'
        ctx = f"fiche-{f['slug']}"
    else:
        titre = "Alerte festivals : un e-mail quand de nouvelles dates sont confirmées"
        opts = "".join(f"<option>{esc(g)}</option>" for g in genres)
        extra = (f'<label class="nl-l">Ton style préféré (facultatif)<select name="STYLE"><option value="">Tous les styles</option>{opts}</select></label>'
                 if genres else "")
        ctx = "accueil"
    return f'''<section class="nl" aria-labelledby="nl-t-{ctx}">
<h2 id="nl-t-{ctx}">{esc(titre)}</h2>
<p class="small">Un e-mail seulement quand il y a du nouveau. Pas de pub, désinscription en un clic.</p>
<form method="POST" action="{esc(NEWSLETTER_ACTION)}" data-goatcounter-click="newsletter-{esc(ctx)}">
<label class="nl-l">Ton e-mail<input type="email" name="EMAIL" required autocomplete="email" placeholder="toi@exemple.fr"></label>
{extra}
<input type="text" name="email_address_check" value="" class="nl-hp" tabindex="-1" autocomplete="off" aria-hidden="true">
<input type="hidden" name="locale" value="fr">
<input type="hidden" name="html_type" value="simple">
<input type="hidden" name="SOURCE" value="{esc(ctx)}">
<label class="nl-ok"><input type="checkbox" name="OPT_IN" value="1" required><span>J'ai 15 ans ou plus et j'accepte de recevoir les alertes {SITE} par e-mail. Je peux me désinscrire à tout moment. Détails dans la <a href="confidentialite.html">politique de confidentialité</a>.</span></label>
<button type="submit" class="btn">S'inscrire</button>
</form>
</section>
'''


def build(fests):
    OUT.mkdir(parents=True, exist_ok=True)
    fests = sorted(fests, key=tri_key)
    defs = group_defs(fests)

    mois_dispo = [m for m in MOIS_ORDRE if any(m in (f.get("mois") or []) for f in fests)]
    regions = sorted({f.get("region") for f in fests if f.get("region")}, key=norm)
    genres = sorted({g for f in fests for g in (f.get("genres") or [])}, key=norm)

    # ---------- page d'accueil ----------
    cards = ""
    date_pos = {f["slug"]: i for i, f in enumerate(fests)}
    by_size = sorted(fests, key=lambda f: (-(f.get("visiteurs") or 0), date_pos[f["slug"]]))
    for f in by_size:
        searchable = " ".join(filter(None, [f["name"], f.get("city"), f.get("region"), f.get("venue")]))
        prix = f.get("price_label") or "Tarifs non publiés"
        pn = prix_num(f)
        cd = f'<span class="cd" data-start="{f["iso"][0]}" data-end="{f["iso"][1]}"></span>' if f.get("iso") else ""
        free = '<span class="free">Entrée libre</span>' if is_free(f) else ""
        visit = f'<span class="vis">≈ {fmt_n(f["visiteurs"])} visiteurs</span>' if f.get("visiteurs") else ""
        lieu = esc(f.get("city") or "")
        if f.get("region") and f.get("region") not in (f.get("city") or ""):
            lieu += f' <span class="reg">· {esc(f["region"])}</span>'
        styles = " · ".join(esc(g) for g in (f.get("genres") or [])[:3])
        cards += f'''<article class="card" data-i="{len(cards.split("</article>")) - 1}" data-d="{date_pos[f["slug"]]}" data-visit="{f.get("visiteurs") or ""}" data-price="{"" if pn is None else pn}" data-free="{1 if is_free(f) else 0}" data-name="{esc(norm(searchable))}" data-mois="{esc(" ".join(f.get("mois") or []))}" data-region="{esc(f.get("region") or "")}" data-genres="{esc("|".join(f.get("genres") or []))}">
  {date_block(f)}
  <div class="what"><h3><a href="{f["slug"]}.html">{esc(f["name"])}</a></h3>
  <p class="meta">{lieu}</p>{('<p class="styles">' + styles + '</p>') if styles else ""}</div>
  <div class="aside"><span class="price">{esc(prix)}</span>{free}{visit}{cd}</div>
</article>
'''
    mcount = {m: sum(1 for f in fests if m in (f.get("mois") or [])) for m in mois_dispo}
    gcount = {}
    for f in fests:
        for g in (f.get("genres") or []):
            gcount[g] = gcount.get(g, 0) + 1
    top_g = sorted(gcount, key=lambda g: (-gcount[g], norm(g)))[:8]
    months_html = "".join(f'<button type="button" class="mt" data-m="{m}"><span>{ABBR.get(m, m)}</span><b>{mcount[m]}</b></button>' for m in mois_dispo)
    genres_html = "".join(f'<button type="button" class="gc" data-g="{esc(g)}">{esc(g)} <b>{gcount[g]}</b></button>' for g in top_g)
    nb_free = sum(1 for f in fests if is_free(f))
    opt = lambda vals: "".join(f"<option>{esc(v)}</option>" for v in vals)
    nb_annonces = sum(1 for f in fests if f.get("status") == "Dates annoncées")
    idx = head(
        f"{len(fests)} festivals de musique : dates, prix | {SITE}",
        f"Les {len(fests)} plus gros festivals de musique de France et de Belgique : dates, lieu, prix, artistes, plan et site officiel. Rock, électro, rap, jazz, metal.",
        f"{BASE_URL}/index.html",
        extra='<script type="application/ld+json">' + json.dumps({"@context": "https://schema.org", "@type": "WebSite", "name": SITE, "url": BASE_URL + "/", "inLanguage": "fr-FR", "description": "Annuaire gratuit de festivals de musique en France et en Belgique."}, ensure_ascii=False) + "</script>\n")
    idx += f'''<main id="contenu">
<section class="hero"><div class="wrap">
<h1>Trouve ton festival de musique en France et en Belgique</h1>
<p>{len(fests)} festivals de France et de Belgique avec leurs dates, leur prix, leur line-up et comment y aller. {nb_annonces} ont déjà leurs dates confirmées par une source officielle, les autres sont marqués « à confirmer ».</p>
</div></section>
<section class="wrap filters" aria-label="Filtres">
<input id="q" type="search" placeholder="Festival, ville ou région" aria-label="Rechercher">
<select id="mois" aria-label="Mois"><option value="">Tous les mois</option>{opt(mois_dispo)}</select>
<select id="region" aria-label="Région"><option value="">Toutes les régions</option>{opt(regions)}</select>
<select id="genre" aria-label="Genre"><option value="">Tous les genres</option>{opt(genres)}</select>
<select id="budget" aria-label="Budget"><option value="">Tous les budgets</option><option value="free">Entrée libre</option><option value="30">Dès 30 € ou moins</option><option value="80">Dès 80 € ou moins</option></select>
<select id="tri" aria-label="Trier"><option value="gros">Tri : les plus gros d'abord</option><option value="date">Tri : prochaine édition</option><option value="prix">Tri : prix croissant</option><option value="az">Tri : A → Z</option></select>
</section>
<section class="wrap quick" aria-label="Raccourcis">
<div class="months" role="group" aria-label="Filtrer par mois">{months_html}</div>
<div class="gchips" role="group" aria-label="Filtrer par style">{genres_html}</div>
</section>
<section class="wrap"><p id="count" class="count"></p>
<div class="grid" id="grid">
{cards}</div>
<p id="empty" class="empty" hidden>Aucun festival ne correspond à ta recherche. <button type="button" id="reset" class="linkbtn">Tout afficher</button></p></section>
<div class="wrap">{newsletter_form(None, top_g)}</div>
<section class="wrap note guide-teaser"><h2>Avant d'y aller</h2>
<p>Faux billets en revente, chaleur, bruit, fouilles à l'entrée : le <a href="guide-securite-festival.html">guide sécurité festival</a> rassemble les règles officielles et les bons réflexes, sources à l'appui.</p></section>
<section class="wrap note explore"><h2>Explorer par mois, style ou lieu</h2>
{nav_groups(defs)}</section>
<section class="wrap note"><h2>Comment lire ces infos</h2>
<p>Par défaut, les festivals sont classés du plus gros au moins gros d'après la <strong>fréquentation publiée</strong> de leur dernière édition (chaque fiche cite le chiffre, l'édition et la source). Ceux dont aucun chiffre fiable n'a été trouvé sont placés après, par date. Le tri « prochaine édition » les classe par date. Quand les dates ne sont pas encore officielles, la fiche affiche le mois habituel et la mention « Dates à confirmer ».</p>
<p>Les prix et les affiches sont souvent ceux de la <strong>dernière édition connue</strong>, car peu de festivals publient leurs tarifs un an à l'avance. Chaque fiche précise l'édition de référence et cite ses sources.</p>
</section>
</main>
{foot()}<script src="script.js?v={JS_V}"></script>
</body></html>
'''
    (OUT / "index.html").write_text(idx, encoding="utf-8")

    # ---------- fiches ----------
    for f in fests:
        crumb_ld = {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Accueil", "item": f"{BASE_URL}/index.html"},
            {"@type": "ListItem", "position": 2, "name": f["name"], "item": f'{BASE_URL}/{f["slug"]}.html'}]}
        ld = '<script type="application/ld+json">' + json.dumps(crumb_ld, ensure_ascii=False) + "</script>\n"
        if f.get("iso"):
            data = {"@context": "https://schema.org", "@type": "Festival", "name": f["name"],
                    "startDate": f["iso"][0], "endDate": f["iso"][1],
                    "eventStatus": "https://schema.org/EventScheduled",
                    "eventAttendanceMode": "https://schema.org/OfflineEventAttendanceMode",
                    "location": {"@type": "Place", "name": f.get("venue") or f.get("city"),
                                 "address": {"@type": "PostalAddress", "addressLocality": f.get("city"),
                                             "addressRegion": f.get("region"),
                                             "addressCountry": "BE" if f.get("country") == "Belgique" else "FR"}},
                    "url": f.get("official")}
            ld += '<script type="application/ld+json">' + json.dumps(data, ensure_ascii=False) + "</script>\n"
        desc = f'{f["name"]} : {f.get("dates")}, {f.get("city")}. Prix, programmation, accès et site officiel.'
        p = head(make_title(f), desc, f'{BASE_URL}/{f["slug"]}.html', ld)
        voisins = "".join(
            f'<li><a href="{g["slug"]}.html">{esc(g["name"])}</a><span class="small">{esc(g.get("city") or "")} · {esc(g.get("dates") or "Dates à confirmer")}</span></li>'
            for g in related(f, fests))
        prices = f.get("prices") or []
        rows = "".join(f"<tr><td>{esc(a)}</td><td>{esc(b)}</td></tr>" for a, b in prices) \
            or '<tr><td colspan="2">Tarifs pas encore publiés pour la prochaine édition.</td></tr>'
        acts = "".join(f'<span class="act">{esc(a)}</span>' for a in (f.get("lineup") or []))
        chips = f'<p class="lineup">{acts}</p>' if acts else '<p class="small">Programmation pas encore annoncée.</p>'
        acc = "".join(f"<li>{esc(a)}</li>" for a in (f.get("access") or [])) or "<li>Voir le site officiel.</li>"
        tips = "".join(f"<li>{esc(a)}</li>" for a in (f.get("tips") or [])) or "<li>Rien de particulier à signaler.</li>"
        src = "".join(f'<li><a href="{esc(u)}" target="_blank" rel="noopener">{esc(t)}</a></li>' for t, u in (f.get("sources") or []))
        gen = "".join(f'<span class="tag">{esc(g)}</span>' for g in (f.get("genres") or []))
        q = html.escape((f.get("maps_q") or f.get("city") or "").replace(" ", "+"), quote=True)
        badge = "ok" if f.get("status") == "Dates annoncées" else "warn"
        official = f.get("official") or ""
        dj = duree(f)
        cdt = f'<span class="cd big" data-start="{f["iso"][0]}" data-end="{f["iso"][1]}"></span>' if f.get("iso") else "<b>À confirmer</b>"
        tiles = f'''<ul class="tiles">
<li><small>Départ</small>{cdt}</li>
<li><small>Durée</small><b>{(str(dj) + (" jours" if dj > 1 else " jour")) if dj else "À confirmer"}</b></li>
<li><small>Budget</small><b>{esc(f.get("price_label") or "Non publié")}</b></li>
<li><small>Où</small><b>{esc(f.get("city") or "")}</b></li>
{('<li><small>Fréquentation</small><b>≈ ' + fmt_n(f["visiteurs"]) + '</b></li>') if f.get("visiteurs") else ""}
</ul>
{('<p class="small">Fréquentation : ' + esc(f.get("visiteurs_note") or "") + '</p>') if f.get("visiteurs") else ""}
<p class="actions">{('<a class="btn ghost" href="' + f["slug"] + '.ics" download data-goatcounter-click="agenda-' + f["slug"] + '">' + ic("cal") + 'Ajouter à mon agenda</a>') if f.get("iso") else ""}<button type="button" class="btn ghost share-btn" data-title="{esc(f["name"])}" data-goatcounter-click="partage-{f["slug"]}">{ic("share")}Partager</button><span class="small share-msg" aria-live="polite"></span></p>'''
        if f.get("iso"):
            (OUT / f'{f["slug"]}.ics').write_text(ics(f), encoding="utf-8", newline="")
        lien_off = f'<a class="btn" href="{esc(official)}" target="_blank" rel="noopener" data-goatcounter-click="billetterie-{f["slug"]}" data-goatcounter-title="Billetterie {esc(f["name"])}">Site officiel et billetterie ↗</a>' if official else '<p class="small">Site officiel non renseigné.</p>'
        p += f'''<main id="contenu" class="wrap fiche">
<nav class="crumb" aria-label="Fil d'Ariane"><a href="index.html">Accueil</a> › <span>{esc(f["name"])}</span></nav>
<h1>{esc(f["name"])}</h1>
<p class="lead">{esc(f.get("about") or "")}</p>
{tiles}
<div class="two">
<section class="box"><h2>Prochaine édition</h2>
<ul class="facts">
<li><strong>Dates :</strong> {esc(f.get("dates") or "À confirmer")} <span class="badge {badge}">{esc(f.get("status") or "")}</span></li>
<li><strong>Lieu :</strong> {esc(f.get("venue") or f.get("city") or "")}</li>
<li><strong>Ville :</strong> {esc(f.get("city") or "")}{(", " + esc(f["region"])) if f.get("region") else ""}, {esc(f.get("country") or "France")}</li>
<li><strong>Style :</strong> {gen}</li>
</ul>
<p class="small">{esc(f.get("status_note") or "")}</p>
{lien_off}
</section>
<section class="box"><h2>Prix</h2>
<table class="prices">{rows}</table>
<p class="small">{esc(f.get("prices_note") or "")}</p>
</section>
</div>
<section class="box"><h2>Programmation : {esc(f.get("last_label") or "dernière édition")}{(" (" + esc(f["last_dates"]) + ")") if f.get("last_dates") else ""}</h2>
{chips}
<p class="small">{esc(f.get("lineup_note") or "")}</p>
</section>
<section class="box"><h2>Plan et localisation</h2>
<div class="map-wrap" data-map-src="https://www.google.com/maps?q={q}&amp;output=embed" data-map-title="Carte : {esc(f["name"])}">
  <div class="map-ph">
    <p class="map-ph-title">{ic("map")}Carte non chargée</p>
    <p class="small">Cette carte est fournie par Google Maps. En l'affichant, vous autorisez Google à recevoir votre adresse IP et à déposer des cookies sur votre appareil. Rien n'est envoyé à Google tant que vous ne cliquez pas.</p>
    <button type="button" class="btn map-btn">Afficher la carte</button>
    <p class="small">Vous pouvez aussi <a href="https://www.google.com/maps/search/?api=1&amp;query={q}" target="_blank" rel="noopener">ouvrir le lieu dans Google Maps ↗</a> — ou lire notre <a href="cookies.html">politique de cookies</a>.</p>
  </div>
</div>
<p class="small">Le plan détaillé des scènes est publié chaque année par le festival : consultez le site officiel.</p>
</section>
<div class="two">
<section class="box"><h2>Y aller</h2><ul>{acc}</ul></section>
<section class="box"><h2>À savoir</h2><ul>{tips}</ul>
<p class="small">Billets, chaleur, bruit, fouilles : lire le <a href="guide-securite-festival.html">guide sécurité festival</a>.</p></section>
</div>
{newsletter_form(f)}
<section class="box"><h2>Autres festivals à découvrir</h2><ul class="rel">{voisins}</ul>
{voir_aussi(f, defs)}</section>
<section class="box"><h2>Sources</h2><ul class="src">{src}</ul><p class="small">Mis à jour le {UPDATED}.</p></section>
</main>
{foot()}<script src="script.js?v={JS_V}"></script>
</body></html>
'''
        (OUT / f'{f["slug"]}.html').write_text(p, encoding="utf-8")

    for d in defs:
        (OUT / f'{d["slug"]}.html').write_text(group_page(d, defs, fests), encoding="utf-8")

    build_legal(len(fests))
    build_guide(fests)
    if NEWSLETTER_ACTION:
        build_inscription()
    shutil.copy(Path(__file__).parent / "goatcounter.js", OUT / "goatcounter.js")

    # ---------- sitemap + robots ----------
    urls = "".join(f"  <url><loc>{BASE_URL}/{s}</loc></url>\n"
                   for s in ["index.html", GUIDE_SLUG] + [f'{d["slug"]}.html' for d in defs] + [f'{f["slug"]}.html' for f in fests] + LEGAL_PAGES)
    (OUT / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + urls + "</urlset>\n", encoding="utf-8")
    (OUT / "robots.txt").write_text(f"User-agent: *\nAllow: /\n\nSitemap: {BASE_URL}/sitemap.xml\n", encoding="utf-8")
    llms = f"""# {SITE}

> Annuaire gratuit de {len(fests)} festivals de musique en France et en Belgique : dates, lieu, prix, line-up, accès et site officiel. Chaque fiche cite ses sources. Aucun billet n'est vendu ici : les achats se font sur les billetteries officielles.

Règles de lecture : une date n'est donnée comme confirmée (« Dates annoncées ») que si une source officielle la confirme ; sinon la fiche indique « Dates à confirmer ». Données indicatives, à vérifier sur le site officiel du festival.

## Pages principales
- [Tous les festivals]({BASE_URL}/index.html): liste complète, filtres par mois, région, style et budget
- [Guide sécurité festival]({BASE_URL}/{GUIDE_SLUG}): billets et revente, fouilles, bruit, chaleur, secours, avec sources officielles
- [Plan du site (sitemap)]({BASE_URL}/sitemap.xml): une page par festival, au format {BASE_URL}/<slug>.html
- [Conditions d'utilisation]({BASE_URL}/conditions-utilisation.html)
- [Mentions légales]({BASE_URL}/mentions-legales.html)
- [Politique de confidentialité]({BASE_URL}/confidentialite.html)
- [Politique de cookies]({BASE_URL}/cookies.html)

## Listes par mois, style et lieu
""" + "".join(f"- [{d['h1']}]({BASE_URL}/{d['slug']}.html): {len(d['list'])} festivals\n" for d in defs) + """
## Festivals
""" + "".join(f"- [{f['name']}]({BASE_URL}/{f['slug']}.html): {f.get('city','')}, {f.get('dates') or 'Dates à confirmer'}\n" for f in fests)
    (OUT / "llms.txt").write_text(llms, encoding="utf-8")
    (OUT / "favicon.svg").write_text(FAVICON, encoding="utf-8")
    (OUT / "fond-hero.svg").write_text(scene_svg(), encoding="utf-8")
    (OUT / "motif.svg").write_text(motif_svg(), encoding="utf-8")
    og = Path(__file__).parent / "og-image.png"  # image de partage : source dans og-image.html
    if og.exists() and og.resolve() != (OUT / "og-image.png").resolve():
        shutil.copy(og, OUT / "og-image.png")
    return fests


GUIDE_SLUG = "guide-securite-festival.html"
GUIDE_SOURCES = [
    ("Code pénal, article 313-6-2 (revente de billets) — Légifrance", "https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000025492294"),
    ("Décret n° 2017-1244 du 7 août 2017 relatif aux sons amplifiés — Légifrance", "https://www.legifrance.gouv.fr/jorf/id/JORFTEXT000035388481"),
    ("Les recommandations « canicule » — ministère de la Santé", "https://sante.gouv.fr/IMG/pdf/Les_recommandations_canicule_.pdf"),
    ("Les fortes chaleurs nous concernent tous — Santé publique France", "https://www.santepubliquefrance.fr/les-actualites/les-fortes-chaleurs-nous-concernent-tous-adoptons-les-bons-reflexes"),
    ("Drogues Info Service — drogues.gouv.fr", "https://www.drogues.gouv.fr/drogues-info-service-informer-dialoguer-et-offrir-une-aide-personnalisee"),
]


def build_guide(fests):
    """Guide pratique : uniquement des règles sourcées (liste GUIDE_SOURCES) et des réflexes de bon sens.
    Les exemples de festivals viennent de festivals.json, rien n'est inventé."""
    revente = [f for f in fests if any("revente" in norm(t) for t in (f.get("tips") or []) + [a for a, _ in (f.get("prices") or [])])]
    canicule = [f for f in fests if "canicule" in norm(f.get("status_note") or "")]
    lien = lambda f: f'<a href="{f["slug"]}.html">{esc(f["name"])}</a>'
    ex_revente = (f'<p>Sur {SITE}, {len(revente)} fiches signalent une revente officielle : '
                  + ", ".join(lien(f) for f in revente) + ". Pour les autres, cherche « revente » dans la FAQ du site officiel.</p>") if revente else ""
    ex_chaleur = "".join(f'<p>Ce n\'est pas théorique : {lien(f)} — {esc(f["status_note"])}</p>' for f in canicule[:1])
    temoin = (f'<blockquote class="temoin"><p>{esc(GUIDE_TEMOIGNAGE)}</p><footer>— {EDITEUR}, sécurité événementielle en festival</footer></blockquote>'
              if GUIDE_TEMOIGNAGE else "")
    src = "".join(f'<li><a href="{esc(u)}" target="_blank" rel="noopener">{esc(t)} ↗</a></li>' for t, u in GUIDE_SOURCES)
    url = f"{BASE_URL}/{GUIDE_SLUG}"
    title = "Sécurité en festival : billets, bruit, chaleur | " + SITE
    desc = "Éviter les faux billets, passer les fouilles, protéger ses oreilles, tenir sous la chaleur : les règles officielles et les bons réflexes avant un festival."
    ld = '<script type="application/ld+json">' + json.dumps({"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": 1, "name": "Accueil", "item": f"{BASE_URL}/index.html"},
        {"@type": "ListItem", "position": 2, "name": "Guide sécurité festival", "item": url}]}, ensure_ascii=False) + "</script>\n"
    ld += '<script type="application/ld+json">' + json.dumps({"@context": "https://schema.org", "@type": "Article", "headline": "Guide sécurité festival",
        "description": desc, "inLanguage": "fr-FR", "author": {"@type": "Person", "name": EDITEUR}, "publisher": {"@type": "Organization", "name": SITE},
        "mainEntityOfPage": url}, ensure_ascii=False) + "</script>\n"
    p = head(title, desc, url, ld)
    p += f'''<main id="contenu" class="wrap fiche guide">
<nav class="crumb" aria-label="Fil d'Ariane"><a href="index.html">Accueil</a> › <span>Guide sécurité festival</span></nav>
<h1>Guide sécurité festival</h1>
<p class="lead">Acheter un billet sans se faire avoir, passer l'entrée sans perdre une heure, tenir plusieurs jours au soleil et devant les enceintes. Chaque règle citée renvoie à sa source officielle, en bas de page.</p>
{temoin}
<nav class="toc" aria-label="Sommaire"><ol>
<li><a href="#billets">Billets</a></li><li><a href="#entree">Entrée et fouilles</a></li><li><a href="#bruit">Bruit</a></li>
<li><a href="#chaleur">Chaleur</a></li><li><a href="#secours">Malaise, alcool, drogues</a></li><li><a href="#sac">Le sac</a></li>
</ol></nav>

<section class="box" id="billets"><h2>1. Billets : seulement l'officiel</h2>
<p>Achète sur la billetterie officielle du festival ou sur sa plateforme de revente officielle. Chaque fiche {SITE} renvoie vers le site officiel, jamais vers un revendeur.</p>
<p><strong>Ce que dit la loi :</strong> en France, revendre des billets de spectacle de manière habituelle sans l'autorisation de l'organisateur est puni de 15 000 € d'amende (article 313-6-2 du Code pénal). Un billet acheté sur un site de revente non autorisé n'a donc aucune garantie d'être valable.</p>
<ul class="facts">
<li><strong>Signal d'alerte :</strong> le vendeur demande un virement, un coupon ou un paiement « entre proches », sans protection acheteur.</li>
<li><strong>Signal d'alerte :</strong> un prix bien plus bas que le tarif officiel, ou une pression pour payer tout de suite.</li>
<li><strong>Signal d'alerte :</strong> un billet envoyé en capture d'écran. Un e-billet se copie en deux secondes : s'il a été vendu plusieurs fois, seule la première personne scannée entre.</li>
</ul>
{ex_revente}
</section>

<section class="box" id="entree"><h2>2. Entrée et fouilles</h2>
<p>Palpation et fouille des sacs sont la règle à l'entrée des grands festivals. Aux heures d'ouverture et avant les têtes d'affiche, la file peut être longue : arrive tôt.</p>
<ul class="facts">
<li>La liste des objets interdits change d'un festival à l'autre (contenants, gourdes, chaises, parapluies, batteries…) : lis la FAQ du site officiel avant de faire ton sac. Ce qui est refusé à l'entrée ne t'est pas toujours rendu.</li>
<li>Un petit sac se contrôle plus vite qu'un gros.</li>
<li>Garde ton billet et ta pièce d'identité à portée de main : certains festivals vérifient l'identité (billets nominatifs, âge).</li>
</ul>
</section>

<section class="box" id="bruit"><h2>3. Bruit : protège tes oreilles</h2>
<p>En France, le décret du 7 août 2017 limite le son à 102 décibels (dB(A)) en moyenne sur 15 minutes partout où le public a accès, et oblige l'organisateur à <strong>mettre gratuitement des protections auditives</strong> à la disposition du public. Demande-les à l'accueil ou aux stands d'information.</p>
<ul class="facts">
<li>Ne reste pas collé aux enceintes et fais des pauses au calme.</li>
<li>Des sifflements dans les oreilles qui durent encore le lendemain sont un signal à prendre au sérieux : parles-en à un médecin.</li>
</ul>
</section>

<section class="box" id="chaleur"><h2>4. Chaleur : boire avant d'avoir soif</h2>
<p>Le ministère de la Santé recommande, en cas de fortes chaleurs, de <strong>boire régulièrement sans attendre d'avoir soif</strong>, d'éviter l'alcool, qui favorise la déshydratation, et de se protéger la tête du soleil.</p>
{ex_chaleur}
<ul class="facts">
<li>Repère les points d'eau et les zones d'ombre en arrivant.</li>
<li>Casquette, crème solaire, vêtements clairs et amples.</li>
<li>Mange vraiment : un repas solide aide l'organisme à tenir.</li>
</ul>
</section>

<section class="box" id="secours"><h2>5. Malaise, alcool, drogues</h2>
<ul class="facts">
<li>Repère les postes de secours sur le plan du festival dès ton arrivée.</li>
<li>Un ami ne va pas bien ? Ne le laisse pas seul : préviens les secouristes ou l'équipe de sécurité la plus proche.</li>
<li>Urgence : <strong>15</strong> (SAMU) ou <strong>112</strong> (numéro d'urgence européen, aussi en Belgique).</li>
<li>Questions sur l'alcool ou les drogues : <strong>Drogues Info Service, 0 800 23 13 13</strong>, gratuit et anonyme, 7 jours sur 7 de 8 h à 2 h.</li>
<li>Ne laisse pas ton verre sans surveillance.</li>
</ul>
</section>

<section class="box" id="sac"><h2>6. Le sac du festivalier</h2>
<ul class="facts">
<li>Billet et pièce d'identité</li>
<li>Bouchons d'oreilles (ou ceux distribués sur place)</li>
<li>Casquette, crème solaire, coupe-vent</li>
<li>Téléphone chargé, et une batterie si le festival l'autorise</li>
<li>Un moyen de paiement accepté sur place : beaucoup de festivals fonctionnent sans espèces, vérifie sur le site officiel</li>
<li>Un point de rendez-vous fixé à l'avance avec tes amis : le réseau mobile sature souvent</li>
</ul>
</section>

<section class="box"><h2>Sources</h2><ul class="src">{src}</ul>
<p class="small">Les règles citées sont celles du droit français. En Belgique, les règles sur le son et la revente sont différentes : vérifie sur le site officiel du festival. Ce guide est informatif et ne remplace pas les consignes des organisateurs ni un avis médical. Mis à jour le {UPDATED}.</p></section>
<p><a href="index.html">Trouver un festival</a></p>
</main>
{foot()}</body></html>
'''
    (OUT / GUIDE_SLUG).write_text(p, encoding="utf-8")


def build_inscription():
    """Pages de retour de Brevo (à renseigner dans Brevo › formulaire › Paramètres) : après l'envoi, puis après le clic de confirmation.
    Hors sitemap et en noindex : elles n'ont d'intérêt que dans le parcours d'inscription."""
    pages = [
        ("inscription-envoyee.html", "Vérifie ta boîte mail",
         "Inscription presque terminée : clique sur le lien de confirmation reçu par e-mail.",
         "<p class=\"lead\">Il reste une étape : tu viens de recevoir un e-mail de confirmation. Clique sur le lien qu'il contient pour activer l'alerte.</p>"
         "<p>Rien reçu d'ici quelques minutes ? Regarde dans les courriers indésirables ou l'onglet Promotions. Sans clic de confirmation, aucune alerte ne te sera envoyée et ton adresse n'est pas ajoutée à la liste.</p>"),
        ("inscription-confirmee.html", "C'est confirmé",
         "Inscription à l'alerte FestiGuide confirmée.",
         "<p class=\"lead\">Ton inscription est confirmée. Tu recevras un e-mail quand il y a du nouveau : dates confirmées, line-up, billetterie.</p>"
         "<p>Pas de pub, et chaque e-mail contient un lien de désinscription. Détails dans la <a href=\"confidentialite.html\">politique de confidentialité</a>.</p>"),
    ]
    for slug, title, desc, body in pages:
        p = head(f"{title} | {SITE}", desc, f"{BASE_URL}/{slug}", '<meta name="robots" content="noindex">\n')
        p += f'''<main id="contenu" class="wrap legal">
<h1>{esc(title)}</h1>
{body}
<p><a class="btn" href="index.html">Voir les festivals</a> <a href="{GUIDE_SLUG}">Lire le guide sécurité</a></p>
</main>
{foot()}</body></html>
'''
        (OUT / slug).write_text(p, encoding="utf-8")


def legal_page(slug, title, desc, body):
    p = head(f"{title} | {SITE}", desc, f"{BASE_URL}/{slug}")
    p += f'''<main id="contenu" class="wrap legal">
<p class="crumb"><a href="index.html">← Retour au site</a></p>
<h1>{esc(title)}</h1>
{body}
<p class="small upd">Dernière mise à jour : {UPDATED}.</p>
</main>
{foot()}</body></html>
'''
    (OUT / slug).write_text(p, encoding="utf-8")


def build_legal(nb):
    # Textes qui dépendent des outils activés en haut du fichier (GOATCOUNTER, NEWSLETTER_ACTION).
    gc_privacy = "https://www.goatcounter.com/help/privacy"
    resume_collecte = (f'<li>{ic("check")}<strong>Aucun compte, aucun formulaire</strong> sur ce site</li>' if not NEWSLETTER_ACTION else
                       f'<li>{ic("check")}<strong>Aucun compte.</strong> Un seul formulaire : l\'alerte e-mail, facultative, envoyée à Brevo seulement si vous cliquez sur « S\'inscrire »</li>')
    collecte = ("<p><strong>Rien.</strong> {SITE} est un site statique : il n'y a ni base de données, ni formulaire, ni espace membre"
                + ("" if GOATCOUNTER else ", ni outil de mesure d'audience")
                + ". Vous pouvez consulter l'intégralité du site sans transmettre la moindre donnée personnelle à l'éditeur.</p>").replace("{SITE}", SITE)
    if NEWSLETTER_ACTION:
        collecte = (f"<p>{SITE} est un site statique, sans base de données ni espace membre. Vous pouvez consulter tout le site sans transmettre de donnée personnelle. "
                    "La seule exception est l'alerte e-mail, si vous choisissez de vous y inscrire (voir ci-dessous).</p>")
    audience = ('''<p>Le site est déclaré auprès de la <strong>Google Search Console</strong>, un outil qui indique à l'éditeur quelles requêtes de recherche mènent au site. Cet outil ne dépose aucun cookie sur votre appareil, n'ajoute aucun script à la page et ne fournit que des statistiques agrégées et anonymes. Il ne permet pas d'identifier un visiteur.</p>''')
    if GOATCOUNTER:
        audience += f'''<p>Le site utilise aussi <strong>GoatCounter</strong>, un outil de statistiques de fréquentation <strong>sans cookie</strong>. À chaque page vue, il reçoit la page consultée, la page de provenance, le type de navigateur et d'écran, et le pays déduit de l'adresse IP. D'après sa documentation, GoatCounter ne conserve pas l'adresse IP et n'utilise aucun identifiant persistant permettant de suivre un visiteur d'un site à l'autre. Il compte aussi les clics sur quelques boutons (billetterie, agenda, partage, inscription) pour savoir quelles fiches sont utiles.</p>
<ul class="facts">
<li><strong>Finalité :</strong> statistiques agrégées de fréquentation, pour améliorer le site</li>
<li><strong>Base légale :</strong> intérêt légitime de l'éditeur (article 6.1.f du RGPD) ; outil sans cookie, configuré pour se limiter à la mesure d'audience</li>
<li><strong>Destinataire :</strong> GoatCounter, en sous-traitant ; le script est hébergé sur {SITE} lui-même</li>
</ul>
<p class="small">Détails : <a href="{gc_privacy}" target="_blank" rel="noopener">politique de confidentialité de GoatCounter ↗</a>.</p>'''
    else:
        audience += "<p>Aucun outil de mesure d'audience de type Google Analytics n'est installé. Si cela devait changer, cette page serait mise à jour avant la mise en ligne.</p>"
    newsletter = ""
    if NEWSLETTER_ACTION:
        newsletter = f'''<section class="box"><h2>Alerte e-mail (newsletter)</h2>
<p>Si vous vous inscrivez à l'alerte e-mail, votre adresse électronique est envoyée à <strong>Brevo</strong>, le service d'envoi utilisé par l'éditeur, avec, si vous les indiquez, le festival ou le style qui vous intéresse et la page d'inscription. Brevo vous envoie d'abord un e-mail de confirmation : sans clic de votre part, vous ne recevez rien.</p>
<ul class="facts">
<li><strong>Finalité :</strong> vous prévenir quand des dates, une programmation ou une billetterie sont annoncées</li>
<li><strong>Base légale :</strong> votre consentement (article 6.1.a du RGPD), donné par la case à cocher et confirmé par e-mail</li>
<li><strong>Destinataire :</strong> l'éditeur et Brevo (Sendinblue SAS), en sous-traitant</li>
<li><strong>Conservation :</strong> jusqu'à votre désinscription ; une adresse sans aucune ouverture pendant 3 ans est supprimée</li>
<li><strong>Retrait :</strong> lien de désinscription en bas de chaque e-mail, ou demande à <a href="mailto:{CONTACT}">{CONTACT}</a></li>
</ul>
<p class="small">Aucune adresse n'est vendue, louée ni utilisée pour de la publicité.</p>
</section>
'''
    cu_donnees = ("Le site ne dépose aucun cookie et ne collecte aucune donnée personnelle par lui-même."
                  if not (NEWSLETTER_ACTION or GOATCOUNTER) else
                  "Le site ne dépose aucun cookie. " + ("Il mesure sa fréquentation sans cookie avec GoatCounter. " if GOATCOUNTER else "")
                  + ("La seule donnée personnelle collectée est l'adresse e-mail des personnes qui s'inscrivent à l'alerte. " if NEWSLETTER_ACTION else ""))
    cookies_gc = (f'''<section class="box"><h2>Statistiques sans cookie</h2>
<p>Le site mesure sa fréquentation avec GoatCounter, qui fonctionne <strong>sans cookie</strong>. Le script lit seulement un réglage local réservé à l'éditeur (pour exclure ses propres visites) et n'écrit rien sur votre appareil. Détails dans la <a href="confidentialite.html">politique de confidentialité</a>.</p>
</section>
''' if GOATCOUNTER else "")
    # ---------- mentions légales ----------
    legal_page("mentions-legales.html", "Mentions légales",
               f"Mentions légales de {SITE} : éditeur, hébergeur, contact, propriété intellectuelle et droit applicable.", f'''
<section class="box"><h2>Éditeur du site</h2>
<ul class="facts">
<li><strong>Éditeur :</strong> {EDITEUR}, particulier</li>
<li><strong>Statut :</strong> site personnel sans activité commerciale</li>
<li><strong>Contact :</strong> <a href="mailto:{CONTACT}">{CONTACT}</a></li>
<li><strong>Directeur de la publication :</strong> {EDITEUR}</li>
</ul>
<p class="small">Conformément à l'article 6, III, 2 de la loi n° 2004-575 du 21 juin 2004 pour la confiance dans l'économie numérique (LCEN), l'éditeur non professionnel d'un site peut ne pas publier son adresse postale, à condition d'avoir communiqué ses éléments d'identification à son hébergeur. Ils ne sont communicables que sur réquisition de l'autorité judiciaire.</p>
</section>

<section class="box"><h2>Hébergeur</h2>
<p>Le site est hébergé par GitHub Pages, service de :</p>
<ul class="facts">
<li><strong>Société :</strong> GitHub, Inc.</li>
<li><strong>Adresse :</strong> 88 Colin P. Kelly Jr. Street, San Francisco, CA 94107, États-Unis</li>
<li><strong>Site :</strong> <a href="https://github.com" target="_blank" rel="noopener">github.com</a></li>
</ul>
</section>

<section class="box"><h2>Objet du site</h2>
<p>{SITE} est un annuaire d'information qui rassemble les dates, lieux, tarifs et programmations de {nb} grands festivals. C'est un projet personnel, réalisé à titre non lucratif et pédagogique.</p>
<p><strong>Ce site ne vend aucun billet</strong>, ne prend aucune commission et n'est affilié, sponsorisé ni mandaté par aucun des festivals cités. Les achats se font exclusivement sur les billetteries officielles, vers lesquelles chaque fiche renvoie.</p>
</section>

<section class="box"><h2>Exactitude des informations</h2>
<p>Les informations sont rassemblées à partir de sources publiques, citées au bas de chaque fiche. Les dates, tarifs et programmations des festivals changent fréquemment, et certaines informations peuvent être périmées, incomplètes ou erronées.</p>
<p>Elles sont fournies à titre indicatif et sans garantie. <strong>Vérifiez toujours l'information sur le site officiel du festival avant d'acheter un billet, de réserver un hébergement ou de vous déplacer.</strong> La responsabilité de l'éditeur ne saurait être engagée en cas d'erreur, d'omission ou de modification intervenue après publication.</p>
<p>Vous avez repéré une erreur ? Signalez-la à <a href="mailto:{CONTACT}">{CONTACT}</a>, elle sera corrigée.</p>
</section>

<section class="box"><h2>Propriété intellectuelle</h2>
<p>Les textes rédigés pour ce site, sa mise en page et son code sont la propriété de l'éditeur. Ils peuvent être cités avec un lien vers la page d'origine.</p>
<p>Les noms, marques et logos des festivals appartiennent à leurs titulaires respectifs et ne sont mentionnés qu'à des fins d'information. Aucun visuel, affiche ou plan officiel de festival n'est reproduit sur ce site.</p>
</section>

<section class="box"><h2>Liens externes</h2>
<p>Ce site contient des liens vers des sites tiers, notamment les sites officiels des festivals et les sources citées. L'éditeur n'exerce aucun contrôle sur leur contenu et décline toute responsabilité à leur égard.</p>
</section>

<section class="box"><h2>Droit applicable</h2>
<p>Le présent site est soumis au droit français. En cas de litige, une solution amiable est recherchée en priorité. À défaut, et sous réserve des règles impératives de protection du consommateur, les tribunaux français sont compétents.</p>
<p>Les conditions d'usage du site figurent dans les <a href="conditions-utilisation.html">conditions d'utilisation</a>.</p>
</section>
''')

    # ---------- conditions d'utilisation ----------
    legal_page("conditions-utilisation.html", "Conditions d'utilisation",
               f"Conditions d'utilisation de {SITE} : accès gratuit, informations indicatives, classement des festivals, usage autorisé, droit applicable.", f'''
<section class="box"><h2>En résumé</h2>
<ul class="facts">
<li>{SITE} est un <strong>annuaire d'information gratuit</strong>, sans compte, sans paiement et sans vente de billets</li>
<li>Les informations sont <strong>indicatives</strong> : vérifiez toujours sur le site officiel du festival</li>
<li>Aucun placement payant : le classement ne dépend d'aucune rémunération</li>
<li>Vous pouvez citer le site avec un lien ; l'extraction en masse de la base n'est pas autorisée</li>
</ul>
</section>

<section class="box"><h2>Objet et acceptation</h2>
<p>Les présentes conditions encadrent l'usage du site {SITE}, édité par {EDITEUR} (voir les <a href="mentions-legales.html">mentions légales</a>). En consultant le site, vous les acceptez. Elles peuvent évoluer : la version en ligne, datée en bas de page, est celle qui s'applique.</p>
</section>

<section class="box"><h2>Un service d'information, pas une boutique</h2>
<p>{SITE} présente les dates, lieux, tarifs et programmations de {nb} festivals de musique de France et de Belgique. Le site <strong>ne vend aucun billet, aucun hébergement, aucun transport</strong>, ne perçoit aucune commission et ne vous demande aucun paiement.</p>
<p>Aucun contrat de vente n'étant conclu avec l'éditeur, il n'existe ni conditions générales de vente, ni délai de rétractation, ni procédure de remboursement sur {SITE}. Un achat de billet se fait sur la billetterie officielle du festival, et ce sont ses propres conditions (annulation, report, remboursement) qui s'appliquent.</p>
</section>

<section class="box"><h2>Accès au site</h2>
<p>Le site est accessible gratuitement, sans inscription, à tout moment, sauf interruption pour maintenance ou cas de force majeure. Les frais de connexion restent à votre charge. L'éditeur peut modifier ou retirer une page sans préavis.</p>
</section>

<section class="box"><h2>Exactitude des informations</h2>
<p>Les informations proviennent de sources publiques citées au bas de chaque fiche. Une date n'est marquée « Dates annoncées » que lorsqu'une source officielle la confirme ; sinon la fiche indique « Dates à confirmer ». Malgré ce soin, des erreurs ou des changements postérieurs à la publication restent possibles : les informations sont fournies <strong>à titre indicatif, sans garantie</strong>. Vérifiez sur le site officiel avant d'acheter un billet, de réserver ou de vous déplacer.</p>
<p>Vous repérez une erreur, ou vous êtes organisateur et souhaitez une correction ou un retrait ? Écrivez à <a href="mailto:{CONTACT}">{CONTACT}</a>.</p>
</section>

<section class="box"><h2>Classement et critères</h2>
<p>Par défaut, la page d'accueil classe les festivals par fréquentation publiée de la dernière édition, du plus gros au plus petit, lorsqu'un chiffre sourcé existe ; les autres sont classés par date de prochaine édition. Vous pouvez aussi trier par date, par prix ou par ordre alphabétique. <strong>Aucun festival ne paie pour apparaître ou monter dans le classement</strong>, et les liens vers les sites officiels ne sont pas des liens d'affiliation. Si cela changeait, la mention serait ajoutée clairement sur les pages concernées.</p>
</section>

<section class="box"><h2>Usage autorisé</h2>
<ul class="facts">
<li>Consultation, impression et partage de liens pour un usage personnel : autorisés</li>
<li>Citation courte avec un lien vers la page d'origine : autorisée</li>
<li>Indexation par les moteurs de recherche et consultation par des assistants ou agents d'IA agissant pour un utilisateur, dans le respect du fichier <a href="robots.txt">robots.txt</a> : autorisées</li>
<li>Extraction systématique ou reproduction substantielle de la base, ou usage qui perturbe le fonctionnement du site : interdits sans accord écrit</li>
</ul>
</section>

<section class="box"><h2>Propriété intellectuelle et liens</h2>
<p>Voir les <a href="mentions-legales.html">mentions légales</a> : les noms et marques des festivals appartiennent à leurs titulaires, et le site contient des liens vers des sites tiers dont l'éditeur ne contrôle pas le contenu.</p>
</section>

<section class="box"><h2>Données personnelles et cookies</h2>
<p>{cu_donnees} Détails dans la <a href="confidentialite.html">politique de confidentialité</a> et la <a href="cookies.html">politique de cookies</a>.</p>
</section>

<section class="box"><h2>Droit applicable</h2>
<p>Les présentes conditions sont soumises au droit français. En cas de litige, une solution amiable est recherchée en priorité ; à défaut, et sous réserve des règles impératives de protection du consommateur, les tribunaux français sont compétents.</p>
</section>
''')

    # ---------- confidentialité ----------
    legal_page("confidentialite.html", "Politique de confidentialité",
               f"Comment {SITE} traite vos données personnelles : aucune collecte directe, pas de compte, pas de publicité, pas de revente.", f'''
<section class="box"><h2>En résumé</h2>
<ul class="facts">
{resume_collecte}
<li>{ic("check")}<strong>Aucun cookie</strong> déposé par le site lui-même</li>
<li>{ic("check")}<strong>Aucune publicité</strong>, aucun traceur publicitaire, aucun revendeur de données</li>
<li>{ic("check")}<strong>Aucune donnée vendue, louée ou transmise</strong> à des fins commerciales</li>
<li>{ic("alert")}{"Trois autres situations" if NEWSLETTER_ACTION else "Trois situations"} détaillées ci-dessous : les <strong>journaux de l'hébergeur</strong>, les <strong>cartes Google Maps</strong> (qui ne se chargent qu'à votre demande) et le <strong>courriel</strong> que vous choisiriez d'envoyer</li>
</ul>
</section>

<section class="box"><h2>Qui est responsable du traitement</h2>
<p>{EDITEUR}, éditeur de {SITE}, joignable à <a href="mailto:{CONTACT}">{CONTACT}</a>. Le site est un projet personnel sans activité commerciale.</p>
</section>

<section class="box"><h2>Ce que le site collecte lui-même</h2>
{collecte}
</section>
{newsletter}

<section class="box"><h2>Journaux de connexion de l'hébergeur</h2>
<p>Le site est hébergé par <strong>GitHub Pages</strong> (GitHub, Inc., États-Unis). Comme tout serveur web, GitHub enregistre techniquement les requêtes qu'il reçoit : adresse IP, date et heure, page demandée, navigateur utilisé.</p>
<ul class="facts">
<li><strong>Finalité :</strong> fournir le service, assurer la sécurité du serveur et prévenir les abus</li>
<li><strong>Base légale :</strong> intérêt légitime de l'hébergeur (article 6.1.f du RGPD)</li>
<li><strong>Destinataire :</strong> GitHub, Inc., en sa qualité d'hébergeur</li>
<li><strong>Transfert hors Union européenne :</strong> oui, vers les États-Unis, encadré notamment par des clauses contractuelles types, selon la déclaration de confidentialité de GitHub</li>
</ul>
<p class="small">L'éditeur n'a pas accès à ces journaux et ne peut pas les exploiter. Pour en savoir plus : <a href="https://docs.github.com/fr/site-policy/privacy-policies/github-general-privacy-statement" target="_blank" rel="noopener">déclaration de confidentialité de GitHub ↗</a>.</p>
</section>

<section class="box"><h2>Cartes Google Maps</h2>
<p>Chaque fiche de festival propose une carte du lieu. <strong>Cette carte n'est pas chargée automatiquement.</strong> Tant que vous ne cliquez pas sur « Afficher la carte », aucune requête n'est envoyée à Google et aucun cookie n'est déposé.</p>
<p>Si vous choisissez de l'afficher, Google reçoit votre adresse IP, des informations sur votre appareil, et peut déposer des cookies. Le traitement relève alors de Google.</p>
<ul class="facts">
<li><strong>Base légale :</strong> votre consentement, donné par le clic (article 6.1.a du RGPD)</li>
<li><strong>Retrait :</strong> rechargez la page, la carte redevient inactive</li>
<li><strong>Responsable :</strong> Google Ireland Limited et Google LLC</li>
</ul>
<p class="small">Détails sur la page <a href="cookies.html">cookies</a> et dans les <a href="https://policies.google.com/privacy?hl=fr" target="_blank" rel="noopener">règles de confidentialité de Google ↗</a>.</p>
</section>

<section class="box"><h2>Mesure d'audience</h2>
{audience}
</section>

<section class="box"><h2>Si vous écrivez à l'éditeur</h2>
<p>L'adresse de contact est la seule porte d'entrée de données personnelles. Si vous envoyez un courriel, l'éditeur reçoit votre adresse électronique, votre message et les informations techniques que votre messagerie y joint.</p>
<ul class="facts">
<li><strong>Finalité :</strong> répondre à votre message (signalement d'une erreur, demande d'exercice de vos droits, question)</li>
<li><strong>Base légale :</strong> intérêt légitime à répondre aux personnes qui le contactent (article 6.1.f du RGPD)</li>
<li><strong>Destinataire :</strong> l'éditeur seul, via son service de messagerie (Gmail, Google Ireland Limited et Google LLC)</li>
<li><strong>Conservation :</strong> le temps de traiter votre demande, puis suppression</li>
</ul>
</section>

<section class="box"><h2>Durée de conservation</h2>
<p>{"Les adresses inscrites à l'alerte e-mail sont conservées jusqu'à la désinscription (voir ci-dessus). En dehors de cela, l'éditeur" if NEWSLETTER_ACTION else "L'éditeur"} ne conserve aucune donnée personnelle. Les journaux de l'hébergeur sont conservés selon la politique de GitHub. Un courriel que vous envoyez à l'adresse de contact est conservé le temps nécessaire au traitement de votre demande, puis supprimé.</p>
</section>

<section class="box"><h2>Vos droits</h2>
<p>Le RGPD vous donne un droit d'accès, de rectification, d'effacement, de limitation, d'opposition et de portabilité sur vos données personnelles.</p>
<p>Pour les exercer, écrivez à <a href="mailto:{CONTACT}">{CONTACT}</a>. {"Pour l'alerte e-mail, l'éditeur traite votre demande avec Brevo. " if NEWSLETTER_ACTION else "L'éditeur ne détenant aucune donnée vous concernant, "}une demande portant sur les journaux de connexion doit être adressée à GitHub, et une demande portant sur les cartes à Google.</p>
<p>Vous pouvez aussi définir des directives relatives au sort de vos données après votre décès (loi Informatique et Libertés, article 85). Si vous estimez que vos droits ne sont pas respectés, vous pouvez saisir la <strong>CNIL</strong> : <a href="https://www.cnil.fr/fr/plaintes" target="_blank" rel="noopener">cnil.fr/fr/plaintes ↗</a>, ou 3 place de Fontenoy, TSA 80715, 75334 Paris Cedex 07.</p>
</section>

<section class="box"><h2>Mineurs</h2>
<p>Le site est accessible à tous{". L'alerte e-mail est réservée aux personnes de 15 ans et plus, âge à partir duquel un mineur peut consentir seul en France (loi Informatique et Libertés, article 45)" if NEWSLETTER_ACTION else " et ne collecte aucune donnée, y compris auprès des mineurs"}. Les festivals cités appliquent leurs propres règles d'âge, indiquées sur leurs sites officiels.</p>
</section>
''')

    # ---------- cookies ----------
    legal_page("cookies.html", "Politique de cookies",
               f"{SITE} ne dépose aucun cookie. Les cartes Google Maps ne se chargent qu'après votre accord explicite.", f'''
<section class="box"><h2>Ce site ne dépose aucun cookie</h2>
<p>En naviguant sur {SITE}, <strong>aucun cookie n'est déposé sur votre appareil</strong> : ni cookie de session, ni cookie de mesure d'audience, ni cookie publicitaire. Le site ne vous demande donc aucun consentement et n'affiche aucun bandeau, parce qu'il n'a rien à vous faire accepter.</p>
<p class="small">Un bandeau cookies n'est obligatoire que lorsqu'un site dépose des traceurs non strictement nécessaires. Ce n'est pas le cas ici.</p>
</section>

<section class="box"><h2>La seule exception : les cartes Google Maps</h2>
<p>Chaque fiche de festival propose une carte du lieu, fournie par Google Maps. Elle fonctionne selon le principe du <strong>double clic</strong> recommandé par la CNIL :</p>
<ul class="facts">
<li><strong>À l'ouverture de la page :</strong> la carte est remplacée par un encadré gris. Aucune requête n'est envoyée à Google, aucun cookie n'est déposé.</li>
<li><strong>Si vous cliquez sur « Afficher la carte » :</strong> la carte se charge. Google reçoit alors votre adresse IP et peut déposer des cookies, notamment <code>NID</code> et <code>CONSENT</code>, utilisés pour les préférences d'affichage et la sécurité.</li>
<li><strong>Pour revenir en arrière :</strong> rechargez la page. La carte redevient inactive et ne se chargera pas tant que vous ne cliquerez pas à nouveau.</li>
</ul>
<p>Ce choix n'est pas mémorisé d'une page à l'autre, précisément parce que mémoriser votre choix supposerait de déposer un cookie.</p>
<p class="small">Durée de vie et finalité des cookies Google : <a href="https://policies.google.com/technologies/cookies?hl=fr" target="_blank" rel="noopener">règles de Google relatives aux cookies ↗</a>.</p>
</section>

{cookies_gc}<section class="box"><h2>Liens vers des sites tiers</h2>
<p>Les liens vers les sites officiels des festivals, leurs billetteries et les sources citées mènent vers des sites qui ont leurs propres pratiques en matière de cookies. Dès que vous quittez {SITE}, c'est la politique du site visité qui s'applique.</p>
</section>

<section class="box"><h2>Gérer les cookies dans votre navigateur</h2>
<p>Vous pouvez à tout moment bloquer ou supprimer les cookies déjà déposés depuis les réglages de votre navigateur :</p>
<ul>
<li><a href="https://support.google.com/chrome/answer/95647?hl=fr" target="_blank" rel="noopener">Google Chrome ↗</a></li>
<li><a href="https://support.mozilla.org/fr/kb/protection-renforcee-contre-suivi-firefox-ordinateur" target="_blank" rel="noopener">Mozilla Firefox ↗</a></li>
<li><a href="https://support.apple.com/fr-fr/guide/safari/sfri11471/mac" target="_blank" rel="noopener">Safari ↗</a></li>
<li><a href="https://support.microsoft.com/fr-fr/microsoft-edge/supprimer-les-cookies-dans-microsoft-edge-63947406-40ac-c3b8-57b9-2a946a29ae09" target="_blank" rel="noopener">Microsoft Edge ↗</a></li>
</ul>
<p class="small">Bloquer tous les cookies n'empêche pas de consulter {SITE}, puisqu'il n'en utilise aucun.</p>
</section>

<section class="box"><h2>Si cela change</h2>
<p>Si un outil déposant des cookies (publicité, mesure d'audience avec cookies…) était ajouté au site, cette page serait mise à jour et un véritable bandeau de consentement serait mis en place <strong>avant</strong> tout dépôt de cookie, avec un refus aussi simple que l'acceptation.</p>
</section>
''')


CSS = r'''
@font-face{font-family:"Big Shoulders";src:url(fonts/big-shoulders-display.woff2) format("woff2");font-weight:100 900;font-display:swap}
:root{--bg:#fbf8f4;--card:#fff;--ink:#2b2623;--muted:#675e57;--accent:#b0304f;--accent-d:#8f2540;--line:#e8e0d7;--line-d:#cfc3b8;--ok:#127a4a;--warn:#8a5200;--brand:#a8274a;--display:"Big Shoulders","Arial Narrow",Impact,sans-serif}
*{box-sizing:border-box}
body{margin:0;font-family:system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;color:var(--ink);background:var(--bg);line-height:1.55;font-variant-numeric:tabular-nums}
.skip{position:absolute;left:-9999px;top:8px;z-index:100;background:#fff;color:#7a1630;padding:8px 16px;border-radius:6px;font-weight:600}
.skip:focus{left:8px;outline:3px solid #7a1630}
a:focus-visible,button:focus-visible,input:focus-visible,select:focus-visible{outline:3px solid #7a1630;outline-offset:2px}
.wrap{max-width:1120px;margin:0 auto;padding:0 20px}
a{color:var(--accent)}
.i{width:16px;height:16px;flex:none;fill:none;stroke:currentColor;stroke-width:1.5;stroke-linecap:round;stroke-linejoin:round;vertical-align:-3px;margin-right:8px;color:var(--muted)}
.btn .i{color:inherit;margin-right:8px}
/* en-tête */
.top{background:var(--bg);border-bottom:1px solid var(--line)}
.top .wrap{display:flex;justify-content:space-between;align-items:center;height:60px}
.brand{font-family:var(--display);font-weight:800;font-size:1.75rem;line-height:1;text-transform:uppercase;letter-spacing:.01em;color:var(--brand);text-decoration:none}
.brand span{color:var(--ink)}
.top nav{display:flex;gap:20px}
.top nav a{color:var(--muted);text-decoration:none;font-size:.95rem}
/* alerte e-mail */
.nl{margin:48px 0 0;padding:20px;border:2px solid var(--ink);border-radius:6px;background:#fff}
.nl h2{margin:0 0 4px;font-family:var(--display);font-weight:800;font-size:1.6rem;line-height:1.05;text-transform:uppercase;letter-spacing:.01em}
.nl form{display:flex;flex-wrap:wrap;gap:12px;align-items:flex-end;margin-top:12px}
.nl-l{display:flex;flex-direction:column;gap:4px;font-size:.88rem;color:var(--muted);flex:1 1 220px}
.nl-l input,.nl-l select{height:46px;padding:0 12px;border:1px solid var(--line-d);border-radius:6px;font:inherit;font-size:1rem;color:var(--ink);background:#fff}
.nl-ok{flex:1 1 100%;font-size:.86rem;color:var(--muted);display:flex;gap:8px;align-items:flex-start}
.nl-ok input{margin-top:3px;width:18px;height:18px;flex:none}
.nl .btn{border:0;cursor:pointer;font:inherit;font-weight:600;height:46px}
.nl-hp{position:absolute;left:-9999px;width:1px;height:1px;opacity:0}
/* guide */
.toc ol{display:flex;flex-wrap:wrap;gap:4px 22px;margin:24px 0 0;padding:12px 0;list-style:none;border-top:1px solid var(--line);border-bottom:1px solid var(--line);counter-reset:t}
.toc li{counter-increment:t}
.toc li::before{content:counter(t) ". ";color:var(--accent);font-family:var(--display);font-weight:800}
.toc a{color:var(--ink);text-decoration:none}
.toc a:hover{color:var(--accent)}
.guide .box p,.guide .facts{max-width:760px}
.guide .box{scroll-margin-top:16px}
.temoin{margin:24px 0 0;padding:4px 0 4px 20px;border-left:4px solid var(--accent);font-size:1.1rem;max-width:760px}
.temoin p{margin:0 0 8px}
.temoin footer{font-size:.9rem;color:var(--muted)}
.top nav a:hover{color:var(--accent)}
/* bandeau */
.hero{position:relative;overflow:hidden;color:#fff;padding:56px 0 160px;background:url(fond-hero.svg?v=@@FOND@@) center bottom/auto 170px no-repeat,linear-gradient(120deg,#a8274a 0%,#b82d4f 62%,#d9503f 88%,#f58a4e 100%)}
.hero .wrap{position:relative;z-index:1}
.hero h1{margin:0 0 18px;font-family:var(--display);font-weight:800;text-transform:uppercase;font-size:clamp(2.7rem,7.2vw,5.2rem);line-height:.9;letter-spacing:.005em;max-width:860px}
.hero p{margin:0;color:#fff;font-size:1.08rem;max-width:580px}
/* filtres */
.filters{display:flex;gap:8px;flex-wrap:wrap;margin-top:-26px;position:relative}
.filters input,.filters select{height:48px;padding:0 14px;border:1px solid var(--line-d);border-radius:6px;font-size:1rem;background:#fff;color:var(--ink);max-width:100%;font-family:inherit}
.filters input{flex:1;min-width:240px}
.quick{margin-top:20px}
.months{display:flex;overflow-x:auto;border:1px solid var(--line);border-radius:6px;background:#fff}
.mt{flex:1 0 58px;display:flex;flex-direction:column;align-items:center;padding:10px 4px 8px;border:0;border-left:1px solid var(--line);background:none;color:var(--ink);font:inherit;cursor:pointer;transition:background-color .15s ease}
.mt:first-child{border-left:0}
.mt b{order:1;font-family:var(--display);font-size:1.6rem;font-weight:700;line-height:1;color:var(--ink)}
.mt span{order:2;font-size:.78rem;color:var(--muted);text-transform:capitalize;margin-top:2px}
.mt:hover:not(:disabled){background:#f6f1eb}
.mt[aria-pressed=true]{background:var(--accent)}
.mt[aria-pressed=true] b,.mt[aria-pressed=true] span{color:#fff}
.mt:disabled{opacity:.4;cursor:default}
.gchips{display:flex;flex-wrap:wrap;gap:0 20px;margin-top:10px}
.gc{background:none;border:0;border-bottom:2px solid transparent;padding:8px 0 6px;color:var(--ink);font:inherit;font-size:.95rem;cursor:pointer}
.gc:hover{border-bottom-color:var(--line-d)}
.gc b{color:var(--muted);font-weight:400;font-size:.82em;margin-left:3px}
.gc[aria-pressed=true]{color:var(--accent);border-bottom-color:var(--accent)}
.gc[aria-pressed=true] b{color:var(--accent)}
/* liste façon programme */
.count{margin:40px 0 0;padding-bottom:10px;border-bottom:2px solid var(--ink);font-family:var(--display);font-weight:800;font-size:1.5rem;line-height:1;text-transform:uppercase;letter-spacing:.01em}
.grid{display:block}
.card{position:relative;display:grid;grid-template-columns:104px minmax(0,1fr) minmax(170px,250px);gap:24px;align-items:center;padding:20px 12px;border-bottom:1px solid var(--line);transition:background-color .15s ease}
.card:hover{background:#fff}
.card[hidden]{display:none}
.when{display:flex;flex-direction:column;line-height:1}
.when b{font-family:var(--display);font-weight:800;font-size:2.3rem;color:var(--accent);white-space:nowrap}
.when span{margin-top:4px;font-size:.8rem;color:var(--muted)}
.when.tbc b{color:#82776e;font-weight:700}
.card h3{margin:0;font-family:var(--display);font-weight:800;font-size:1.85rem;line-height:1;text-transform:uppercase;letter-spacing:.01em}
.card h3 a{color:var(--ink);text-decoration:none}
.card h3 a::after{content:"";position:absolute;inset:0}
.card:hover h3 a{color:var(--accent)}
.card .meta{margin:6px 0 0;font-size:.95rem;color:var(--ink)}
.reg{color:var(--muted)}
.styles{margin:2px 0 0;font-size:.88rem;color:var(--muted)}
.aside{display:flex;flex-direction:column;align-items:flex-end;text-align:right;gap:2px;font-size:.9rem}
.aside .price{font-weight:600;line-height:1.35}
.vis{color:var(--muted);font-size:.84rem}
.free{color:var(--ok);font-weight:600;font-size:.84rem}
.cd:not(:empty){color:var(--accent);font-weight:600;font-size:.84rem}
.meta{margin:0;color:var(--muted);font-size:.94rem}
.price{margin:0}
.tags{margin:4px 0}
.tag{display:inline;font-size:.92rem;color:var(--ink)}
.tag+.tag::before{content:" · ";color:var(--muted)}
.btn{display:inline-block;background:var(--accent);color:#fff!important;text-decoration:none;padding:11px 18px;border-radius:6px;font-weight:600;text-align:center;transition:background-color .15s ease}
.btn:hover{background:var(--accent-d)}
.btn.ghost{background:transparent;color:var(--accent)!important;border:1px solid var(--accent);cursor:pointer;font:inherit;font-weight:600}
.btn.ghost:hover{background:#f6eeee}
.linkbtn{background:none;border:0;color:var(--accent);font:inherit;cursor:pointer;text-decoration:underline}
.badge{font-size:.76rem;padding:1px 6px;border-radius:4px;font-weight:500;margin-left:4px;white-space:nowrap}
.badge.ok{background:#e6f2ec;color:var(--ok)}
.badge.warn{background:#f8eddc;color:var(--warn)}
.empty{color:var(--muted);text-align:center;padding:40px}
/* titres de section */
.note{margin:64px auto 0}
.note h2,.box h2{margin:0 0 16px;font-family:var(--display);font-weight:800;font-size:1.7rem;line-height:1;text-transform:uppercase;letter-spacing:.01em}
.note h2{padding-top:14px;border-top:2px solid var(--ink)}
.note p{max-width:760px}
.explore h3{margin:20px 0 4px;font-size:.92rem;font-weight:600;color:var(--muted)}
.chips-nav{list-style:none;padding:0;margin:0 0 16px;display:flex;flex-wrap:wrap;gap:0 22px}
.chips-nav a,.chips-nav .cur{display:inline-block;padding:7px 0 5px;color:var(--ink);text-decoration:none;font-size:.95rem;border-bottom:1px solid var(--line-d)}
.chips-nav a:hover{color:var(--accent);border-bottom-color:var(--accent)}
.chips-nav .cur{color:var(--accent);border-bottom:2px solid var(--accent)}
.chips-nav b{font-weight:400;color:var(--muted);font-size:.85em;margin-left:3px}
/* fiches */
.fiche{padding-top:28px;padding-bottom:32px}
.crumb{margin:0 0 12px;font-size:.92rem;color:var(--muted)}
.fiche h1{margin:0 0 18px;font-family:var(--display);font-weight:800;text-transform:uppercase;font-size:clamp(2.7rem,7.5vw,5rem);line-height:.9;letter-spacing:.005em;color:var(--ink);max-width:900px}
.lead{color:#4a423c;font-size:1.1rem;max-width:720px;margin:0 0 8px}
.tiles{list-style:none;display:flex;flex-wrap:wrap;padding:0;margin:32px 0 10px;border-top:2px solid var(--ink);border-bottom:1px solid var(--line)}
.tiles li{flex:1 1 150px;padding:14px 18px 14px 0;display:flex;flex-direction:column;gap:2px}
.tiles li+li{padding-left:18px;border-left:1px solid var(--line)}
.tiles small{color:var(--muted);font-size:.82rem}
.tiles b,.cd.big:not(:empty){font-family:var(--display);font-size:1.45rem;font-weight:700;line-height:1.05;color:var(--ink)}
.actions{display:flex;flex-wrap:wrap;gap:10px;align-items:center;margin:16px 0 0}
.two{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:0 48px;margin:0}
.box{margin:48px 0 0;padding:14px 0 0;border-top:2px solid var(--ink)}
.facts{list-style:none;padding:0;margin:0 0 12px}
.facts li{padding:9px 0;border-bottom:1px solid var(--line)}
.small{font-size:.88rem;color:var(--muted)}
.prices{width:100%;border-collapse:collapse}
.prices td{padding:9px 0;border-bottom:1px solid var(--line);vertical-align:top}
.prices td:last-child{text-align:right;font-weight:600;padding-left:12px}
.prices td[colspan]{text-align:left;font-weight:400;color:var(--muted)}
.lineup{margin:4px 0 14px;font-family:var(--display);font-weight:800;font-size:clamp(1.5rem,3.4vw,2.1rem);line-height:1.15;text-transform:uppercase;letter-spacing:.01em;color:var(--ink)}
.act+.act::before{content:"·";margin:0 .35em;color:var(--accent);font-weight:400}
.map{width:100%;height:340px;border:0;border-radius:6px;background:#ebe6df;display:block}
.map-wrap{width:100%}
.map-ph{background:#fff;border:1px dashed var(--line-d);border-radius:6px;padding:28px 20px;text-align:center}
.map-ph-title{margin:0 0 8px;font-weight:600;font-size:1rem}
.map-ph .small{max-width:560px;margin:0 auto 16px}
.map-ph .btn{margin:0 auto 16px;display:inline-block;cursor:pointer;border:0;font-size:1rem;font-family:inherit}
.map-ph .small:last-child{margin-bottom:0}
.src a{word-break:break-word}
.rel{list-style:none;padding:0;margin:0;display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));gap:0 32px}
.rel li{padding:12px 0;border-bottom:1px solid var(--line)}
.rel a{font-family:var(--display);font-weight:800;font-size:1.4rem;line-height:1.05;text-transform:uppercase;text-decoration:none;color:var(--ink)}
.rel a:hover{color:var(--accent)}
.rel .small{display:block;margin-top:2px}
.see{margin-top:16px}
/* pages de listes */
.glist{list-style:none;padding:0;margin:32px 0 0;border-top:2px solid var(--ink)}
.gl{padding:16px 0;border-bottom:1px solid var(--line);display:grid;gap:3px}
.gl-name{font-family:var(--display);font-weight:800;font-size:1.7rem;line-height:1;text-transform:uppercase;color:var(--ink);text-decoration:none}
.gl-name:hover{color:var(--accent)}
.gl-meta{font-size:.92rem;color:var(--muted)}
.gl .tags{margin:0}
.gl .tag{font-size:.88rem;color:var(--muted)}
/* pages légales */
.legal{padding-top:28px;padding-bottom:12px;max-width:820px}
.legal h1{margin:0 0 8px;font-family:var(--display);font-weight:800;text-transform:uppercase;font-size:clamp(2.2rem,6vw,3.6rem);line-height:.95}
.legal .box p:last-child{margin-bottom:0}
.legal .facts .i{color:var(--ok)}
.legal code{background:#f1ece5;padding:1px 6px;border-radius:4px;font-size:.9em}
.legal .upd{margin:20px 0 0;text-align:center}
/* pied de page */
footer{background:var(--bg);color:var(--muted);padding:28px 0;margin-top:64px;font-size:.88rem;border-top:2px solid var(--ink)}
footer p{max-width:760px}
.foot-nav{margin:16px 0 8px;display:flex;flex-wrap:wrap;gap:8px 20px}
.foot-nav a{color:var(--accent);text-decoration:none}
.foot-nav a:hover{text-decoration:underline}
.foot-copy{margin:0;font-size:.85rem}
@media (prefers-reduced-motion:reduce){.card,.btn,.mt{transition:none}}
@media (max-width:640px){
.hero{padding:40px 0 108px;background:url(fond-hero.svg?v=@@FOND@@) center bottom/auto 110px no-repeat,linear-gradient(160deg,#a8274a 0%,#b82d4f 72%,#e0603f 100%)}
.filters input{flex:1 1 100%;min-width:0}
.filters select{flex:1 1 calc(50% - 4px);min-width:0;height:44px;padding:0 10px;font-size:.92rem}
.card{grid-template-columns:68px minmax(0,1fr);gap:4px 14px;align-items:start;padding:16px 0}
.when b{font-size:1.65rem}
.card h3{font-size:1.5rem}
.aside{grid-column:2;flex-direction:row;flex-wrap:wrap;align-items:baseline;text-align:left;gap:2px 12px;margin-top:6px}
.tiles li{flex-basis:45%}
.map-ph{padding:20px 16px}
}
'''

JS = r'''
// Cartes : rien n'est demandé à Google tant que le visiteur n'a pas cliqué.
(function () {
  var wrap = document.querySelector('.map-wrap');
  if (!wrap) return;
  var btn = wrap.querySelector('.map-btn');
  if (!btn) return;
  btn.addEventListener('click', function () {
    var src = wrap.getAttribute('data-map-src');
    if (!src) return;
    var frame = document.createElement('iframe');
    frame.className = 'map';
    frame.setAttribute('title', wrap.getAttribute('data-map-title') || 'Carte');
    frame.setAttribute('loading', 'lazy');
    frame.setAttribute('referrerpolicy', 'no-referrer');
    frame.setAttribute('src', src);
    wrap.innerHTML = '';
    wrap.appendChild(frame);
  });
})();

(function () {
  var q = document.getElementById('q');
  if (!q) return;
  var mois = document.getElementById('mois');
  var region = document.getElementById('region');
  var genre = document.getElementById('genre');
  var budget = document.getElementById('budget');
  var tri = document.getElementById('tri');
  var grid = document.getElementById('grid');
  var mts = Array.prototype.slice.call(document.querySelectorAll('.mt'));
  var gcs = Array.prototype.slice.call(document.querySelectorAll('.gc'));
  var cards = Array.prototype.slice.call(document.querySelectorAll('.card'));
  var count = document.getElementById('count');
  var empty = document.getElementById('empty');
  var reset = document.getElementById('reset');
  function norm(s) { return (s || '').normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase(); }
  function apply() {
    var text = norm(q.value).trim(), m = mois.value, r = region.value, g = genre.value, b = budget.value, n = 0;
    cards.forEach(function (c) {
      var ok = (!text || c.dataset.name.indexOf(text) !== -1) &&
               (!m || c.dataset.mois.split(' ').indexOf(m) !== -1) &&
               (!r || c.dataset.region === r) &&
               (!g || c.dataset.genres.split('|').indexOf(g) !== -1) &&
               (!b || (b === 'free' ? c.dataset.free === '1' : (c.dataset.price !== '' && parseFloat(c.dataset.price) <= parseFloat(b))));
      c.hidden = !ok;
      if (ok) n++;
    });
    mts.forEach(function (x) { x.setAttribute('aria-pressed', x.dataset.m === m ? 'true' : 'false'); });
    gcs.forEach(function (x) { x.setAttribute('aria-pressed', x.dataset.g === g ? 'true' : 'false'); });
    count.textContent = n + (n > 1 ? ' festivals' : ' festival');
    empty.hidden = n !== 0;
  }
  function sortCards() {
    var k = tri.value;
    var list = cards.slice().sort(function (a, b) {
      if (k === 'date') return a.dataset.d - b.dataset.d;
      if (k === 'az') return a.querySelector('h3').textContent.localeCompare(b.querySelector('h3').textContent, 'fr');
      if (k === 'prix') {
        var pa = a.dataset.price === '' ? 1e9 : parseFloat(a.dataset.price), pb = b.dataset.price === '' ? 1e9 : parseFloat(b.dataset.price);
        if (pa !== pb) return pa - pb;
      }
      return a.dataset.i - b.dataset.i;
    });
    list.forEach(function (c) { grid.appendChild(c); });
  }
  tri.addEventListener('change', sortCards);
  mts.forEach(function (x) { x.addEventListener('click', function () { mois.value = mois.value === x.dataset.m ? '' : x.dataset.m; apply(); }); });
  gcs.forEach(function (x) { x.addEventListener('click', function () { genre.value = genre.value === x.dataset.g ? '' : x.dataset.g; apply(); }); });
  [q, mois, region, genre, budget].forEach(function (el) {
    el.addEventListener('input', apply);
    el.addEventListener('change', apply);
  });
  if (reset) reset.addEventListener('click', function () {
    q.value = ''; mois.value = ''; region.value = ''; genre.value = ''; budget.value = ''; apply();
  });
  apply();
})();

// Compte à rebours (calculé dans le navigateur, aucune donnée envoyée).
(function () {
  var day = 86400000, now = new Date(), today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  function d(s) { var p = s.split('-'); return new Date(+p[0], +p[1] - 1, +p[2]); }
  Array.prototype.forEach.call(document.querySelectorAll('.cd[data-start]'), function (el) {
    var a = d(el.dataset.start), b = d(el.dataset.end), n = Math.round((a - today) / day);
    el.textContent = today > b ? '' : today >= a ? 'En cours' : n === 1 ? 'Demain' : 'Dans ' + n + ' jours';
  });
})();

// Bouton Partager : partage natif si disponible, sinon copie du lien.
(function () {
  var b = document.querySelector('.share-btn');
  if (!b) return;
  b.addEventListener('click', function () {
    var msg = document.querySelector('.share-msg'), url = location.href.split('#')[0];
    if (navigator.share) { navigator.share({ title: b.dataset.title, url: url }).catch(function () {}); return; }
    if (navigator.clipboard) navigator.clipboard.writeText(url).then(function () { msg.textContent = 'Lien copié.'; }, function () { msg.textContent = url; });
    else msg.textContent = url;
  });
})();
'''

def scene_svg():
    """Décor du bandeau : champ de festival au coucher du soleil (dessin original, déterministe).
    Collines en trois plans, chapiteaux à fanions, grande roue, guirlandes de fanions et d'ampoules."""
    import math, random
    r = random.Random(5)
    W, H = 2400, 190
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" preserveAspectRatio="xMidYMax slice">']

    def hill(base, a1, w1, p1, a2, w2, p2):
        return lambda x: base + a1 * math.sin(x / w1 + p1) + a2 * math.sin(x / w2 + p2)

    def fill_hill(f, color, op):
        pts = "L".join(f"{x} {f(x):.1f}" for x in range(0, W + 1, 24))
        return f'<path d="M0 {H}L{pts}L{W} {H}Z" fill="{color}" opacity="{op}"/>'

    far = hill(112, 13, 150, 0.6, 7, 61, 2.0)
    mid = hill(138, 11, 190, 2.2, 6, 73, 0.7)
    near = hill(168, 8, 230, 4.0, 4, 90, 1.3)

    out.append(fill_hill(far, "#d4506a", .30))
    # guirlandes : poteaux et fanions
    cols = ["#fcc65a", "#ffffff", "#f58a4e", "#ffd9a8", "#ffa3b1"]
    poles = [60, 520, 940, 1380, 1800, 2250]
    tops = [58, 50, 62, 52, 60, 54]
    g = ['<g opacity=".8">']
    for (x, y) in zip(poles, tops):
        g.append(f'<path d="M{x} {y}V{far(x) + 10:.0f}" stroke="#a8325a" stroke-width="3" opacity=".6"/>')
    for i in range(len(poles) - 1):
        x0, y0, x1, y1 = poles[i], tops[i], poles[i + 1], tops[i + 1]
        cx, cy = (x0 + x1) / 2, max(y0, y1) + 44
        g.append(f'<path d="M{x0} {y0}Q{cx:.0f} {cy} {x1} {y1}" stroke="#fff" stroke-width="1.6" fill="none" opacity=".6"/>')
        n = int((x1 - x0) / 24)
        for k in range(1, n):
            u = k / n
            x = (1 - u) ** 2 * x0 + 2 * (1 - u) * u * cx + u ** 2 * x1
            y = (1 - u) ** 2 * y0 + 2 * (1 - u) * u * cy + u ** 2 * y1
            c = cols[(i * 7 + k) % len(cols)]
            g.append(f'<path d="M{x - 6.5:.1f} {y:.1f}L{x + 6.5:.1f} {y:.1f}L{x:.1f} {y + 15:.1f}Z" fill="{c}"/>')
            if k % 3 == 0:
                g.append(f'<circle cx="{x + 12:.1f}" cy="{y + 3:.1f}" r="2.4" fill="#ffe9a8" opacity=".95"/>')
    g.append('</g>')
    out.append("".join(g))

    out.append(fill_hill(mid, "#b03a5c", .45))
    # chapiteaux sur la colline du milieu
    tents = ['<g fill="#8f2f50" opacity=".72">']
    x = 70
    while x < W - 60:
        w = r.randint(46, 84)
        h = r.randint(30, 52)
        if abs(x - 1610) < 110:  # laisse la place à la grande roue
            x += 130
            continue
        yb = mid(x) + 5
        wall = h * .42
        tents.append(f'<path d="M{x - w / 2:.0f} {yb:.0f}V{yb - wall:.0f}L{x} {yb - h:.0f}L{x + w / 2:.0f} {yb - wall:.0f}V{yb:.0f}Z"/>')
        tents.append(f'<path d="M{x} {yb - h:.0f}V{yb - h - 11:.0f}M{x} {yb - h - 11:.0f}l9 3.5l-9 3.5Z" stroke="#8f2f50" stroke-width="1.6"/>')
        x += w + r.randint(60, 190)
    tents.append('</g>')
    out.append("".join(tents))

    # grande roue
    cx, cy, rad = 1610, 88, 50
    wheel = [f'<g stroke="#8f2f50" fill="none" opacity=".6" stroke-width="2.4">',
             f'<circle cx="{cx}" cy="{cy}" r="{rad}"/><circle cx="{cx}" cy="{cy}" r="{rad * .55:.0f}" stroke-width="1.4"/>']
    for k in range(12):
        a = math.radians(k * 30)
        px, py = cx + rad * math.cos(a), cy + rad * math.sin(a)
        wheel.append(f'<path d="M{cx} {cy}L{px:.1f} {py:.1f}" stroke-width="1.6"/>')
    wheel.append(f'<path d="M{cx} {cy}L{cx - 30} {mid(cx - 30) + 6:.0f}M{cx} {cy}L{cx + 30} {mid(cx + 30) + 6:.0f}" stroke-width="3.4"/>')
    wheel.append('</g><g fill="#8f2f50" opacity=".62">')
    for k in range(12):
        a = math.radians(k * 30 + 15)
        wheel.append(f'<circle cx="{cx + rad * math.cos(a):.1f}" cy="{cy + rad * math.sin(a) + 3:.1f}" r="4.4"/>')
    wheel.append('</g>')
    out.append("".join(wheel))

    out.append(fill_hill(near, "#7a2744", .6))
    out.append('</svg>')
    return "".join(out)


def motif_svg():
    """Motif discret (étoiles, ronds, notes) répété en fond de page."""
    star = lambda cx, cy, s, c, o: (f'<path d="M{cx} {cy - s}l{s * .28:.1f} {s * .72:.1f} {s * .72:.1f} {s * .28:.1f}-{s * .72:.1f} {s * .28:.1f}-{s * .28:.1f} {s * .72:.1f}-{s * .28:.1f}-{s * .72:.1f}-{s * .72:.1f}-{s * .28:.1f} {s * .72:.1f}-{s * .28:.1f}z" fill="{c}" opacity="{o}"/>')
    note = lambda x, y, c, o: (f'<g fill="{c}" stroke="{c}" opacity="{o}"><ellipse cx="{x}" cy="{y}" rx="6" ry="4.5" stroke="none" transform="rotate(-20 {x} {y})"/><path d="M{x + 5} {y - 1}V{y - 22}l9 4" fill="none" stroke-width="2.2" stroke-linecap="round"/></g>')
    return ('<svg xmlns="http://www.w3.org/2000/svg" width="260" height="260" viewBox="0 0 260 260">'
            + star(40, 44, 14, "#e11d48", .07) + star(190, 120, 10, "#f97316", .09) + star(100, 210, 12, "#fbbf24", .16)
            + '<circle cx="150" cy="40" r="6" fill="#f97316" opacity=".08"/><circle cx="30" cy="150" r="4" fill="#e11d48" opacity=".08"/><circle cx="225" cy="225" r="7" fill="#fbbf24" opacity=".14"/>'
            + note(210, 50, "#e11d48", .07) + note(60, 120, "#f97316", .08) + note(170, 200, "#e11d48", .06)
            + '</svg>')


# Empreintes ajoutées aux liens : le navigateur recharge le fichier dès qu'il change.
FOND_V = hashlib.md5((scene_svg() + motif_svg()).encode("utf-8")).hexdigest()[:8]
CSS = CSS.replace("@@FOND@@", FOND_V)
CSS_V = hashlib.md5(CSS.strip().encode("utf-8")).hexdigest()[:8]
JS_V = hashlib.md5(JS.strip().encode("utf-8")).hexdigest()[:8]


if __name__ == "__main__":
    data = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    fests = build(data)
    (OUT / "style.css").write_text(CSS.strip() + "\n", encoding="utf-8")
    (OUT / "script.js").write_text(JS.strip() + "\n", encoding="utf-8")
    print(f"{len(fests)} fiches générées dans {OUT}")
