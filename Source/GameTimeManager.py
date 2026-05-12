import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import customtkinter as ctk
import os
import time
from datetime import datetime
import webbrowser
import sqlite3
import sys
import socket
import json

if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Port used for the command line to talk to the GUI
IPC_PORT = 54321

# Set modern theme globally
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")


class Game_Time_Manager:
    def __init__(self, root, initial_cmd=None):
        self.root = root
        self.root.title("Game Time Manager")
        self.root.geometry("1000x550")
        self.root.resizable(False, False)

        self.running = False
        self.start_time = 0
        self.elapsed_time = 0
        self.current_start_str = "--/--/---- --:--:--"
        self.current_end_str = "--/--/---- --:--:--"
        self.game_name_str = ""
        self.current_tags_str = ""

        # --- Database Setup ---
        self.setup_database()

        # --- Layout Frames ---
        self.main_container = ctk.CTkFrame(root, fg_color="transparent")
        self.main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Left Frame
        self.left_frame = ctk.CTkFrame(self.main_container, corner_radius=15)
        self.left_frame.pack(side=tk.LEFT, padx=10, pady=10, fill=tk.Y)

        # Right Frame
        self.right_frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(10, 0))

        # --- Left Frame Widgets (Game Time Manager) ---
        self.game_name_label = ctk.CTkLabel(self.left_frame, text="", font=("Helvetica", 14, "bold"),
                                            text_color="#3a7ebf", wraplength=250)
        self.game_name_label.pack(pady=(15, 0))

        self.tags_label = ctk.CTkLabel(self.left_frame, text="", font=("Helvetica", 11, "italic"), text_color="gray",
                                       wraplength=250)
        self.tags_label.pack()

        self.time_label = ctk.CTkLabel(self.left_frame, text="00:00:00.00", font=("Helvetica", 35, "bold"))
        self.time_label.pack(pady=15, padx=20)

        self.start_timestamp_label = ctk.CTkLabel(self.left_frame, text=f"Started: {self.current_start_str}",
                                                  font=("Helvetica", 12))
        self.start_timestamp_label.pack()

        self.end_timestamp_label = ctk.CTkLabel(self.left_frame, text=f"Ended: {self.current_end_str}",
                                                font=("Helvetica", 12))
        self.end_timestamp_label.pack(pady=(0, 15))

        button_frame = ctk.CTkFrame(self.left_frame, fg_color="transparent")
        button_frame.pack(pady=10)

        self.btn_start = ctk.CTkButton(button_frame, text="Start", command=self.start, width=60, fg_color="#28a745",
                                       hover_color="#218838")
        self.btn_start.pack(side=tk.LEFT, padx=5)

        self.btn_stop = ctk.CTkButton(button_frame, text="Stop", command=self.stop, width=60, fg_color="#dc3545",
                                      hover_color="#c82333")
        self.btn_stop.pack(side=tk.LEFT, padx=5)

        self.btn_save = ctk.CTkButton(button_frame, text="Save", command=self.save_to_table, width=60)
        self.btn_save.pack(side=tk.LEFT, padx=5)

        self.btn_reset = ctk.CTkButton(button_frame, text="Reset", command=self.reset, width=60, fg_color="#6c757d",
                                       hover_color="#5a6268")
        self.btn_reset.pack(side=tk.LEFT, padx=5)

        self.pizza_btn = ctk.CTkButton(
            self.left_frame,
            text="Send pizza hawaii to Nicolaï",
            fg_color="#dc3545",
            hover_color="#8b0000",
            font=("Helvetica", 12, "bold"),
            command=self.order_pizza
        )
        self.pizza_btn.pack(side=tk.BOTTOM, pady=20)

        # --- Right Frame Widgets (Table & Export) ---
        right_top_bar = ctk.CTkFrame(self.right_frame, fg_color="transparent")
        right_top_bar.pack(fill=tk.X, pady=(0, 5))

        ctk.CTkLabel(right_top_bar, text="History Log", font=("Helvetica", 14, "bold")).pack(side=tk.LEFT)

        self.btn_settings = ctk.CTkButton(right_top_bar, text="⚙ Settings", command=self.open_settings_dialog, width=80,
                                          font=("Helvetica", 12))
        self.btn_settings.pack(side=tk.RIGHT)

        self.btn_stats = ctk.CTkButton(right_top_bar, text="📊 Stats", command=self.open_stats_dialog, width=80,
                                       font=("Helvetica", 12))
        self.btn_stats.pack(side=tk.RIGHT, padx=5)

        # --- Treeview Base Styling ---
        style = ttk.Style()
        style.theme_use("default")
        style.map('Treeview', background=[('selected', '#1f538d')])
        style.configure("Treeview", borderwidth=0, rowheight=30, font=("Helvetica", 12))
        style.configure("Treeview.Heading", borderwidth=1, font=("Helvetica", 12, "bold"))
        self.apply_theme_to_legacy_widgets()

        columns = ("game", "tags", "start", "end", "total")
        self.tree = ttk.Treeview(self.right_frame, columns=columns, show="headings", height=10)

        self.tree.heading("game", text="Game Name")
        self.tree.heading("tags", text="Tags")
        self.tree.heading("start", text="Start Time")
        self.tree.heading("end", text="End Time")
        self.tree.heading("total", text="Total Time")

        self.tree.column("game", width=140)
        self.tree.column("tags", width=130)
        self.tree.column("start", width=160)
        self.tree.column("end", width=160)
        self.tree.column("total", width=100)

        self.tree.pack(fill=tk.BOTH, expand=True, pady=5)

        self.status_label = ctk.CTkLabel(self.right_frame, text="", font=("Helvetica", 12), text_color="#28a745")
        self.status_label.pack(side=tk.BOTTOM, pady=2)

        bottom_buttons_frame = ctk.CTkFrame(self.right_frame, fg_color="transparent")
        bottom_buttons_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=5)

        self.btn_export = ctk.CTkButton(bottom_buttons_frame, text="Export", command=self.export_to_txt)
        self.btn_export.pack(side=tk.LEFT, expand=True, padx=2)

        self.btn_add_entry = ctk.CTkButton(bottom_buttons_frame, text="Add",
                                           command=lambda: self.open_entry_dialog(is_edit=False))
        self.btn_add_entry.pack(side=tk.LEFT, expand=True, padx=2)

        self.btn_edit_entry = ctk.CTkButton(bottom_buttons_frame, text="Edit",
                                            command=lambda: self.open_entry_dialog(is_edit=True))
        self.btn_edit_entry.pack(side=tk.LEFT, expand=True, padx=2)

        self.btn_delete_entry = ctk.CTkButton(bottom_buttons_frame, text="Delete", fg_color="#dc3545",
                                              hover_color="#c82333", command=self.delete_entry)
        self.btn_delete_entry.pack(side=tk.LEFT, expand=True, padx=2)

        self.load_history()
        self.update_clock()

        # --- Local Server Setup (for CLI commands) ---
        self.setup_server()

        if initial_cmd:
            self.root.after(100, lambda: self.process_command(initial_cmd))

    # --- Theme Adapting Function ---
    def apply_theme_to_legacy_widgets(self):
        actual_mode = ctk.get_appearance_mode()
        bg_color = "#2b2b2b" if actual_mode == "Dark" else "#ffffff"
        fg_color = "white" if actual_mode == "Dark" else "black"
        head_bg = "#444" if actual_mode == "Dark" else "#e0e0e0"

        style = ttk.Style()
        style.configure("Treeview", background=bg_color, foreground=fg_color, fieldbackground=bg_color)
        style.configure("Treeview.Heading", background=head_bg, foreground=fg_color)

    # --- Database Functions ---
    def setup_database(self):
        db_path = os.path.join(BASE_DIR, "Game Time.db")
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()
        self.cursor.execute('''
                            CREATE TABLE IF NOT EXISTS history
                            (
                                id
                                INTEGER
                                PRIMARY
                                KEY
                                AUTOINCREMENT,
                                game_name
                                TEXT,
                                tags
                                TEXT,
                                start_time
                                TEXT,
                                end_time
                                TEXT,
                                total_time
                                TEXT
                            )
                            ''')

        self.cursor.execute('''
                            CREATE TABLE IF NOT EXISTS tags
                            (
                                id
                                INTEGER
                                PRIMARY
                                KEY
                                AUTOINCREMENT,
                                tag_name
                                TEXT
                                UNIQUE
                            )
                            ''')

        try:
            self.cursor.execute("ALTER TABLE history ADD COLUMN game_name TEXT")
        except sqlite3.OperationalError:
            pass

        try:
            self.cursor.execute("ALTER TABLE history ADD COLUMN tags TEXT")
        except sqlite3.OperationalError:
            pass

        self.conn.commit()

    def load_history(self):
        for row in self.tree.get_children():
            self.tree.delete(row)

        self.cursor.execute("SELECT id, game_name, tags, start_time, end_time, total_time FROM history")
        for row in self.cursor.fetchall():
            game = row[1] if row[1] is not None else ""
            tags = row[2] if row[2] is not None else ""
            self.tree.insert("", tk.END, iid=str(row[0]), values=(game, tags, row[3], row[4], row[5]))

    def get_all_tags(self):
        self.cursor.execute("SELECT tag_name FROM tags ORDER BY tag_name")
        return [row[0] for row in self.cursor.fetchall()]

    def get_all_games(self):
        self.cursor.execute(
            "SELECT DISTINCT game_name FROM history WHERE game_name IS NOT NULL AND game_name != '' ORDER BY game_name")
        return [row[0] for row in self.cursor.fetchall()]

    # --- Command Line Server Functions ---
    def setup_server(self):
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            self.server.bind(('localhost', IPC_PORT))
            self.server.listen(1)
            self.server.setblocking(False)
            self.check_server()
        except OSError:
            pass

    def check_server(self):
        try:
            conn, addr = self.server.accept()
            with conn:
                data = conn.recv(1024).decode('utf-8')
                self.process_command(data)
                conn.sendall(b"OK")
        except (BlockingIOError, socket.error):
            pass
        finally:
            self.root.after(200, self.check_server)

    def process_command(self, data):
        try:
            args = json.loads(data)
        except json.JSONDecodeError:
            args = data.strip().split(" ", 1)

        if not args:
            return

        cmd = args[0].lower()
        game_name = args[1] if len(args) > 1 else ""
        tags_input = args[2] if len(args) > 2 else ""

        if cmd == "launch":
            self.open_pre_game_tracker(game_name)

        elif cmd == "start":
            if self.running:
                self.save_to_table()

            self.start(cli_game_name=game_name, cli_tags=tags_input)

        elif cmd == "stop":
            if self.current_start_str != "--/--/---- --:--:--":
                self.save_to_table()
                self.status_label.configure(text="CLI Command: Stopped and Saved!", text_color="#3a7ebf")
            else:
                self.status_label.configure(text="CLI Command: Nothing to save.", text_color="#dc3545")

    # --- Timer Functions ---
    def update_clock(self):
        if self.running:
            current_time = time.time()
            self.elapsed_time = current_time - self.start_time

            mins, secs = divmod(self.elapsed_time, 60)
            hours, mins = divmod(mins, 60)
            hundredths = int((self.elapsed_time % 1) * 100)

            time_str = f"{int(hours):02}:{int(mins):02}:{int(secs):02}.{hundredths:02}"
            self.time_label.configure(text=time_str)

        self.root.after(10, self.update_clock)

    def center_dialog(self, dialog):
        dialog.update_idletasks()
        dialog_width = dialog.winfo_reqwidth()
        dialog_height = dialog.winfo_reqheight()

        main_x = self.root.winfo_x()
        main_y = self.root.winfo_y()
        main_width = self.root.winfo_width()
        main_height = self.root.winfo_height()

        pos_x = int(main_x + (main_width / 2) - (dialog_width / 2))
        pos_y = int(main_y + (main_height / 2) - (dialog_height / 2))

        dialog.geometry(f"+{pos_x}+{pos_y}")

    def ask_game_name(self):
        dialog = ctk.CTkToplevel(self.root)
        dialog.title("Start Timer")
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.grab_set()

        ctk.CTkLabel(dialog, text="Enter game name (optional):", font=("Helvetica", 12)).pack(pady=(15, 5))
        entry = ctk.CTkEntry(dialog, width=200)
        entry.pack(padx=20)
        entry.focus_set()

        available_tags = self.get_all_tags()
        tag_vars = {}
        if available_tags:
            ctk.CTkLabel(dialog, text="Select Tags:", font=("Helvetica", 12)).pack(pady=(15, 5))
            tags_frame = ctk.CTkScrollableFrame(dialog, height=80, width=200)
            tags_frame.pack(padx=20, pady=5)

            for tag in available_tags:
                var = tk.BooleanVar()
                tag_vars[tag] = var
                ctk.CTkCheckBox(tags_frame, text=tag, variable=var).pack(anchor="w", pady=3)

        result = [None, ""]

        def on_ok(event=None):
            selected_tags = [tag for tag, var in tag_vars.items() if var.get()]
            result[0] = entry.get()
            result[1] = ", ".join(selected_tags)
            dialog.destroy()

        def on_cancel(event=None):
            dialog.destroy()

        btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_frame.pack(pady=20)
        ctk.CTkButton(btn_frame, text="OK", command=on_ok, width=80).pack(side=tk.LEFT, padx=5)
        ctk.CTkButton(btn_frame, text="Cancel", command=on_cancel, width=80, fg_color="#6c757d",
                      hover_color="#5a6268").pack(side=tk.LEFT, padx=5)

        dialog.bind("<Return>", on_ok)
        dialog.bind("<Escape>", on_cancel)

        self.center_dialog(dialog)
        self.root.wait_window(dialog)

        return result

    def open_pre_game_tracker(self, game_name):
        dialog = ctk.CTkToplevel(self.root)
        dialog.title("Pre-Game Tracker")
        dialog.resizable(False, False)
        dialog.transient(self.root)

        # Attempt to bring to front
        dialog.attributes("-topmost", True)

        window_width = 550

        # --- Container Frame ---
        container = ctk.CTkFrame(dialog, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=20, pady=20)

        # --- Build UI Elements ---
        title_label = ctk.CTkLabel(container, text="Do you want to track time?", font=("Helvetica", 18, "bold"))
        title_label.pack(pady=(10, 15))

        ctk.CTkLabel(container, text="Game Name:", font=("Helvetica", 12)).pack(pady=(5, 0))

        game_name_display = ctk.CTkLabel(container,
                                         text=game_name if game_name else "Unknown Game",
                                         font=("Helvetica", 16, "bold"),
                                         text_color="#3a7ebf", wraplength=window_width - 80)
        game_name_display.pack(pady=(5, 15))

        tags_label = ctk.CTkLabel(container, text="Select Tags (Optional):", font=("Helvetica", 12))
        tags_label.pack(pady=(5, 0))

        tags_frame = ctk.CTkFrame(container, fg_color="transparent")
        tags_frame.pack(pady=5)

        tags = self.get_all_tags()
        tag_vars = {}

        if tags:
            for index, tag in enumerate(tags):
                var = ctk.StringVar(value="off")
                tag_vars[tag] = var
                row_num = index % 5
                col_num = index // 5
                ctk.CTkCheckBox(tags_frame, text=tag, variable=var, onvalue="on", offvalue="off").grid(
                    row=row_num, column=col_num, pady=4, padx=5, sticky="w")
        else:
            ctk.CTkLabel(tags_frame, text="No tags found in DB.", text_color="gray").pack(pady=5)

        def start_tracking():
            selected_tags = [tag for tag, var in tag_vars.items() if var.get() == "on"]
            tags_str = ", ".join(selected_tags)

            if self.root.state() == "withdrawn":
                self.root.deiconify()

            self.start(cli_game_name=game_name if game_name else "Unknown Game", cli_tags=tags_str)
            dialog.destroy()

        def cancel_tracking():
            if self.root.state() == "withdrawn":
                self.root.destroy()
            else:
                dialog.destroy()

        btn_frame = ctk.CTkFrame(container, fg_color="transparent")
        btn_frame.pack(fill="x", pady=(20, 10))

        btn_frame.grid_columnconfigure(0, weight=1)
        btn_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkButton(btn_frame, text="Yes, Track", width=120, height=35, font=("Helvetica", 13, "bold"),
                      fg_color="#28a745", hover_color="#218838", command=start_tracking).grid(row=0, column=0,
                                                                                              padx=(0, 10), sticky="e")

        ctk.CTkButton(btn_frame, text="No", width=120, height=35, font=("Helvetica", 13, "bold"),
                      fg_color="#dc3545", hover_color="#c82333", command=cancel_tracking).grid(row=0, column=1,
                                                                                               padx=(10, 0), sticky="w")

        self.center_dialog(dialog)
        dialog.focus_force()

    def start(self, cli_game_name=None, cli_tags=None):
        if not self.running:
            if self.current_start_str == "--/--/---- --:--:--":

                if cli_game_name is not None:
                    game_input = cli_game_name

                    valid_tags = []
                    if cli_tags:
                        available_tags = self.get_all_tags()
                        available_tags_lower = {t.lower(): t for t in available_tags}

                        for tag in cli_tags.split(","):
                            clean_tag = tag.strip()
                            if clean_tag.lower() in available_tags_lower:
                                valid_tags.append(available_tags_lower[clean_tag.lower()])

                    tags_input = ", ".join(valid_tags)

                    if valid_tags:
                        self.status_label.configure(text=f"CLI: Started '{game_input}' with tags '{tags_input}'",
                                                    text_color="#3a7ebf")
                    else:
                        self.status_label.configure(text=f"CLI: Started '{game_input}' (Invalid tags ignored)",
                                                    text_color="#3a7ebf")

                else:
                    res = self.ask_game_name()
                    if res[0] is None:
                        return
                    game_input = res[0]
                    tags_input = res[1]

                self.game_name_str = game_input
                self.current_tags_str = tags_input

                self.game_name_label.configure(text=self.game_name_str)
                self.tags_label.configure(text=self.current_tags_str)

                self.current_start_str = time.strftime("%d/%m/%Y %H:%M:%S")
                self.start_timestamp_label.configure(text=f"Started: {self.current_start_str}")

            self.current_end_str = "--/--/---- --:--:--"
            self.end_timestamp_label.configure(text="Ended: --/--/---- --:--:--")

            self.start_time = time.time() - self.elapsed_time
            self.running = True
            self.status_label.configure(text="")

    def stop(self):
        if self.running:
            self.current_end_str = time.strftime("%d/%m/%Y %H:%M:%S")
            self.end_timestamp_label.configure(text=f"Ended: {self.current_end_str}")
            self.running = False

    def save_to_table(self):
        if self.current_start_str != "--/--/---- --:--:--":
            total_time = self.time_label.cget("text")

            if self.current_end_str == "--/--/---- --:--:--":
                self.stop()

            self.cursor.execute(
                "INSERT INTO history (game_name, tags, start_time, end_time, total_time) VALUES (?, ?, ?, ?, ?)",
                (self.game_name_str, self.current_tags_str, self.current_start_str, self.current_end_str, total_time))
            self.conn.commit()

            new_id = self.cursor.lastrowid
            self.tree.insert("", tk.END, iid=str(new_id),
                             values=(self.game_name_str, self.current_tags_str, self.current_start_str,
                                     self.current_end_str, total_time))

            self.running = False
            self.elapsed_time = 0
            self.current_start_str = "--/--/---- --:--:--"
            self.current_end_str = "--/--/---- --:--:--"
            self.game_name_str = ""
            self.current_tags_str = ""
            self.game_name_label.configure(text="")
            self.tags_label.configure(text="")
            self.time_label.configure(text="00:00:00.00")
            self.start_timestamp_label.configure(text=f"Started: {self.current_start_str}")
            self.end_timestamp_label.configure(text=f"Ended: {self.current_end_str}")

            self.status_label.configure(text="Saved to database and reset!", text_color="#28a745")

    def export_to_txt(self):
        self.cursor.execute("SELECT game_name, tags, start_time, end_time, total_time FROM history")
        records = self.cursor.fetchall()

        if not records:
            self.status_label.configure(text="Nothing to export.", text_color="#dc3545")
            return

        filename = "Game_Time_Export.txt"

        # --- FIX: Added encoding="utf-8" here so it can handle ALL characters ---
        with open(filename, "w", encoding="utf-8") as file:
            file.write("--- GAME TIME HISTORY LOG ---\n\n")
            for record in records:
                game = record[0] if record[0] else "Unknown Game"
                tags = record[1] if record[1] else "None"
                file.write(
                    f"Game: {game} | Tags: {tags} | Started: {record[2]} | Ended: {record[3]} | Total Time: {record[4]}\n")

        self.status_label.configure(text=f"Successfully exported to {filename}", text_color="#28a745")

    def reset(self):
        self.running = False
        self.elapsed_time = 0
        self.current_start_str = "--/--/---- --:--:--"
        self.current_end_str = "--/--/---- --:--:--"
        self.game_name_str = ""
        self.current_tags_str = ""
        self.game_name_label.configure(text="")
        self.tags_label.configure(text="")
        self.time_label.configure(text="00:00:00.00")
        self.start_timestamp_label.configure(text=f"Started: {self.current_start_str}")
        self.end_timestamp_label.configure(text=f"Ended: {self.current_end_str}")
        self.status_label.configure(text="Timer reset.", text_color="#3a7ebf")

    def order_pizza(self):
        webbrowser.open("https://www.dominos.nl/menu-pizza/pizza-hawaii-phaw")

    # --- Stats Dialog ---
    def open_stats_dialog(self):
        dialog = ctk.CTkToplevel(self.root)
        dialog.title("Statistics Dashboard")
        dialog.geometry("850x780")
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.grab_set()

        # Filters Frame
        filter_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        filter_frame.pack(pady=15)

        ctk.CTkLabel(filter_frame, text="From (DD/MM/YYYY):").grid(row=0, column=0, padx=5, sticky="e")
        from_entry = ctk.CTkEntry(filter_frame, width=120)
        from_entry.grid(row=0, column=1, padx=5)

        ctk.CTkLabel(filter_frame, text="To (DD/MM/YYYY):").grid(row=0, column=2, padx=5, sticky="e")
        to_entry = ctk.CTkEntry(filter_frame, width=120)
        to_entry.grid(row=0, column=3, padx=5)

        ctk.CTkLabel(filter_frame, text="Game:").grid(row=1, column=0, padx=5, pady=10, sticky="e")
        game_var = tk.StringVar(value="All")
        games = ["All"] + self.get_all_games()
        game_cb = ctk.CTkComboBox(filter_frame, variable=game_var, values=games, state="readonly", width=120)
        game_cb.grid(row=1, column=1, padx=5, pady=10)

        ctk.CTkLabel(filter_frame, text="Tag:").grid(row=1, column=2, padx=5, pady=10, sticky="e")
        tag_var = tk.StringVar(value="All")
        tags = ["All"] + self.get_all_tags()
        tag_cb = ctk.CTkComboBox(filter_frame, variable=tag_var, values=tags, state="readonly", width=120)
        tag_cb.grid(row=1, column=3, padx=5, pady=10)

        # Dynamic Total Time Label
        total_time_label = ctk.CTkLabel(dialog, text="Total Time: 00:00:00.00", font=("Helvetica", 16, "bold"),
                                        text_color="#3a7ebf")
        total_time_label.pack(pady=5)

        # Charts Area
        charts_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        charts_frame.pack(fill=tk.X, padx=20, pady=5)

        actual_mode = ctk.get_appearance_mode()
        canvas_bg = "#2b2b2b" if actual_mode == "Dark" else "#ffffff"

        # Game Pie Chart Container
        game_chart_frame = ctk.CTkFrame(charts_frame)
        game_chart_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        ctk.CTkLabel(game_chart_frame, text="Time Spent per Game", font=("Helvetica", 12, "bold")).pack(pady=(5, 0))
        game_canvas = tk.Canvas(game_chart_frame, width=250, height=250, bg=canvas_bg, highlightthickness=0)
        game_canvas.pack(pady=5)
        game_legend = ctk.CTkFrame(game_chart_frame, fg_color="transparent")
        game_legend.pack(pady=5)

        # Tag Pie Chart Container
        tag_chart_frame = ctk.CTkFrame(charts_frame)
        tag_chart_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5)
        ctk.CTkLabel(tag_chart_frame, text="Time Spent per Tag", font=("Helvetica", 12, "bold")).pack(pady=(5, 0))
        tag_canvas = tk.Canvas(tag_chart_frame, width=250, height=250, bg=canvas_bg, highlightthickness=0)
        tag_canvas.pack(pady=5)
        tag_legend = ctk.CTkFrame(tag_chart_frame, fg_color="transparent")
        tag_legend.pack(pady=5)

        # Table Area (Below Pie Charts)
        table_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        table_frame.pack(fill=tk.BOTH, expand=True, padx=25, pady=10)

        ctk.CTkLabel(table_frame, text="Filtered Entries (Recent 20 max)", font=("Helvetica", 12, "bold")).pack(
            anchor="w")

        columns = ("game", "tags", "start", "total")
        stats_tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=8)

        stats_tree.heading("game", text="Game Name")
        stats_tree.heading("tags", text="Tags")
        stats_tree.heading("start", text="Start Time")
        stats_tree.heading("total", text="Total Time")

        stats_tree.column("game", width=180)
        stats_tree.column("tags", width=180)
        stats_tree.column("start", width=160)
        stats_tree.column("total", width=120)

        stats_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Chart Colors
        chart_colors = ["#FF9999", "#66B2FF", "#99FF99", "#FFCC99", "#C2C2F0", "#FFB3E6", "#C4E17F", "#FF6666",
                        "#FFD966", "#85E085"]

        def time_to_seconds(t_str):
            try:
                parts = t_str.split(':')
                return int(parts[0]) * 3600 + int(parts[1]) * 60 + float(parts[2])
            except:
                return 0

        def update_stats():
            from_date = from_entry.get().strip()
            to_date = to_entry.get().strip()
            selected_game = game_var.get()
            selected_tag = tag_var.get()

            dt_from = None
            dt_to = None

            try:
                if from_date:
                    dt_from = datetime.strptime(from_date, "%d/%m/%Y")
                if to_date:
                    dt_to = datetime.strptime(to_date, "%d/%m/%Y")
                    dt_to = dt_to.replace(hour=23, minute=59, second=59)
            except ValueError:
                messagebox.showerror("Error", "Invalid date format. Use DD/MM/YYYY", parent=dialog)
                return

            self.cursor.execute("SELECT game_name, tags, start_time, total_time FROM history")
            records = self.cursor.fetchall()

            filtered_records = []
            for rec in records:
                rec_game = rec[0] if rec[0] else "Unknown"
                rec_tags = rec[1] if rec[1] else "None"
                rec_start = rec[2]
                rec_total = rec[3]

                try:
                    rec_dt = datetime.strptime(rec_start, "%d/%m/%Y %H:%M:%S")
                except ValueError:
                    continue

                if dt_from and rec_dt < dt_from: continue
                if dt_to and rec_dt > dt_to: continue

                if selected_game != "All" and rec_game != selected_game:
                    continue

                if selected_tag != "All":
                    tag_list = [t.strip() for t in rec_tags.split(",")]
                    if selected_tag not in tag_list:
                        continue

                filtered_records.append((rec_game, rec_tags, rec_start, rec_total))

            for row in stats_tree.get_children():
                stats_tree.delete(row)

            recent_20 = list(reversed(filtered_records))[:20]
            for r in recent_20:
                stats_tree.insert("", tk.END, values=(r[0], r[1], r[2], r[3]))

            total_seconds = sum(time_to_seconds(r[3]) for r in filtered_records)
            hours, remainder = divmod(total_seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            total_time_label.configure(text=f"Total Time: {int(hours):02}:{int(minutes):02}:{seconds:05.2f}")

            game_totals = {}
            tag_totals = {}
            for r in filtered_records:
                g = r[0]
                sec = time_to_seconds(r[3])

                if sec <= 0:
                    continue

                game_totals[g] = game_totals.get(g, 0) + sec

                t_str = r[1]
                if t_str and t_str != "None":
                    t_list = [t.strip() for t in t_str.split(",") if t.strip()]
                    for t in t_list:
                        if selected_tag != "All" and t != selected_tag:
                            continue
                        tag_totals[t] = tag_totals.get(t, 0) + sec
                else:
                    if selected_tag == "All":
                        tag_totals["None"] = tag_totals.get("None", 0) + sec

            draw_pie(game_canvas, game_legend, game_totals)
            draw_pie(tag_canvas, tag_legend, tag_totals)

        def draw_pie(canvas, legend_frame, data_dict):
            canvas.delete("all")
            for widget in legend_frame.winfo_children():
                widget.destroy()

            valid_items = {k: v for k, v in data_dict.items() if v > 0}
            total = sum(valid_items.values())

            if total <= 0:
                canvas.create_text(125, 125, text="No Data Available", fill="gray", font=("Helvetica", 10))
                return

            start_angle = 0
            items = list(valid_items.items())
            items.sort(key=lambda x: x[1], reverse=True)

            for i, (key, val) in enumerate(items):
                extent = (val / total) * 360
                color = chart_colors[i % len(chart_colors)]

                if extent >= 359.9:
                    canvas.create_oval(25, 25, 225, 225, fill=color, outline=canvas_bg)
                else:
                    draw_extent = max(1.0, extent)
                    canvas.create_arc(25, 25, 225, 225, start=start_angle, extent=draw_extent, fill=color,
                                      outline=canvas_bg, style=tk.PIESLICE)

                start_angle += extent

                if i < 7:
                    row = ctk.CTkFrame(legend_frame, fg_color="transparent")
                    row.pack(anchor="w", pady=1)

                    color_box = ctk.CTkLabel(row, text="", fg_color=color, width=15, height=15, corner_radius=2)
                    color_box.pack(side=tk.LEFT, padx=(0, 5))

                    h, m = divmod(int(val), 3600)
                    m, s = divmod(m, 60)
                    time_str = f"{h}h {m}m {s}s"
                    ctk.CTkLabel(row, text=f"{key} ({time_str})", font=("Helvetica", 11)).pack(side=tk.LEFT)
                elif i == 7:
                    ctk.CTkLabel(legend_frame, text="...and more", font=("Helvetica", 10, "italic"),
                                 text_color="gray").pack(anchor="w")

        apply_btn = ctk.CTkButton(filter_frame, text="Apply Filters", command=update_stats, width=100,
                                  fg_color="#28a745", hover_color="#218838")
        apply_btn.grid(row=1, column=4, padx=15, pady=10)

        self.center_dialog(dialog)
        update_stats()

        # --- Tags Settings Dialog ---

    def open_settings_dialog(self):
        dialog = ctk.CTkToplevel(self.root)
        dialog.title("Settings")
        dialog.geometry("380x420")
        dialog.resizable(False, False)
        dialog.transient(self.root)

        # Grab set initially
        dialog.grab_set()

        self.center_dialog(dialog)

        tabview = ctk.CTkTabview(dialog)
        tabview.pack(fill=tk.BOTH, expand=True, padx=15, pady=(5, 15))

        tab_tags = tabview.add("Tags")
        tab_appearance = tabview.add("Appearance")

        # --- TAGS TAB ---
        ctk.CTkLabel(tab_tags, text="Available Tags:", font=("Helvetica", 14, "bold")).pack(pady=(10, 5))

        listbox_frame = ctk.CTkFrame(tab_tags, fg_color="transparent")
        listbox_frame.pack(fill=tk.BOTH, expand=True, padx=10)

        actual_mode = ctk.get_appearance_mode()
        bg_color = "#2b2b2b" if actual_mode == "Dark" else "#ffffff"
        fg_color = "white" if actual_mode == "Dark" else "black"

        tag_listbox = tk.Listbox(listbox_frame, bg=bg_color, fg=fg_color, selectbackground="#3a7ebf",
                                 font=("Helvetica", 12), highlightthickness=0, borderwidth=1)
        tag_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        def refresh_listbox():
            tag_listbox.delete(0, tk.END)
            for tag in self.get_all_tags():
                tag_listbox.insert(tk.END, tag)

        refresh_listbox()

        def add_tag():
            tag_dialog = ctk.CTkInputDialog(text="Enter new tag name:", title="Add Tag")
            new_tag = tag_dialog.get_input()
            if new_tag and new_tag.strip():
                try:
                    self.cursor.execute("INSERT INTO tags (tag_name) VALUES (?)", (new_tag.strip(),))
                    self.conn.commit()
                    refresh_listbox()
                except sqlite3.IntegrityError:
                    messagebox.showerror("Error", "Tag already exists!", parent=dialog)

        def edit_tag():
            selected = tag_listbox.curselection()
            if not selected:
                messagebox.showwarning("Warning", "Select a tag to edit.", parent=dialog)
                return
            old_tag = tag_listbox.get(selected[0])

            tag_dialog = ctk.CTkInputDialog(text=f"Enter new tag name for '{old_tag}':", title="Edit Tag")
            new_tag = tag_dialog.get_input()

            if new_tag and new_tag.strip():
                try:
                    self.cursor.execute("UPDATE tags SET tag_name = ? WHERE tag_name = ?", (new_tag.strip(), old_tag))
                    self.conn.commit()
                    refresh_listbox()
                except sqlite3.IntegrityError:
                    messagebox.showerror("Error", "Tag already exists!", parent=dialog)

        def delete_tag():
            selected = tag_listbox.curselection()
            if not selected:
                messagebox.showwarning("Warning", "Select a tag to delete.", parent=dialog)
                return
            tag_to_delete = tag_listbox.get(selected[0])
            confirm = messagebox.askyesno("Confirm", f"Delete tag '{tag_to_delete}'?", parent=dialog)
            if confirm:
                self.cursor.execute("DELETE FROM tags WHERE tag_name = ?", (tag_to_delete,))
                self.conn.commit()
                refresh_listbox()

        btn_frame = ctk.CTkFrame(tab_tags, fg_color="transparent")
        btn_frame.pack(pady=15)
        ctk.CTkButton(btn_frame, text="Add", command=add_tag, width=70).pack(side=tk.LEFT, padx=5)
        ctk.CTkButton(btn_frame, text="Edit", command=edit_tag, width=70).pack(side=tk.LEFT, padx=5)
        ctk.CTkButton(btn_frame, text="Delete", command=delete_tag, width=70, fg_color="#dc3545",
                      hover_color="#c82333").pack(side=tk.LEFT, padx=5)

        # --- APPEARANCE TAB ---
        ctk.CTkLabel(tab_appearance, text="UI Theme:", font=("Helvetica", 14, "bold")).pack(pady=(30, 10))

        def change_theme_event(new_mode):
            # 1. Release the grab lock temporarily so the app doesn't freeze during the heavy redraw
            dialog.grab_release()

            def apply_theme():
                # 2. Change the global theme
                ctk.set_appearance_mode(new_mode)
                self.apply_theme_to_legacy_widgets()

                curr_mode = ctk.get_appearance_mode()
                new_bg = "#2b2b2b" if curr_mode == "Dark" else "#ffffff"
                new_fg = "white" if curr_mode == "Dark" else "black"
                tag_listbox.configure(bg=new_bg, fg=new_fg)

                def restore_focus_and_lock():
                    # 3. Force the window back to the front and re-apply the grab lock
                    dialog.deiconify()
                    dialog.lift()
                    dialog.attributes("-topmost", True)
                    dialog.attributes("-topmost", False)
                    dialog.focus_force()
                    dialog.grab_set()

                    # Wait 250ms for CustomTkinter to fully finish drawing the new theme

                dialog.after(250, restore_focus_and_lock)

            # Wait 100ms so the OptionMenu dropdown has time to visually close first
            dialog.after(100, apply_theme)

        appearance_menu = ctk.CTkOptionMenu(tab_appearance, values=["System", "Dark", "Light"],
                                            command=change_theme_event)
        appearance_menu.pack(pady=10)
        appearance_menu.set(ctk.get_appearance_mode())

    # --- Combined Add/Edit Entry Function ---
    def open_entry_dialog(self, is_edit=False):
        selected_item = None

        if is_edit:
            selected_items = self.tree.selection()
            if not selected_items:
                self.status_label.configure(text="Select an entry to edit first.", text_color="#dc3545")
                return
            selected_item = selected_items[0]

        dialog = ctk.CTkToplevel(self.root)
        dialog.title("Edit Entry" if is_edit else "Add Manual Entry")
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.grab_set()

        ctk.CTkLabel(dialog, text="Game Name (Optional)", font=("Helvetica", 12)).pack(pady=(15, 2))
        game_entry = ctk.CTkEntry(dialog, width=200)
        game_entry.pack()

        # Tags Input
        available_tags = self.get_all_tags()
        tag_vars = {}
        current_tags_list = []

        if is_edit:
            vals = self.tree.item(selected_item, "values")
            if vals[1]:
                current_tags_list = [t.strip() for t in vals[1].split(",")]

        if available_tags:
            ctk.CTkLabel(dialog, text="Select Tags:", font=("Helvetica", 12)).pack(pady=(10, 0))
            tags_frame = ctk.CTkScrollableFrame(dialog, height=80, width=200)
            tags_frame.pack(padx=20, pady=5)

            for tag in available_tags:
                var = tk.BooleanVar()
                if is_edit and tag in current_tags_list:
                    var.set(True)

                tag_vars[tag] = var
                ctk.CTkCheckBox(tags_frame, text=tag, variable=var).pack(anchor="w", pady=3)

        ctk.CTkLabel(dialog, text="Start Time (DD/MM/YYYY HH:MM:SS)", font=("Helvetica", 12)).pack(pady=(5, 2))
        start_entry = ctk.CTkEntry(dialog, width=200)
        start_entry.pack()

        ctk.CTkLabel(dialog, text="End Time (DD/MM/YYYY HH:MM:SS)", font=("Helvetica", 12)).pack(pady=(5, 2))
        end_entry = ctk.CTkEntry(dialog, width=200)
        end_entry.pack()

        ctk.CTkLabel(dialog, text="Total Time (Auto-calculates, editable)", font=("Helvetica", 12)).pack(pady=(5, 2))
        total_entry = ctk.CTkEntry(dialog, width=200)
        total_entry.pack(pady=(0, 5))

        if is_edit:
            vals = self.tree.item(selected_item, "values")
            game_entry.insert(0, vals[0])
            start_entry.insert(0, vals[2])
            end_entry.insert(0, vals[3])
            total_entry.insert(0, vals[4])
        else:
            start_entry.insert(0, time.strftime("%d/%m/%Y %H:%M:%S"))

        def calculate_diff(*args):
            try:
                start_dt = datetime.strptime(start_entry.get(), "%d/%m/%Y %H:%M:%S")
                end_dt = datetime.strptime(end_entry.get(), "%d/%m/%Y %H:%M:%S")

                diff = end_dt - start_dt
                if diff.total_seconds() >= 0:
                    hours, remainder = divmod(int(diff.total_seconds()), 3600)
                    minutes, seconds = divmod(remainder, 60)

                    total_str = f"{hours:02}:{minutes:02}:{seconds:02}.00"
                    total_entry.delete(0, tk.END)
                    total_entry.insert(0, total_str)
            except ValueError:
                pass

        start_entry.bind("<KeyRelease>", calculate_diff)
        end_entry.bind("<KeyRelease>", calculate_diff)

        def save_entry():
            game_val = game_entry.get()
            selected_tags = [tag for tag, var in tag_vars.items() if var.get()]
            tags_val = ", ".join(selected_tags)

            start_val = start_entry.get()
            end_val = end_entry.get()
            total_val = total_entry.get()

            if is_edit:
                self.cursor.execute(
                    "UPDATE history SET game_name=?, tags=?, start_time=?, end_time=?, total_time=? WHERE id=?",
                    (game_val, tags_val, start_val, end_val, total_val, selected_item))
                self.conn.commit()
                self.tree.item(selected_item, values=(game_val, tags_val, start_val, end_val, total_val))
                self.status_label.configure(text="Entry updated!", text_color="#28a745")
            else:
                self.cursor.execute(
                    "INSERT INTO history (game_name, tags, start_time, end_time, total_time) VALUES (?, ?, ?, ?, ?)",
                    (game_val, tags_val, start_val, end_val, total_val))
                self.conn.commit()
                new_id = self.cursor.lastrowid
                self.tree.insert("", tk.END, iid=str(new_id),
                                 values=(game_val, tags_val, start_val, end_val, total_val))
                self.status_label.configure(text="Manual entry added!", text_color="#28a745")

            dialog.destroy()

        btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_frame.pack(pady=20)
        ctk.CTkButton(btn_frame, text="Save", command=save_entry, width=80).pack(side=tk.LEFT, padx=5)
        ctk.CTkButton(btn_frame, text="Cancel", command=dialog.destroy, width=80, fg_color="#6c757d",
                      hover_color="#5a6268").pack(side=tk.LEFT, padx=5)

        self.center_dialog(dialog)

    def delete_entry(self):
        selected_items = self.tree.selection()

        if not selected_items:
            self.status_label.configure(text="Select an entry to delete first.", text_color="#dc3545")
            return

        selected_item = selected_items[0]

        confirm = messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this entry?")

        if confirm:
            self.cursor.execute("DELETE FROM history WHERE id=?", (selected_item,))
            self.conn.commit()

            self.tree.delete(selected_item)
            self.status_label.configure(text="Entry deleted successfully.", text_color="#28a745")
        else:
            self.status_label.configure(text="Deletion cancelled.", text_color="#3a7ebf")

    def __del__(self):
        if hasattr(self, 'conn'):
            self.conn.close()
        if hasattr(self, 'server'):
            self.server.close()


if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Check if it's a known command
        first_arg = sys.argv[1].lower()
        if first_arg not in ["start", "stop"]:
            # If not a command, treat as game name for the launcher
            game_name = " ".join(sys.argv[1:])
            cmd_args = ["launch", game_name]
        else:
            cmd_args = sys.argv[1:]

        cmd_data = json.dumps(cmd_args)

        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect(('localhost', IPC_PORT))
                s.sendall(cmd_data.encode('utf-8'))
                s.recv(1024)
                print(f"Success: Command sent to running Game Time Manager.")
                sys.exit(0)
        except ConnectionRefusedError:
            root = ctk.CTk()
            # If it's a launch command, hide the main window initially
            if cmd_args[0] == "launch":
                root.withdraw()
            app = Game_Time_Manager(root, initial_cmd=cmd_data)
            root.mainloop()
    else:
        root = ctk.CTk()
        app = Game_Time_Manager(root)
        root.mainloop()