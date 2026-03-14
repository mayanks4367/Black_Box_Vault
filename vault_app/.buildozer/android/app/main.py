#!/usr/bin/env python3
"""
Black Box Vault - Polished UI Version with Functional Tabs
Look-and-feel update matching the provided target image.
"""
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.label import Label
from kivy.uix.image import Image
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.widget import Widget
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.clock import Clock
from kivy.graphics.texture import Texture
from kivy.core.window import Window
from kivy.lang import Builder
from kivy.properties import BooleanProperty
import qrcode
import time
import hashlib
import json
import os
from datetime import datetime

# --- CONFIGURATION ---
SHARED_SECRET = b"MY_SUPER_SECRET_VAULT_KEY"
HISTORY_FILE = "vault_history.json"

# --- Kivy Language Styling (KV) ---
# This defines the look and feel: colors, rounded corners, and layout structure.
KV_STYLES = """
#:import hex kivy.utils.get_color_from_hex

# Define Theme Colors
#:set color_bg_dark hex('#1a1c23')
#:set color_bg_light hex('#2b2e3b')
#:set color_white hex('#ffffff')
#:set color_gray hex('#8a8a8a')
#:set color_accent hex('#f5c542') # Yellow/Gold

<RootLayout>:
    orientation: 'vertical'
    canvas.before:
        Color:
            rgba: color_bg_dark
        Rectangle:
            pos: self.pos
            size: self.size

# Custom Label optimized for the dark theme
<DarkThemeLabel@Label>:
    color: color_white
    markup: True

<SubTextLabel@Label>:
    color: color_gray
    font_size: '14sp'

# The white rounded container for the QR code
<QRContainer@AnchorLayout>:
    anchor_x: 'center'
    anchor_y: 'center'
    padding: dp(20)
    canvas.before:
        Color:
            rgba: color_white
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [dp(15),]

# The visual "scanner brackets" overlay
<ScannerOverlay@Widget>:
    canvas:
        Color:
            rgba: color_accent
        Line:
            width: dp(2)
            # Top Left corner
            points: [self.x, self.top - dp(20), self.x, self.top, self.x + dp(20), self.top]
        Line:
            width: dp(2)
            # Top Right corner
            points: [self.right - dp(20), self.top, self.right, self.top, self.right, self.top - dp(20)]
        Line:
            width: dp(2)
            # Bottom Left corner
            points: [self.x, self.y + dp(20), self.x, self.y, self.x + dp(20), self.y]
        Line:
            width: dp(2)
            # Bottom Right corner
            points: [self.right - dp(20), self.y, self.right, self.y, self.right, self.y + dp(20)]

# Bottom Navigation Item style
<NavItem@BoxLayout>:
    orientation: 'vertical'
    icon_text: ''
    label_text: ''
    is_active: BooleanProperty(False)
    on_touch_down: app.nav_click(self)
    DarkThemeLabel:
        text: root.icon_text
        font_size: '24sp'
        color: color_accent if root.is_active else color_gray
        size_hint_y: 0.6
    DarkThemeLabel:
        text: root.label_text
        font_size: '11sp'
        color: color_accent if root.is_active else color_gray
        size_hint_y: 0.4

# ================= MAIN UI STRUCTURE =================
<MainUI>:
    orientation: 'vertical'
    spacing: dp(10)
    
    # --- TOP SPACER / HEADER ---
    BoxLayout:
        size_hint_y: 0.15
        DarkThemeLabel:
            id: header_label
            text: "Place QR Code in the frame"
            font_size: '16sp'
            valign: 'bottom'

    # --- MIDDLE CONTENT (QR AREA) ---
    AnchorLayout:
        size_hint_y: 0.6
        anchor_x: 'center'
        anchor_y: 'center'
        
        # The white rounded box
        QRContainer:
            size_hint: None, None
            size: dp(280), dp(280)
            
            # The actual QR image inside the white box
            Image:
                id: qr_image_widget
                allow_stretch: True
                keep_ratio: True
                size_hint: 0.9, 0.9
                
            # The yellow brackets overlay
            ScannerOverlay:
                size_hint: 0.95, 0.95

    # --- STATUS TEXT AREA ---
    BoxLayout:
        orientation: 'vertical'
        size_hint_y: 0.15
        padding: dp(10)
        DarkThemeLabel:
            id: token_label_widget
            text: "---"
            font_size: '32sp'
            bold: True
        SubTextLabel:
            id: timer_label_widget
            text: "Refreshing..."

    # --- BOTTOM NAVIGATION BAR ---
    BoxLayout:
        id: nav_bar
        size_hint_y: 0.1
        padding: dp(10)
        canvas.before:
            Color:
                rgba: color_bg_light
            Rectangle:
                pos: self.pos
                size: self.size
                
        NavItem:
            id: nav_screen
            icon_text: '⌂'
            label_text: 'Screen'
            is_active: True
        NavItem:
            id: nav_generate
            icon_text: '🔑'
            label_text: 'Generate'
            is_active: False
        NavItem:
            id: nav_history
            icon_text: '📜'
            label_text: 'History'
            is_active: False
        NavItem:
            id: nav_settings
            icon_text: '⚙'
            label_text: 'Settings'
            is_active: False
"""
# Load style definitions
Builder.load_string(KV_STYLES)

class RootLayout(BoxLayout):
    pass

class MainUI(RootLayout):
    """The main application layout defined in KV structure above"""
    pass

class VaultKeyApp(App):
    # Global state
    current_screen = 'screen'
    history_list = []
    app_settings = {
        'token_timeout': 30,
        'auto_refresh': True,
        'dark_theme': True,
        'haptic_feedback': True
    }
    
    def build(self):
        # Initialize the main UI defined in KV
        self.root_widget = MainUI()
        
        # Get references to the widgets
        self.qr_image = self.root_widget.ids.qr_image_widget
        self.token_label = self.root_widget.ids.token_label_widget
        self.timer_label = self.root_widget.ids.timer_label_widget
        self.header_label = self.root_widget.ids.header_label
        
        # Navigation references
        self.nav_screen = self.root_widget.ids.nav_screen
        self.nav_generate = self.root_widget.ids.nav_generate
        self.nav_history = self.root_widget.ids.nav_history
        self.nav_settings = self.root_widget.ids.nav_settings
        
        self.last_generated_time_block = 0
        self.last_generated_token = None
        
        # Load history
        self.load_history()
        
        # Run the update loop every 1 second
        Clock.schedule_interval(self.update_state, 1)
        # Generate immediately on start
        self.update_state(0)
        
        return self.root_widget

    def nav_click(self, instance):
        """Handle navigation item clicks"""
        # Reset all nav items
        self.nav_screen.is_active = False
        self.nav_generate.is_active = False
        self.nav_history.is_active = False
        self.nav_settings.is_active = False
        
        # Determine which nav was clicked and activate it
        if instance == self.nav_screen:
            self.nav_screen.is_active = True
            self.switch_to_screen()
        elif instance == self.nav_generate:
            self.nav_generate.is_active = True
            self.switch_to_generate()
        elif instance == self.nav_history:
            self.nav_history.is_active = True
            self.switch_to_history()
        elif instance == self.nav_settings:
            self.nav_settings.is_active = True
            self.switch_to_settings()

    def switch_to_screen(self):
        """Switch to main Screen tab"""
        self.current_screen = 'screen'
        self.header_label.text = "Place QR Code in the frame"
        # Show QR area
        self.qr_image.parent.opacity = 1
        self.token_label.opacity = 1
        self.timer_label.opacity = 1
        # Resume token generation
        Clock.schedule_interval(self.update_state, 1)
        # Generate current token
        self.update_state(0)

    def switch_to_generate(self):
        """Switch to Generate tab - manual QR code entry"""
        self.current_screen = 'generate'
        self.header_label.text = "Generate Custom QR"
        # Generate custom QR for vault unlock
        token = self.generate_static_token()
        self.generate_qr(token)
        self.token_label.text = token
        self.timer_label.text = "Static token - use this to unlock"
        # Stop auto-refresh
        Clock.unschedule(self.update_state)

    def switch_to_history(self):
        """Switch to History tab"""
        self.current_screen = 'history'
        self.header_label.text = "Token History"
        # Show last 5 tokens as QR codes
        if self.history_list:
            # Show most recent token
            recent_token = self.history_list[0]['token']
            self.generate_qr(recent_token)
            self.token_label.text = recent_token
            self.timer_label.text = f"History: {len(self.history_list)} tokens saved"
        else:
            self.token_label.text = "No history"
            self.timer_label.text = "Generate tokens to build history"
        Clock.unschedule(self.update_state)

    def switch_to_settings(self):
        """Switch to Settings tab"""
        self.current_screen = 'settings'
        self.header_label.text = "Settings"
        # Show settings info
        self.token_label.text = "⚙ Config"
        self.timer_label.text = f"Timeout: {self.app_settings['token_timeout']}s | Auto-refresh: {self.app_settings['auto_refresh']}"
        Clock.unschedule(self.update_state)

    def generate_static_token(self):
        """Generate the static unlock token"""
        return "UNLOCK_MY_VAULT_NOW"

    # --- LOGIC ---
    def get_totp_token(self):
        """Generates a time-based hash valid for 30 seconds"""
        time_block = int(time.time() // 30)
        if time_block == self.last_generated_time_block:
            return None
        self.last_generated_time_block = time_block
        # Use simple hash instead of hmac to avoid blake2b issue on Android
        data = str(time_block).encode() + SHARED_SECRET
        h = hashlib.sha256(data).hexdigest()
        return h[:8].upper()

    def update_state(self, dt):
        # Update Timer Text
        seconds_remaining = 30 - (int(time.time()) % 30)
        self.timer_label.text = f"Refreshing token in: {seconds_remaining}s"
        
        # Check for new token block
        new_token = self.get_totp_token()
        if new_token:
            self.generate_qr(new_token)
            # Update main token text
            self.token_label.text = new_token
            # Save to history
            self.save_to_history(new_token)

    def generate_qr(self, data):
        # Standard "No-Dependency" QR Generation
        qr = qrcode.QRCode(box_size=1, border=0) 
        qr.add_data(data)
        qr.make(fit=True)
        matrix = qr.get_matrix()
        
        buff = bytearray()
        for row in matrix:
            for val in row:
                # Black pixels for data, White for background
                buff.extend([0, 0, 0] if val else [255, 255, 255])
        
        size = len(matrix)
        texture = Texture.create(size=(size, size), colorfmt='rgb')
        texture.blit_buffer(bytes(buff), colorfmt='rgb', bufferfmt='ubyte')
        # Nearest neighbor for sharp pixel look
        texture.mag_filter = 'nearest' 
        self.qr_image.texture = texture

    def save_to_history(self, token):
        """Save generated token to history"""
        if token != self.last_generated_token:
            self.last_generated_token = token
            entry = {
                'token': token,
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            # Add to beginning of list
            self.history_list.insert(0, entry)
            # Keep only last 10 tokens
            if len(self.history_list) > 10:
                self.history_list = self.history_list[:10]
            # Save to file
            self.persist_history()

    def load_history(self):
        """Load history from file"""
        try:
            if os.path.exists(HISTORY_FILE):
                with open(HISTORY_FILE, 'r') as f:
                    self.history_list = json.load(f)
        except:
            self.history_list = []

    def persist_history(self):
        """Save history to file"""
        try:
            with open(HISTORY_FILE, 'w') as f:
                json.dump(self.history_list, f)
        except:
            pass

    def on_stop(self):
        """Save data when app closes"""
        self.persist_history()

if __name__ == '__main__':
    VaultKeyApp().run()
