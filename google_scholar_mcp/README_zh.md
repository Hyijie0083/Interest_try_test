# Google Scholar MCP

一个用于检索 Google Scholar 引用文献并导出为 Excel 文件的 MCP 服务器。

## 功能特点

- 🔍 根据论文标题搜索 Google Scholar 引用
- 📊 导出引用文献信息（标题、年份、出版社、摘要、URL）
- 🏷️ 支持关键词标记（搜索标题和摘要中包含指定关键词的文章）
- 📝 关键词匹配支持 OR 逻辑（如：`CPP OR central OR parietal`）
- 📑 Excel 高亮显示匹配关键词的文章

## 安装

```bash
pip install -r requirements.txt
```

## 使用方法

### 启动 MCP 服务器

```bash
python server.py
```

### MCP 配置

在 MCP 配置文件中添加：

```json
{
  "mcpServers": {
    "google_scholar_mcp": {
      "command": "python3",
      "args": ["/完整路径/google_scholar_mcp/server.py"]
    }
  }
}
```

## 重要说明

### 1. 索引顺序

**引用文献的索引顺序与 Google Scholar 页面显示顺序完全一致。**

Google Scholar 默认按相关性排序，我们的检索按照 Google Scholar 的分页顺序（每页 10 篇）依次获取。

### 2. 检索数量限制

Google Scholar 对未登录用户有访问限制。

**实际测试结果：**
- 单次连续检索：约 53-67 页（530-670 篇文献）
- 触发限流后，需等待 15-60 分钟或更换 IP

### 3. IP 限制与解决方案

Google Scholar 会根据 IP 地址进行限流。当触发限流后：

**解决方案：**
- 🪜 更换代理 IP（梯子）继续检索
- ⏰ 等待 15-60 分钟让限流自动解除
- 🔄 分批次检索（每次获取部分页面）

### 4. 排除无摘要文献

**Google Scholar 上只有引用数但没有摘要信息的文献（如部分学位论文、书籍等）会被排除。**

我们的检索只包含 Google Scholar 显示完整标题和摘要的文献。部分只有 Citation Count 的引用不会被包含。

### 5. 摘要内容说明

**无法获取完整摘要，只能获取 Google Scholar 上显示的截断摘要（约 150-200 字）。**

原因：
- 论文详情页（如 Nature.com、ScienceDirect 等）有严格的反爬虫保护
- 需要额外配置 Academic API（如 Semantic Scholar API、OpenAlex API）获取完整摘要

## 工具

### scholar_search_and_export

**功能：** 搜索论文引用并导出为 Excel

**参数：**
| 参数 | 类型 | 说明 |
|------|------|------|
| paper_title | string | 论文标题（必填） |
| keyword | string | 关键词（可选，用于标记） |
| max_results | int | 最大结果数，默认 50，最多 100 |

**返回：**
- 被引用次数
- Excel 文件路径
- 引用文献列表（标题、年份、出版社、摘要、URL、是否包含关键词）

### scholar_get_citation_count

**功能：** 快速获取论文的引用次数

**参数：**
| 参数 | 类型 | 说明 |
|------|------|------|
| paper_title | string | 论文标题（必填） |

## 示例

### 示例 1：搜索引用并标记关键词

```
搜索 "Attention is all you need" 的引用，标记包含 "transformer" 的文章
```

### 示例 2：使用 OR 逻辑

```
搜索引用并标记包含 CPP、central 或 parietal 的文章
关键词：CPP OR central OR parietal
```

### 示例 3：获取引用数量

```
查询 "GPT-3" 被引用了多少次
```

## 项目结构

```
google_scholar_mcp/
├── server.py         # MCP 服务器主文件
├── requirements.txt # Python 依赖
└── README.md         # 说明文档
```

## 依赖

- mcp[fastapi]==1.1.0
- httpx==0.27.0
- beautifulsoup4==4.12.3
- lxml==5.2.2
- openpyxl==3.1.2
- pydantic==2.7.1

## 注意事项

1. **合理使用**：避免过于频繁的请求，建议间隔 2-3 秒
2. **限流处理**：触发限流后请更换 IP 或等待
3. **数据完整性**：如需完整数据，建议分批次获取
4. **摘要限制**：如需完整摘要，建议配合 Semantic Scholar API 使用

## License

MIT