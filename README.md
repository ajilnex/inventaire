# Inventaire

**Cours d'introduction à l'économie politique historique** — texte, audio, cartes de mémorisation espacée. Publié à l'adresse : **https://ajilnex.github.io/inventaire/**

Les sociétés humaines produisent plus qu'il ne leur faut pour survivre. Qui prend la différence, comment, et au nom de quoi ? Douze modules, de la tablette comptable d'Uruk à la crise contemporaine de la preuve statistique en histoire, en dialogue constant avec les auteurs qui structurent la discipline — Scott, Wrigley, Braudel, Polanyi, Pomeranz, Allen, Malm, Beckert, Tilly, Acemoglu, Bloch, Porter.

## Structure du dépôt

```
src-md/           sources du cours (markdown) — la vérité du contenu
src-md/_fragments/  figures interactives (HTML/SVG autonomes)
cours/            pages HTML générées (ne pas éditer à la main)
anki/             paquets de cartes, un par module (.txt importables dans Anki)
audio/            pistes audio générées (une par module)
audio-texte/      versions orales des modules (source des pistes)
assets/           style.css, site.js, image de partage
_template.html    gabarit unique de page
build.py          génération complète du site : python3 build.py
check.py          suite de vérifications : python3 check.py
```

## Développer

```bash
python3 build.py   # reconstruit toutes les pages depuis src-md/
python3 check.py   # liens, structure, formats, chaînes interdites — doit rester vert
```

Les deux commandes n'ont **aucune dépendance** hors de Python 3 standard. L'intégration continue exécute `check.py` à chaque poussée.

Avant toute contribution, lire **[AGENTS.md](AGENTS.md)** : il fixe les invariants du projet — charte intellectuelle, contraintes de forme, contrat des textes oraux, palette validée, procédure d'ajout d'un module ou d'un cours futur.

## Licence

Contenu et code sous [Creative Commons BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/deed.fr) — lecture, rediffusion, traduction et adaptation libres, avec attribution et partage à l'identique. Voir [LICENSE.md](LICENSE.md).
