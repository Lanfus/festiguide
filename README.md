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

## Mettre à jour une fiche

⚠️ **Les fichiers `.html` sont générés : ne les modifie pas à la main**, ils seraient écrasés à la prochaine génération.

Pour corriger une date, un prix ou un artiste, ou pour ajouter un festival, modifie `src/festivals.json`, puis régénère :

```bash
python3 src/check.py src/festivals.json /tmp/ok.json   # vérifie les données
python3 src/build.py src/festivals.json .              # régénère les pages
```

Les prix et les programmations affichés sont ceux de la dernière édition connue tant que la suivante n'est pas annoncée ; chaque fiche précise l'édition de référence.

## Vie privée

Le site ne dépose aucun cookie et n'utilise aucun outil de mesure d'audience. Les cartes Google Maps ne se chargent qu'après un clic explicite du visiteur, selon le principe du double clic recommandé par la CNIL : tant que personne ne clique, aucune requête n'est envoyée à Google.

## Remarque

Les informations proviennent de sources publiques, citées en bas de chaque fiche, et changent souvent. Vérifie toujours sur le site officiel du festival avant d'acheter un billet. Ce projet n'est affilié à aucun festival et ne vend aucun billet.
