# FestiGuide — notes pour Claude

Annuaire de 134 festivals de musique (France, plus une quarantaine en Belgique : Tomorrowland, Rock Werchter, Pukkelpop, Graspop, Gentse Feesten, Les Ardentes, Dour…). Site statique publié par GitHub Pages sur https://lanfus.github.io/festiguide/

Projet personnel de Florent H. (GitHub : Lanfus). Objectif : servir de preuve de compétences SEO / CRM pour sa recherche d'alternance en e-commerce. Donc le référencement et la qualité des données comptent plus que la sophistication technique.

## Règle la plus importante

**Les fichiers `.html` à la racine sont générés. Ne les modifie jamais à la main.**

Toute correction de contenu (date, prix, artiste, nouveau festival) se fait dans `src/festivals.json`, puis on régénère. Une modification directe du HTML est écrasée à la régénération suivante.

```bash
python3 src/check.py src/festivals.json /tmp/ok.json   # valide les données
python3 src/build.py src/festivals.json .              # régénère les 139 pages à la racine
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
| `<slug>.ics` (70 fichiers) | générés par `build.py` pour les festivals qui ont `iso` : bouton « Ajouter à mon agenda » des fiches. Ne pas les éditer ni les mettre dans le sitemap |
| `mentions-legales.html`, `conditions-utilisation.html`, `confidentialite.html`, `cookies.html` | générés par `build_legal()` dans `build.py` (pas de CGV ni page de remboursement : le site ne vend rien, à créer si de la vente ou de l'affiliation apparaît) |
| `llms.txt` | généré par `build.py` : résumé du site et liste des fiches pour les assistants IA |

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

Palette « vin » (demandée par Florent le 18/11/2026, remplace l'ancienne palette rose-rouge/orange) : rouge vin `#7b1e3a` (accent, liens, boutons), violet vin `#4a1d42` (`--plum` : survol, filtres actifs, logo), et en contraste la couleur opposée, vert menthe `#3ee6a8` (`--pop`, seulement sur fond vin ou en aplat décoratif) / vert foncé `#0a6b4a` (`--pop-d`, texte sur fond clair, focus clavier), fond crème `#fbf8f4`. Ancienne note conservée pour l'historique : Florent a demandé « un peu moins de contraste » : couleurs et foule volontairement douces, mais le texte blanc du bandeau doit rester à au moins 4,5:1 (mesuré le 17/11/2026 sur les pixels réels, rayons et paillettes compris : pire cas 4,66:1 ; ne pas réaugmenter l'opacité des rayons/paillettes ni rapprocher l'orange du texte sans re-mesurer) (le dégradé reste rouge sous le texte). Le violet vif avait été retiré (trop fort) ; le violet vin sombre a été réintroduit à la demande de Florent le 18/11/2026. Le style reste clair (Florent ne voulait pas de noir). Les visuels sont dessinés en code, jamais copiés des festivals. Le bandeau n'a volontairement aucun personnage : Florent a refusé les silhouettes en bonshommes bâton (« ça fait IA ») et les photos/vecteurs de foule fournis n'étaient pas libres de droits. Le décor (`scene_svg()`) est un champ de festival au coucher du soleil : collines, chapiteaux à fanions, grande roue, guirlandes. Ne pas réintroduire de foule ni de photo sans licence claire.

## Nom de domaine (préparé le 18 novembre 2026)

Interrupteur `DOMAINE` en haut de `build.py` : vide = `lanfus.github.io/festiguide` ; rempli = `BASE_URL` passe sur `https://<domaine>` et `build.py` écrit `CNAME` (le supprime si on revide). Ne jamais le remplir avant que les DNS pointent vers GitHub Pages (procédure complète dans le README). `build.py` génère aussi `404.html` (avec `<base>` vers la racine, noindex) et `.nojekyll`. Les `UID` des `.ics` gardent `@lanfus.github.io` exprès : les changer créerait des doublons dans les agendas déjà importés.

## Effet visuel du bandeau (18 novembre 2026)

Florent a demandé de choisir entre cinq styles d'effet : fluted glass (verre cannelé, marques premium), halftone (trame de points, affiche imprimée), blueprint (plan technique bleu), contour lines (courbes de niveau, plein air et cartes), ASCII (image en caractères, outils de dev). Choix : **halftone**, cohérent avec la direction « programme imprimé ». `trame_svg()` dessine un soleil en points dont la taille suit la lumière (`trame.svg`), posé en `.hero::before` en haut à droite, réduit sur mobile. Ne pas empiler un deuxième effet ; garder le texte blanc à 4,5:1 si on change l'opacité ou la couleur des points.

## Refonte « moins slop IA » (18 novembre 2026)

Demandée par Florent, avec la méthode du skill unslop (heydamir/unslop, CC BY 4.0, lue mais non installée). Direction : fond papier crème `#fbf8f4`, encre `#2b2623`, un seul accent `#b0304f` (boutons, liens, mois actif), le décor du bandeau reste le seul élément riche. Changé dans `build.py` : plus de dégradés sauf le bandeau, plus de bande orange/ambre sur les cartes, pas d'ombres ni de survol qui bouge, graisses 400-600 (plus de 800), plus de capitales espacées, rayons 6/8/12 (plus de pastilles rondes partout), chiffres tabulaires, emoji remplacés par des icônes SVG en trait fin via `ic()` (une seule taille et une seule épaisseur), fond de page sans halos ni `motif.svg` (le fichier est encore généré mais n'est plus référencé). H1 de l'accueil : « Trouve ton festival de musique en France et en Belgique ». Contraste du texte blanc du bandeau re-mesuré le 18/11 sur les pixels réels, de 320 à 1600 px : pire cas 4,95:1. Ne pas remettre d'emoji ni de dégradé hors bandeau.

## Direction « programme de festival imprimé » (18 novembre 2026, 2e passe)

Suite de la refonte : la structure faisait encore gabarit (grille de cartes identiques à gros bouton, rangée de chiffres clés, boîtes blanches partout). Changé dans `build.py` :
- Police d'affiche **Big Shoulders Display** (OFL, licence dans `fonts/OFL.txt`), auto-hébergée dans `fonts/big-shoulders-display.woff2` : aucune requête tierce. Utilisée en capitales pour le logo, les H1, les titres de section, les noms de festivals et le line-up ; le texte courant reste en police système.
- Accueil : plus de cartes ni de bouton « Voir la fiche ». Chaque festival est une ligne de programme (`.card` gardé pour le JS) : colonne de dates (`date_block()` : jours en gros si `iso`, sinon mois habituel grisé + « à confirmer »), nom, lieu, styles, puis prix/visiteurs/compte à rebours à droite. Toute la ligne est cliquable (lien étiré sur le `h3`). Rangée de chiffres du bandeau retirée (les chiffres sont dans la phrase).
- Mois en bandeau calendrier, styles en onglets texte soulignés, liens « Explorer » en texte souligné.
- Fiches : sections séparées par un filet épais au lieu de boîtes, tuiles « En bref » en bande à séparateurs, **line-up typographié comme une affiche** (`.lineup` / `.act`), trait décoratif sous le H1 retiré.
- Mobile : filtres deux par ligne, liste en deux colonnes (dates + contenu).
Ne pas remettre de grille de cartes à bouton ni de rangée de statistiques.

## Mesure, alerte e-mail et guide (18 novembre 2026, 3e passe)

Demandé par Florent pour prouver des compétences SEO / CRM chiffrées.
- **Interrupteurs en haut de `build.py`** : `GOATCOUNTER`, `NEWSLETTER_ACTION`, `GUIDE_TEMOIGNAGE`. Vides = rien n'est chargé ni affiché. État au 18/11 : GoatCounter activé (`lanfus`, tableau de bord https://lanfus.goatcounter.com) ; Brevo activé le 19/11 (formulaire « FestiGuide - Alertes » → liste « FestiGuide - Alertes » #3, double opt-in, redirections vers `inscription-envoyee.html` puis `inscription-confirmee.html`, pages générées par `build_inscription()`, en noindex et hors sitemap ; automatisation Brevo #1 « Message de bienvenue » active depuis le 18/11 : ajout à la liste #3 → 1 minute → e-mail #7 « Ton alerte FestiGuide est active », HTML codé, bouton vers la fiche si `FESTIVAL` est rempli, UTM `utm_campaign=bienvenue`, pas de réentrée) ; témoignage encore vide. Procédure d'activation dans le README.
- **GoatCounter** (sans cookie) : script auto-hébergé `src/goatcounter.js` (ISC) copié à la racine par `build.py` ; seul le comptage part vers `<code>.goatcounter.com`. C'est l'unique exception assumée à « aucune ressource tierce » : une mesure d'audience envoie forcément ses données à un service. Événements suivis par `data-goatcounter-click` : `billetterie-<slug>`, `agenda-<slug>`, `partage-<slug>`, `newsletter-<page>`.
- **Alerte e-mail Brevo** : `newsletter_form()`, formulaire HTML simple posté à Brevo seulement au clic (aucun script Brevo, pas de reCAPTCHA chargé), case de consentement obligatoire (15 ans et plus), double opt-in à activer côté Brevo, attributs `FESTIVAL`, `STYLE`, `SOURCE`. Affiché sur l'accueil et sur chaque fiche.
- **Pages légales conditionnelles** : `build_legal()` adapte confidentialité, cookies et conditions d'utilisation selon les interrupteurs. Ne jamais activer un outil sans régénérer ces pages.
- **Guide** `guide-securite-festival.html` (`build_guide()`) : billets/revente (art. 313-6-2 Code pénal), fouilles, bruit (décret 2017-1244 : 102 dB(A)/15 min, protections auditives gratuites), chaleur (recommandations canicule du ministère de la Santé, Santé publique France), secours (15, 112, Drogues Info Service 0 800 23 13 13). Sources dans `GUIDE_SOURCES`, exemples tirés de `festivals.json`. Le témoignage terrain de Florent (sécurité événementielle) est l'angle E-E-A-T : à écrire par lui, jamais inventé. Lié depuis l'en-tête, le pied de page, l'accueil et le bloc « À savoir » des fiches ; présent dans le sitemap et `llms.txt`.

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

1. Liens internes et balises équilibrées sur les 138 pages, aucun titre de plus de 60 caractères.
2. `script.js` s'évalue sans erreur, `sitemap.xml` est un XML valide, chaque bloc JSON-LD parse.
3. Avec Playwright : aucune requête externe et aucun cookie avant le clic sur la carte, filtres de l'accueil fonctionnels, pas de scroll horizontal à 390 px de large.

## État au 13 novembre 2026

70 festivals sur 134 ont des dates confirmées (18/11/2026 : Pukkelpop 19–22 août 2027, site officiel ; Festival Le Bon Air 14–16 mai 2027, billetterie Shotgun ; 17/11/2026 : Rise Festival 5–12 déc. 2026 et Snowattack 16–23 janv. 2027, office de tourisme des 2 Alpes ; Marvellous Island 15–16 mai 2027, Paris Je t'aime ; 16/11/2026 : Chamonix Unlimited 25–29 mars 2027, office de tourisme de Chamonix ; Snowboxx 13–20 mars 2027, office de tourisme d'Avoriaz ; 15/11/2026 : Art Rock 14–16 mai 2027, site officiel ; 14/11/2026 : Rio Loco 9–13 juin 2027, source Ville de Toulouse), les 64 autres sont marqués à confirmer. Cas particuliers déjà traités, à ne pas « corriger » par erreur : Rock en Seine ne se tient pas en 2027 (pause, retour en août 2028), Lollapalooza Paris n'est pas confirmé pour 2027, Solidays 2026 a été annulé pour canicule, Delta Festival et Download France ont été volontairement exclus car ils n'existent plus. Ajoutés le 13 novembre 2026 : Trans Musicales (2–6 déc. 2026), Dour, Art Rock, Terres du Son, Carcassonne. Pour Dour, Terres du Son et Carcassonne (Art Rock confirmé le 15/11), les dates 2027 ne sont pas confirmées par une source officielle (Dour 7–11 juillet circule mais restent à vérifier) : ne pas passer `iso` tant qu'un communiqué officiel ne les confirme pas. Les sites officiels n'étaient pas consultables depuis la session de recherche.

À faire ensuite : brancher Google Search Console et soumettre le sitemap, puis ajouter un guide pratique des festivals écrit depuis l'expérience de Florent en sécurité événementielle (Solidays, We Love Green, Dream Nation…), qui est l'angle que les gros sites concurrents ne peuvent pas copier.

## Périmètre et extension du 13 novembre 2026 (100 → 206 festivals)

**Périmètre décidé par Florent : pas de cinéma, pas d'arts de la rue, pas de livres.** Retirés du site le 13 novembre (16 fiches) : Cannes, Annecy, Lumière, Deauville, Gérardmer, La Rochelle cinéma, Cinemed, Clermont-Ferrand court métrage, Premiers Plans, Étonnants Voyageurs, Quais du Polar, Aurillac, Chalon dans la rue, ainsi que trois fiches de cinéma ajoutées puis retirées dans la foulée (Angoulême francophone, Cabourg, Sarlat). Ne pas les rajouter. La bande dessinée (Angoulême BD, Quai des Bulles) a été gardée : à retirer aussi si Florent la considère comme du livre. Les pages supprimées renvoient désormais une 404 : à signaler dans Search Console et à re-soumettre le sitemap.

Sources des ajouts : sites officiels, offices de tourisme, villes, billetteries. Les 16 fiches issues de l'agrégateur Music Festival Wizard (Rise, Snowattack, Snowboxx, Rock the Pistes, Chamonix Unlimited, Le Bon Air, Marvellous Island, Le Jardin du Michel, Rampage, Rampage Open Air, Horst, Werchter Boutique, Paradise City, Ostend Beach, BrakRock, WeCanDance) sont toutes « à confirmer » et citent cet agrégateur comme source non officielle. Exclus faute de source : Weather Festival (plus d'activité depuis 2016), Chorus (annulé définitivement), Rock in Évreux, Rockomotives (édition 2026 seulement), Bars en Trans, Garance Reggae (annulé en 2026), Sylak, Woodstower, I Love Techno, Mimos, Viva Cité. Lot de marchés de Noël (Strasbourg, Colmar, Metz, Mulhouse, Lyon, Bruxelles, Liège) : dates de l'édition 2026 en cours, officielles ; elles passeront en 2026 dans la frise des mois.

À re-vérifier sur les sites officiels dès que possible (dates absentes, contradictoires ou non officielles) : Escale à Sète (site : 2028 ; Facebook : avril 2027), BIFFF retiré, Fêtes de Wallonie (sources contradictoires), Madeleine de Mont-de-Marsan (règle déduite, pas de communiqué), La Chaise-Dieu (dates relevées chez Haute-Loire Tourisme seulement), Biennale de la danse de Lyon (un agenda donne d'autres dates), Fête des Remparts de Dinan, Foire aux Vins d'Alsace, Nuit Blanche (office de tourisme seulement).

Fiches encore pauvres : presque aucune des 106 fiches ajoutées n'a de prix, d'accès ni de conseils ; c'est le chantier suivant et ce qui distingue le site des concurrents.

## Retrait des non-festivals (13 novembre 2026, 206 → 155)

Florent veut un annuaire de festivals uniquement. Retirés (51 fiches) : carnavals (Nice, Dunkerque, Limoux, Granville, Binche, Alost, Malmedy, Paris, Bailleul, Chalon), Fête du Citron, férias (Nîmes, Dax, Béziers, Arles), fêtes populaires et traditions (Bayonne, Gayant, Madeleine, Jeanne d'Arc, Remparts, Provins, Napoléoniennes, Ommegang, Ath, Mons, Wallonie, Escale à Sète, Braderie de Lille, Mondial Air Ballons, Armada, cerfs-volants de Berck, Vendanges de Montmartre, Bordeaux Fête le Vin, Foire aux Vins d'Alsace, Sarmentelles, Journées du patrimoine, Nuit Blanche), les 7 marchés de Noël, salons et conventions (Japan Expo, Paris Games Week, Salon de l'agriculture, Paris Photo), Techno Parade, Les Tombées de la Nuit (arts de la rue), Rendez-vous de l'histoire (conférences). Ne pas les rajouter. Gardés malgré un doute : Fête de la Musique, Fête des Lumières, Gentse Feesten, Fête de l'Humanité (vrais programmes de concerts/spectacles), festivals de BD, de photo et de géographie, Festival des jardins de Chaumont. Les pages supprimées renvoient une 404 : à signaler dans Search Console.

## Musique uniquement (13 novembre 2026, 155 → 135)

Cible décidée par Florent : des jeunes qui cherchent vite un festival de musique. Retirés (20) : théâtre, danse, BD, photo, géographie, jardins et fêtes de ville (Avignon, Angoulême BD, Quai des Bulles, Rencontres d'Arles, Visa pour l'image, La Gacilly, Fête des Lumières, Festival d'Automne, Paris l'été, Festival de Marseille, Montpellier Danse, Biennale de la danse de Lyon, Marionnettes, Mythos, Festival d'Anjou, Mois Molière, Printemps des Comédiens, Festival international de géographie, Jardins de Chaumont, Gentse Feesten). Ne pas les rajouter : tout nouveau festival doit être un festival de musique. Gardés : classique, opéra et baroque (c'est de la musique ; à retirer si Florent veut cibler les jeunes), Nuits de Fourvière et Nuits de la Citadelle (concerts et spectacles). Titre et description de l'accueil mis à jour dans `build.py`.

Reggae Sun Ska retiré le 14/11/2026 : aucune source officielle (seul un guide non officiel), ne pas le remettre sans site officiel. MaMA gardé (site officiel présent).


## Audit légal et accessibilité du 17 novembre 2026

Constat : aucun cookie, aucun stockage local, aucune requête externe avant clic (Playwright) ; aucun formulaire ni compte ; aucune `<img>` (visuels en CSS/SVG, emojis décoratifs en `aria-hidden`). Ajouts : page `conditions-utilisation.html`, lien d'évitement « Aller au contenu », focus visible, `llms.txt`, JSON-LD `WebSite` sur l'accueil. Corrigé : contraste du bandeau (3 à 3,4:1 avant), mention « cadre UE–États-Unis » retirée de `confidentialite.html` (non vérifiée pour GitHub : seules les clauses contractuelles types sont sourcées), clause de compétence des tribunaux réservée aux règles impératives de protection du consommateur (lectorat belge). Points à décider par Florent : mentions légales sans adresse postale (régime LCEN art. 6-III-2 : suppose que ses éléments d'identité ont été donnés à GitHub) ; si le site devient une activité professionnelle, ajouter l'adresse. Cette analyse n'est pas un avis juridique.

## Pages de regroupement (18 novembre 2026)

`build.py` génère 35 pages de listes pour le SEO : par mois (`festivals-musique-<mois>.html`, seuil 3 festivals), par style (`GENRE_PAGES`, seuil 5), par région et pour la Belgique (seuil 5). Définies par `group_defs()`, rendues par `group_page()`. Elles sont liées depuis l'accueil (bloc « Explorer »), depuis chaque fiche (« Voir aussi »), le sitemap et `llms.txt`. Pour ne pas créer de pages creuses, ne pas baisser les seuils ; une page n'existe que si elle a assez de festivals. Le texte d'intro est calculé à partir des données (comptes, plus gros festivals, prix le plus bas), rien n'est rédigé à la main. Région « Bruxelles » harmonisée en « Bruxelles-Capitale ».

## Enrichissement du 18 novembre 2026

Rock Werchter (prix 2027, train inclus, Coins, revente), Graspop (billetterie ouverte le 14/11, 110 groupes), Jazz à Juan (accès, tarif réduit, soirées offertes d'après la page 2026) enrichis depuis les sites officiels. Tomorrowland Belgium laissé tel quel : les pages officielles trouvées mélangent 2026 et 2027, donc aucun prix relevé. Pukkelpop passé en dates confirmées (19–22 août 2027, site officiel). Fiches toujours vides côté prix, accès et conseils : voir `python3` ci-dessus (`prices == []`), à traiter par ordre de taille.
