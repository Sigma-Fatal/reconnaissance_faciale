📋 Résumé des commandes

# 1. Se placer dans le projet
cd ~/Projets_all/reconnaissance_faciale

# 2. Activer l'environnement virtuel
source .venv/bin/activate

# 3. Encoder les visages (une seule fois, ou quand vous ajoutez des photos)
python src/encode_faces.py

# 4. Lancer l'application
python src/gui_app.py

# 5. Tester les imports
python test_imports.py



⚙️ Configurer l'email
En haut du fichier, modifiez :

EMAIL_CONFIG = {
    "smtp_server": "smtp.gmail.com",
    "smtp_port": 587,
    "email_from": "votre.email@gmail.com",       # ← À CHANGER
    "email_password": "votre_mot_de_passe_app",   # ← Mot de passe d'application Gmail
    "email_to": "destinataire@example.com",       # ← À CHANGER
    "notifications_active": False,
}
