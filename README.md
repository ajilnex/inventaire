# Décodage

**Des cours ouverts** — texte, audio, cartes de mémorisation espacée. Gratuits, sans compte, sans publicité. Publiés à l'adresse : **https://ajilnex.github.io/inventaire/**

### Cours publiés

**[Inventaire](https://ajilnex.github.io/inventaire/cours/inventaire/)** — *Introduction à l'économie politique historique.* Les sociétés humaines produisent plus qu'il ne leur faut pour survivre : qui prend la différence, comment, et au nom de quoi ? Treize modules, deux heures trente de cours parlé, deux cent une cartes — de la tablette comptable d'Uruk à la crise contemporaine de la preuve statistique en histoire, en dialogue avec Scott, Wrigley, Braudel, Polanyi, Pomeranz, Allen, Malm, Beckert, Tilly, Acemoglu, Bloch et Porter.

## Structure du dépôt

```
cours.json              déclaration des cours — le point d'entrée du générateur
src-md/                 sources (markdown) — la vérité du contenu
  index.md              accueil du site
  cours.md              la page listant les cours
  methode.md            méthode de travail, transversale à tous les cours
  _fragments/           figures interactives (HTML/SVG autonomes)
  cours/<slug>/         un cours : _cours.md, NN-titre.md, bibliographie.md
anki/<slug>/            paquets de cartes, un par module
audio/<slug>/           pistes audio (MP3 mono 64 kbit/s)
audio-texte/<slug>/     versions orales des modules — source des pistes
assets/                 style.css, site.js, image de partage
_template.html          gabarit unique de page
build.py                génération du site : python3 build.py
check.py                suite de vérifications : python3 check.py
generer_audio.py        production des pistes depuis audio-texte/
```

Les pages HTML à la racine et dans `cours/` sont **générées** : ne jamais les éditer à la main.

## Développer

```bash
python3 build.py   # reconstruit toutes les pages depuis src-md/
python3 check.py   # liens, structure, formats, chaînes interdites — doit rester vert
```

Les deux commandes n'ont **aucune dépendance** hors de Python 3 standard. L'intégration continue exécute `check.py` à chaque poussée.

Avant toute contribution, lire **[AGENTS.md](AGENTS.md)** : il fixe les invariants du projet — charte intellectuelle, contraintes de forme, contrat des textes oraux, palette validée, procédure d'ajout d'un module ou d'un cours futur.

## Licence

Contenu et code sous [Creative Commons BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/deed.fr) — lecture, rediffusion, traduction et adaptation libres, avec attribution et partage à l'identique. Voir [LICENSE.md](LICENSE.md).
