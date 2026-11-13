# FestiGuide — notes pour Claude

Annuaire de 43 grands festivals (France, plus Les Ardentes et Dour en Belgique). Site statique publié par GitHub Pages sur https://lanfus.github.io/festiguide/

Projet personnel de Florent H. (GitHub : Lanfus). Objectif : servir de preuve de compétences SEO / CRM pour sa recherche d'alternance en e-commerce. Donc le référencement et la qualité des données comptent plus que la sophistication technique.

## Règle la plus importante

**Les fichiers `.html` à la racine sont générés. Ne les modifie jamais à la main.**

Toute correction de contenu (date, prix, artiste, nouveau festival) se fait dans `src/festivals.json`, puis on régénère. Une modification directe du HTML est écrasée à la régénération suivante.

```bash
python3 src/check.py src/festivals.json /tmp/ok.json   # valide les données
python3 src/build.py src/festivals.json .              # régénère les 47 pages à la racine
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
| `sitemap.xml`, `robots.txt`, `favicon.svg`, `og-image.png`, `fond-hero.svg`, `motif.svg` | générés ou copiés par `build.py` (`fond-hero.svg` : foule en silhouette du bandeau, `motif.svg` : motif de fond de page, tous deux dessinés par `crowd_svg()` et `motif_svg()`) |
| `mentions-legales.html`, `confidentialite.html`, `cookies.html` | générés par `build_legal()` dans `build.py` |

## Contrat de données (un festival)

Champs obligatoires : `slug`, `name`, `city`, `country`. Tout le reste a une valeur par défaut dans `check.py`.

- `iso` : `["AAAA-MM-JJ", "AAAA-MM-JJ"]` seulement si les dates de la prochaine édition sont confirmées par une source, sinon `null`. `check.py` force `status` à « Dates à confirmer » quand `iso` est absent, et l'inverse.
- `status` : exactement « Dates annoncées » ou « Dates à confirmer ».
- `short` (facultatif) : nom court utilisé dans le `<title>` quand le nom complet le ferait dépasser 60 caractères (ex. Annecy). `make_title()` choisit le gabarit le plus complet qui tient en 60 caractères.
- `mois` : minuscules accentuées (`"juin"`, `"août"`, `"décembre"`), sert aux filtres.
- `prices` et `sources` : listes de paires `[libellé, valeur]`. Au moins une source en `http`, sinon le festival est signalé.
- `prices_note` doit toujours dire de quelle édition viennent les tarifs.

## Ce qu'il ne faut pas faire

- **Ne jamais inventer** une date, un tarif ou un artiste. Si l'information n'est pas dans une source consultée, mettre `null` et l'expliquer dans `status_note` ou `prices_note`. C'est un site d'information : une fausse date fait rater un festival à quelqu'un.
- **Ne pas recopier** les textes, affiches, photos ou plans de scènes des festivals : contenu dupliqué pour le SEO et risque juridique. On reformule, et pour les plans on renvoie au site officiel.
- **Ne pas charger de ressource tierce automatiquement.** Les cartes Google Maps suivent le principe du double clic de la CNIL : `script.js` n'injecte l'iframe qu'après un clic sur « Afficher la carte ». Le site ne dépose donc aucun cookie et n'a pas besoin de bandeau de consentement. Si on ajoute un jour une mesure d'audience ou une newsletter, il faut un vrai bandeau **avant** tout dépôt de cookie, et mettre à jour `cookies.html` et `confidentialite.html`.
- Ne pas ajouter de framework ni de dépendance : le site doit rester ouvrable en double-cliquant sur `index.html`.

## Identité visuelle

Palette « coucher de soleil de scène » : rose-rouge adouci `#a8274a` / `#d93d5f`, orange `#f58a4e`, ambre `#fcc65a`, fond crème `#fff9f4`. Florent a demandé « un peu moins de contraste » : couleurs et foule volontairement douces, mais le texte blanc du bandeau doit rester à au moins 4,4:1 (le dégradé reste rouge sous le texte). Le violet a été retiré à la demande de Florent (trop fort) : ne pas le réintroduire. Le style reste clair (Florent ne voulait pas de noir). Les visuels sont dessinés en code, jamais copiés des festivals. La foule du bandeau (`crowd_svg()`) doit rester faite de vraies silhouettes (corps, cou, épaules, bras épais à coudes pliés, mains, coiffures variées, trois plans) : Florent a refusé une première version en bonshommes bâton qui faisait « IA ».

## SEO déjà en place

Titres ≤ 60 caractères, descriptions 70–160, canonical, Open Graph + Twitter card avec `og-image.png`, favicon SVG, JSON-LD `BreadcrumbList` sur chaque fiche et `Festival` quand `iso` est renseigné, bloc « Autres festivals à découvrir » (4 liens par fiche, calculés par `related()` selon région, mois et genre), balise de vérification Google Search Console dans `head()` (ne pas la supprimer), sitemap soumis dans Search Console le 13 novembre 2026. Les liens vers `style.css` et `script.js` portent une empreinte (`?v=…`) calculée par `build.py` : sans elle, les navigateurs gardent l'ancien CSS en cache et les visiteurs ne voient pas les changements.

## Vérifications avant de publier

1. Liens internes et balises équilibrées sur les 47 pages, aucun titre de plus de 60 caractères.
2. `script.js` s'évalue sans erreur, `sitemap.xml` est un XML valide, chaque bloc JSON-LD parse.
3. Avec Playwright : aucune requête externe et aucun cookie avant le clic sur la carte, filtres de l'accueil fonctionnels, pas de scroll horizontal à 390 px de large.

## État au 13 novembre 2026

29 festivals sur 43 ont des dates confirmées, les 14 autres sont marqués à confirmer. Cas particuliers déjà traités, à ne pas « corriger » par erreur : Rock en Seine ne se tient pas en 2027 (pause, retour en août 2028), Lollapalooza Paris n'est pas confirmé pour 2027, Solidays 2026 a été annulé pour canicule, Delta Festival et Download France ont été volontairement exclus car ils n'existent plus. Ajoutés le 13 novembre 2026 : Trans Musicales (2–6 déc. 2026), Dour, Art Rock, Terres du Son, Carcassonne. Pour les quatre derniers, les dates 2027 ne sont pas confirmées par une source officielle (Dour 7–11 juillet et Art Rock 14–16 mai circulent mais restent à vérifier) : ne pas passer `iso` tant qu'un communiqué officiel ne les confirme pas. Les sites officiels n'étaient pas consultables depuis la session de recherche.

À faire ensuite : brancher Google Search Console et soumettre le sitemap, puis ajouter un guide pratique des festivals écrit depuis l'expérience de Florent en sécurité événementielle (Solidays, We Love Green, Dream Nation…), qui est l'angle que les gros sites concurrents ne peuvent pas copier.
