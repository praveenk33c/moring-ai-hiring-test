# Ledgerline Issues Tracker

Track every issue identified across the codebase. Mark each checkbox (`- [x]`) once the fix and its tests are complete.

---

## Part A: Issues Identified in `FIRST_HOUR.md`

- [x] **Issue 1: Duplicate Payment on Double-Click / Repeat Approval**
  - **Files:** `backend/ledgerline/api.py` (`approve_invoice`), `frontend/src/App.tsx` (`approve`)
  - **Details:** Calling `/api/invoices/{id}/approve` on an already-approved invoice inserts another approval row and creates duplicate payment rows in `payments`. The UI button also does not disable while a request is in flight.

- [x] **Issue 2: AI Decides Routing & Ignores Deterministic Code Checks**
  - **Files:** `backend/ledgerline/pipeline.py` (`process_document`)
  - **Details:** `run_checks()` only populates `warnings`. `needs_review` and `review_reasons` are taken directly from the LLM's JSON output (`data.get("requires_review")`), allowing hallucinations or prompt injections to bypass AP policy.

- [x] **Issue 3: Bank Change Check Only Checks IFSC, Ignores Account Number**
  - **Files:** `backend/ledgerline/validation.py` (`check_bank_details`)
  - **Details:** Only checks `inv.ifsc != vendor["ifsc"]` (case-sensitively) and completely ignores `inv.bank_account`. Per AP Policy Section 3, bank account numbers must be compared digits-only and IFSC case-insensitively (e.g., `dev_024` has a changed account number with the same IFSC).

- [x] **Issue 4: Totals & Indian GST Rules Are Broken**
  - **Files:** `backend/ledgerline/validation.py` (`check_tax_type`, `check_totals`, `is_valid_gstin`)
  - **Details:**
    - **State code bug:** `BUYER_STATE_CODE = 27` is an `int`, while `inv.supplier_gstin[:2]` is a `str` (`"27"`). `"27" == 27` is always `False` in Python, inverting intra-state GST checks (and it should read `buyer["state_code"]` from `ref.buyer`).
    - **GSTIN checksum unused:** `gstin_checksum()` is defined but never called in `is_valid_gstin()`, and regex uses `.match()` instead of `.fullmatch()`.
    - **Totals math:** `check_totals()` uses binary `float` instead of `Decimal`, ignores `inv.round_off`, and checks exact equality (`computed == inv.total`) instead of allowing the policy's `<= ₹1.00` tolerance.

- [x] **Issue 5: LLM Cost Dashboard Mismatch ($165 actual bill vs ₹15 shown)**
  - **Files:** `backend/ledgerline/llm/pricing.py` (`USD_PER_MTOK`, `cost_usd`), `backend/ledgerline/extraction.py` (`extract`)
  - **Details:** `pricing.py` stores per-1K token prices (e.g., `0.004`, `0.020`) under a dict named `USD_PER_MTOK` and divides by `1,000,000` in `cost_usd()`, under-reporting cost by `1,000x`. Also, `extraction.py` makes 2 full LLM passes per document using the most expensive model (`claude-opus-5-5`) with bloated prompts.

---

## Part B: Additional Issues Identified in the Codebase

### 1. Data Privacy & Security (DPO Blockers)

- [x] **Issue 6: Leaking Vendor Bank Accounts to External LLMs**
  - **Files:** `backend/ledgerline/extraction.py` (`build_extraction_prompt`, `build_verification_prompt`)
  - **Details:** Embeds the entire raw `ref.vendors_csv` (containing all 38 vendors' bank account numbers) into every prompt, and sends unmasked bank account numbers in raw document text. Violates AP Policy Section 5.1 (bank account numbers must not leave internal systems; masking all but the last 4 digits is acceptable).

- [x] **Issue 7: Prompt Injection (`suspicious_content`) & Stored XSS in UI**
  - **Files:** `backend/ledgerline/validation.py`, `frontend/src/App.tsx`
  - **Details:**
    - Hostile documents (`dev_012`, `dev_013`) contain prompt-injection instructions to skip checks or embedded `<script>`/HTML markup.
    - `validation.py` has no check for `suspicious_content` (AP Policy Section 3).
    - `frontend/src/App.tsx` renders `selected.notes` via `dangerouslySetInnerHTML={{ __html: selected.notes }}`, creating a Stored XSS vulnerability.

- [x] **AI Response & Automated Decision Snapshot Logging (Audit Trail - Policy Section 5.3)**
  - **Files:** `backend/ledgerline/db.py`, `backend/ledgerline/extraction.py`, `backend/ledgerline/pipeline.py`
  - **Details:** Persists a trace snapshot in `ai_logs` with a unique `uuid4` (`log_id`), `provider`, `model_version`, `prompt_version`, masked `prompt`, `extraction_result`, `confidence`, `policy_version`, `decision`, and UTC ISO `timestamp`.

### 2. Missing or Broken Policy Validation Rules (`validation.py`)

- [x] **Issue 8: Vendor Matching Uses Exact `supplier_name` Instead of GSTIN / Supplier Key**
  - **Files:** `backend/ledgerline/validation.py` (`find_vendor`)
  - **Details:** Matches by `legal_name.strip().lower()`. Per AP Policy Section 1, domestic suppliers must be matched **by GSTIN alone**, and foreign suppliers by legal name ignoring case, spaces, and punctuation.

- [x] **Issue 9: Duplicate Detection Ignores Supplier Key, Normalized Invoice Number, and Financial Year (FY)**
  - **Files:** `backend/ledgerline/validation.py` (`check_duplicate`)
  - **Details:** Checks exact `supplier_name` and `invoice_number` without normalizing or checking FY. Per AP Policy Section 1 & 3:
    - Normalize invoice number (uppercase, strip spaces and `/ - # .`, preserve leading zeros).
    - Match duplicates on `(supplier_key, normalized_invoice_number, financial_year)` against `ref.paid_invoices` and earlier invoices in the same batch (e.g., `dev_016` is in a different FY and not a duplicate; `dev_019` is a duplicate of `dev_006` despite `"Pvt Ltd"` without dots).
    - Skip duplicate check for `credit_note` documents.

- [x] **Issue 10: Missing `credit_note`, `vendor_new`, and `foreign_currency` Checks**
  - **Files:** `backend/ledgerline/validation.py`
  - **Details:**
    - `credit_note`: Flag when `document_type == "credit_note"` (`dev_007`).
    - `vendor_new`: Flag when matched vendor's `onboarded_on` date is `< 90` days before `invoice_date` (`dev_011`, `dev_012`).
    - `foreign_currency`: Flag when `currency != "INR"` (`dev_014`).

- [x] **Deterministic OCR GSTIN Repair Workflow (CFO Ask / Disputed `disp_01.txt`)**
  - **Files:** `backend/ledgerline/validation.py` (`repair_ocr_gstin`), `backend/ledgerline/pipeline.py`
  - **Details:** Never let the LLM randomly change GSTINs. Instead, deterministically verify against the internal vendor DB first; if not found or invalid, try single-character OCR confusable substitutions (`I` ↔ `1`, `B` ↔ `8`, `O` ↔ `0`, `S` ↔ `5`, `Z` ↔ `2`, `G` ↔ `6`) against known vendor GSTINs and verify structural + mod-36 checksum validity (`is_valid_gstin`). Gated behind `LEDGERLINE_FLAG_OCR_GSTIN_REPAIR=1` so strict mode routes to human review (`gstin_invalid` / `vendor_unknown`) by default.

### 3. Approval & Audit Workflow Bugs (`pipeline.py` & `api.py`)

- [x] **Issue 11: Wrong `required_approvals` Calculation**
  - **Files:** `backend/ledgerline/pipeline.py`
  - **Details:** Uses `2 if (inv.total or 0) > 500000 else 1`. Per AP Policy Section 4.1:
    - Credit notes require `0` approvals (`dev_007`).
    - Foreign-currency invoices (`currency != "INR"`) require `2` approvals (`dev_014`).
    - High-value threshold is `>= 500000.00` (`5,00,000.00` or more, affecting `dev_017` where total is `500000.00`).
    - All other invoices require `1` approval.

- [x] **Issue 12: Missing Server-Side Approval Enforcement & Audit Logging**
  - **Files:** `backend/ledgerline/api.py`, `backend/ledgerline/db.py`
  - **Details:**
    - Same user can approve twice (`SELECT COUNT(*)` instead of `COUNT(DISTINCT user_id)` — violates Policy Section 4.2).
    - Credit notes and `duplicate`-flagged invoices can currently be approved for payment (violates Section 4.1 & 4.4).
    - Documents with `needs_review == True` can be approved with an empty `note` (violates Section 4.5).
    - `reject_invoice` does not record who rejected the document, when, or the note in an audit log (violates Section 4.7).

### 4. Parsing Bugs (`parsing.py`)

- [x] **Issue 13: Indian Date Parsing is Month-First Instead of Day-First**
  - **Files:** `backend/ledgerline/parsing.py` (`parse_date`), `backend/tests/test_parsing.py`
  - **Details:** `dateparser.parse(str(value))` defaults to `dayfirst=False` (US `MM/DD/YYYY`), parsing `"03/04/2026"` as March 4 (FY 25-26) instead of April 3 (FY 26-27). Per Policy Section 1, Indian vendors use day-first (`DD/MM/YYYY`) and US vendors (`country == "US"`) use month-first (`MM/DD/YYYY`).

- [x] **Issue 14: Amount Parsing & Binary Floating-Point Precision**
  - **Files:** `backend/ledgerline/parsing.py` (`parse_amount`), `backend/ledgerline/models.py`
  - **Details:** Only strips `₹`, `INR`, and `,`. Fails on `Rs.`, `/-`, `$`, `USD`, or words like `lakh`/`crore` (AP Policy Section 1), and uses binary `float` instead of exact `Decimal`.

### 5. Evaluation, Data Leakage & Batch CLI Contract (`extraction.py`, `cli.py`, `run_eval.py`)

- [x] **Issue 15: Dev Set Data Leakage in Prompt**
  - **Files:** `backend/ledgerline/extraction.py` (`_few_shot_examples`)
  - **Details:** Reads the first 3 rows directly from `data/ground_truth/dev.jsonl` into the extraction prompt, leaking evaluation ground truth and coupling runtime code to the dev dataset path.

- [x] **Issue 16: Silently Dropping Failed Documents (`processing_error`)**
  - **Files:** `backend/ledgerline/cli.py` (`predict`), `backend/eval/run_eval.py` (`main`), `backend/ledgerline/pipeline.py`
  - **Details:** Both `cli.py` and `run_eval.py` catch exceptions and `continue` (skipping the document). Per `OUTPUT_CONTRACT.md` and AP Policy Section 3, no document may ever be skipped—failed documents must output a prediction row with `needs_review: true` and `"processing_error"` in `review_reasons`.

- [x] **Issue 17: Output Contract Formatting Mismatches**
  - **Files:** `backend/ledgerline/cli.py` (`to_contract`), `backend/ledgerline/pipeline.py`
  - **Details:** Uncharged taxes/round_off must be `"0.00"` (not `null`), and `line_items` fields (`quantity`, `unit_price`, `amount`) must match the `OUTPUT_CONTRACT.md` format.

