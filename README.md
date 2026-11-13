# FestiGuide

Petit site qui rassemble les infos des plus gros festivals : dates, lieu, prix, artistes, site officiel et carte.

Festivals présents : We Love Green, Solidays, Les Ardentes, Festival Interceltique de Lorient, Fête de l'Humanité.

## Fonctionnement

Site statique en HTML, CSS et JavaScript, sans dépendance :

- `index.html` : page d'accueil avec recherche et filtres (mois, pays)
- `<festival>.html` : une fiche par festival (dates, prix, artistes, carte, accès, sources)
- `style.css` : mise en page
- `script.js` : filtres de la page d'accueil

Pour le voir en local, ouvre `index.html` dans un navigateur.

## Mettre à jour les infos

Chaque fiche est un fichier HTML. Pour changer une date, un prix ou un artiste, modifie le fichier correspondant. Les prix et les artistes affichés sont ceux de la dernière édition connue tant que la nouvelle n'est pas annoncée.

## Remarque

Les informations viennent de sources publiques (listées en bas de chaque fiche) et peuvent changer. Vérifie toujours sur le site officiel du festival avant d'acheter un billet. Ce projet n'est affilié à aucun festival.
