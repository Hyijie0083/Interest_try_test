# Google Scholar Detail MCP

A Model Context Protocol (MCP) server for searching Google Scholar and extracting detailed paper information including abstract and keywords.

## Features

- Search Google Scholar for papers
- Get citation counts
- Export citations to Excel with detailed information
- **Extract abstract and keywords from each paper's page**

## Installation

```bash
pip install -r requirements.txt
playwright install chromium
```

## Usage

### As MCP Server

```python
from mcp.server.fastmcp import FastMCP

# Run the server
python server.py
```

### Using Playwright Script

```bash
python playwright_detail_search.py
```

This will:
1. Search for the target paper on Google Scholar
2. Get all citing papers
3. Open each paper's page to extract abstract and keywords
4. Save results to Excel with columns: Title, Year, Publisher, Abstract, Keywords, URL

## Output Format

Excel file with columns:
- **Title**: Paper title
- **Year**: Publication year
- **Publisher**: Publisher/Author info
- **Abstract**: Paper abstract (extracted from paper page)
- **Keywords**: Paper keywords (extracted from paper page)
- **URL**: Link to the paper

## Anti-Crawler Strategy

- Random delays between requests
- Human-like behavior simulation
- Captcha detection and manual solving support
- Rate limiting protection
