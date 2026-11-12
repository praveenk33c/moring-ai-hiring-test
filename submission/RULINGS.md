# Rulings on the disputed documents

_There is no right answer for these. Copy the block below for each document in `data/invoices/disputed/`, about 150 words each, in your own words._

## My flags

Every departure from `AP_POLICY.md`, as an environment variable that is off by default: its name, what it changes, and which rulings need it. `predictions_disputed.jsonl` was produced with these switched on.

## disp_01

- **Ruling:** needs review or ready; which reasons; how many approvals
- **It rests on:** the policy text you relied on, or the gap in the policy it falls into
- **The best argument against my ruling:**
- **The policy change I'd propose, if any:**
- **Implemented?** Yes (flag and test names), or no, and why not
- **Does my pipeline's line in `predictions_disputed.jsonl` match?** If not, why

## The two I consider riskiest, and why

1. disp_01 — OCR GSTIN correction

This is risky because a wrong GSTIN correction could associate an invoice with a different vendor. A correction must never be based on the model's guess alone. I chose a deterministic approach that checks the internal vendor master, validates the GSTIN structure and checksum, and accepts only one unique match.

2. disp_02 — Revised invoice

This is risky because the revised invoice has the same invoice number as the earlier version but a different amount. If both versions are processed, Meridian could make duplicate or excessive payments. I would require confirmation that the previous version has been cancelled or replaced before allowing the revised invoice to proceed.
