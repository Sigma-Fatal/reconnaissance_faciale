"""
Moteur de Reconnaissance Faciale
---------------------------------
Module optionnel qui peut être utilisé pour séparer la logique
de reconnaissance de l'interface graphique.
"""

import face_recognition
import numpy as np
import cv2


class MoteurReconnaissance:
    """
    Classe qui encapsule la logique de reconnaissance faciale.
    Peut être utilisée indépendamment de l'interface graphique.
    """
    
    def __init__(self, encodages_connus: list, noms_connus: list, seuil: float = 0.5):
        """
        Initialise le moteur de reconnaissance.
        
        Args:
            encodages_connus: Liste des signatures faciales de référence
            noms_connus: Liste des noms associés
            seuil: Seuil de reconnaissance (0.4-0.6 recommandé)
        """
        self.encodages_connus = encodages_connus
        self.noms_connus = noms_connus
        self.seuil = seuil
    
    def traiter_frame(self, frame, reduire: bool = True):
        """
        Traite une frame vidéo pour détecter et reconnaître les visages.
        
        Args:
            frame: Image OpenCV (BGR)
            reduire: Si True, réduit l'image pour accélérer le traitement
            
        Returns:
            tuple: (frame_annotée, liste_detections)
        """
        if reduire:
            petite_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
        else:
            petite_frame = frame.copy()
        
        rgb_frame = cv2.cvtColor(petite_frame, cv2.COLOR_BGR2RGB)
        
        # Détection des visages
        emplacements = face_recognition.face_locations(rgb_frame)
        
        if not emplacements:
            return frame, []
        
        # Encodage des visages détectés
        encodages = face_recognition.face_encodings(rgb_frame, emplacements)
        
        detections = []
        
        for encodage, (top, right, bottom, left) in zip(encodages, emplacements):
            if reduire:
                top *= 4
                right *= 4
                bottom *= 4
                left *= 4
            
            # Comparaison
            distances = face_recognition.face_distance(self.encodages_connus, encodage)
            meilleur_index = np.argmin(distances)
            distance_min = distances[meilleur_index]
            
            if distance_min < self.seuil:
                nom = self.noms_connus[meilleur_index]
                confiance = (1 - distance_min) * 100
            else:
                nom = "Inconnu"
                confiance = (1 - distance_min) * 100
            
            detections.append({
                "nom": nom,
                "confiance": confiance,
                "position": (top, right, bottom, left)
            })
            
            # Annotation
            couleur = (0, 255, 0) if nom != "Inconnu" else (0, 0, 255)
            cv2.rectangle(frame, (left, top), (right, bottom), couleur, 2)
            cv2.rectangle(frame, (left, bottom - 35), (right, bottom), couleur, cv2.FILLED)
            cv2.putText(frame, f"{nom} ({confiance:.1f}%)", 
                       (left + 6, bottom - 10),
                       cv2.FONT_HERSHEY_DUPLEX, 0.6, (255, 255, 255), 1)
        
        return frame, detections