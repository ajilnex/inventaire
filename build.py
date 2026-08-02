#!/usr/bin/env python3
"""Décodage — génération du site depuis src-md/. Python 3 standard, zéro dépendance.

Arborescence produite :
    /                              accueil du site
    /methode.html                  méthode de travail, transversale
    /cours/index.html              la liste des cours
    /cours/<slug>/index.html       la page d'un cours
    /cours/<slug>/NN-titre.html    ses modules
    /cours/<slug>/bibliographie.html

Ajouter un cours = ajouter une entrée dans cours.json et un dossier
src-md/cours/<slug>/ ; ce fichier n'a pas à changer.

Usage : python3 build.py
"""
import hashlib
import html as H
import json
import os
import re
import unicodedata

RACINE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(RACINE, "src-md")
FRAG = os.path.join(SRC, "_fragments")

with open(os.path.join(RACINE, "cours.json"), encoding="utf-8") as fh:
    CONFIG = json.load(fh)
SITE = CONFIG["site"]
BASE = SITE["base"]


def empreinte(*chemins):
    """Empreinte courte du contenu, pour forcer les navigateurs à recharger
    les ressources modifiées sans jamais rendre le cache inutile."""
    h = hashlib.sha256()
    for c in chemins:
        with open(os.path.join(RACINE, c), "rb") as fh:
            h.update(fh.read())
    return h.hexdigest()[:8]


VER = empreinte("assets/style.css", "assets/site.js")

# ---------- conversion markdown -> html ----------

def inline(s: str) -> str:
    s = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", lambda m: '<a href="%s">%s</a>' % (m.group(2).replace(".md", ".html"), m.group(1)), s)
    s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"(?<![\w*])\*([^*]+)\*(?![\w*])", r"<em>\1</em>", s)
    s = re.sub(r"`([^`]+)`", r"<code>\1</code>", s)
    return s


def slug(s: str) -> str:
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def md_vers_html(texte: str) -> str:
    out, i = [], 0
    lignes = texte.split("\n")
    en_liste = False

    def fermer_liste():
        nonlocal en_liste
        if en_liste:
            out.append("</ul>")
            en_liste = False

    while i < len(lignes):
        l = lignes[i]
        strip = l.strip()
        m = re.match(r"^@@FIG:([a-z-]+)@@$", strip)
        if m:
            fermer_liste()
            with open(os.path.join(FRAG, "fig-%s.html" % m.group(1)), encoding="utf-8") as fh:
                out.append(fh.read())
            i += 1
            continue
        if strip.startswith("<!--") or strip.startswith("<"):
            fermer_liste()
            out.append(l)
            i += 1
            continue
        if strip == "---":
            fermer_liste()
            out.append("<hr>")
            i += 1
            continue
        if strip.startswith("### "):
            fermer_liste()
            out.append("<h3>%s</h3>" % inline(strip[4:]))
            i += 1
            continue
        if strip.startswith("## "):
            fermer_liste()
            t = strip[3:]
            ident = "emporter" if t.lower().startswith("ce qu'il faut emporter") else slug(re.sub(r"^\d+\.\s*", "", t))
            out.append('<h2 id="%s">%s</h2>' % (ident, inline(re.sub(r"^\d+\.\s*", "", t))))
            i += 1
            continue
        if strip.startswith("# "):
            i += 1
            continue
        if strip.startswith("> "):
            fermer_liste()
            bloc = []
            while i < len(lignes) and lignes[i].strip().startswith(">"):
                bloc.append(lignes[i].strip().lstrip(">").strip())
                i += 1
            out.append("<blockquote><p>%s</p></blockquote>" % inline(" ".join(b for b in bloc if b)))
            continue
        if strip.startswith("- "):
            if not en_liste:
                out.append("<ul>")
                en_liste = True
            out.append("<li>%s</li>" % inline(strip[2:]))
            i += 1
            continue
        if strip == "":
            fermer_liste()
            i += 1
            continue
        par = [strip]
        i += 1
        while i < len(lignes) and lignes[i].strip() and not re.match(r"^(#|>|- |---$|@@|<)", lignes[i].strip()):
            par.append(lignes[i].strip())
            i += 1
        out.append("<p>%s</p>" % inline(" ".join(par)))
    fermer_liste()
    return "\n".join(out)


# ---------- lecture des sources ----------

def lire_module(chemin):
    with open(chemin, encoding="utf-8") as fh:
        texte = fh.read()
    m = re.search(r"^# (.+)$", texte, re.M)
    titre_brut = m.group(1).strip() if m else os.path.basename(chemin)
    titre = re.sub(r"^(Module \d+|Ouverture)\s+—\s+", "", titre_brut)
    lectures, corps = [], texte
    ml = re.search(r"^# .+?\n+((?:\*\*.+?\n)+)\n*---", texte, re.S | re.M)
    if ml:
        lectures = [l.strip() for l in ml.group(1).strip().split("\n") if l.strip()]
        corps = texte.replace(ml.group(1), "", 1)
    corps = re.sub(r"\*\*(Module suivant|Retour au)\b.*$", "", corps, flags=re.M).rstrip()
    mots = len(re.findall(r"[\wÀ-ÿ']+", texte))
    return {"titre": titre, "titre_brut": titre_brut, "lectures": lectures,
            "corps": corps, "minutes": max(3, round(mots / 200))}


def premiere_phrase(html_corps, defaut):
    m = re.search(r"<p>(.+?)</p>", html_corps, re.S)
    if not m:
        return defaut
    txt = H.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", m.group(1)))).strip()
    return (txt[:152] + "…") if len(txt) > 155 else txt


def duree_mp3(chemin):
    """Durée en minutes. Les pistes sont encodées à débit constant de 64 kbit/s."""
    return max(1, round(os.path.getsize(chemin) * 8 / 64000 / 60))


# ---------- assemblage ----------

def page(gabarit, *, titre, desc, canonique, contenu, racine,
         modcode="", audio="", pied="", filariane="", jsonld=None, courant=""):
    p = gabarit
    for cle, val in [("{{TITLE}}", H.escape(titre, quote=True)), ("{{DESC}}", H.escape(desc, quote=True)),
                     ("{{CANONICAL}}", canonique), ("{{CONTENT}}", contenu), ("{{ROOT}}", racine),
                     ("{{MODCODE}}", modcode), ("{{AUDIO}}", audio), ("{{PIED}}", pied),
                     ("{{FILARIANE}}", filariane), ("{{JSONLD}}", json.dumps(jsonld or {}, ensure_ascii=False)),
                     ("{{VER}}", VER)]:
        p = p.replace(cle, val)
    for nom in ["COURS", "METHODE"]:
        p = p.replace("{{CUR_%s}}" % nom, ' aria-current="page"' if courant == nom else "")
    return p


def bloc_audio(slug_cours, nn, racine):
    chemin = os.path.join(RACINE, "audio", slug_cours, "%s.mp3" % nn)
    if os.path.exists(chemin):
        corps = '<audio controls preload="none" src="%saudio/%s/%s.mp3"></audio>' % (racine, slug_cours, nn)
        etiquette = "Écouter ce module — %d min" % duree_mp3(chemin)
    else:
        corps = '<span class="abs">piste en préparation</span>'
        etiquette = "Piste audio"
    return '<div class="piste"><span class="lab">%s</span>%s</div>' % (etiquette, corps)


def fil(racine, *etapes):
    """Fil d'Ariane : liste de couples (libellé, href ou None pour l'étape courante)."""
    morceaux = []
    for libelle, href in etapes:
        if href:
            morceaux.append('<a href="%s%s">%s</a>' % (racine, href, H.escape(libelle)))
        else:
            morceaux.append('<span aria-current="page">%s</span>' % H.escape(libelle))
    return '<nav class="fil" aria-label="Fil d\'Ariane">%s</nav>' % "<span class=\"sep\">/</span>".join(morceaux)


def construire():
    with open(os.path.join(RACINE, "_template.html"), encoding="utf-8") as fh:
        gabarit = fh.read()
    pages_sitemap = []
    fiches_cours = []   # pour les listes (accueil, /cours/)

    # ================= les cours =================
    for cfg in CONFIG["cours"]:
        sl = cfg["slug"]
        dsrc = os.path.join(SRC, "cours", sl)
        dout = os.path.join(RACINE, "cours", sl)
        os.makedirs(dout, exist_ok=True)
        racine = "../../"
        fichiers = sorted(f for f in os.listdir(dsrc) if re.match(r"^\d\d-.*\.md$", f))
        modules = [(f[:2], f[:-3], lire_module(os.path.join(dsrc, f))) for f in fichiers]
        url_cours = BASE + "cours/%s/" % sl

        # -- modules --
        for idx, (nn, base_nom, mod) in enumerate(modules):
            corps_html = md_vers_html(mod["corps"])
            lect = ""
            if mod["lectures"]:
                lect = '<div class="lectures">%s</div>' % "".join("<p>%s</p>" % inline(l) for l in mod["lectures"])
            contenu = "<h1>%s</h1>\n%s\n%s" % (H.escape(mod["titre"]), bloc_audio(sl, nn, racine), lect + "\n" + corps_html)
            if idx > 0:
                p_nn, p_base, p_mod = modules[idx - 1]
                prev_a = '<a rel="prev" href="%s.html"><span class="k">◀ précédent</span>MOD.%s — %s</a>' % (p_base, p_nn, H.escape(p_mod["titre"]))
            else:
                prev_a = '<a rel="prev" href="index.html"><span class="k">◀ le cours</span>Sommaire d\'%s</a>' % H.escape(cfg["titre"])
            if idx < len(modules) - 1:
                n_nn, n_base, n_mod = modules[idx + 1]
                next_a = '<a rel="next" href="%s.html" style="text-align:right"><span class="k">suivant ▶</span>MOD.%s — %s</a>' % (n_base, n_nn, H.escape(n_mod["titre"]))
            else:
                next_a = '<a rel="next" href="index.html" style="text-align:right"><span class="k">fin ▶</span>Retour au sommaire</a>'
            url = url_cours + base_nom + ".html"
            jl = {"@context": "https://schema.org", "@type": "LearningResource",
                  "name": mod["titre_brut"], "inLanguage": "fr",
                  "isPartOf": {"@type": "Course", "name": cfg["titre"], "url": url_cours},
                  "license": "https://creativecommons.org/licenses/by-sa/4.0/", "url": url}
            htmlp = page(gabarit,
                         titre="%s — %s · %s" % (mod["titre"], cfg["titre"], SITE["nom"]),
                         desc=premiere_phrase(corps_html, cfg["resume"]), canonique=url,
                         contenu=contenu, racine=racine,
                         modcode='<p class="modcode">%d min de lecture · %s</p>' % (mod["minutes"], H.escape(cfg["titre"])),
                         audio="", pied='<nav class="pied">%s%s</nav>' % (prev_a, next_a),
                         filariane=fil(racine, ("Cours", "cours/index.html"),
                                       (cfg["titre"], "cours/%s/index.html" % sl),
                                       ("MOD." + nn, None)),
                         jsonld=jl, courant="COURS")
            with open(os.path.join(dout, base_nom + ".html"), "w", encoding="utf-8") as fh:
                fh.write(htmlp)
            pages_sitemap.append(url)

        # -- registre du cours --
        reg, total_audio = [], 0
        for mvt in cfg["mouvements"]:
            reg.append('<p class="mvt">%s</p><ul class="registre">' % H.escape(mvt["nom"]))
            for nn in mvt["modules"]:
                trouve = [m for m in modules if m[0] == nn]
                if not trouve:
                    continue
                _, base_nom, mod = trouve[0]
                piste = os.path.join(RACINE, "audio", sl, "%s.mp3" % nn)
                badge = ""
                if os.path.exists(piste):
                    d = duree_mp3(piste)
                    total_audio += d
                    badge = '<span class="au" title="piste audio disponible">▶ %d min</span>' % d
                reg.append('<li><a href="%s.html"><span class="n">MOD.%s</span>'
                           '<span class="t">%s</span>%s<span class="dots"></span>'
                           '<span class="len">lire %d min</span></a></li>'
                           % (base_nom, nn, H.escape(mod["titre"]), badge, mod["minutes"]))
            reg.append("</ul>")

        # -- page du cours --
        with open(os.path.join(dsrc, "_cours.md"), encoding="utf-8") as fh:
            corps = md_vers_html(fh.read()).replace("<!--REGISTRE-->", "\n".join(reg))
        jl = {"@context": "https://schema.org", "@type": "Course", "name": cfg["titre"],
              "description": cfg["resume"], "inLanguage": "fr", "isAccessibleForFree": True,
              "license": "https://creativecommons.org/licenses/by-sa/4.0/",
              "provider": {"@type": "Organization", "name": SITE["nom"], "url": BASE},
              "url": url_cours}
        with open(os.path.join(dout, "index.html"), "w", encoding="utf-8") as fh:
            fh.write(page(gabarit, titre="%s — %s · %s" % (cfg["titre"], cfg["sous_titre"], SITE["nom"]),
                          desc=cfg["resume"], canonique=url_cours, contenu=corps, racine=racine,
                          filariane=fil(racine, ("Cours", "cours/index.html"), (cfg["titre"], None)),
                          jsonld=jl, courant="COURS"))
        pages_sitemap.append(url_cours)

        # -- bibliographie du cours --
        chemin_bib = os.path.join(dsrc, "bibliographie.md")
        if os.path.exists(chemin_bib):
            with open(chemin_bib, encoding="utf-8") as fh:
                texte = fh.read()
            m = re.search(r"^# (.+)$", texte, re.M)
            h1 = "<h1>%s</h1>\n" % H.escape(m.group(1)) if m else ""
            url = url_cours + "bibliographie.html"
            with open(os.path.join(dout, "bibliographie.html"), "w", encoding="utf-8") as fh:
                fh.write(page(gabarit, titre="Bibliographie — %s · %s" % (cfg["titre"], SITE["nom"]),
                              desc="Les livres dont le cours %s est l'échafaudage, module par module." % cfg["titre"],
                              canonique=url, contenu=h1 + md_vers_html(texte), racine=racine,
                              filariane=fil(racine, ("Cours", "cours/index.html"),
                                            (cfg["titre"], "cours/%s/index.html" % sl), ("Bibliographie", None)),
                              jsonld={"@context": "https://schema.org", "@type": "WebPage",
                                      "name": "Bibliographie — " + cfg["titre"], "url": url},
                              courant="COURS"))
            pages_sitemap.append(url)

        fiches_cours.append(
            '<li><a href="%s"><span class="n">%s</span><span class="t">%s</span>'
            '<span class="len">%d modules · %d h %02d de cours parlé</span>'
            '<span class="resume">%s</span><span class="entrer">Entrer →</span></a></li>'
            % ("{RACINE}cours/%s/index.html" % sl, H.escape(cfg["titre"]), H.escape(cfg["sous_titre"]),
               len(modules), total_audio // 60, total_audio % 60, H.escape(cfg["resume"])))

    liste_cours = '<ul class="registre cours">%s</ul>' % "".join(fiches_cours)

    # ================= pages du site =================
    simples = [
        ("index", "", "%s — cours ouverts" % SITE["nom"], SITE["accroche"], "", []),
        ("cours", "cours/", "Cours · %s" % SITE["nom"],
         "Les cours publiés : leçons, version parlée, cartes de mémorisation, bibliographie. Gratuits et ouverts.",
         "COURS", [("Cours", None)]),
        ("methode", "", "Méthode · %s" % SITE["nom"],
         "Comment travailler : la lecture, l'écoute, et les cartes à mémorisation espacée.",
         "METHODE", [("Méthode", None)]),
    ]
    for nom, sous_dossier, titre, desc, courant, etapes in simples:
        with open(os.path.join(SRC, nom + ".md"), encoding="utf-8") as fh:
            texte = fh.read()
        m = re.search(r"^# (.+)$", texte, re.M)
        h1 = "<h1>%s</h1>\n" % H.escape(m.group(1)) if m else ""
        racine = "../" if sous_dossier else ""
        corps = md_vers_html(texte).replace("<!--COURS-->", liste_cours.replace("{RACINE}", racine))
        if "<!--PAQUETS-->" in corps:
            paquets = []
            for cfg in CONFIG["cours"]:
                d = os.path.join(RACINE, "anki", cfg["slug"])
                if not os.path.isdir(d):
                    continue
                for f in sorted(os.listdir(d)):
                    if not f.endswith(".txt"):
                        continue
                    with open(os.path.join(d, f), encoding="utf-8") as fh:
                        lignes = fh.read().split("\n")
                    nomp = next((l[6:].strip() for l in lignes if l.startswith("#deck:")), f)
                    n = sum(1 for l in lignes if "\t" in l)
                    paquets.append('<li><a href="%sanki/%s/%s" download><span class="n">%d cartes</span>'
                                   '<span class="t">%s</span><span class="dots"></span>'
                                   '<span class="len">.txt</span></a></li>' % (racine, cfg["slug"], f, n, H.escape(nomp)))
            corps = corps.replace("<!--PAQUETS-->", '<ul class="registre">%s</ul>' % "".join(paquets))
        dossier = os.path.join(RACINE, sous_dossier) if sous_dossier else RACINE
        os.makedirs(dossier, exist_ok=True)
        url = BASE + sous_dossier + ("" if nom in ("index", "cours") else nom + ".html")
        jl = ({"@context": "https://schema.org", "@type": "EducationalOrganization",
               "name": SITE["nom"], "description": SITE["accroche"], "url": BASE}
              if nom == "index" else
              {"@context": "https://schema.org", "@type": "WebPage", "name": titre, "url": url})
        with open(os.path.join(dossier, "index.html" if nom in ("index", "cours") else nom + ".html"),
                  "w", encoding="utf-8") as fh:
            fh.write(page(gabarit, titre=titre, desc=desc, canonique=url, contenu=h1 + corps,
                          racine=racine, filariane=fil(racine, *etapes) if etapes else "",
                          jsonld=jl, courant=courant))
        pages_sitemap.append(url)

    # ================= redirections des anciennes adresses =================
    anciennes = {"bibliographie.html": "cours/inventaire/bibliographie.html"}
    for cfg in CONFIG["cours"]:
        if cfg["slug"] != "inventaire":
            continue
        for f in sorted(os.listdir(os.path.join(SRC, "cours", "inventaire"))):
            if re.match(r"^\d\d-.*\.md$", f):
                anciennes["cours/%s.html" % f[:-3]] = "cours/inventaire/%s.html" % f[:-3]
    for ancienne, nouvelle in anciennes.items():
        chemin = os.path.join(RACINE, ancienne)
        os.makedirs(os.path.dirname(chemin) or RACINE, exist_ok=True)
        profondeur = "../" * ancienne.count("/")
        cible = profondeur + nouvelle
        with open(chemin, "w", encoding="utf-8") as fh:
            fh.write('<!DOCTYPE html><html lang="fr"><head><meta charset="utf-8">'
                     '<title>Page déplacée</title><link rel="canonical" href="%s%s">'
                     '<meta name="robots" content="noindex"><meta http-equiv="refresh" content="0; url=%s">'
                     '</head><body><p>Cette page a été déplacée. <a href="%s">Suivre le nouveau lien</a>.</p>'
                     '</body></html>' % (BASE, nouvelle, cible, cible))

    # ================= sitemap =================
    with open(os.path.join(RACINE, "sitemap.xml"), "w", encoding="utf-8") as fh:
        fh.write('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n')
        for u in sorted(set(pages_sitemap)):
            fh.write("  <url><loc>%s</loc></url>\n" % u)
        fh.write("</urlset>\n")

    print("build : %d cours, %d pages, %d redirections" % (len(CONFIG["cours"]), len(pages_sitemap), len(anciennes)))


if __name__ == "__main__":
    construire()
