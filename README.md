# QuiziFy – Générateur Automatique de Shorts Quiz sur YouTube !

**QuiziFy** est un programme Python autonome qui crée des Shorts de quiz, puis les **publie automatiquement sur YouTube**.  
Idéal pour automatiser une chaîne de quiz !

---

## Fonctionnalités

- Génération automatique de quiz via **ChatGPT** (API OpenAI)
- Synthèse vocale avec voix TikTok
- Intégration de gameplay et d’arrière-plans vidéos
- Compte à rebours animé pour chaque question
- Musiques et effets sonores personnalisés
- Upload automatique sur YouTube via l'API
- Boucle infinie : 1 vidéo toutes les heures

---

## Structure du projet

```
QuiziFy/
│
├── programmes/
│   ├── main.py             # Script principal (génère + publie les vidéos)
│   ├── reload_token.py     # Réinitialise les tokens d'accès YouTube
│   ├── requirements.txt    # Les modules utilisés
├── outis/
│   ├── youtubeAPI/         # fLes fichiers API pour YouTube (.json et .pickle)
│   ├── font/               # La police
│   ├── gameplay/           # Les clips de gameplay
│   ├── background_video/   # Les vidéos de fond
│   ├── audio/              # Les effets sonores (bip et musique)
│   ├── config.txt          # Contient le nombre de vidéos créées et est utilisé pour les noms des vidéos (vidéo 1 = 1.mp4)
│   ├── constantes.json     # Les variables (API OpenAI etc...)
│   ├── themes.txt          # Les thèmes des quiz qui pourront être utilisés sont indiqués ici.
├── shorts/                 # Les vidéos générées automatiquement seront ici (mais supprimées après l'upload sur YouTube)
```

---

## Installation

1. **Pré-requis** :
   - Python 3.9+
   - `ffmpeg` installé
   - Clé(s) API OpenAI
   - Credentials Google pour l'API YouTube

2. **Installation des dépendances** :
   ```bash
   pip install -r requirements.txt
   ```

4. **Configuration** :
   - Remplir `outis/constantes.json` avec vos chemins, clés API, sons, etc.
   - Lancer `reload_token.py` pour authentifier vos comptes YouTube

5. **Lancer le programme** :
   ```bash
   py main.py
   ```
   
## Licence

Projet personnel – libre d’utilisation et de modification.

---

## 👤 Auteur

Créé par **[NatCode](https://www.youtube.com/@NatCode171)**  
Chaîne dédiée au codage, à l'automatisation et à la créativité numérique.
