#!/usr/bin/env python3
import gi
gi.require_version("Gtk", "4.0")
from gi.repository import Gtk, GLib
import threading
import subprocess
import os

SCRIPT_DIR = "/home/v/ai_apx/steam_review"
VENV_PYTHON = os.path.join(SCRIPT_DIR, ".venv", "bin", "python")

class MainWindow(Gtk.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app, title="Steam Review Analyzer")
        self.set_default_size(800, 600)
        
        # Main box
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.set_child(vbox)
        
        # Header
        header = Gtk.HeaderBar()
        header.set_title("Steam Review Analyzer")
        vbox.append(header)
        
        # Notebook (tabs)
        notebook = Gtk.Notebook()
        notebook.set_margin_top(6)
        notebook.set_margin_bottom(6)
        notebook.set_margin_start(6)
        notebook.set_margin_end(6)
        vbox.append(notebook)
        
        # Tab 1: Scrape
        scrape_box = self.create_scrape_tab()
        notebook.append_page(scrape_box, Gtk.Label(label="Scrape"))
        
        # Tab 2: Database
        db_box = self.create_db_tab()
        notebook.append_page(db_box, Gtk.Label(label="Database"))
        
        # Tab 3: Analysis
        analysis_box = self.create_analysis_tab()
        notebook.append_page(analysis_box, Gtk.Label(label="Analysis"))

    def create_scrape_tab(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        box.set_margin_top(20)
        box.set_margin_bottom(20)
        box.set_margin_start(20)
        box.set_margin_end(20)
        
        # Title
        title = Gtk.Label(label="Scrape Reviews")
        title.set_markup("<b><big>Scrape Reviews</big></b>")
        box.append(title)
        
        # App ID
        app_id_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        box.append(app_id_box)
        app_id_box.append(Gtk.Label(label="App ID:"))
        self.app_id_entry = Gtk.Entry()
        self.app_id_entry.set_placeholder_text("2277560")
        self.app_id_entry.set_hexpand(True)
        app_id_box.append(self.app_id_entry)
        
        # Limit
        limit_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        box.append(limit_box)
        limit_box.append(Gtk.Label(label="Limit:"))
        self.limit_entry = Gtk.Entry()
        self.limit_entry.set_placeholder_text("1000")
        limit_box.append(self.limit_entry)
        
        # Button
        scrape_btn = Gtk.Button(label="Start Scraping")
        scrape_btn.connect("clicked", self.on_scrape)
        box.append(scrape_btn)
        
        # Status
        self.scrape_status = Gtk.Label(label="Ready")
        box.append(self.scrape_status)
        
        return box

    def create_db_tab(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        box.set_margin_top(20)
        box.set_margin_bottom(20)
        box.set_margin_start(20)
        box.set_margin_end(20)
        
        # Title
        title = Gtk.Label(label="Database")
        title.set_markup("<b><big>Database</big></b>")
        box.append(title)
        
        # Stats
        self.stats_label = Gtk.Label(label="Loading...")
        box.append(self.stats_label)
        
        # Buttons
        btn_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        box.append(btn_box)
        
        refresh_btn = Gtk.Button(label="Refresh")
        refresh_btn.connect("clicked", self.on_db_refresh)
        btn_box.append(refresh_btn)
        
        export_btn = Gtk.Button(label="Export CSV")
        export_btn.connect("clicked", self.on_export)
        btn_box.append(export_btn)
        
        return box

    def create_analysis_tab(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        box.set_margin_top(20)
        box.set_margin_bottom(20)
        box.set_margin_start(20)
        box.set_margin_end(20)
        
        # Title
        title = Gtk.Label(label="Analysis")
        title.set_markup("<b><big>Analysis</big></b>")
        box.append(title)
        
        # CSV selection
        csv_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        box.append(csv_box)
        csv_box.append(Gtk.Label(label="CSV:"))
        self.csv_combo = Gtk.ComboBoxText()
        self.refresh_csv_combo()
        csv_box.append(self.csv_combo)
        
        # Analyze button
        analyze_btn = Gtk.Button(label="Analyze")
        analyze_btn.connect("clicked", self.on_analyze)
        box.append(analyze_btn)
        
        # Status
        self.analysis_status = Gtk.Label(label="Ready")
        box.append(self.analysis_status)
        
        return box

    def refresh_csv_combo(self):
        self.csv_combo.remove_all()
        for f in sorted(os.listdir(SCRIPT_DIR)):
            if f.endswith('_reviews.csv'):
                self.csv_combo.append(f, f)

    def run_venv(self, *args):
        cmd = [VENV_PYTHON, os.path.join(SCRIPT_DIR, args[0])] + list(args[1:])
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=SCRIPT_DIR)
        return result

    def on_scrape(self, btn):
        app_id = self.app_id_entry.get_text()
        if not app_id:
            self.scrape_status.set_label("Enter App ID")
            return
        limit = self.limit_entry.get_text()
        
        self.scrape_status.set_label("Scraping...")
        
        def run():
            args = ["steam_review_scraper.py", "--app_id", app_id]
            if limit:
                args.extend(["--limit", limit])
            self.run_venv(*args)
            GLib.idle_add(self.scrape_status.set_label, "Done")
            GLib.idle_add(self.refresh_csv_combo)
        
        threading.Thread(target=run, daemon=True).start()

    def on_db_refresh(self, btn):
        def run():
            out, _ = self.run_venv("export_cli.py", "stats")
            GLib.idle_add(self.stats_label.set_label, out.strip() if out else "Error")
        threading.Thread(target=run, daemon=True).start()

    def on_export(self, btn):
        import datetime
        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        self.run_venv("export_cli.py", "export", "--format", "csv", "--output", f"export_{ts}.csv")
        self.stats_label.set_label(f"Exported export_{ts}.csv")

    def on_analyze(self, btn):
        csv_file = self.csv_combo.get_active_id()
        if not csv_file:
            self.analysis_status.set_label("Select file")
            return
        
        self.analysis_status.set_label("Analyzing...")
        
        def run():
            self.run_venv("analyze_reviews.py", csv_file, "--save_db")
            GLib.idle_add(self.analysis_status.set_label, "Done")
        
        threading.Thread(target=run, daemon=True).start()


class App(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="org.steamreview.app")
        self.connect('activate', self.on_activate)

    def on_activate(self, app):
        win = MainWindow(app)
        win.present()


if __name__ == "__main__":
    app = App()
    app.run(None)
