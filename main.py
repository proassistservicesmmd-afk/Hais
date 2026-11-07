# -*- coding: utf-8 -*-
"""
HUMANITY AI SHIELD - V7.0
Point d'entrée Android (Kivy)
"""

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from kivy.core.window import Window
from kivy.utils import platform

# Import de votre logique métier existante
try:
    from package.moteur_risques import analyser_action
    from package.tableau_bord import charger_evenements
    IMPORTS_OK = True
    ERREUR_IMPORT = ""
except Exception as e:
    IMPORTS_OK = False
    ERREUR_IMPORT = str(e)


class EcranPrincipal(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation='vertical', padding=15, spacing=15, **kwargs)

        # --- EN-TÊTE ---
        entete = Label(
            text="[b]HUMANITY AI SHIELD[/b]\n[i]Version 7.0 - Sécurité Android[/i]",
            markup=True,
            size_hint_y=0.15,
            halign="center",
            valign="middle"
        )
        entete.bind(size=entete.setter('text_size'))
        self.add_widget(entete)

        # --- ZONE DE SAISIE ---
        zone_saisie = BoxLayout(orientation='vertical', spacing=5, size_hint_y=0.2)
        zone_saisie.add_widget(Label(text="Action à analyser :", size_hint_y=0.4))
        
        self.champ_action = TextInput(
            hint_text="ex: suppression_fichier, acces_non_autorise...",
            multiline=False,
            size_hint_y=0.6,
            font_size=16
        )
        zone_saisie.add_widget(self.champ_action)
        self.add_widget(zone_saisie)

        # --- BOUTON D'ANALYSE ---
        self.btn_analyser = Button(
            text="ANALYSER L'ACTION",
            size_hint_y=0.1,
            background_color=(0.1, 0.6, 1, 1),
            bold=True
        )
        self.btn_analyser.bind(on_press=self.analyser_action)
        self.add_widget(self.btn_analyser)

        # --- ZONE DE RÉSULTAT ---
        scroll = ScrollView(size_hint_y=0.4)
        self.zone_resultat = Label(
            text="En attente d'une action...",
            size_hint_y=None,
            halign="left",
            valign="top",
            markup=True
        )
        self.zone_resultat.bind(
            width=lambda *x: setattr(self.zone_resultat, 'text_size', (self.zone_resultat.width, None)),
            texture_size=lambda *x: setattr(self.zone_resultat, 'height', self.zone_resultat.texture_size[1])
        )
        scroll.add_widget(self.zone_resultat)
        self.add_widget(scroll)

        # --- BOUTON INTÉGRITÉ ---
        self.btn_integrite = Button(
            text="VÉRIFIER L'INTÉGRITÉ DU JOURNAL",
            size_hint_y=0.1,
            background_color=(0.2, 0.7, 0.2, 1)
        )
        self.btn_integrite.bind(on_press=self.verifier_integrite)
        self.add_widget(self.btn_integrite)

        # --- MESSAGE D'ERREUR D'IMPORT ---
        if not IMPORTS_OK:
            self.zone_resultat.text = f"[color=ff0000][b]Erreur d'import :[/b][/color]\n{ERREUR_IMPORT}"

    def analyser_action(self, instance):
        if not IMPORTS_OK:
            self.zone_resultat.text = "[color=ff0000]Impossible d'analyser : module manquant.[/color]"
            return

        action = self.champ_action.text.strip()
        if not action:
            self.zone_resultat.text = "[color=ffaa00]Veuillez entrer une action.[/color]"
            return

        try:
            resultat = analyser_action(action)
            decision = resultat.get('decision', 'INCONNU')
            niveau = resultat.get('niveau', 'INCONNU')
            motif = resultat.get('motif', '')

            couleur = "00ff00" if decision == "AUTORISER" else "ffaa00" if decision == "ALERTE" else "ff0000"

            self.zone_resultat.text = (
                f"[b]Action :[/b] {action}\n\n"
                f"[b]Décision :[/b] [color={couleur}]{decision}[/color]\n"
                f"[b]Niveau :[/b] {niveau}\n"
                f"[b]Motif :[/b] {motif}"
            )
        except Exception as e:
            self.zone_resultat.text = f"[color=ff0000]Erreur d'analyse :[/color]\n{e}"

    def verifier_integrite(self, instance):
        if not IMPORTS_OK:
            self.zone_resultat.text = "[color=ff0000]Impossible de vérifier : module manquant.[/color]"
            return

        try:
            evenements = charger_evenements()
            self.zone_resultat.text = (
                f"[color=00ff00][b]Succès :[/b][/color]\n"
                f"Journal chargé avec succès.\n"
                f"Nombre d'événements : {len(evenements)}"
            )
        except Exception as e:
            self.zone_resultat.text = f"[color=ff0000]Erreur d'intégrité :[/color]\n{e}"


class HumanityShieldApp(App):
    def build(self):
        if platform not in ('android', 'ios'):
            Window.size = (400, 700)
        
        self.title = "Humanity AI Shield V7.0"
        return EcranPrincipal()


if __name__ == "__main__":
    HumanityShieldApp().run()
from main_app import *
