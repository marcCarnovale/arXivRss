# gui_digest.py

import tkinter as tk
from tkinter import ttk, messagebox
import re
import datetime

from arxiv_query import queryArXiv, parse_arxiv_response
from gui_utils import extract_keywords

from gui_utils import initialize_checkboxes, handle_tree_click, refresh_checkboxes

class DigestTab(ttk.Frame):
    """
    A new "Digest" tab that handles user subscriptions to authors or topics.
    On refresh, we fetch new results since last_fetch for each subscription,
    display them, and let the user keep or discard them.
    """
    def __init__(self, parent, db, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.db = db
        self.subscriptions = []

        # Top area: create new subscription
        top_frame = ttk.LabelFrame(self, text="Manage Subscriptions")
        top_frame.pack(fill=tk.X, padx=5, pady=5)

        self.sub_type_var = tk.StringVar(value="author")
        type_frame = ttk.Frame(top_frame)
        type_frame.pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(type_frame, text="Author", variable=self.sub_type_var, value="author").pack(anchor=tk.W)
        ttk.Radiobutton(type_frame, text="Topic", variable=self.sub_type_var, value="topic").pack(anchor=tk.W)

        self.query_var = tk.StringVar()
        ttk.Label(top_frame, text="Query:").pack(side=tk.LEFT, padx=5)
        ttk.Entry(top_frame, textvariable=self.query_var, width=40).pack(side=tk.LEFT, padx=5)
        ttk.Button(top_frame, text="Add Subscription", command=self.on_add_subscription).pack(side=tk.LEFT, padx=5)

        # Refresh button
        self.refresh_btn = ttk.Button(top_frame, text="Refresh Subscriptions", command=self.on_refresh_subscriptions)
        self.refresh_btn.pack(side=tk.RIGHT, padx=5)

        # Middle area: list of subscriptions
        subs_frame = ttk.LabelFrame(self, text="Current Subscriptions")
        subs_frame.pack(fill=tk.X, padx=5, pady=5)

        self.sub_list = tk.Listbox(subs_frame, height=4)
        self.sub_list.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.update_subscription_list()

        # Lower area: results table
        results_frame = ttk.LabelFrame(self, text="Digest Results")
        results_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.columns = ("Selected", "Title", "Authors", "Published", "Subscription")
        self.tree = ttk.Treeview(results_frame, columns=self.columns, show="headings", height=12)
        self.tree.heading("Selected", text="Select")
        self.tree.heading("Title", text="Title")
        self.tree.heading("Authors", text="Authors")
        self.tree.heading("Published", text="Published")
        self.tree.heading("Subscription", text="From Subscription")

        self.tree.column("Selected", width=60, anchor=tk.CENTER)
        self.tree.column("Title", width=300)
        self.tree.column("Authors", width=200)
        self.tree.column("Published", width=120)
        self.tree.column("Subscription", width=150)

        self.tree.bind("<Button-1>", self.on_tree_click)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(results_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.save_button = ttk.Button(results_frame, text="Add Selected to DB", command=self.on_save_to_db)
        self.save_button.pack(side=tk.BOTTOM, pady=5)

        self.fetched_entries = []    # (entry, sub_id, published_date)
        self.selected_rows = set()   # track which rows are checked

    def update_subscription_list(self):
        """
        Refresh the listbox that shows the current subscriptions from DB.
        """
        self.sub_list.delete(0, tk.END)
        self.subscriptions = self.db.get_subscriptions()  # returns sub_id, sub_type, query, last_fetch
        for s in self.subscriptions:
            sub_id, sub_type, query, last_fetch = s
            label = f"[{sub_type}] {query} (last fetch: {last_fetch})"
            self.sub_list.insert(tk.END, label)

    def on_add_subscription(self):
        sub_type = self.sub_type_var.get()
        query = self.query_var.get().strip()
        if not query:
            messagebox.showwarning("No Query", "Please enter a query.")
            return
        self.db.add_subscription(sub_type, query)
        messagebox.showinfo("Subscription Added", f"Added subscription for {sub_type}:{query}")
        self.update_subscription_list()
        self.query_var.set("")

    def on_refresh_subscriptions(self):
        """
        For each subscription, fetch new results since last_fetch, show them in the tree.
        We'll keep track in `self.fetched_entries`.
        """
        self.tree.delete(*self.tree.get_children())
        self.selected_rows.clear()
        self.fetched_entries.clear()

        self.subscriptions = self.db.get_subscriptions()
        if not self.subscriptions:
            messagebox.showinfo("No Subscriptions", "You have no subscriptions yet.")
            return

        # For each subscription
        for sub_id, sub_type, query, last_fetch in self.subscriptions:
            # If last_fetch is '20000101', we'll get older items too
            # We'll do local date filtering in arxiv_query
            query_parts = []
            if sub_type == "author":
                query_parts.append(("author", query))
            elif sub_type == "topic":
                # treat topic as 'all' or 'abstract'
                query_parts.append(("all", query))
            else:
                query_parts.append(("all", query))

            try:
                tree, ns = queryArXiv(query_parts, start_date=last_fetch, end_date=None)
                new_entries = parse_arxiv_response(tree.getroot(), ns)

                for i, e in enumerate(new_entries):
                    # Auto-generate keywords
                    auto_keywords = extract_keywords(e.summary, top_n=5)
                    e.tags.extend(auto_keywords)

                    # Guess published date
                    pub_str = e.published[:10] if e.published else ""
                    row_id = f"{sub_id}-{len(self.fetched_entries)}"  # unique

                    # Insert entry into the tree with an empty checkbox
                    self.tree.insert(
                        "",
                        tk.END,
                        iid=row_id,
                        values=("☐", e.title[:60], ", ".join(e.authors), pub_str, f"{sub_type}:{query}")
                    )
                    
                    # Track the entry
                    self.fetched_entries.append((e, sub_id, pub_str))

            except Exception as ex:
                messagebox.showerror("Subscription Error", str(ex))

        # Ensure all checkboxes are initialized as empty
        for row_id in self.tree.get_children():
            self.tree.set(row_id, "Selected", "☐")

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

    def on_save_to_db(self):
        """
        Add the checked items to the main DB, and update the subscription's last_fetch
        to the newest date among them.
        """
        if not self.selected_rows:
            messagebox.showinfo("No Selection", "Check at least one item to save.")
            return
        # We'll collect by subscription -> the max date we got
        # Then update last_fetch
        sub_newdate_map = {}  # sub_id -> max published date string

        def date_str_to_dt(d):
            # parse "YYYY-MM-DD" => datetime
            try:
                return datetime.datetime.strptime(d, "%Y-%m-%d")
            except:
                return None

        for row_id in self.selected_rows:
            # row_id is something like "2-14"
            # We can parse our self.fetched_entries list to find the matching index
            # simpler approach: build a dictionary at on_refresh time or do a search
            # We'll do a small loop:
            for i, (entry, sub_id, pub_str) in enumerate(self.fetched_entries):
                test_rowid = f"{sub_id}-{i}"
                if test_rowid == row_id:
                    # add entry to DB
                    self.db.add_entry(entry)
                    # track date
                    dt = date_str_to_dt(pub_str)
                    if dt:
                        if sub_id not in sub_newdate_map:
                            sub_newdate_map[sub_id] = dt
                        else:
                            if dt > sub_newdate_map[sub_id]:
                                sub_newdate_map[sub_id] = dt
                    break

        # Now update last_fetch for each sub_id
        for sub_id, dt in sub_newdate_map.items():
            # store as YYYYMMDD
            new_str = dt.strftime("%Y%m%d")
            self.db.update_subscription_date(sub_id, new_str)

        messagebox.showinfo("Done", "Selected entries added. Subscriptions updated.")
        # Optionally clear them out of the tree
        for row_id in list(self.selected_rows):
            self.tree.delete(row_id)
        self.selected_rows.clear()
