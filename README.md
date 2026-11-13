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

Site statique en HTML, CSS et JavaScript, sans dépendance ni framework.

| Fichier | Rôle |
|---|---|
| `index.html` | page d'accueil : liste triée par date, recherche, filtres mois / région / genre |
| `<slug>.html` | une fiche par festival |
| `style.css` | mise en page |
| `script.js` | filtres de la page d'accueil |
| `sitemap.xml`, `robots.txt` | référencement |

Pour le voir en local, ouvre `index.html` dans un navigateur. Aucune installation nécessaire.

## Mettre à jour une fiche

Chaque fiche est un fichier HTML autonome : pour corriger une date, un prix ou un artiste, modifie le fichier correspondant directement sur GitHub (icône crayon, puis *Commit changes*). Le site se met à jour en une à deux minutes.

Les prix et les affiches affichés sont ceux de la dernière édition connue tant que la suivante n'est pas annoncée.

## Remarque

Les informations proviennent de sources publiques, citées en bas de chaque fiche, et changent souvent. Vérifie toujours sur le site officiel du festival avant d'acheter un billet. Ce projet n'est affilié à aucun festival et ne vend aucun billet.
