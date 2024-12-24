# -*- coding: utf-8 -*-
"""
arxiv_query.py

Fetches *all* results for a given search by paging through the Atom feed,
then locally filters out <entry> elements with <published> outside [start_date, end_date].
Finally, returns (tree, ns) that includes only the kept entries.

Usage (unchanged from older code):
    tree, ns = queryArXiv([("author", "Bergelson")],
                          start_date="20210101", end_date="20211231")
    entries = parse_arxiv_response(tree.getroot(), ns)
"""

import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
import re
from datetime import datetime

###############################################################################
#                               Data Classes
###############################################################################

class Entry:
    def __init__(self, arxiv_id, version, title, summary, authors, url,
                 tags=None, published=None, updated=None):
        self.id = arxiv_id
        self.version = version
        self.title = title
        self.summary = summary
        self.authors = authors
        self.url = url
        self.tags = tags if tags else []
        self.published = published
        self.updated = updated

    def __repr__(self):
        return f"Entry(id={self.id}, version={self.version}, title={self.title})"

###############################################################################
#                         Build Search Expression
###############################################################################

def build_arxiv_search_expression(field: str, keyword: str) -> str:
    """
    Convert (field, keyword) to e.g. 'au:Bergelson' or 'ti:Host'.
    Fields: 'author'->au:, 'title'->ti:, 'abstract'->abs:, 'all'->all:
    """
    prefix_map = {
        "author":   "au:",
        "title":    "ti:",
        "abstract": "abs:",
        "all":      "all:",
    }
    prefix = prefix_map.get(field, "all:")
    return prefix + keyword


def getArXivQuery(query_parts, start_date=None, end_date=None, max_results=2000):
    """
    Builds a search query (URL) for *one page* of results, ignoring date.
    The user might pass start_date/end_date but we won't embed them server-side.
    We'll do local date filtering after collecting all entries.

    :param query_parts: list of (field, keyword)
    :param start_date:  ignored for server query, used only for local filtering
    :param end_date:    ignored for server query, used only for local filtering
    :param max_results: how many to retrieve *in one chunk*
    """
    base_url = "http://export.arxiv.org/api/query?search_query="

    # Combine query parts
    exprs = []
    for field, kw in query_parts:
        exprs.append(build_arxiv_search_expression(field, kw))
    if not exprs:
        exprs = ["all:*"]
    combined_expr = "+AND+".join(exprs)

    encoded_expr = urllib.parse.quote_plus(combined_expr)

    # We won't add date constraints to the server query
    # because 'submittedDate:[ ... ]' is broken

    # We'll return a base url; the caller can tack on &start=..., &sortBy=..., etc.
    # But to preserve your old function signature, let's just do it here for one page
    return f"{base_url}{encoded_expr}&start=0&max_results={max_results}"

###############################################################################
#                 The Main Paging + Local Filter Approach
###############################################################################

def queryArXiv(query_parts, start_date=None, end_date=None):
    """
    Returns (tree, ns) for *all* results. We do the paging manually, retrieve
    up to 2000 results at a time, store them in a single <feed>, then remove
    <entry> elements outside [start_date, end_date] by <published> date.

    :param query_parts: e.g. [("author","Bergelson")]
    :param start_date: e.g. "20230101" => local filter min published date
    :param end_date:   e.g. "20231231" => local filter max published date
    :return: (tree, ns) with the pruned feed
    """
    # We'll gather <entry> from all pages in one list, then build a single feed root.
    all_entries = []
    ns = ""  # we'll store once we parse the first page

    chunk_size = 2000  # max arXiv allows in one page
    start_index = 0
    total_collected = 0

    while True:
        # 1) Build page-specific URL
        url = _build_paged_url(query_parts, start_index, chunk_size)
        # 2) Fetch data, parse
        data = urllib.request.urlopen(url).read().decode("UTF-8")
        root = ET.fromstring(data)
        if start_index == 0:
            # Extract namespace from the first page
            ns_match = re.match(r'{.*}', root.tag)
            ns = ns_match.group(0) if ns_match else ""
        # 3) gather <entry> from this page
        page_entries = root.findall(f"{ns}entry")
        if not page_entries:
            # no more results or we reached the end
            break
        all_entries.extend(page_entries)
        total_collected += len(page_entries)

        # 4) see if we got fewer than chunk_size => last page
        # Also check if we've reached the 30000 limit (arxiv API can do up to 30000 in slices).
        if len(page_entries) < chunk_size or total_collected >= 30000:
            break
        # else increment start
        start_index += chunk_size

    # Now we have up to 30000 <entry> items in 'all_entries'.
    # We'll create a new root feed containing them all:
    # We'll do something minimal: parse an empty feed skeleton, or we can reuse the last feed's <title> etc.

    combined_root = _create_empty_feed(ns, original_root=root)
    for e in all_entries:
        combined_root.append(e)

    # local filtering
    if start_date or end_date:
        sdt = _parse_user_date(start_date, is_start=True) if start_date else None
        edt = _parse_user_date(end_date,   is_start=False) if end_date else None
        # remove out-of-range
        for entry_elem in combined_root.findall(f"{ns}entry"):
            published_text = None
            for child in entry_elem:
                if child.tag == ns + "published":
                    published_text = child.text
                    break
            pub_dt = _parse_atom_date(published_text)
            if (not pub_dt) or (sdt and pub_dt < sdt) or (edt and pub_dt > edt):
                combined_root.remove(entry_elem)

    # return (tree, ns)
    final_tree = ET.ElementTree(combined_root)
    return final_tree, ns


def parse_arxiv_response(root, ns, tags=None):
    """
    Unchanged from your older code: parse the final <feed> (which we've pruned).
    """
    entries = []
    for entry_elem in root:
        if entry_elem.tag == ns + "entry":
            authors_list = []
            summary = ""
            title = ""
            arxiv_id = ""
            version = 1
            url = ""
            published = None
            updated = None

            for child in entry_elem:
                tag_name = child.tag
                if tag_name == ns + "id":
                    url = child.text
                    split_id = url.split('/')[-1].split('v')
                    arxiv_id = split_id[0]
                    if len(split_id) > 1:
                        version = split_id[1]
                elif tag_name == ns + "title":
                    title = child.text
                elif tag_name == ns + "author":
                    for author_child in child:
                        if author_child.tag == ns + "name":
                            authors_list.append(author_child.text)
                elif tag_name == ns + "summary":
                    summary = child.text
                elif tag_name == ns + "published":
                    published = child.text
                elif tag_name == ns + "updated":
                    updated = child.text

            entry_obj = Entry(
                arxiv_id=arxiv_id,
                version=version,
                title=title,
                summary=summary,
                authors=authors_list,
                url=url,
                tags=tags,
                published=published,
                updated=updated
            )
            entries.append(entry_obj)
    return entries


###############################################################################
#                           Internal Helpers
###############################################################################

def _build_paged_url(query_parts, start_index, chunk_size):
    """
    Build a URL for one page of results, ignoring date constraints.
    """
    base_url = "http://export.arxiv.org/api/query?search_query="
    exprs = []
    for field, kw in query_parts:
        exprs.append(build_arxiv_search_expression(field, kw))
    if not exprs:
        exprs = ["all:*"]
    combined_expr = "+AND+".join(exprs)
    encoded_expr = urllib.parse.quote_plus(combined_expr)
    # We'll sort by submittedDate descending so that the newest appear first
    # or you can do lastUpdatedDate if you want the newest revised papers
    url = (f"{base_url}{encoded_expr}"
           f"&start={start_index}"
           f"&max_results={chunk_size}"
           f"&sortBy=submittedDate"
           f"&sortOrder=descending")
    return url


def _create_empty_feed(ns, original_root):
    """
    Build a minimal <feed> element as the container for the combined entries.

    We'll copy some metadata from the last or first feed if we want.
    For simplicity, let's clone the original's top-level <feed> and remove children.
    """
    # We'll clone the original feed's tag, but remove <entry> children
    feed_tag = original_root.tag  # e.g. '{http://www.w3.org/2005/Atom}feed'
    new_feed = ET.Element(feed_tag)
    # copy children except <entry>
    for child in original_root:
        if child.tag.endswith("entry"):
            continue
        # copy a shallow copy
        new_child = ET.Element(child.tag, child.attrib)
        new_child.text = child.text
        new_child.tail = child.tail
        # If you want to copy sub-children of <title>, <id>, <link>, etc., do that here
        # or simply skip them if you only care about <entry>.
        new_feed.append(new_child)
    return new_feed


def _parse_user_date(date_str, is_start=True):
    """
    Convert user input '20230101' => datetime(2023,01,01,00,00,00) if is_start
    or => datetime(2023,01,01,23,59,59) if not is_start.
    """
    if not date_str:
        return None
    ds = date_str.strip()
    # if 8 digits => "YYYY-MM-DD"
    if len(ds) == 8 and ds.isdigit():
        ds = ds[:4] + "-" + ds[4:6] + "-" + ds[6:8]
    try:
        dt = datetime.strptime(ds, "%Y-%m-%d")
        if is_start:
            return dt.replace(hour=0, minute=0, second=0)
        else:
            return dt.replace(hour=23, minute=59, second=59)
    except ValueError:
        return None


def _parse_atom_date(atom_date_str):
    """
    parse "2023-01-10T14:23:10Z" => datetime(2023,1,10,14,23,10)
    return None if invalid
    """
    if not atom_date_str:
        return None
    s = atom_date_str.strip().replace("Z", "")
    fmts = ["%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"]
    for fmt in fmts:
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            pass
    return None
