#!/usr/bin/env python3
"""
Black Box Vault - Mobile App
Material You redesign featuring a Welcome Screen, Scanner, and History.
"""

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.screenmanager import ScreenManager, Screen, FadeTransition
from kivy.uix.widget import Widget
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.clock import Clock
from kivy.graphics.texture import Texture
from kivy.lang import Builder
from kivy.properties import BooleanProperty, StringProperty

import qrcode
import time
import hashlib
import json
import os
import logging
from datetime import datetime
from typing import Optional, Dict, List, Any

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("vault_app")

# --- CONFIGURATION ---
# Use environment variable for secrets as per security constraints
SHARED_SECRET: bytes = os.environ.get("VAULT_SHARED_SECRET", "MY_SUPER_SECRET_VAULT_KEY").encode()
HISTORY_FILE: str = "vault_history.json"

KV_STYLES = """
#:import hex kivy.utils.get_color_from_hex

# Material You Color Palette
#:set color_mustard hex('#F4E3B5')
#:set color_dark_gray hex('#3D3D3D')
#:set color_yellow hex('#E5C05C')
#:set color_orange hex('#E65100')
#:set color_white hex('#FFFFFF')
#:set color_light_mustard hex('#FDF5E6')

<MaterialLabel@Label>:
    color: color_dark_gray
    markup: True

<NavButton@BoxLayout>:
    orientation: 'vertical'
    icon_text: ''
    label_text: ''
    is_active: BooleanProperty(False)
    on_touch_down: app.nav_click(self)
    MaterialLabel:
        text: root.icon_text
        font_size: '24sp'
        color: color_orange if root.is_active else color_dark_gray
        size_hint_y: 0.6
    MaterialLabel:
        text: root.label_text
        font_size: '12sp'
        bold: root.is_active
        color: color_orange if root.is_active else color_dark_gray
        size_hint_y: 0.4

<HistoryItem@BoxLayout>:
    orientation: 'vertical'
    size_hint_y: None
    height: dp(60)
    padding: dp(10)
    spacing: dp(5)
    token_text: ''
    time_text: ''
    canvas.before:
        Color:
            rgba: color_yellow
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [dp(10)]
    MaterialLabel:
        text: root.token_text
        font_size: '18sp'
        bold: True
        halign: 'left'
        text_size: self.size
    MaterialLabel:
        text: root.time_text
        font_size: '12sp'
        halign: 'left'
        text_size: self.size

<WelcomeScreen>:
    canvas.before:
        Color:
            rgba: color_mustard
        Rectangle:
            pos: self.pos
            size: self.size
    BoxLayout:
        orientation: 'vertical'
        padding: dp(40)
        spacing: dp(20)
        
        # Spacer
        Widget:
            size_hint_y: 0.2
            
        # Large Orange QR Icon
        AnchorLayout:
            size_hint_y: 0.4
            Widget:
                size_hint: None, None
                size: dp(120), dp(120)
                canvas.before:
                    Color:
                        rgba: color_orange
                    RoundedRectangle:
                        pos: self.pos
                        size: self.size
                        radius: [dp(20)]
                    Color:
                        rgba: color_mustard
                    Rectangle:
                        pos: self.x + dp(30), self.y + dp(30)
                        size: dp(60), dp(60)
                    Color:
                        rgba: color_orange
                    Rectangle:
                        pos: self.x + dp(45), self.y + dp(45)
                        size: dp(30), dp(30)
                        
        MaterialLabel:
            text: "Black Box Vault"
            font_size: '32sp'
            bold: True
            size_hint_y: 0.15
            
        MaterialLabel:
            text: "Secure your secrets with\\nzero-trust TOTP authentication."
            font_size: '16sp'
            halign: 'center'
            size_hint_y: 0.15
            
        # CTA Button
        AnchorLayout:
            size_hint_y: 0.2
            Button:
                text: "START SCANNING"
                size_hint: 0.8, 0.6
                background_normal: ''
                background_color: color_yellow
                color: color_dark_gray
                bold: True
                font_size: '16sp'
                on_release: app.switch_to_main()
                canvas.before:
                    Color:
                        rgba: color_yellow
                    RoundedRectangle:
                        pos: self.pos
                        size: self.size
                        radius: [dp(25)]

<ScannerScreen>:
    canvas.before:
        Color:
            rgba: color_mustard
        Rectangle:
            pos: self.pos
            size: self.size
    BoxLayout:
        orientation: 'vertical'
        padding: dp(20)
        spacing: dp(10)
        
        MaterialLabel:
            text: "Scanner"
            font_size: '24sp'
            bold: True
            size_hint_y: 0.1
            
        AnchorLayout:
            size_hint_y: 0.6
            # Orange Frame
            Widget:
                size_hint: None, None
                size: dp(280), dp(280)
                canvas.before:
                    Color:
                        rgba: color_orange
                    Line:
                        width: dp(4)
                        rounded_rectangle: (self.x, self.y, self.width, self.height, dp(15))
            # White background for QR code for contrast
            Widget:
                size_hint: None, None
                size: dp(260), dp(260)
                canvas.before:
                    Color:
                        rgba: color_white
                    RoundedRectangle:
                        pos: self.pos
                        size: self.size
                        radius: [dp(10)]
            # QR Image Widget
            Image:
                id: qr_image_widget
                size_hint: None, None
                size: dp(240), dp(240)
                allow_stretch: True
                keep_ratio: True
                
        BoxLayout:
            orientation: 'vertical'
            size_hint_y: 0.3
            MaterialLabel:
                id: token_label_widget
                text: "---"
                font_size: '36sp'
                bold: True
            MaterialLabel:
                id: timer_label_widget
                text: "Refreshing..."
                font_size: '14sp'

<HistoryScreen>:
    canvas.before:
        Color:
            rgba: color_mustard
        Rectangle:
            pos: self.pos
            size: self.size
    BoxLayout:
        orientation: 'vertical'
        padding: dp(20)
        spacing: dp(10)
        
        MaterialLabel:
            text: "History"
            font_size: '24sp'
            bold: True
            size_hint_y: 0.1
            
        ScrollView:
            size_hint_y: 0.9
            BoxLayout:
                id: history_list_layout
                orientation: 'vertical'
                size_hint_y: None
                height: self.minimum_height
                spacing: dp(10)

<MainAppLayout>:
    orientation: 'vertical'
    ScreenManager:
        id: sm
        size_hint_y: 0.9
        ScannerScreen:
            name: 'scanner'
            id: scanner_screen
        HistoryScreen:
            name: 'history'
            id: history_screen
            
    # Bottom Navigation
    BoxLayout:
        size_hint_y: 0.1
        canvas.before:
            Color:
                rgba: color_light_mustard
            Rectangle:
                pos: self.pos
                size: self.size
        NavButton:
            id: nav_scanner
            icon_text: '📷'
            label_text: 'SCANNER'
            is_active: True
        NavButton:
            id: nav_history
            icon_text: '📜'
            label_text: 'HISTORY'
            is_active: False

<RootScreenManager>:
    transition: FadeTransition()
    WelcomeScreen:
        name: 'welcome'
    Screen:
        name: 'main'
        MainAppLayout:
            id: main_app_layout
"""

Builder.load_string(KV_STYLES)

class WelcomeScreen(Screen):
    pass

class ScannerScreen(Screen):
    pass

class HistoryScreen(Screen):
    pass

class MainAppLayout(BoxLayout):
    pass

class RootScreenManager(ScreenManager):
    pass

class VaultKeyApp(App):
    history_list: List[Dict[str, str]] = []
    
    def build(self) -> Widget:
        self.root_widget = RootScreenManager()
        self.main_layout = self.root_widget.ids.main_app_layout
        
        # Screen references
        self.scanner_screen = self.main_layout.ids.scanner_screen
        self.history_screen = self.main_layout.ids.history_screen
        self.sm = self.main_layout.ids.sm
        
        # Widget references
        self.qr_image = self.scanner_screen.ids.qr_image_widget
        self.token_label = self.scanner_screen.ids.token_label_widget
        self.timer_label = self.scanner_screen.ids.timer_label_widget
        self.history_layout = self.history_screen.ids.history_list_layout
        
        # Nav references
        self.nav_scanner = self.main_layout.ids.nav_scanner
        self.nav_history = self.main_layout.ids.nav_history
        
        self.last_generated_time_block: int = 0
        self.last_generated_token: Optional[str] = None
        
        self.load_history()
        
        # Do not start clock until main screen is active
        return self.root_widget

    def switch_to_main(self) -> None:
        """Transitions from Welcome screen to Main App screens"""
        self.root_widget.current = 'main'
        Clock.schedule_interval(self.update_state, 1)
        self.update_state(0)

    def nav_click(self, instance: Widget) -> None:
        """Handle bottom navigation clicks"""
        if self.root_widget.current != 'main':
            return
            
        self.nav_scanner.is_active = False
        self.nav_history.is_active = False
        
        if instance == self.nav_scanner:
            self.nav_scanner.is_active = True
            self.sm.current = 'scanner'
        elif instance == self.nav_history:
            self.nav_history.is_active = True
            self.sm.current = 'history'
            self.populate_history_ui()

    def get_totp_token(self) -> Optional[str]:
        """Generates a time-based hash valid for 30 seconds"""
        time_block = int(time.time() // 30)
        if time_block == self.last_generated_time_block:
            return None
        self.last_generated_time_block = time_block
        data = str(time_block).encode() + SHARED_SECRET
        h = hashlib.sha256(data).hexdigest()
        return h[:8].upper()

    def update_state(self, dt: float) -> None:
        """Periodic UI and token state update"""
        if self.sm.current != 'scanner':
            return
            
        seconds_remaining = 30 - (int(time.time()) % 30)
        self.timer_label.text = f"Refreshing token in: {seconds_remaining}s"
        
        new_token = self.get_totp_token()
        if new_token:
            self.generate_qr(new_token)
            self.token_label.text = new_token
            self.save_to_history(new_token)

    def generate_qr(self, data: str) -> None:
        """Generates pixel-perfect QR code texture"""
        qr = qrcode.QRCode(box_size=1, border=0)
        qr.add_data(data)
        qr.make(fit=True)
        matrix = qr.get_matrix()
        
        buff = bytearray()
        for row in matrix:
            for val in row:
                buff.extend([0, 0, 0] if val else [255, 255, 255])
        
        size = len(matrix)
        texture = Texture.create(size=(size, size), colorfmt='rgb')
        texture.blit_buffer(bytes(buff), colorfmt='rgb', bufferfmt='ubyte')
        texture.mag_filter = 'nearest'
        self.qr_image.texture = texture

    def save_to_history(self, token: str) -> None:
        """Saves generated token to persistent history"""
        if token != self.last_generated_token:
            self.last_generated_token = token
            entry = {
                'token': token,
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            self.history_list.insert(0, entry)
            if len(self.history_list) > 20:
                self.history_list = self.history_list[:20]
            self.persist_history()

    def populate_history_ui(self) -> None:
        """Renders history items onto the History screen ScrollView"""
        self.history_layout.clear_widgets()
        
        # Avoid circular imports by using the dynamically created KV widget
        from kivy.factory import Factory
        
        if not self.history_list:
            lbl = Factory.MaterialLabel(text="No history available.", font_size="16sp")
            self.history_layout.add_widget(lbl)
            return

        for item in self.history_list:
            hist_widget = Factory.HistoryItem()
            hist_widget.token_text = item.get('token', 'Unknown')
            hist_widget.time_text = item.get('timestamp', 'Unknown time')
            self.history_layout.add_widget(hist_widget)

    def load_history(self) -> None:
        """Loads history from JSON file safely"""
        self.history_list = []
        if os.path.exists(HISTORY_FILE):
            try:
                with open(HISTORY_FILE, 'r') as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        self.history_list = data
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse history JSON: {e}")
            except Exception as e:
                logger.error(f"Error loading history: {e}")

    def persist_history(self) -> None:
        """Saves history to JSON file safely"""
        try:
            with open(HISTORY_FILE, 'w') as f:
                json.dump(self.history_list, f)
        except Exception as e:
            logger.error(f"Error saving history: {e}")

    def on_stop(self) -> None:
        """App shutdown hook"""
        self.persist_history()

if __name__ == '__main__':
    VaultKeyApp().run()
