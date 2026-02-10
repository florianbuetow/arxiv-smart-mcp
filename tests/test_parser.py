"""Tests for the arXiv Atom XML parser."""

import pytest

from arxivsmart.arxiv.parser import parse_author, parse_search_response
from arxivsmart.arxiv.types import Author

SAMPLE_ATOM_FEED = b"""<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom"
      xmlns:opensearch="http://a9.com/-/spec/opensearch/1.1/"
      xmlns:arxiv="http://arxiv.org/schemas/atom">
  <opensearch:totalResults>1</opensearch:totalResults>
  <opensearch:startIndex>0</opensearch:startIndex>
  <opensearch:itemsPerPage>1</opensearch:itemsPerPage>
  <entry>
    <id>http://arxiv.org/abs/2301.00001v1</id>
    <title>  Test Paper
    Title  </title>
    <summary>This is a test paper abstract.</summary>
    <author>
      <name>Alice Smith</name>
      <arxiv:affiliation>MIT</arxiv:affiliation>
    </author>
    <author>
      <name>Bob Jones</name>
    </author>
    <category term="cs.AI" />
    <category term="cs.LG" />
    <arxiv:primary_category term="cs.AI" />
    <published>2023-01-01T00:00:00Z</published>
    <updated>2023-01-02T00:00:00Z</updated>
    <link href="http://arxiv.org/pdf/2301.00001v1" title="pdf" type="application/pdf" />
    <arxiv:doi>10.1234/test</arxiv:doi>
    <arxiv:comment>10 pages, 3 figures</arxiv:comment>
    <arxiv:journal_ref>Nature 2023</arxiv:journal_ref>
  </entry>
</feed>"""

SAMPLE_ENTRY_NO_OPTIONAL = b"""<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom"
      xmlns:opensearch="http://a9.com/-/spec/opensearch/1.1/"
      xmlns:arxiv="http://arxiv.org/schemas/atom">
  <opensearch:totalResults>1</opensearch:totalResults>
  <opensearch:startIndex>0</opensearch:startIndex>
  <opensearch:itemsPerPage>1</opensearch:itemsPerPage>
  <entry>
    <id>http://arxiv.org/abs/2301.00002v1</id>
    <title>Minimal Paper</title>
    <summary>Minimal abstract.</summary>
    <author>
      <name>Charlie Brown</name>
    </author>
    <category term="math.CO" />
    <arxiv:primary_category term="math.CO" />
    <published>2023-02-01T00:00:00Z</published>
    <updated>2023-02-01T00:00:00Z</updated>
  </entry>
</feed>"""


class TestParseSearchResponse:
    def test_parse_full_feed(self):
        result = parse_search_response(SAMPLE_ATOM_FEED)
        assert result.total_results == 1
        assert result.start_index == 0
        assert result.items_per_page == 1
        assert len(result.papers) == 1

        paper = result.papers[0]
        assert paper.arxiv_id == "2301.00001v1"
        assert paper.title == "Test Paper Title"
        assert paper.summary == "This is a test paper abstract."
        assert len(paper.authors) == 2
        assert paper.authors[0].name == "Alice Smith"
        assert paper.authors[0].affiliation == "MIT"
        assert paper.authors[1].name == "Bob Jones"
        assert paper.authors[1].affiliation == ""
        assert paper.categories == ["cs.AI", "cs.LG"]
        assert paper.primary_category == "cs.AI"
        assert paper.published == "2023-01-01T00:00:00Z"
        assert paper.updated == "2023-01-02T00:00:00Z"
        assert paper.pdf_url == "http://arxiv.org/pdf/2301.00001v1"
        assert paper.doi == "10.1234/test"
        assert paper.comment == "10 pages, 3 figures"
        assert paper.journal_ref == "Nature 2023"

    def test_parse_entry_without_optional_fields(self):
        result = parse_search_response(SAMPLE_ENTRY_NO_OPTIONAL)
        paper = result.papers[0]
        assert paper.arxiv_id == "2301.00002v1"
        assert paper.doi == ""
        assert paper.comment == ""
        assert paper.journal_ref == ""
        assert paper.pdf_url == ""

    def test_malformed_xml_raises(self):
        from xml.etree.ElementTree import ParseError

        with pytest.raises(ParseError):
            parse_search_response(b"not xml at all")


class TestParseAuthor:
    def test_parse_author_with_affiliation(self):
        from xml.etree.ElementTree import Element, SubElement

        author_elem = Element("{http://www.w3.org/2005/Atom}author")
        name_elem = SubElement(author_elem, "{http://www.w3.org/2005/Atom}name")
        name_elem.text = "Alice Smith"
        affil_elem = SubElement(author_elem, "{http://arxiv.org/schemas/atom}affiliation")
        affil_elem.text = "MIT"

        author = parse_author(author_elem)
        assert author == Author(name="Alice Smith", affiliation="MIT")

    def test_parse_author_without_affiliation(self):
        from xml.etree.ElementTree import Element, SubElement

        author_elem = Element("{http://www.w3.org/2005/Atom}author")
        name_elem = SubElement(author_elem, "{http://www.w3.org/2005/Atom}name")
        name_elem.text = "Bob Jones"

        author = parse_author(author_elem)
        assert author == Author(name="Bob Jones", affiliation="")
