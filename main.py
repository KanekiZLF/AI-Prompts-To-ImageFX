import customtkinter as ctk
import os
import tempfile
import atexit
import shutil
import random
import requests
import webbrowser
import sys
import json
import base64
from packaging import version
from tkinter import filedialog
from PIL import Image
import threading
import re
from CTkMessagebox import CTkMessagebox

# --- INFORMAÇÕES DO PROGRAMA ---
__version__ = "2.3.0"
# URL CORRETA para o arquivo de texto puro
VERSION_URL = "https://raw.githubusercontent.com/KanekiZLF/PrismaFX---Gerador-ImageFX-em-Lote/refs/heads/master/version.txt"
UPDATE_URL = "https://github.com/KanekiZLF/PrismaFX---Gerador-ImageFX-em-Lote"
YOUTUBE_TUTORIAL_URL = "https://www.youtube.com/watch?v=SEU_VIDEO_ID"
LICENSE_TEXT = """
Licença de Uso e Termos de Serviço do PrismaFX
Copyright (c) 2025 PrismaFX & Luiz F. R. Pimentel

Este software é licenciado sob os termos da Licença MIT, detalhada abaixo.

---

A permissão é concedida, gratuitamente, a qualquer pessoa que obtenha uma cópia deste software e dos arquivos de documentação associados (o "Software"), para negociar o Software sem restrições, incluindo, sem limitação, os direitos de:

• Usar o software para qualquer finalidade (pessoal, comercial, etc.).
• Copiar, modificar e mesclar cópias do software.
• Publicar, distribuir, sublicenciar e/ou vender cópias do Software.

A única condição é que o aviso de direitos autorais acima e este aviso de permissão sejam incluídos em todas as cópias ou partes substanciais do Software.

---

AVISO SOBRE A API NÃO OFICIAL

PrismaFX depende de uma API não oficial para se comunicar com os serviços do Google ImageFX. Este programa não possui afiliação, patrocínio ou endosso do Google.

Como a API não é pública ou documentada, ela pode ser alterada ou desativada pelo Google a qualquer momento, sem aviso prévio, o que faria este programa parar de funcionar permanentemente. Ao usar este software, você reconhece e aceita este risco integralmente.

---

O SOFTWARE É FORNECIDO "COMO ESTÁ" (AS IS)

Este software é disponibilizado sem nenhuma garantia, expressa ou implícita, incluindo, mas não se limitando a, garantias de comercialização, adequação a um propósito específico e não violação de direitos.

LIMITAÇÃO DE RESPONSABILIDADE

EM NENHUMA CIRCUNSTÂNCIA OS AUTORES OU DETENTORES DOS DIREITOS AUTORAIS SERÃO RESPONSÁVEIS POR QUALQUER REIVINDICAÇÃO, DANOS OU OUTRA RESPONSABILIDADE, SEJA EM UMA AÇÃO DE CONTRATO, DELITO OU DE OUTRA FORMA, DECORRENTE DE, OU EM CONEXÃO COM O SOFTWARE OU O USO OU OUTRAS NEGOCIAÇÕES NO SOFTWARE.
"""

# --- FUNÇÃO HELPER PARA ENCONTRAR ARQUIVOS (ASSETS) ---
def resource_path(relative_path):
    """ Obtém o caminho absoluto para o recurso, funciona para dev e para PyInstaller """
    try:
        # PyInstaller cria uma pasta temp e armazena o caminho em _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

def get_config_path(filename="config.json"):
    """
    Obtém o caminho para um arquivo de configuração na pasta AppData do usuário.
    Cria a pasta do aplicativo se ela não existir.
    """
    # Encontra a pasta AppData\Roaming, que é o local padrão para configs
    app_data_path = os.getenv('APPDATA')
    if app_data_path is None:
        # Se não encontrar AppData (raro), usa a pasta home do usuário como alternativa
        app_data_path = os.path.expanduser("~")

    # Cria o caminho para a pasta específica do nosso app
    app_folder = os.path.join(app_data_path, "PrismaFX")

    # Cria a pasta se ela não existir
    os.makedirs(app_folder, exist_ok=True)

    # Retorna o caminho completo para o arquivo de configuração
    return os.path.join(app_folder, filename)



# --- CLASSE DYNAMIC COMBOBOX ---
class DynamicComboBox(ctk.CTkComboBox):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._is_open = False
        self.bind("<Button-1>", self._toggle_dropdown, add="+")

    def _open_dropdown(self):
        # Sobrescrevemos o método de abrir para atualizar nosso estado
        super()._open_dropdown()
        self._is_open = True

    def _close_dropdown(self):
        # Sobrescrevemos o método de fechar para atualizar nosso estado
        super()._close_dropdown()
        self._is_open = False

    def _toggle_dropdown(self, event):
        if self._is_open:
            self._close_dropdown()  # Fecha o menu se estiver aberto
            return "break"        # Impede que o evento de clique padrão tente reabri-lo
        else:
            # Se estiver fechado, a ação padrão do CTkComboBox vai abrir o menu
            pass

# --- APLICAÇÃO PRINCIPAL ---
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class ImageFXApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        # --- CONTROLE DA JANELA DE DOAÇÃO ---
        # Variável para ligar/desligar a funcionalidade (True = ligada, False = desligada)
        self.ENABLE_DONATION_REMINDER = True
        
        # Carrega a configuração do arquivo JSON
        self.config = self._load_config()

        # Incrementa o contador de execuções
        self.config["execution_count"] += 1
        count = self.config["execution_count"]

        # Verifica se deve mostrar a janela de "Sobre" para doação
        if self.ENABLE_DONATION_REMINDER and not self.config.get("user_has_donated", False):
            # Mostra na primeira e na quinta execução
            if count == 1 or count == 5: # Lógica simplificada para o ciclo
                # Usamos 'after' para garantir que a janela principal apareça primeiro
                self.after(100, self.show_about_window)

        # <<< NOVA LÓGICA: Reseta o contador se ele atingir 5 >>>
        if count >= 5:
            self.config["execution_count"] = 0

        # Salva a configuração atualizada no arquivo JSON
        self._save_config()

        # Salva a configuração atualizada no arquivo JSON
        self._save_config()
        # --- FIM DO CONTROLE ---
        self.title("PrismaFX - Gerador ImageFX em Lote")
        try:
            # Usa nossa função helper para encontrar o ícone na pasta 'assets'
            icon_path = resource_path("assets/icon.ico")
            self.iconbitmap(icon_path)
        except Exception as e:
            # Se o ícone não for encontrado ou houver um erro, o programa não quebra
            print(f"Erro ao carregar o ícone: {e}")
            print("Verifique se o arquivo 'icon.ico' está na pasta 'assets'.")
        self._editable_fg_color = ("#F0F0F0", "#272525")
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
        self.cancel_requested = False # "Bandeira" para sinalizar o cancelamento
        self.image_display_frame = None
        self.image_display_frame = None # Frame que conterá as imagens
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
        self.auth_token_entry = ctk.CTkEntry(auth_frame, placeholder_text="Cole o seu token aqui", fg_color=self._editable_fg_color)
        self.auth_token_entry.grid(row=0, column=0, sticky="ew")
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
        
        ctk.CTkLabel(prompt_options_frame, text="Quantidade de Prompts:").pack(side="left", padx=(0,5))
        
        self.prompt_count_var = ctk.StringVar(value="1")
        # Aumentamos o range da combobox para 50
        self.prompt_count_menu = DynamicComboBox(prompt_options_frame, 
                                                 variable=self.prompt_count_var,
                                                 values=[str(i) for i in range(1, 51)],
                                                 command=self.validate_and_update_prompts,
                                                 fg_color=self._editable_fg_color,
                                                 width=80)
        self.prompt_count_menu.pack(side="left", padx=5)
        self.prompt_count_menu.bind("<Return>", self.validate_and_update_prompts)

        # Botão para carregar prompts de um arquivo de texto
        self.load_button = ctk.CTkButton(prompt_options_frame, text="Carregar de TXT", command=self.load_prompts_from_txt, fg_color="#28A745", hover_color="#218838")
        self.load_button.pack(side="left", padx=(10, 0))

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
        self.ratio_var = ctk.StringVar(value="Quadrado (1:1)")
        self.ratio_menu = DynamicComboBox(options_frame, variable=self.ratio_var, values=["Quadrado (1:1)", "Retrato (9:16)", "Paisagem (16:9)"], state="readonly")
        self.ratio_menu.grid(row=1, column=0, padx=10, pady=(0,10), sticky="ew")
        self._ratio_menu_default_state = self.ratio_menu.cget("state")
        ctk.CTkLabel(options_frame, text="Imagens por Prompt").grid(row=0, column=1, padx=10, pady=(5,0), sticky="w")
        self.count_var = ctk.StringVar(value="1")
        self.count_menu = DynamicComboBox(options_frame, variable=self.count_var, values=["1", "2", "3", "4"], state="readonly")
        self.count_menu.grid(row=1, column=1, padx=10, pady=(0,10), sticky="ew")
        self._count_menu_default_state = self.count_menu.cget("state")
        ctk.CTkLabel(options_frame, text="Seed").grid(row=2, column=0, padx=10, pady=(5,0), sticky="w")
        self.seed_var = ctk.StringVar()
        self.seed_entry = ctk.CTkEntry(options_frame, textvariable=self.seed_var, 
                                       fg_color=self._editable_fg_color)
        self.seed_entry.grid(row=3, column=0, padx=10, pady=(0,10), sticky="ew")
        self.seed_lock_var = ctk.BooleanVar(value=False)
        self.seed_lock_checkbox = ctk.CTkCheckBox(options_frame, text="Travar Seed", variable=self.seed_lock_var, command=self.toggle_seed_lock)
        self.seed_lock_checkbox.grid(row=3, column=1, padx=10, pady=(0,10), sticky="w")
        
        # 1. Criamos o frame container
        self.action_button_frame = ctk.CTkFrame(bottom_frame, fg_color="transparent")
        self.action_button_frame.pack(fill="x", pady=5)
        self.action_button_frame.grid_columnconfigure(0, weight=1)

        # 2. Criamos os dois botões, com o mesmo frame como pai
        self.generate_button = ctk.CTkButton(self.action_button_frame, text="Gerar Todas as Imagens", command=self.start_generation_sequence, height=40)
        self.cancel_button = ctk.CTkButton(self.action_button_frame, text="Cancelar Geração", command=self.cancel_generation, height=40, fg_color="red", hover_color="#CC0000")

        # 3. Posicionamos AMBOS na mesma célula do grid (row=0, column=0)
        self.generate_button.grid(row=0, column=0, sticky="ew")
        self.cancel_button.grid(row=0, column=0, sticky="ew")

        # 4. Trazemos o botão "Gerar" para a FRENTE por padrão
        self.generate_button.lift()

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
    
    # <<< SUBSTITUA O MÉTODO ANTIGO POR ESTE >>>
    def load_prompts_from_txt(self):
        """Abre uma janela para o usuário selecionar um arquivo .txt e carrega os prompts."""
        
        file_path = filedialog.askopenfilename(
            title="PrismaFX - Selecione um arquivo de prompts (.txt)",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )

        if not file_path:
            return

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            prompts_list = []
            current_prompt_lines = []

            # Itera por todas as linhas do arquivo
            for line in lines:
                # Usa regex para encontrar o padrão "Prompt X –" de forma flexível
                if re.match(r'^\s*Prompt \d+\s*–', line, re.IGNORECASE):
                    # Se encontrarmos um novo prompt, salvamos o anterior que estávamos montando
                    if current_prompt_lines:
                        full_prompt = " ".join(current_prompt_lines).strip()
                        prompts_list.append(full_prompt)
                    current_prompt_lines = [] # Limpa para o novo prompt
                else:
                    # Se não for uma linha de título, é uma linha de conteúdo
                    line_content = line.strip()
                    if line_content: # Ignora linhas vazias
                        current_prompt_lines.append(line_content)
            
            # Adiciona o último prompt que estava sendo montado
            if current_prompt_lines:
                full_prompt = " ".join(current_prompt_lines).strip()
                prompts_list.append(full_prompt)

            # --- Validação dos dados carregados ---
            if not prompts_list:
                CTkMessagebox(title="Erro de Formato", message="Nenhum prompt válido encontrado no arquivo.\nVerifique se o formato é 'Prompt 1 – ...'", icon="cancel")
                return

            num_prompts = len(prompts_list)

            if num_prompts > 50:
                prompts_list = prompts_list[:50]
                num_prompts = 50
                CTkMessagebox(title="Aviso", message="O arquivo continha mais de 50 prompts. Apenas os 50 primeiros foram carregados.", icon="warning")

            # --- Atualiza o estado do programa ---
            self.prompt_data_list = [""] * 50
            for i, prompt in enumerate(prompts_list):
                self.prompt_data_list[i] = prompt
            
            self.prompt_count_var.set(str(num_prompts))
            self.validate_and_update_prompts()

            CTkMessagebox(title="Sucesso", message=f"{num_prompts} prompts foram carregados com sucesso!")

        except Exception as e:
            CTkMessagebox(title="Erro Inesperado", message=f"Ocorreu um erro ao carregar o arquivo:\n{e}", icon="cancel")

    def cancel_generation(self):
        """Sinaliza para o processo de geração que um cancelamento foi solicitado."""
        if not self.cancel_requested:
            self.cancel_requested = True
            self.status_label.configure(text="Cancelando... Aguardando o prompt atual terminar.")
            self.cancel_button.configure(state="disabled", text="Aguarde...")

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
        help_win.title("PrismaFX - Como Obter o Token de Autenticação")
        help_win.geometry("550x480") # Aumentamos um pouco a altura
        help_win.transient(self)
        help_win.grab_set()
        help_win.minsize(550, 480)
        help_win.maxsize(550, 480)

        js_script = 'let script = document.querySelector("#__NEXT_DATA__");\nlet obj = JSON.parse(script.textContent);\nconsole.log(obj.props.pageProps.session.access_token);'
        
        def copy_script_to_clipboard():
            self.clipboard_clear()
            self.clipboard_append(js_script)
            copy_button.configure(text="Copiado!")
            self.after(2000, lambda: copy_button.configure(text="Copiar Código para o Console"))

        ctk.CTkLabel(help_win, text="Passo a Passo para Obter o Token", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(10, 15))

        instructions_frame = ctk.CTkFrame(help_win, fg_color="transparent")
        instructions_frame.pack(fill="x", padx=20)

        # <<< BOTÃO PARA O VÍDEO ADICIONADO AQUI >>>
        video_button = ctk.CTkButton(instructions_frame, text="▶️ Como Obter o Token (YouTube)", 
                                     command=lambda: webbrowser.open_new(YOUTUBE_TUTORIAL_URL))
        video_button.pack(fill="x", pady=(0, 15))

        # --- O resto das instruções continua igual ---
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

    # Janela de "Sobre"
    def show_about_window(self):
        about_win = ctk.CTkToplevel(self)
        about_win.withdraw()
        about_win.title("Sobre o PrismaFX") # Nome do projeto atualizado
        about_win.transient(self)
        about_win.grab_set()

        window_width = 600
        window_height = 700
        
        # Centraliza a janela
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        center_x = int(screen_width / 2 - window_width / 2)
        center_y = int(screen_height / 2 - window_height / 2)
        about_win.geometry(f"{window_width}x{window_height}+{center_x}+{center_y}")
        about_win.minsize(window_width, window_height)
        about_win.maxsize(window_width, window_height) 

        about_win.grid_columnconfigure(0, weight=1)
        about_win.grid_rowconfigure(0, weight=1)

        main_frame = ctk.CTkScrollableFrame(about_win)
        main_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        main_frame.grid_columnconfigure(0, weight=1)
        
        header_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        header_frame.pack(fill="x", padx=10, pady=(10, 10))
        title_label = ctk.CTkLabel(header_frame, text="PrismaFX - Gerador ImageFX em Lote", font=ctk.CTkFont(size=20, weight="bold"))
        title_label.pack()
        version_label = ctk.CTkLabel(header_frame, text=f"Versão {__version__}", font=ctk.CTkFont(size=12))
        version_label.pack()
        
        dev_label = ctk.CTkLabel(main_frame, text="Desenvolvido por: Luiz F. R. Pimentel", font=ctk.CTkFont(size=14, weight="bold"))
        dev_label.pack(pady=0)
        description_text = "Uma ferramenta de automação para otimizar a criação de imagens em lote, potencializada pela tecnologia ImageFX do Google Labs."
        description_label = ctk.CTkLabel(main_frame, text=description_text, wraplength=480, justify="center")
        description_label.pack(padx=20)
        
        donation_frame = ctk.CTkFrame(main_frame)
        donation_frame.pack(fill="x", padx=20, pady=10)
        donation_frame.grid_columnconfigure(0, weight=1)
        donation_title = ctk.CTkLabel(donation_frame, text="Apoie este Projeto", font=ctk.CTkFont(size=13, weight="bold"))
        donation_title.pack(pady=5)
        try:
            qrcode_path = resource_path("assets/qrcode_pix.png")
            pil_image = Image.open(qrcode_path)
            qrcode_image = ctk.CTkImage(light_image=pil_image, size=(160, 160))
            qrcode_label = ctk.CTkLabel(donation_frame, image=qrcode_image, text="")
            qrcode_label.pack(pady=5)
            donation_text_label = ctk.CTkLabel(donation_frame, text="Escaneie o QR Code para fazer um PIX", wraplength=400)
            donation_text_label.pack(pady=8)
        except FileNotFoundError:
            error_label = ctk.CTkLabel(donation_frame, text="Erro: qrcode_pix.png não encontrado na pasta 'assets'.", text_color="red")
            error_label.pack(pady=15, padx=10)
        
        notice_frame = ctk.CTkFrame(main_frame, border_width=1)
        notice_frame.pack(fill="x", padx=20)
        notice_title = ctk.CTkLabel(notice_frame, text="Aviso Importante", font=ctk.CTkFont(size=13, weight="bold"))
        notice_title.pack(pady=(10, 5))
        notice_text = (
            "Este programa utiliza uma API **não oficial** e não possui afiliação com o Google.\n\n"
            "A ferramenta pode parar de funcionar a qualquer momento. Use por sua conta e risco."
        )
        notice_label = ctk.CTkLabel(notice_frame, text=notice_text, wraplength=480, justify="left")
        notice_label.pack(pady=(0, 15), padx=15)

        links_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        links_frame.pack(fill="x", padx=20, pady=20)
        links_frame.grid_columnconfigure((0, 1), weight=1)

        github_url = "https://github.com/KanekiZLF/PrismaFX---Gerador-ImageFX-em-Lote" 
        github_button = ctk.CTkButton(links_frame, text="Ver Projeto no GitHub", command=lambda: webbrowser.open_new(github_url))
        github_button.grid(row=0, column=0, padx=5, sticky="ew")

        imagefx_url = "https://labs.google/fx/pt/tools/image-fx"
        imagefx_button = ctk.CTkButton(links_frame, text="Acessar ImageFX Oficial", command=lambda: webbrowser.open_new(imagefx_url))
        imagefx_button.grid(row=0, column=1, padx=5, sticky="ew")

        video_button_about = ctk.CTkButton(links_frame, text="▶️ Como Usar o PrismaFX (YouTube)", 
                                           command=lambda: webbrowser.open_new(YOUTUBE_TUTORIAL_URL))
        # Ocupa as duas colunas na linha de baixo para centralizar
        video_button_about.grid(row=1, column=0, columnspan=2, padx=5, pady=(10,0), sticky="ew")

        close_button = ctk.CTkButton(main_frame, text="Fechar", command=about_win.destroy, width=120)
        close_button.pack(pady=(10, 15))
        
        about_win.deiconify()

    # Tela de Licença
    def show_license_window(self):
        license_win = ctk.CTkToplevel(self)
        license_win.title("PrismaFX - Licença e Termos de Uso")
        
        # Aumentamos o tamanho da janela para o novo texto
        window_width = 600
        window_height = 650
        
        # Centraliza a janela
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        center_x = int(screen_width / 2 - window_width / 2)
        center_y = int(screen_height / 2 - window_height / 2)
        license_win.geometry(f"{window_width}x{window_height}+{center_x}+{center_y}")
        license_win.minsize(window_width, window_height)
        license_win.maxsize(window_width, window_height)
        license_win.transient(self)
        license_win.grab_set()

        ctk.CTkLabel(license_win, text="Licença de Uso e Termos de Serviço", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(15, 10))
        
        textbox = ctk.CTkTextbox(license_win, wrap="word")
        textbox.pack(fill="both", expand=True, padx=15, pady=5)
        textbox.insert("1.0", LICENSE_TEXT)
        textbox.configure(state="disabled") # Bloqueia a edição
        
        ctk.CTkButton(license_win, text="Fechar", command=license_win.destroy).pack(pady=15)

    def clear_current_prompt(self):
        prompt_index = self.current_prompt_page
        the_textbox = self.prompt_text_widgets[0]['textbox']
        the_textbox.delete("1.0", "end")
        self.prompt_data_list[prompt_index] = ""
        self.status_label.configure(text=f"Prompt {prompt_index + 1} Limpo.")

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
    
    # Verificação de Atualizações

    def start_update_check(self):
        """Inicia a verificação de atualização em uma thread separada para não congelar a UI."""
        self.status_label.configure(text="Verificando atualizações...")
        # Desabilita o menu para evitar múltiplas verificações
        self.settings_menu.configure(state="disabled")
        
        thread = threading.Thread(target=self.check_for_updates)
        thread.daemon = True
        thread.start()

    def check_for_updates(self):
        """Busca a versão mais recente no GitHub e compara com a versão local."""
        try:
            # Faz a requisição para a URL do arquivo de versão com um timeout
            headers = {'User-Agent': 'PrismaFX-Update-Checker/1.0'}
            response = requests.get(VERSION_URL, timeout=5, headers=headers)
            response.raise_for_status()  # Lança um erro se a resposta não for 200 (OK)
            
            latest_version_str = response.text.strip()
            local_version_str = __version__

            # Compara as versões usando a biblioteca packaging
            if version.parse(latest_version_str) > version.parse(local_version_str):
                # Se houver uma nova versão, pergunta ao usuário se ele quer atualizar
                msg = CTkMessagebox(
                    title="PrismaFX - Atualização Disponível",
                    message=f"Uma nova versão ({latest_version_str}) está disponível!\nSua versão é {local_version_str}.\n\nDeseja abrir a página de download?",
                    icon="question", option_1="Não", option_2="Sim"
                )
                if msg.get() == "Sim":
                    webbrowser.open_new(UPDATE_URL)
                self.status_label.configure(text="Atualização disponível. Visite a página para baixar.")
            else:
                # Se o usuário já tem a versão mais recente
                CTkMessagebox(title="PrismaFX - Atualizado !", message=f"Você já está com a versão mais recente do PrismaFX ({local_version_str}).")
                self.status_label.configure(text="Pronto.")

        except requests.RequestException as e:
            # Se houver um erro de rede ou de acesso
            CTkMessagebox(title="Erro de Rede", message=f"Não foi possível verificar as atualizações.\n\nErro: {e}", icon="cancel")
            self.status_label.configure(text="Falha ao verificar atualizações.")
        
        finally:
            # Reabilita o menu de configurações, independentemente do resultado
            self.settings_menu.configure(state="readonly")

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
    
    # <<< MÉTODO ATUALIZADO >>>
    def run_generation_sequence(self, prompts, auth_token, regeneration_index=None):
        if regeneration_index is None: self.all_results = [[] for _ in prompts]
        
        auth_error_occurred = False
        
        try:
            for i, prompt_text in enumerate(prompts):
                if self.cancel_requested:
                    self.status_label.configure(text="Geração cancelada pelo usuário.")
                    break

                current_index = regeneration_index if regeneration_index is not None else i
                self.status_label.configure(text=f"A gerar Prompt {current_index + 1} de {len(prompts)}...")
                prompt_data = {"prompt": prompt_text, "ratio": self.ratio_var.get(), "count": self.count_var.get(), "auth_token": auth_token}
                
                new_image_paths = self.generate_single_prompt(prompt_data, current_index)

                if new_image_paths == 'AUTH_ERROR':
                    self.status_label.configure(text="Falha na autenticação. Geração cancelada.")
                    auth_error_occurred = True
                    break

                if not self.cancel_requested:
                    self.after(0, self.update_ui_after_prompt, current_index, new_image_paths or [])
            
            if not self.cancel_requested and not auth_error_occurred:
                self.status_label.configure(text="Geração concluída!")

        finally:
            self.cancel_requested = False
            # Chama a NOVA função para restaurar a UI corretamente
            self._update_ui_for_generation_end()

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
            "Quadrado (1:1)": "IMAGE_ASPECT_RATIO_SQUARE",
            "Retrato (9:16)": "IMAGE_ASPECT_RATIO_PORTRAIT",
            "Paisagem (16:9)": "IMAGE_ASPECT_RATIO_LANDSCAPE"
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
                self.after(0, lambda: CTkMessagebox(title="PrismaFX - Erro de Autenticação (401)", message="Seu token de autenticação é inválido ou expirou.\n\nPor favor, obtenha um novo token e cole-o no campo apropriado.", icon="cancel"))
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
        # Limpa o frame antigo de imagens, se ele existir
        if self.image_display_frame is not None:
            self.image_display_frame.destroy()

        self.current_page_index = page_index
        if not self.all_results: 
            return

        # Cria um novo frame container para as novas imagens
        # Este frame fica DENTRO do CTkScrollableFrame
        self.image_display_frame = ctk.CTkFrame(self.images_scroll_frame, fg_color="transparent")
        self.image_display_frame.pack(fill="both", expand=True)
        self.image_display_frame.grid_columnconfigure((0, 1), weight=1)

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

                # Adiciona o label de imagem ao NOVO frame container
                img_label = ctk.CTkLabel(self.image_display_frame, image=ctk_img, text="")

                row, col = divmod(i, 2)
                img_label.grid(row=row, column=col, padx=10, pady=10)

            except Exception as e: 
                print(f"Erro ao carregar a imagem {img_path}: {e}")
                
    def next_page(self):
        if self.current_page_index < len(self.all_results) - 1: self.show_page(self.current_page_index + 1)

    def prev_page(self):
        if self.current_page_index > 0: self.show_page(self.current_page_index - 1)

    def save_images(self):
        paths_to_save = self.all_results[self.current_page_index]
        if not paths_to_save:
            CTkMessagebox(title="PrismaFX - Nenhuma imagem", message="Não há imagens nesta página para salvar.", icon="warning")
            return
        dest_folder = filedialog.askdirectory(title="PrismaFX - Selecione uma pasta para salvar as imagens")
        if not dest_folder: return
        try:
            for src_path in paths_to_save: shutil.copy2(src_path, dest_folder)
            CTkMessagebox(title="PrismaFX - Sucesso", message=f"{len(paths_to_save)} imagem(ns) salvas com sucesso!")
        except Exception as e:
            CTkMessagebox(title="PrismaFX - Erro ao Salvar", message=f"Erro: {e}", icon="cancel")

    # <<< NOVO MÉTODO >>>
    def _update_ui_for_generation_end(self):
        """Restaura a interface ao estado correto após a geração terminar ou ser cancelada."""
        # Restaura o estado dos widgets de entrada
        self.auth_token_entry.configure(state="normal")
        self.prompt_count_menu.configure(state="normal") # Este é editável
        
        # Restaura o estado original dos menus 'readonly'
        self.ratio_menu.configure(state=self._ratio_menu_default_state)
        self.count_menu.configure(state=self._count_menu_default_state)
        
        for widget_dict in self.prompt_text_widgets:
            widget_dict['textbox'].configure(state="normal")

        # Alterna de volta para o botão "Gerar"
        self.cancel_button.grid_forget()
        self.generate_button.grid(row=0, column=0, sticky="ew")
        self.generate_button.configure(state="normal")
        
        # Reabilita botões de navegação e salvamento se houver resultados
        if self.all_results:
            self.show_page(self.current_page_index)

    # <<< MÉTODO ATUALIZADO >>>
    def set_ui_state(self, generating: bool):
        """Gerencia a UI APENAS para o início da geração, desabilitando os controles."""
        if not generating:
            # Esta função não deve mais ser usada para reabilitar a UI.
            # A nova função _update_ui_for_generation_end() fará isso.
            return

        state = "disabled"
        
        # Desabilita todos os controles
        self.auth_token_entry.configure(state=state)
        self.prompt_count_menu.configure(state=state)
        self.ratio_menu.configure(state=state)
        self.count_menu.configure(state=state)
        for widget_dict in self.prompt_text_widgets:
            widget_dict['textbox'].configure(state=state)

        # Alterna a visibilidade dos botões Gerar/Cancelar
        self.generate_button.grid_forget()
        self.cancel_button.grid(row=0, column=0, sticky="ew")
        self.cancel_button.configure(state="normal", text="Cancelar Geração")
        
        # Desabilita botões de navegação
        self.prev_button.configure(state=state)
        self.next_button.configure(state=state)
        self.save_button.configure(state=state)
        self.regenerate_current_button.configure(state=state)

    # Salva as configurações em um arquivo JSON
    def _load_config(self):
        """Carrega as configurações de um arquivo JSON de forma robusta."""
        default_config = {
            "header": "ARQUIVO DE CONFIGURACAO DO PRISMAFX - NAO EDITE MANUALMENTE",
            "execution_count": 0,
        }
        
        # <<< ALTERADO: Usa a nova função para encontrar o arquivo de config >>>
        config_file_path = get_config_path()

        try:
            with open(config_file_path, "r") as f:
                loaded_config = json.load(f)
            
            sanitized_config = default_config.copy()
            count = loaded_config.get("execution_count")
            if isinstance(count, int) and count >= 0:
                sanitized_config["execution_count"] = count
            
            donated = loaded_config.get("user_has_donated")
            if isinstance(donated, bool):
                sanitized_config["user_has_donated"] = donated

            return sanitized_config

        except (FileNotFoundError, json.JSONDecodeError, TypeError):
            return default_config
        
    def _save_config(self):
            """Salva as configurações atuais em um arquivo JSON."""
            # <<< ALTERADO: Usa a nova função para encontrar o arquivo de config >>>
            config_file_path = get_config_path()
            with open(config_file_path, "w") as f:
                json.dump(self.config, f, indent=4)

if __name__ == "__main__":
    app = ImageFXApp()
    try:
        app.mainloop()
    except KeyboardInterrupt:
        print("\nPrograma encerrado pelo usuário.")
        app.destroy()