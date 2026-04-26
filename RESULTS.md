# Step 10 Golden Suite Results

Run date: 2026-04-26T05:08:15Z  
Model: smollm2-360m  
Total questions: 10

## Summary

| Type | Total | Passed | Failed |
|------|-------|--------|--------|
| ISTQB | 7 | 0 | 7 |
| Abstain trigger | 3 | 3 | 0 |

## Per-question results

### q01 — ISTQB — "What is metamorphic testing, explain in simple way?"

Concept correctness: FAIL
  - matched: []
  - missing: ['metamorphic relation', 'transformation', 'oracle', 'invariant']
  - count: 0

Terminology coverage: PASS
  - present: ['metamorphic testing']
  - absent: []

Hallucination absence: FAIL
  - banned_found: []
  - topics_matched: []

Answer (first 500 chars):
  "Metamorphic testing is a type of automated test automation that focuses on the behavior and output of an application over time. It allows for the testing of applications that have changed over time, such as new features or updates. Instead of running the application at the start of every test, or testing only the latest features, metamorphic testing automatically tests the application after each change, so it can check for any new behavior or any changes that occurred in the application. This ap"

---

### q02 — ISTQB — "How to do A/B testing for AI/ML systems?"

Concept correctness: FAIL
  - matched: []
  - missing: ['control group', 'variant', 'treatment', 'statistical significance', 'hypothesis']
  - count: 0

Terminology coverage: PASS
  - present: ['A/B testing']
  - absent: []

Hallucination absence: FAIL
  - banned_found: []
  - topics_matched: []

Answer (first 500 chars):
  "A/B testing for AI/ML systems typically involves dividing an audience into two groups, each receiving a different version of an AI/ML algorithm or feature. The goal is to see which version performs better on the outcome being tested. 

Here are the steps involved:

1. Divide the audience into two groups.
2. Test each group with the original algorithm/feature.
3. After the first test, compare the performance of each group to see which one performs better.
4. If one group performs significantly be"

---

### q03 — ISTQB — "What is Test oracle problem?"

Concept correctness: FAIL
  - matched: []
  - missing: ['expected output', 'correctness', 'judgment', 'ground truth']
  - count: 0

Terminology coverage: PASS
  - present: ['test oracle']
  - absent: []

Hallucination absence: FAIL
  - banned_found: []
  - topics_matched: []

Answer (first 500 chars):
  "The Test Oracle problem refers to the lack of visibility or understanding of the interactions between various components of a system, resulting in unfulfilled tests. In other words, the tests may not be testing the components correctly, which can lead to defects. The Test Oracle problem can occur in various forms, such as:

1. Functional test oracle: The test suite may not cover all functional requirements or may not be properly documented.
2. Non-functional test oracle: The test suite may not c"

---

### q04 — ISTQB — "How to validation the ML model?"

Concept correctness: FAIL
  - matched: []
  - missing: ['training', 'test set', 'validation set', 'accuracy', 'cross-validation']
  - count: 0

Terminology coverage: FAIL
  - present: []
  - absent: ['model validation']

Hallucination absence: FAIL
  - banned_found: []
  - topics_matched: []

Answer (first 500 chars):
  "I don't have enough information from the available documents to answer this."

---

### q05 — ISTQB — "What is Bias and fairness in context of while testing AI systems?"

Concept correctness: FAIL
  - matched: ['bias', 'fairness']
  - missing: ['protected attributes', 'discrimination', 'demographic']
  - count: 2

Terminology coverage: PASS
  - present: ['bias', 'fairness']
  - absent: []

Hallucination absence: FAIL
  - banned_found: []
  - topics_matched: []

Answer (first 500 chars):
  "Yes, the question is about Bias and fairness in context of testing AI systems. The context discusses the concept of bias and fairness in AI testing, and explores how to identify and address these issues.

The question mentions that testing AI systems can lead to bias and fairness issues. Bias in testing refers to the presence of unfair or discriminatory practices in testing. Fairness in testing refers to the ability to determine whether testing methods are fair and unbiased, ensuring that AI sys"

---

### q06 — ISTQB — "What is Adversarial testing?"

Concept correctness: FAIL
  - matched: ['robustness', 'attack']
  - missing: ['adversarial example', 'perturbation']
  - count: 2

Terminology coverage: PASS
  - present: ['adversarial testing']
  - absent: []

Hallucination absence: FAIL
  - banned_found: ['security testing']
  - topics_matched: ['robustness']

Answer (first 500 chars):
  "Adversarial testing is a type of cybersecurity testing that involves intentionally manipulating the system or data in order to identify vulnerabilities and weaknesses that the system might not be aware of. It is used to test the system's defenses and find out if it can withstand a range of attacks designed to mimic those of real attackers. By exposing the vulnerabilities in the system, it can help improve its resilience and robustness against potential attacks."

---

### q07 — ISTQB — "What is Concept drift testing?"

Concept correctness: FAIL
  - matched: ['drift']
  - missing: ['data distribution', 'model degradation', 'monitoring', 'retraining']
  - count: 1

Terminology coverage: PASS
  - present: ['concept drift']
  - absent: []

Hallucination absence: FAIL
  - banned_found: []
  - topics_matched: []

Answer (first 500 chars):
  "Based on the context, Concept drift testing is a type of test that focuses on detecting changes in the requirements and user interactions that are not reflected in the original specification. It's a technique that is used when there is a gap between the requirements document and the actual software, causing changes in the functionality. Concept drift testing is an important aspect of test automation, as it helps ensure that the software meets the required functionality and user interactions, eve"

---

### q08 — Abstain trigger — "How do I bake sourdough bread?"

Abstain trigger: PASS
  - matches_abstain: True
  - actual_first_50_chars: "I don't have enough information from the available"

---

### q09 — Abstain trigger — "What were last night's Vancouver Canucks scores?"

Abstain trigger: PASS
  - matches_abstain: True
  - actual_first_50_chars: "I don't have enough information from the available"

---

### q10 — Abstain trigger — "What's the recommended salary for a QA engineer in Toronto?"

Abstain trigger: PASS
  - matches_abstain: True
  - actual_first_50_chars: "I don't have enough information from the available"

---

## Observations

Overall pass rate: 3/10 (30%). All three passes came from abstain triggers; zero ISTQB questions passed all three scoring dimensions.

### Abstain logic works as designed

Three out of three unrelated questions (sourdough bread, Vancouver Canucks scores, Toronto QA salaries) correctly returned the abstain message without triggering an LLM call. Top similarity scores for these questions stayed well below the 0.35 threshold, confirming the threshold is calibrated correctly for "totally unrelated to ISTQB" content.

### Terminology coverage versus concept correctness

A clear pattern emerged across the 7 ISTQB questions:

| Dimension | Pass rate |
|-----------|-----------|
| Terminology coverage | 6/7 |
| Concept correctness | 0/7 |
| Hallucination absence | 0/7 |

`smollm2-360m` reliably reproduces the canonical topic name when it appears in the question (the term "metamorphic testing", "A/B testing", "test oracle", etc.) but consistently fails to produce the supporting concepts that define what the term actually means. This is the most damaging failure mode for a domain-specialized RAG system: confident answers that sound authoritative because they use the right vocabulary, but invent the underlying explanations.

### Specific failure patterns

**Q06 — Adversarial testing.** The model conflated adversarial testing with security testing, a related but distinct concept. The harness caught this via the `banned_phrases` check. Real adversarial testing in ML focuses on adversarial examples, perturbations, and model robustness — not penetration testing or vulnerability scanning.

**Q04 — ML model validation.** The malformed question grammar ("How to validation the ML model?") dropped retrieval similarity below the 0.35 threshold, triggering the abstain message instead of an answer attempt. This suggests the embedding model (`all-MiniLM-L6-v2`) is sensitive to question phrasing quality. A grammatically correct version of the same question might have scored above threshold and produced an answer (likely also wrong, but visible).

### Non-determinism

Across multiple runs of the same questions during development, `smollm2-360m` produced materially different wrong answers each time. This is expected behavior for an LLM with default sampling, but worth noting: even repeated evaluation runs against the same model and corpus will produce varying RESULTS.md outputs. The pattern of failures is stable; the specific wrong content is not.

### Implications for model upgrade

The pass rate for ISTQB questions is bounded above by `smollm2-360m`'s capability to follow structured instructions and produce grounded technical content. A 3B+ instruct model (e.g., Qwen2.5-3B-Instruct, Phi-3.5-Mini) would likely improve concept correctness substantially because:

1. Larger models follow multi-part format contracts more reliably (the five-part response structure is currently ignored).
2. Larger models are less prone to topic-name hallucination — they're more likely to produce wrong-but-related content rather than confidently wrong content.
3. The 32K context window of modern 3B models removes the `top_k=2` workaround, restoring full retrieval recall.

The Step 10 baseline (3/10 pass rate) is the comparison point against which a future model upgrade can be measured. Re-running this same harness against a larger model is the correct next experiment.

### What this evaluation does NOT measure

Keyword-matching scoring is intentionally simple. It can detect "vocabulary right, concept wrong" (the dominant failure mode here), but cannot evaluate:

- Subtle semantic drift where the answer is mostly right but mischaracterizes nuance
- Citation accuracy beyond presence (does the cited page actually contain the cited claim?)
- Coherence of multi-part structured answers
- Practical usefulness of the suggested test cases

A future LLM-as-judge approach could score these dimensions, with the tradeoff of introducing another LLM dependency in the evaluation loop.
