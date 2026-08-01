#!/usr/bin/env python3
"""Inventaire — suite de vérifications. Doit rester verte. Usage : python3 check.py"""
import os
import re
import sys

RACINE = os.path.dirname(os.path.abspath(__file__))
ECHECS = []


def erreur(msg):
    ECHECS.append(msg)
    print("  ÉCHEC  " + msg)


def ok(msg):
    print("  ok     " + msg)


def fichiers_html():
    pages = [os.path.join(RACINE, f) for f in ("index.html", "methode.html", "bibliographie.html")]
    dossier = os.path.join(RACINE, "cours")
    if os.path.isdir(dossier):
        pages += [os.path.join(dossier, f) for f in sorted(os.listdir(dossier)) if f.endswith(".html")]
    return [p for p in pages if os.path.exists(p)]


print("[1] pages construites")
pages = fichiers_html()
if len(pages) < 16:
    erreur("%d pages trouvées, 16 attendues (3 + 13 modules)" % len(pages))
else:
    ok("%d pages" % len(pages))

print("[2] chaînes interdites (contexte de fabrication, sources illégitimes)")
INTERDITS = ["_texte", "Bibliothèque céleste", "Anna's Archive", "annas-archive", "z-lib",
             "Module à rédiger", "votre étagère", "@@FIG", "{{", "scratchpad", "aubinrobert"]
for p in pages:
    with open(p, encoding="utf-8") as fh:
        contenu = fh.read()
    for mot in INTERDITS:
        if mot in contenu:
            erreur("%s contient « %s »" % (os.path.basename(p), mot))
ok("balayage terminé") if not ECHECS else None

print("[3] liens et ressources internes")
for p in pages:
    with open(p, encoding="utf-8") as fh:
        contenu = fh.read()
    base = os.path.dirname(p)
    for m in re.finditer(r'(?:href|src)="([^"#]+)"', contenu):
        cible = m.group(1)
        if cible.startswith(("http", "data:", "mailto:")):
            continue
        chemin = os.path.normpath(os.path.join(base, cible))
        if not os.path.exists(chemin):
            erreur("%s → lien mort : %s" % (os.path.basename(p), cible))
ok("liens internes résolus")

print("[4] structure des pages de modules")
for p in pages:
    if os.sep + "cours" + os.sep not in p:
        continue
    with open(p, encoding="utf-8") as fh:
        c = fh.read()
    attendus = [('class="modcode"', "code de module"), ("<h1>", "titre h1"),
                ('class="piste"', "bloc audio"), ('class="pied"', "navigation"),
                ('rel="canonical"', "canonique")]
    if "00-ouverture" not in p:  # l'ouverture se clôt autrement, à dessein
        attendus.append(('id="emporter"', "section emporter"))
    for morceau, nom in attendus:
        if morceau not in c:
            erreur("%s sans %s" % (os.path.basename(p), nom))
ok("structure vérifiée")

print("[5] paquets anki")
dossier = os.path.join(RACINE, "anki")
if os.path.isdir(dossier):
    for f in sorted(os.listdir(dossier)):
        if not f.endswith(".txt"):
            continue
        with open(os.path.join(dossier, f), encoding="utf-8") as fh:
            lignes = fh.read().rstrip("\n").split("\n")
        entetes = [l for l in lignes if l.startswith("#")]
        cartes = [l for l in lignes if l and not l.startswith("#")]
        if not any(l.startswith("#separator:tab") for l in entetes):
            erreur("%s : en-tête separator manquant" % f)
        for i, l in enumerate(cartes, 1):
            if l.count("\t") != 1 or not all(ch.strip() for ch in l.split("\t")):
                erreur("%s carte %d : doit avoir exactement 2 champs non vides" % (f, i))
                break
    ok("paquets balayés")

print("[6] contrat des textes oraux")
dossier = os.path.join(RACINE, "audio-texte")
if os.path.isdir(dossier) and os.listdir(dossier):
    for f in sorted(os.listdir(dossier)):
        if not f.endswith(".txt"):
            continue
        with open(os.path.join(dossier, f), encoding="utf-8") as fh:
            c = fh.read()
        if re.search(r"[0-9#*_|\[\]{}<>@]", c):
            car = re.search(r"[0-9#*_|\[\]{}<>@]", c).group(0)
            erreur("audio-texte/%s : caractère proscrit « %s »" % (f, car))
        if "http" in c:
            erreur("audio-texte/%s : contient une URL" % f)
        if len(c) > 40000:
            erreur("audio-texte/%s : %d caractères (max 40000)" % (f, len(c)))
    ok("contrat oral vérifié")
else:
    print("  —      pas encore de textes oraux (toléré)")

print("[7] sitemap")
chemin = os.path.join(RACINE, "sitemap.xml")
if not os.path.exists(chemin):
    erreur("sitemap.xml absent")
else:
    with open(chemin, encoding="utf-8") as fh:
        sm = fh.read()
    if sm.count("<loc>") != len(pages):
        erreur("sitemap : %d entrées pour %d pages" % (sm.count("<loc>"), len(pages)))
    else:
        ok("%d entrées" % sm.count("<loc>"))

print()
if ECHECS:
    print("ROUGE — %d échec(s)" % len(ECHECS))
    sys.exit(1)
print("VERT — tout passe")
