#!/usr/bin/env python3
"""Inventaire — génération du site depuis src-md/. Python 3 standard, zéro dépendance.
Usage : python3 build.py"""
import html as H
import json
import os
import re
import unicodedata

RACINE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(RACINE, "src-md")
FRAG = os.path.join(SRC, "_fragments")
BASE = "https://ajilnex.github.io/inventaire/"

MOUVEMENTS = [
    ("Ouverture", ["00"]),
    ("I. Le monde plein", ["01", "02", "03", "04", "05", "06"]),
    ("II. La rupture", ["07", "08", "09", "10"]),
    ("III. Comment on sait", ["11", "12"]),
]

# ---------- conversion markdown -> html (adaptée au corpus du cours) ----------

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
            chemin = os.path.join(FRAG, "fig-%s.html" % m.group(1))
            with open(chemin, encoding="utf-8") as fh:
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
            continue  # le h1 est géré par la page
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
        # paragraphe (agrège les lignes contiguës)
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
    # bloc lectures : lignes **Mot** : … avant le premier ---
    lectures = []
    corps = texte
    ml = re.search(r"^# .+?\n+((?:\*\*.+?\n)+)\n*---", texte, re.S | re.M)
    if ml:
        lectures = [l.strip() for l in ml.group(1).strip().split("\n") if l.strip()]
        corps = texte.replace(ml.group(1), "", 1)
    # retirer la ligne « Module suivant / Retour au »
    corps = re.sub(r"\*\*(Module suivant|Retour au)\b.*$", "", corps, flags=re.M).rstrip()
    mots = len(re.findall(r"[\wÀ-ÿ']+", texte))
    return {"titre": titre, "titre_brut": titre_brut, "lectures": lectures,
            "corps": corps, "minutes": max(3, round(mots / 200))}


def premiere_phrase(html_corps):
    m = re.search(r"<p>(.+?)</p>", html_corps, re.S)
    if not m:
        return "Cours d'introduction à l'économie politique historique."
    txt = re.sub(r"<[^>]+>", "", m.group(1))
    txt = H.unescape(re.sub(r"\s+", " ", txt)).strip()
    return (txt[:152] + "…") if len(txt) > 155 else txt


# ---------- assemblage ----------

def page(gabarit, *, titre, desc, canonique, contenu, racine, modcode="", audio="", pied="", jsonld=None, courant=""):
    p = gabarit
    for cle, val in [("{{TITLE}}", H.escape(titre, quote=True)), ("{{DESC}}", H.escape(desc, quote=True)),
                     ("{{CANONICAL}}", canonique), ("{{CONTENT}}", contenu), ("{{ROOT}}", racine),
                     ("{{MODCODE}}", modcode), ("{{AUDIO}}", audio), ("{{PIED}}", pied),
                     ("{{JSONLD}}", json.dumps(jsonld or {}, ensure_ascii=False))]:
        p = p.replace(cle, val)
    for nom in ["INDEX", "METHODE", "BIBLIO"]:
        p = p.replace("{{CUR_%s}}" % nom, ' aria-current="page"' if courant == nom else "")
    return p


def duree_mp3(chemin):
    """Durée en minutes. Les pistes sont encodées à débit constant de 64 kbit/s."""
    return max(1, round(os.path.getsize(chemin) * 8 / 64000 / 60))


def bloc_audio(nn, racine):
    chemin = os.path.join(RACINE, "audio", "%s.mp3" % nn)
    if os.path.exists(chemin):
        corps = '<audio controls preload="none" src="%saudio/%s.mp3"></audio>' % (racine, nn)
        etiquette = "Écouter ce module — %d min" % duree_mp3(chemin)
    else:
        corps = '<span class="abs">piste en préparation</span>'
        etiquette = "Piste audio — MOD.%s" % nn
    return ('<div class="piste"><span class="lab">%s</span>%s</div>' % (etiquette, corps))


def construire():
    with open(os.path.join(RACINE, "_template.html"), encoding="utf-8") as fh:
        gabarit = fh.read()
    os.makedirs(os.path.join(RACINE, "cours"), exist_ok=True)

    fichiers = sorted(f for f in os.listdir(SRC) if re.match(r"^\d\d-.*\.md$", f))
    modules = []
    for f in fichiers:
        nn = f[:2]
        modules.append((nn, f[:-3], lire_module(os.path.join(SRC, f))))

    pages_sitemap = []

    # -- pages de modules --
    for idx, (nn, base_nom, mod) in enumerate(modules):
        corps_html = md_vers_html(mod["corps"])
        lect = ""
        if mod["lectures"]:
            lect = '<div class="lectures">%s</div>' % "".join("<p>%s</p>" % inline(l) for l in mod["lectures"])
        contenu = "<h1>%s</h1>\n%s\n%s\n%s" % (H.escape(mod["titre"]), bloc_audio(nn, "../"), lect, corps_html)
        prev_a = next_a = ""
        if idx > 0:
            p_nn, p_base, p_mod = modules[idx - 1]
            prev_a = '<a rel="prev" href="%s.html"><span class="k">◀ précédent</span>MOD.%s — %s</a>' % (p_base, p_nn, H.escape(p_mod["titre"]))
        else:
            prev_a = '<a rel="prev" href="../index.html"><span class="k">◀ registre</span>Sommaire du cours</a>'
        if idx < len(modules) - 1:
            n_nn, n_base, n_mod = modules[idx + 1]
            next_a = '<a rel="next" href="%s.html" style="text-align:right"><span class="k">suivant ▶</span>MOD.%s — %s</a>' % (n_base, n_nn, H.escape(n_mod["titre"]))
        else:
            next_a = '<a rel="next" href="../index.html" style="text-align:right"><span class="k">fin ▶</span>Retour au registre</a>'
        pied = '<nav class="pied">%s%s</nav>' % (prev_a, next_a)
        url = BASE + "cours/%s.html" % base_nom
        jl = {"@context": "https://schema.org", "@type": "LearningResource",
              "name": mod["titre_brut"], "inLanguage": "fr",
              "isPartOf": {"@type": "Course", "name": "Inventaire — économie politique historique", "url": BASE},
              "license": "https://creativecommons.org/licenses/by-sa/4.0/", "url": url}
        htmlp = page(gabarit, titre="MOD.%s — %s · Inventaire" % (nn, mod["titre"]),
                     desc=premiere_phrase(corps_html), canonique=url, contenu=contenu, racine="../",
                     modcode='<p class="modcode">Inventaire · MOD.%s · %d min de lecture · texte &amp; audio</p>' % (nn, mod["minutes"]),
                     audio="", pied=pied, jsonld=jl)
        with open(os.path.join(RACINE, "cours", base_nom + ".html"), "w", encoding="utf-8") as fh:
            fh.write(htmlp)
        pages_sitemap.append(url)

    # -- registre pour l'accueil --
    reg = []
    for mvt, nns in MOUVEMENTS:
        reg.append('<p class="mvt">%s</p>' % H.escape(mvt))
        reg.append('<ul class="registre">')
        for nn in nns:
            trouve = [m for m in modules if m[0] == nn]
            if not trouve:
                continue
            _, base_nom, mod = trouve[0]
            piste = os.path.join(RACINE, "audio", "%s.mp3" % nn)
            badge = ('<span class="au" title="piste audio disponible">▶ %d min</span>' % duree_mp3(piste)) if os.path.exists(piste) else ""
            reg.append('<li><a href="cours/%s.html"><span class="n">MOD.%s</span>'
                       '<span class="t">%s</span>%s<span class="dots"></span>'
                       '<span class="len">lire %d min</span></a></li>' % (base_nom, nn, H.escape(mod["titre"]), badge, mod["minutes"]))
        reg.append("</ul>")
    registre = "\n".join(reg)

    # -- pages simples --
    simples = {
        "index": ("Inventaire — cours d'économie politique historique",
                  "Qui prend le surplus, comment, au nom de quoi ? Un cours d'introduction gratuit : douze modules, audio, cartes de mémorisation. Sans prérequis.",
                  "INDEX"),
        "methode": ("Méthode & cartes · Inventaire",
                    "Comment travailler avec le cours : la lecture, l'audio, et les paquets de cartes à mémorisation espacée (Anki).",
                    "METHODE"),
        "bibliographie": ("Bibliographie · Inventaire",
                          "Les livres dont le cours est l'échafaudage, module par module, avec leurs éditions et traductions françaises.",
                          "BIBLIO"),
    }
    for nom, (titre, desc, cur) in simples.items():
        with open(os.path.join(SRC, nom + ".md"), encoding="utf-8") as fh:
            texte = fh.read()
        m = re.search(r"^# (.+)$", texte, re.M)
        h1 = "<h1>%s</h1>\n" % H.escape(m.group(1)) if m else ""
        corps = md_vers_html(texte)
        corps = corps.replace("<!--REGISTRE-->", registre)
        if "<!--PAQUETS-->" in corps:
            paquets = []
            dossier = os.path.join(RACINE, "anki")
            if os.path.isdir(dossier):
                for f in sorted(os.listdir(dossier)):
                    if not f.endswith(".txt"):
                        continue
                    chemin = os.path.join(dossier, f)
                    with open(chemin, encoding="utf-8") as fh:
                        lignes = fh.read().split("\n")
                    nomp = next((l[6:].strip() for l in lignes if l.startswith("#deck:")), f)
                    n = sum(1 for l in lignes if "\t" in l)
                    paquets.append('<li><a href="anki/%s" download><span class="n">%d cartes</span>'
                                   '<span class="t">%s</span><span class="dots"></span>'
                                   '<span class="len">.txt</span></a></li>' % (f, n, H.escape(nomp)))
            corps = corps.replace("<!--PAQUETS-->",
                                  '<ul class="registre">%s</ul>' % "".join(paquets) if paquets
                                  else "<p><em>Les paquets arrivent — le premier est en préparation.</em></p>")
        url = BASE if nom == "index" else BASE + nom + ".html"
        jl = {"@context": "https://schema.org", "@type": "Course",
              "name": "Inventaire — cours d'introduction à l'économie politique historique",
              "description": simples["index"][1], "inLanguage": "fr", "isAccessibleForFree": True,
              "license": "https://creativecommons.org/licenses/by-sa/4.0/",
              "provider": {"@type": "Person", "name": "Inventaire"}, "url": BASE} if nom == "index" else \
             {"@context": "https://schema.org", "@type": "WebPage", "name": titre, "inLanguage": "fr", "url": url}
        htmlp = page(gabarit, titre=titre, desc=desc, canonique=url, contenu=h1 + corps,
                     racine="", pied="", jsonld=jl, courant=cur)
        with open(os.path.join(RACINE, nom + ".html"), "w", encoding="utf-8") as fh:
            fh.write(htmlp)
        pages_sitemap.append(url)

    # -- sitemap --
    with open(os.path.join(RACINE, "sitemap.xml"), "w", encoding="utf-8") as fh:
        fh.write('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n')
        for u in sorted(set(pages_sitemap)):
            fh.write("  <url><loc>%s</loc></url>\n" % u)
        fh.write("</urlset>\n")

    print("build : %d modules, %d pages, sitemap ok" % (len(modules), len(pages_sitemap)))


if __name__ == "__main__":
    construire()
