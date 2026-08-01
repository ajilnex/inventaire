#!/usr/bin/env python3
"""Inventaire — génération des pistes audio depuis audio-texte/.
La clé API ElevenLabs est lue dans ~/.config/elevenlabs/key (jamais dans le dépôt).
Usage : python3 generer_audio.py [NN …]   (sans argument : toutes les pistes manquantes)"""
import json
import os
import sys
import urllib.request

RACINE = os.path.dirname(os.path.abspath(__file__))
VOIX = "ucMmKRQbfDEYyb2IIGax"        # Aurore — française
MODELE = "eleven_turbo_v2_5"          # un demi-crédit par caractère
URL = "https://api.elevenlabs.io/v1/text-to-speech/%s?output_format=mp3_44100_128" % VOIX


def cle():
    chemin = os.path.expanduser("~/.config/elevenlabs/key")
    if not os.path.exists(chemin):
        sys.exit("Clé absente : " + chemin)
    with open(chemin) as fh:
        return fh.read().strip()


def generer(nn, k):
    src = os.path.join(RACINE, "audio-texte", nn + ".txt")
    dst = os.path.join(RACINE, "audio", nn + ".mp3")
    with open(src, encoding="utf-8") as fh:
        texte = fh.read().strip()
    if len(texte) > 40000:
        sys.exit("%s : %d caractères, contrat dépassé" % (src, len(texte)))
    corps = json.dumps({"text": texte, "model_id": MODELE,
                        "voice_settings": {"stability": 0.5, "similarity_boost": 0.75}}).encode()
    req = urllib.request.Request(URL, data=corps, method="POST",
                                 headers={"xi-api-key": k, "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=600) as rep:
        donnees = rep.read()
    if len(donnees) < 10000 or donnees[:2] not in (b"ID", b"\xff\xfb", b"\xff\xf3"):
        sys.exit("%s : réponse suspecte (%d octets) — %s" % (nn, len(donnees), donnees[:200]))
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    with open(dst, "wb") as fh:
        fh.write(donnees)
    print("  %s.mp3 — %d caractères → %d Ko (≈ %d crédits)" % (nn, len(texte), len(donnees) // 1024, len(texte) // 2))
    return len(texte)


def main():
    k = cle()
    dossier = os.path.join(RACINE, "audio-texte")
    voulues = sys.argv[1:] or sorted(f[:-4] for f in os.listdir(dossier) if f.endswith(".txt"))
    total = 0
    for nn in voulues:
        if os.path.exists(os.path.join(RACINE, "audio", nn + ".mp3")):
            print("  %s.mp3 existe — passé (supprimer le fichier pour régénérer)" % nn)
            continue
        total += generer(nn, k)
    print("total : %d caractères, ≈ %d crédits consommés" % (total, total // 2))


if __name__ == "__main__":
    main()
