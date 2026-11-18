# FestiGuide

Annuaire des grands festivals de France (et quelques voisins) : dates, lieu, prix, programmation, plan et site officiel.

👉 **[Voir le site](https://lanfus.github.io/festiguide/)**

## Contenu

Une fiche par festival, avec :

- les dates de la prochaine édition (ou le mois habituel quand elles ne sont pas annoncées)
- le lieu précis et une carte
- les tarifs, avec l'édition de référence
- la programmation (annoncée, ou celle de la dernière édition)
- l'accès, quelques conseils pratiques et le lien officiel
- les sources utilisées

## Fonctionnement

Site statique en HTML, CSS et JavaScript, sans dépendance ni framework. Les pages sont générées à partir d'un seul fichier de données.

| Chemin | Rôle |
|---|---|
| `src/festivals.json` | **la source de vérité** : toutes les données des festivals |
| `src/build.py` | génère les pages, le CSS, le JS et le sitemap |
| `src/check.py` | valide les données avant génération |
| `index.html` | page d'accueil générée : liste triée par date, recherche, filtres mois / région / genre |
| `<festival>.html` | une fiche par festival, générée |
| `mentions-legales.html`, `confidentialite.html`, `cookies.html` | pages légales générées |
| `style.css`, `script.js`, `sitemap.xml`, `robots.txt` | générés |

Pour voir le site en local, ouvre `index.html` dans un navigateur. Aucune installation nécessaire.

## Pages d'intention (SEO)

En plus des listes par mois, style et lieu, `group_defs()` génère des pages qui collent aux recherches réelles, seulement quand elles contiennent assez de festivals pour ne pas être creuses :

- `festivals-pas-chers.html` : billet à 50 € ou moins (au moins 8 festivals, triés par prix)
- `festivals-<mois>-<région>.html` : par exemple « Festivals en juillet en Bretagne » (au moins 5)
- `festivals-<style>-<mois>.html` pour juin, juillet et août : par exemple « Festivals rock en juillet » (au moins 8)

Les seuils sont en tête de `build.py` (`MIN_BUDGET`, `BUDGET_MAX`, `MIN_COMBO_REGION`, `MIN_COMBO_GENRE`). Chaque fiche renvoie vers deux de ces pages au plus. Suivre leurs impressions dans Search Console › Performances › Pages.

## Mettre à jour une fiche

⚠️ **Les fichiers `.html` sont générés : ne les modifie pas à la main**, ils seraient écrasés à la prochaine génération.

Pour corriger une date, un prix ou un artiste, ou pour ajouter un festival, modifie `src/festivals.json`, puis régénère :

```bash
python3 src/check.py src/festivals.json /tmp/ok.json   # vérifie les données
python3 src/build.py src/festivals.json .              # régénère les pages
```

Les prix et les programmations affichés sont ceux de la dernière édition connue tant que la suivante n'est pas annoncée ; chaque fiche précise l'édition de référence.

## Vie privée

Le site ne dépose aucun cookie. Les cartes Google Maps ne se chargent qu'après un clic explicite du visiteur, selon le principe du double clic recommandé par la CNIL : tant que personne ne clique, aucune requête n'est envoyée à Google.

La mesure d'audience (GoatCounter, sans cookie) et l'alerte e-mail (Brevo, double opt-in) sont **activées**. Chacune se coupe en vidant son identifiant en haut de `src/build.py` : elle ne s'affiche et ne charge alors plus rien. L'alerte ne charge aucun script Brevo : le formulaire n'envoie l'adresse qu'au clic sur « S'inscrire », puis Brevo renvoie vers `inscription-envoyee.html` et, après confirmation, vers `inscription-confirmee.html`. Les pages `confidentialite.html`, `cookies.html` et `conditions-utilisation.html` s'adaptent toutes seules à ce qui est activé.

## Activer la mesure d'audience (GoatCounter)

1. Crée un compte gratuit sur [goatcounter.com](https://www.goatcounter.com) et choisis un code, par exemple `festiguide` (ton tableau de bord sera `https://festiguide.goatcounter.com`).
2. Dans `src/build.py`, mets ce code : `GOATCOUNTER = "festiguide"`.
3. Régénère et publie. Le script est hébergé sur le site (`goatcounter.js`), seul le comptage part vers GoatCounter.
4. Pour ne pas compter tes propres visites : ouvre une fois `https://lanfus.github.io/festiguide/#toggle-goatcounter` dans chacun de tes navigateurs.

Ce qui est mesuré : pages vues, provenance, appareil, pays, et les clics sur **Site officiel et billetterie** (`billetterie-<festival>`), **Ajouter à mon agenda**, **Partager** et **S'inscrire** (`newsletter-<page>`). Le taux « clics billetterie / vues de la fiche » est ton indicateur de conversion.

## Activer l'alerte e-mail (Brevo)

1. Crée un compte gratuit sur [brevo.com](https://www.brevo.com).
2. **Contacts › Paramètres › Attributs** : crée trois attributs texte, `FESTIVAL`, `STYLE` et `SOURCE`.
3. **Contacts › Formulaires** : crée un formulaire d'inscription avec le champ e-mail, les trois attributs et la case de consentement. Active la **confirmation par double opt-in**.
4. Dans le partage du formulaire, prends le **code HTML** et copie l'adresse `action="https://….sibforms.com/serve/…"`.
5. Dans `src/build.py`, colle-la : `NEWSLETTER_ACTION = "https://….sibforms.com/serve/…"`. Régénère et publie.
6. Teste avec ta propre adresse depuis l'accueil et depuis une fiche, puis vérifie dans Brevo que le contact arrive avec `FESTIVAL` ou `STYLE` rempli. Si Brevo refuse l'envoi, c'est qu'un champ du site manque dans le formulaire Brevo.

Ensuite : une liste segmentée par festival (`FESTIVAL`) et par style (`STYLE`), et une campagne envoyée à un segment quand des dates passent à « confirmées » dans `festivals.json`.

## Passer sur un vrai nom de domaine

Tout est prêt dans le code : il suffit de remplir `DOMAINE` en haut de `src/build.py`. L'hébergement reste GitHub Pages, gratuit. Seul le domaine se paie (environ 7 à 15 € par an). Libres au 18/11/2026 : `lefestiguide.fr`, `monfestiguide.fr`, `festi-guide.fr`, `festiguide.info` (`festiguide.fr` et `.com` sont pris).

**Ordre à respecter**, sinon le site est coupé le temps que les DNS se propagent :

1. **Acheter le domaine** chez un registrar (OVH, Gandi, Infomaniak…).
2. **Prouver à GitHub que le domaine est à toi** (évite qu'un autre compte le détourne) : GitHub › Settings (du compte) › Pages › *Add a domain*. GitHub donne un enregistrement `TXT` à créer chez le registrar, puis *Verify*.
3. **Zone DNS chez le registrar** (supprimer d'abord les enregistrements `A`/`AAAA` par défaut qui pointent vers une page de parking) :

   | Type | Nom | Valeur |
   |---|---|---|
   | A | `@` | `185.199.108.153` |
   | A | `@` | `185.199.109.153` |
   | A | `@` | `185.199.110.153` |
   | A | `@` | `185.199.111.153` |
   | AAAA | `@` | `2606:50c0:8000::153` |
   | AAAA | `@` | `2606:50c0:8001::153` |
   | AAAA | `@` | `2606:50c0:8002::153` |
   | AAAA | `@` | `2606:50c0:8003::153` |
   | CNAME | `www` | `lanfus.github.io.` |

   Vérifier la propagation (de quelques minutes à quelques heures) : `nslookup lefestiguide.fr` doit renvoyer les quatre adresses `185.199.x.153`.
4. **Basculer le site** : mettre `DOMAINE = "lefestiguide.fr"` dans `src/build.py`, régénérer, publier. `build.py` écrit le fichier `CNAME` ; toutes les adresses (canonical, Open Graph, sitemap, `llms.txt`, robots) passent sur le nouveau domaine. GitHub redirige alors automatiquement `lanfus.github.io/festiguide/…` vers `lefestiguide.fr/…` (redirection 301 : Google transfère le référencement).
5. **HTTPS** : dépôt › Settings › Pages, attendre que le certificat soit émis, puis cocher *Enforce HTTPS*.
6. **Search Console** : ajouter une propriété *Domaine* pour `lefestiguide.fr` (validation par un `TXT` chez le registrar), soumettre `https://lefestiguide.fr/sitemap.xml`. Garder l'ancienne propriété : elle montrera la redirection.
7. **Brevo** :
   - formulaire « FestiGuide - Alertes » › Paramètres : remplacer les deux URL de redirection par `https://lefestiguide.fr/inscription-envoyee.html` et `…/inscription-confirmee.html` ;
   - automatisation « Message de bienvenue », e-mail #7 : remplacer `lanfus.github.io/festiguide` par `lefestiguide.fr` dans les liens ;
   - conseillé : créer une adresse `contact@lefestiguide.fr` (souvent incluse avec le domaine), l'utiliser comme expéditeur et **authentifier le domaine** dans Brevo › Paramètres › Expéditeurs, domaines (enregistrements DKIM, SPF et DMARC fournis par Brevo à copier chez le registrar). Envoyer depuis une adresse Gmail via Brevo fait souvent atterrir les e-mails en indésirables.
8. **GoatCounter** : rien à changer, il compte les pages quel que soit le domaine. Refaire `#toggle-goatcounter` sur la nouvelle adresse pour ne pas compter tes visites.
9. Mettre à jour le lien en haut de ce README et la description du dépôt GitHub.

Pour revenir en arrière : vider `DOMAINE`, régénérer et publier (le fichier `CNAME` est supprimé).

## Tableau de bord (à tenir chaque semaine)

| Indicateur | Où le lire |
|---|---|
| Impressions, clics, position moyenne, top requêtes | Google Search Console › Performances |
| Visiteurs, pages vues, top fiches, provenance | GoatCounter |
| Clics billetterie par fiche (conversion) | GoatCounter › événements `billetterie-*` |
| Inscrits, taux de confirmation, taux d'ouverture et de clic | Brevo |

Garde une capture datée chaque mois : c'est la preuve chiffrée du projet.

## Remarque

Les informations proviennent de sources publiques, citées en bas de chaque fiche, et changent souvent. Vérifie toujours sur le site officiel du festival avant d'acheter un billet. Ce projet n'est affilié à aucun festival et ne vend aucun billet.
