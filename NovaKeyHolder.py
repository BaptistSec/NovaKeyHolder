import tkinter as tk
from tkinter import messagebox, scrolledtext, simpledialog
import json
import os
import logging
from logging.handlers import RotatingFileHandler
import pygame
import requests

class KeyHolderApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('Nova Key Holder')
        self.geometry('440x450')
        self.minsize(440, 450)

        pygame.mixer.init()
        self.controllers = []
        self.detect_controllers()

        self.settingsFileLocation = "settings.json"
        self.presetsFileLocation = "key_presets.json"
        self.log_filename = 'keyholder.log'
        self.changelog_filename = 'changelog.json'
        self.version = "0.2"

        self.load_settings()

        self.themes = {
            "light": {"bg": "white", "fg": "black", "button": "light gray", "label": "black"},
            "dark": {"bg": "gray20", "fg": "white", "button": "gray30", "label": "white"},
            "retro": {"bg": "bisque2", "fg": "blue4", "button": "tan1", "label": "blue2"},
            "matrix": {"bg": "black", "fg": "light green", "button": "black", "label": "light green"}}

        self.keysToHold = []
        self.numKeys = tk.IntVar(value=self.settings.get("numKeys", 1))
        self.toggleHotkey = tk.StringVar(value=self.settings.get("toggleHotkey", ""))
        self.current_theme = tk.StringVar(value=self.settings.get("current_theme", "light"))
        self.areKeysHeld = False
        self.isHotkeyCaptured = False

        self.numKeys_button = tk.Button(self, text=f"Switch number of keys (current: {self.numKeys.get()})", command=self.switch_numKeys)
        self.toggleHotkey_button = tk.Button(self, text="Capture Hotkey", command=self.captureHotkey)
        self.hotkeyLabel = tk.Label(self, text=f"Current hotkey: {self.toggleHotkey.get()}")
        self.captureKeys_button = tk.Button(self, text="Capture Keys", command=self.captureKeys, state=tk.DISABLED)
        self.savePreset_button = tk.Button(self, text="Save Preset", command=self.savePreset, state=tk.DISABLED)
        self.loadPreset_button = tk.Button(self, text="Load Preset", command=self.loadPreset)
        self.deletePreset_button = tk.Button(self, text="Delete Preset", command=self.deletePreset)
        self.feedbackLabel = tk.Label(self, text="")
        self.keyStateLabel = tk.Label(self, text="Keys state: Released")
        self.keysToHoldLabel = tk.Label(self, text="Keys to hold:")

        self.theme_button = tk.Button(self, text="Change Theme", command=self.change_theme)
        self.logs_button = tk.Button(self, text="Logs", command=self.show_logs)

        self.credits_button = tk.Button(self, text="Credits", command=self.show_credits)

        self.versionLabel = tk.Label(self, text=f"Version: {self.version}")
        self.update_button = tk.Button(self, text="Check for Updates", command=self.check_for_updates)

        self.place_gui_elements()
        self.apply_theme()
        self.load_audio_files()

        self.bind("<Configure>", self.on_resize)

        # Setup logging
        logging.basicConfig(level=logging.INFO,
                            format='%(asctime)s - %(levelname)s - %(message)s',
                            handlers=[RotatingFileHandler(self.log_filename, maxBytes=10000, backupCount=3)])

    def detect_controllers(self):
        pygame.joystick.init()
        self.controllers = [pygame.joystick.Joystick(i) for i in range(pygame.joystick.get_count())]
        for controller in self.controllers:
            controller.init()
            logging.info(f"Detected controller: {controller.get_name()}")

    def load_audio_files(self):
        try:
            self.key_press_sound = pygame.mixer.Sound("key_press.mp3")
            self.key_release_sound = pygame.mixer.Sound("key_release.mp3")
            self.error_sound = pygame.mixer.Sound("error.mp3")
        except Exception as e:
            logging.error("Error loading audio files: %s", e)
            self.show_error("Error loading audio files.")

    def play_sound(self, sound):
        try:
            sound.play()
        except Exception as e:
            logging.error("Error playing sound: %s", e)
            self.show_error("Error playing sound.")

    def place_gui_elements(self):
        self.numKeys_button.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        self.toggleHotkey_button.grid(row=1, column=0, padx=10, pady=10, sticky="ew")
        self.hotkeyLabel.grid(row=1, column=1, padx=10, pady=10, sticky="ew")
        self.captureKeys_button.grid(row=2, column=0, padx=10, pady=10, sticky="ew")
        self.savePreset_button.grid(row=3, column=0, padx=10, pady=10, sticky="ew")
        self.loadPreset_button.grid(row=4, column=0, padx=10, pady=10, sticky="ew")
        self.deletePreset_button.grid(row=5, column=0, padx=10, pady=10, sticky="ew")
        self.feedbackLabel.grid(row=2, column=1, padx=10, pady=10, sticky="ew")
        self.keyStateLabel.grid(row=6, column=0, padx=10, pady=10, sticky="ew")
        self.keysToHoldLabel.grid(row=3, column=1, padx=10, pady=10, sticky="ew")
        self.theme_button.grid(row=7, column=0, padx=10, pady=10, sticky="ew")
        self.logs_button.grid(row=8, column=0, padx=10, pady=10, sticky="ew")
        self.credits_button.grid(row=9, column=0, padx=10, pady=10, sticky="ew")
        self.versionLabel.grid(row=10, column=0, padx=10, pady=10, sticky="ew")
        self.update_button.grid(row=10, column=1, padx=10, pady=10, sticky="ew")

        for i in range(11):
            self.grid_rowconfigure(i, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

    def apply_theme(self):
        theme = self.themes[self.current_theme.get()]
        self.configure(bg=theme["bg"])
        self.numKeys_button.configure(bg=theme["button"], fg=theme["fg"])
        self.toggleHotkey_button.configure(bg=theme["button"], fg=theme["fg"])
        self.captureKeys_button.configure(bg=theme["button"], fg=theme["fg"])
        self.savePreset_button.configure(bg=theme["button"], fg=theme["fg"])
        self.loadPreset_button.configure(bg=theme["button"], fg=theme["fg"])
        self.deletePreset_button.configure(bg=theme["button"], fg=theme["fg"])
        self.theme_button.configure(bg=theme["button"], fg=theme["fg"])
        self.hotkeyLabel.configure(bg=theme["bg"], fg=theme["label"])
        self.feedbackLabel.configure(bg=theme["bg"], fg=theme["label"])
        self.keyStateLabel.configure(bg=theme["bg"], fg=theme["label"])
        self.keysToHoldLabel.configure(bg=theme["bg"], fg=theme["label"])
        self.logs_button.configure(bg=theme["button"], fg=theme["fg"])
        self.credits_button.configure(bg=theme["button"], fg=theme["fg"])
        self.versionLabel.configure(bg=theme["bg"], fg=theme["label"])
        self.update_button.configure(bg=theme["button"], fg=theme["fg"])

    def switch_numKeys(self):
        self.numKeys.set(3 - self.numKeys.get())
        self.numKeys_button.config(text=f"Switch number of keys (current: {self.numKeys.get()})")
        self.save_settings()
        logging.info(f"Number of keys switched to {self.numKeys.get()}")

    def change_theme(self):
        themes = list(self.themes.keys())
        current_index = themes.index(self.current_theme.get())
        next_index = (current_index + 1) % len(themes)
        self.current_theme.set(themes[next_index])
        self.apply_theme()
        self.save_settings()
        logging.info(f"Theme changed to {self.current_theme.get()}")

    def toggleKeys(self):
        if self.areKeysHeld:
            self.releaseKeys()
            self.areKeysHeld = False
            self.keyStateLabel.config(text="Keys state: Released")
            logging.info("Keys released.")
        else:
            self.holdKeys()
            self.areKeysHeld = True
            self.keyStateLabel.config(text="Keys state: Pressed")
            logging.info("Keys pressed.")

    def holdKeys(self):
        for key in self.keysToHold:
            keyboard.press(key)
            self.play_sound(self.key_press_sound)

    def releaseKeys(self):
        for key in self.keysToHold:
            keyboard.release(key)
            self.play_sound(self.key_release_sound)

    def captureHotkey(self):
        self.isHotkeyCaptured = True
        self.feedbackLabel.config(text="Press the hotkey...")
        self.toggleHotkey_button.config(state=tk.DISABLED)
        logging.info("Started capturing hotkey.")
        keyboard.on_press(self.onKeyPress)

    def onKeyPress(self, key):
        if self.isHotkeyCaptured:
            if hasattr(key, 'name'):
                hotkey = self.normaliseKeyName(key.name)
                self.toggleHotkey.set(hotkey)
                self.hotkeyLabel.config(text=f"Current hotkey: {hotkey}")
                self.isHotkeyCaptured = False
                self.toggleHotkey_button.config(state=tk.NORMAL)
                self.captureKeys_button.config(state=tk.NORMAL)
                self.registerHotkey(hotkey)
                self.save_settings()
                logging.info(f"Hotkey captured: {hotkey}")

    def captureKeys(self):
        self.keysToHold = []
        self.feedbackLabel.config(text="Press the key(s) to hold.")
        logging.info("Started capturing keys.")
        keyboard.hook(self.keyPressCapture)

    def keyPressCapture(self, key):
        if hasattr(key, 'name'):
            keyName = self.normaliseKeyName(key.name)
            if keyName not in self.keysToHold:
                self.keysToHold.append(keyName)
                self.keysToHoldLabel.config(text=f"Keys to hold: {', '.join(self.keysToHold)}")
                self.feedbackLabel.config(text=f"Key captured: {keyName}.")
                logging.info(f"Key captured: {keyName}")
                if len(self.keysToHold) == self.numKeys.get():
                    keyboard.unhook(self.keyPressCapture)
                    self.savePreset_button.config(state=tk.NORMAL)

    def normaliseKeyName(self, keyName):
        return keyName[4:] if keyName.startswith('Key.') else keyName

    def registerHotkey(self, hotkey):
        keyboard.add_hotkey(hotkey, self.toggleKeys)

    def savePreset(self):
        toggleHotkey = self.toggleHotkey.get()
        if not toggleHotkey or not self.keysToHold:
            self.feedbackLabel.config(text="No keys or hotkey to save.")
            self.play_sound(self.error_sound)
            logging.error("No keys or hotkey to save.")
            self.show_error("No keys or hotkey to save.")
            return

        preset_name = simpledialog.askstring("Preset Name", "Enter a name for the preset:")
        if not preset_name:
            self.feedbackLabel.config(text="Preset save cancelled.")
            return

        presets = self.load_presets()
        presets[preset_name] = {"hotkey": toggleHotkey, "keys": self.keysToHold}
        self.save_presets(presets)
        self.feedbackLabel.config(text="Current preset saved.")
        logging.info(f"Preset saved: {preset_name} with hotkey {toggleHotkey} and keys {self.keysToHold}")

    def loadPreset(self):
        presets = self.load_presets()
        if not presets:
            self.feedbackLabel.config(text="No presets available.")
            self.play_sound(self.error_sound)
            logging.error("No presets available.")
            self.show_error("No presets available.")
            return

        preset_name = simpledialog.askstring("Load Preset", "Enter the name of the preset to load:")
        if not preset_name or preset_name not in presets:
            self.feedbackLabel.config(text="Preset not found.")
            self.play_sound(self.error_sound)
            logging.error("Preset not found.")
            self.show_error("Preset not found.")
            return

        preset = presets[preset_name]
        self.toggleHotkey.set(preset["hotkey"])
        self.keysToHold = preset["keys"]
        self.feedbackLabel.config(text=f"Preset loaded: {preset['keys']}.")
        self.hotkeyLabel.config(text=f"Current hotkey: {preset['hotkey']}")
        self.keysToHoldLabel.config(text=f"Keys to hold: {', '.join(self.keysToHold)}")
        logging.info(f"Preset loaded: {preset_name} with hotkey {self.toggleHotkey.get()} and keys {self.keysToHold}")

    def deletePreset(self):
        presets = self.load_presets()
        if not presets:
            self.feedbackLabel.config(text="No presets available.")
            self.play_sound(self.error_sound)
            logging.error("No presets available.")
            self.show_error("No presets available.")
            return

        preset_name = simpledialog.askstring("Delete Preset", "Enter the name of the preset to delete:")
        if not preset_name or preset_name not in presets:
            self.feedbackLabel.config(text="Preset not found.")
            self.play_sound(self.error_sound)
            logging.error("Preset not found.")
            self.show_error("Preset not found.")
            return

        del presets[preset_name]
        self.save_presets(presets)
        self.feedbackLabel.config(text=f"Preset '{preset_name}' deleted.")
        logging.info(f"Preset deleted: {preset_name}")

    def load_presets(self):
        if os.path.isfile(self.presetsFileLocation):
            with open(self.presetsFileLocation, "r") as file:
                return json.load(file)
        else:
            return {}

    def save_presets(self, presets):
        with open(self.presetsFileLocation, "w") as file:
            json.dump(presets, file)

    def save_settings(self):
        settings = {
            "numKeys": self.numKeys.get(),
            "toggleHotkey": self.toggleHotkey.get(),
            "current_theme": self.current_theme.get()
        }
        with open(self.settingsFileLocation, "w") as file:
            json.dump(settings, file)

    def load_settings(self):
        if os.path.isfile(self.settingsFileLocation):
            with open(self.settingsFileLocation, "r") as file:
                self.settings = json.load(file)
        else:
            self.settings = {}

    def show_error(self, message):
        messagebox.showerror("Error", message)

    def show_logs(self):
        log_window = tk.Toplevel(self)
        log_window.title("Logs")
        log_window.geometry("600x400")

        text_area = scrolledtext.ScrolledText(log_window, wrap=tk.WORD, width=80, height=20)
        text_area.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        with open(self.log_filename, "r") as log_file:
            log_content = log_file.read()
            text_area.insert(tk.END, log_content)

        text_area.config(state=tk.DISABLED)

        clear_button = tk.Button(log_window, text="Clear Logs", command=lambda: self.clear_logs(text_area))
        clear_button.pack(pady=10)

    def clear_logs(self, text_area):
        with open(self.log_filename, "w"):
            pass
        logging.info("Logs cleared.")
        text_area.config(state=tk.NORMAL)
        text_area.delete(1.0, tk.END)
        text_area.config(state=tk.DISABLED)
        messagebox.showinfo("Logs", "Logs have been cleared.")

    def show_credits(self):
        credits_window = tk.Toplevel(self)
        credits_window.title("Credits")
        credits_window.geometry("600x400")

        credits_text = (
            "Nova Key Holder\n\n"
            "Developed by BaptistSec\n"
            "Libraries Used:\n"
            "- tkinter (Python Standard Library)\n"
            "- pygame\n"
            "- keyboard\n"
            "- json\n"
            "- os\n"
            "- logging\n"
            "- webbrowser\n"
            "- RotatingFileHandler (logging.handlers)\n"
            "\n"
            "Special thanks to all the developers of these libraries and the Python community."
        )

        text_area = scrolledtext.ScrolledText(credits_window, wrap=tk.WORD, width=80, height=20)
        text_area.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
        text_area.insert(tk.END, credits_text)
        text_area.config(state=tk.DISABLED)

    def show_changelog(self):
        if os.path.isfile(self.changelog_filename):
            with open(self.changelog_filename, "r") as file:
                changelog = json.load(file)
        else:
            changelog = {}

        current_version_log = changelog.get(self.version, "No changelog available for this version.")

        changelog_window = tk.Toplevel(self)
        changelog_window.title("Changelog")
        changelog_window.geometry("600x400")

        changelog_text = f"Version {self.version} Changelog:\n\n{current_version_log}\n\n"

        for version, log in changelog.items():
            if version != self.version:
                changelog_text += f"Version {version}:\n{log}\n\n"

        text_area = scrolledtext.ScrolledText(changelog_window, wrap=tk.WORD, width=80, height=20)
        text_area.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
        text_area.insert(tk.END, changelog_text)
        text_area.config(state=tk.DISABLED)

        acknowledge_button = tk.Button(changelog_window, text="Acknowledge", command=changelog_window.destroy)
        acknowledge_button.pack(pady=10)

    def check_for_updates(self):
        try:
            response = requests.get("https://api.github.com/repos/BaptistSec/NovaKeyHolder/releases/latest")
            latest_release = response.json()
            latest_version = latest_release["tag_name"]

            if self.version < latest_version:
                update_message = f"A new version ({latest_version}) is available. Please visit the GitHub repository to download the latest version."
                logging.info(update_message)
                messagebox.showinfo("Update Available", update_message)
            else:
                messagebox.showinfo("No Updates", "You are using the latest version.")
        except Exception as e:
            logging.error("Error checking for updates: %s", e)
            self.show_error("Error checking for updates. Please try again later.")

    def on_resize(self, event):
        for widget in self.winfo_children():
            if isinstance(widget, tk.Toplevel):
                continue
            widget.grid_configure(sticky="ew")

if __name__ == "__main__":
    log_filename = 'keyholder.log'
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s - %(levelname)s - %(message)s',
                        handlers=[RotatingFileHandler(log_filename, maxBytes=10000, backupCount=3)])
    app = KeyHolderApp()
    app.mainloop()
