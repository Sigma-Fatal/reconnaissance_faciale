"""
Interface Graphique de Reconnaissance Faciale - Version Ultime
----------------------------------------------------------------
Fonctionnalités :
  • Reconnaissance en temps réel multi-caméras
  • Ajout de visage en direct (3 captures avec preview)
  • Sauvegarde auto des captures avec nom + date
  • Export CSV de l'historique
  • Alerte visuelle (flash) lors d'une reconnaissance
  • 🎙️ Synthèse vocale "Bonjour [Nom]"
  • 📊 Tableau de bord statistique (onglet stats)
  • 📧 Notification email quand une personne arrive
  • Interface avec onglets (Caméra | Statistiques)
"""
import customtkinter as ctk
from PIL import Image
import cv2
import face_recognition
import pickle
import os
import sys
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
import time
import csv
import threading
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from collections import Counter

# Synthèse vocale (plusieurs backends possibles)
try:
    import pyttsx3  # Offline, recommandé
    TTS_ENGINE = "pyttsx3"
except ImportError:
    try:
        import gtts
        from io import BytesIO
        import pygame
        TTS_ENGINE = "gtts"
    except ImportError:
        TTS_ENGINE = None
        print("⚠️ Synthèse vocale désactivée (installez pyttsx3 : pip install pyttsx3)")

sys.path.append(str(Path(__file__).parent))

# ============================================================
# CONFIGURATION
# ============================================================
COULEURS = {
    "vert": "#2ecc71", "rouge": "#e74c3c", "bleu": "#3498db",
    "orange": "#f39c12", "violet": "#9b59b6", "gris": "#95a5a6",
    "fond": "#1a1a2e", "alerte_vert": "#1a3a1a", "alerte_rouge": "#3a1a1a",
    "or": "#f1c40f", "cyan": "#00bcd4",
}

CAMERA_NOMS = {0: "Intégrée", 2: "Logitech C930e"}

# Configuration email (à personnaliser)
EMAIL_CONFIG = {
    "smtp_server": "smtp.gmail.com",
    "smtp_port": 587,
    "email_from": "votre.email@gmail.com",
    "email_password": "votre_mot_de_passe_app",  # Mot de passe d'application Gmail
    "email_to": "destinataire@example.com",
    "notifications_active": False,  # Désactivé par défaut
}

# ============================================================
# CLASSE PRINCIPALE
# ============================================================

class ApplicationReconnaissanceFaciale(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("🎯 Reconnaissance Faciale Pro - Édition Ultime")
        self.geometry("1350x800")
        self.minsize(1100, 700)
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        # ---- Variables d'état ----
        self.camera_active = False
        self.cap = None
        self.camera_index = 0
        self.encodages_charges = False
        self.encodages_connus = []
        self.noms_connus = []
        self.image_tk = None
        self.personne_actuelle = "Inconnu"
        self.confiance_actuelle = 0.0
        self.seuil_reconnaissance = 0.5
        self.compteur_frames = 0
        self.dernier_resultat = None
        self.fps = 0
        self.frame_times = []
        self.photos_prises = 0
        self.temps_debut = time.time()

        # ---- Historique ----
        self.historique_csv = []
        self.derniere_notification = {}  # Pour éviter les doublons email

        # ---- Mode ajout ----
        self.mode_ajout = False
        self.nom_ajout = ""
        self.captures_ajout = []
        self.captures_requises = 3

        # ---- Synthèse vocale ----
        self.tts_engine = None
        self.init_tts()

        # ---- Alerte ----
        self.flash_actif = False
        self.derniere_alerte = ""
        self.derniere_personne_vocale = ""
        self.temps_derniere_vocal = time.time()

        # ---- Données statistiques ----
        self.stats_passages = Counter()
        self.stats_heures = Counter()
        self.stats_jours = Counter()
        self.stats_confiance_total = 0.0
        self.stats_nb_detections = 0

        # ---- Initialisation ----
        self.charger_encodages()
        self.creer_interface()
        self.protocol("WM_DELETE_WINDOW", self.fermer_application)

    # ================================================================
    # SYNTHÈSE VOCALE
    # ================================================================
    def init_tts(self):
        if TTS_ENGINE == "pyttsx3":
            try:
                self.tts_engine = pyttsx3.init()
                self.tts_engine.setProperty('rate', 160)
                self.tts_engine.setProperty('volume', 0.8)
                print("🔊 Synthèse vocale pyttsx3 prête")
            except Exception as e:
                print(f"⚠️ Erreur TTS: {e}")
                self.tts_engine = None
        elif TTS_ENGINE == "gtts":
            print("🔊 Synthèse vocale gTTS prête (online)")
        else:
            print("⚠️ Synthèse vocale non disponible")

    def parler(self, texte):
        """Prononce un texte de manière asynchrone"""
        if self.tts_engine is None and TTS_ENGINE != "gtts":
            return

        def _parler():
            try:
                if TTS_ENGINE == "pyttsx3" and self.tts_engine:
                    self.tts_engine.say(texte)
                    self.tts_engine.runAndWait()
                elif TTS_ENGINE == "gtts":
                    tts = gtts.gTTS(text=texte, lang='fr')
                    fp = BytesIO()
                    tts.write_to_fp(fp)
                    fp.seek(0)
                    pygame.mixer.init()
                    pygame.mixer.music.load(fp)
                    pygame.mixer.music.play()
                    while pygame.mixer.music.get_busy():
                        time.sleep(0.1)
            except Exception as e:
                print(f"⚠️ Erreur parole: {e}")

        threading.Thread(target=_parler, daemon=True).start()

    # ================================================================
    # ENCODAGES
    # ================================================================
    def charger_encodages(self):
        chemin = Path(__file__).parent.parent / "data" / "encodages" / "encodings.pkl"
        if not os.path.exists(chemin):
            self.encodages_charges = False
            return
        try:
            with open(chemin, 'rb') as f:
                donnees = pickle.load(f)
            self.encodages_connus = list(donnees["encodages"])
            self.noms_connus = list(donnees["noms"])
            self.encodages_charges = True
            print(f"✅ {len(self.encodages_connus)} encodages chargés")
        except Exception as e:
            print(f"❌ Erreur : {e}")

    def sauvegarder_encodages(self):
        chemin = Path(__file__).parent.parent / "data" / "encodages" / "encodings.pkl"
        chemin.parent.mkdir(parents=True, exist_ok=True)
        with open(chemin, 'wb') as f:
            pickle.dump({"encodages": self.encodages_connus, "noms": self.noms_connus}, f)

    # ================================================================
    # INTERFACE AVEC ONGLETS
    # ================================================================
    def creer_interface(self):
        # Système d'onglets
        self.tabview = ctk.CTkTabview(self, corner_radius=10)
        self.tabview.pack(padx=10, pady=10, expand=True, fill="both")

        self.tab_camera = self.tabview.add("📷 Caméra")
        self.tab_stats = self.tabview.add("📊 Statistiques")

        self.creer_tab_camera()
        self.creer_tab_stats()

    # ================================================================
    # ONGLET CAMÉRA
    # ================================================================
    def creer_tab_camera(self):
        self.tab_camera.grid_columnconfigure(0, weight=3)
        self.tab_camera.grid_columnconfigure(1, weight=1)
        self.tab_camera.grid_rowconfigure(0, weight=1)

        # Zone vidéo
        self.frame_video = ctk.CTkFrame(self.tab_camera, corner_radius=10, fg_color=COULEURS["fond"])
        self.frame_video.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")
        image_noire = Image.new("RGB", (640, 480), COULEURS["fond"])
        self.image_tk = ctk.CTkImage(light_image=image_noire, dark_image=image_noire, size=(640, 480))
        self.label_video = ctk.CTkLabel(self.frame_video, text="", image=self.image_tk)
        self.label_video.pack(padx=5, pady=5, expand=True, fill="both")

        # Panneau droit
        panneau = ctk.CTkFrame(self.tab_camera, corner_radius=10)
        panneau.grid(row=0, column=1, padx=5, pady=5, sticky="nsew")

        # === CONTRÔLES CAMÉRA ===
        ctk.CTkLabel(panneau, text="📷 CAMÉRA", font=ctk.CTkFont(size=13, weight="bold"), text_color=COULEURS["bleu"]).pack(pady=(10, 5))
        self.bouton_camera = ctk.CTkButton(panneau, text="▶ DÉMARRER", height=36, font=ctk.CTkFont(size=12, weight="bold"), command=self.basculer_camera)
        self.bouton_camera.pack(pady=3, padx=15, fill="x")

        frm = ctk.CTkFrame(panneau, fg_color="transparent")
        frm.pack(pady=3, padx=15, fill="x")
        frm.grid_columnconfigure((0, 1), weight=1)
        ctk.CTkButton(frm, text="🔄 Changer", font=ctk.CTkFont(size=10), height=28, command=self.changer_camera).grid(row=0, column=0, padx=(0, 3), sticky="ew")
        self.bouton_capture = ctk.CTkButton(frm, text="📸 Capture", font=ctk.CTkFont(size=10), height=28, fg_color=COULEURS["orange"], command=self.capturer_photo)
        self.bouton_capture.grid(row=0, column=1, padx=(3, 0), sticky="ew")

        self.label_statut = ctk.CTkLabel(panneau, text="⏸ INACTIF", font=ctk.CTkFont(size=11, weight="bold"), text_color=COULEURS["rouge"])
        self.label_statut.pack(pady=3)
        self.label_photos = ctk.CTkLabel(panneau, text="📸 0 captures", font=ctk.CTkFont(size=10), text_color="#555555")
        self.label_photos.pack()
        self.label_debug = ctk.CTkLabel(panneau, text="", font=ctk.CTkFont(size=9), text_color="#555555")
        self.label_debug.pack(pady=2)

        ctk.CTkFrame(panneau, height=1, fg_color="#2a2a4a").pack(pady=8, padx=15, fill="x")

        # === RECONNAISSANCE ===
        ctk.CTkLabel(panneau, text="👤 RECONNAISSANCE", font=ctk.CTkFont(size=13, weight="bold"), text_color=COULEURS["vert"]).pack(pady=(5, 5))
        self.label_personne = ctk.CTkLabel(panneau, text="En attente...", font=ctk.CTkFont(size=24, weight="bold"))
        self.label_personne.pack(pady=3)
        self.barre_confiance = ctk.CTkProgressBar(panneau, width=180, height=12, fg_color="#2a2a4a", progress_color=COULEURS["vert"])
        self.barre_confiance.pack(pady=3, padx=25)
        self.barre_confiance.set(0)
        self.label_confiance = ctk.CTkLabel(panneau, text="", font=ctk.CTkFont(size=11), text_color=COULEURS["gris"])
        self.label_confiance.pack()

        ctk.CTkFrame(panneau, height=1, fg_color="#2a2a4a").pack(pady=8, padx=15, fill="x")

        # === AJOUT DE VISAGE ===
        ctk.CTkLabel(panneau, text="➕ AJOUTER UNE PERSONNE", font=ctk.CTkFont(size=12, weight="bold"), text_color=COULEURS["violet"]).pack(pady=(5, 5))
        self.entry_nom = ctk.CTkEntry(panneau, placeholder_text="Nom de la personne", height=30, font=ctk.CTkFont(size=11))
        self.entry_nom.pack(pady=3, padx=15, fill="x")
        self.bouton_ajout = ctk.CTkButton(panneau, text="🎯 Ajouter (3 photos auto)", height=30, font=ctk.CTkFont(size=10), fg_color=COULEURS["violet"], command=self.demarrer_ajout)
        self.bouton_ajout.pack(pady=3, padx=15, fill="x")
        self.label_progression_ajout = ctk.CTkLabel(panneau, text="", font=ctk.CTkFont(size=10), text_color=COULEURS["orange"])
        self.label_progression_ajout.pack(pady=2)

        ctk.CTkFrame(panneau, height=1, fg_color="#2a2a4a").pack(pady=8, padx=15, fill="x")

        # === PARAMÈTRES ===
        ctk.CTkLabel(panneau, text="⚙️ PARAMÈTRES", font=ctk.CTkFont(size=12, weight="bold"), text_color=COULEURS["orange"]).pack(pady=(5, 3))
        self.slider_seuil = ctk.CTkSlider(panneau, from_=0.3, to=0.7, number_of_steps=40, command=self.maj_seuil)
        self.slider_seuil.pack(pady=3, padx=15, fill="x")
        self.slider_seuil.set(self.seuil_reconnaissance)
        self.label_valeur_seuil = ctk.CTkLabel(panneau, text=f"Seuil: {self.seuil_reconnaissance:.2f}", font=ctk.CTkFont(size=10), text_color=COULEURS["gris"])
        self.label_valeur_seuil.pack()

        self.check_voix = ctk.CTkCheckBox(panneau, text="🔊 Annonce vocale", font=ctk.CTkFont(size=10), checkbox_width=16, checkbox_height=16)
        self.check_voix.pack(pady=3, padx=15, anchor="w")
        self.check_voix.select()

        self.check_flash = ctk.CTkCheckBox(panneau, text="💡 Alerte flash", font=ctk.CTkFont(size=10), checkbox_width=16, checkbox_height=16)
        self.check_flash.pack(pady=3, padx=15, anchor="w")
        self.check_flash.select()

        self.check_email = ctk.CTkCheckBox(panneau, text="📧 Notification email", font=ctk.CTkFont(size=10), checkbox_width=16, checkbox_height=16, command=self.basculer_email)
        self.check_email.pack(pady=3, padx=15, anchor="w")
        if EMAIL_CONFIG["notifications_active"]:
            self.check_email.select()

        ctk.CTkFrame(panneau, height=1, fg_color="#2a2a4a").pack(pady=8, padx=15, fill="x")

        # === DONNÉES ===
        ctk.CTkLabel(panneau, text="📋 DONNÉES", font=ctk.CTkFont(size=12, weight="bold"), text_color=COULEURS["cyan"]).pack(pady=(5, 5))
        frm_export = ctk.CTkFrame(panneau, fg_color="transparent")
        frm_export.pack(pady=3, padx=15, fill="x")
        frm_export.grid_columnconfigure((0, 1), weight=1)
        ctk.CTkButton(frm_export, text="📊 CSV", font=ctk.CTkFont(size=10), height=28, fg_color="#16a085", command=self.exporter_csv).grid(row=0, column=0, padx=(0, 3), sticky="ew")
        ctk.CTkButton(frm_export, text="🗑️ RAZ", font=ctk.CTkFont(size=10), height=28, fg_color="#555555", command=self.raz_historique).grid(row=0, column=1, padx=(3, 0), sticky="ew")
        self.label_nb_enreg = ctk.CTkLabel(panneau, text=f"Événements: {len(self.historique_csv)}", font=ctk.CTkFont(size=10), text_color="#666666")
        self.label_nb_enreg.pack(pady=3)

        # === PERSONNES ===
        ctk.CTkLabel(panneau, text="📋 PERSONNES ENREGISTRÉES", font=ctk.CTkFont(size=10, weight="bold"), text_color="#666666").pack(pady=(10, 3))
        self.frame_liste_personnes = ctk.CTkFrame(panneau, fg_color="transparent")
        self.frame_liste_personnes.pack(pady=3, padx=15, fill="x")
        self.actualiser_liste_personnes_widget()

        ctk.CTkFrame(panneau, fg_color="transparent").pack(expand=True)
        ctk.CTkButton(panneau, text="❌ QUITTER", height=35, fg_color=COULEURS["rouge"], command=self.fermer_application).pack(pady=10, padx=15, fill="x")

    # ================================================================
    # ONGLET STATISTIQUES
    # ================================================================
    def creer_tab_stats(self):
        self.tab_stats.grid_columnconfigure((0, 1), weight=1)
        self.tab_stats.grid_rowconfigure(0, weight=0)
        self.tab_stats.grid_rowconfigure(1, weight=1)

        # En-tête
        ctk.CTkLabel(self.tab_stats, text="📊 TABLEAU DE BORD STATISTIQUE", font=ctk.CTkFont(size=22, weight="bold"), text_color=COULEURS["or"]).grid(row=0, column=0, columnspan=2, pady=(20, 10))

        # ---- Colonne gauche : Top personnes ----
        frame_gauche = ctk.CTkFrame(self.tab_stats, corner_radius=10)
        frame_gauche.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")

        ctk.CTkLabel(frame_gauche, text="🏆 TOP PERSONNES DÉTECTÉES", font=ctk.CTkFont(size=14, weight="bold"), text_color=COULEURS["or"]).pack(pady=(15, 10))
        self.texte_top_personnes = ctk.CTkTextbox(frame_gauche, height=200, corner_radius=6, fg_color="#111122", text_color="#ffffff", font=ctk.CTkFont(size=12, family="monospace"))
        self.texte_top_personnes.pack(pady=5, padx=15, fill="both", expand=True)
        self.texte_top_personnes.insert("1.0", "En attente de données...\n")
        self.texte_top_personnes.configure(state="disabled")

        # ---- Colonne droite : Stats globales ----
        frame_droite = ctk.CTkFrame(self.tab_stats, corner_radius=10)
        frame_droite.grid(row=1, column=1, padx=10, pady=10, sticky="nsew")

        ctk.CTkLabel(frame_droite, text="📈 STATISTIQUES GLOBALES", font=ctk.CTkFont(size=14, weight="bold"), text_color=COULEURS["cyan"]).pack(pady=(15, 10))

        self.label_total_detections = ctk.CTkLabel(frame_droite, text="Détections totales : 0", font=ctk.CTkFont(size=16, weight="bold"), text_color="#ffffff")
        self.label_total_detections.pack(pady=5)

        self.label_confiance_moyenne = ctk.CTkLabel(frame_droite, text="Confiance moyenne : --", font=ctk.CTkFont(size=14), text_color=COULEURS["gris"])
        self.label_confiance_moyenne.pack(pady=5)

        self.label_personne_plus_vue = ctk.CTkLabel(frame_droite, text="Personne la plus vue : --", font=ctk.CTkFont(size=14), text_color=COULEURS["vert"])
        self.label_personne_plus_vue.pack(pady=5)

        self.label_derniere_detection = ctk.CTkLabel(frame_droite, text="Dernière détection : --", font=ctk.CTkFont(size=12), text_color="#888888")
        self.label_derniere_detection.pack(pady=5)

        ctk.CTkFrame(frame_droite, height=1, fg_color="#2a2a4a").pack(pady=15, padx=15, fill="x")

        # Distribution horaire
        ctk.CTkLabel(frame_droite, text="🕐 DISTRIBUTION HORAIRE", font=ctk.CTkFont(size=13, weight="bold"), text_color=COULEURS["orange"]).pack(pady=(10, 5))
        self.texte_distribution = ctk.CTkTextbox(frame_droite, height=100, corner_radius=6, fg_color="#111122", text_color="#aaaaaa", font=ctk.CTkFont(size=11, family="monospace"))
        self.texte_distribution.pack(pady=5, padx=15, fill="x")
        self.texte_distribution.insert("1.0", "00h-06h: 0\n06h-12h: 0\n12h-18h: 0\n18h-24h: 0\n")
        self.texte_distribution.configure(state="disabled")

        # Bouton rafraîchir
        ctk.CTkButton(frame_droite, text="🔄 Rafraîchir les stats", font=ctk.CTkFont(size=11), height=30, command=self.rafraichir_stats).pack(pady=15)

    # ================================================================
    # CAMÉRA
    # ================================================================
    def basculer_camera(self):
        if not self.camera_active:
            self.demarrer_camera()
        else:
            self.arreter_camera()

    def demarrer_camera(self):
        self.cap = cv2.VideoCapture(self.camera_index)
        if not self.cap.isOpened():
            self.cap.release()
            self.cap = cv2.VideoCapture(0)
            self.camera_index = 0
        if not self.cap.isOpened():
            self.label_debug.configure(text="❌ Aucune caméra")
            return
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        ret, _ = self.cap.read()
        if not ret:
            self.cap.release()
            self.cap = None
            return
        self.camera_active = True
        self.temps_debut = time.time()
        self.bouton_camera.configure(text="⏹ ARRÊTER", fg_color=COULEURS["rouge"])
        nom = CAMERA_NOMS.get(self.camera_index, f"Cam {self.camera_index}")
        self.label_statut.configure(text=f"▶ {nom}", text_color=COULEURS["vert"])
        self.boucle_video()

    def arreter_camera(self):
        self.camera_active = False
        if self.cap:
            self.cap.release()
            self.cap = None
        self.bouton_camera.configure(text="▶ DÉMARRER", fg_color=COULEURS["bleu"])
        self.label_statut.configure(text="⏸ INACTIF", text_color=COULEURS["rouge"])
        self.label_personne.configure(text="En attente...")
        self.label_confiance.configure(text="")
        self.barre_confiance.set(0)
        self.label_debug.configure(text="")
        self.dernier_resultat = None
        self.arreter_flash()
        image_noire = Image.new("RGB", (640, 480), COULEURS["fond"])
        self.image_tk.configure(light_image=image_noire, dark_image=image_noire, size=(640, 480))

    def changer_camera(self):
        if self.camera_active:
            self.arreter_camera()
        cameras_valides = [0, 2]
        try:
            pos = cameras_valides.index(self.camera_index)
            self.camera_index = cameras_valides[(pos + 1) % len(cameras_valides)]
        except ValueError:
            self.camera_index = cameras_valides[0]
        nom = CAMERA_NOMS.get(self.camera_index, f"Cam {self.camera_index}")
        self.label_debug.configure(text=f"📷 {nom} prête")

    # ================================================================
    # BOUCLE VIDÉO
    # ================================================================
    def boucle_video(self):
        if not self.camera_active or not self.cap:
            return
        try:
            ret, frame = self.cap.read()
            if not ret or frame is None:
                if self.camera_active:
                    self.after(15, self.boucle_video)
                return

            maintenant = time.time()
            self.frame_times.append(maintenant)
            self.frame_times = [t for t in self.frame_times if t > maintenant - 1]
            if len(self.frame_times) > 1:
                self.fps = len(self.frame_times)

            skip = 3 if hasattr(self, 'check_perf') and self.check_perf.get() else 2
            self.compteur_frames += 1

            if self.mode_ajout and self.compteur_frames % 30 == 0:
                self.capturer_pour_ajout(frame)
            elif self.encodages_charges and len(self.encodages_connus) > 0 and self.compteur_frames % skip == 0:
                self.dernier_resultat = self.analyser_frame(frame)

            if self.dernier_resultat is not None:
                frame = self.dessiner_cadres(frame, self.dernier_resultat)

            if self.mode_ajout:
                cv2.putText(frame, f"AJOUT: {self.nom_ajout} ({len(self.captures_ajout)}/{self.captures_requises})",
                           (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 165, 0), 2)

            display = cv2.resize(frame, (640, 480))
            display_rgb = cv2.cvtColor(display, cv2.COLOR_BGR2RGB)

            if self.flash_actif:
                overlay = display_rgb.copy()
                if self.derniere_alerte == "reconnu":
                    overlay[:, :] = [46, 204, 113]
                else:
                    overlay[:, :] = [231, 76, 60]
                display_rgb = cv2.addWeighted(display_rgb, 0.7, overlay, 0.3, 0)

            img_pil = Image.fromarray(display_rgb)
            self.image_tk.configure(light_image=img_pil, dark_image=img_pil, size=(640, 480))

        except Exception as e:
            print(f"❌ {e}")

        if self.camera_active:
            self.after(15, self.boucle_video)

    # ================================================================
    # RECONNAISSANCE
    # ================================================================
    def analyser_frame(self, frame):
        small = cv2.resize(frame, (0, 0), fx=0.5, fy=0.5)
        rgb = cv2.cvtColor(small, cv2.COLOR_BGR2RGB)
        locations = face_recognition.face_locations(rgb)

        nom_cam = CAMERA_NOMS.get(self.camera_index, f"C{self.camera_index}")
        self.label_debug.configure(text=f"{nom_cam} | 👤 {len(locations)} | FPS: {self.fps}")

        if len(locations) == 0:
            self.label_personne.configure(text="Aucun visage", text_color="#888888")
            self.label_confiance.configure(text="")
            self.barre_confiance.set(0)
            return None

        encodages_frame = face_recognition.face_encodings(rgb, locations)
        resultats = []

        for encodage, (top, right, bottom, left) in zip(encodages_frame, locations):
            distances = face_recognition.face_distance(self.encodages_connus, encodage)
            best = np.argmin(distances)
            dist = distances[best]

            if dist < self.seuil_reconnaissance:
                nom = self.noms_connus[best]
                confiance = (1 - dist) * 100
                couleur = (46, 204, 113)
                couleur_ui = COULEURS["vert"]
                alerte_type = "reconnu"
            else:
                nom = "Inconnu"
                confiance = max(0, (1 - dist) * 100)
                couleur = (231, 76, 60)
                couleur_ui = COULEURS["rouge"]
                alerte_type = "inconnu"

            resultats.append({
                "nom": nom, "confiance": confiance,
                "couleur": couleur, "couleur_ui": couleur_ui,
                "top": top * 2, "right": right * 2,
                "bottom": bottom * 2, "left": left * 2,
                "alerte": alerte_type,
            })

        r = resultats[0]
        self.label_personne.configure(text=r["nom"], text_color=r["couleur_ui"])
        self.label_confiance.configure(text=f"Confiance: {r['confiance']:.1f}%")
        self.barre_confiance.set(r["confiance"] / 100)

        # Historique + Stats
        self.ajouter_historique(r["nom"], r["confiance"])
        now = datetime.now()
        self.stats_passages[r["nom"]] += 1
        self.stats_heures[f"{now.hour:02d}h"] += 1
        self.stats_jours[now.strftime("%A")] += 1
        self.stats_confiance_total += r["confiance"]
        self.stats_nb_detections += 1

        # Alerte flash
        if self.check_flash.get() and r["nom"] != self.personne_actuelle:
            if r["nom"] != "Inconnu" or self.personne_actuelle != "Aucun visage":
                self.declencher_flash(r["alerte"])

        # Synthèse vocale
        if self.check_voix.get() and r["nom"] != "Inconnu":
            if r["nom"] != self.derniere_personne_vocale or (time.time() - self.temps_derniere_vocal) > 10:
                self.parler(f"Bonjour {r['nom']}")
                self.derniere_personne_vocale = r["nom"]
                self.temps_derniere_vocal = time.time()

        # Notification email
        if self.check_email.get() and EMAIL_CONFIG["notifications_active"] and r["nom"] != "Inconnu":
            self.envoyer_notification_email(r["nom"], r["confiance"])

        self.personne_actuelle = r["nom"]
        return resultats

    # ================================================================
    # NOTIFICATION EMAIL
    # ================================================================
    def basculer_email(self):
        if self.check_email.get():
            EMAIL_CONFIG["notifications_active"] = True
            self.label_debug.configure(text="📧 Notifications email activées")
        else:
            EMAIL_CONFIG["notifications_active"] = False
            self.label_debug.configure(text="📧 Notifications email désactivées")

    def envoyer_notification_email(self, nom, confiance):
        """Envoie un email de notification (max 1 par personne toutes les 5 minutes)"""
        maintenant = time.time()
        if nom in self.derniere_notification:
            if maintenant - self.derniere_notification[nom] < 300:  # 5 minutes
                return

        self.derniere_notification[nom] = maintenant

        def _envoyer():
            try:
                msg = MIMEMultipart()
                msg['From'] = EMAIL_CONFIG["email_from"]
                msg['To'] = EMAIL_CONFIG["email_to"]
                msg['Subject'] = f"🔔 {nom} détecté(e) - Reconnaissance Faciale"
                
                corps = f"""
                <h2>👤 Personne reconnue</h2>
                <p><strong>Nom :</strong> {nom}</p>
                <p><strong>Confiance :</strong> {confiance:.1f}%</p>
                <p><strong>Date/Heure :</strong> {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}</p>
                <p><strong>Caméra :</strong> {CAMERA_NOMS.get(self.camera_index, 'Inconnue')}</p>
                <hr>
                <p><em>Envoyé par le système de reconnaissance faciale MadaPro</em></p>
                """
                msg.attach(MIMEText(corps, 'html'))

                server = smtplib.SMTP(EMAIL_CONFIG["smtp_server"], EMAIL_CONFIG["smtp_port"])
                server.starttls()
                server.login(EMAIL_CONFIG["email_from"], EMAIL_CONFIG["email_password"])
                server.send_message(msg)
                server.quit()
                print(f"📧 Email envoyé pour {nom}")
            except Exception as e:
                print(f"⚠️ Erreur email: {e}")

        threading.Thread(target=_envoyer, daemon=True).start()

    # ================================================================
    # STATISTIQUES
    # ================================================================
    def rafraichir_stats(self):
        """Met à jour l'affichage des statistiques"""
        # Top personnes
        top = self.stats_passages.most_common(10)
        self.texte_top_personnes.configure(state="normal")
        self.texte_top_personnes.delete("1.0", "end")
        if top:
            for i, (nom, nb) in enumerate(top, 1):
                barre = "█" * min(nb, 30)
                self.texte_top_personnes.insert("end", f"{i:2d}. {nom:<20s} {barre} {nb}\n")
        else:
            self.texte_top_personnes.insert("1.0", "Aucune donnée\n")
        self.texte_top_personnes.configure(state="disabled")

        # Stats globales
        self.label_total_detections.configure(text=f"Détections totales : {self.stats_nb_detections}")
        if self.stats_nb_detections > 0:
            moyenne = self.stats_confiance_total / self.stats_nb_detections
            self.label_confiance_moyenne.configure(text=f"Confiance moyenne : {moyenne:.1f}%")
        if top:
            self.label_personne_plus_vue.configure(text=f"Personne la plus vue : {top[0][0]} ({top[0][1]} fois)")
        if self.historique_csv:
            self.label_derniere_detection.configure(text=f"Dernière détection : {self.historique_csv[-1]['heure']} - {self.historique_csv[-1]['personne']}")

        # Distribution horaire
        tranches = {"00h-06h": 0, "06h-12h": 0, "12h-18h": 0, "18h-24h": 0}
        for heure_str, nb in self.stats_heures.items():
            h = int(heure_str.replace("h", ""))
            if h < 6:
                tranches["00h-06h"] += nb
            elif h < 12:
                tranches["06h-12h"] += nb
            elif h < 18:
                tranches["12h-18h"] += nb
            else:
                tranches["18h-24h"] += nb

        self.texte_distribution.configure(state="normal")
        self.texte_distribution.delete("1.0", "end")
        max_val = max(tranches.values()) if max(tranches.values()) > 0 else 1
        for tranche, nb in tranches.items():
            barre = "█" * int(nb / max_val * 20)
            self.texte_distribution.insert("end", f"{tranche}: {barre} {nb}\n")
        self.texte_distribution.configure(state="disabled")

    # ================================================================
    # (Le reste des fonctions : dessiner_cadres, declencher_flash,
    #  ajouter_historique, exporter_csv, raz_historique,
    #  demarrer_ajout, capturer_pour_ajout, finaliser_ajout,
    #  actualiser_liste_personnes_widget, capturer_photo,
    #  maj_seuil, fermer_application)
    # ... IDENTIQUES à la version précédente ...
    # ================================================================

    def dessiner_cadres(self, frame, resultats):
        for r in resultats:
            cv2.rectangle(frame, (r["left"], r["top"]), (r["right"], r["bottom"]), r["couleur"], 3)
            cv2.rectangle(frame, (r["left"], r["bottom"] - 35), (r["right"], r["bottom"]), r["couleur"], cv2.FILLED)
            cv2.putText(frame, f"{r['nom']} ({r['confiance']:.0f}%)",
                       (r["left"] + 6, r["bottom"] - 10),
                       cv2.FONT_HERSHEY_DUPLEX, 0.7, (255, 255, 255), 2)
        return frame

    def declencher_flash(self, type_alerte):
        self.flash_actif = True
        self.derniere_alerte = type_alerte
        self.after(500, self.arreter_flash)

    def arreter_flash(self):
        self.flash_actif = False
        self.derniere_alerte = ""

    def ajouter_historique(self, nom, confiance):
        maintenant = datetime.now()
        entree = {
            "date": maintenant.strftime("%Y-%m-%d"),
            "heure": maintenant.strftime("%H:%M:%S"),
            "personne": nom,
            "confiance": f"{confiance:.1f}%",
            "camera": CAMERA_NOMS.get(self.camera_index, str(self.camera_index)),
        }
        if self.historique_csv:
            derniere = self.historique_csv[-1]
            if derniere["personne"] == nom:
                try:
                    t1 = datetime.strptime(derniere["heure"], "%H:%M:%S")
                    if (maintenant - t1).seconds < 2:
                        return
                except:
                    pass
        self.historique_csv.append(entree)
        self.label_nb_enreg.configure(text=f"Événements: {len(self.historique_csv)}")

    def exporter_csv(self):
        if not self.historique_csv:
            self.label_debug.configure(text="⚠️ Aucune donnée")
            return
        dossier = Path(__file__).parent.parent / "data" / "exports"
        dossier.mkdir(parents=True, exist_ok=True)
        nom_fichier = dossier / f"historique_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        try:
            with open(nom_fichier, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=["date", "heure", "personne", "confiance", "camera"])
                writer.writeheader()
                writer.writerows(self.historique_csv)
            self.label_debug.configure(text=f"✅ {nom_fichier.name}")
        except Exception as e:
            self.label_debug.configure(text=f"❌ {e}")

    def raz_historique(self):
        self.historique_csv = []
        self.stats_passages.clear()
        self.stats_heures.clear()
        self.stats_jours.clear()
        self.stats_confiance_total = 0.0
        self.stats_nb_detections = 0
        self.label_nb_enreg.configure(text="Événements: 0")
        self.label_debug.configure(text="🗑️ Données effacées")

    def demarrer_ajout(self):
        nom = self.entry_nom.get().strip()
        if not nom:
            self.label_debug.configure(text="⚠️ Entrez un nom")
            return
        if nom in self.noms_connus:
            self.label_debug.configure(text=f"⚠️ '{nom}' existe déjà")
            return
        self.mode_ajout = True
        self.nom_ajout = nom
        self.captures_ajout = []
        self.bouton_ajout.configure(text="⏳ Capture...", state="disabled", fg_color=COULEURS["orange"])
        self.label_progression_ajout.configure(text=f"📸 0/{self.captures_requises}")

    def capturer_pour_ajout(self, frame):
        if len(self.captures_ajout) >= self.captures_requises:
            return
        small = cv2.resize(frame, (0, 0), fx=0.5, fy=0.5)
        rgb = cv2.cvtColor(small, cv2.COLOR_BGR2RGB)
        locations = face_recognition.face_locations(rgb)
        if len(locations) != 1:
            self.label_progression_ajout.configure(text=f"⚠️ {len(locations)} visage(s) - montrez-en 1 seul")
            return
        encodage = face_recognition.face_encodings(rgb, locations)[0]
        self.captures_ajout.append(encodage)
        self.label_progression_ajout.configure(text=f"📸 {len(self.captures_ajout)}/{self.captures_requises}")
        if len(self.captures_ajout) >= self.captures_requises:
            self.finaliser_ajout()

    def finaliser_ajout(self):
        encodage_moyen = np.mean(self.captures_ajout, axis=0)
        self.encodages_connus.append(encodage_moyen)
        self.noms_connus.append(self.nom_ajout)
        self.sauvegarder_encodages()
        self.label_progression_ajout.configure(text=f"✅ '{self.nom_ajout}' ajouté !")
        self.label_debug.configure(text=f"✅ {self.nom_ajout} enregistré")
        self.bouton_ajout.configure(text="🎯 Ajouter (3 photos auto)", state="normal", fg_color=COULEURS["violet"])
        self.entry_nom.delete(0, "end")
        self.mode_ajout = False
        self.captures_ajout = []
        self.actualiser_liste_personnes_widget()

    def actualiser_liste_personnes_widget(self):
        for widget in self.frame_liste_personnes.winfo_children():
            widget.destroy()
        txt = "\n".join([f"• {n}" for n in self.noms_connus]) if self.noms_connus else "Aucune"
        ctk.CTkLabel(self.frame_liste_personnes, text=txt, font=ctk.CTkFont(size=9), text_color="#888888").pack()

    def capturer_photo(self):
        if not self.camera_active or not self.cap:
            return
        ret, frame = self.cap.read()
        if not ret:
            return
        self.photos_prises += 1
        self.label_photos.configure(text=f"📸 {self.photos_prises} captures")
        dossier = Path(__file__).parent.parent / "data" / "captures"
        dossier.mkdir(parents=True, exist_ok=True)
        prefixe = self.personne_actuelle.replace(" ", "_") if self.personne_actuelle not in ["En attente...", "Aucun visage", "Inconnu"] else "inconnu"
        nom_fichier = dossier / f"{prefixe}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
        cv2.imwrite(str(nom_fichier), frame)
        self.label_debug.configure(text=f"💾 {nom_fichier.name}")
        self.bouton_capture.configure(fg_color=COULEURS["vert"])
        self.after(200, lambda: self.bouton_capture.configure(fg_color=COULEURS["orange"]))

    def maj_seuil(self, val):
        self.seuil_reconnaissance = round(float(val), 2)
        self.label_valeur_seuil.configure(text=f"Seuil: {self.seuil_reconnaissance:.2f}")

    def fermer_application(self):
        print("🛑 Fermeture...")
        self.camera_active = False
        if self.cap:
            self.cap.release()
        cv2.destroyAllWindows()
        self.destroy()
        sys.exit(0)


def main():
    print("=" * 55)
    print("🚀 Reconnaissance Faciale Pro - Édition Ultime")
    print("=" * 55)
    app = ApplicationReconnaissanceFaciale()
    app.mainloop()

if __name__ == "__main__":
    main()