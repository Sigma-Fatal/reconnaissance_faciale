# 🎯 Reconnaissance Faciale Pro

Application de reconnaissance faciale en temps réel avec interface graphique moderne, développée avec **Python**, **OpenCV**, **dlib** et **CustomTkinter**.

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![License](https://img.shields.io/badge/License-MIT-green)
![Status](https://img.shields.io/badge/Status-Production--Ready-brightgreen)

---

## ✨ Fonctionnalités

| Fonctionnalité | Description |
|----------------|-------------|
| 📷 **Reconnaissance en temps réel** | Détection et identification instantanée via webcam |
| 🎥 **Multi-caméras** | Bascule entre caméra intégrée et caméras USB (ex: Logitech C930e) |
| ➕ **Ajout de visage en direct** | Enregistrement de nouvelles personnes avec 3 captures automatiques |
| 🎙️ **Synthèse vocale** | Annonce vocale "Bonjour [Nom]" lors d'une reconnaissance |
| 💡 **Alerte visuelle** | Flash vert (reconnu) ou rouge (inconnu) sur le flux vidéo |
| 📊 **Tableau de bord** | Statistiques en temps réel (top personnes, distribution horaire) |
| 📈 **Export CSV** | Historique complet des reconnaissances |
| 📧 **Notifications email** | Alerte email lors de la détection d'une personne |
| 📸 **Capture photo** | Sauvegarde automatique avec nom et horodatage |
| 🌙 **Interface moderne** | Thème sombre avec CustomTkinter |

---

## 🖼️ Aperçu

```
┌─────────────────────────────────────────────────────────┐
│  📷 Caméra  |  📊 Statistiques                          │
├──────────────────────────────────┬──────────────────────┤
│                                  │  🎯 CONTRÔLES        │
│                                  │  ▶ DÉMARRER          │
│      [FLUX VIDÉO WEBCAM]         │  🔄 Changer 📸 Capture│
│                                  │  👤 Delmas (95.2%)    │
│      ┌──────────────┐            │  ████████████░░ 95%   │
│      │ 👤 Delmas    │            │  ⚙️ Seuil: 0.50       │
│      │    (95.2%)   │            │  ☑ Annonce vocale     │
│      └──────────────┘            │  ☑ Alerte flash       │
│                                  │  📋 3 personnes       │
│                                  │  ❌ QUITTER           │
└──────────────────────────────────┴──────────────────────┘
```

---

## 🚀 Installation

### Prérequis système (Ubuntu/Debian)

```bash
sudo apt update
sudo apt install -y build-essential cmake
sudo apt install -y libopenblas-dev liblapack-dev
sudo apt install -y libx11-dev libgtk-3-dev
sudo apt install -y libboost-all-dev
sudo apt install -y python3-dev python3-tk
sudo apt install -y libv4l-dev
```

### Installation du projet

```bash
# 1. Cloner le dépôt
git clone https://github.com/Sigma-Fatal/reconnaissance_faciale.git
cd reconnaissance_faciale

# 2. Créer l'environnement virtuel
python3 -m venv .venv
source .venv/bin/activate  # Linux/Mac
# ou
.venv\Scripts\activate     # Windows

# 3. Installer les dépendances
pip install --upgrade pip
pip install dlib
pip install -r requirements.txt
```

---

## 📁 Structure du projet

```
reconnaissance_faciale/
├── data/
│   ├── images_reference/       # Photos des personnes connues
│   │   ├── delmas.png
│   │   └── elon_musk.webp
│   ├── encodages/              # Encodages générés automatiquement
│   │   └── encodings.pkl
│   ├── captures/               # Photos capturées via l'interface
│   └── exports/                # Exports CSV de l'historique
│
├── src/
│   ├── __init__.py
│   ├── encode_faces.py         # Script d'encodage des visages
│   ├── gui_app.py              # Interface graphique principale
│   └── recognition_engine.py   # Moteur de reconnaissance (optionnel)
│
├── .venv/                      # Environnement virtuel
├── requirements.txt
├── README.md
└── .gitignore
```

---

## 🎮 Utilisation

### Étape 1 : Ajouter des photos de référence

Placez une photo par personne dans `data/images_reference/`.

**Règles importantes :**
- ✅ Une seule personne par photo
- ✅ Visage bien visible et éclairé
- ✅ Nom du fichier = nom de la personne
- ✅ Formats : JPG, PNG, BMP, WebP

```
data/images_reference/
├── delmas.png          → personne "delmas"
├── elon_musk.webp      → personne "elon_musk"
└── alice.jpg           → personne "alice"
```

### Étape 2 : Générer les encodages

```bash
python src/encode_faces.py
```

Sortie attendue :
```
📁 3 image(s) trouvée(s)
🔄 Début de l'encodage des visages...
🔍 Analyse : delmas.png → 'delmas'
   ✅ Encodé avec succès
💾 Encodages sauvegardés dans : data/encodages/encodings.pkl
```

### Étape 3 : Lancer l'application

```bash
python src/gui_app.py
```

---

## 🎛️ Guide d'utilisation de l'interface

### Onglet "📷 Caméra"

| Bouton | Action |
|--------|--------|
| **▶ DÉMARRER** | Active la webcam et lance la reconnaissance |
| **🔄 Changer** | Bascule entre les caméras disponibles |
| **📸 Capture** | Sauvegarde une photo nommée automatiquement |
| **🎯 Ajouter** | Enregistre un nouveau visage (3 captures) |
| **📊 CSV** | Exporte l'historique des reconnaissances |
| **🗑️ RAZ** | Réinitialise l'historique |

### Onglet "📊 Statistiques"

- **🏆 Top personnes** : Classement des détections
- **📈 Stats globales** : Nombre total, confiance moyenne
- **🕐 Distribution horaire** : Répartition par tranches de 6h

---

## ⚙️ Configuration

### Seuil de reconnaissance

Modifiable via le **slider** dans l'interface ou dans le code :

```python
self.seuil_reconnaissance = 0.5  # 0.3 (strict) à 0.7 (tolérant)
```

### Notifications email

Configurez vos identifiants dans `src/gui_app.py` :

```python
EMAIL_CONFIG = {
    "smtp_server": "smtp.gmail.com",
    "smtp_port": 587,
    "email_from": "votre.email@gmail.com",
    "email_password": "mot_de_passe_application",
    "email_to": "destinataire@example.com",
    "notifications_active": False,
}
```

> 💡 Pour Gmail, générez un **mot de passe d'application** dans les paramètres de sécurité de votre compte.

---

## 🧪 Vérification de l'installation

Créez un fichier `test_imports.py` à la racine :

```python
import cv2
import face_recognition
import dlib
import customtkinter
from PIL import Image
import numpy as np

print("✅ Toutes les dépendances sont correctement installées !")
```

Puis exécutez :
```bash
python test_imports.py
```

---

## 🐛 Dépannage

### Erreur `ModuleNotFoundError: No module named 'tkinter'`

```bash
sudo apt install python3-tk
```

### Erreur `list index out of range`

Vérifiez que les encodages sont bien chargés :
```bash
ls -la data/encodages/
```

### Erreur `Please install face_recognition_models`

```bash
pip uninstall face-recognition face-recognition-models -y
pip install face-recognition==1.3.0 face-recognition-models==0.3.0
```

### La caméra ne s'ouvre pas

```bash
# Vérifier les caméras disponibles
ls -la /dev/video*
v4l2-ctl --list-devices

# Tester avec ffplay
ffplay /dev/video0
```

### Le cadre clignote

Le système conserve le dernier résultat pendant 3 frames pour éviter ce problème. Vérifiez `skip_frames` dans le code.

---

## 🤝 Contribution

Les contributions sont les bienvenues ! N'hésitez pas à :

1. Fork le projet
2. Créer une branche (`git checkout -b feature/AmazingFeature`)
3. Commit vos changements (`git commit -m 'Add some AmazingFeature'`)
4. Push sur la branche (`git push origin feature/AmazingFeature`)
5. Ouvrir une Pull Request

---

## 📄 Licence

Ce projet est sous licence **MIT**. Voir le fichier `LICENSE` pour plus de détails.

---

## 👨‍💻 Auteur

**Sigma-Fatal** - [GitHub](https://github.com/Sigma-Fatal)

---

## 🙏 Remerciements

- [face_recognition](https://github.com/ageitgey/face_recognition) par Adam Geitgey
- [dlib](http://dlib.net/) par Davis King
- [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter) par Tom Schimansky
- [OpenCV](https://opencv.org/)

---

## 📚 Ressources

- [Documentation face_recognition](https://face-recognition.readthedocs.io/)
- [Guide dlib](http://dlib.net/python/index.html)
- [Tutoriel CustomTkinter](https://customtkinter.tomschimansky.com/)

---

⭐ **Si ce projet vous plaît, n'hésitez pas à lui donner une étoile sur GitHub !** ⭐