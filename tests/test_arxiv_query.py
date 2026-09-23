import urllib.parse
import xml.etree.ElementTree as ET

from arxiv_query import _build_paged_url, parse_arxiv_response

ATOM = "http://www.w3.org/2005/Atom"


def test_build_url_uses_https_and_pagination():
    url = _build_paged_url([("author", "Izabella Laba")], 200, 100)
    parsed = urllib.parse.urlparse(url)
    params = urllib.parse.parse_qs(parsed.query)
    assert parsed.scheme == "https"
    assert parsed.netloc == "export.arxiv.org"
    assert params["start"] == ["200"]
    assert params["max_results"] == ["100"]
    assert "au:Izabella Laba" in params["search_query"][0]


def test_parse_minimal_atom_entry():
    xml = f"""<feed xmlns=\"{ATOM}\">
      <entry>
        <id>https://arxiv.org/abs/2403.12603v2</id>
        <title>Obtaining the Fourier spectrum via Fourier coefficients</title>
        <summary>Summary.</summary>
        <author><name>Marc Carnovale</name></author>
        <published>2024-03-19T10:12:48Z</published>
        <updated>2024-03-19T10:12:48Z</updated>
      </entry>
    </feed>"""
    root = ET.fromstring(xml)
    entries = parse_arxiv_response(root, f"{{{ATOM}}}")
    assert len(entries) == 1
    assert entries[0].id == "2403.12603"
    assert entries[0].version == "2"
    assert entries[0].authors == ["Marc Carnovale"]
