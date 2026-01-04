import customtkinter as ctk
import os
import threading
import requests
import re
import time
import json
from typing import List

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class MinecraftDownloaderApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("MC Ultimate Downloader")
        self.geometry("600x800")
        self.resizable(True, True)

        self.stop_event = threading.Event()
        self.pause_event = threading.Event()
        self.pause_event.set()
        self.is_running = False
        
        self.api_key = self.load_api_key()
        
        self.versions_vars = [ctk.StringVar() for _ in range(3)]
        self.loaders_vars = {
            "Fabric": ctk.BooleanVar(value=True),
            "Forge": ctk.BooleanVar(value=False),
            "NeoForge": ctk.BooleanVar(value=False),
            "Quilt": ctk.BooleanVar(value=False)
        }
        self.types_vars = {
            "mods": ctk.BooleanVar(value=True),
            "resourcepacks": ctk.BooleanVar(value=False),
            "datapacks": ctk.BooleanVar(value=False)
        }
        self.smart_search_var = ctk.BooleanVar(value=True)
        
        self.loader_widgets = []
        
        self.overlay_frame = None
        
        self.setup_ui()
        
        if not self.api_key:
            self.after(200, self.show_api_overlay)

    def load_api_key(self):
        try:
            if os.path.exists(".secret_key"):
                with open(".secret_key", "r") as f:
                    key = f.read().strip()
                    return key if key else None
        except:
            pass
        return None

    def save_api_key_to_file(self, key):
        try:
            with open(".secret_key", "w") as f:
                f.write(key)
        except:
            pass

    def create_overlay_base(self):
        if self.overlay_frame:
            self.overlay_frame.destroy()
        
        self.overlay_frame = ctk.CTkFrame(self, fg_color="#101010", corner_radius=0)
        self.overlay_frame.place(relx=0, rely=0, relwidth=1, relheight=1)
        self.overlay_frame.bind("<Button-1>", lambda e: "break")

    def show_api_overlay(self):
        self.create_overlay_base()

        dialog_frame = ctk.CTkFrame(self.overlay_frame, width=500, height=350, fg_color="#2b2b2b", corner_radius=10, border_width=2, border_color="#3b8ed0")
        dialog_frame.place(relx=0.5, rely=0.5, anchor="center")
        dialog_frame.pack_propagate(False)

        close_btn = ctk.CTkButton(dialog_frame, text="X", width=30, height=30, fg_color="gray", hover_color="#505050", command=self.show_warning_overlay)
        close_btn.place(relx=0.92, rely=0.05)

        ctk.CTkLabel(dialog_frame, text="Enter OpenRouter API Key", font=("Roboto", 18, "bold")).pack(pady=(20, 10))

        entry_key = ctk.CTkEntry(dialog_frame, width=400, placeholder_text="sk-or-...")
        entry_key.pack(pady=10)
        
        def right_click_paste(event):
            try:
                clipboard = self.clipboard_get()
                entry_key.insert(ctk.INSERT, clipboard)
            except:
                pass
        
        entry_key.bind("<Button-3>", right_click_paste)
        entry_key.bind("<Control-v>", lambda e: None) 

        instructions = (
            "To get key, follow these instructions:\n\n"
            "openrouter.ai -> “Register” -> Get API Key ->\n"
            "Create API Key -> “Enter any name” -> Create\n\n"
            "Once the key appears, copy and paste it into the\n"
            "program without sharing it anywhere.\n"
            "This is necessary for better smart research performance."
        )

        ctk.CTkLabel(dialog_frame, text=instructions, font=("Roboto", 12), text_color="silver").pack(pady=10)

        def save_and_close():
            key = entry_key.get().strip()
            if key:
                self.api_key = key
                self.save_api_key_to_file(key)
                self.overlay_frame.destroy()
                self.overlay_frame = None

        ctk.CTkButton(dialog_frame, text="Save & Continue", fg_color="#2CC985", hover_color="#229C68", command=save_and_close).pack(pady=10)

    def show_warning_overlay(self):
        self.create_overlay_base()
        
        warn_frame = ctk.CTkFrame(self.overlay_frame, width=450, height=250, fg_color="#2b2b2b", corner_radius=10, border_width=2, border_color="#D63D3D")
        warn_frame.place(relx=0.5, rely=0.5, anchor="center")
        warn_frame.pack_propagate(False)

        ctk.CTkLabel(warn_frame, text="⚠️ Warning", font=("Roboto", 20, "bold"), text_color="#D63D3D").pack(pady=(20, 10))

        msg = "If you do not enter the key, search performance\nmay deteriorate. We strongly recommend that you do so!\nIt is not difficult and it is free."
        ctk.CTkLabel(warn_frame, text=msg, font=("Roboto", 13), text_color="white").pack(pady=10)

        btn_box = ctk.CTkFrame(warn_frame, fg_color="transparent")
        btn_box.pack(pady=20)

        def go_back():
            self.show_api_overlay()

        def confirm_no_key():
            self.api_key = None
            self.smart_search_var.set(False)
            self.overlay_frame.destroy()
            self.overlay_frame = None

        ctk.CTkButton(btn_box, text="Return", fg_color="#3B8ED0", width=100, command=go_back).pack(side="left", padx=10)
        ctk.CTkButton(btn_box, text="Okay", fg_color="transparent", border_width=1, border_color="white", width=100, command=confirm_no_key).pack(side="left", padx=10)

    def setup_ui(self):
        self.main_frame = ctk.CTkScrollableFrame(self, width=580, height=780)
        self.main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        lbl_title = ctk.CTkLabel(self.main_frame, text="MC Ultimate Downloader", font=("Roboto Medium", 24))
        lbl_title.pack(pady=(10, 20))

        ver_frame = ctk.CTkFrame(self.main_frame)
        ver_frame.pack(fill="x", pady=5)
        ctk.CTkLabel(ver_frame, text="Game Versions (filling in all 3 fields is optional):", font=("Roboto", 14, "bold")).pack(anchor="w", padx=10, pady=5)
        
        for i, var in enumerate(self.versions_vars):
            ctk.CTkEntry(ver_frame, textvariable=var, placeholder_text=f"Version {i+1} (e.g. 1.21.1)").pack(fill="x", padx=10, pady=2)

        settings_frame = ctk.CTkFrame(self.main_frame)
        settings_frame.pack(fill="x", pady=10)

        grid_frame = ctk.CTkFrame(settings_frame, fg_color="transparent")
        grid_frame.pack(fill="x", padx=10, pady=10)

        type_col = ctk.CTkFrame(grid_frame, fg_color="transparent")
        type_col.pack(side="left", fill="both", expand=True)
        ctk.CTkLabel(type_col, text="Content Type", font=("Roboto", 14, "bold")).pack(anchor="w")
        
        self.chk_mods = ctk.CTkCheckBox(type_col, text="Mods", variable=self.types_vars["mods"], command=self.toggle_loaders_state)
        self.chk_mods.pack(anchor="w", pady=2)
        ctk.CTkCheckBox(type_col, text="Resource Packs", variable=self.types_vars["resourcepacks"]).pack(anchor="w", pady=2)
        ctk.CTkCheckBox(type_col, text="Datapacks", variable=self.types_vars["datapacks"]).pack(anchor="w", pady=2)

        loader_col = ctk.CTkFrame(grid_frame, fg_color="transparent")
        loader_col.pack(side="right", fill="both", expand=True)
        
        self.lbl_loaders = ctk.CTkLabel(loader_col, text="Loaders:", font=("Roboto", 14, "bold"))
        self.lbl_loaders.pack(anchor="w")
        self.loader_widgets.append(self.lbl_loaders)

        for name, var in self.loaders_vars.items():
            cb = ctk.CTkCheckBox(loader_col, text=name, variable=var)
            cb.pack(anchor="w", pady=2)
            self.loader_widgets.append(cb)

        adv_frame = ctk.CTkFrame(self.main_frame)
        adv_frame.pack(fill="x", pady=5)
        ctk.CTkSwitch(adv_frame, text="Smart Research", variable=self.smart_search_var).pack(pady=10)

        self.textbox_log = ctk.CTkTextbox(self.main_frame, height=200, font=("Consolas", 12))
        self.textbox_log.pack(fill="x", pady=10)
        
        self.textbox_log.tag_config("center", justify="center")
        
        self.textbox_log.insert("0.0", "--- Ready ---\nFill 'mods_list.txt', 'rp_list.txt', or/and 'dp_list.txt'\n", "center")
        self.textbox_log.configure(state="disabled")

        btn_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        btn_frame.pack(fill="x", pady=10)

        self.btn_start = ctk.CTkButton(btn_frame, text="START", fg_color="#2CC985", hover_color="#229C68", command=self.start_thread, width=150)
        self.btn_start.pack(side="left", padx=5)

        self.btn_pause = ctk.CTkButton(btn_frame, text="PAUSE", fg_color="#E0A800", hover_color="#B08400", command=self.toggle_pause, state="disabled", width=150)
        self.btn_pause.pack(side="left", padx=5)

        self.btn_stop = ctk.CTkButton(btn_frame, text="STOP", fg_color="#D63D3D", hover_color="#A82A2A", command=self.stop_process, state="disabled", width=150)
        self.btn_stop.pack(side="left", padx=5)
        
        self.toggle_loaders_state()

    def toggle_loaders_state(self):
        is_mods = self.types_vars["mods"].get()
        state = "normal" if is_mods else "disabled"
        
        for widget in self.loader_widgets:
            if isinstance(widget, ctk.CTkLabel):
                widget.configure(text_color=("black", "white") if is_mods else "gray")
            elif isinstance(widget, ctk.CTkCheckBox):
                widget.configure(state=state)
                widget.configure(text_color=("black", "white") if is_mods else "gray30")

    def log(self, message):
        self.textbox_log.configure(state="normal")
        self.textbox_log.insert("end", message + "\n", "center")
        self.textbox_log.see("end")
        self.textbox_log.configure(state="disabled")

    def start_thread(self):
        if self.is_running: return

        versions = [v.get().strip() for v in self.versions_vars if v.get().strip()]
        loaders = [k for k, v in self.loaders_vars.items() if v.get()]
        types = [k for k, v in self.types_vars.items() if v.get()]
        smart_mode = self.smart_search_var.get()

        if not versions:
            self.log("!!! Error: Specify at least one version.")
            return
        if not types:
            self.log("!!! Error: Select a content type.")
            return
        if "mods" in types and not loaders:
            self.log("!!! Error: Select at least one loader for mods.")
            return

        self.is_running = True
        self.stop_event.clear()
        self.pause_event.set()
        
        self.btn_start.configure(state="disabled")
        self.btn_pause.configure(state="normal", text="PAUSE")
        self.btn_stop.configure(state="normal")
        
        self.textbox_log.configure(state="normal")
        self.textbox_log.delete("1.0", "end")
        self.textbox_log.configure(state="disabled")

        thread = threading.Thread(target=self.process_downloads, args=(versions, types, loaders, smart_mode))
        thread.start()

    def toggle_pause(self):
        if self.pause_event.is_set():
            self.pause_event.clear()
            self.btn_pause.configure(text="RESUME", fg_color="#3B8ED0")
            self.log("\n--- PAUSED ---\n")
        else:
            self.pause_event.set()
            self.btn_pause.configure(text="PAUSE", fg_color="#E0A800")
            self.log("\n--- RESUMED ---\n")

    def stop_process(self):
        if self.is_running:
            self.stop_event.set()
            self.pause_event.set()
            self.log("\n!!! STOPPING... Please wait.")

    def reset_ui_state(self):
        self.is_running = False
        self.btn_start.configure(state="normal")
        self.btn_pause.configure(state="disabled", text="PAUSE", fg_color="#E0A800")
        self.btn_stop.configure(state="disabled")

    def check_flow_control(self):
        if self.stop_event.is_set():
            return "stop"
        
        if not self.pause_event.is_set():
            while not self.pause_event.is_set():
                if self.stop_event.is_set(): return "stop"
                time.sleep(0.5)
        return "ok"

    def clean_name(self, raw_name: str) -> str:
        name = raw_name.lower()
        name = name.replace(".jar", "").replace(".zip", "")
        name = re.sub(r'fabric|forge|quilt|neoforge|snaphot|release', '', name)
        name = re.sub(r'v\s*\d+', '', name)
        name = re.sub(r'\bmc\b', '', name)
        name = re.sub(r'\.x\b', '', name)
        name = re.sub(r'[0-9\-\.\+\(\)]', ' ', name)
        return " ".join(name.split())

    def validate_ai_match(self, original: str, found: str) -> bool:
        if not self.api_key: return True
        try:
            prompt_content = (
                f"Original User Request: '{original}'. Found Modrinth Project Name: '{found}'. "
                "Context: Minecraft Mods/ResourcePacks. "
                "Do these two names represent the same project, or is the found project strictly related to the request? "
                "Reply EXACTLY with 'YES' or 'NO'."
            )
            
            response = requests.post(
                url="https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                data=json.dumps({
                    "model": "xiaomi/mimo-v2-flash:free",
                    "messages": [
                        {
                            "role": "system", 
                            "content": "You are a strict logic validator. Reply ONLY with YES or NO."
                        },
                        {
                            "role": "user",
                            "content": prompt_content
                        }
                    ],
                    "reasoning": {"enabled": False}
                }),
                timeout=10
            )

            if response.status_code == 200:
                content = response.json()['choices'][0]['message']['content'].strip().upper()
                return "YES" in content
            return False
        except:
            return False

    def get_ai_suggestions(self, raw_text: str, content_type: str) -> List[str]:
        if not self.api_key: return []
        try:
            prompt_content = (
                f"Input string: '{raw_text}'. Content Type: {content_type}. "
                "Analyze the input description or messy filename. "
                "Output ONLY a JSON list of 3 strings. "
                "Each string must consist of EXACTLY 2 words that represent the most likely official project name. "
                "Do not add any explanations."
            )

            response = requests.post(
                url="https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                data=json.dumps({
                    "model": "xiaomi/mimo-v2-flash:free",
                    "messages": [
                        {
                            "role": "system", 
                            "content": (
                                "You are a precise keyword extractor. "
                                "Your task is to turn messy Minecraft file names into clean 2-word project names."
                                "Do not use the words “datapack,” “mods,” or “resourcepack” in your attempts; instead, use a generalized name."
                                "Output strict JSON format: [\"Word1 Word2\", \"Word3 Word4\"]."
                            )
                        },
                        {
                            "role": "user",
                            "content": prompt_content
                        }
                    ],
                    "reasoning": {"enabled": False}
                }),
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                content = data['choices'][0]['message']['content']
                content = content.replace("```json", "").replace("```", "")
                match = re.search(r'\[.*\]', content, re.DOTALL)
                if match:
                    json_str = match.group(0)
                    return json.loads(json_str)
            return []
        except:
            return []

    def get_loader_filter(self, content_type: str, loader_name: str) -> str:
        if content_type == "mods":
            return loader_name.lower()
        elif content_type == "datapacks":
            return "datapack"
        elif content_type == "resourcepacks":
            return "minecraft"
        return ""

    def search_modrinth_smart(self, query: str, version: str, content_type: str, loader: str, save_path: str, validation_original: str = None) -> str:
        base_url = "https://api.modrinth.com/v2"
        headers = {'User-Agent': 'MC-Ultimate-Downloader/Merged-Version'}
        
        if content_type == "mods":
            facet_type = "mod"
        elif content_type == "resourcepacks":
            facet_type = "resourcepack"
        else:
            facet_type = "datapack"

        params = {
            'query': query,
            'limit': 1,
            'facets': f'[["project_type:{facet_type}"], ["versions:{version}"]]'
        }

        try:
            r = requests.get(f"{base_url}/search", params=params, headers=headers)
            r.raise_for_status()
            data = r.json()
            hits = data.get('hits', [])

            if not hits:
                params_broad = {
                    'query': query,
                    'limit': 3,
                    'facets': f'[["project_type:{facet_type}"]]'
                }
                r2 = requests.get(f"{base_url}/search", params=params_broad, headers=headers)
                hits = r2.json().get('hits', [])

            if not hits:
                return "not_found"

            for project in hits:
                project_id = project['project_id']
                project_slug = project['slug']
                project_title = project['title']
                
                if validation_original and self.api_key:
                    is_valid = self.validate_ai_match(validation_original, project_title)
                    if not is_valid:
                        self.log(f"    [AI-CHECK] '{project_title}' does not match '{validation_original}'. Skipping.")
                        continue
                    else:
                        self.log(f"    [AI-CHECK] Match confirmed: {project_title}")

                v_params = {'game_versions': f'["{version}"]'}
                
                target_loader = self.get_loader_filter(content_type, loader)
                if target_loader:
                    v_params['loaders'] = f'["{target_loader}"]'
                
                rv = requests.get(f"{base_url}/project/{project_id}/version", params=v_params, headers=headers)
                
                versions_data = []
                if rv.status_code == 200:
                    versions_data = rv.json()
                
                if not versions_data and content_type in ["datapacks", "resourcepacks"]:
                    self.log(f"    ~ Strict version {version} not found. Trying loose search for {content_type}...")
                    v_params_loose = {} 
                    if target_loader:
                        v_params_loose['loaders'] = f'["{target_loader}"]'
                    
                    rv_loose = requests.get(f"{base_url}/project/{project_id}/version", params=v_params_loose, headers=headers)
                    if rv_loose.status_code == 200:
                        versions_data = rv_loose.json()

                if versions_data:
                    target_file = None
                    required_extension = ".jar" if content_type == "mods" else ".zip"
                    
                    found_version = versions_data[0] 
                    
                    for file_obj in found_version['files']:
                        if file_obj['filename'].endswith(required_extension):
                            target_file = file_obj
                            break
                    
                    if not target_file:
                        self.log(f"    [SKIP] No file with extension {required_extension} found for {project_slug}.")
                        return "error"

                    file_url = target_file['url']
                    filename = target_file['filename']
                    
                    type_label = loader if content_type == 'mods' else ('RP' if content_type == 'resourcepacks' else 'DP')
                    self.log(f"--> Downloading: {project_slug} [{type_label}]")
                    
                    resp = requests.get(file_url, stream=True)
                    full_path = os.path.join(save_path, filename)
                    
                    if os.path.exists(full_path):
                            self.log(f"    [SKIP] File already exists.")
                            return "success"

                    with open(full_path, 'wb') as f:
                        for chunk in resp.iter_content(chunk_size=8192):
                            if self.stop_event.is_set(): return "error"
                            f.write(chunk)
                    
                    self.log(f"    [OK] Saved.")
                    return "success"
            
            return "not_found"

        except Exception as e:
            self.log(f"!!! Network/API Error: {e}")
            return "error"

    def process_downloads(self, versions: List[str], types: List[str], loaders: List[str], smart_mode: bool):
        self.log(f"=== STARTED ===")
        
        for ver in versions:
            for c_type in types:
                task_loaders = loaders if c_type == "mods" else ["any"]
                
                if c_type == "mods": filename = "mods_list.txt"
                elif c_type == "resourcepacks": filename = "rp_list.txt"
                else: filename = "dp_list.txt"

                if not os.path.exists(filename):
                    self.log(f"[SKIP] File {filename} not found.")
                    continue
                
                with open(filename, "r", encoding="utf-8") as f:
                    lines = [l.strip() for l in f.readlines() if l.strip()]

                for loader in task_loaders:
                    if self.check_flow_control() == "stop": break

                    base_folder = os.path.join(os.getcwd(), "Downloads", ver, c_type)
                    target_folder = base_folder
                    if c_type == "mods":
                        target_folder = os.path.join(base_folder, loader)
                    
                    os.makedirs(target_folder, exist_ok=True)
                    
                    header_loader = f"[{loader}]" if c_type == "mods" else ("[RP]" if c_type == "resourcepacks" else "[DP]")
                    self.log(f"\n>>> Ver: {ver} | Type: {c_type} {header_loader}")

                    for raw_line in lines:
                        if self.check_flow_control() == "stop": break
                        
                        clean_query = self.clean_name(raw_line)
                        if not clean_query: continue
                        
                        result = self.search_modrinth_smart(clean_query, ver, c_type, loader, target_folder)
                        
                        if result == "success":
                            continue
                        elif result == "not_found":
                            if smart_mode and self.api_key:
                                self.log(f"    ~ Analogs not found. Trying Smart Research (AI)...")
                                ai_queries = self.get_ai_suggestions(raw_line, c_type)
                                found_via_ai = False
                                for ai_q in ai_queries:
                                    if self.check_flow_control() == "stop": break
                                    self.log(f"    ? AI suggests: {ai_q}")
                                    res_ai = self.search_modrinth_smart(ai_q, ver, c_type, loader, target_folder, validation_original=raw_line)
                                    if res_ai == "success":
                                        found_via_ai = True
                                        break
                                if not found_via_ai:
                                    self.log("    [FAIL] Not found via AI.")
                            else:
                                if smart_mode and not self.api_key:
                                    self.log("    [WARN] Smart Mode enabled but no API Key provided.")
                                self.log(f"    [FAIL] '{clean_query}' not found.")
                        elif result == "error":
                            pass

            if self.stop_event.is_set(): break
        
        if self.stop_event.is_set():
            self.log("\n!!! INTERRUPTED !!!")
        else:
            self.log("\n=== ALL TASKS COMPLETED ===")
        
        self.reset_ui_state()

if __name__ == "__main__":
    app = MinecraftDownloaderApp()
    app.mainloop()
