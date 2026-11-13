# Proxynet (ex-FestiGuide) — notes pour Claude

Annuaire de 206 grands festivals et grands événements (France, plus une quarantaine en Belgique : Tomorrowland, Rock Werchter, Pukkelpop, Graspop, Gentse Feesten, Les Ardentes, Dour…). Site statique publié par GitHub Pages sur https://lanfus.github.io/festiguide/

Projet personnel de Florent H. (GitHub : Lanfus). Objectif : servir de preuve de compétences SEO / CRM pour sa recherche d'alternance en e-commerce. Donc le référencement et la qualité des données comptent plus que la sophistication technique.

## Règle la plus importante

**Les fichiers `.html` à la racine sont générés. Ne les modifie jamais à la main.**

Toute correction de contenu (date, prix, artiste, nouveau festival) se fait dans `src/festivals.json`, puis on régénère. Une modification directe du HTML est écrasée à la régénération suivante.

```bash
python3 src/check.py src/festivals.json /tmp/ok.json   # valide les données
python3 src/build.py src/festivals.json .              # régénère les 210 pages à la racine
```

`check.py` normalise les mois, vérifie les sources, rejette les dates ISO passées ou incohérentes et signale les doublons. `build.py` trie les festivals par date de prochaine édition, génère l'accueil, une fiche par festival, les trois pages légales, `sitemap.xml` et `robots.txt`.

## Arborescence

| Chemin | Rôle |
|---|---|
| `src/festivals.json` | **la source de vérité** : un objet par festival |
| `src/build.py` | générateur (contient aussi le CSS et le JS, en bas du fichier) |
| `src/check.py` | validation et fusion des données |
| `src/og-image.html`, `src/og-image.png` | image de partage 1200x630 : le PNG est copié à la racine par `build.py`. Pour la refaire, capturer le HTML en 1200x630 avec Playwright |
| `*.html`, `style.css`, `script.js` | **générés**, publiés par GitHub Pages |
| `sitemap.xml`, `robots.txt`, `favicon.svg`, `og-image.png`, `fond-hero.svg`, `motif.svg` | générés ou copiés par `build.py` (`fond-hero.svg` : décor de champ de festival du bandeau, `motif.svg` : motif de fond de page, dessinés par `scene_svg()` et `motif_svg()`) |
| `<slug>.ics` (98 fichiers) | générés par `build.py` pour les festivals qui ont `iso` : bouton « Ajouter à mon agenda » des fiches. Ne pas les éditer ni les mettre dans le sitemap |
| `mentions-legales.html`, `confidentialite.html`, `cookies.html` | générés par `build_legal()` dans `build.py` |

## Contrat de données (un festival)

Champs obligatoires : `slug`, `name`, `city`, `country`. Tout le reste a une valeur par défaut dans `check.py`.

- `iso` : `["AAAA-MM-JJ", "AAAA-MM-JJ"]` seulement si les dates de la prochaine édition sont confirmées par une source, sinon `null`. `check.py` force `status` à « Dates à confirmer » quand `iso` est absent, et l'inverse.
- `status` : exactement « Dates annoncées » ou « Dates à confirmer ».
- `short` (facultatif) : nom court utilisé dans le `<title>` quand le nom complet le ferait dépasser 60 caractères (ex. Annecy). `make_title()` choisit le gabarit le plus complet qui tient en 60 caractères.
- `mois` : minuscules accentuées (`"juin"`, `"août"`, `"décembre"`), sert aux filtres.
- `visiteurs` (facultatif, entier) et `visiteurs_note` (obligatoire si `visiteurs`) : fréquentation publiée de la dernière édition, avec l'édition et la source. Sert au tri « les plus gros d'abord » (tri par défaut de l'accueil) et au badge « 👥 environ N visiteurs ». Sans chiffre sourcé, ne rien mettre : ne jamais estimer soi-même.
- `prices` et `sources` : listes de paires `[libellé, valeur]`. Au moins une source en `http`, sinon le festival est signalé.
- `prices_note` doit toujours dire de quelle édition viennent les tarifs.

## Ce qu'il ne faut pas faire

- **Ne jamais inventer** une date, un tarif ou un artiste. Si l'information n'est pas dans une source consultée, mettre `null` et l'expliquer dans `status_note` ou `prices_note`. C'est un site d'information : une fausse date fait rater un festival à quelqu'un.
- **Ne pas recopier** les textes, affiches, photos ou plans de scènes des festivals : contenu dupliqué pour le SEO et risque juridique. On reformule, et pour les plans on renvoie au site officiel.
- **Ne pas charger de ressource tierce automatiquement.** Les cartes Google Maps suivent le principe du double clic de la CNIL : `script.js` n'injecte l'iframe qu'après un clic sur « Afficher la carte ». Le site ne dépose donc aucun cookie et n'a pas besoin de bandeau de consentement. Si on ajoute un jour une mesure d'audience ou une newsletter, il faut un vrai bandeau **avant** tout dépôt de cookie, et mettre à jour `cookies.html` et `confidentialite.html`.
- Ne pas ajouter de framework ni de dépendance : le site doit rester ouvrable en double-cliquant sur `index.html`.

## Identité visuelle

Palette « coucher de soleil de scène » : rose-rouge adouci `#a8274a` / `#d93d5f`, orange `#f58a4e`, ambre `#fcc65a`, fond crème `#fff9f4`. Florent a demandé « un peu moins de contraste » : couleurs et foule volontairement douces, mais le texte blanc du bandeau doit rester à au moins 4,4:1 (le dégradé reste rouge sous le texte). Le violet a été retiré à la demande de Florent (trop fort) : ne pas le réintroduire. Le style reste clair (Florent ne voulait pas de noir). Les visuels sont dessinés en code, jamais copiés des festivals. Le bandeau n'a volontairement aucun personnage : Florent a refusé les silhouettes en bonshommes bâton (« ça fait IA ») et les photos/vecteurs de foule fournis n'étaient pas libres de droits. Le décor (`scene_svg()`) est un champ de festival au coucher du soleil : collines, chapiteaux à fanions, grande roue, guirlandes. Ne pas réintroduire de foule ni de photo sans licence claire.

## SEO déjà en place

Titres ≤ 60 caractères, descriptions 70–160, canonical, Open Graph + Twitter card avec `og-image.png`, favicon SVG, JSON-LD `BreadcrumbList` sur chaque fiche et `Festival` quand `iso` est renseigné, bloc « Autres festivals à découvrir » (4 liens par fiche, calculés par `related()` selon région, mois et genre), balise de vérification Google Search Console dans `head()` (ne pas la supprimer), sitemap soumis dans Search Console le 13 novembre 2026. Les liens vers `style.css` et `script.js` portent une empreinte (`?v=…`) calculée par `build.py` : sans elle, les navigateurs gardent l'ancien CSS en cache et les visiteurs ne voient pas les changements.

## Fonctionnalités de l'accueil et des fiches (ajoutées le 13 nov. 2026 après étude de festt.io, festapp.io, festivalabroad.com et festivalenfrance.com)

Ces sites ont des cartes pauvres (nom, dates, ville) et aucun n'affiche prix, accès, conseils ni statut des dates : c'est notre avantage, à garder. Ajouts : bandeau de chiffres, frise des 12 mois avec compteurs, pastilles des 8 styles les plus fréquents, filtre budget (`prix_num()` : Cannes a `price_from` 0 mais n'est pas gratuit, seul `is_free()` décide de « Gratuit »), tri (date, prix, A→Z), compte à rebours calculé dans le navigateur, et sur les fiches : tuiles « En bref », export `.ics`, bouton Partager. Tout vient de `festivals.json` : aucune donnée inventée, aucune ressource tierce, aucun cookie. Pas de favoris : ça demanderait du `localStorage` et une mise à jour de `cookies.html`. Idée suivante : pages de regroupement (par mois, région, style) pour le SEO, comme le fait festt.io.

## Ajout de masse du 13 novembre 2026 (43 → 100 festivals)

57 festivals ajoutés à partir de recherches web, source par source. Règle appliquée : `iso` seulement si la date vient de l'organisateur, de la ville/office de tourisme, de la billetterie (Live Nation, Ticketmaster…) ou du compte officiel du festival. Les sites agrégateurs (musicfestivalwizard, festiplannr, raveparty, carnifest…) ne suffisent pas : la date est alors citée dans `status_note` avec la mention « non officiel ». 28 des 57 ont `iso`.
À re-vérifier sur les sites officiels dès que possible (dates non confirmées ou ambiguës) : Pukkelpop, Motocultor, Couleur Café, Cactus Festival, Les Nuits Secrètes, Les Escales, Féria de Béziers (agrégateurs seulement) ; Rio Loco et Festival de Marseille (année illisible dans l'extrait) ; Pause Guitare (7–11 juillet selon l'office de tourisme, 6–11 selon le site) ; Calvi on the Rocks (travaux du Théâtre de Verdure signalés en 2025) ; Rencontres d'Arles (fin non relevée) ; Festival de Saint-Denis (début 3 juin seulement) ; Fêtes de Gayant (seul le dimanche 11 juillet est confirmé).
Exclus faute de source ou d'édition 2027 : Fnac Live Paris (annulé en 2026), Reggae Sun Ska, MaMA, Weather Festival, Les Tombées de la Nuit, Festival Chorus. La Braderie de Lille n'est pas un festival : gardée pour sa taille, signalée dans sa fiche. Le Carnaval de Dunkerque porte les dates de toute la saison (3 janvier – 17 avril 2027).
Les fiches ajoutées ont peu de prix, d'accès et de conseils (`prices`, `access`, `tips` vides) : les enrichir fiche par fiche est la suite logique, les concurrents n'ont pas ça.

## Vérifications avant de publier

1. Liens internes et balises équilibrées sur les 210 pages, aucun titre de plus de 60 caractères.
2. `script.js` s'évalue sans erreur, `sitemap.xml` est un XML valide, chaque bloc JSON-LD parse.
3. Avec Playwright : aucune requête externe et aucun cookie avant le clic sur la carte, filtres de l'accueil fonctionnels, pas de scroll horizontal à 390 px de large.

## État au 13 novembre 2026

98 festivals sur 206 ont des dates confirmées, les 108 autres sont marqués à confirmer. Cas particuliers déjà traités, à ne pas « corriger » par erreur : Rock en Seine ne se tient pas en 2027 (pause, retour en août 2028), Lollapalooza Paris n'est pas confirmé pour 2027, Solidays 2026 a été annulé pour canicule, Delta Festival et Download France ont été volontairement exclus car ils n'existent plus. Ajoutés le 13 novembre 2026 : Trans Musicales (2–6 déc. 2026), Dour, Art Rock, Terres du Son, Carcassonne. Pour les quatre derniers, les dates 2027 ne sont pas confirmées par une source officielle (Dour 7–11 juillet et Art Rock 14–16 mai circulent mais restent à vérifier) : ne pas passer `iso` tant qu'un communiqué officiel ne les confirme pas. Les sites officiels n'étaient pas consultables depuis la session de recherche.

À faire ensuite : brancher Google Search Console et soumettre le sitemap, puis ajouter un guide pratique des festivals écrit depuis l'expérience de Florent en sécurité événementielle (Solidays, We Love Green, Dream Nation…), qui est l'angle que les gros sites concurrents ne peuvent pas copier.

## Périmètre et extension du 13 novembre 2026 (100 → 206 festivals)

**Périmètre décidé par Florent : pas de cinéma, pas d'arts de la rue, pas de livres.** Retirés du site le 13 novembre (16 fiches) : Cannes, Annecy, Lumière, Deauville, Gérardmer, La Rochelle cinéma, Cinemed, Clermont-Ferrand court métrage, Premiers Plans, Étonnants Voyageurs, Quais du Polar, Aurillac, Chalon dans la rue, ainsi que trois fiches de cinéma ajoutées puis retirées dans la foulée (Angoulême francophone, Cabourg, Sarlat). Ne pas les rajouter. La bande dessinée (Angoulême BD, Quai des Bulles) a été gardée : à retirer aussi si Florent la considère comme du livre. Les pages supprimées renvoient désormais une 404 : à signaler dans Search Console et à re-soumettre le sitemap.

Sources des ajouts : sites officiels, offices de tourisme, villes, billetteries. Les 16 fiches issues de l'agrégateur Music Festival Wizard (Rise, Snowattack, Snowboxx, Rock the Pistes, Chamonix Unlimited, Le Bon Air, Marvellous Island, Le Jardin du Michel, Rampage, Rampage Open Air, Horst, Werchter Boutique, Paradise City, Ostend Beach, BrakRock, WeCanDance) sont toutes « à confirmer » et citent cet agrégateur comme source non officielle. Exclus faute de source : Weather Festival (plus d'activité depuis 2016), Chorus (annulé définitivement), Rock in Évreux, Rockomotives (édition 2026 seulement), Bars en Trans, Garance Reggae (annulé en 2026), Sylak, Woodstower, I Love Techno, Mimos, Viva Cité. Lot de marchés de Noël (Strasbourg, Colmar, Metz, Mulhouse, Lyon, Bruxelles, Liège) : dates de l'édition 2026 en cours, officielles ; elles passeront en 2026 dans la frise des mois.

À re-vérifier sur les sites officiels dès que possible (dates absentes, contradictoires ou non officielles) : Escale à Sète (site : 2028 ; Facebook : avril 2027), BIFFF retiré, Fêtes de Wallonie (sources contradictoires), Madeleine de Mont-de-Marsan (règle déduite, pas de communiqué), La Chaise-Dieu (dates relevées chez Haute-Loire Tourisme seulement), Biennale de la danse de Lyon (un agenda donne d'autres dates), Fête des Remparts de Dinan, Foire aux Vins d'Alsace, Nuit Blanche (office de tourisme seulement).

Fiches encore pauvres : presque aucune des 106 fiches ajoutées n'a de prix, d'accès ni de conseils ; c'est le chantier suivant et ce qui distingue le site des concurrents.
