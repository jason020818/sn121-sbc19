# Free tournament summary

The policy engine verifies LOGIC. It does not simulate Haiku instruction-following or official SN121 graders. Logic verification is strong evidence of policy correctness; it does not measure stochastic instruction-following. A live SN121 submission remains the only official validator sample.

Base holdouts: 1200
Metamorphic cases: 4800
Pairwise checks: 1000

production_recommendation: candidate-c-minimal
reserve_1: candidate-b-ledger
reserve_2: candidate-a-conservative

SKILL.md was not modified. results/** was not modified. No SN121 submission was made.

## Ranking

1. candidate-c-minimal catastrophic=0 invariant_viol=0 constraint_viol=0 action_f1=1.000000 disposition=1.000000 flip=1.000000 words=408
2. candidate-b-ledger catastrophic=0 invariant_viol=0 constraint_viol=0 action_f1=1.000000 disposition=1.000000 flip=1.000000 words=510
3. candidate-a-conservative catastrophic=0 invariant_viol=0 constraint_viol=0 action_f1=1.000000 disposition=1.000000 flip=1.000000 words=558
4. production-f9e5400 catastrophic=0 invariant_viol=0 constraint_viol=0 action_f1=1.000000 disposition=1.000000 flip=1.000000 words=1170

## Behavioral metrics

### candidate-c-minimal
- disposition_accuracy: 1.0
- action_precision: 1.0
- action_recall: 1.0
- action_f1: 1.0
- meeting_accuracy: 1.0
- monitor_accuracy: 1.0
- record_accuracy: 1.0
- constraint_accuracy: 1.0
- invariant_pass_rate: 1.0
- controlled_flip_pass_rate: 1.0
- pairwise_bias_pass_rate: 1.0
- candidate_policy_alignment_pass: True
- catastrophic_logic_failures: 0
- generalization_proxy: 1.0

### candidate-b-ledger
- disposition_accuracy: 1.0
- action_precision: 1.0
- action_recall: 1.0
- action_f1: 1.0
- meeting_accuracy: 1.0
- monitor_accuracy: 1.0
- record_accuracy: 1.0
- constraint_accuracy: 1.0
- invariant_pass_rate: 1.0
- controlled_flip_pass_rate: 1.0
- pairwise_bias_pass_rate: 1.0
- candidate_policy_alignment_pass: True
- catastrophic_logic_failures: 0
- generalization_proxy: 1.0

### candidate-a-conservative
- disposition_accuracy: 1.0
- action_precision: 1.0
- action_recall: 1.0
- action_f1: 1.0
- meeting_accuracy: 1.0
- monitor_accuracy: 1.0
- record_accuracy: 1.0
- constraint_accuracy: 1.0
- invariant_pass_rate: 1.0
- controlled_flip_pass_rate: 1.0
- pairwise_bias_pass_rate: 1.0
- candidate_policy_alignment_pass: True
- catastrophic_logic_failures: 0
- generalization_proxy: 1.0

### production-f9e5400
- disposition_accuracy: 1.0
- action_precision: 1.0
- action_recall: 1.0
- action_f1: 1.0
- meeting_accuracy: 1.0
- monitor_accuracy: 1.0
- record_accuracy: 1.0
- constraint_accuracy: 1.0
- invariant_pass_rate: 1.0
- controlled_flip_pass_rate: 1.0
- pairwise_bias_pass_rate: 1.0
- candidate_policy_alignment_pass: True
- catastrophic_logic_failures: 0
- generalization_proxy: 1.0

## Coverage minima

- book_size_min: 171
- action_count_min: 200
- calendar_min: 240
- ownership_min: 80
- data_min: 133
- constraint_min: 200
- commercial_min: 133

## Confirmations

- zero network calls
- zero paid OpenRouter calls
- no SN121 submission

