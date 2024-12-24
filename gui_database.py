# gui_database.py

import tkinter as tk
from tkinter import ttk, messagebox
import webbrowser

from gui_embeddings import visualize_embeddings
from gui_utils import initialize_checkboxes, handle_tree_click, refresh_checkboxes

class DatabaseViewTab(ttk.Frame):
    """
    Database tab:
      - Shows all documents in the DB with checkboxes for removal
      - Double-click row to open PDF
      - "Visualize Embeddings" button => shows a similarity graph
    """
    def __init__(self, parent, db, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.db = db
        self.selected_rows = set()
        self.db_rows = []

        top_frame = ttk.Frame(self)
        top_frame.pack(fill=tk.X)

        self.refresh_btn = ttk.Button(top_frame, text="Refresh", command=self.populate_list)
        self.refresh_btn.pack(side=tk.LEFT, padx=5, pady=5)

        self.remove_btn = ttk.Button(top_frame, text="Remove Selected", command=self.on_remove_selected)
        self.remove_btn.pack(side=tk.LEFT, padx=5, pady=5)

        self.vis_btn = ttk.Button(top_frame, text="Visualize Embeddings", command=self.on_visualize)
        self.vis_btn.pack(side=tk.LEFT, padx=5, pady=5)

        # Treeview with columns
        columns = ("Selected", "ID", "Title", "Version", "Author")
        self.tree = ttk.Treeview(self, columns=columns, show="headings", height=15)
        self.tree.heading("Selected", text="Select")
        self.tree.heading("ID", text="ID")
        self.tree.heading("Title", text="Title")
        self.tree.heading("Version", text="Ver")
        self.tree.heading("Author", text="Author")

        self.tree.column("Selected", width=60, anchor=tk.CENTER)
        self.tree.column("ID", width=100)
        self.tree.column("Title", width=300)
        self.tree.column("Version", width=60)
        self.tree.column("Author", width=200)

        self.tree.bind("<Button-1>", self.on_tree_click)
        self.tree.bind("<Double-1>", self.on_double_click_row)

        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(self, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def populate_list(self):
        self.tree.delete(*self.tree.get_children())
        self.selected_rows.clear()
        self.db_rows.clear()
        try:
            rows = self.db.cursor.execute(
                "SELECT id, title, version, author, url, summary FROM 'arxiv entries'"
            ).fetchall()
            self.db_rows = rows
            for i, row in enumerate(rows):
                # row = (id, title, version, author, url, summary)
                row_id = str(i)
                # We'll show just partial title
                self.tree.insert(
                    "",
                    tk.END,
                    iid=row_id,
                    values=("", row[0], row[1][:80], row[2], row[3])
                )
        except Exception as e:
            messagebox.showerror("DB Error", str(e))

    def on_tree_click(self, event):
        region = self.tree.identify("region", event.x, event.y)
        if region == "heading":
            return
        if region != "cell":
            return
        col = self.tree.identify_column(event.x)
        if col == "#1":  # "Selected"
            row_id = self.tree.identify_row(event.y)
            if row_id:
                if row_id in self.selected_rows:
                    self.selected_rows.remove(row_id)
                else:
                    self.selected_rows.add(row_id)
                self._refresh_checkboxes()

    def _refresh_checkboxes(self):
        for row_id in self.tree.get_children():
            symbol = "☑" if row_id in self.selected_rows else "☐"
            self.tree.set(row_id, "Selected", symbol)

    def on_double_click_row(self, event):
        """
        Open the PDF in a browser for the double-clicked row.
        """
        row_id = self.tree.identify_row(event.y)
        if not row_id:
            return
        idx = int(row_id)
        row = self.db_rows[idx]
        doc_id, doc_title, doc_version, doc_author, doc_url, doc_summary = row
        # doc_id (like '2301.12345'), doc_version (like '1'), etc.
        pdf_url = f"http://arxiv.org/pdf/{doc_id}v{doc_version}.pdf"
        webbrowser.open(pdf_url)

    def on_remove_selected(self):
        if not self.selected_rows:
            messagebox.showinfo("No Selection", "Please select at least one item to remove.")
            return
        confirm = messagebox.askyesno("Confirm Removal",
                                      f"Remove {len(self.selected_rows)} entries from DB?")
        if not confirm:
            return
        try:
            for row_id in self.selected_rows:
                idx = int(row_id)
                doc_id = self.db_rows[idx][0]
                self.db.cursor.execute("DELETE FROM 'arxiv entries' WHERE id = ?", (doc_id,))
                self.db.cursor.execute("DELETE FROM 'authors' WHERE id = ?", (doc_id,))
                self.db.cursor.execute("DELETE FROM 'tags' WHERE id = ?", (doc_id,))
            self.db.connection.commit()
            self.populate_list()
            messagebox.showinfo("Deleted", "Selected entries removed from database.")
        except Exception as e:
            messagebox.showerror("DB Error", str(e))

    def on_visualize(self):
        """
        Calls a function that fetches all entries from DB, embeds them, and
        displays a graph of their relationships in a popup.
        """
        rows = self.db.cursor.execute("SELECT id, summary, author, title FROM 'arxiv entries'").fetchall()
        if not rows:
            messagebox.showinfo("Empty", "No documents in DB to visualize.")
            return
        try:
            visualize_embeddings(rows, parent=self)
        except Exception as ex:
            messagebox.showerror("Visualization Error", str(ex))



    def populate_list(self):
        self.tree.delete(*self.tree.get_children())
        self.selected_rows.clear()
        self.db_rows.clear()
        try:
            rows = self.db.cursor.execute(
                "SELECT id, title, version, author, url, summary FROM 'arxiv entries'"
            ).fetchall()
            self.db_rows = rows
            for i, row in enumerate(rows):
                # row = (id, title, version, author, url, summary)
                row_id = str(i)
                # Initialize with empty checkboxes
                self.tree.insert(
                "",
                tk.END,
                iid=row_id,
                values=("☐", row[0], row[1][:80], row[2], row[3])
            )
        except Exception as e:
            messagebox.showerror("DB Error", str(e))


    def on_tree_click(self, event):
        handle_tree_click(event, self.tree, self.selected_rows)