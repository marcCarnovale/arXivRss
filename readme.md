# arXiv RSS Reader

An arXiv-specific RSS reader that allows users to search, subscribe, and manage arXiv entries with ease. This project is designed to streamline the process of discovering and curating research papers tailored to the user's interests.

## **Project Purpose**

The arXiv RSS Reader provides a comprehensive interface to:
- Query arXiv with advanced search options.
- Subscribe to authors or topics of interest.
- Manage and visualize a personal database of selected entries.
- Automatically generate keywords and create semantic relationships between papers.

## **Features**

### **Search Tab**
- Perform advanced arXiv queries with fields:
  - Title
  - Abstract
  - Author
  - Content
  - All Fields
- Specify date ranges for filtering results.
- View search results in a table with checkboxes for selection.
- Auto-generate keywords from abstracts using semantic analysis.
- Add selected entries to a persistent database.

### **Database Tab**
- Display all stored entries with metadata (ID, title, version, author).
- Checkboxes for selecting entries to remove.
- Open PDFs directly in the browser by double-clicking an entry.
- Visualize relationships between entries using semantic embeddings.

### **Digest Tab**
- Subscribe to authors or topics of interest.
- Fetch new results since the last refresh for subscriptions.
- Add or discard results to/from the database.
- Automatically update the last fetch date for each subscription.

### **Semantic Embeddings**
- Generate embeddings for abstracts using SentenceTransformers.
- Create a similarity graph to visualize relationships between stored entries.
- Extract keywords for enhanced search and categorization.

### **Keyboard Shortcuts**
- Support for standard text editing shortcuts:
  - **Ctrl+C:** Copy
  - **Ctrl+X:** Cut
  - **Ctrl+V:** Paste
  - **Ctrl+A:** Select all (Known issue: not functioning consistently in entry widgets).

---

## **Known Bugs**
- **Ctrl+A for Select All:**
  - The shortcut does not consistently select all text in entry widgets. Investigation is ongoing.
- **Checkbox Visibility:**
  - In some cases, checkboxes may not appear until interacted with. This is being actively reviewed.

---

## **Future Enhancements**
- Add semantic search capabilities to allow querying by related topics.
- Improve performance with asynchronous calls for non-blocking UI updates.
- Introduce advanced subscription filtering (e.g., filter by citation count or specific fields).
- Implement export/import functionality for the database in JSON or CSV formats.
- Expand accessibility features and keyboard navigation.

---

## **Installation**

1. Clone the repository:
   ```bash
   git clone https://github.com/your-username/arxiv-rss-reader.git

2. Install the required dependencies:
    ```bash
    pip install -r requirements.txt

3. Run the application:
    ```python
    python main.py


## **Contributing**
- Contributions are welcome! If you encounter a bug or have a feature suggestion, please open an issue or submit a pull request.

## **License**
- This project is licensed under the MIT License. 
