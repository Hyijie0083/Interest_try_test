# Google Scholar MCP

An MCP server for searching Google Scholar citations and exporting to Excel files.

## Features

- 🔍 Search Google Scholar citations by paper title
- 📊 Export citation information (title, year, publisher, abstract, URL)
- 🏷️ Keyword marking support (search papers containing specified keywords in title and abstract)
- 📝 Keyword matching supports OR logic (e.g., `CPP OR central OR parietal`)
- 📑 Excel highlighting for keyword-matched papers

## Installation

```bash
pip install -r requirements.txt
```

## Usage

### Start MCP Server

```bash
python server.py
```

### MCP Configuration

Add to your MCP configuration file:

```json
{
  "mcpServers": {
    "google_scholar_mcp": {
      "command": "python3",
      "args": ["/full/path/to/google_scholar_mcp/server.py"]
    }
  }
}
```

## Important Notes

### 1. Index Order

**The citation index order is exactly the same as displayed on Google Scholar.**

Google Scholar defaults to relevance sorting, and our retrieval follows Google Scholar's pagination order (10 papers per page).

### 2. Retrieval Quantity Limit

Google Scholar has access limits for non-logged-in users.

**Actual test results:**
- Single continuous retrieval: approximately 53-67 pages (530-670 papers)
- After triggering rate limit, wait 15-60 minutes or change IP

### 3. IP Limitation and Solutions

Google Scholar applies rate limiting based on IP address. When rate limited:

**Solutions:**
- 🪜 Change proxy IP (VPN) to continue retrieval
- ⏰ Wait 15-60 minutes for automatic limit reset
- 🔄 Retrieve in batches (get part of the pages each time)

### 4. Excluding Papers Without Abstracts

**Papers on Google Scholar that only have citation counts but no abstract information (such as some theses, books, etc.) are excluded.**

Our retrieval only includes papers with complete titles and abstracts displayed on Google Scholar. Some citations with only Citation Count will not be included.

### 5. Abstract Content Notice

**Cannot fetch complete abstracts, only truncated abstracts displayed on Google Scholar (~150-200 characters).**

Reasons:
- Paper detail pages (such as Nature.com, ScienceDirect, etc.) have strict anti-scraping protection
- Requires additional Academic API configuration (such as Semantic Scholar API, OpenAlex API) to get complete abstracts

## Tools

### scholar_search_and_export

**Function:** Search paper citations and export to Excel

**Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| paper_title | string | Paper title (required) |
| keyword | string | Keyword for marking (optional) |
| max_results | int | Max results, default 50, max 100 |

**Returns:**
- Citation count
- Excel file path
- Citation list (title, year, publisher, abstract, URL, contains keyword)

### scholar_get_citation_count

**Function:** Quickly get citation count for a paper

**Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| paper_title | string | Paper title (required) |

## Examples

### Example 1: Search and mark keywords

```
Search citations for "Attention is all you need" and mark papers containing "transformer"
```

### Example 2: Using OR logic

```
Search citations and mark papers containing CPP, central, or parietal
Keyword: CPP OR central OR parietal
```

### Example 3: Get citation count

```
How many citations does "GPT-3" have?
```

## Project Structure

```
google_scholar_mcp/
├── server.py         # MCP server main file
├── requirements.txt # Python dependencies
└── README.md        # Documentation
```

## Dependencies

- mcp[fastapi]==1.1.0
- httpx==0.27.0
- beautifulsoup4==4.12.3
- lxml==5.2.2
- openpyxl==3.1.2
- pydantic==2.7.1

## Notes

1. **Reasonable Usage**: Avoid too frequent requests, recommended interval 2-3 seconds
2. **Rate Limiting**: When rate limited, change IP or wait
3. **Data Completeness**: For complete data, retrieve in batches
4. **Abstract Limitation**: For complete abstracts, consider using Semantic Scholar API

## License

MIT