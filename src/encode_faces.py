"""
Script d'encodage des visages connus
------------------------------------
Ce script scanne le dossier 'data/images_reference/' pour détecter et encoder
les visages des personnes connues. Les encodages sont sauvegardés pour être
utilisés plus tard par le système de reconnaissance en temps réel.
"""

import sys
import os
import pickle
from pathlib import Path

# ============================================================
# CORRECTIF : Force l'import silencieux de face_recognition
# ============================================================
import warnings
warnings.filterwarnings('ignore')

import io
stderr_backup = sys.stderr
sys.stderr = io.StringIO()

try:
    import face_recognition
except ImportError as e:
    sys.stderr = stderr_backup
    print(f"❌ Erreur d'import : {e}")
    print("📦 Installation des modèles manquants...")
    import subprocess
    subprocess.check_call([
        sys.executable, "-m", "pip", "install",
        "git+https://github.com/ageitgey/face_recognition_models"
    ])
    import face_recognition
finally:
    sys.stderr = stderr_backup
# ============================================================


def encoder_visages(dossier_images: str, fichier_sortie: str) -> None:
    """
    Encode tous les visages trouvés dans les images du dossier spécifié.
    
    Args:
        dossier_images (str): Chemin vers le dossier contenant les images
        fichier_sortie (str): Chemin où sauvegarder les encodages (.pkl)
    """
    
    # Initialisation des listes pour stocker les données
    encodages_connus = []  # Les signatures numériques des visages
    noms_connus = []        # Les noms associés aux visages
    
    # Vérification que le dossier d'images existe
    if not os.path.exists(dossier_images):
        print(f"❌ ERREUR : Le dossier '{dossier_images}' n'existe pas.")
        print(f"   Créez-le et ajoutez-y des photos de personnes.")
        sys.exit(1)
    
    # Récupération de toutes les images dans le dossier
    # ✅ AJOUT DU FORMAT WEBP
    extensions_valides = ('.jpg', '.jpeg', '.png', '.bmp', '.webp')
    
    fichiers_images = []
    
    for fichier in os.listdir(dossier_images):
        if fichier.lower().endswith(extensions_valides):
            fichiers_images.append(fichier)
    
    # Vérification qu'il y a au moins une image
    if len(fichiers_images) == 0:
        print(f"❌ ERREUR : Aucune image trouvée dans '{dossier_images}'.")
        print(f"   Ajoutez des photos au format : {', '.join(extensions_valides)}")
        sys.exit(1)
    
    print(f"📁 {len(fichiers_images)} image(s) trouvée(s) dans '{dossier_images}'")
    print("🔄 Début de l'encodage des visages...")
    print("-" * 50)
    
    # Traitement de chaque image
    for fichier in fichiers_images:
        chemin_image = os.path.join(dossier_images, fichier)
        
        # Extraction du nom de la personne (nom du fichier sans extension)
        nom_personne = os.path.splitext(fichier)[0]
        
        print(f"🔍 Analyse de : {fichier} → Personne : '{nom_personne}'")
        
        try:
            # Chargement de l'image (face_recognition gère le WebP nativement)
            image = face_recognition.load_image_file(chemin_image)
            
            # Détection des visages dans l'image
            emplacements_visages = face_recognition.face_locations(image)
            
            # Vérification du nombre de visages trouvés
            if len(emplacements_visages) == 0:
                print(f"   ⚠️  ATTENTION : Aucun visage détecté dans '{fichier}'")
                print(f"   → Cette image sera ignorée.")
                continue
            
            if len(emplacements_visages) > 1:
                print(f"   ⚠️  ATTENTION : Plusieurs visages détectés ({len(emplacements_visages)})")
                print(f"   → Seul le premier visage sera utilisé pour '{nom_personne}'")
            
            # Génération de l'encodage (128 mesures faciales) pour chaque visage
            encodages = face_recognition.face_encodings(image, emplacements_visages)
            
            # On prend le premier visage trouvé
            encodages_connus.append(encodages[0])
            noms_connus.append(nom_personne)
            
            print(f"   ✅ Visage encodé avec succès pour '{nom_personne}'")
            
        except Exception as e:
            print(f"   ❌ ERREUR lors du traitement de '{fichier}' : {e}")
            continue
    
    print("-" * 50)
    
    # Vérification qu'au moins un visage a été encodé
    if len(encodages_connus) == 0:
        print("❌ ERREUR : Aucun visage n'a pu être encodé.")
        print("   Vérifiez vos images et réessayez.")
        sys.exit(1)
    
    # Création du dossier de sortie si nécessaire
    dossier_sortie = os.path.dirname(fichier_sortie)
    if dossier_sortie and not os.path.exists(dossier_sortie):
        os.makedirs(dossier_sortie)
        print(f"📁 Dossier créé : {dossier_sortie}")
    
    # Sauvegarde des encodages dans un fichier
    donnees = {
        "encodages": encodages_connus,
        "noms": noms_connus
    }
    
    try:
        with open(fichier_sortie, 'wb') as f:
            pickle.dump(donnees, f)
        print(f"💾 Encodages sauvegardés dans : {fichier_sortie}")
    except Exception as e:
        print(f"❌ ERREUR lors de la sauvegarde : {e}")
        sys.exit(1)
    
    # Résumé final
    print("\n" + "=" * 50)
    print("📊 RÉSUMÉ DE L'ENCODAGE")
    print("=" * 50)
    print(f"✅ {len(encodages_connus)} visage(s) encodé(s) avec succès :")
    for i, nom in enumerate(noms_connus, 1):
        print(f"   {i}. {nom}")


def main():
    """
    Fonction principale qui lance l'encodage des visages.
    """
    print("=" * 50)
    print("🎯 ENCODAGE DES VISAGES DE RÉFÉRENCE")
    print("=" * 50)
    print()
    
    # Définition des chemins
    chemin_projet = Path(__file__).parent.parent
    
    dossier_images = chemin_projet / "data" / "images_reference"
    fichier_encodages = chemin_projet / "data" / "encodages" / "encodings.pkl"
    
    print(f"📂 Dossier des images : {dossier_images}")
    print(f"📂 Fichier de sortie : {fichier_encodages}")
    print()
    
    # Lancement de l'encodage
    encoder_visages(
        dossier_images=str(dossier_images),
        fichier_sortie=str(fichier_encodages)
    )
    
    print("\n✨ Encodage terminé avec succès !")
    print("💡 Vous pouvez maintenant lancer l'application avec : python src/gui_app.py")


if __name__ == "__main__":
    main()