import tkinter as tk
import webbrowser
import keyboard
import json
import os


class KeyHolderApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('Nova Key Holder')
        self.geometry('440x330')

        # Variables
        self.keys_to_hold = []
        self.num_keys = tk.IntVar(value=1)
        self.toggle_hotkey = tk.StringVar()
        self.keys_are_held = False
        self.is_capturing_hotkey = False
        self.presets_file = "key_presets.json"

        # GUI elements
        self.num_keys_button = tk.Button(self, text="Switch number of keys (current: 1)", command=self.switch_num_keys)
        self.toggle_hotkey_button = tk.Button(self, text="Capture Hotkey", command=self.capture_hotkey)
        self.hotkey_display_label = tk.Label(self, text="")
        self.capture_keys_button = tk.Button(self, text="Capture Keys", command=self.capture_keys, state=tk.DISABLED)
        self.save_preset_button = tk.Button(self, text="Save Preset", command=self.save_preset, state=tk.DISABLED)
        self.load_preset_button = tk.Button(self, text="Load Preset", command=self.load_preset)
        self.feedback_label = tk.Label(self, text="")
        self.keys_state_label = tk.Label(self, text="Keys state: Released")

        # GitHub link
        self.github_link = tk.Label(self, text="Developed by BaptistSec", cursor="hand2", fg="blue")
        self.github_link.bind("<Button-1>", lambda e: webbrowser.open_new("https://github.com/BaptistSec"))

        # Placement
        self.num_keys_button.grid(row=0, column=0, padx=10, pady=10)
        self.toggle_hotkey_button.grid(row=1, column=0, padx=10, pady=10)
        self.hotkey_display_label.grid(row=1, column=1, padx=10, pady=10)
        self.capture_keys_button.grid(row=2, column=0, padx=10, pady=10)
        self.save_preset_button.grid(row=3, column=0, padx=10, pady=10)
        self.load_preset_button.grid(row=4, column=0, padx=10, pady=10)
        self.feedback_label.grid(row=2, column=1, padx=10, pady=10)
        self.keys_state_label.grid(row=5, column=0, padx=10, pady=10)
        self.github_link.grid(row=6, column=0, padx=10, pady=10)

        # Hotkey capture state
        self.is_capturing_hotkey = False

    def switch_num_keys(self):
        self.num_keys.set(3 - self.num_keys.get())
        self.num_keys_button.config(text=f"Switch number of keys (current: {self.num_keys.get()})")

    def toggle_keys(self):
        if self.keys_are_held:
            self.release_keys()
            self.keys_are_held = False
            self.keys_state_label.config(text="Keys state: Released")
        else:
            self.hold_keys()
            self.keys_are_held = True
            self.keys_state_label.config(text="Keys state: Pressed")

    def hold_keys(self):
        for key in self.keys_to_hold:
            keyboard.press(key)

    def release_keys(self):
        for key in self.keys_to_hold:
            keyboard.release(key)

    def capture_hotkey(self):
        self.is_capturing_hotkey = True
        self.feedback_label.config(text="Press the hotkey...")
        self.toggle_hotkey_button.config(state=tk.DISABLED)
        keyboard.on_press(self.on_key_press)

    def on_key_press(self, key):
        if self.is_capturing_hotkey:
            if hasattr(key, 'name'):
                hotkey = self.normalize_key_name(key.name)
                self.toggle_hotkey.set(hotkey)
                self.hotkey_display_label.config(text=f"Current hotkey: {hotkey}")
                self.is_capturing_hotkey = False
                self.toggle_hotkey_button.config(state=tk.NORMAL)
                self.capture_keys_button.config(state=tk.NORMAL)
                self.register_hotkey(hotkey)

    def capture_keys(self):
        self.keys_to_hold = []
        num_keys = self.num_keys.get()

        self.feedback_label.config(text="Press the key(s) you want to hold down.")

        def on_key_press_capture(key):
            if hasattr(key, 'name'):
                key_name = self.normalize_key_name(key.name)
                if key_name not in self.keys_to_hold:
                    self.keys_to_hold.append(key_name)
                    self.feedback_label.config(text=f"Key captured: {key_name}.")
                    if len(self.keys_to_hold) == self.num_keys.get():
                        keyboard.unhook(on_key_press_capture)
                        self.save_preset_button.config(state=tk.NORMAL)

                        if num_keys == 2:
                            self.hotkey_display_label.config(text=f"Current hotkey: {self.keys_to_hold[0]} + {self.keys_to_hold[1]}")
                        else:
                            self.hotkey_display_label.config(text=f"Current hotkey: {self.keys_to_hold[0]}")

        keyboard.hook(on_key_press_capture)

    def normalize_key_name(self, key_name):
        if key_name.startswith('Key.'):
            return key_name[4:]
        else:
            return key_name

    def register_hotkey(self, hotkey):
        def callback():
            self.toggle_keys()

        keyboard.add_hotkey(hotkey, callback)

    def save_preset(self):
        toggle_hotkey = self.toggle_hotkey.get()
        if not toggle_hotkey or not self.keys_to_hold:
            self.feedback_label.config(text="No keys or hotkey to save.")
            return

        if os.path.isfile(self.presets_file):
            with open(self.presets_file, "r") as file:
                presets = json.load(file)
        else:
            presets = {}

        presets[toggle_hotkey] = self.keys_to_hold

        with open(self.presets_file, "w") as file:
            json.dump(presets, file)

        self.feedback_label.config(text="Current preset saved.")

    def load_preset(self):
        toggle_hotkey = self.toggle_hotkey.get()
        if not toggle_hotkey:
            self.feedback_label.config(text="Enter a hotkey to load preset.")
            return

        if not os.path.isfile(self.presets_file):
            self.feedback_label.config(text="No presets found.")
            return

        with open(self.presets_file, "r") as file:
            presets = json.load(file)

        if toggle_hotkey not in presets:
            self.feedback_label.config(text="No preset found for this hotkey.")
            return

        self.keys_to_hold = presets[toggle_hotkey]
        self.feedback_label.config(text=f"Preset loaded: {self.keys_to_hold}.")


if __name__ == "__main__":
    app = KeyHolderApp()
    app.mainloop()
