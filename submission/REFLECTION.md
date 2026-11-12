# Reflection

_In your own words, about 20 minutes._

## Three things I didn't know when I started, and how I learned each one

1. I didn't realize that an invoice itself could contain a prompt injection
2. Initially, I treated the confidence returned by the model as something that could help determine whether an invoice was safe to process automatically. While working on the evaluation, I realized that a model saying it is 95% confident does not mean it is actually correct 95% of the time. I learned that confidence needs to be evaluated against labelled ground truth and calibrated before it can be used for production routing.
3. I initially thought that providing a few existing invoice examples to the model would simply help it understand the expected output format. During the evaluation review, I realized that if those examples come from the same dataset being used for evaluation, the model is effectively seeing some of the answers before being tested. This can make the measured accuracy look better than it really is. I learned this by tracing where the few-shot examples were loaded from and comparing them with the evaluation dataset. I then understood why evaluation examples need to be kept separate from the data used to measure performance.

## The decision I'm least sure of

What it was, why I made it, and what would show me it was wrong.

## With one more week
1. I would create a clean labelled test set that is separate from any few-shot examples and measure field-level accuracy, full-invoice accuracy, false-ready rate, false-review rate, and routing accuracy. This would give me confidence that the changes actually improve the system.

2. Once the accuracy, security, cost, and routing metrics are understood, I would gradually increase the percentage of invoices that can bypass manual review rather than assuming that all invoices under ₹10,000 are safe.
