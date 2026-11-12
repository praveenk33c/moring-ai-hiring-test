# How I worked with AI

## Tools and models
I used Antigravity IDE's AI assistant as my primary AI coding and reasoning tool. I used it for repository exploration, understanding the existing implementation, identifying risks, explaining unfamiliar code, proposing fixes, writing tests, debugging failures, and reviewing implementation decisions.

I treated the AI as a pair programmer rather than as the source of truth. The written AP policy, output contract, existing tests, reference data, and observed application behavior were used to verify its suggestions.

## How I set up context
I first asked the AI to inspect the repository and explain the project and its risks before making implementation changes. I then had it read the README, AP policy, architecture, handover, output contract, backend modules, frontend code, evaluation code, tests, and reference data.

I created submission/FIRST_HOUR.md before modifying the backend/frontend, as required by the assignment. I also created an ISSUES.md tracker containing the identified problems so that I could work through them individually.

For each issue, I gave the AI the specific problem and relevant code context rather than asking it to make broad uncontrolled changes.

## My workflow

How you split the work between yourself and the AI, and how you checked its output.

## Where the AI was wrong

I divided the work into individual issues and handled them one at a time.

For each issue, I first asked the AI to explain the problem and the relevant policy requirement. I then reviewed the proposed approach before allowing code changes. Where appropriate, I asked for a test that demonstrated the expected behavior.

I used a test-driven feedback loop:

Understand the policy and existing behavior.

Identify the specific defect.

Add or update a focused test.

Run the test and observe the failure.

Implement the fix.

Run the complete test suite.

Review the resulting code and behavior.

Mark the issue complete only after verification.

For example, the idempotency change initially produced two failing tests. After the implementation was corrected, the complete suite passed with 22 tests. This helped me verify the behavior instead of relying only on the AI's explanation.

I also used the AI to investigate broader issues such as prompt injection, stored XSS, evaluation leakage, LLM cost calculation, policy enforcement, and OCR-related GSTIN handling. For security- and finance-sensitive decisions, I preferred deterministic validation in code over relying on the LLM's judgment.

## What I deliberately didn't delegate, and why

## Time

I have spent around 8 hours to fix around 15 issues.

## Transcripts

The transcripts were attached in ai-logs named "Project explanation and Fixes.md".
