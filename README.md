# IPTV Azure

Application IPTV Windows haut de gamme — Xtream API + M3U, interface Azure, lecteur VLC integre.

## Fonctionnalites

- Connexion Xtream API (serveur + utilisateur + mot de passe)
- Chargement playlist M3U (URL ou fichier local)
- Live TV, VOD (Films), Series
- Favoris (clic droit sur chaque element)
- Reprise de lecture automatique (point rouge dans la liste)
- Recherche en temps reel
- Categories avec filtrage
- Gestion de playlists sauvegardees
- Lecteur VLC integre (play/pause, volume, progression)
- Plein ecran : touche `F` pour entrer, `ESC` pour sortir
- Raccourcis clavier : `Space` pause, `←→` ±10s, `↑↓` volume
- Theme sombre premium bleu Azure

## Stack technique

- Python 3.11
- PyQt5
- python-vlc
- PyInstaller (one-dir windowed)
- Inno Setup
- GitHub Actions (build automatique)

## Build

Le build se lance automatiquement via GitHub Actions a chaque push sur `main`.

Pour recuperer l'installateur :
1. Va sur l'onglet **Actions** de ce depot
2. Clique sur le dernier workflow reussi
3. Telecharge l'artifact **IPTV-Azure-Setup**
4. Lance `IPTV-Azure-Setup.exe`

## Installation manuelle (developpement)

```bash
pip install -r requirements.txt
python main.py
```

## Credits

IPTV Azure v1.0.0 — Propulse par Python, PyQt5 & VLC
