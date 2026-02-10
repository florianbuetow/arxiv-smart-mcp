"""Atom XML parser for arXiv API responses."""

from __future__ import annotations

from defusedxml import ElementTree

from arxivsmart.arxiv.types import Author, Paper, SearchResult

_NS: dict[str, str] = {
    "atom": "http://www.w3.org/2005/Atom",
    "opensearch": "http://a9.com/-/spec/opensearch/1.1/",
    "arxiv": "http://arxiv.org/schemas/atom",
}


def _find_text(element: ElementTree.Element, tag: str) -> str:
    """Find text content of a child element, raising if missing."""
    child = element.find(tag, _NS)
    if child is None:
        raise ValueError(f"missing required element: {tag}")
    if child.text is None:
        return ""
    return child.text.strip()


def _find_text_optional(element: ElementTree.Element, tag: str) -> str:
    """Find text content of an optional child element, returning empty string if absent."""
    child = element.find(tag, _NS)
    if child is None:
        return ""
    if child.text is None:
        return ""
    return child.text.strip()


def parse_author(author_element: ElementTree.Element) -> Author:
    """Parse a single <author> element into an Author."""
    name = _find_text(author_element, "atom:name")
    affiliation = _find_text_optional(author_element, "arxiv:affiliation")
    return Author(name=name, affiliation=affiliation)


def _extract_arxiv_id(entry_id: str) -> str:
    """Extract arXiv ID from the full Atom entry ID URL."""
    # entry_id looks like "http://arxiv.org/abs/2301.00001v1"
    parts = entry_id.split("/abs/")
    if len(parts) != 2:
        raise ValueError(f"unexpected entry id format: {entry_id}")
    return parts[1]


def _extract_pdf_url(entry: ElementTree.Element) -> str:
    """Extract PDF URL from entry links."""
    for link in entry.findall("atom:link", _NS):
        if link.get("title") == "pdf":
            href = link.get("href")
            if href is not None:
                return href
    return ""


def parse_entry(entry: ElementTree.Element) -> Paper:
    """Parse a single <entry> element into a Paper."""
    entry_id = _find_text(entry, "atom:id")
    arxiv_id = _extract_arxiv_id(entry_id)
    title = _find_text(entry, "atom:title")
    # Normalize whitespace in title
    title = " ".join(title.split())
    summary = _find_text(entry, "atom:summary").strip()

    authors = [parse_author(a) for a in entry.findall("atom:author", _NS)]

    categories: list[str] = []
    for cat in entry.findall("atom:category", _NS):
        term = cat.get("term")
        if term is not None:
            categories.append(term)

    primary_cat_elem = entry.find("arxiv:primary_category", _NS)
    if primary_cat_elem is not None:
        primary_term = primary_cat_elem.get("term")
        if primary_term is None:
            raise ValueError("primary_category element missing term attribute")
        primary_category = primary_term
    else:
        raise ValueError("missing arxiv:primary_category element")

    published = _find_text(entry, "atom:published")
    updated = _find_text(entry, "atom:updated")
    pdf_url = _extract_pdf_url(entry)
    abstract_url = entry_id

    doi = _find_text_optional(entry, "arxiv:doi")
    comment = _find_text_optional(entry, "arxiv:comment")
    journal_ref = _find_text_optional(entry, "arxiv:journal_ref")

    return Paper(
        arxiv_id=arxiv_id,
        title=title,
        summary=summary,
        authors=authors,
        categories=categories,
        primary_category=primary_category,
        published=published,
        updated=updated,
        pdf_url=pdf_url,
        abstract_url=abstract_url,
        doi=doi,
        comment=comment,
        journal_ref=journal_ref,
    )


def parse_search_response(xml_bytes: bytes) -> SearchResult:
    """Parse a full Atom feed from arXiv search API."""
    root = ElementTree.fromstring(xml_bytes)

    total_text = _find_text(root, "opensearch:totalResults")
    start_text = _find_text(root, "opensearch:startIndex")
    per_page_text = _find_text(root, "opensearch:itemsPerPage")

    total_results = int(total_text)
    start_index = int(start_text)
    items_per_page = int(per_page_text)

    papers = [parse_entry(entry) for entry in root.findall("atom:entry", _NS)]

    return SearchResult(
        total_results=total_results,
        start_index=start_index,
        items_per_page=items_per_page,
        papers=papers,
    )
