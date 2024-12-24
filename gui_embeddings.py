# gui_embeddings.py

import tkinter as tk
import networkx as nx
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.text import Annotation
from semantic_embeddings import SemanticEmbedder
import numpy as np

def visualize_embeddings(rows, parent):
    """
    Visualize semantic embeddings as a graph.

    Args:
        rows (list): List of tuples (id, summary, author, title).
        parent: Tk parent widget.

    1. Embed the summaries.
    2. Compute a similarity matrix.
    3. Build a graph with similarity edges.
    4. Display the graph with hoverable tooltips for full titles.
    """
    # Parse data
    doc_ids = [r[0] for r in rows]
    texts = [r[1] if r[1] else "" for r in rows]
    authors = [r[2] if r[2] else "Unknown Author" for r in rows]
    titles = [r[3] if r[3] else "Untitled Paper" for r in rows]

    # Embed
    embedder = SemanticEmbedder()
    embedder.load_model()
    embeddings = embedder.embed_texts(texts)  # shape (n, dim)
    sim_matrix = embedder.compute_similarity(embeddings)  # shape (n, n)

    # Build graph
    G = nx.Graph()
    n = len(doc_ids)
    threshold = 0.7
    for i in range(n):
        label = f"{authors[i].split()[-1]}: {titles[i][:20]}..."  # Last name + truncated title
        G.add_node(doc_ids[i], label=label, full_title=titles[i])
        for j in range(i + 1, n):
            if sim_matrix[i, j] > threshold:
                G.add_edge(doc_ids[i], doc_ids[j])

    # Plot with matplotlib
    fig, ax = plt.subplots(figsize=(8, 6))
    pos = nx.spring_layout(G)
    labels = nx.get_node_attributes(G, 'label')
    nx.draw_networkx(
        G, pos, ax=ax, labels=labels, with_labels=True, node_size=500, font_size=8
    )

    # Add hover tooltips for full titles
    annot = Annotation("", xy=(0, 0), xytext=(20, 20), textcoords="offset points", 
                        bbox=dict(boxstyle="round", fc="w"), arrowprops=dict(arrowstyle="->"))
    annot.set_visible(False)
    ax.add_artist(annot)

    def update_annot(node):
        """Update the hover annotation."""
        annot.xy = pos[node]
        full_title = G.nodes[node]['full_title']
        annot.set_text(full_title)
        annot.get_bbox_patch().set_alpha(0.9)

    def on_hover(event):
        """Handle hover events to display tooltips."""
        if event.inaxes == ax:
            for node, coords in pos.items():
                x, y = coords
                if abs(x - event.xdata) < 0.03 and abs(y - event.ydata) < 0.03:
                    update_annot(node)
                    annot.set_visible(True)
                    fig.canvas.draw_idle()
                    return
            annot.set_visible(False)
            fig.canvas.draw_idle()

    fig.canvas.mpl_connect("motion_notify_event", on_hover)

    # Display the graph in a Tkinter popup
    popup = tk.Toplevel(parent)
    popup.title("Semantic Embedding Graph")
    canvas = FigureCanvasTkAgg(fig, master=popup)
    canvas.draw()
    canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

