# Metrics

### all (n=200)

| system | n | intent_acc | intent_macro_f1 | esc_accuracy | esc_recall | esc_precision | auto_rate | unsafe_auto | send_ready | helpful | grounded | tone | safe_automation | auto_send_ready |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| trivial | 200 | 0.305 | 0.058 | 0.430 | 1.000 | 0.430 | 0.000 | 0 | 0.410 | 2.975 | 4.185 | 4.030 | 0.000 | - |
| simple | 200 | 0.655 | 0.583 | 0.800 | 0.942 | 0.698 | 0.420 | 5 | 0.425 | 2.815 | 3.595 | 3.905 | 0.150 | 0.381 |
| agent_noretrieval | 200 | 0.855 | 0.848 | 0.905 | 0.988 | 0.825 | 0.485 | 1 | 0.930 | 4.730 | 4.855 | 4.850 | 0.470 | 0.979 |
| agent_noguard | 200 | 0.905 | 0.900 | 0.910 | 1.000 | 0.827 | 0.480 | 0 | 0.940 | 4.655 | 4.805 | 4.855 | 0.470 | 0.979 |
| agent | 200 | 0.905 | 0.900 | 0.910 | 1.000 | 0.827 | 0.480 | 0 | 0.940 | 4.655 | 4.805 | 4.855 | 0.470 | 0.979 |

### random stratum only (n=150)

| system | n | intent_acc | intent_macro_f1 | esc_accuracy | esc_recall | esc_precision | auto_rate | unsafe_auto | send_ready | helpful | grounded | tone | safe_automation | auto_send_ready |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| trivial | 150 | 0.220 | 0.045 | 0.340 | 1.000 | 0.340 | 0.000 | 0 | 0.320 | 2.640 | 4.053 | 3.887 | 0.000 | - |
| simple | 150 | 0.607 | 0.567 | 0.780 | 0.902 | 0.622 | 0.507 | 5 | 0.420 | 2.747 | 3.547 | 3.893 | 0.180 | 0.382 |
| agent_noretrieval | 150 | 0.827 | 0.837 | 0.893 | 0.980 | 0.769 | 0.567 | 1 | 0.913 | 4.673 | 4.827 | 4.847 | 0.547 | 0.976 |
| agent_noguard | 150 | 0.900 | 0.906 | 0.913 | 1.000 | 0.797 | 0.573 | 0 | 0.927 | 4.593 | 4.760 | 4.847 | 0.560 | 0.977 |
| agent | 150 | 0.900 | 0.906 | 0.913 | 1.000 | 0.797 | 0.573 | 0 | 0.927 | 4.593 | 4.760 | 4.847 | 0.560 | 0.977 |

### Historical SpotifyCares reply (human reference), judged with the same rubric

| scope | send_ready | helpful | grounded | tone | action_ok |
|---|---|---|---|---|---|
| all | 0.680 | 3.79 | 4.13 | 4.38 | 0.845 |
| random | 0.700 | 3.75 | 4.13 | 4.39 | 0.860 |

### Agent: 95% bootstrap CIs (all 200, resampling messages)

- intent_acc: 0.905  CI (0.865, 0.94)
- esc_recall: 1.000  CI (1.0, 1.0)
- safe_automation: 0.470  CI (0.4, 0.545)
- send_ready: 0.940  CI (0.905, 0.97)

### Agent per gold intent

| intent | n | intent_acc | esc_recall | auto_rate | send_ready |
|---|---|---|---|---|---|
| billing_payment | 61 | 0.93 | 1.000 | 0.18 | 0.934 |
| plan_student_family | 12 | 0.92 | 1.000 | 0.17 | 0.833 |
| account_access | 15 | 1.00 | 1.000 | 0.00 | 1.000 |
| account_security | 17 | 1.00 | 1.000 | 0.00 | 0.941 |
| playback_technical | 30 | 0.87 | 1.000 | 0.93 | 0.967 |
| content_availability | 15 | 0.93 | 1.000 | 0.87 | 0.867 |
| feature_feedback | 25 | 0.92 | 1.000 | 0.96 | 1.000 |
| other | 25 | 0.72 | 1.000 | 0.72 | 0.920 |

### Agent intent confusion matrix (rows = gold)

```
                   billing_  plan_stu  account_  account_  playback  content_  feature_  other
gold:billing_paym        57         0         3         0         0         0         1      0
gold:plan_student         1        11         0         0         0         0         0      0
gold:account_acce         0         0        15         0         0         0         0      0
gold:account_secu         0         0         0        17         0         0         0      0
gold:playback_tec         1         0         0         0        26         0         2      1
gold:content_avai         0         0         0         0         0        14         0      1
gold:feature_feed         0         0         0         0         0         2        23      0
gold:other                0         0         1         0         0         2         4     18
```

### LLM judge vs human ratings

Not computed yet: run `python -m scripts.rate`.
