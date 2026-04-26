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

Overall pass rate: 3/10 (30%). Results reflect smollm2-360m capabilities at evaluation time. Failures are evidence of model limitations, not implementation errors.
