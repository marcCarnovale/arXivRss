# -*- coding: utf-8 -*-
"""
database.py

Contains the DataBase class for handling arXiv entries in a SQLite database.
"""

import sqlite3 as sql

class DataBase:
    """
    Simple SQLite database manager for storing arXiv entries.
    """
    def __init__(self, path="database.db"):
        self.path = path
        self.isOpen = False
        self.connection = None
        self.cursor = None

    def open(self):
        if not self.isOpen:
            self.connection = sql.connect(self.path)
            self.cursor = self.connection.cursor()
            self.isOpen = True

    def close(self):
        if self.isOpen:
            self.connection.close()
            self.isOpen = False

    def create_tables(self):
        """
        Creates the needed tables if they do not exist yet.
        """
        if not self.isOpen:
            self.open()

        # Create 'arxiv entries' table
        # We'll store (id, title, version, primary_author, url, summary)
        query_entries = """CREATE TABLE IF NOT EXISTS 'arxiv entries'(
                            id TEXT,
                            title TEXT,
                            version TEXT,
                            author TEXT,
                            url TEXT,
                            summary TEXT
                          );"""
        self.cursor.execute(query_entries)

        # Create 'tags' table
        # We'll store (id, tag)
        query_tags = """CREATE TABLE IF NOT EXISTS 'tags'(
                            id TEXT,
                            tag TEXT
                        );"""
        self.cursor.execute(query_tags)

        # Create 'authors' table
        # We'll store (id, author)
        query_authors = """CREATE TABLE IF NOT EXISTS 'authors'(
                                id TEXT,
                                author TEXT
                           );"""
        self.cursor.execute(query_authors)

        self.cursor.execute("""CREATE TABLE IF NOT EXISTS 'subscriptions'(
                                sub_id INTEGER PRIMARY KEY AUTOINCREMENT,
                                sub_type TEXT,
                                query TEXT,
                                last_fetch TEXT
                              );""")
        
        self.connection.commit()


    def add_subscription(self, sub_type, query):
        """
        Insert a new subscription row with sub_type = 'author'|'topic'
        and the query string. We'll set last_fetch to '20000101' initially
        so we pick up old papers, or today's date, etc.
        """
        if not self.isOpen:
            self.open()

        # By default, we might set last_fetch to '20000101'
        default_date = '20000101'
        self.cursor.execute(
            "INSERT INTO 'subscriptions'(sub_type, query, last_fetch) VALUES(?,?,?)",
            (sub_type, query, default_date)
        )
        self.connection.commit()

    def get_subscriptions(self):
        """
        Return list of (sub_id, sub_type, query, last_fetch).
        """
        if not self.isOpen:
            self.open()
        rows = self.cursor.execute(
            "SELECT sub_id, sub_type, query, last_fetch FROM 'subscriptions'"
        ).fetchall()
        return rows

    def update_subscription_date(self, sub_id, new_date):
        """
        Set last_fetch = new_date for the given subscription ID.
        """
        if not self.isOpen:
            self.open()
        self.cursor.execute(
            "UPDATE 'subscriptions' SET last_fetch = ? WHERE sub_id = ?",
            (new_date, sub_id)
        )
        self.connection.commit()
        
    def clear_tables(self):
        """
        Removes any existing data from the relevant tables (drops the tables).
        """
        if not self.isOpen:
            self.open()

        # Identify and drop relevant tables
        tables = self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
        table_names = [t[0] for t in tables]
        for name in table_names:
            if name in ['arxiv entries', 'tags', 'authors']:
                print("Deleting table:", name)
                self.cursor.execute(f"DROP TABLE '{name}'")

        self.connection.commit()

    def add_entry(self, entry):
        """
        Adds a new entry to the database, inserting any tags/authors as needed.
        """
        if not self.isOpen:
            self.open()

        # Check if the entry already exists
        result = self.cursor.execute(
            "SELECT * FROM 'arxiv entries' WHERE id = ?",
            (entry.id,)
        ).fetchall()

        if len(result) == 0:
            print("Adding new entry:", entry.url)
            self.cursor.execute(
                "INSERT INTO 'arxiv entries' VALUES (?,?,?,?,?,?)",
                (
                    entry.id,
                    entry.title,
                    entry.version,
                    entry.authors[0] if entry.authors else '_None',
                    entry.url,
                    entry.summary
                )
            )

            # Insert tags
            if entry.tags:
                for tag in entry.tags:
                    if tag == '_None':
                        print("Cannot commit tag '_None'. Removing it.")
                        entry.tags.remove('_None')
                    else:
                        self.cursor.execute(
                            "INSERT INTO 'tags' VALUES (?,?)",
                            (entry.id, tag)
                        )
            else:
                # If no tags exist, store '_None'
                self.cursor.execute(
                    "INSERT INTO 'tags' VALUES (?,?)",
                    (entry.id, '_None')
                )

            # Insert authors
            if entry.authors:
                for author in entry.authors:
                    self.cursor.execute(
                        "INSERT INTO 'authors' VALUES (?,?)",
                        (entry.id, author)
                    )
            else:
                self.cursor.execute(
                    "INSERT INTO 'authors' VALUES (?,?)",
                    (entry.id, '_None')
                )

        self.connection.commit()
