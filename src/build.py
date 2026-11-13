#!/usr/bin/env python3
"""Génère le site FestiGuide à partir de festivals.json."""
import hashlib, html, json, shutil, sys, unicodedata
from pathlib import Path

esc = lambda s: html.escape(str(s), quote=True)
SITE = "FestiGuide"
UPDATED = "13 novembre 2026"
BASE_URL = "https://lanfus.github.io/festiguide"
EDITEUR = "Florent H."
CONTACT = "contact.festiguide@gmail.com"
LEGAL_PAGES = ["mentions-legales.html", "confidentialite.html", "cookies.html"]
OUT = Path(sys.argv[2] if len(sys.argv) > 2 else ".")

MOIS_ORDRE = ["janvier", "février", "mars", "avril", "mai", "juin", "juillet",
              "août", "septembre", "octobre", "novembre", "décembre"]


def norm(s):
    s = unicodedata.normalize("NFD", str(s))
    return "".join(c for c in s if unicodedata.category(c) != "Mn").lower()


def tri_key(f):
    if f.get("iso"):
        return (0, f["iso"][0])
    mois = f.get("mois") or []
    i = MOIS_ORDRE.index(mois[0]) if mois and mois[0] in MOIS_ORDRE else 99
    return (1, f"{i:02d}")


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


FAVICON = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">
<defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#9f1239"/><stop offset=".55" stop-color="#e11d48"/><stop offset="1" stop-color="#f97316"/></linearGradient></defs>
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
<link rel="stylesheet" href="style.css?v={CSS_V}">
{extra}</head>
<body>
<header class="top"><div class="wrap"><a class="brand" href="index.html">🎪 {SITE}</a><nav><a href="index.html">Tous les festivals</a></nav></div></header>
'''


def foot():
    return f'''<footer><div class="wrap">
<p>Informations rassemblées le {UPDATED} depuis des sources publiques, citées en bas de chaque fiche. Dates, prix et programmations changent souvent : vérifiez toujours sur le site officiel avant d'acheter un billet. {SITE} n'est affilié à aucun festival et ne vend aucun billet.</p>
<nav class="foot-nav" aria-label="Informations légales">
<a href="index.html">Accueil</a><a href="mentions-legales.html">Mentions légales</a><a href="confidentialite.html">Confidentialité</a><a href="cookies.html">Cookies</a>
</nav>
<p class="foot-copy">© 2026 {SITE} — Éditeur : {EDITEUR}</p>
</div></footer>
'''


def build(fests):
    OUT.mkdir(parents=True, exist_ok=True)
    fests = sorted(fests, key=tri_key)

    mois_dispo = [m for m in MOIS_ORDRE if any(m in (f.get("mois") or []) for f in fests)]
    regions = sorted({f.get("region") for f in fests if f.get("region")}, key=norm)
    genres = sorted({g for f in fests for g in (f.get("genres") or [])}, key=norm)

    # ---------- page d'accueil ----------
    cards = ""
    for f in fests:
        tags = "".join(f'<span class="tag">{esc(g)}</span>' for g in (f.get("genres") or [])[:4])
        searchable = " ".join(filter(None, [f["name"], f.get("city"), f.get("region"), f.get("venue")]))
        badge = "ok" if f.get("status") == "Dates annoncées" else "warn"
        prix = f.get("price_label") or "Tarifs non publiés"
        cards += f'''<article class="card" data-name="{esc(norm(searchable))}" data-mois="{esc(" ".join(f.get("mois") or []))}" data-region="{esc(f.get("region") or "")}" data-genres="{esc("|".join(f.get("genres") or []))}">
  <div class="card-top"><span class="pill">{esc(" / ".join(m.capitalize() for m in (f.get("mois") or ["Date à venir"])))}</span><span class="country">{esc(f.get("region") or f.get("country"))}</span></div>
  <h3><a href="{f["slug"]}.html">{esc(f["name"])}</a></h3>
  <p class="meta">📍 {esc(f.get("city") or "")}</p>
  <p class="meta">📅 {esc(f.get("dates") or "À confirmer")} <span class="badge {badge}">{esc(f.get("status") or "")}</span></p>
  <p class="tags">{tags}</p>
  <p class="price">🎫 {esc(prix)}</p>
  <a class="btn" href="{f["slug"]}.html">Voir la fiche</a>
</article>
'''
    opt = lambda vals: "".join(f"<option>{esc(v)}</option>" for v in vals)
    nb_annonces = sum(1 for f in fests if f.get("status") == "Dates annoncées")
    idx = head(
        f"{len(fests)} grands festivals en France : dates, prix | {SITE}",
        f"Les {len(fests)} plus gros festivals de France et de Belgique : dates, lieu, prix, artistes, plan et site officiel. Musique, cinéma, théâtre, BD.",
        f"{BASE_URL}/index.html")
    idx += f'''<main>
<section class="hero"><div class="wrap">
<h1>Les grands festivals, au même endroit</h1>
<p>Dates, lieux, prix, artistes et plans : {len(fests)} festivals de France et de Belgique, dont {nb_annonces} aux dates déjà confirmées.</p>
</div></section>
<section class="wrap filters" aria-label="Filtres">
<input id="q" type="search" placeholder="Festival, ville ou région…" aria-label="Rechercher">
<select id="mois" aria-label="Mois"><option value="">Tous les mois</option>{opt(mois_dispo)}</select>
<select id="region" aria-label="Région"><option value="">Toutes les régions</option>{opt(regions)}</select>
<select id="genre" aria-label="Genre"><option value="">Tous les genres</option>{opt(genres)}</select>
</section>
<section class="wrap"><p id="count" class="count"></p>
<div class="grid" id="grid">
{cards}</div>
<p id="empty" class="empty" hidden>Aucun festival ne correspond à ta recherche. <button type="button" id="reset" class="linkbtn">Tout afficher</button></p></section>
<section class="wrap note"><h2>Comment lire ces infos</h2>
<p>Les festivals sont classés par date de la <strong>prochaine édition</strong>. Quand les dates ne sont pas encore officielles, la fiche affiche le mois habituel et la mention « Dates à confirmer ».</p>
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
        chips = "".join(f'<span class="chip">{esc(a)}</span>' for a in (f.get("lineup") or [])) \
            or '<span class="small">Programmation pas encore annoncée.</span>'
        acc = "".join(f"<li>{esc(a)}</li>" for a in (f.get("access") or [])) or "<li>Voir le site officiel.</li>"
        tips = "".join(f"<li>{esc(a)}</li>" for a in (f.get("tips") or [])) or "<li>Rien de particulier à signaler.</li>"
        src = "".join(f'<li><a href="{esc(u)}" target="_blank" rel="noopener">{esc(t)}</a></li>' for t, u in (f.get("sources") or []))
        gen = "".join(f'<span class="tag">{esc(g)}</span>' for g in (f.get("genres") or []))
        q = html.escape((f.get("maps_q") or f.get("city") or "").replace(" ", "+"), quote=True)
        badge = "ok" if f.get("status") == "Dates annoncées" else "warn"
        official = f.get("official") or ""
        lien_off = f'<a class="btn" href="{esc(official)}" target="_blank" rel="noopener">Site officiel et billetterie ↗</a>' if official else '<p class="small">Site officiel non renseigné.</p>'
        p += f'''<main class="wrap fiche">
<nav class="crumb" aria-label="Fil d'Ariane"><a href="index.html">Accueil</a> › <span>{esc(f["name"])}</span></nav>
<h1>{esc(f["name"])}</h1>
<p class="lead">{esc(f.get("about") or "")}</p>
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
<p>{chips}</p>
<p class="small">{esc(f.get("lineup_note") or "")}</p>
</section>
<section class="box"><h2>Plan et localisation</h2>
<div class="map-wrap" data-map-src="https://www.google.com/maps?q={q}&amp;output=embed" data-map-title="Carte : {esc(f["name"])}">
  <div class="map-ph">
    <p class="map-ph-title">🗺️ Carte non chargée</p>
    <p class="small">Cette carte est fournie par Google Maps. En l'affichant, vous autorisez Google à recevoir votre adresse IP et à déposer des cookies sur votre appareil. Rien n'est envoyé à Google tant que vous ne cliquez pas.</p>
    <button type="button" class="btn map-btn">Afficher la carte</button>
    <p class="small">Vous pouvez aussi <a href="https://www.google.com/maps/search/?api=1&amp;query={q}" target="_blank" rel="noopener">ouvrir le lieu dans Google Maps ↗</a> — ou lire notre <a href="cookies.html">politique de cookies</a>.</p>
  </div>
</div>
<p class="small">Le plan détaillé des scènes est publié chaque année par le festival : consultez le site officiel.</p>
</section>
<div class="two">
<section class="box"><h2>Y aller</h2><ul>{acc}</ul></section>
<section class="box"><h2>À savoir</h2><ul>{tips}</ul></section>
</div>
<section class="box"><h2>Autres festivals à découvrir</h2><ul class="rel">{voisins}</ul></section>
<section class="box"><h2>Sources</h2><ul class="src">{src}</ul><p class="small">Mis à jour le {UPDATED}.</p></section>
</main>
{foot()}<script src="script.js?v={JS_V}"></script>
</body></html>
'''
        (OUT / f'{f["slug"]}.html').write_text(p, encoding="utf-8")

    build_legal(len(fests))

    # ---------- sitemap + robots ----------
    urls = "".join(f"  <url><loc>{BASE_URL}/{s}</loc></url>\n"
                   for s in ["index.html"] + [f'{f["slug"]}.html' for f in fests] + LEGAL_PAGES)
    (OUT / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + urls + "</urlset>\n", encoding="utf-8")
    (OUT / "robots.txt").write_text(f"User-agent: *\nAllow: /\n\nSitemap: {BASE_URL}/sitemap.xml\n", encoding="utf-8")
    (OUT / "favicon.svg").write_text(FAVICON, encoding="utf-8")
    (OUT / "fond-hero.svg").write_text(crowd_svg(), encoding="utf-8")
    (OUT / "motif.svg").write_text(motif_svg(), encoding="utf-8")
    og = Path(__file__).parent / "og-image.png"  # image de partage : source dans og-image.html
    if og.exists() and og.resolve() != (OUT / "og-image.png").resolve():
        shutil.copy(og, OUT / "og-image.png")
    return fests


def legal_page(slug, title, desc, body):
    p = head(f"{title} | {SITE}", desc, f"{BASE_URL}/{slug}")
    p += f'''<main class="wrap legal">
<p class="crumb"><a href="index.html">← Retour au site</a></p>
<h1>{esc(title)}</h1>
{body}
<p class="small upd">Dernière mise à jour : {UPDATED}.</p>
</main>
{foot()}</body></html>
'''
    (OUT / slug).write_text(p, encoding="utf-8")


def build_legal(nb):
    # ---------- mentions légales ----------
    legal_page("mentions-legales.html", "Mentions légales",
               f"Mentions légales de {SITE} : éditeur, hébergeur, contact et conditions d'utilisation.", f'''
<section class="box"><h2>Éditeur du site</h2>
<ul class="facts">
<li><strong>Éditeur :</strong> {EDITEUR}, particulier</li>
<li><strong>Statut :</strong> site personnel sans activité commerciale</li>
<li><strong>Contact :</strong> <a href="mailto:{CONTACT}">{CONTACT}</a></li>
<li><strong>Directeur de la publication :</strong> {EDITEUR}</li>
</ul>
<p class="small">Conformément à la loi n° 2004-575 du 21 juin 2004 pour la confiance dans l'économie numérique (LCEN), l'éditeur non professionnel d'un site peut ne pas publier son adresse postale, à condition de l'avoir communiquée à son hébergeur. Celle-ci est tenue à la disposition des autorités judiciaires.</p>
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
<p>Le présent site est soumis au droit français. En cas de litige, et après tentative de recherche d'une solution amiable, les tribunaux français sont seuls compétents.</p>
</section>
''')

    # ---------- confidentialité ----------
    legal_page("confidentialite.html", "Politique de confidentialité",
               f"Comment {SITE} traite vos données personnelles : aucune collecte directe, pas de compte, pas de publicité, pas de revente.", f'''
<section class="box"><h2>En résumé</h2>
<ul class="facts">
<li>✅ <strong>Aucun formulaire, aucun compte, aucune newsletter</strong> sur ce site</li>
<li>✅ <strong>Aucun cookie</strong> déposé par le site lui-même</li>
<li>✅ <strong>Aucune publicité</strong>, aucun traceur publicitaire, aucun revendeur de données</li>
<li>✅ <strong>Aucune donnée vendue, louée ou transmise</strong> à des fins commerciales</li>
<li>⚠️ Deux exceptions détaillées ci-dessous : les <strong>journaux de l'hébergeur</strong> et les <strong>cartes Google Maps</strong>, qui ne se chargent qu'à votre demande</li>
</ul>
</section>

<section class="box"><h2>Qui est responsable du traitement</h2>
<p>{EDITEUR}, éditeur de {SITE}, joignable à <a href="mailto:{CONTACT}">{CONTACT}</a>. Le site est un projet personnel sans activité commerciale.</p>
</section>

<section class="box"><h2>Ce que le site collecte lui-même</h2>
<p><strong>Rien.</strong> {SITE} est un site statique : il n'y a ni base de données, ni formulaire, ni espace membre, ni outil de mesure d'audience. Vous pouvez consulter l'intégralité du site sans transmettre la moindre donnée personnelle à l'éditeur.</p>
</section>

<section class="box"><h2>Journaux de connexion de l'hébergeur</h2>
<p>Le site est hébergé par <strong>GitHub Pages</strong> (GitHub, Inc., États-Unis). Comme tout serveur web, GitHub enregistre techniquement les requêtes qu'il reçoit : adresse IP, date et heure, page demandée, navigateur utilisé.</p>
<ul class="facts">
<li><strong>Finalité :</strong> fournir le service, assurer la sécurité du serveur et prévenir les abus</li>
<li><strong>Base légale :</strong> intérêt légitime de l'hébergeur (article 6.1.f du RGPD)</li>
<li><strong>Destinataire :</strong> GitHub, Inc., en sa qualité d'hébergeur</li>
<li><strong>Transfert hors Union européenne :</strong> oui, vers les États-Unis, encadré par les clauses contractuelles types et le cadre de protection des données UE–États-Unis</li>
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
<p>Le site est déclaré auprès de la <strong>Google Search Console</strong>, un outil qui indique à l'éditeur quelles requêtes de recherche mènent au site. Cet outil ne dépose aucun cookie sur votre appareil, n'ajoute aucun script à la page et ne fournit que des statistiques agrégées et anonymes. Il ne permet pas d'identifier un visiteur.</p>
<p>Aucun outil de mesure d'audience de type Google Analytics n'est installé. Si cela devait changer, cette page serait mise à jour et un bandeau de consentement serait mis en place <strong>avant</strong> tout dépôt de cookie.</p>
</section>

<section class="box"><h2>Durée de conservation</h2>
<p>L'éditeur ne conserve aucune donnée personnelle. Les journaux de l'hébergeur sont conservés selon la politique de GitHub. Un courriel que vous envoyez à l'adresse de contact est conservé le temps nécessaire au traitement de votre demande, puis supprimé.</p>
</section>

<section class="box"><h2>Vos droits</h2>
<p>Le RGPD vous donne un droit d'accès, de rectification, d'effacement, de limitation, d'opposition et de portabilité sur vos données personnelles.</p>
<p>Pour les exercer, écrivez à <a href="mailto:{CONTACT}">{CONTACT}</a>. L'éditeur ne détenant aucune donnée vous concernant, une demande portant sur les journaux de connexion doit être adressée à GitHub, et une demande portant sur les cartes à Google.</p>
<p>Si vous estimez que vos droits ne sont pas respectés, vous pouvez saisir la <strong>CNIL</strong> : <a href="https://www.cnil.fr/fr/plaintes" target="_blank" rel="noopener">cnil.fr/fr/plaintes ↗</a>, ou 3 place de Fontenoy, TSA 80715, 75334 Paris Cedex 07.</p>
</section>

<section class="box"><h2>Mineurs</h2>
<p>Le site est accessible à tous et ne collecte aucune donnée, y compris auprès des mineurs. Les festivals cités appliquent leurs propres règles d'âge, indiquées sur leurs sites officiels.</p>
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

<section class="box"><h2>Liens vers des sites tiers</h2>
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
<p>Si un outil de mesure d'audience ou une inscription à une newsletter était ajouté au site, cette page serait mise à jour et un véritable bandeau de consentement serait mis en place <strong>avant</strong> tout dépôt de cookie, avec un refus aussi simple que l'acceptation.</p>
</section>
''')


CSS = r'''
:root{--bg:#ffffff;--card:#fff;--ink:#1c1f2e;--muted:#5b6075;--accent:#be123c;--accent2:#ff5a7a;--line:#f1e2d9;--ok:#127a4a;--warn:#a15c00;--brand:#9f1239;--pink:#e11d48;--orange:#f97316;--stripe:linear-gradient(90deg,#e11d48,#f97316 55%,#fbbf24)}
*{box-sizing:border-box}
body{margin:0;font-family:system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;color:var(--ink);background:#fff9f4;line-height:1.55;position:relative}
body::before{content:"";position:fixed;inset:0;z-index:-1;pointer-events:none;background:url(motif.svg?v=@@FOND@@),radial-gradient(60% 45% at 8% 6%,rgba(225,29,72,.09),transparent 70%),radial-gradient(55% 45% at 95% 20%,rgba(251,191,36,.16),transparent 70%),radial-gradient(60% 50% at 70% 100%,rgba(249,115,22,.10),transparent 70%)}
.wrap{max-width:1100px;margin:0 auto;padding:0 18px}
a{color:var(--accent)}
.top{background:rgba(255,255,255,.92);color:var(--ink);border-bottom:1px solid var(--line);border-top:5px solid transparent;border-image:var(--stripe) 1 0 0 0}
.top .wrap{display:flex;justify-content:space-between;align-items:center;height:56px}
.brand{color:var(--brand);text-decoration:none;font-weight:800;font-size:1.15rem;letter-spacing:-.01em}
.top nav a{color:var(--muted);text-decoration:none;font-size:.95rem}
.top nav a:hover{color:var(--accent)}
.hero{position:relative;overflow:hidden;color:#fff;padding:64px 0 150px;background:url(fond-hero.svg?v=@@FOND@@) center bottom/auto 170px no-repeat,linear-gradient(120deg,#9f1239 0%,#e11d48 45%,#f97316 80%,#fbbf24 100%)}
.hero::before{content:"";position:absolute;inset:0;pointer-events:none;background:conic-gradient(from 168deg at 22% -25%,transparent 0 5deg,rgba(255,255,255,.20) 5deg 9deg,transparent 9deg 19deg,rgba(255,255,255,.14) 19deg 22deg,transparent 22deg 360deg),conic-gradient(from 188deg at 78% -25%,transparent 0 6deg,rgba(255,255,255,.18) 6deg 10deg,transparent 10deg 21deg,rgba(255,255,255,.12) 21deg 24deg,transparent 24deg 360deg)}
.hero::after{content:"";position:absolute;inset:0;pointer-events:none;opacity:.55;background-image:radial-gradient(circle,rgba(255,255,255,.75) 0 2px,transparent 3px),radial-gradient(circle,rgba(255,224,102,.8) 0 3px,transparent 4px),radial-gradient(circle,rgba(255,255,255,.55) 0 1.5px,transparent 2.5px);background-size:150px 130px,230px 190px,90px 110px;background-position:20px 30px,90px 70px,50px 10px}
.hero .wrap{position:relative;z-index:1}
.hero h1{margin:0 0 10px;font-size:clamp(1.9rem,4.4vw,2.9rem);max-width:640px;text-shadow:0 2px 14px rgba(90,10,20,.45)}
.hero p{margin:0;color:rgba(255,255,255,.95);font-size:1.08rem;max-width:620px;text-shadow:0 1px 8px rgba(90,10,20,.4)}
.filters{display:flex;gap:10px;flex-wrap:wrap;margin-top:-22px;position:relative}
.filters input,.filters select{padding:12px 14px;border:1px solid var(--line);border-radius:10px;font-size:1rem;background:#fff;box-shadow:0 2px 8px rgba(20,20,60,.06);max-width:100%}
.filters input{flex:1;min-width:220px}
.count{color:var(--muted);margin:18px 0 8px}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(290px,1fr));gap:16px}
.card{position:relative;overflow:hidden;background:var(--card);border:1px solid var(--line);border-radius:14px;padding:22px 18px 18px;display:flex;flex-direction:column;gap:6px;box-shadow:0 2px 10px rgba(120,40,20,.07);transition:transform .18s ease,box-shadow .18s ease}
.card::before{content:"";position:absolute;inset:0 0 auto 0;height:5px;background:var(--stripe)}
.card:hover{transform:translateY(-3px);box-shadow:0 10px 24px rgba(159,18,57,.18)}
@media (prefers-reduced-motion:reduce){.card{transition:none}.card:hover{transform:none}}
.card[hidden]{display:none}
.card-top{display:flex;justify-content:space-between;gap:8px;font-size:.82rem}
.pill{background:#ffe4e9;color:var(--accent);padding:2px 10px;border-radius:99px;font-weight:600}
.country{color:var(--muted);text-align:right}
.card h3{margin:4px 0 2px;font-size:1.2rem}
.card h3 a{color:var(--ink);text-decoration:none}
.card h3 a:hover{color:var(--accent)}
.meta{margin:0;color:var(--muted);font-size:.93rem}
.tags{margin:4px 0}
.tag{display:inline-block;background:#f1f2f8;color:#3b3f55;font-size:.78rem;padding:2px 9px;border-radius:99px;margin:0 4px 4px 0}
.price{margin:2px 0 8px;font-weight:600}
.btn{display:inline-block;margin-top:auto;background:linear-gradient(100deg,#be123c,#c2410c);color:#fff!important;text-decoration:none;padding:10px 16px;border-radius:10px;font-weight:600;text-align:center}
.btn:hover{background:linear-gradient(100deg,#9f1239,#9a3412)}
.linkbtn{background:none;border:0;color:var(--accent);font:inherit;cursor:pointer;text-decoration:underline}
.badge{font-size:.72rem;padding:2px 8px;border-radius:99px;font-weight:600;margin-left:4px;white-space:nowrap}
.badge.ok{background:#e3f6ec;color:var(--ok)}
.badge.warn{background:#fff1dc;color:var(--warn)}
.empty{color:var(--muted);text-align:center;padding:30px}
.note{margin:36px auto}
.note h2{font-size:1.15rem}
.fiche{padding-top:22px;padding-bottom:30px}
.crumb{margin:0 0 6px;font-size:.92rem;color:var(--muted)}
.rel{list-style:none;padding:0;margin:0;display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));gap:10px}
.rel li{background:#fff6f0;border:1px solid var(--line);border-radius:10px;padding:10px 12px}
.rel a{font-weight:600;text-decoration:none;color:var(--brand)}
.rel a:hover{text-decoration:underline}
.rel .small{display:block;margin-top:2px}
.fiche h1{margin:0 0 8px;font-size:clamp(1.7rem,4vw,2.4rem);color:var(--brand)}
.fiche h1::after{content:"";display:block;width:84px;height:5px;border-radius:99px;margin-top:10px;background:var(--stripe)}
.lead{color:var(--muted);font-size:1.05rem;max-width:760px}
.two{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:16px;margin:16px 0}
.box{background:#fff;border:1px solid var(--line);border-radius:14px;padding:18px 20px;margin:16px 0}
.two .box{margin:0}
.box h2{margin:0 0 10px;font-size:1.1rem}
.facts{list-style:none;padding:0;margin:0 0 10px}
.facts li{padding:6px 0;border-bottom:1px solid var(--line)}
.small{font-size:.88rem;color:var(--muted)}
.prices{width:100%;border-collapse:collapse}
.prices td{padding:8px 0;border-bottom:1px solid var(--line);vertical-align:top}
.prices td:last-child{text-align:right;font-weight:600;padding-left:12px}
.prices td[colspan]{text-align:left;font-weight:400;color:var(--muted)}
.chip{display:inline-block;background:#ffeadb;color:#9a3412;padding:5px 12px;border-radius:99px;margin:0 6px 8px 0;font-size:.92rem;font-weight:500}
.map{width:100%;height:340px;border:0;border-radius:10px;background:#e8eaf2;display:block}
.map-wrap{width:100%}
.map-ph{background:#fff4ee;border:1px dashed #f3c9b8;border-radius:10px;padding:26px 20px;text-align:center}
.map-ph-title{margin:0 0 8px;font-weight:700;font-size:1rem}
.map-ph .small{max-width:560px;margin:0 auto 14px}
.map-ph .btn{margin:0 auto 14px;display:inline-block;cursor:pointer;border:0;font-size:1rem;font-family:inherit}
.map-ph .small:last-child{margin-bottom:0}
.src a{word-break:break-word}
.legal{padding-top:22px;padding-bottom:10px;max-width:820px}
.legal h1{margin:0 0 14px;font-size:clamp(1.6rem,4vw,2.2rem)}
.legal .box p:last-child{margin-bottom:0}
.legal .facts li{padding:8px 0}
.legal code{background:#f1f2f8;padding:1px 6px;border-radius:5px;font-size:.9em}
.legal .upd{margin:18px 0 0;text-align:center}
footer{background:#fff0e6;color:var(--muted);padding:22px 0;margin-top:30px;font-size:.88rem;border-top:5px solid transparent;border-image:var(--stripe) 1 0 0 0}
.foot-nav{margin:14px 0 8px;display:flex;flex-wrap:wrap;gap:6px 18px}
.foot-nav a{color:var(--accent);text-decoration:none}
.foot-nav a:hover{text-decoration:underline}
.foot-copy{margin:0;font-size:.85rem}
@media (max-width:560px){.hero{padding:38px 0 100px;background:url(fond-hero.svg?v=@@FOND@@) center bottom/auto 110px no-repeat,linear-gradient(160deg,#9f1239 0%,#e11d48 62%,#f97316 100%)}.box{padding:16px}.filters input,.filters select{width:100%}.map-ph{padding:20px 14px}}
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
  var cards = Array.prototype.slice.call(document.querySelectorAll('.card'));
  var count = document.getElementById('count');
  var empty = document.getElementById('empty');
  var reset = document.getElementById('reset');
  function norm(s) { return (s || '').normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase(); }
  function apply() {
    var text = norm(q.value).trim(), m = mois.value, r = region.value, g = genre.value, n = 0;
    cards.forEach(function (c) {
      var ok = (!text || c.dataset.name.indexOf(text) !== -1) &&
               (!m || c.dataset.mois.split(' ').indexOf(m) !== -1) &&
               (!r || c.dataset.region === r) &&
               (!g || c.dataset.genres.split('|').indexOf(g) !== -1);
      c.hidden = !ok;
      if (ok) n++;
    });
    count.textContent = n + (n > 1 ? ' festivals' : ' festival');
    empty.hidden = n !== 0;
  }
  [q, mois, region, genre].forEach(function (el) {
    el.addEventListener('input', apply);
    el.addEventListener('change', apply);
  });
  if (reset) reset.addEventListener('click', function () {
    q.value = ''; mois.value = ''; region.value = ''; genre.value = ''; apply();
  });
  apply();
})();
'''

def crowd_svg():
    """Foule de silhouettes les bras levés (dessin original, généré de façon déterministe)."""
    import random
    r = random.Random(11)
    W, H = 2400, 170
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" preserveAspectRatio="xMidYMax slice">']

    def layer(fill, alpha, n, hr, top, bottom, arms, phones):
        g = [f'<g fill="{fill}" stroke="{fill}" opacity="{alpha}" stroke-linecap="round">']
        for i in range(n):
            x = int((i + 0.5) * W / n + r.randint(-14, 14))
            rr = r.randint(hr[0], hr[1])
            hy = r.randint(top, bottom)
            g.append(f'<circle cx="{x}" cy="{hy}" r="{rr}" stroke="none"/>')
            g.append(f'<ellipse cx="{x}" cy="{hy + rr + 26}" rx="{rr + 9}" ry="30" stroke="none"/>')
            k = r.random()
            if k < arms:
                for s in (-1, 1) if r.random() < .7 else (r.choice((-1, 1)),):
                    ex, ey = x + s * r.randint(16, 34), hy - r.randint(22, 52)
                    g.append(f'<path d="M{x + s * (rr + 3)} {hy + rr + 14}L{ex} {ey}" fill="none" stroke-width="{max(5, rr // 2)}"/>')
                    if r.random() < phones:
                        g.append(f'<rect x="{ex - 4}" y="{ey - 11}" width="8" height="13" rx="2" fill="#fde68a" stroke="none"/>')
        g.append('</g>')
        return "".join(g)

    out.append(layer("#7f1d3a", .55, 78, (9, 11), 78, 108, .45, 0))
    out.append(layer("#3b0a1c", .92, 52, (13, 16), 108, 130, .5, .18))
    out.append(f'<rect y="{H - 28}" width="{W}" height="28" fill="#3b0a1c"/>')
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
FOND_V = hashlib.md5((crowd_svg() + motif_svg()).encode("utf-8")).hexdigest()[:8]
CSS = CSS.replace("@@FOND@@", FOND_V)
CSS_V = hashlib.md5(CSS.strip().encode("utf-8")).hexdigest()[:8]
JS_V = hashlib.md5(JS.strip().encode("utf-8")).hexdigest()[:8]


if __name__ == "__main__":
    data = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    fests = build(data)
    (OUT / "style.css").write_text(CSS.strip() + "\n", encoding="utf-8")
    (OUT / "script.js").write_text(JS.strip() + "\n", encoding="utf-8")
    print(f"{len(fests)} fiches générées dans {OUT}")
