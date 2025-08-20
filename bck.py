import customtkinter as ctk
import os
import tempfile
import atexit
import shutil
import random
import requests
import webbrowser
import json
import base64
from tkinter import filedialog
from PIL import Image
import threading
from CTkMessagebox import CTkMessagebox

# --- INFORMAÇÕES DO PROGRAMA ---
__version__ = "2.6.0"
VERSION_URL = "https://gist.githubusercontent.com/anisio/d54c7286381b16b471696b99b59e74bb/raw/7027877e5d269894982bf0be7341e97486e96906/version.txt"
UPDATE_URL = "https://github.com/anisio"
LICENSE_TEXT = """
MIT License

Copyright (c) 2025 [Seu Nome ou Nome do Projeto]

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN an ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

# --- CLASSE DYNAMIC COMBOBOX ---
class DynamicComboBox(ctk.CTkComboBox):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._is_open = False
        self.bind("<Button-1>", self._toggle_dropdown, add="+")
        if hasattr(self, '_dropdown_menu'):
             self._dropdown_menu.bind("<FocusOut>", self._on_focus_out, add="+")
    def _toggle_dropdown(self, event):
        if self._is_open:
            self.focus_set(); self._is_open = False; return "break"
        else: self._is_open = True
    def _on_focus_out(self, event):
        self._is_open = False

# --- APLICAÇÃO PRINCIPAL ---
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class ImageFXApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Gerador de Imagens ImageFX (em Lote)")
        
        window_width = 900
        window_height = 700
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        center_x = int(screen_width/2 - window_width / 2)
        center_y = int(screen_height/2 - window_height / 2)
        self.geometry(f"{window_width}x{window_height}+{center_x}+{center_y}")
        self.minsize(900, 700)

        self.prompts_per_page = 1
        self.current_prompt_page = 0
        self.prompt_data_list = [""] * 50
        self.prompt_text_widgets = []
        self.temp_dir = tempfile.mkdtemp(prefix="imagefx_app_")
        atexit.register(self.cleanup)
        self.all_results = []
        self.current_page_index = 0
        self.grid_columnconfigure(0, weight=1, minsize=400)
        self.grid_columnconfigure(1, weight=2)
        self.grid_rowconfigure(0, weight=1)
        controls_frame = ctk.CTkFrame(self, corner_radius=10)
        controls_frame.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")
        controls_frame.grid_columnconfigure(0, weight=1)
        controls_frame.grid_rowconfigure(0, weight=0)
        controls_frame.grid_rowconfigure(3, weight=1)
        controls_frame.grid_rowconfigure(4, weight=0)
        top_frame = ctk.CTkFrame(controls_frame, fg_color="transparent")
        top_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=(0, 10))
        top_bar_frame = ctk.CTkFrame(top_frame, fg_color="transparent")
        top_bar_frame.pack(fill="x", pady=(10,5))
        top_bar_frame.grid_columnconfigure(1, weight=1)
        self.settings_var = ctk.StringVar(value="⚙️ Configurações")
        self.settings_menu = DynamicComboBox(top_bar_frame, variable=self.settings_var, 
                                             values=["Verificar Atualizações", "Licença", "Sobre"],
                                             command=self.handle_settings, width=150,
                                             state="readonly")
        self.settings_menu.grid(row=0, column=0, sticky="w")
        self.theme_button = ctk.CTkButton(top_bar_frame, text="", command=self.toggle_theme, width=40)
        self.theme_button.grid(row=0, column=2, sticky="e")
        self.update_theme_button()
        ctk.CTkLabel(top_frame, text="Token de Autenticação (Auth)").pack(anchor="w", padx=10, pady=(10, 5))
        auth_frame = ctk.CTkFrame(top_frame, fg_color="transparent")
        auth_frame.pack(fill="x", padx=10, pady=(0, 5))
        auth_frame.grid_columnconfigure(0, weight=1)
        auth_frame.grid_columnconfigure(1, weight=0)
        self.auth_token_entry = ctk.CTkEntry(auth_frame, placeholder_text="Cole o seu token aqui")
        self.auth_token_entry.grid(row=0, column=0, sticky="ew")
        self._editable_fg_color = self.auth_token_entry.cget("fg_color")
        self.token_help_button = ctk.CTkButton(auth_frame, text="?", width=30, command=self.show_token_help)
        self.token_help_button.grid(row=0, column=1, padx=(5, 0))
        self._default_border_color = self.auth_token_entry.cget("border_color")
        self.auth_token_entry.bind("<KeyRelease>", self._reset_token_entry_style)
        prompts_outer_frame = ctk.CTkFrame(controls_frame)
        prompts_outer_frame.grid(row=3, column=0, padx=10, sticky="nsew")
        prompts_outer_frame.grid_columnconfigure(0, weight=1)
        prompts_outer_frame.grid_rowconfigure(0, weight=1)
        self.prompts_container_frame = ctk.CTkFrame(prompts_outer_frame, fg_color="transparent")
        self.prompts_container_frame.grid(row=0, column=0, sticky="nsew")
        prompt_nav_frame = ctk.CTkFrame(prompts_outer_frame)
        prompt_nav_frame.grid(row=1, column=0, sticky="ew", pady=(5,0))
        prompt_nav_frame.grid_columnconfigure(1, weight=1)
        self.prompt_prev_button = ctk.CTkButton(prompt_nav_frame, text="< Anterior", command=self._prev_prompt_page)
        self.prompt_prev_button.grid(row=0, column=0, padx=5, pady=5)
        self.prompt_page_label = ctk.CTkLabel(prompt_nav_frame, text="Página 1 de 1")
        self.prompt_page_label.grid(row=0, column=1)
        self.prompt_next_button = ctk.CTkButton(prompt_nav_frame, text="Próximo >", command=self._next_prompt_page)
        self.prompt_next_button.grid(row=0, column=2, padx=5, pady=5)
        bottom_frame = ctk.CTkFrame(controls_frame, fg_color="transparent")
        bottom_frame.grid(row=4, column=0, sticky="ew", padx=10, pady=10)
        prompt_options_frame = ctk.CTkFrame(bottom_frame, fg_color="transparent")
        prompt_options_frame.pack(fill="x", pady=5)
        ctk.CTkLabel(prompt_options_frame, text="Quantidade de Prompts:").pack(side="left")
        self.prompt_count_var = ctk.StringVar(value="1")
        self.prompt_count_menu = DynamicComboBox(prompt_options_frame, 
                                                 variable=self.prompt_count_var,
                                                 values=[str(i) for i in range(1, 15)],
                                                 command=self.validate_and_update_prompts,
                                                 fg_color=self._editable_fg_color)
        self.prompt_count_menu.pack(side="left", padx=10)
        self.prompt_count_menu.bind("<Return>", self.validate_and_update_prompts)
        clipboard_buttons_frame = ctk.CTkFrame(bottom_frame)
        clipboard_buttons_frame.pack(fill="x", pady=5)
        clipboard_buttons_frame.grid_columnconfigure((0, 1), weight=1)
        self.clear_button = ctk.CTkButton(clipboard_buttons_frame, text="Limpar Prompt Atual", command=self.clear_current_prompt)
        self.clear_button.grid(row=0, column=0, padx=(0, 5), sticky="ew")
        self.paste_button = ctk.CTkButton(clipboard_buttons_frame, text="Colar no Prompt Atual", command=self.paste_to_current_prompt)
        self.paste_button.grid(row=0, column=1, padx=(5, 0), sticky="ew")
        options_frame = ctk.CTkFrame(bottom_frame)
        options_frame.pack(fill="x", pady=5)
        options_frame.grid_columnconfigure((0, 1), weight=1)
        ctk.CTkLabel(options_frame, text="Proporção").grid(row=0, column=0, padx=10, pady=(5,0), sticky="w")
        self.ratio_var = ctk.StringVar(value="Square (1:1)")
        self.ratio_menu = DynamicComboBox(options_frame, variable=self.ratio_var, values=["Square (1:1)", "Portrait (9:16)", "Landscape (16:9)"], state="readonly")
        self.ratio_menu.grid(row=1, column=0, padx=10, pady=(0,10), sticky="ew")
        ctk.CTkLabel(options_frame, text="Imagens por Prompt").grid(row=0, column=1, padx=10, pady=(5,0), sticky="w")
        self.count_var = ctk.StringVar(value="1")
        self.count_menu = DynamicComboBox(options_frame, variable=self.count_var, values=["1", "2", "3", "4"], state="readonly")
        self.count_menu.grid(row=1, column=1, padx=10, pady=(0,10), sticky="ew")
        ctk.CTkLabel(options_frame, text="Seed").grid(row=2, column=0, padx=10, pady=(5,0), sticky="w")
        self.seed_var = ctk.StringVar()
        self.seed_entry = ctk.CTkEntry(options_frame, textvariable=self.seed_var, 
                                       fg_color=self._editable_fg_color)
        self.seed_entry.grid(row=3, column=0, padx=10, pady=(0,10), sticky="ew")
        self.seed_lock_var = ctk.BooleanVar(value=False)
        self.seed_lock_checkbox = ctk.CTkCheckBox(options_frame, text="Travar Seed", variable=self.seed_lock_var, command=self.toggle_seed_lock)
        self.seed_lock_checkbox.grid(row=3, column=1, padx=10, pady=(0,10), sticky="w")
        self.generate_button = ctk.CTkButton(bottom_frame, text="Gerar Todas as Imagens", command=self.start_generation_sequence, height=40)
        self.generate_button.pack(fill="x", pady=5)
        secondary_buttons_frame = ctk.CTkFrame(bottom_frame, fg_color="transparent")
        secondary_buttons_frame.pack(fill="x", pady=5)
        secondary_buttons_frame.grid_columnconfigure((0,1), weight=1)
        self.regenerate_current_button = ctk.CTkButton(secondary_buttons_frame, text="Regerar Atual", command=self.start_regenerate_current, state="disabled", height=40)
        self.regenerate_current_button.grid(row=0, column=0, padx=(0,5), sticky="ew")
        self.save_button = ctk.CTkButton(secondary_buttons_frame, text="Salvar Página...", command=self.save_images, state="disabled", height=40)
        self.save_button.grid(row=0, column=1, padx=(5,0), sticky="ew")
        self.status_label = ctk.CTkLabel(bottom_frame, text="Pronto.", wraplength=350)
        self.status_label.pack(fill="x", pady=5)
        display_frame = ctk.CTkFrame(self, fg_color="transparent")
        display_frame.grid(row=0, column=1, padx=(0, 20), pady=20, sticky="nsew")
        display_frame.grid_rowconfigure(0, weight=1)
        display_frame.grid_columnconfigure(0, weight=1)
        self.images_scroll_frame = ctk.CTkScrollableFrame(display_frame, label_text="Resultado do Prompt: 1")
        self.images_scroll_frame.grid(row=0, column=0, sticky="nsew")
        self.images_scroll_frame.grid_columnconfigure((0, 1), weight=1)
        self.image_labels = []
        pagination_frame = ctk.CTkFrame(display_frame)
        pagination_frame.grid(row=1, column=0, pady=(10, 0), sticky="ew")
        pagination_frame.grid_columnconfigure(1, weight=1)
        self.prev_button = ctk.CTkButton(pagination_frame, text="< Anterior", command=self.prev_page, state="disabled")
        self.prev_button.grid(row=0, column=0, padx=10)
        self.page_label = ctk.CTkLabel(pagination_frame, text="Página 0 de 0")
        self.page_label.grid(row=0, column=1)
        self.next_button = ctk.CTkButton(pagination_frame, text="Próximo >", command=self.next_page, state="disabled")
        self.next_button.grid(row=0, column=2, padx=10)
        self._create_prompt_widgets()
        self.validate_and_update_prompts()
        self.bind_all("<Tab>", self._go_to_next_page_on_tab)
        self.bind_all("<Shift-Tab>", self._go_to_prev_page_on_shift_tab)
        self.toggle_seed_lock()

    def _center_window(self, window):
        """Centraliza uma janela (Toplevel) no meio da tela."""
        window.update_idletasks()
        width = window.winfo_width()
        height = window.winfo_height()
        screen_width = window.winfo_screenwidth()
        screen_height = window.winfo_screenheight()
        x = (screen_width // 2) - (width // 2)
        y = (screen_height // 2) - (height // 2)
        window.geometry(f'{width}x{height}+{x}+{y}')

    def show_token_help(self):
        help_win = ctk.CTkToplevel(self)
        help_win.title("Como Obter o Token de Autenticação")
        help_win.geometry("550x420")
        help_win.minsize(550, 420)
        help_win.maxsize(550, 420)
        help_win.transient(self)
        help_win.grab_set()
        js_script = 'let script = document.querySelector("#__NEXT_DATA__");\nlet obj = JSON.parse(script.textContent);\nconsole.log(obj.props.pageProps.session.access_token);'
        def copy_script_to_clipboard():
            self.clipboard_clear()
            self.clipboard_append(js_script)
            copy_button.configure(text="Copiado!")
            self.after(2000, lambda: copy_button.configure(text="Copiar Código para o Console"))
        ctk.CTkLabel(help_win, text="Passo a Passo para Obter o Token", font=("", 16, "bold")).pack(pady=(10, 15))
        instructions_frame = ctk.CTkFrame(help_win, fg_color="transparent")
        instructions_frame.pack(fill="x", padx=20)
        ctk.CTkButton(instructions_frame, text="1. Abra o site do ImageFX no seu navegador", command=lambda: webbrowser.open_new("https://labs.google/fx/pt/tools/image-fx")).pack(fill="x", pady=4)
        ctk.CTkLabel(instructions_frame, text="2. No site, pressione a tecla F12 para abrir as Ferramentas de Desenvolvedor.", justify="left").pack(anchor="w", pady=4)
        ctk.CTkLabel(instructions_frame, text="3. Vá para a aba 'Console'.", justify="left").pack(anchor="w", pady=4)
        ctk.CTkLabel(instructions_frame, text="4. Copie o código abaixo e cole no console. Pressione Enter.", justify="left").pack(anchor="w", pady=4)
        code_textbox = ctk.CTkTextbox(help_win, height=80, wrap="word")
        code_textbox.pack(fill="x", padx=20, pady=5)
        code_textbox.insert("1.0", js_script)
        code_textbox.configure(state="disabled")
        copy_button = ctk.CTkButton(help_win, text="Copiar Código para o Console", command=copy_script_to_clipboard)
        copy_button.pack(pady=8, padx=20)
        ctk.CTkLabel(help_win, text="5. O token será exibido. Copie e cole no campo de autenticação do programa.", justify="left", wraplength=500).pack(anchor="w", padx=20, pady=4)
        ctk.CTkButton(help_win, text="Fechar", command=help_win.destroy).pack(side="bottom", pady=15)
        self._center_window(help_win)

    def show_about_window(self):
        about_win = ctk.CTkToplevel(self)
        about_win.title("Sobre o Gerador ImageFX")
        about_win.geometry("400x250"); about_win.transient(self); about_win.grab_set()
        about_win.minsize(400, 250)
        about_win.maxsize(400, 250)
        ctk.CTkLabel(about_win, text="Gerador ImageFX em Lote", font=("", 16, "bold")).pack(pady=(10,5))
        ctk.CTkLabel(about_win, text=f"Versão {__version__}").pack()
        ctk.CTkLabel(about_win, text="Este programa utiliza a API não oficial do ImageFX\npara gerar imagens em massa.", justify="center").pack(pady=10)
        ctk.CTkButton(about_win, text="Fechar", command=about_win.destroy).pack(pady=20)
        self._center_window(about_win)

    def show_license_window(self):
        license_win = ctk.CTkToplevel(self)
        license_win.title("Licença")
        license_win.geometry("500x400"); license_win.transient(self); license_win.grab_set()
        license_win.minsize(500, 400)
        license_win.maxsize(500, 400)
        ctk.CTkLabel(license_win, text="Licença de Uso (MIT)", font=("", 16, "bold")).pack(pady=(10,5))
        textbox = ctk.CTkTextbox(license_win, wrap="word")
        textbox.pack(fill="both", expand=True, padx=10, pady=5)
        textbox.insert("1.0", LICENSE_TEXT)
        textbox.configure(state="disabled")
        ctk.CTkButton(license_win, text="Fechar", command=license_win.destroy).pack(pady=10)
        self._center_window(license_win)

    def clear_current_prompt(self):
        prompt_index = self.current_prompt_page
        the_textbox = self.prompt_text_widgets[0]['textbox']
        the_textbox.delete("1.0", "end")
        self.prompt_data_list[prompt_index] = ""
        self.status_label.configure(text=f"Prompt {prompt_index + 1} limpo.")

    def paste_to_current_prompt(self):
        try:
            clipboard_content = self.clipboard_get()
            prompt_index = self.current_prompt_page
            the_textbox = self.prompt_text_widgets[0]['textbox']
            the_textbox.delete("1.0", "end")
            the_textbox.insert("1.0", clipboard_content)
            self.prompt_data_list[prompt_index] = clipboard_content.strip()
            self.status_label.configure(text=f"Texto colado no Prompt {prompt_index + 1}.")
        except ctk.TclError:
            self.status_label.configure(text="Área de transferência vazia ou sem texto.")

    def _go_to_next_page_on_tab(self, event):
        if self.prompt_next_button.cget("state") == "normal":
            self._next_prompt_page()
        return "break"

    def _go_to_prev_page_on_shift_tab(self, event):
        if self.prompt_prev_button.cget("state") == "normal":
            self._prev_prompt_page()
        return "break"
        
    def _create_prompt_widgets(self):
        self.prompts_container_frame.grid_rowconfigure(0, weight=1)
        self.prompts_container_frame.grid_columnconfigure(0, weight=1)
        entry_frame = ctk.CTkFrame(self.prompts_container_frame)
        entry_frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=(5, 10))
        entry_frame.grid_columnconfigure(0, weight=1)
        entry_frame.grid_rowconfigure(1, weight=1)
        label = ctk.CTkLabel(entry_frame, text="", font=("", 14, "bold"))
        label.grid(row=0, column=0, sticky="w", padx=5, pady=(5, 0))
        textbox = ctk.CTkTextbox(entry_frame)
        textbox.grid(row=1, column=0, pady=(0, 5), padx=5, sticky="nsew")
        textbox.bind("<KeyRelease>", lambda event, idx=0: self._update_prompt_data(event, idx))
        self.prompt_text_widgets.append({'frame': entry_frame, 'label': label, 'textbox': textbox})

    def _display_current_prompt_page(self):
        total_prompts = int(self.prompt_count_var.get())
        prompt_index = self.current_prompt_page
        widget_dict = self.prompt_text_widgets[0]
        widget_dict['label'].configure(text=f"Prompt {prompt_index + 1}:")
        widget_dict['textbox'].delete("1.0", "end")
        widget_dict['textbox'].insert("1.0", self.prompt_data_list[prompt_index])
        self.prompt_page_label.configure(text=f"Prompt {prompt_index + 1} de {total_prompts}")
        self.prompt_prev_button.configure(state="normal" if self.current_prompt_page > 0 else "disabled")
        self.prompt_next_button.configure(state="normal" if self.current_prompt_page < total_prompts - 1 else "disabled")

    def _update_prompt_data(self, event, widget_index_on_page):
        prompt_index = self.current_prompt_page
        widget = self.prompt_text_widgets[0]['textbox']
        self.prompt_data_list[prompt_index] = widget.get("1.0", "end-1c")

    def _next_prompt_page(self):
        total_prompts = int(self.prompt_count_var.get())
        if self.current_prompt_page < total_prompts - 1:
            self.current_prompt_page += 1
            self._display_current_prompt_page()

    def _prev_prompt_page(self):
        if self.current_prompt_page > 0:
            self.current_prompt_page -= 1
            self._display_current_prompt_page()
            
    def validate_and_update_prompts(self, event=None):
        try:
            value = int(self.prompt_count_menu.get())
            if not 1 <= value <= 50:
                value = 10 if value > 10 else 1
                self.prompt_count_var.set(str(value))
        except (ValueError, TypeError):
            value = 1
            self.prompt_count_var.set(str(value))
            self.status_label.configure(text="Erro: Insira um número de 1 a 10.")
        self.current_prompt_page = 0
        self._display_current_prompt_page()
        
    def cleanup(self):
        try: shutil.rmtree(self.temp_dir)
        except Exception as e: print(f"Erro ao limpar pasta temporária: {e}")
    
    def toggle_theme(self):
        new_mode = "Light" if ctk.get_appearance_mode() == "Dark" else "Dark"
        ctk.set_appearance_mode(new_mode)
        self.update_theme_button()
    
    def update_theme_button(self):
        icon = "☀️" if ctk.get_appearance_mode() == "Dark" else "🌙"
        self.theme_button.configure(text=icon)

    def handle_settings(self, choice):
        if choice == "Sobre":
            self.show_about_window()
        elif choice == "Verificar Atualizações":
            self.start_update_check()
        elif choice == "Licença":
            self.show_license_window()
        self.settings_var.set("⚙️ Configurações")
    
    def start_update_check(self):
        self.status_label.configure(text="A verificar atualizações...")
        thread = threading.Thread(target=self.check_for_updates); thread.daemon = True; thread.start()

    def check_for_updates(self):
        try:
            response = requests.get(VERSION_URL, timeout=5)
            response.raise_for_status()
            latest_version = response.text.strip()
            if latest_version > __version__:
                msg = CTkMessagebox(title="Atualização Disponível", 
                                    message=f"Uma nova versão ({latest_version}) está disponível!\nA sua versão é {__version__}.\n\nDeseja abrir a página de download?",
                                    icon="question", option_1="Não", option_2="Sim")
                if msg.get() == "Sim":
                    webbrowser.open_new(UPDATE_URL)
                self.status_label.configure(text="Atualização disponível.")
            else:
                CTkMessagebox(title="Nenhuma Atualização", message=f"Você já tem a versão mais recente! ({__version__})")
                self.status_label.configure(text="Pronto.")
        except requests.RequestException as e:
            CTkMessagebox(title="Erro de Rede", message=f"Não foi possível verificar as atualizações.\nErro: {e}", icon="cancel")
            self.status_label.configure(text="Pronto.")

    def _reset_token_entry_style(self, event=None):
        self.auth_token_entry.configure(border_color=self._default_border_color)

    def toggle_seed_lock(self):
        is_locked = self.seed_lock_var.get()
        if is_locked:
            self.seed_entry.configure(state="disabled", fg_color=("gray85", "gray28"))
        else:
            self.seed_entry.configure(state="normal", fg_color=self._editable_fg_color)

    def start_generation_sequence(self, regeneration_index=None):
        self._reset_token_entry_style()
        auth_token = self.auth_token_entry.get().strip()
        if not auth_token or auth_token == self.auth_token_entry.cget("placeholder_text"):
            self.status_label.configure(text="Erro: Preencha o Token de Autenticação.")
            self.auth_token_entry.configure(border_color="red")
            self.auth_token_entry.focus_set()
            return
        total_prompts_to_generate = int(self.prompt_count_var.get())
        prompts = [p.strip() for p in self.prompt_data_list[:total_prompts_to_generate]]
        if regeneration_index is not None:
            prompts = [self.prompt_data_list[regeneration_index]]
        if not all(prompts):
            self.status_label.configure(text="Erro: Preencha todos os campos de prompt."); return
        self.set_ui_state(generating=True)
        thread = threading.Thread(target=self.run_generation_sequence, args=(prompts, auth_token, regeneration_index))
        thread.daemon = True
        thread.start()

    def start_regenerate_current(self):
        self.start_generation_sequence(regeneration_index=self.current_page_index)
    
    def run_generation_sequence(self, prompts, auth_token, regeneration_index=None):
        if regeneration_index is None: self.all_results = [[] for _ in prompts]
        auth_error_occurred = False
        for i, prompt_text in enumerate(prompts):
            current_index = regeneration_index if regeneration_index is not None else i
            self.status_label.configure(text=f"A gerar Prompt {current_index + 1}...")
            prompt_data = {"prompt": prompt_text, "ratio": self.ratio_var.get(), "count": self.count_var.get(), "auth_token": auth_token}
            new_image_paths = self.generate_single_prompt(prompt_data, current_index)
            if new_image_paths == 'AUTH_ERROR':
                self.status_label.configure(text="Falha na autenticação. Geração cancelada.")
                auth_error_occurred = True
                break
            self.after(0, self.update_ui_after_prompt, current_index, new_image_paths or [])
        if not auth_error_occurred:
            self.status_label.configure(text="Geração concluída!")
        self.set_ui_state(generating=False)

    def update_ui_after_prompt(self, page_index, image_paths):
        self.all_results[page_index] = image_paths
        if self.current_page_index == page_index: self.show_page(page_index)
        self.page_label.configure(text=f"Página {self.current_page_index + 1} de {len(self.all_results)}")

    def generate_single_prompt(self, prompt_data, current_index):
        if current_index < len(self.all_results) and self.all_results[current_index]:
            for path in self.all_results[current_index]:
                try: os.remove(path)
                except OSError: pass
        if not self.seed_lock_var.get():
            new_seed = random.randint(100000, 999999)
            self.seed_var.set(str(new_seed))
        current_seed = 0
        try:
            current_seed = int(self.seed_var.get())
        except (ValueError, TypeError):
            current_seed = random.randint(100000, 999999)
            self.seed_var.set(str(current_seed))
        ratio_map = {
            "Square (1:1)": "IMAGE_ASPECT_RATIO_SQUARE",
            "Portrait (9:16)": "IMAGE_ASPECT_RATIO_PORTRAIT",
            "Landscape (16:9)": "IMAGE_ASPECT_RATIO_LANDSCAPE"
        }
        api_ratio = ratio_map.get(prompt_data["ratio"], "IMAGE_ASPECT_RATIO_SQUARE")
        api_model = "IMAGEN_3_5"
        api_url = "https://aisandbox-pa.googleapis.com/v1:runImageFx"
        headers = {
            "Authorization": f"Bearer {prompt_data['auth_token']}",
            "Content-Type": "application/json",
        }
        payload = {
            "userInput": {
                "candidatesCount": int(prompt_data["count"]),
                "prompts": [prompt_data["prompt"]],
                "seed": current_seed,
            },
            "aspectRatio": api_ratio,
            "modelInput": {"modelNameType": api_model},
            "clientContext": {"sessionId": f";{random.randint(1740000000000, 1799999999999)}", "tool": "IMAGE_FX"},
        }
        try:
            response = requests.post(api_url, headers=headers, json=payload, timeout=120)
            response.raise_for_status()
            response_data = response.json()
            generated_images_data = response_data.get("imagePanels", [{}])[0].get("generatedImages", [])
            if not generated_images_data:
                self.status_label.configure(text=f"Erro no prompt {current_index + 1}: Resposta vazia.")
                return None
            new_image_paths = []
            for i, img_data in enumerate(generated_images_data):
                base64_string = img_data.get("encodedImage")
                if base64_string:
                    image_bytes = base64.b64decode(base64_string)
                    temp_file_path = os.path.join(self.temp_dir, f"prompt_{current_index}_{i}_{random.randint(1000, 9999)}.png")
                    with open(temp_file_path, "wb") as f:
                        f.write(image_bytes)
                    new_image_paths.append(temp_file_path)
            return new_image_paths
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 401:
                self.after(0, lambda: CTkMessagebox(title="Erro de Autenticação (401)", message="Seu token de autenticação é inválido ou expirou.\n\nPor favor, obtenha um novo token e cole-o no campo apropriado.", icon="cancel"))
                return 'AUTH_ERROR'
            else:
                print(f"Erro HTTP ao gerar prompt: {e.response.status_code}\n{e.response.text}")
                self.status_label.configure(text=f"Erro HTTP {e.response.status_code} no prompt {current_index + 1}...")
                return None
        except requests.exceptions.RequestException as e:
            print(f"Erro de rede ao gerar prompt: {e}")
            self.status_label.configure(text=f"Erro de rede no prompt {current_index + 1}...")
            return None

    def show_page(self, page_index):
        for widget in self.image_labels: widget.destroy()
        self.image_labels.clear()
        if not self.all_results: return
        self.current_page_index = page_index
        image_paths_for_page = self.all_results[self.current_page_index]
        self.images_scroll_frame.configure(label_text=f"Resultado do Prompt: {self.current_page_index + 1}")
        self.page_label.configure(text=f"Página {self.current_page_index + 1} de {len(self.all_results)}")
        self.prev_button.configure(state="normal" if self.current_page_index > 0 else "disabled")
        self.next_button.configure(state="normal" if self.current_page_index < len(self.all_results) - 1 else "disabled")
        self.save_button.configure(state="normal" if image_paths_for_page else "disabled")
        self.regenerate_current_button.configure(state="normal")
        self.display_images(image_paths_for_page)

    def display_images(self, image_paths):
        max_dim = 320
        for i, img_path in enumerate(image_paths):
            try:
                img = Image.open(img_path)
                width, height = img.size
                ratio = max_dim / max(width, height)
                new_width = int(width * ratio)
                new_height = int(height * ratio)
                ctk_img = ctk.CTkImage(light_image=img, size=(new_width, new_height))
                img_label = ctk.CTkLabel(self.images_scroll_frame, image=ctk_img, text="")
                row, col = divmod(i, 2)
                img_label.grid(row=row, column=col, padx=10, pady=10)
                self.image_labels.append(img_label)
            except Exception as e: print(f"Erro ao carregar a imagem {img_path}: {e}")

    def next_page(self):
        if self.current_page_index < len(self.all_results) - 1: self.show_page(self.current_page_index + 1)

    def prev_page(self):
        if self.current_page_index > 0: self.show_page(self.current_page_index - 1)

    def save_images(self):
        paths_to_save = self.all_results[self.current_page_index]
        if not paths_to_save:
            CTkMessagebox(title="Nenhuma imagem", message="Não há imagens nesta página para salvar.", icon="warning")
            return
        dest_folder = filedialog.askdirectory(title="Selecione uma pasta para salvar as imagens")
        if not dest_folder: return
        try:
            for src_path in paths_to_save: shutil.copy2(src_path, dest_folder)
            CTkMessagebox(title="Sucesso", message=f"{len(paths_to_save)} imagem(ns) salvas com sucesso!")
        except Exception as e:
            CTkMessagebox(title="Erro ao Salvar", message=f"Erro: {e}", icon="cancel")

    def set_ui_state(self, generating: bool):
        state = "disabled" if generating else "normal"
        self.generate_button.configure(state=state)
        self.auth_token_entry.configure(state=state)
        self.prompt_count_menu.configure(state=state)
        self.ratio_menu.configure(state=state)
        self.count_menu.configure(state=state)
        for widget_dict in self.prompt_text_widgets:
            widget_dict['textbox'].configure(state=state)
        if generating:
            self.prev_button.configure(state="disabled")
            self.next_button.configure(state="disabled")
            self.save_button.configure(state="disabled")
            self.regenerate_current_button.configure(state="disabled")
        else:
            if self.all_results: self.show_page(self.current_page_index)

if __name__ == "__main__":
    app = ImageFXApp()
    try:
        app.mainloop()
    except KeyboardInterrupt:
        print("\nPrograma encerrado pelo usuário.")
        app.destroy()