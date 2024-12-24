# gui_utils.py
import tkinter as tk
import re

def extract_keywords(abstract: str, top_n=5) -> list:
    """
    Naive approach: find all words of length >= 4, count frequency,
    return top_n by freq.
    """
    if not abstract:
        return []
    words = re.findall(r"[A-Za-z]\w{3,}", abstract.lower())
    freq = {}
    for w in words:
        freq[w] = freq.get(w, 0) + 1
    sorted_words = sorted(freq.items(), key=lambda x: x[1], reverse=True)
    return [w[0] for w in sorted_words[:top_n]]


def initialize_checkboxes(tree, rows):
    """
    Populate a Treeview with rows and initialize all checkboxes as unchecked.
    :param tree: Treeview widget
    :param rows: List of tuples representing the rows to be added
    """
    for i, row in enumerate(rows):
        tree.insert("", tk.END, iid=str(i), values=("", *row))

def handle_tree_click(event, tree, selected_rows):
    """
    Toggle checkbox state in a Treeview column.
    :param event: The click event
    :param tree: Treeview widget
    :param selected_rows: A set of selected row IDs
    """
    region = tree.identify("region", event.x, event.y)
    if region != "cell":
        return
    col = tree.identify_column(event.x)
    if col == "#1":  # "Selected" column
        row_id = tree.identify_row(event.y)
        if row_id:
            if row_id in selected_rows:
                selected_rows.remove(row_id)
            else:
                selected_rows.add(row_id)
            refresh_checkboxes(tree, selected_rows)

def refresh_checkboxes(tree, selected_rows):
    """
    Update checkbox column symbols based on the selected rows.
    :param tree: Treeview widget
    :param selected_rows: A set of selected row IDs
    """
    for row_id in tree.get_children():
        symbol = "☑" if row_id in selected_rows else "☐"
        tree.set(row_id, "Selected", symbol)
