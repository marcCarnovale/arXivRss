# main_gui.py

import tkinter as tk
from tkinter import ttk, messagebox
from database import DataBase
from gui_search import ArxivSearchTab
from gui_database import DatabaseViewTab
from gui_digest import DigestTab


class MainApp(tk.Tk):
    """
    The main Tk application:
      - Creates a Notebook with 2 tabs: Search, Database
      - Maintains a shared DB object
      - Provides an on_closing method to properly close DB
    """
    def __init__(self):
        super().__init__()
        self.title("arXiv System with Embeddings")
        self.geometry("1200x700")


        # Enable global text shortcuts
        enable_text_shortcuts(self)

        # Initialize database
        self.db = DataBase("my_arxiv.db")
        self.db.open()
        self.db.create_tables()

        # Notebook
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        # Tabs
        self.tab_search = ArxivSearchTab(self.notebook, db=self.db)
        self.tab_database = DatabaseViewTab(self.notebook, db=self.db)
        self.tab_digest = DigestTab(self.notebook, db=self.db) 

        self.notebook.add(self.tab_search, text="Search")
        self.notebook.add(self.tab_database, text="Database")
        self.notebook.add(self.tab_digest, text="Digest") 

        # After creation, populate DB tab
        self.tab_database.populate_list()

    def on_closing(self):
        if messagebox.askokcancel("Quit", "Close the application?"):
            self.db.close()
            self.destroy()

def enable_text_shortcuts(root):
    """
    Enables standard text editing shortcuts (Ctrl+A, Ctrl+C, Ctrl+X, Ctrl+V)
    for all Entry and Text widgets in the application.
    """
    def select_all(event):
        widget = event.widget
        if isinstance(widget, tk.Entry):
            widget.select_range(0, tk.END)  # Select all text
            widget.icursor(tk.END)         # Move cursor to the end
            return "break"
        elif isinstance(widget, tk.Text):
            widget.tag_add("sel", "1.0", "end-1c")  # Select all text
            widget.mark_set("insert", "end-1c")     # Move cursor to the end
            widget.see("insert")
            return "break"

    def copy(event):
        root.event_generate("<<Copy>>")
        return "break"

    def cut(event):
        root.event_generate("<<Cut>>")
        return "break"

    def paste(event):
        root.event_generate("<<Paste>>")
        return "break"

    # Bind shortcuts globally for Entry and Text widgets
    widgets = ("Entry", "Text")
    for widget_class in widgets:
        root.bind_class(widget_class, "<Control-a>", select_all)
        root.bind_class(widget_class, "<Control-A>", select_all)  # Handle capital A
        root.bind_class(widget_class, "<Control-c>", copy)
        root.bind_class(widget_class, "<Control-C>", copy)
        root.bind_class(widget_class, "<Control-x>", cut)
        root.bind_class(widget_class, "<Control-X>", cut)
        root.bind_class(widget_class, "<Control-v>", paste)
        root.bind_class(widget_class, "<Control-V>", paste)



def main():
    app = MainApp()
    app.mainloop()

if __name__ == "__main__":
    main()
