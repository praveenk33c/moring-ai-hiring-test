# Project Explanation and Fixes Simplified

- **Cascade ID**: `4e04ccf7-2299-4904-9314-8663c0a365a9`
- **Steps**: 38
- **Status**: CASCADE_RUN_STATUS_IDLE
- **Created**: 2026-11-10T06:41:07.018259Z
- **Last Modified**: 2026-11-10T06:43:14.664735Z
- **Workspace**: file:///Users/praveenk/E-Drive/moring%20ai%20take%20home%20assessment/moring-ai-hiring-test
- **Exported**: 2026-11-11 03:02:25

---

## 🧑 User  `2026-11-10T06:41:07`
Hey agy, explain this project, issues and what needs to be fixed in simpler words to easily understand.

### 🔧 Tool: `run_command`  `2026-11-10T06:41:11`
```bash
ls -la
```
* (in `/Users/praveenk/E-Drive/moring ai take home assessment/moring-ai-hiring-test`) → exit 0*

<details><summary>📤 Output</summary>

```
Command exited with code 0.

Command output:
total 64
drwxr-xr-x@ 15 praveenk  staff    480 Nov 10 12:09 .
drwxr-xr-x@  3 praveenk  staff     96 Nov  6 23:08 ..
-rw-r--r--@  1 praveenk  staff    964 Nov  6 23:40 .env
-rw-r--r--@  1 praveenk  staff    979 Nov  6 23:08 .env.example
drwxr-xr-x@ 14 praveenk  staff    448 Nov 10 10:24 .git
drwxr-xr-x@  3 praveenk  staff     96 Nov  6 23:08 .github
-rw-r--r--@  1 praveenk  staff    132 Nov  6 23:08 .gitignore
drwxr-xr-x@  7 praveenk  staff    224 Nov  6 23:10 .venv
-rw-r--r--@  1 praveenk  staff    778 Nov  6 23:08 Makefile
-rw-r--r--@  1 praveenk  staff  14999 Nov  6 23:08 README.md
drwxr-xr-x@ 10 praveenk  staff    320 Nov  7 10:52 backend
drwxr-xr-x@  5 praveenk  staff    160 Nov  6 23:08 data
drwxr-xr-x@  8 praveenk  staff    256 Nov  6 23:08 docs
drwxr-xr-x@  9 praveenk  staff    288 Nov  6 23:26 frontend
drwxr-xr-x@ 10 praveenk  staff    320 Nov 10 10:24 submission

```

</details>

### 🔧 Tool: `view_file`  `2026-11-10T06:41:15`
`file:///Users/praveenk/E-Drive/moring ai take home assessment/moring-ai-hiring-test/README.md` (174 lines, 14999 bytes)

### 🔧 Tool: `run_command`  `2026-11-10T06:41:20`
```bash
ls -la docs submission backend/app
```
* (in `/Users/praveenk/E-Drive/moring ai take home assessment/moring-ai-hiring-test`) → exit 1*

<details><summary>📤 Output</summary>

```
Command exited with code 1.

Command output:
ls: backend/app: No such file or directory
docs:
total 64
drwxr-xr-x@  8 praveenk  staff   256 Nov  6 23:08 .
drwxr-xr-x@ 15 praveenk  staff   480 Nov 10 12:09 ..
-rw-r--r--@  1 praveenk  staff  6339 Nov  6 23:08 AP_POLICY.md
-rw-r--r--@  1 praveenk  staff  1171 Nov  6 23:08 ARCHITECTURE.md
-rw-r--r--@  1 praveenk  staff  1224 Nov  6 23:08 HANDOVER.md
-rw-r--r--@  1 praveenk  staff  4151 Nov  6 23:08 OUTPUT_CONTRACT.md
-rw-r--r--@  1 praveenk  staff  1852 Nov  6 23:08 PRODUCT_BRIEF.md
-rw-r--r--@  1 praveenk  staff  3677 Nov  6 23:08 STAKEHOLDER_THREAD.md

submission:
total 56
drwxr-xr-x@ 10 praveenk  staff   320 Nov 10 10:24 .
drwxr-xr-x@ 15 praveenk  staff   480 Nov 10 12:09 ..
-rw-r--r--@  1 praveenk  staff   717 Nov  6 23:08 AI_USAGE.md
-rw-r--r--@  1 praveenk  staff   651 Nov  6 23:08 DECISIONS.md
-rw-r--r--@  1 praveenk  staff  1139 Nov  6 23:08 EVAL_REPORT.md
-rw-r--r--@  1 praveenk  staff  1034 Nov  6 23:08 FINDINGS.md
-rw-r--r--@  1 praveenk  staff   481 Nov 10 10:24 FIRST_HOUR.md
-rw-r--r--@  1 praveenk  staff   309 Nov  6 23:08 REFLECTION.md
-rw-r--r--@  1 praveenk  staff   855 Nov  6 23:08 RULINGS.md
drwxr-xr-x@  3 praveenk  staff    96 Nov 10 10:24 ai-logs

```

</details>

### 🔧 Tool: `run_command`  `2026-11-10T06:41:23`
```bash
ls -la backend
```
* (in `/Users/praveenk/E-Drive/moring ai take home assessment/moring-ai-hiring-test`) → exit 0*

<details><summary>📤 Output</summary>

```
Command exited with code 0.

Command output:
total 56
drwxr-xr-x@ 10 praveenk  staff    320 Nov  7 10:52 .
drwxr-xr-x@ 15 praveenk  staff    480 Nov 10 12:09 ..
drwxr-xr-x@  6 praveenk  staff    192 Nov  7 10:52 .pytest_cache
drwxr-xr-x@  7 praveenk  staff    224 Nov  6 23:24 .venv
drwxr-xr-x@  3 praveenk  staff     96 Nov  6 23:08 eval
drwxr-xr-x@ 15 praveenk  staff    480 Nov  6 23:26 ledgerline
-rw-r--r--@  1 praveenk  staff  24576 Nov  6 23:26 ledgerline.db
drwxr-xr-x@  7 praveenk  staff    224 Nov  7 10:52 ledgerline.egg-info
-rw-r--r--@  1 praveenk  staff    655 Nov  6 23:08 pyproject.toml
drwxr-xr-x@  9 praveenk  staff    288 Nov  7 10:52 tests

```

</details>

### 🔧 Tool: `view_file`  `2026-11-10T06:41:28`
`file:///Users/praveenk/E-Drive/moring ai take home assessment/moring-ai-hiring-test/docs/HANDOVER.md` (24 lines, 1224 bytes)

### 🔧 Tool: `view_file`  `2026-11-10T06:41:35`
`file:///Users/praveenk/E-Drive/moring ai take home assessment/moring-ai-hiring-test/docs/STAKEHOLDER_THREAD.md` (66 lines, 3677 bytes)

### 🔧 Tool: `view_file`  `2026-11-10T06:41:39`
`file:///Users/praveenk/E-Drive/moring ai take home assessment/moring-ai-hiring-test/submission/FIRST_HOUR.md` (13 lines, 481 bytes)

### 🔧 Tool: `run_command`  `2026-11-10T06:41:42`
```bash
git status
```
* (in `/Users/praveenk/E-Drive/moring ai take home assessment/moring-ai-hiring-test`) → exit 0*

<details><summary>📤 Output</summary>

```
Command exited with code 0.

Command output:
On branch main
Your branch is up to date with 'origin/main'.

nothing to commit, working tree clean

```

</details>

### 🔧 Tool: `run_command`  `2026-11-10T06:41:47`
```bash
ls -la backend/ledgerline
```
* (in `/Users/praveenk/E-Drive/moring ai take home assessment/moring-ai-hiring-test`) → exit 0*

<details><summary>📤 Output</summary>

```
Command exited with code 0.

Command output:
total 88
drwxr-xr-x@ 15 praveenk  staff   480 Nov  6 23:26 .
drwxr-xr-x@ 10 praveenk  staff   320 Nov  7 10:52 ..
-rw-r--r--@  1 praveenk  staff   114 Nov  6 23:08 __init__.py
drwxr-xr-x@ 12 praveenk  staff   384 Nov  6 23:26 __pycache__
-rw-r--r--@  1 praveenk  staff  3848 Nov  6 23:08 api.py
-rw-r--r--@  1 praveenk  staff  3031 Nov  6 23:08 cli.py
-rw-r--r--@  1 praveenk  staff  1170 Nov  6 23:08 config.py
-rw-r--r--@  1 praveenk  staff  2907 Nov  6 23:08 db.py
-rw-r--r--@  1 praveenk  staff  2741 Nov  6 23:08 extraction.py
drwxr-xr-x@  9 praveenk  staff   288 Nov  6 23:26 llm
-rw-r--r--@  1 praveenk  staff   753 Nov  6 23:08 models.py
-rw-r--r--@  1 praveenk  staff   683 Nov  6 23:08 parsing.py
-rw-r--r--@  1 praveenk  staff  3916 Nov  6 23:08 pipeline.py
-rw-r--r--@  1 praveenk  staff  1141 Nov  6 23:08 reference.py
-rw-r--r--@  1 praveenk  staff  3169 Nov  6 23:08 validation.py

```

</details>

### 🔧 Tool: `run_command`  `2026-11-10T06:41:50`
```bash
ls -la backend/eval
```
* (in `/Users/praveenk/E-Drive/moring ai take home assessment/moring-ai-hiring-test`) → exit 0*

<details><summary>📤 Output</summary>

```
Command exited with code 0.

Command output:
total 8
drwxr-xr-x@  3 praveenk  staff    96 Nov  6 23:08 .
drwxr-xr-x@ 10 praveenk  staff   320 Nov  7 10:52 ..
-rw-r--r--@  1 praveenk  staff  1718 Nov  6 23:08 run_eval.py

```

</details>

### 🔧 Tool: `view_file`  `2026-11-10T06:41:55`
`file:///Users/praveenk/E-Drive/moring ai take home assessment/moring-ai-hiring-test/backend/eval/run_eval.py` (51 lines, 1718 bytes)

### 🔧 Tool: `run_command`  `2026-11-10T06:42:00`
```bash
ls -la backend/ledgerline/llm
```
* (in `/Users/praveenk/E-Drive/moring ai take home assessment/moring-ai-hiring-test`) → exit 0*

<details><summary>📤 Output</summary>

```
Command exited with code 0.

Command output:
total 48
drwxr-xr-x@  9 praveenk  staff   288 Nov  6 23:26 .
drwxr-xr-x@ 15 praveenk  staff   480 Nov  6 23:26 ..
-rw-r--r--@  1 praveenk  staff   822 Nov  6 23:08 __init__.py
drwxr-xr-x@  6 praveenk  staff   192 Nov  7 10:52 __pycache__
-rw-r--r--@  1 praveenk  staff  1052 Nov  6 23:08 anthropic_client.py
-rw-r--r--@  1 praveenk  staff   404 Nov  6 23:08 base.py
-rw-r--r--@  1 praveenk  staff  1644 Nov  6 23:08 fake.py
-rw-r--r--@  1 praveenk  staff  1581 Nov  6 23:08 openai_compat.py
-rw-r--r--@  1 praveenk  staff   762 Nov  6 23:08 pricing.py

```

</details>

### 🔧 Tool: `view_file`  `2026-11-10T06:42:04`
`file:///Users/praveenk/E-Drive/moring ai take home assessment/moring-ai-hiring-test/backend/ledgerline/extraction.py` (76 lines, 2741 bytes)

### 🔧 Tool: `view_file`  `2026-11-10T06:42:10`
`file:///Users/praveenk/E-Drive/moring ai take home assessment/moring-ai-hiring-test/backend/ledgerline/llm/pricing.py` (18 lines, 762 bytes)

### 🔧 Tool: `view_file`  `2026-11-10T06:42:19`
`file:///Users/praveenk/E-Drive/moring ai take home assessment/moring-ai-hiring-test/backend/ledgerline/pipeline.py` (91 lines, 3916 bytes)

### 🔧 Tool: `view_file`  `2026-11-10T06:42:24`
`file:///Users/praveenk/E-Drive/moring ai take home assessment/moring-ai-hiring-test/backend/ledgerline/api.py` (103 lines, 3848 bytes)

### 🔧 Tool: `view_file`  `2026-11-10T06:42:30`
`file:///Users/praveenk/E-Drive/moring ai take home assessment/moring-ai-hiring-test/backend/ledgerline/validation.py` (99 lines, 3169 bytes)

### 🔧 Tool: `view_file`  `2026-11-10T06:42:42`
`file:///Users/praveenk/E-Drive/moring ai take home assessment/moring-ai-hiring-test/docs/AP_POLICY.md` (90 lines, 6339 bytes)

## 🤖 Assistant  `2026-11-10T06:42:42`
<details><summary>💭 Thinking</summary>

The user's prompt requests a simplified explanation of the project, its issues, and required fixes, focusing on clarity and ease of understanding. This involves breaking down complex information into a structured, human-readable format. The initial step is to define the project's big picture.


The project, Ledgerline, aims to automate invoice processing using an AI-driven system, addressing a monthly influx of invoices. Critical vulnerabilities exist in the system's policy enforcement; AI-driven decisions bypass validation checks, creating significant financial risks and fraud exposure, including handling duplicate invoices incorrectly and failing to properly handle bank account changes. The code is flawed in tax and rounding calculations.


The system's vulnerabilities include significant data privacy breaches, such as exposing sensitive vendor financial information to external AI services. A critical pricing bug leads to inaccurate billing calculations due to an error in the token usage calculation, resulting in inflated costs. The evaluation of the system's accuracy is flawed, as it only assesses text extraction, omits error cases, and leaks test data into the prompts, artificially inflating the results. Furthermore, the lack of clear traceability and UI usability issues impede the invoice review process, eroding user trust.




</details>

Here is a straightforward, plain-English breakdown of what this project is, what’s broken, and what you need to do to fix it.

---

### 1. What is this project?
**Meridian Precision Components** (an auto parts manufacturer near Pune) receives around 3,000 vendor invoices each month (scanned OCR text, emails, and GST e-invoices). 

A contractor built **Ledgerline** (Python FastAPI + SQLite backend, React frontend). Its job is:
1. Read incoming invoices using an LLM.
2. Check them against Meridian’s Accounts Payable (AP) policy.
3. Route them to **"Ready for Approval"** (safe to pay) or **"Needs Review"** (a human must check).

Meridian wants to roll this out next month to handle all invoices, but right now the system cannot be trusted.

---

### 2. The Core Problems (Why it’s failing)

#### A. Real Financial & Fraud Risk
* **The AI makes the decisions, ignoring code:** The contractor moved all policy checking into the LLM prompt. The deterministic Python validator (`validation.py`) only logs "warnings" for the UI and is completely ignored when deciding if an invoice is ready for payment! If the model hallucinates or gets confused, bad or fraudulent invoices get marked as safe to pay.
* **Duplicate payments can actually happen:**
  * In the API (`/approve`), double-clicking "Approve" creates duplicate payment records in the database.
  * Invoices requiring two approvals can be approved twice by the *same person*.
  * Duplicate invoice detection only does a naive string match on the vendor name, rather than checking GSTIN + normalized invoice number + financial year.
* **Bank account fraud vulnerability:** Meridian previously lost ₹3.8 lakh to a fake "our bank account changed" email. Yet `validation.py` only checks if the IFSC changed—it doesn't even check if the bank account number changed!
* **Calculations & GST:** The totals check doesn't handle Indian GST rules properly (intra-state CGST/SGST vs inter-state IGST), doesn't use the allowed ₹1 rounding tolerance, and uses floating-point arithmetic rather than exact decimals. The GSTIN checksum function is written but never actually called!

#### B. Data Privacy & Security Violation
* **Leaking bank accounts to external LLMs:** The prompt dumps the entire `vendors.csv` database into every single prompt. This directly violates company policy and Indian data regulations (the Data Protection Officer explicitly flagged that vendor bank accounts must not leave internal systems).

#### C. The Handover's "94% Accuracy" is Fake
* **Cheating the eval:** The prompt leaks the first 3 test invoices directly from `dev.jsonl` as few-shot examples.
* **Skipping failures:** The eval script (`run_eval.py`) wraps document processing in `except Exception: continue`—any document that crashes is completely omitted from the score rather than counted as a failure!
* **Measuring the wrong thing:** It only measures whether extracted text fields match, not whether the document was routed correctly (Ready vs Needs Review).

#### D. The Cost & Speed Mystery ($165 vs ₹15)
* The dashboard showed ₹15 total spend, but the CTO received a $165 bill from Anthropic. 
* Why? `pricing.py` has a severe math bug: it uses per-thousand token prices, but divides by 1,000,000 again.
* Furthermore, the code makes **two round-trip LLM calls** (`claude-opus-5-5`, the most expensive model) for every single invoice, stuffing the full policy text and the entire vendor database into both calls.

#### E. Reviewers Don't Trust It
* Reviewers can't see *where* on the document a number came from (no visual grounding or character offsets), so they re-type every number manually from the PDF anyway.

---

### 3. What Needs to Be Done (Step-by-Step)

| Step | What to do | Key Deliverable |
| :--- | :--- | :--- |
| **Part 0: First Hour** | Before modifying backend/frontend code, write a short diagnosis (< 300 words) of what you see, the top risks, and your plan. Commit it first. | `submission/FIRST_HOUR.md` |
| **Part 1: Make It Trustworthy** | 1. **Make routing deterministic**: Base `needs_review` and `review_reasons` on code checks (`validation.py`), not just LLM hallucination.<br>2. **Fix duplicate detection & bank verification**: Check bank account numbers + IFSC; check duplicates by GSTIN + normalized invoice number + FY.<br>3. **Fix API concurrency**: Prevent double-approval, enforce separate approvers, and stop duplicate payment creation.<br>4. **Fix data privacy**: Mask/remove bank details before sending text to the LLM.<br>5. **Fix token pricing**: Correct the formula in `pricing.py`. | Code fixes + unit tests + `submission/FINDINGS.md` |
| **Part 2: Disputed Invoices** | Review the 6 ambiguous documents in `data/invoices/disputed/`. Make a clear ruling on each (Ready or Review, which policy clause applies, and arguments for/against). Put any policy deviations behind feature flags. | `submission/RULINGS.md` + `predictions_disputed.jsonl` |
| **Part 3: Honest Evaluation** | Fix `run_eval.py`: remove data leakage, count crashed documents as failures, and evaluate routing accuracy (false acceptances/rejections), latency, and real cost (₹). | `submission/EVAL_REPORT.md` + `predictions_dev.jsonl` |
| **Part 4: Deep Dive (Pick One)** | Choose one area to go deep on:<br>• **A. Evidence-linked review**: Show source character offsets/citations in the UI & queue.<br>• **B. Survive production**: Switch to a cheaper model, optimize prompts, add fallback handling.<br>• **C. Custom idea**. | Code + writeup in `submission/DECISIONS.md` |
| **Part 5 & 6: Stakeholder Replies & Reflection** | Reply to the 5 stakeholders (CFO, AP Lead, CTO, DPO, Controller) addressing their specific requests, and write your retrospective. | `DECISIONS.md` & `REFLECTION.md` |

---

### Recommended First Step
Start by drafting **`submission/FIRST_HOUR.md`** and committing it to git. Once that's committed, we can begin fixing the highest-risk issues in `backend/ledgerline/validation.py`, `pipeline.py`, and `api.py`. Let me know when you're ready to draft `FIRST_HOUR.md`!

*Model: `MODEL_PLACEHOLDER_M319` | Stop: `STOP_REASON_STOP_PATTERN` | Think: `18.297871s`*
