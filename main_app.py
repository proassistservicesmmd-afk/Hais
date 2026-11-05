import os
import subprocess
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.tabbedpanel import TabbedPanel, TabbedPanelItem
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.button import Button

class HAISApp(App):
    def build(self):
        self.title = "HUMANITY AI SHIELD V7.0"
        
        # Panneau principal avec onglets
        panel = TabbedPanel(do_default_tab=False)
        
        # --- ONGLET 1 : Vérification Globale ---
        tab_verif = TabbedPanelItem(text='Vérification')
        layout_verif = BoxLayout(orientation='vertical', padding=10, spacing=10)
        
        self.scroll_verif = ScrollView()
        self.label_verif = Label(text="Prêt à vérifier l'intégrité...", size_hint_y=None, halign="left", valign="top")
        self.label_verif.bind(texture_size=self.label_verif.setter('size'))
        self.scroll_verif.add_widget(self.label_verif)
        
        btn_verif = Button(text="Lancer verifier.sh", size_hint=(1, 0.2), background_color=(0, 0.7, 0, 1))
        btn_verif.bind(on_press=self.run_verifier)
        
        layout_verif.add_widget(self.scroll_verif)
        layout_verif.add_widget(btn_verif)
        tab_verif.add_widget(layout_verif)
        panel.add_widget(tab_verif)

        # --- ONGLET 2 : Tableau de Bord ---
        tab_bord = TabbedPanelItem(text='Tableau de Bord')
        layout_bord = BoxLayout(orientation='vertical', padding=10, spacing=10)
        
        self.scroll_bord = ScrollView()
        self.label_bord = Label(text="Cliquez pour afficher le tableau de bord...", size_hint_y=None, halign="left", valign="top")
        self.label_bord.bind(texture_size=self.label_bord.setter('size'))
        self.scroll_bord.add_widget(self.label_bord)
        
        btn_bord = Button(text="Afficher le Tableau", size_hint=(1, 0.2), background_color=(0, 0.5, 1, 1))
        btn_bord.bind(on_press=self.run_dashboard)
        
        layout_bord.add_widget(self.scroll_bord)
        layout_bord.add_widget(btn_bord)
        tab_bord.add_widget(layout_bord)
        panel.add_widget(tab_bord)

        # --- ONGLET 3 : Risques & Sécurité ---
        tab_secu = TabbedPanelItem(text='Sécurité')
        layout_secu = BoxLayout(orientation='vertical', padding=10, spacing=10)
        
        self.scroll_secu = ScrollView()
        self.label_secu = Label(text="Surveillance des risques...", size_hint_y=None, halign="left", valign="top")
        self.label_secu.bind(texture_size=self.label_secu.setter('size'))
        self.scroll_secu.add_widget(self.label_secu)
        
        btn_secu = Button(text="Lancer l'Analyse", size_hint=(1, 0.2), background_color=(1, 0.5, 0, 1))
        btn_secu.bind(on_press=self.run_security)
        
        layout_secu.add_widget(self.scroll_secu)
        layout_secu.add_widget(btn_secu)
        tab_secu.add_widget(layout_secu)
        panel.add_widget(tab_secu)

        return panel

    def run_verifier(self, instance):
        self.label_verif.text = "Exécution de verifier.sh en cours..."
        try:
            os.chdir(os.path.expanduser("~/HUMANITY_AI_SHIELD_V7_0"))
            result = subprocess.run(["./verifier.sh"], capture_output=True, text=True, timeout=60)
            self.label_verif.text = result.stdout + "\n" + result.stderr
        except Exception as e:
            self.label_verif.text = f"Erreur: {str(e)}"

    def run_dashboard(self, instance):
        self.label_bord.text = "Chargement..."
        try:
            os.chdir(os.path.expanduser("~/HUMANITY_AI_SHIELD_V7_0/package"))
            result = subprocess.run(["python", "tableau_bord.py"], capture_output=True, text=True, timeout=30)
            self.label_bord.text = result.stdout + "\n" + result.stderr
        except Exception as e:
            self.label_bord.text = f"Erreur: {str(e)}"

    def run_security(self, instance):
        self.label_secu.text = "Analyse des risques en cours..."
        try:
            os.chdir(os.path.expanduser("~/HUMANITY_AI_SHIELD_V7_0/package"))
            result = subprocess.run(["python", "moteur_risques.py"], capture_output=True, text=True, timeout=30)
            self.label_secu.text = result.stdout + "\n" + result.stderr
        except Exception as e:
            self.label_secu.text = f"Erreur: {str(e)}"

if __name__ == '__main__':
    HAISApp().run()

