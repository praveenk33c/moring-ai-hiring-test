# Decisions

## Architecture

My main architectural decision was to separate information extraction from financial decision-making.

The LLM is responsible for understanding invoice documents and extracting information that may be difficult to obtain using fixed parsing rules. Python code is responsible for validating the extracted information, enforcing the AP policy, deciding whether an invoice can proceed, and recording the decision.

## Part 4: what I went deep on, and why

Which option you chose (A, B or C), and why it mattered more than the others.

## Replies to stakeholders

### Anita Rao, CFO
I've implemented support for the under-₹10,000 straight-through processing target, but only when all mandatory validation checks pass. Any OCR-corrected GSTIN must be verified against the vendor master rather than guessed or inferred by the model.

### Farhan Sheikh, Head of AP
I've ensured the system will provide evidence for extracted values, block bank-detail changes pending independent verification, and prevent duplicate payments. His preference for the most accurate model must be balanced against Deepak's cost and latency targets.

### Deepak Menon, CTO
I have corrected the 1,000× pricing error, optimize prompts and model calls, and benchmark before considering fine-tuning.

### Priya Natarajan, Data Protection Officer
I've implemented masking of bank account numbers, ensuring they are never exposed in external LLM prompts.

### Sunil Joshi, Finance Controller
I've implemented risk-based routing to avoid sending every uncertain invoice for manual review. I've also recommended defining a clear callback verification process before adding vendor phone numbers to the master.

### Ravi Kulkarni, contractor
I used AI to handle messy invoice layouts and variations in vendor name formats, where it adds the most value. However, I moved policy enforcement into Python (validation.py) to prevent prompt injection risks, protect vendor bank account details from external LLM providers, ensure accurate GSTIN validation, and reduce unnecessary API costs.

## Policy changes I propose

Each as a short proposal to the Finance Controller: what changes, why, and what it costs or risks.
