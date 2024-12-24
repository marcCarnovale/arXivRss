# gui_search.py

import tkinter as tk
from tkinter import ttk, messagebox
import re

from arxiv_query import queryArXiv, parse_arxiv_response
from gui_utils import extract_keywords, initialize_checkboxes, handle_tree_click, refresh_checkboxes
# If you want advanced embeddings for auto-keywords, you can import them here.

class ArxivSearchTab(ttk.Frame):
    """
    The "Search" tab in a Notebook:
      - Title, Abstract, Author, Content, All fields
      - Date range: start_date, end_date
      - A Treeview with checkboxes to select multiple search results
      - "Add to DB" button to add selected items
      - Each item has naive auto-generated keywords from the abstract
    """
    def __init__(self, parent, db, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.db = db

        # ========== Input Fields ==========
        input_frame = ttk.LabelFrame(self, text="ArXiv Search")
        input_frame.pack(fill=tk.X, padx=5, pady=5)

        # Title
        row1 = ttk.Frame(input_frame)
        row1.pack(fill=tk.X, pady=2)
        ttk.Label(row1, text="Title:").pack(side=tk.LEFT, padx=5)
        self.title_var = tk.StringVar()
        ttk.Entry(row1, textvariable=self.title_var, width=40).pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Abstract
        row2 = ttk.Frame(input_frame)
        row2.pack(fill=tk.X, pady=2)
        ttk.Label(row2, text="Abstract:").pack(side=tk.LEFT, padx=5)
        self.abstract_var = tk.StringVar()
        ttk.Entry(row2, textvariable=self.abstract_var, width=40).pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Author
        row3 = ttk.Frame(input_frame)
        row3.pack(fill=tk.X, pady=2)
        ttk.Label(row3, text="Author:").pack(side=tk.LEFT, padx=5)
        self.author_var = tk.StringVar()
        ttk.Entry(row3, textvariable=self.author_var, width=40).pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Content
        row4 = ttk.Frame(input_frame)
        row4.pack(fill=tk.X, pady=2)
        ttk.Label(row4, text="Content:").pack(side=tk.LEFT, padx=5)
        self.content_var = tk.StringVar()
        ttk.Entry(row4, textvariable=self.content_var, width=40).pack(side=tk.LEFT, fill=tk.X, expand=True)

        # All
        row5 = ttk.Frame(input_frame)
        row5.pack(fill=tk.X, pady=2)
        ttk.Label(row5, text="All:").pack(side=tk.LEFT, padx=5)
        self.all_var = tk.StringVar()
        ttk.Entry(row5, textvariable=self.all_var, width=40).pack(side=tk.LEFT, fill=tk.X, expand=True)

        # ========== Date Range Fields ==========
        date_frame = ttk.LabelFrame(self, text="Date Range (YYYYMMDD)")
        date_frame.pack(fill=tk.X, padx=5, pady=5)

        row6 = ttk.Frame(date_frame)
        row6.pack(fill=tk.X, pady=2)
        ttk.Label(row6, text="Start Date:").pack(side=tk.LEFT, padx=5)
        self.start_date_var = tk.StringVar()
        ttk.Entry(row6, textvariable=self.start_date_var, width=10).pack(side=tk.LEFT, padx=5)

        row7 = ttk.Frame(date_frame)
        row7.pack(fill=tk.X, pady=2)
        ttk.Label(row7, text="End Date:  ").pack(side=tk.LEFT, padx=5)
        self.end_date_var = tk.StringVar()
        ttk.Entry(row7, textvariable=self.end_date_var, width=10).pack(side=tk.LEFT, padx=5)

        self.search_button = ttk.Button(date_frame, text="Search", command=self.on_search)
        self.search_button.pack(side=tk.RIGHT, padx=5, pady=5)

        # ========== Results Table with Checkboxes ==========
        results_frame = ttk.LabelFrame(self, text="Search Results")
        results_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.columns = ("Selected", "Title", "Authors", "Published")
        self.tree = ttk.Treeview(results_frame, columns=self.columns, show="headings", height=15)
        self.tree.heading("Selected", text="Select")
        self.tree.heading("Title", text="Title")
        self.tree.heading("Authors", text="Authors")
        self.tree.heading("Published", text="Published")

        self.tree.column("Selected", width=60, anchor=tk.CENTER)
        self.tree.column("Title", width=300)
        self.tree.column("Authors", width=200)
        self.tree.column("Published", width=120)

        self.tree.bind("<Button-1>", self.on_tree_click)  # for toggling checkboxes
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(results_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # "Add to DB" button
        self.save_button = ttk.Button(results_frame, text="Add Selected to DB", command=self.on_save_to_db)
        self.save_button.pack(side=tk.BOTTOM, pady=5)

        self.fetched_entries = []
        self.selected_rows = set()  # track checked row-ids

    def on_tree_click(self, event):
        region = self.tree.identify("region", event.x, event.y)
        if region == "heading":
            return
        if region != "cell":
            return
        col = self.tree.identify_column(event.x)
        if col == "#1":  # "Selected" column
            row_id = self.tree.identify_row(event.y)
            if row_id:
                if row_id in self.selected_rows:
                    self.selected_rows.remove(row_id)
                else:
                    self.selected_rows.add(row_id)
                self._refresh_checkboxes()

    def _refresh_checkboxes(self):
        """
        Update the tree's "Selected" column to show a checkmark for rows in self.selected_rows.
        """
        for row_id in self.tree.get_children():
            symbol = "☑" if row_id in self.selected_rows else "☐"
            self.tree.set(row_id, "Selected", symbol)

    def on_search(self):
        """
        Build query_parts, call queryArXiv, parse, fill the tree with results.
        """
        # Validate date
        date_pattern = re.compile(r'^\d{8}$')
        start_date = self.start_date_var.get().strip()
        end_date = self.end_date_var.get().strip()
        if start_date and not date_pattern.match(start_date):
            messagebox.showwarning("Date Error", "Start date must be YYYYMMDD or empty.")
            return
        if end_date and not date_pattern.match(end_date):
            messagebox.showwarning("Date Error", "End date must be YYYYMMDD or empty.")
            return

        # Build query_parts
        query_parts = []
        if self.title_var.get().strip():
            query_parts.append(("title", self.title_var.get().strip()))
        if self.abstract_var.get().strip():
            query_parts.append(("abstract", self.abstract_var.get().strip()))
        if self.author_var.get().strip():
            query_parts.append(("author", self.author_var.get().strip()))
        if self.content_var.get().strip():
            query_parts.append(("content", self.content_var.get().strip()))
        if self.all_var.get().strip():
            query_parts.append(("all", self.all_var.get().strip()))

        self.tree.delete(*self.tree.get_children())
        self.selected_rows.clear()
        self.fetched_entries.clear()

        if not query_parts and not (start_date or end_date):
            messagebox.showwarning("Empty Query", "At least one field or a date range is required.")
            return

        try:
            # Actually fetch from arxiv
            arxiv_tree, ns = queryArXiv(query_parts, start_date=start_date, end_date=end_date)
            entries = parse_arxiv_response(arxiv_tree.getroot(), ns)

            for i, e in enumerate(entries):
                # For demonstration, auto-generate naive keywords from the abstract
                auto_keywords = extract_keywords(e.summary, top_n=5)
                e.tags.extend(auto_keywords)

                row_id = str(i)
                self.tree.insert(
                    "",
                    tk.END,
                    iid=row_id,
                    values=("☐", e.title[:100], ", ".join(e.authors), e.published[:10] if e.published else "")
                )

            self.fetched_entries = entries

        except Exception as ex:
            messagebox.showerror("Search Error", str(ex))


    def on_tree_click(self, event):
        handle_tree_click(event, self.tree, self.selected_rows)
        
    def on_save_to_db(self):
        """
        Insert the *selected* items into the DB, including any auto-generated tags.
        """
        if not self.selected_rows:
            messagebox.showinfo("No Selection", "Check at least one item to save.")
            return
        for row_id in self.selected_rows:
            idx = int(row_id)
            entry = self.fetched_entries[idx]
            try:
                self.db.add_entry(entry)
            except Exception as e:
                messagebox.showerror("DB Error", str(e))
        messagebox.showinfo("Done", "Selected entries added to DB.")
