import customtkinter as ctk
import os
import threading
import requests
import re
import time
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

        self.setup_ui()

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
        ctk.CTkCheckBox(type_col, text="Mods", variable=self.types_vars["mods"]).pack(anchor="w", pady=2)
        ctk.CTkCheckBox(type_col, text="Resource Packs", variable=self.types_vars["resourcepacks"]).pack(anchor="w", pady=2)
        ctk.CTkCheckBox(type_col, text="Datapacks", variable=self.types_vars["datapacks"]).pack(anchor="w", pady=2)

        loader_col = ctk.CTkFrame(grid_frame, fg_color="transparent")
        loader_col.pack(side="right", fill="both", expand=True)
        ctk.CTkLabel(loader_col, text="Loaders:", font=("Roboto", 14, "bold")).pack(anchor="w")
        for name, var in self.loaders_vars.items():
            ctk.CTkCheckBox(loader_col, text=name, variable=var).pack(anchor="w", pady=2)

        adv_frame = ctk.CTkFrame(self.main_frame)
        adv_frame.pack(fill="x", pady=5)
        ctk.CTkSwitch(adv_frame, text="Smart Search (find analogs if original not found)", variable=self.smart_search_var).pack(pady=10)

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

    def clean_name(self, raw_name: str) -> str:
        name = raw_name.lower()
        name = name.replace(".jar", "").replace(".zip", "")
        name = re.sub(r'fabric|forge|quilt|neoforge|snaphot|release', '', name)
        name = re.sub(r'v\s*\d+', '', name)
        name = re.sub(r'\bmc\b', '', name)
        name = re.sub(r'\.x\b', '', name)
        name = re.sub(r'[0-9\-\.\+\(\)]', ' ', name)
        return " ".join(name.split())

    def check_flow_control(self):
        if self.stop_event.is_set():
            return "stop"
        
        if not self.pause_event.is_set():
            while not self.pause_event.is_set():
                if self.stop_event.is_set(): return "stop"
                time.sleep(0.5)
        return "ok"

    def search_modrinth_smart(self, query: str, version: str, content_type: str, loader: str, save_path: str, smart_mode: bool) -> str:
        base_url = "https://api.modrinth.com/v2"
        headers = {'User-Agent': 'MC-Ultimate-Downloader/3.0'}
        
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

            if not hits and smart_mode:
                self.log(f"    ~ Strict search failed. Looking for analogs for '{query}'...")
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
                
                v_params = {'game_versions': f'["{version}"]'}
                
                if content_type == "mods":
                    v_params['loaders'] = f'["{loader.lower()}"]'
                
                rv = requests.get(f"{base_url}/project/{project_id}/version", params=v_params, headers=headers)
                
                if rv.status_code == 200:
                    versions_data = rv.json()
                    if versions_data:
                        target_file = versions_data[0]['files'][0]
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
                        
                        self.log(f"    [OK] Saved to: .../{os.path.basename(save_path)}/")
                        return "success"
            
            return "not_found"

        except Exception as e:
            self.log(f"!!! Network/API Error: {e}")
            return "error"

    def process_downloads(self, versions: List[str], types: List[str], loaders: List[str], smart_mode: bool):
        self.log(f"=== STARTED ===")
        self.log(f"Versions: {versions}")
        self.log(f"Types: {types}")
        if "mods" in types: self.log(f"Loaders: {loaders}")
        
        for ver in versions:
            for c_type in types:
                
                task_loaders = loaders if c_type == "mods" else ["any"]
                
                if c_type == "mods":
                    filename = "mods_list.txt"
                elif c_type == "resourcepacks":
                    filename = "rp_list.txt"
                else:
                    filename = "dp_list.txt"

                if not os.path.exists(filename):
                    self.log(f"\n[SKIP] File {filename} not found.")
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
                    
                    if c_type == "mods":
                        header_loader = f"[{loader}]"
                    elif c_type == "resourcepacks":
                        header_loader = "[RP]"
                    else:
                        header_loader = "[DP]"

                    self.log(f"\n>>> Version: {ver} | Type: {c_type} {header_loader}")

                    for i, raw_line in enumerate(lines):
                        if self.check_flow_control() == "stop": break
                        
                        clean_query = self.clean_name(raw_line)
                        if not clean_query: continue

                        result = self.search_modrinth_smart(clean_query, ver, c_type, loader, target_folder, smart_mode)
                        
                        if result == "not_found":
                            self.log(f"    [FAIL] '{clean_query}' not found (even analogs).")
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