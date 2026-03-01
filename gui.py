#!/usr/bin/env python3
import sys
import os
import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw, GLib
import threading
import subprocess

SCRIPT_DIR = "/home/v/ai_apx/steam_review"
VENV_PYTHON = os.path.join(SCRIPT_DIR, ".venv", "bin", "python")

class SteamReviewApp(Adw.Application):
    def __init__(self):
        super().__init__(application_id="org.steamreview.app", flags=0)
        self.connect('activate', self.on_activate)

    def on_activate(self, app):
        self.window = Adw.ApplicationWindow(application=app)
        self.window.set_title("Steam Review Analyzer")
        self.window.set_default_size(900, 650)

        # Toast overlay
        toast = Adw.ToastOverlay()
        self.window.set_content(toast)

        # Main box
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        toast.set_child(main_box)

        # Header with tabs
        header = Adw.HeaderBar()
        main_box.append(header)

        # Tab view
        tab_view = Adw.TabView()
        tab_view.set_margin_top(6)
        main_box.append(tab_view)

        # Page 1: Scrape
        scrape_page = self.create_scrape_page()
        tab_view.add_page(scrape_page, Adw.TabPage(title="🔍 Scrape"))

        # Page 2: Database  
        db_page = self.create_db_page()
        tab_view.add_page(db_page, Adw.TabPage(title="💾 Database"))

        # Page 3: Analysis
        analysis_page = self.create_analysis_page()
        tab_view.add_page(analysis_page, Adw.TabPage(title="📊 Analysis"))

        self.window.present()

    def create_scrape_page(self):
        clamp = Adw.Clamp()
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        box.set_margin_top(24)
        box.set_margin_bottom(24)
        box.set_margin_start(24)
        box.set_margin_end(24)
        clamp.set_child(box)

        # Title
        title = Gtk.Label()
        title.set_markup("<span size='xx-large' weight='bold'>Scrape Reviews</span>")
        title.set_halign(Gtk.Align.CENTER)
        box.append(title)

        # Card
        card = Adw.Card()
        card.set_margin_top(16)
        box.append(card)

        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        vbox.set_margin_top(16)
        vbox.set_margin_bottom(16)
        vbox.set_margin_start(16)
        vbox.set_margin_end(16)
        card.set_child(vbox)

        # App ID
        app_id_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        vbox.append(app_id_box)
        app_id_box.append(Gtk.Label(label="App ID:"))
        
        self.app_id_entry = Gtk.Entry()
        self.app_id_entry.set_placeholder_text("2277560")
        self.app_id_entry.set_hexpand(True)
        app_id_box.append(self.app_id_entry)

        # Limit
        limit_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        vbox.append(limit_box)
        limit_box.append(Gtk.Label(label="Limit:"))
        
        self.limit_entry = Gtk.Entry()
        self.limit_entry.set_placeholder_text("1000")
        self.limit_entry.set_hexpand(True)
        limit_box.append(self.limit_entry)

        # Button
        scrape_btn = Gtk.Button(label="Start Scraping")
        scrape_btn.add_css_class("suggested-action")
        scrape_btn.set_margin_top(12)
        scrape_btn.set_halign(Gtk.Align.CENTER)
        scrape_btn.connect("clicked", self.on_scrape)
        vbox.append(scrape_btn)

        # Status
        self.scrape_status = Gtk.Label(label="Ready")
        self.scrape_status.set_margin_top(12)
        self.scrape_status.set_halign(Gtk.Align.CENTER)
        box.append(self.scrape_status)

        self.progress = Adw.ProgressBar()
        self.progress.set_margin_top(12)
        self.progress.set_visible(False)
        box.append(self.progress)

        return clamp

    def create_db_page(self):
        clamp = Adw.Clamp()
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        box.set_margin_top(24)
        box.set_margin_bottom(24)
        box.set_margin_start(24)
        box.set_margin_end(24)
        clamp.set_child(box)

        # Title
        title = Gtk.Label()
        title.set_markup("<span size='xx-large' weight='bold'>Database</span>")
        title.set_halign(Gtk.Align.CENTER)
        box.append(title)

        # Stats card
        stats_card = Adw.Card()
        stats_card.set_margin_top(16)
        box.append(stats_card)

        stats_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        stats_box.set_margin_all(16)
        stats_card.set_child(stats_box)

        self.stats_label = Gtk.Label(label="No data")
        self.stats_label.set_markup("<span size='large'>Loading...</span>")
        self.stats_label.set_halign(Gtk.Align.CENTER)
        stats_box.append(self.stats_label)

        # Buttons
        btn_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        btn_box.set_halign(Gtk.Align.CENTER)
        btn_box.set_margin_top(12)
        box.append(btn_box)

        refresh_btn = Gtk.Button(label="Refresh")
        refresh_btn.connect("clicked", self.on_db_refresh)
        btn_box.append(refresh_btn)

        export_btn = Gtk.Button(label="Export CSV")
        export_btn.connect("clicked", self.on_export)
        btn_box.append(export_btn)

        return clamp

    def create_analysis_page(self):
        clamp = Adw.Clamp()
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        box.set_margin_top(24)
        box.set_margin_bottom(24)
        box.set_margin_start(24)
        box.set_margin_end(24)
        clamp.set_child(box)

        # Title
        title = Gtk.Label()
        title.set_markup("<span size='xx-large' weight='bold'>Analysis</span>")
        title.set_halign(Gtk.Align.CENTER)
        box.append(title)

        # Card
        card = Adw.Card()
        card.set_margin_top(16)
        box.append(card)

        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        vbox.set_margin_all(16)
        card.set_child(vbox)

        # CSV selection
        csv_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        vbox.append(csv_box)
        csv_box.append(Gtk.Label(label="CSV File:"))
        
        self.csv_combo = Gtk.ComboBoxText()
        self.csv_combo.set_hexpand(True)
        self.refresh_csv_combo()
        csv_box.append(self.csv_combo)

        # Switch
        self.save_db_check = Gtk.Switch()
        self.save_db_check.set_active(True)
        switch_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        vbox.append(switch_box)
        switch_box.append(Gtk.Label(label="Save to DB:"))
        switch_box.append(self.save_db_check)

        # Button
        analyze_btn = Gtk.Button(label="Run Analysis")
        analyze_btn.add_css_class("suggested-action")
        analyze_btn.set_margin_top(12)
        analyze_btn.set_halign(Gtk.Align.CENTER)
        analyze_btn.connect("clicked", self.on_analyze)
        vbox.append(analyze_btn)

        # Status
        self.analysis_status = Gtk.Label(label="Ready")
        self.analysis_status.set_margin_top(12)
        self.analysis_status.set_halign(Gtk.Align.CENTER)
        box.append(self.analysis_status)

        return clamp

    def refresh_csv_combo(self):
        self.csv_combo.remove_all()
        files = sorted([f for f in os.listdir(SCRIPT_DIR) if f.endswith('_reviews.csv')], 
                      key=lambda x: os.path.getmtime(os.path.join(SCRIPT_DIR, x)), reverse=True)
        for f in files:
            self.csv_combo.append(f, f)
        if files:
            self.csv_combo.set_active(0)

    def run_venv(self, *args):
        cmd = [VENV_PYTHON, os.path.join(SCRIPT_DIR, args[0])] + list(args[1:])
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=SCRIPT_DIR)
        return result.stdout, result.stderr

    def on_scrape(self, btn):
        app_id = self.app_id_entry.get_text()
        if not app_id:
            self.scrape_status.set_label("Please enter App ID")
            return

        limit = self.limit_entry.get_text()
        
        self.scrape_status.set_label("Scraping...")
        self.progress.set_visible(True)
        self.progress.set_pulsate(True)
        btn.set_sensitive(False)
        
        thread = threading.Thread(target=self._scrape_thread, args=(app_id, limit, btn))
        thread.daemon = True
        thread.start()

    def _scrape_thread(self, app_id, limit, btn):
        args = ["steam_review_scraper.py", "--app_id", app_id]
        if limit:
            args.extend(["--limit", limit])
        
        self.run_venv(*args)
        
        GLib.idle_add(self.progress.set_visible, False)
        GLib.idle_add(btn.set_sensitive, True)
        GLib.idle_add(self.scrape_status.set_label, "Done!")
        GLib.idle_add(self.refresh_csv_combo)

    def on_db_refresh(self, btn):
        self.stats_label.set_text("Loading...")
        thread = threading.Thread(target=self._db_refresh_thread)
        thread.daemon = True
        thread.start()

    def _db_refresh_thread(self):
        out, err = self.run_venv("export_cli.py", "stats")
        text = out.strip() if out else err
        GLib.idle_add(self.stats_label.set_text, text.replace('\n', ' | '))

    def on_export(self, btn):
        import datetime
        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        out, err = self.run_venv("export_cli.py", "export", "--format", "csv", "--output", f"export_{ts}.csv")
        self.stats_label.set_text(f"Exported export_{ts}.csv")

    def on_analyze(self, btn):
        csv_file = self.csv_combo.get_active_id()
        if not csv_file:
            self.analysis_status.set_label("No file selected")
            return

        save_db = self.save_db_check.get_active()
        
        self.analysis_status.set_label("Analyzing...")
        
        thread = threading.Thread(target=self._analyze_thread, args=(csv_file, save_db))
        thread.daemon = True
        thread.start()

    def _analyze_thread(self, csv_file, save_db):
        args = ["analyze_reviews.py", csv_file]
        if save_db:
            args.append("--save_db")
        
        self.run_venv(*args)
        GLib.idle_add(self.analysis_status.set_label, "Analysis complete!")


if __name__ == "__main__":
    app = SteamReviewApp()
    app.run(None)
