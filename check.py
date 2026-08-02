#!/usr/bin/env python3
"""Décodage — suite de vérifications. Doit rester verte. Usage : python3 check.py"""
import json
import os
import re
import sys

RACINE = os.path.dirname(os.path.abspath(__file__))
ECHECS = []
with open(os.path.join(RACINE, "cours.json"), encoding="utf-8") as fh:
    CONFIG = json.load(fh)


def erreur(msg):
    ECHECS.append(msg)
    print("  ÉCHEC  " + msg)


def ok(msg):
    print("  ok     " + msg)


def pages_generees():
    """Toutes les pages du site, hors redirections."""
    trouvees = [os.path.join(RACINE, "index.html"),
                os.path.join(RACINE, "methode.html"),
                os.path.join(RACINE, "cours", "index.html")]
    for cfg in CONFIG["cours"]:
        d = os.path.join(RACINE, "cours", cfg["slug"])
        if os.path.isdir(d):
            trouvees += [os.path.join(d, f) for f in sorted(os.listdir(d)) if f.endswith(".html")]
    return [p for p in trouvees if os.path.exists(p)]


def est_redirection(chemin):
    with open(chemin, encoding="utf-8") as fh:
        return "http-equiv=\"refresh\"" in fh.read(400)


print("[1] pages construites")
pages = pages_generees()
attendu = 3 + sum(len(os.listdir(os.path.join(RACINE, "src-md", "cours", c["slug"]))) for c in CONFIG["cours"])
if len(pages) < 17:
    erreur("%d pages seulement" % len(pages))
else:
    ok("%d pages, %d cours" % (len(pages), len(CONFIG["cours"])))

print("[2] chaînes interdites")
INTERDITS = ["_texte", "Bibliothèque céleste", "Anna's Archive", "annas-archive", "z-lib",
             "Module à rédiger", "votre étagère", "@@FIG", "{{", "{RACINE}", "scratchpad", "aubinrobert"]
for p in pages:
    with open(p, encoding="utf-8") as fh:
        contenu = fh.read()
    for mot in INTERDITS:
        if mot in contenu:
            erreur("%s contient « %s »" % (os.path.relpath(p, RACINE), mot))
if not ECHECS:
    ok("balayage terminé")

print("[3] liens et ressources internes")
for p in pages:
    with open(p, encoding="utf-8") as fh:
        contenu = fh.read()
    base = os.path.dirname(p)
    for m in re.finditer(r'(?:href|src)="([^"#]+)"', contenu):
        cible = m.group(1)
        if cible.startswith(("http", "data:", "mailto:")):
            continue
        cible = cible.split("?", 1)[0]          # empreinte de version : ?v=…
        if not cible:
            continue
        chemin = os.path.normpath(os.path.join(base, cible))
        if os.path.isdir(chemin):
            chemin = os.path.join(chemin, "index.html")
        if not os.path.exists(chemin):
            erreur("%s → lien mort : %s" % (os.path.relpath(p, RACINE), cible))
ok("liens internes résolus")

print("[4] structure des pages de modules")
for cfg in CONFIG["cours"]:
    d = os.path.join(RACINE, "cours", cfg["slug"])
    for f in sorted(os.listdir(d)):
        if not re.match(r"^\d\d-.*\.html$", f):
            continue
        with open(os.path.join(d, f), encoding="utf-8") as fh:
            c = fh.read()
        attendus = [('class="modcode"', "code de module"), ("<h1>", "titre"),
                    ('class="piste"', "bloc audio"), ('class="pied"', "navigation"),
                    ('class="fil"', "fil d'Ariane"), ('rel="canonical"', "canonique")]
        if not f.startswith("00-"):
            attendus.append(('id="emporter"', "section emporter"))
        for morceau, nom in attendus:
            if morceau not in c:
                erreur("%s/%s sans %s" % (cfg["slug"], f, nom))
        # l'audio doit précéder le corps du module
        if 'class="piste"' in c and 'class="lectures"' in c:
            if c.index('class="piste"') > c.index('class="lectures"'):
                erreur("%s/%s : l'audio n'est pas en tête" % (cfg["slug"], f))
ok("structure vérifiée")

print("[5] redirections des anciennes adresses")
red = [os.path.join(RACINE, "bibliographie.html")]
red += [os.path.join(RACINE, "cours", f) for f in os.listdir(os.path.join(RACINE, "cours"))
        if re.match(r"^\d\d-.*\.html$", f)]
manquantes = [r for r in red if not os.path.exists(r)]
if manquantes:
    erreur("%d redirection(s) manquante(s)" % len(manquantes))
else:
    for r in red:
        if not est_redirection(r):
            erreur("%s n'est pas une redirection" % os.path.relpath(r, RACINE))
    ok("%d anciennes adresses redirigées" % len(red))

print("[6] paquets anki")
for cfg in CONFIG["cours"]:
    d = os.path.join(RACINE, "anki", cfg["slug"])
    if not os.path.isdir(d):
        erreur("anki/%s absent" % cfg["slug"])
        continue
    for f in sorted(os.listdir(d)):
        if not f.endswith(".txt"):
            continue
        with open(os.path.join(d, f), encoding="utf-8") as fh:
            lignes = fh.read().rstrip("\n").split("\n")
        if not any(l.startswith("#separator:tab") for l in lignes if l.startswith("#")):
            erreur("%s : en-tête separator manquant" % f)
        for i, l in enumerate([l for l in lignes if l and not l.startswith("#")], 1):
            if l.count("\t") != 1 or not all(ch.strip() for ch in l.split("\t")):
                erreur("%s carte %d : 2 champs non vides attendus" % (f, i))
                break
ok("paquets balayés")

print("[7] contrat des textes oraux")
vus = 0
for cfg in CONFIG["cours"]:
    d = os.path.join(RACINE, "audio-texte", cfg["slug"])
    if not os.path.isdir(d):
        continue
    for f in sorted(os.listdir(d)):
        if not f.endswith(".txt"):
            continue
        vus += 1
        with open(os.path.join(d, f), encoding="utf-8") as fh:
            c = fh.read()
        m = re.search(r"[0-9#*_|\[\]{}<>@]", c)
        if m:
            erreur("audio-texte/%s/%s : caractère proscrit « %s »" % (cfg["slug"], f, m.group(0)))
        if "http" in c:
            erreur("audio-texte/%s/%s : contient une URL" % (cfg["slug"], f))
        if len(c) > 40000:
            erreur("audio-texte/%s/%s : %d caractères" % (cfg["slug"], f, len(c)))
ok("%d textes oraux conformes" % vus) if vus else print("  —      pas de textes oraux")

print("[8] pistes audio")
total = 0
for cfg in CONFIG["cours"]:
    d = os.path.join(RACINE, "audio", cfg["slug"])
    if not os.path.isdir(d):
        continue
    for f in sorted(os.listdir(d)):
        if not f.endswith(".mp3"):
            continue
        chemin = os.path.join(d, f)
        taille = os.path.getsize(chemin)
        total += taille
        with open(chemin, "rb") as fh:
            tete = fh.read(3)
        if tete != b"ID3" and tete[:2] not in (b"\xff\xfb", b"\xff\xf3"):
            erreur("audio/%s/%s : en-tête MP3 invalide" % (cfg["slug"], f))
        if taille < 200000:
            erreur("audio/%s/%s : piste probablement tronquée" % (cfg["slug"], f))
        if not os.path.exists(os.path.join(RACINE, "audio-texte", cfg["slug"], f[:-4] + ".txt")):
            erreur("audio/%s/%s : texte source absent" % (cfg["slug"], f))
if total:
    if total > 400 * 1024 * 1024:
        erreur("audio : %d Mo, au-delà du raisonnable pour Pages" % (total // 1048576))
    else:
        ok("%d Mo, ≈ %d min" % (total // 1048576, total * 8 / 64000 / 60))

print("[9] image de partage")
with open(os.path.join(RACINE, "_template.html"), encoding="utf-8") as fh:
    og = re.search(r'og:image" content="([^"]+)"', fh.read())
if og:
    nom = og.group(1).rsplit("/", 1)[-1]
    if not os.path.exists(os.path.join(RACINE, "assets", nom)):
        erreur("assets/%s référencé par og:image mais absent" % nom)
    else:
        ok("assets/%s présent" % nom)

print("[10] sitemap")
chemin = os.path.join(RACINE, "sitemap.xml")
if not os.path.exists(chemin):
    erreur("sitemap.xml absent")
else:
    with open(chemin, encoding="utf-8") as fh:
        sm = fh.read()
    n = sm.count("<loc>")
    if n != len(pages):
        erreur("sitemap : %d entrées pour %d pages" % (n, len(pages)))
    elif "cours/inventaire/" not in sm:
        erreur("sitemap : le cours n'y figure pas")
    else:
        ok("%d entrées" % n)

print()
if ECHECS:
    print("ROUGE — %d échec(s)" % len(ECHECS))
    sys.exit(1)
print("VERT — tout passe")
