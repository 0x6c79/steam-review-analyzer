import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw
     
class MinimalAdwApp(Adw.Application):
    def __init__(self):
        super().__init__(application_id="org.example.MinimalAdwApp")   
    
    def do_activate(self):
        window = Adw.ApplicationWindow(application=self)
        window.set_title("Minimal Adwaita Window")
        window.set_default_size(400, 300)
        window.present()
     
if __name__ =="__main__":
    app = MinimalAdwApp()
    app.run(None)
