# AGENTS.md — invariants du projet Décodage

Ce fichier s'adresse à tout agent — humain ou machine — qui développe ce dépôt. Les règles ci-dessous ne sont pas des préférences : elles sont le contrat du projet. Une contribution qui les viole est refusée, si brillante soit-elle.

## 1. Charte intellectuelle (s'applique à tout contenu)

- **Aucun chiffre sans son fabricant.** Tout nombre cité indique d'où il vient et comment il a été construit. Les meilleurs passages du cours montrent la fourchette avant le point (voir Wrigley, module 2) : imiter cela.
- **Aucun auteur sans son argument.** Un nom s'accompagne de sa thèse, de l'objection qu'on lui fait, et de ce qui en a été retenu.
- **Aucune explication sans concurrente** quand elle existe ; et quand elle n'existe pas, on le dit.
- **Aucune référence non vérifiée.** Auteur, titre, éditeur, date : vérifiés dans le document lui-même ou explicitement signalés comme non vérifiés. Ne jamais lisser une incertitude. Ne jamais citer une phrase dont on n'a pas vu la page (voir l'avertissement Tilly, module 5 — il est dans le cours parce qu'il est la règle du projet).
- **Le cours renvoie aux livres, jamais l'inverse.** Toute fonctionnalité doit rendre une lecture possible ou plus profonde ; une fonctionnalité qui ne passe pas ce test est retirée.

## 2. Contenu et langue

- Français de haute tenue, registre du cours : construction pas à pas, définitions opératoires d'abord, controverses nommées avec leurs défenseurs réels. Pas de jargon sans construction préalable.
- Structure d'un module : en-tête `# Module N — Titre`, bloc **Lecture**, sections `## n.` numérotées, section finale `## Ce qu'il faut emporter` (liste), lien vers le module suivant.
- **Chaînes interdites** dans tout contenu publié (vérifiées par `check.py`) : toute mention de fichiers locaux, de bibliothèques personnelles, d'outils de session ou de sources de téléchargement. Le site ne contient et ne pointe **aucun texte sous droits**.

## 3. Le pipeline

```
cours.json + src-md/**.md ──build.py──▶ *.html + cours/<slug>/*.html + sitemap.xml
src-md/_fragments/fig-*.html ──(marqueur @@FIG:nom@@)──▶ injectés en place
audio-texte/<slug>/NN.txt ──generer_audio.py──▶ audio/<slug>/NN.mp3
```

**Audio.** `python3 generer_audio.py [NN …]` produit les pistes manquantes ; la clé API est lue dans `~/.config/elevenlabs/key` et **ne doit jamais entrer dans le dépôt**. Les pistes sont ensuite réencodées en **MP3 mono 64 kbit/s à débit constant** — c'est ce débit qui permet à `build.py` de calculer les durées affichées sans dépendance, et il divise par deux le poids pour les lecteurs en données mobiles. Le script refuse d'écraser une piste existante : supprimer le fichier pour régénérer.

- `cours.json` déclare les cours ; `src-md/` est **la seule source de vérité** du contenu. On n'édite jamais un HTML généré.
- Les ressources statiques portent une empreinte de version (`style.css?v=…`) calculée depuis leur contenu : un déploiement met à jour les navigateurs sans jamais désactiver leur cache.
- `python3 build.py` doit rester **sans dépendance** (Python 3 standard uniquement) et idempotent.
- `python3 check.py` doit rester **vert** ; toute nouvelle fonctionnalité ajoute ses vérifications.

## 4. Contrat des textes oraux (`audio-texte/`)

Transformation, jamais résumé : le texte oral contient toutes les phrases du module, adaptées à l'oreille.
- **Aucun chiffre en chiffres** : tout nombre, toute année, en toutes lettres françaises. Aucun caractère de la classe `[0-9#*_|\[\]]`, aucune URL.
- Siècles en toutes lettres (« dix-huitième siècle »), « pour cent » en toutes lettres, monnaies dites (« livres sterling »).
- Citations encadrées à l'oral : « je cite : … Fin de citation. »
- Listes converties en énumérations parlées ; titres de sections dits en phrases ; le bloc Lecture devient une phrase finale « Les lectures de ce module : … ».
- Un fichier par module, `audio-texte/<slug>/NN.txt`, moins de quarante mille caractères.

## 5. Design

- Palette : fond `#0b0d0c`, encre `#dde3de`, accent `#2fe08c` (interface seulement), **données** : vert `#15a869` et bleu `#5b7fd0` — cette paire est **validée** (bande de luminance, plancher de chroma, séparation daltonienne, contraste) sur le fond sombre. Toute nouvelle couleur de données doit être revalidée avant usage.
- Monospace pour l'appareil (navigation, codes `MOD.NN`, légendes), serif pour la prose. Identité jamais portée par la couleur seule : étiquettes directes sur les marques.
- Figures : SVG inline autonome dans `src-md/_fragments/`, `<title>` et `<desc>` renseignés, texte des étiquettes en encre (pas en couleur de série), zéro dépendance, zéro requête externe.
- Animations discrètes et **désactivées** sous `prefers-reduced-motion`.

## 6. Ajouter un module, ajouter un cours

- **Module** dans un cours existant `<slug>` : créer `src-md/cours/<slug>/NN-titre.md` au format ci-dessus ; l'ajouter au mouvement voulu dans `cours.json` ; créer `anki/<slug>/NN-titre.txt` (cartes tirées du seul texte du module) et `audio-texte/<slug>/NN.txt` selon le contrat oral ; générer la piste ; `build.py` fait le reste.

- **Cours nouveau** : c'est une opération **déclarative**, `build.py` n'a pas à changer.
  1. Ajouter une entrée dans `cours.json` : `slug`, `titre`, `sous_titre`, `resume`, `statut`, et les `mouvements` (nom + numéros de modules).
  2. Créer `src-md/cours/<slug>/` avec `_cours.md` (page du cours, contenant le marqueur `<!--REGISTRE-->`), les modules `NN-titre.md`, et `bibliographie.md`.
  3. Créer `anki/<slug>/`, `audio-texte/<slug>/`, `audio/<slug>/`.
  4. `python3 build.py && python3 check.py`. Le cours apparaît seul dans la liste de l'accueil et dans `/cours/`.

- **Les URL publiées ne cassent jamais.** Si un chemin doit changer, `build.py` écrit une page de redirection à l'ancienne adresse — voir le dictionnaire `anciennes` en fin de `construire()`, et le test [5] de `check.py` qui vérifie qu'aucune ne manque.

## 7. Vérification avant toute poussée

```bash
python3 build.py && python3 check.py
```

Puis regarder réellement le rendu — bureau **et** mobile (moins de six cents pixels) : la vérification visuelle fait partie de la procédure, pas de la politesse.
