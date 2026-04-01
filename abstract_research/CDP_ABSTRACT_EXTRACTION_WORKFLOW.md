# CDP Abstract Extraction Workflow

Last updated: 2026-04-01
Workspace: `/Users/hyijie/Desktop/爬取文献-前400`
Primary output directory: `/Users/hyijie/Desktop/爬取文献-前400/重做版`

## Purpose

This document records the **validated operating procedure** for extracting literature abstracts and EEG evaluations from the source Excel workbook.

Use this file when:

- another model needs to continue the workflow,
- the same model resumes in a later session,
- a rerun is needed and correctness matters more than speed.

This workflow was created because earlier approaches produced two serious classes of errors:

1. **empty abstracts** caused by pages not fully loading before extraction,
2. **wrong abstracts** caused by capturing visible non-abstract content such as copyright notices, landing-page text, or abstract-shell pages.

The corrected workflow below is the one to follow.

---

## Source of truth

- Source workbook: `/Users/hyijie/Desktop/爬取文献-前400/v2_delete_blank_nonEnglish.xlsx`
- Output schema is fixed to exactly 5 columns:
  1. `Title`
  2. `Year`
  3. `URL`
  4. `完整摘要`
  5. `EEG综合评价`

---

## Non-negotiable rules

### 1. Process strictly **10 rows at a time**

Never run a large continuous range without checkpoints.

Correct examples:

- `rows1_10`
- `rows11_20`
- `rows21_30`

Wrong examples:

- `rows21_400` in one shot
- silent multi-batch continuation without reporting

### 1.1 Allowed parallelism rule

Although output files are still saved **per 10 rows**, execution may run in parallel in controlled chunks.

Validated parallel rule:

- Default to **5 parallel operations** whenever the current workset has 5 or more rows/pages that can be processed independently
- Do **not** wait until 100 papers accumulate before enabling 5-way parallelism
- Even when only **5 papers** are being investigated, extracted, or verified, they should be launched as **5 concurrent operations** if independence allows
- Output files are still saved **per 10 rows**; parallelism only changes runtime scheduling, not deliverable granularity

Examples:

- If processing 5 individual papers, launch 5 concurrent page operations
- If processing 10 papers, split them into 5 concurrent operations first, then continue with the remaining 5 as another concurrent wave if needed
- If reprocessing the first 100 papers, you may still split them into larger ranges for orchestration, but inside each range the actual page work should keep 5 concurrent operations whenever possible

Important:

- This does **not** mean saving a 5-row or 20-row Excel file.
- It only means runtime execution should aggressively maintain 5 concurrent independent operations while the saved deliverables remain:
  - `rows1_10_full_abstracts_eeg_eval.xlsx`
  - `rows11_20_full_abstracts_eeg_eval.xlsx`
  - etc.

Do **not** exceed 5 simultaneous operations, because CDP page stabilization and browser loading quality will degrade if too many article pages are opened at once.

### 1.2 Execution compliance note

If a future run processes a small subset (for example fixing a few rows or rerunning a single 10-row batch), do **not** silently fall back to serial execution just because it is convenient.

Required rule:

- If there are **5 or more independent page operations available**, launch **5 concurrent operations**.
- Only use fewer than 5 when fewer than 5 truly independent items exist, or when a real dependency prevents parallel execution.

Clarification:

- A previous session temporarily reran a single batch with fewer concurrent operations during debugging.
- That should be treated as a **debug exception**, not the standard mode.
- Standard mode remains: **keep extraction/checking at 5-way parallel whenever possible**.

### 2. Use **CDP/browser mode only** for extraction

Do **not** rely on mixed static HTML scraping as the primary extraction mechanism.

Reason:

- static pages often expose no abstract,
- abstract-shell pages often expose wrong text,
- some publishers only render usable article content after the page settles in-browser.

### 3. Save only the **visible Abstract section**

The extractor must save the text from the page’s actual abstract area.

Do **not** save these as abstract:

- copyright text,
- cookie banners,
- access/login prompts,
- metrics panels,
- highlights if they are not the abstract,
- graphical abstract text unless it is clearly the only abstract block,
- generic site descriptions.

### 4. Wait for the page to finish loading before extracting

This is critical.

The model must **not close the tab too quickly**.

Validated improvement:

- earlier short waits caused many `about:blank` and false empty abstracts,
- increasing wait time and requiring repeated stable URL/title checks fixed those cases.

### 5. Maintain per-batch verification artifacts

For every 10-row batch, generate:

- `rowsX_Y_source_manifest.json`
- `rowsX_Y_extraction_results.json`
- `rowsX_Y_alignment_report.json`
- `rowsX_Y_reread_report.json`
- `rowsX_Y_full_abstracts_eeg_eval.xlsx`

All evidence files live in:

`/Users/hyijie/Desktop/爬取文献-前400/重做版/.sisyphus/evidence`

---

## Output location rules

### Always write new work here

`/Users/hyijie/Desktop/爬取文献-前400/重做版`

### Never write to sibling lookalike folders

There are multiple similarly named directories on Desktop. This has caused confusion before.

Do **not** write outputs into:

- `爬取文献`
- `Interest_try_test`
- other similarly named legacy folders

All redo outputs must stay inside `重做版/`.

---

## EEG evaluation rules

### Thesis/dissertation rule

If the source is clearly a dissertation / thesis / 学位论文:

- `完整摘要` = empty string
- `EEG综合评价` = `❌学位论文`

This rule is mandatory and should not be replaced with softer wording.

If a row is judged to be a thesis/dissertation:

- do **not** save any abstract text,
- do **not** keep a partially extracted abstract,
- write the evaluation exactly as: `❌学位论文`

### EEG classification intent

The EEG evaluation must be written in Chinese.

The goal is not to over-claim. Use the page-visible abstract and clearly visible article text only.

Typical categories:

- `Yes：...` when the abstract or visible article text clearly indicates EEG/ERP/P300/CPP/etc.
- `No：...` when the page clearly indicates non-EEG modality or no EEG use.
- `Unclear：...` when the page is accessible but no reliable abstract or modality confirmation is visible.

### EEG综合评价文本模板（必须遵守）

`EEG综合评价` 不能只写简短的 `Yes/No/Unclear` 判定。

从本项目的参考文件风格看，合格输出必须接近：

- **一句结论**：先判断是否属于 EEG/ERP 实证研究、非 EEG 研究、理论/综述/评论文章、或方法学文章；
- **至少一个具体技术信息点**：例如 EEG、ERP、EEG-fMRI、iEEG、MEG、TMS、LFP；
- **至少一个内容信息点**：例如任务范式、ERP 成分、频段、分析方法、研究目的或主要发现；
- **必要时指出文章性质**：实证、综述、理论框架、commentary、方法学、教程等。

信息密度要求：

- 目标长度通常应明显高于简单标签，建议 **1–2 句、约 45–120 个中文字符**；
- 要能让读者仅看这一列就知道：**这篇文章是不是 EEG 相关、用的是什么方法、研究重点是什么**；
- 不允许只写：
  - `Yes：使用EEG/ERP相关证据...`
  - `No：摘要未显示使用EEG数据。`
  - `Unclear：当前页面未可靠暴露可读摘要...`
  这类过短且缺少信息量的句子作为最终版本。

### EEG综合评价符号体系

参考文件使用如下风格，后续输出必须尽量统一：

- `✅`：明确的 EEG/ERP 实证研究，或明确的 EEG/ERP 方法学文献
- `⚠️`：与 EEG/ERP 主题相关，但属于理论、综述、评论、框架、教程，或并未报告新的 EEG 实验数据
- `❌`：无 EEG 相关内容，或明确使用其他主要技术（如 TMS、fMRI、纯行为、访谈等）

优先使用以上符号体系，而不是机械的 `Yes/No/Unclear`。

### EEG综合评价写作模板

#### 模板 A：明确 EEG/ERP 实证研究

写法：

`✅ 这是一项EEG/ERP实证研究，采用[任务/范式]，重点分析[ERP成分/频段/信号]，结果表明[核心发现]。`

可填信息示例：

- 任务/范式：oddball、知觉决策、工作记忆、图片-句子匹配、置信度判断、反应抑制等
- 成分/频段：P3/P300、CPP、ERN、FRN、SPCN、PD、NSW、theta、alpha、beta 等
- 方法：源定位、RIDE、时频分析、解码、Granger 因果、EEG-fMRI 联合记录等

#### 模板 B：非 EEG 研究

写法：

`❌ 该研究主要使用[MEG/TMS/fMRI/行为实验/访谈/计算建模]，探讨[研究主题]，不属于EEG实证研究。`

#### 模板 C：理论 / 综述 / 框架文章

写法：

`⚠️ 这是[理论/综述/框架]文章，讨论[主题]与[EEG/决策/神经表征]的关系，但未报告新的EEG实验数据。`

#### 模板 D：EEG/ERP 方法学 / commentary / 教程

写法：

`✅ 这是EEG/ERP方法学文献，核心讨论[数据处理问题/成分/分析流程]，对[具体ERP领域]具有直接参考价值。`

### 评价内容提取优先级

为了写出更像参考文件的 `EEG综合评价`，从 abstract 中优先提取这些信息：

1. **技术类型**
   - EEG, ERP, EEG-fMRI, intracranial EEG, MEG, TMS, LFP
2. **研究性质**
   - empirical, review, commentary, tutorial, framework, model, perspective
3. **任务 / 范式**
   - oddball, delayed match, discrimination, confidence, working memory, response inhibition 等
4. **成分 / 频段 / 指标**
   - P3, P300, CPP, ERN, FRN, NSW, SPCN, PD, theta, alpha, beta, gamma
5. **分析方法**
   - source localization, time-frequency analysis, decoding, RIDE, DDM, Granger causality 等

如果无法从可见 abstract 中提取这些信息，就不要硬编；此时应保守输出 `⚠️` 或 `❌` 风格说明。

### EEG综合评价质量检查

一个合格的 `EEG综合评价` 至少应满足以下条件：

1. 使用 `✅ / ⚠️ / ❌` 之一作为起始符号（学位论文规则除外）
2. 不只是标签判断，必须包含至少 **1 个技术信息点**
3. 尽量包含至少 **1 个内容信息点**（任务、成分、频段、方法或文章性质）
4. 与 `完整摘要` 内容一致，不得超出可见 abstract 明确支持的范围
5. 不得使用空泛句式替代具体说明

---

## 详细执行计划（面向未来模型）

如果后续需要把现有批次的 `EEG综合评价` 升级为参考文件那种风格，按下面顺序执行：

1. **先读取参考文件样式**
   - 例如：`/Users/hyijie/Desktop/爬取文献-前400/rows371_380_full_abstracts_eeg_eval.xlsx`
   - 提炼其符号体系、句式、技术细节密度
2. **再读取当前输出文件**
   - 比较当前 `EEG综合评价` 是否过短、是否缺少技术/范式信息
3. **不要先重抓 abstract**
   - 优先在现有正确 abstract 基础上重写 `EEG综合评价`
4. **先小范围验证一批**
   - 推荐先在代表性批次（例如 `rows41_50`）验证新写法
5. **验证通过后，再批量覆盖重写**
   - 覆盖目标批次的同名 xlsx 文件
6. **重写后再次 reread 验证**
   - 确认行数、列数、标题顺序不变，只更新 `EEG综合评价` 内容

这个计划的目的不是改变 abstract 抽取逻辑，而是**提升 EEG综合评价 的表达质量和信息密度**。

---

## Validated CDP operating procedure

### Step 0. Confirm CDP is available

Run the web-access dependency check.

Expected outcome:

- Chrome remote debugging is available,
- CDP proxy is reachable,
- extraction can create background tabs.

### Step 1. Open the target URL in a new background tab

Use CDP `/new` with the article URL.

Do **not** immediately evaluate the page.

### Step 2. Wait for page stability

Use repeated polling of page info (`url`, `title`) before extraction.

Validated rule:

- wait up to about **24 seconds**,
- require multiple consecutive stable checks,
- if page is still `about:blank`, keep waiting instead of failing immediately.

This waiting step materially improved accuracy.

### Step 3. Extract only abstract-focused content

In the page evaluation step, prioritize:

1. explicit abstract metadata (`citation_abstract`, `abstract`, similar tags)
2. DOM blocks whose id/class contains `abstract`
3. sibling content following a heading exactly matching `Abstract` or `Summary`

Avoid broad “first 20 paragraphs” logic unless it is only being used as a debug aid and **not** as a final abstract source.

### Step 4. Validate article identity before accepting the abstract

Compare source title against page identity hints such as:

- `document.title`
- visible `h1`
- `citation_title`

Use a tolerant but bounded comparison:

- similarity score,
- token overlap,
- accept only when page identity clearly corresponds to the source article.

Important: do **not** accept text just because a page opened successfully.

### Step 5. Reject noisy pseudo-abstracts

Reject extracted text if it matches patterns like:

- `copyright`
- `all content on this site`
- `all rights reserved`
- `cookies`
- `access options`
- `metrics details`
- `sign in`
- `log in`

If a candidate matches these, it is **not** a valid abstract.

### Step 6. Close the tab only after extraction completes

This is important.

The tab must remain open until:

- page stability has been achieved,
- abstract extraction has run,
- identity validation has completed.

Do not close early.

---

## Batch execution procedure

For each batch `rowsX_Y`:

Note: a runtime orchestration block may span many rows, but the actual extraction/checking work should maintain up to 5 concurrent independent operations, and output artifacts are still generated per 10-row batch.

### A. Build source manifest

Read rows `X..Y` from the source workbook and write:

- source row number
- Title
- Year
- URL

to `rowsX_Y_source_manifest.json`

### B. Extract each row

For each row:

1. Open URL with CDP
2. Wait for stable page load
3. Extract visible abstract block only
4. Validate page identity against source title
5. Save:
   - `完整摘要`
   - `EEG综合评价`
   - `final_url`
   - `evidence_note`

### C. Write extraction results

Save row-level output to:

- `rowsX_Y_extraction_results.json`

### D. Write alignment report

Confirm:

- expected rows match actual rows,
- titles match,
- years match,
- URLs match,
- row order is preserved.

Save to:

- `rowsX_Y_alignment_report.json`

### E. Write Excel output

Write exactly one Excel file:

- `rowsX_Y_full_abstracts_eeg_eval.xlsx`

### F. Re-read Excel and verify

Check:

- file exists,
- 10 rows,
- 5 columns,
- header order is correct,
- first and last titles match manifest,
- alignment report passed.

Save to:

- `rowsX_Y_reread_report.json`

### G. EEG文本质量检查

在完成 Excel 写出后，额外检查 `EEG综合评价` 是否满足新的风格要求：

- 是否使用了 `✅ / ⚠️ / ❌`
- 是否包含技术信息点
- 是否包含内容信息点
- 是否明显比单纯的 Yes/No 句式更有信息量
- 是否与 `完整摘要` 一致

---

## What counts as success for one batch

A batch is only complete when all of the following are true:

1. Excel exists,
2. row count is correct,
3. header order is correct,
4. alignment report passes,
5. reread report passes,
6. no row contains obvious non-abstract junk text,
7. any empty abstract is explainable by evidence, not by rushed closing or wrong-page capture,
8. `EEG综合评价` does not collapse to low-information Yes/No labels,
9. `EEG综合评价` follows the richer template style defined above.

---

## Known failure modes and how to respond

### Failure mode 1: `final_url = about:blank`

Meaning:

- page did not finish loading,
- tab was read too early,
- or CDP navigation failed.

Action:

- wait longer,
- re-check stability,
- do not accept result as final.

### Failure mode 2: abstract equals copyright / site boilerplate

Meaning:

- wrong content block was captured.

Action:

- reject candidate,
- continue searching for explicit abstract block,
- do not write this text into Excel.

### Failure mode 3: page opens but title mismatch is large

Meaning:

- may be wrong page,
- or publisher uses a transformed title.

Action:

- compare `h1`, `citation_title`, and page title,
- use token overlap as secondary validation,
- only accept if identity is still clearly the same article.

### Failure mode 4: abstract-shell pages (`abstract`, `short`, `doi/abs`)

Meaning:

- page may not expose the full abstract cleanly.

Action:

- rely on visible abstract block if present,
- if not visible, keep abstract empty and explain in `evidence_note`,
- do not invent or guess.

### Failure mode 5: APA PsycNet pages show abstract but output remains empty

Meaning:

- the page may load successfully,
- the page body may visibly contain the article title and an `Abstract` section,
- but normal title validation or noise filtering may still reject the row.

Action:

- use CDP to confirm whether the body visibly contains both the source title and an `Abstract` section;
- if the page title or `h1` is too generic (for example `APA PsycNET` or `APA PsycNet FullTextHTML page`), allow an **APA-specific identity fallback** when the body clearly matches the article;
- sanitize the abstract candidate before rejection, because APA often appends boilerplate such as:
  - `(PsycInfo Database Record (c) ... )`
  - `Copyright Statement: ...`

Do not reject the whole abstract candidate just because those suffixes are present. Strip them first, then score the cleaned abstract.

### Failure mode 6: Site returns an error page instead of the article

Meaning:

- CDP navigation technically succeeds,
- but the loaded page is not the article page,
- instead the site serves an error or protection page.

Verified examples from this project:

- ScienceDirect / Elsevier may return:
  - `There was a problem providing the content you requested`
- PLOS may return:
  - `503 Backend fetch failed`

Action:

- do **not** classify this as an ordinary title-mismatch problem;
- do **not** keep retrying selectors on the same loaded page;
- record the row as a site-level failure / backend-unavailable case;
- keep the abstract empty only when the page is clearly an error page rather than a partially loaded article page.

Important:

- A blocked/error page is different from a normal article page with a weak abstract selector.
- These cases should be documented as site accessibility failures, not as generic extraction misses.

### Recovery mode: search the title in Google, then enter a working result URL

If the publisher URL returns an error page or unstable backend response, do not stop at the failed direct URL.

Validated recovery workflow:

1. Search the **full article title** in Google.
2. Inspect the top result URLs.
3. Prefer entering these result types in this order when available:
   - `pmc.ncbi.nlm.nih.gov`
   - `pubmed.ncbi.nlm.nih.gov`
   - Google Scholar redirect/result URLs
   - the publisher page only if it now looks stable
4. Once a working page opens, extract the abstract from that page and record the recovery source in `evidence_note`.

Parallelism rule for Google recovery:

- The Google-recovery stage must also follow the **5 concurrent operations** rule.
- Do **not** switch back to single-page recovery just because the workflow is in fallback mode.
- If there are 5 unresolved rows available, open/search/enter **5 Google-discovered candidate pages in parallel**.
- After those 5 finish, continue with the next wave of up to 5 unresolved rows.

Why this works:

- Google often exposes alternative stable entry points when the original publisher URL returns an error page;
- PMC / PubMed pages frequently expose a reliable abstract even when the publisher page is blocked or unstable;
- Google Scholar redirect URLs can sometimes reach a readable publisher entry even when direct navigation fails.

Important constraints:

- Do not treat the Google snippet itself as the final abstract.
- Use Google only as a discovery step; the actual saved abstract must come from the page you enter next.
- Record the recovery source URL in `evidence_note` so the path is traceable.
- Even in Google recovery mode, the execution layer should preserve the same concurrency discipline as the main workflow: **5-way parallel whenever possible**.

---

## Important lessons learned from this run

### Lesson 1

`alignment_ok = true` does **not** mean the abstract is correct.

It only means the row order and source identifiers were preserved.

### Lesson 2

Most “empty abstracts” were not because the article truly lacked an abstract.

Many were caused by:

- premature tab closing,
- CDP not waiting long enough,
- abstract-shell pages,
- weak candidate filtering.

### Lesson 3

Longer CDP stabilization materially improves correctness.

When wait time was increased and stability checks were tightened, a previously problematic batch (`rows41_50`) improved from multiple empty/wrong rows to full recovery.

### Lesson 4

Wrong-article extraction can happen even when the file structure looks “verified”.

Identity validation is mandatory.

### Lesson 5

APA PsycNet requires site-specific handling.

In a verified case, the page visibly contained the correct abstract, but the workflow still saved an empty abstract because:

- the page title / `h1` was too generic for normal identity validation, and/or
- the abstract candidate ended with PsycInfo boilerplate that triggered bad-text rejection.

The fix was:

1. allow an APA-specific identity fallback when the body clearly contains the source title plus an `Abstract` section;
2. sanitize the abstract candidate by removing PsycInfo record suffixes and copyright tails before scoring.

### Lesson 6

Not every empty abstract is caused by extraction logic.

In later batches, several remaining empty rows were traced to site-level error pages rather than selector failures. For example:

- ScienceDirect loaded an Elsevier error page instead of the article;
- PLOS returned a `503 Backend fetch failed` page.

This means the correct response is not always “improve the selector.” Sometimes the correct response is to recognize that the site never served the article page at all.

### Lesson 7

Google title search can recover abstracts when direct publisher URLs fail.

In the 101–200 range, multiple previously empty rows were recovered by searching the exact title in Google and then entering alternative result URLs such as:

- PMC
- PubMed
- Google Scholar redirect links

This worked especially well for rows that originally failed due to:

- ScienceDirect / Elsevier error pages
- PLOS backend 503 pages

The key rule is: use Google as the discovery layer, but extract the actual abstract only after entering a stable result page.

### Lesson 8

Google-title recovery is not just a theoretical fallback; it has already been validated in bulk.

In the 201–300 range, 21 rows were initially empty after direct processing. Using the title-in-Google workflow:

- 20 rows were successfully recovered via alternative entry pages,
- only 1 row remained unresolved after that pass.

This means the Google-title recovery path should be treated as a practical second-stage recovery method for publisher-failure cases, not as an optional last resort.

---

## 为什么这一版流程更可靠

这一版流程之所以明显优于早期版本，不是因为“运气好”或某一篇文章碰巧更容易抓，而是因为整个流程从“尽量抓到内容”改成了“只接受经过验证的内容”。下面这些改动是本轮成功的主要原因，后续模型必须保留。

### 1. CDP 成为唯一主路径，而不是静态抓取与动态抓取混用

早期版本会混合使用静态 HTML、meta description、页面段落文本等候选来源，再从中挑一个“像摘要”的文本。这样虽然看起来更容易得到非空结果，但实际上会引入两类错误：

- 页面没有完全加载时，抽不到真正的摘要，导致空摘要；
- 页面有版权、导航、cookie、metrics 等文本时，容易把这些噪音误收成摘要。

当前版本改成 **CDP-only** 主流程，优先读取浏览器中已经实际加载并渲染完成的文章页面，再从其中抽取摘要。这个改动显著减少了“抓到的是页面壳而不是论文内容”的情况。

### 2. 页面稳定优先于提取速度

本轮最关键的改善之一，是不再在页面刚打开时立即读取或关闭标签页，而是先等待页面稳定。具体做法是：

- 打开新 tab 后轮询 `url` 和 `title`；
- 要求连续多次检查结果稳定；
- 如果页面仍然停留在 `about:blank`，就继续等待，而不是立即判失败。

这个改动直接解决了大量“空摘要但文章其实有摘要”的问题。早期很多空摘要不是文章本身缺摘要，而是因为页面还没完全加载完成就被读取甚至关闭。实际测试中，加长等待后，之前问题明显的批次恢复到了接近完整可抽取状态。

### 3. 增加文章身份校验，而不是只看 URL 是否打开

旧流程中的 `alignment_ok` 只能证明：

- 行顺序没有错；
- Title / Year / URL 没串位。

但这并不能证明当前页面真的是目标文章，也不能证明被抽取的文本一定是该文章的摘要。因此当前流程增加了身份校验：

- 比较源表标题与页面 `title`、`h1`、`citation_title`；
- 使用相似度和词重叠做双重判断；
- 页面身份不可靠时，不接受抽取结果。

这一步的作用是防止“打开了一个看起来差不多的页面，就把它当成目标文章”的错误。

### 4. 明确拒收噪音文本

早期最典型的错误之一，是将版权声明、站点说明、登录或导航文本当成摘要。当前版本明确把这些文本作为拒收对象，例如：

- copyright
- all rights reserved
- cookies
- access options
- metrics details
- sign in / log in

一旦候选文本命中这些模式，就必须丢弃，不能为了得到“非空摘要”而勉强保留。这个规则的意义在于：**宁可保守为空，也不要把错误文本写进最终 Excel。**

### 5. 只接受真正的 abstract 区块，而不是宽泛的正文候选

为了提高正确性，当前流程优先使用：

1. `citation_abstract` 或类似元数据；
2. 明确带有 `abstract` 标识的 DOM 区块；
3. `Abstract` / `Summary` 标题之后的兄弟节点内容。

而不是把整页前几段正文、壳页说明、Highlights 或别的边缘内容都纳入“摘要候选”。

这个收缩策略会让一部分边界情况变成空摘要，但它换来的是更高的可信度。当前工作流的核心原则是：**正确性优先于填充率。**

### 6. 抽取正确性与评价质量分开处理

本轮成功的另一个原因，是把两个不同问题拆开处理：

- 先保证 `完整摘要` 抽取得正确、稳定；
- 再单独提升 `EEG综合评价` 的写法和信息密度。

如果摘要本身是错的，而评价写得再漂亮，也只是在放大错误。因此后续模型必须遵守：**先修抽取，再修表述；不要在错误摘要上生成高置信度评价。**

### 7. 先用代表性批次验证，再扩大范围

这次流程改进没有一上来就全量重跑，而是先在代表性批次（例如 `rows41_50`）上验证。原因是这种批次里通常同时包含：

- EEG 实证研究；
- 非 EEG 研究；
- 理论 / 综述文章；
- 之前出现过空摘要或错摘要的高风险页面。

先在这样的批次里验证，可以更快看出：

- 页面等待是否足够；
- 身份校验是否过严或过宽；
- 噪音文本过滤是否有效；
- 评价生成是否会乱写技术细节。

只有代表性批次验证通过，才适合扩大到更多批次。

### 8. 这一版流程的核心思想

后续模型必须记住：这版流程成功的关键，不是“抓得更快”，而是“拒收更严格”。

具体来说：

- 页面没稳定，不接受；
- 页面身份不清楚，不接受；
- 文本像版权或导航，不接受；
- 不是 abstract 专属区块，不轻易接受；
- 评价信息不够，不算完成。

这意味着本流程的核心不是“尽量把表填满”，而是：

> 只把经过验证、可解释、可回溯的内容写进最终文件。

### 9. 改进必须同步到执行约束与站点经验

Two operational lessons must be preserved for future models:

1. **Parallelism discipline matters**
   - do not drift back to serial execution just because the current slice is small;
   - if 5 independent rows/pages are available, process them with 5 concurrent operations.

2. **APA handling is site-specific, not generic**
   - generic validation/filtering is insufficient for some PsycNet pages;
   - keep the APA fallback and abstract-sanitization behavior, or the workflow will regress to false empty abstracts.

3. **Error-page detection matters as much as selector quality**
   - ScienceDirect and PLOS may sometimes return error pages that superficially look like successful navigations;
   - these rows must be recognized and recorded as site-level failures rather than treated as ordinary selector misses.

4. **Google-title recovery is a valid fallback path**
   - when direct URLs fail, searching the title in Google and entering PMC / PubMed / Scholar result pages can recover real abstracts;
   - this fallback should be attempted before declaring a row unrecoverable.

5. **Google fallback does not relax the concurrency rule**
   - the fallback stage is still part of the operational workflow;
   - if multiple unresolved rows remain, Google search + page entry should also be executed in 5 parallel operations when feasible.

---

## What not to do

Do **not**:

- process hundreds of rows in one silent run,
- close CDP tabs immediately after opening,
- accept `about:blank` as a real article page,
- treat copyright text as abstract,
- rely only on static HTML for publishers known to be unstable,
- assume `alignment_ok` means content correctness,
- continue to the next batch before reporting current batch status.

---

## Current preferred operating rhythm

1. Default save unit: **one 10-row batch**
2. Default runtime behavior: maintain up to **5 concurrent independent operations** whenever possible
3. Do not defer parallelism until large ranges; even a 5-row workset should use 5 concurrent operations if feasible
4. Verify each resulting 10-row batch completely
5. Report status before expanding further

This keeps the workflow observable and makes mistakes easy to catch early.

---

## Suggested handoff sentence for future sessions

If resuming later, provide this instruction to the next model:

> Read `/Users/hyijie/Desktop/爬取文献-前400/.sisyphus/CDP_ABSTRACT_EXTRACTION_WORKFLOW.md` first, then continue the batch extraction strictly 10 rows at a time using CDP-only abstract extraction with long page stabilization and per-batch alignment/reread verification.

If parallel reprocessing is needed, use at most 5 concurrent operations at any time. Keep the extraction/checking layer 5-way parallel whenever independence allows, while still saving outputs per 10 rows.
