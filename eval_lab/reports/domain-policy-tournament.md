# Domain policy tournament

Domain scoring compares candidate policy engines to an independent sales-ops contract. It does not simulate Haiku instruction-following.

Independent oracle cases: 3000
Metamorphic cases: 12000
Pairwise cases: 1000
Total independent cases: 16000
Discriminating cases: 1620

recommended_semantic_policy: candidate-b-ledger
reserve_policy_1: production-f9e5400
reserve_policy_2: candidate-a-conservative

## Ranking

1. candidate-b-ledger false_action=0.0000 f1=1.0000 wait_boundary=1.0000 disposition=1.0000
2. production-f9e5400 false_action=0.0000 f1=1.0000 wait_boundary=1.0000 disposition=1.0000
3. candidate-a-conservative false_action=0.0000 f1=0.8005 wait_boundary=0.9200 disposition=0.8092
4. candidate-c-assertive false_action=0.0067 f1=0.9942 wait_boundary=0.8400 disposition=0.9933

## Metrics

### candidate-b-ledger
- disposition_accuracy: 1.0
- action_precision: 1.0
- action_recall: 1.0
- action_f1: 1.0
- false_action_rate: 0.0
- missed_action_rate: 0.0
- meeting_accuracy: 1.0
- record_accuracy: 1.0
- monitor_accuracy: 1.0
- constraint_accuracy: 1.0
- catastrophic_logic_failures: 0
- boundary_accuracy_external_wait: 1.0
- boundary_accuracy_record: 1.0
- boundary_accuracy_contact: 1.0
- pairwise_bias_pass_rate: 1.0
- invariant_pass_rate: 1.0
- controlled_flip_pass_rate: 0.9866666666666667

### production-f9e5400
- disposition_accuracy: 1.0
- action_precision: 1.0
- action_recall: 1.0
- action_f1: 1.0
- false_action_rate: 0.0
- missed_action_rate: 0.0
- meeting_accuracy: 1.0
- record_accuracy: 1.0
- monitor_accuracy: 1.0
- constraint_accuracy: 1.0
- catastrophic_logic_failures: 0
- boundary_accuracy_external_wait: 1.0
- boundary_accuracy_record: 1.0
- boundary_accuracy_contact: 1.0
- pairwise_bias_pass_rate: 1.0
- invariant_pass_rate: 1.0
- controlled_flip_pass_rate: 0.9866666666666667

### candidate-a-conservative
- disposition_accuracy: 0.8091666666666667
- action_precision: 1.0
- action_recall: 0.6673928830791576
- action_f1: 0.8005226480836237
- false_action_rate: 0.0
- missed_action_rate: 0.19083333333333333
- meeting_accuracy: 1.0
- record_accuracy: 1.0
- monitor_accuracy: 0.5980340530103563
- constraint_accuracy: 1.0
- catastrophic_logic_failures: 0
- boundary_accuracy_external_wait: 0.92
- boundary_accuracy_record: 1.0
- boundary_accuracy_contact: 1.0
- pairwise_bias_pass_rate: 1.0
- invariant_pass_rate: 0.4866666666666667
- controlled_flip_pass_rate: 0.48

### candidate-c-assertive
- disposition_accuracy: 0.9933333333333333
- action_precision: 0.9885139985642498
- action_recall: 1.0
- action_f1: 0.9942238267148015
- false_action_rate: 0.006666666666666667
- missed_action_rate: 0.0
- meeting_accuracy: 1.0
- record_accuracy: 1.0
- monitor_accuracy: 0.9765189316113884
- constraint_accuracy: 1.0
- catastrophic_logic_failures: 0
- boundary_accuracy_external_wait: 0.84
- boundary_accuracy_record: 1.0
- boundary_accuracy_contact: 1.0
- pairwise_bias_pass_rate: 1.0
- invariant_pass_rate: 0.9733333333333334
- controlled_flip_pass_rate: 0.98
