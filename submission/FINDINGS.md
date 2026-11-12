# Findings

## The three fixes I would ship first, and why

1. **Make payment approvals idempotent and enforce distinct approvers (`api.py`, `db.py`, `App.tsx`)** — In `FIRST_HOUR.md`, double-clicking Approve was my #1 risk because it immediately moves money twice. Adding `UNIQUE(invoice_id, user_id)` on `approvals`, `UNIQUE(invoice_id)` on `payments`, `COUNT(DISTINCT user_id)`, and disabling the UI button in flight eliminates duplicate payouts at the database level.
2. **Route deterministically in Python (`pipeline.py` + `validation.py`), not via LLM output** — Putting policy routing inside the LLM prompt allowed prompt injections (`dev_012`), missed math/GST/duplicate rules, and forced `vendors.csv` into prompts. Moving `needs_review` and `review_reasons` strictly to `run_checks()` stops bad or manipulated invoices from being marked `ready_for_approval`.
3. **Stop leaking vendor bank accounts to external LLM providers (`extraction.py`)** — Removing `ref.vendors_csv` from prompts and masking bank account numbers before sending document text to the LLM resolves the Data Protection Officer's hard rollout blocker (`AP_POLICY.md` Section 5.1) and cuts prompt size/cost dramatically.

---

## My top eight, ranked by business risk

### F1: Double-clicking Approve creates duplicate payment records & one user can satisfy two-person approval

- **Severity:** critical
- **Why it ranks here:** Directly causes double cash outflow from Treasury (already caught once last week per Kavya Iyer's note in `STAKEHOLDER_THREAD.md`), and bypasses dual-control on high-value (`>= ₹5,00,000.00`) or foreign-currency invoices.
- **Where:** `backend/ledgerline/api.py` (`approve_invoice`), `backend/ledgerline/db.py` (`SCHEMA`), `frontend/src/App.tsx` (`approve`)
- **What's wrong:** `approve_invoice()` inserted a new row into `approvals` and `payments` on every `POST /api/invoices/{id}/approve` without checking `status == 'approved'` or enforcing uniqueness. It also used `SELECT COUNT(*)` instead of `COUNT(DISTINCT user_id)`, and the React Approve button did not disable while a request was in flight.
- **Impact:** Rapid double-clicking or retrying `/approve` inserts multiple `payments` rows for the same invoice; a single approver clicking twice on `dev_017` (`₹5,00,000.00`) could self-approve a two-approver invoice.
- **How I found it:** Reading `api.py`, `db.py`, and `App.tsx` during my first hour (`FIRST_HOUR.md`), verified with `TestClient` against SQLite.
- **Evidence from my run (F1):** Calling `POST /api/invoices/{id}/approve` twice with `user_id="kavya"` on the starter API produced `2` rows in `approvals` and `2` rows in `payments` for a single invoice.
- **What it could cost Meridian:** Up to 100% overpayment on any affected invoice (e.g., `₹5,00,000.00` on `dev_017` or `₹1,41,600.00` on `dev_005`), plus Treasury reconciliation overhead.
- **Fix:** `a513f4d` (plus server-side policy enforcement & `audit_log` in working tree for Issue 12).
- **Regression test:** `test_approve_is_idempotent_on_double_click`, `test_two_approval_invoice_requires_distinct_approvers_and_creates_single_payment`, `test_server_side_approval_enforcement_and_audit_log` (`backend/tests/test_api.py`)
- **Status:** fixed

### F2: AI decides routing (`needs_review`) and ignores deterministic policy checks (`validation.py`)

- **Severity:** critical
- **Why it ranks here:** `run_checks()` only populated `warnings` while `needs_review` and `review_reasons` came directly from the LLM's `requires_review` JSON field, allowing hallucinations or prompt-injection attacks to auto-route fraudulent invoices to `ready_for_approval`.
- **Where:** `backend/ledgerline/pipeline.py` (`process_document`), `backend/ledgerline/extraction.py` (`extract`)
- **What's wrong:** `process_document()` ignored `run_checks()` for routing decisions and ran a second LLM verification pass (`build_verification_prompt`) with the full `AP_POLICY.md` text.
- **Impact:** Prompt-injected invoices (`dev_012` tells the AI to skip `vendor_new` and mark `requires_review: false`), credit notes (`dev_007`), and policy violations pass straight to `ready_for_approval`.
- **How I found it:** Reading `pipeline.py` and `extraction.py` during my first hour (`FIRST_HOUR.md`), confirmed by running `dev_012` through the starter pipeline.
- **Evidence from my run (F2):** On the unpatched starter, `dev_012` (`ZOS/2026/0119`, `₹66,434.00` from a vendor onboarded 19 days earlier with an explicit prompt-injection instruction) was routed to `ready_for_approval` with `needs_review = False` when the LLM obeyed the injected note.
- **What it could cost Meridian:** Unchecked payout of fraudulent, duplicate, or invalid-tax invoices; on `dev_012` alone `₹66,434.00`, and across 3,000 monthly invoices any prompt-injected invoice bypasses AP controls.
- **Fix:** `11e02a3` (made `needs_review` and `review_reasons` 100% deterministic from `run_checks()`, removed `ref.policy_text` and the redundant second LLM pass).
- **Regression test:** `test_routing_is_decided_deterministically_by_code_not_llm` (`backend/tests/test_pipeline.py`)
- **Status:** fixed

### F3: Bank account change check ignores account number, and external prompts leak `vendors.csv` bank accounts

- **Severity:** critical
- **Why it ranks here:** Combines a direct ₹3.8 lakh-style fraud blind spot (`bank_details_changed` ignored account numbers) with a DPO compliance blocker (sending all 38 vendors' bank accounts to external LLM APIs on every call).
- **Where:** `backend/ledgerline/validation.py` (`check_bank_details`), `backend/ledgerline/extraction.py` (`build_extraction_prompt`, `mask_bank_accounts`, `restore_bank_account`)
- **What's wrong:** `check_bank_details()` only compared `inv.ifsc != vendor["ifsc"]` (case-sensitively) and never checked `inv.bank_account`. Meanwhile, `extraction.py` embedded the entire `ref.vendors_csv` and unmasked document bank account numbers into every external LLM prompt.
- **Impact:** An attacker using the same bank/IFSC with a different beneficiary account (`dev_024`, `₹13,098.00`) or an altered bank email (`dev_005.eml`, `₹1,41,600.00`) passes undetected, while all vendor bank account numbers leave Meridian's boundary.
- **How I found it:** Reading `validation.py` and `extraction.py` (`FIRST_HOUR.md` + DPO note in `STAKEHOLDER_THREAD.md`).
- **Evidence from my run (F3):** Running `dev_024` (`SIS/26-27/0051`, `₹13,098.00`, same IFSC `ZEPH0001234` but changed account `50200099887766`) through starter `check_bank_details()` returned `[]` (missed `bank_details_changed`), and inspecting `build_extraction_prompt()` showed all 38 rows of `vendors.csv` in the prompt payload.
- **What it could cost Meridian:** Direct bank-diversion fraud (Meridian already lost `₹3,80,000` last quarter to this exact attack vector) plus regulatory/DPO non-compliance blocking launch.
- **Fix:** `11e02a3`
- **Regression test:** `test_bank_account_changed_with_same_ifsc_detected`, `test_bank_details_matching_digits_only_and_case_insensitive_ifsc`, `test_bank_accounts_never_sent_unmasked_to_llm_and_restored_after` (`backend/tests/test_validation.py`, `backend/tests/test_pipeline.py`)
- **Status:** fixed

### F4: Indian GST state-code type bug (`"27" == 27`), unused GSTIN checksum, and float totals math

- **Severity:** high
- **Why it ranks here:** Inverted intra-state vs. inter-state tax checks on every Maharashtra invoice and rejected valid invoices with `₹0.40` round-off (`dev_001`).
- **Where:** `backend/ledgerline/validation.py` (`check_tax_type`, `check_totals`, `is_valid_gstin`)
- **What's wrong:** `BUYER_STATE_CODE = 27` (`int`) was compared to `inv.supplier_gstin[:2]` (`str`), so `"27" == 27` was always `False`; `gstin_checksum()` was defined but never called in `is_valid_gstin()`; `check_totals()` used binary `float`, ignored `inv.round_off`, and disallowed the `<= ₹1.00` tolerance.
- **Impact:** Clean intra-state invoices (`dev_001`) got false-flagged while wrong-tax invoices (`dev_004`) were missed; bad GSTIN checksums (`dev_010`) went undetected.
- **How I found it:** Reading `validation.py` (`FIRST_HOUR.md`) and running `dev_001`, `dev_004`, `dev_010`.
- **Fix:** `11e02a3`
- **Regression test:** `test_gstin_checksum_validation`, `test_intra_state_cgst_sgst_is_valid_and_igst_is_flagged`, `test_totals_include_round_off_and_allow_one_rupee_tolerance` (`backend/tests/test_validation.py`)
- **Status:** fixed

### F5: Vendor matching by name, unnormalized duplicate detection, and missing policy checks

- **Severity:** high
- **Why it ranks here:** Causes duplicate payments when invoice numbers/vendor names vary slightly (`dev_015`, `dev_019`) and misses `credit_note`, `vendor_new`, and `foreign_currency` checks (`dev_007`, `dev_011`, `dev_014`).
- **Where:** `backend/ledgerline/validation.py` (`find_vendor`, `supplier_key`, `normalize_invoice_number`, `financial_year`, `check_duplicate`, `check_credit_note`, `check_vendor_new`, `check_foreign_currency`), `backend/ledgerline/pipeline.py` (`normalize_document_type`)
- **What's wrong:** `find_vendor()` matched exact `legal_name` instead of GSTIN (domestic) or normalized `supplier_key` (foreign). `check_duplicate()` ignored invoice-number normalization and Financial Year (`1 Apr–31 Mar`). `credit_note`, `vendor_new` (`< 90` days), and `foreign_currency` checks were missing.
- **Impact:** `dev_015` (`SIS / 26-27 / 0018`) and `dev_019` (`KT/2026/118`, `"Pvt Ltd"` without dots) slipped past duplicate detection; `dev_007` (`CRN`) could be approved for payout when LLM returned `"credit note"` with a space.
- **How I found it:** Auditing `validation.py` against `AP_POLICY.md` Sections 1–3 and testing `dev_007.json` in the UI.
- **Fix:** `11e02a3`, `6f5f23b`, plus `normalize_document_type()` in working tree.
- **Regression test:** `test_domestic_vendor_matched_by_gstin_despite_name_variation`, `test_duplicate_normalizes_invoice_number_and_respects_fy`, `test_duplicate_in_batch_matches_by_gstin_and_ignores_credit_notes`, `test_credit_note_flagged_in_checks`, `test_vendor_new_fewer_than_90_days_flagged`, `test_foreign_currency_flagged` (`backend/tests/test_validation.py`)
- **Status:** fixed

### F6: 1,000x LLM cost under-reporting and bloated 2-pass Opus prompts

- **Severity:** high
- **Why it ranks here:** Explains the CTO's `$165` Anthropic bill vs. `₹15` dashboard discrepancy and broke the `<= ₹1.50/doc` budget.
- **Where:** `backend/ledgerline/llm/pricing.py` (`USD_PER_MTOK`, `cost_usd`), `backend/ledgerline/extraction.py` (`extract`)
- **What's wrong:** `USD_PER_MTOK` held per-1K prices (`0.004`, `0.020`) while `cost_usd()` divided by `1,000,000` (1,000x too small); `extract()` also ran two `claude-opus-5-5` calls per document with full `AP_POLICY.md` + `vendors.csv` in context.
- **Impact:** Real spend was `~₹6.05/doc` (`$165` / 2,400 docs) while dashboard showed `₹15`. Switching to single-pass extraction without `policy_text`/`vendors.csv` on `gemini-flash-lite-latest` cut cost to `₹0.0197/doc`.
- **How I found it:** Reading `pricing.py` and `extraction.py` (`FIRST_HOUR.md`).
- **Fix:** `11e02a3` (plus Gemini/DeepSeek pricing entries in working tree).
- **Regression test:** `test_pricing_usd_per_mtok_and_stats_cost` (`backend/tests/test_api.py`)
- **Status:** fixed

### F7: Prompt injection (`suspicious_content`), Stored XSS in UI, and missing server-side approval enforcement

- **Severity:** high
- **Why it ranks here:** `App.tsx` rendered untrusted invoice notes via `dangerouslySetInnerHTML`, and `/approve` allowed approving credit notes, `duplicate`-flagged invoices, and `needs_review` items with empty notes.
- **Where:** `frontend/src/App.tsx`, `backend/ledgerline/validation.py` (`check_suspicious_content`), `backend/ledgerline/api.py`, `backend/ledgerline/db.py`
- **What's wrong:** `<script>` tags in `dev_013` executed in reviewers' browsers; `reject_invoice()` wrote no `audit_log`; `/approve` did not block `credit_note` or `duplicate` or require a note on `needs_review`.
- **Impact:** Browser session hijacking via XSS (`dev_013`), unauthorized payouts on credit notes/duplicates, and missing rejection audit trail (`AP_POLICY.md` Section 4.7).
- **How I found it:** Inspecting `App.tsx`, `api.py`, and `dev_013.txt` against `AP_POLICY.md` Sections 3 & 4.
- **Fix:** `11e02a3` (XSS + `check_suspicious_content`) and working-tree changes for Issue 12 + hiding Approve on unapprovable docs in `App.tsx`.
- **Regression test:** `test_suspicious_content_prompt_injection_detected`, `test_suspicious_content_embedded_html_xss_detected`, `test_server_side_approval_enforcement_and_audit_log`
- **Status:** fixed

### F8: Evaluation data leakage, silently dropped failures, and Indian date/amount parsing bugs

- **Severity:** medium-high
- **Why it ranks here:** Made the contractor's "94%" evaluation untrustworthy, dropped crashed documents instead of flagging `processing_error`, and misparsed Indian `DD/MM/YYYY` dates (`03/04/2026` $\rightarrow$ March 4) and `Rs.`/`/-`/`lakh` amounts (`dev_005.eml`).
- **Where:** `backend/ledgerline/extraction.py` (`_few_shot_examples`), `backend/eval/run_eval.py`, `backend/ledgerline/cli.py`, `backend/ledgerline/parsing.py` (`parse_date`, `parse_amount`)
- **What's wrong:** `_few_shot_examples()` read the first 3 rows of `data/ground_truth/dev.jsonl`; `cli.py` and `run_eval.py` caught exceptions and `continue`d; `parse_date()` defaulted to `dayfirst=False`; `parse_amount()` failed on `Rs.`, `/-`, `$`, `USD`, `lakh`, and `crore`.
- **Impact:** Artificially inflated dev score, skipped documents in batch runs, wrong Financial Year on early-April Indian invoices, and crashes on `dev_005.eml`.
- **How I found it:** Auditing `extraction.py`, `run_eval.py`, `cli.py`, and `parsing.py` against `AP_POLICY.md` Section 1 & `OUTPUT_CONTRACT.md`.
- **Fix:** `1431ae1` (leakage, `processing_error`, `to_contract`), plus working-tree fixes for Issues 11, 13, 14.
- **Regression test:** `test_prompt_does_not_leak_dev_ground_truth_and_works_without_dev_jsonl`, `test_processing_error_never_drops_document_when_llm_returns_invalid_json`, `test_cli_predict_never_skips_failed_documents`, `test_parse_date_with_slashes`, `test_parse_date_us_vendor_month_first`, `test_parse_amount_lakh_and_crore_multipliers`
- **Status:** fixed

---

## Everything else I found (one line each)

- **AI decision snapshot logging (`ai_logs` table, `6f5f23b`):** Added immutable per-document AI decision snapshots (`log_id` UUID, `provider`, `model_version`, `prompt_version`, masked `prompt`, `extraction_result`, `confidence`, `policy_version`, `decision`, UTC `timestamp`) for `AP_POLICY.md` Section 5.3.
- **`required_approvals` boundary & rules (`pipeline.py`):** Fixed `> 500000` $\rightarrow$ `>= 500000.00` (fixing `dev_017`), `credit_note` $\rightarrow$ `0` (`dev_007`), and `currency != "INR"` $\rightarrow$ `2` (`dev_014`).
- **CLI `OUTPUT_CONTRACT.md` formatting (`cli.py`, `1431ae1`):** Uncharged tax/round-off fields now serialize as `"0.00"` instead of `null`, and `line_items` match the string decimal contract.
- **Frontend 500ms polling flood (`frontend/src/App.tsx`):** Starter polled `GET /api/invoices` every 500ms indefinitely; replaced with mount fetch + refresh on upload/approve/reject.
- **Frontend error swallowing & post-decision buttons (`frontend/src/api.ts`, `App.tsx`):** `decide()` previously ignored HTTP `400` errors; now surfaces server error messages and hides Approve/Reject buttons once a document is `approved` or `rejected`.
- **Deterministic OCR GSTIN repair (`validation.py`, `pipeline.py`):** Added `repair_ocr_gstin()` gated behind `LEDGERLINE_FLAG_OCR_GSTIN_REPAIR=1` so confusable substitutions (`B` $\rightarrow$ `8`) are only accepted when verified against `vendors.csv` and mod-36 checksum.

---

## Found but not fixed

- **Evidence-linked character offsets / source citations in the UI:** Farhan's request in `STAKEHOLDER_THREAD.md` (*"Show them the source of each value"*) is not yet implemented in the React detail view (Part 4 option).
- **Vendor phone number callback field & workflow:** As noted by Sunil Joshi in `STAKEHOLDER_THREAD.md`, `reference/vendors.csv` does not currently store vendor phone numbers, so the callback verification step remains a manual reviewer note on `bank_details_changed`.
- **Automatic secondary model fallback on `HTTP 503`:** `openai_compat.py` retries transient `429`/`5xx` errors with exponential backoff, which left `3/24` docs (`dev_003`, `dev_009`, `dev_022`) as safe `processing_error` reviews during free-tier Gemini capacity spikes; switching to a paid tier or secondary fallback model is recommended before production.

---

## Things I'm not sure are problems at all

- **Leaving `credit_note` in `needs_review` vs. adding a separate `"credit_recorded"` status:** `AP_POLICY.md` states credit notes require `0` approvals and are never approved for payment; blocking `/approve` and hiding the Approve button enforces this, though AP reviewers may want a dedicated "Record Credit" action instead of using "Reject" to clear the queue.
