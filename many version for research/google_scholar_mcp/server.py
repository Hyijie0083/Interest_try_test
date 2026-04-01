#!/usr/bin/env python3
"""
MCP Server for Google Scholar.

This server provides tools to search Google Scholar, retrieve citations,
and export citation data to Excel files with keyword marking in title or abstract.
"""

import asyncio
import json
import re
from datetime import datetime
from typing import List, Optional

import httpx
from bs4 import BeautifulSoup
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from pydantic import BaseModel, ConfigDict, Field, field_validator

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("google_scholar_mcp")

USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}


class PaperInfo(BaseModel):
    title: str
    year: Optional[str] = None
    publisher: Optional[str] = None
    url: Optional[str] = None
    abstract: Optional[str] = None
    contains_keyword: bool = False


class SearchInput(BaseModel):
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
    )

    paper_title: str = Field(
        ...,
        description="Title of the paper to search on Google Scholar",
        min_length=1,
        max_length=500,
    )
    keyword: Optional[str] = Field(
        default=None,
        description="Keyword to mark papers (checks title AND abstract for this keyword)",
        max_length=100,
    )
    max_results: Optional[int] = Field(
        default=50,
        description="Maximum number of citation results to retrieve",
        ge=1,
        le=100,
    )

    @field_validator("paper_title")
    @classmethod
    def validate_paper_title(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Paper title cannot be empty")
        return v.strip()


def _parse_citation_count(text: str) -> int:
    match = re.search(r"[\d,]+", text.replace(",", ""))
    if match:
        return int(match.group().replace(",", ""))
    return 0


def _extract_year(text: str) -> Optional[str]:
    year_match = re.search(r"\b(19|20)\d{2}\b", text)
    if year_match:
        return year_match.group()
    return None


def _check_keyword(title: str, abstract: str, keyword: Optional[str]) -> bool:
    if not keyword:
        return False
    keyword_lower = keyword.lower()
    return keyword_lower in title.lower() or keyword_lower in abstract.lower()


async def _get_citation_count_and_id(client: httpx.AsyncClient, paper_title: str) -> tuple[int, str]:
    search_url = f"https://scholar.google.com/scholar?q={paper_title.replace(' ', '+')}&hl=en&as_sdt=0,5"

    response = await client.get(search_url, headers=HEADERS)
    soup = BeautifulSoup(response.text, "lxml")

    cited_by = 0
    citation_id = None

    for text in soup.find_all(string=re.compile(r"Cited by")):
        cited_by = _parse_citation_count(text)
        href = text.parent.get("href", "")
        id_match = re.search(r"cites=([^&]+)", href)
        if id_match:
            citation_id = id_match.group(1)
        break

    return cited_by, citation_id


def _parse_papers_from_page(soup: BeautifulSoup, keyword: Optional[str]) -> List[PaperInfo]:
    papers: List[PaperInfo] = []
    results = soup.select("div.gs_r")

    for result in results:
        try:
            title_elem = result.select_one("h3.gs_rt a")
            if not title_elem:
                continue

            title = title_elem.get_text(strip=True)
            url = title_elem.get("href")

            abstract_elem = result.select_one("div.gs_rs")
            abstract = abstract_elem.get_text(strip=True) if abstract_elem else ""

            info_elem = result.select_one("div.gs_a")
            meta_text = info_elem.get_text(strip=True) if info_elem else ""

            year = _extract_year(meta_text)

            parts = meta_text.split(" - ")
            publisher = None
            if parts:
                publisher = parts[0].strip() if parts[0] else None

            contains_keyword = _check_keyword(title, abstract, keyword)

            papers.append(PaperInfo(
                title=title,
                year=year,
                publisher=publisher,
                url=url,
                abstract=abstract,
                contains_keyword=contains_keyword,
            ))
        except Exception:
            continue
    return papers


async def _get_citing_papers(
    client: httpx.AsyncClient,
    citation_id: str,
    keyword: Optional[str],
    max_results: int = 50,
) -> List[PaperInfo]:
    all_papers: List[PaperInfo] = []
    start = 0

    while len(all_papers) < max_results:
        cites_url = f"https://scholar.google.com/scholar?cites={citation_id}&as_sdt=2005&sciodt=0,5&hl=en&start={start}"

        response = await client.get(cites_url, headers=HEADERS)
        soup = BeautifulSoup(response.text, "lxml")

        papers = _parse_papers_from_page(soup, keyword)
        if not papers:
            break

        all_papers.extend(papers)

        if len(papers) < 10:
            break

        start += 10
        await asyncio.sleep(1)

    return all_papers[:max_results]


def _save_to_excel(papers: List[PaperInfo], output_path: str, keyword: Optional[str]) -> None:
    wb = Workbook()
    ws = wb.active
    ws.title = "Citations"

    header_fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
    header_font = Font(color="FFFFFF", bold=True)
    header_alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    highlight_fill = PatternFill(start_color="FFFF00", end_color="FFFF00", fill_type="solid")

    headers = ["Title", "Year", "Publisher", "Abstract", "URL", "Contains Keyword"]
    for col, header in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col, value=header)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = header_alignment

    for row, paper in enumerate(papers, 2):
        ws.cell(row=row, column=1, value=paper.title)
        ws.cell(row=row, column=2, value=paper.year or "N/A")
        ws.cell(row=row, column=3, value=paper.publisher or "N/A")
        ws.cell(row=row, column=4, value=paper.abstract if paper.abstract else "N/A")
        ws.cell(row=row, column=5, value=paper.url or "N/A")
        ws.cell(row=row, column=6, value="YES" if paper.contains_keyword else "NO")

        if paper.contains_keyword and keyword:
            for col in range(1, 7):
                ws.cell(row=row, column=col).fill = highlight_fill

        ws.row_dimensions[row].height = 60

    ws.column_dimensions["A"].width = 40
    ws.column_dimensions["B"].width = 10
    ws.column_dimensions["C"].width = 25
    ws.column_dimensions["D"].width = 80
    ws.column_dimensions["E"].width = 40
    ws.column_dimensions["F"].width = 15

    wb.save(output_path)


@mcp.tool(
    name="scholar_search_and_export",
    annotations={
        "title": "Search Google Scholar and Export Citations to Excel",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def scholar_search_and_export(params: SearchInput) -> str:
    """
    Search Google Scholar for a paper and export citations to an Excel file.

    This tool searches Google Scholar using the provided paper title, retrieves
    citing papers, and exports the results to an Excel spreadsheet. Papers containing
    the specified keyword in title OR abstract will be marked.

    Args:
        params (SearchInput): Validated input parameters containing:
            - paper_title (str): Title of the paper to search
            - keyword (Optional[str]): Keyword to mark papers (checks both title AND abstract)
            - max_results (Optional[int]): Maximum number of results (default: 50, max: 100)

    Returns:
        str: JSON-formatted response containing:
            - success (bool): Whether the operation succeeded
            - paper_title (str): The search query
            - cited_by_count (int): Number of papers citing the main paper
            - results_count (int): Number of citation entries found
            - papers_with_abstract (int): Number of papers that have abstract
            - keyword_matched_count (int): Number of papers containing the keyword
            - excel_file (str): Path to the saved Excel file
            - citations (list): Array of citation objects with title, year, publisher, abstract, url, contains_keyword
    """
    try:
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            cited_by, citation_id = await _get_citation_count_and_id(client, params.paper_title)

            if citation_id:
                papers = await _get_citing_papers(
                    client,
                    citation_id,
                    params.keyword,
                    params.max_results,
                )
            else:
                papers = []

        keyword_matched_count = sum(1 for p in papers if p.contains_keyword)
        papers_with_abstract_count = sum(1 for p in papers if p.abstract)

        if not papers and cited_by == 0:
            return json.dumps({
                "success": True,
                "paper_title": params.paper_title,
                "cited_by_count": 0,
                "results_count": 0,
                "papers_with_abstract": 0,
                "keyword_matched_count": 0,
                "excel_file": None,
                "citations": [],
                "message": f"No citation results found for '{params.paper_title}'",
            }, indent=2)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_title = re.sub(r"[^\w\s-]", "", params.paper_title)[:30]
        safe_title = re.sub(r"\s+", "_", safe_title)
        output_path = f"citations_{safe_title}_{timestamp}.xlsx"

        _save_to_excel(papers, output_path, params.keyword)

        result = {
            "success": True,
            "paper_title": params.paper_title,
            "cited_by_count": cited_by,
            "results_count": len(papers),
            "papers_with_abstract": papers_with_abstract_count,
            "keyword_matched_count": keyword_matched_count,
            "keyword": params.keyword,
            "excel_file": output_path,
            "citations": [
                {
                    "title": p.title,
                    "year": p.year,
                    "publisher": p.publisher,
                    "abstract": p.abstract,
                    "url": p.url,
                    "contains_keyword": p.contains_keyword,
                }
                for p in papers
            ],
        }

        return json.dumps(result, indent=2, ensure_ascii=False)

    except httpx.HTTPStatusError as e:
        return json.dumps({
            "success": False,
            "error": f"HTTP error occurred: {e.response.status_code}",
            "message": "Failed to access Google Scholar. Please try again later.",
        }, indent=2)
    except httpx.TimeoutException:
        return json.dumps({
            "success": False,
            "error": "Request timed out",
            "message": "Google Scholar request timed out. Please try again.",
        }, indent=2)
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": str(e),
            "message": "An unexpected error occurred while searching Google Scholar.",
        }, indent=2)


@mcp.tool(
    name="scholar_get_citation_count",
    annotations={
        "title": "Get Citation Count for a Paper",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def scholar_get_citation_count(paper_title: str) -> str:
    """
    Get the citation count for a paper from Google Scholar.

    Args:
        paper_title (str): Title of the paper to search

    Returns:
        str: JSON-formatted response containing citation count
    """
    try:
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            cited_by, _ = await _get_citation_count_and_id(client, paper_title)

        return json.dumps({
            "success": True,
            "paper_title": paper_title,
            "citation_count": cited_by,
            "message": f"'{paper_title}' has been cited by {cited_by} papers on Google Scholar.",
        }, indent=2, ensure_ascii=False)

    except httpx.HTTPStatusError as e:
        return json.dumps({
            "success": False,
            "error": f"HTTP error occurred: {e.response.status_code}",
            "message": "Failed to access Google Scholar. Please try again later.",
        }, indent=2)
    except httpx.TimeoutException:
        return json.dumps({
            "success": False,
            "error": "Request timed out",
            "message": "Google Scholar request timed out. Please try again.",
        }, indent=2)
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": str(e),
            "message": "An unexpected error occurred while searching Google Scholar.",
        }, indent=2)


if __name__ == "__main__":
    mcp.run()