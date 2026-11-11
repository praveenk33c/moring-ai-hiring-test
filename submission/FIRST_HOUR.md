# My first hour

_Under about 300 words, in your own words. Commit it on its own, before any commit that touches `backend/` or `frontend/`, and don't edit it afterwards. Save the AI sessions from this stretch in `ai-logs/` with a name starting `00_first_hour`. Being wrong here is fine._

## What I think is going on

It is basically an AP(accounts payable) automation system, where an invoice is raised by a vendor and then it will passed to the llm to extract the data from it and then it will be validated against the AP policy. If everything is in place, it will be approved and payment will be made. If not, it will be sent to the user to review and approve.

## The risks I suspect, most serious first
- Double clicking the approve button leading to approve the payment twice or more. This makes duplicating the payment.

- The AI makes the decision ignoring the code in AP policy (Hallucinating). This can lead to fraud or approving the payment without following the policy.

- When the bank account got changed or updated in the vendor master, it checks only for the IFSC code and not for the account number. This can lead to fraud.

- Total checks doesn't handle indian GST rules properly.

- LLM's usage bill amount is higer than the usage cost showing in dashboard.

## My plan for the time I have

- I'll start with implementing idempotency for the payment approval API.

- Improve validation for the bank account changes and make sure that the invoices are following AP policy before marking as approved.

- Adding GST rule validation with proper audit trail

- Adding test cases for all the above mentioned scenarios.

## What I would ask Meridian
