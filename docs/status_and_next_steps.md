# Project Status and Next Steps

**As of:** 12 October 2026 · **Deadline:** 18 October 2026, 11:59 PM (6 days left)
**Submit:** Kaggle notebook link, GitHub repo link, report PDF.

## Summary

The data stages are finished: the audit and all of cleaning (Steps 1 and 2) are done, and the cleaned base table `clean_df` now exists. The three data-engineering questions (Step 3) are also answered in notebook section 4. Feature engineering (Step 4) is done in notebook section 5 and produces `model_df`. Nothing from modeling, ablation, XAI, inference or the report has been started, and the project is about three days behind the original timeline.

M2, M3 and M4 are no longer blocked. The cleaning cells are in the working copy of the notebook but are **not committed or pushed yet**, and decisions DEC-009 and DEC-010 still need team approval.

---

## 1. Where we stand

All work is in [formula-1.ipynb](../formula-1.ipynb) (52 cells). The last commit on `main` was on 9 October; Tasks 5–8 were added on 12 October and are uncommitted.

| Step | Owner | Status | Notes |
| :--- | :--- | :--- | :--- |
| Shared components (config, plot helper, leakage guard, data contract) | All | Done | Notebook section 1 |
| 1. Audit: inventory, keys, foreign keys, "before" EDA | M1 | Done | Six `before_eda_*` figures in [figures/](../figures/) |
| 2. Cleaning, Task 4: typing and sentinels | M1 | Done | |
| 2. Cleaning, Task 5: scope filter and non-starters | M1 | Done, uncommitted | DEC-009 and DEC-010 proposed |
| 2. Cleaning, Task 6: shared-drive deduplication | M1 | Done, uncommitted | |
| 2. Cleaning, Task 7: base table and `podium` target | M1 | Done, uncommitted | `clean_df` passes the data contract |
| 2. Cleaning, Task 8: "after" EDA | M1 | Done, uncommitted | Five `after_eda_*` figures |
| 3. Data-engineering questions Q1–Q3 | M2 | Done, uncommitted | Notebook section 4, four `de_q*` figures, DEC-011 to DEC-014 (DEC-012 proposed) |
| 4. Feature engineering | M3 | Done, uncommitted | Notebook section 5: `model_df` with 21 features, two leakage tests, five `feat_*` figures, DEC-015 to DEC-018 proposed |
| 5. Split and preprocessing experiments | M3 | Not started | |
| 6. Modeling (baselines, two ML models, shallow NN) | M4 | Not started | |
| 7. Ablation | M3 | Not started | |
| 8. XAI | M2 | Not started | |
| 9. Inference function | M4 | Not started | |
| 10. Kaggle Run All and report PDF | All | Not started | |

Decisions DEC-001 to DEC-010 are logged in [decision_log.md](decision_log.md). The task-level spec for Steps 1 and 2 is in [Step 1,2 plan.md](Step%201,2%20plan.md).

### What cleaning produced

| Stage | Rows removed | Rows left |
| :--- | ---: | ---: |
| Raw `results` | | 26,759 |
| Drop Indianapolis 500, 1950–1960 (11 races) | 405 | 26,354 |
| Drop non-starters (DEC-009) | 1,715 | 24,639 |
| Deduplicate shared drives (DEC-008, all in 1950–1964) | 64 | 24,575 |

| Split | Rows | Races | Podiums | Rate |
| :--- | ---: | ---: | ---: | ---: |
| Train (≤ 2019) | 22,448 | 1,007 | 3,038 | 13.53% |
| Validation (2020–2021) | 775 | 39 | 117 | 15.10% |
| Test (≥ 2022) | 1,352 | 68 | 204 | 15.09% |

Hand-off objects in the notebook:

- `clean_df`: one row per `(raceId, driverId)`, with race and circuit context, `pit_start` and `podium`. It still carries the outcome columns for M2's analysis; they stay blacklisted as features.
- `qualifying_clean`: `position` renamed to `quali_position`, `q1`–`q3` in seconds.
- `sprint_clean`: all non-key columns prefixed with `sprint_`.

Two decisions are logged as **Proposed** and need a team yes or no:

- **DEC-009, non-starters.** A row is dropped when it has zero laps *and* is either labelled DNQ, DNPQ or withdrawn, or never held a grid slot. The zero-laps condition matters: 24 rows labelled `Withdrew` or `Did not qualify` actually raced (one finished 4th), so filtering on the label alone would delete real starters.
- **DEC-010, pit-lane starts.** The 72 remaining `grid = 0` rows (2015–2024) get `pit_start = 1` and `grid` set to one slot behind the last car on that race's grid.

Fifteen races from 1950–1960 keep four or five podium rows, because two drivers were classified in the same podium car. They are kept on purpose.

---

## 2. Problems in what is already committed

1. **Fixed: missing outputs.** Cells from Task 3 onward now carry outputs from a clean top-to-bottom run (Python 3.14, pandas 2.3.3). Cells before Task 3 keep their earlier outputs.
2. **Fixed: pandas 3 failure.** Cell 32 asserted `dtype == object`, which is false on pandas 3 because strings load as `str`. The check now uses `pd.api.types`, and the whole notebook runs clean on both pandas 2.3.3 and 3.0.6. Kaggle itself is still untested.
3. **The repo has no `requirements.txt`, README or `.gitignore`.** Nobody can tell which pandas version the notebook expects. Add a pinned `requirements.txt` at least.
4. **Machine-specific paths.** `resolve_dataset_dir()` in cell 2 has a `d:/GUC/...` fallback, and [Step 1,2 plan.md](Step%201,2%20plan.md) links use `file:///d:/...`, which are broken for everyone else. Remove the fallback and make the links relative.
5. **The docs quote three numbers that the data does not support.** Fix them before they reach the report:

   | Docs say | Data says |
   | :--- | :--- |
   | 176 duplicate rows to remove | 176 rows are *involved* in duplicates (85 groups). Only 91 are surplus, and 64 remain after Task 5. |
   | Podium base rate ≈ 15% | 12.69% raw, 13.67% after cleaning. It is 15% only in the modern 20-car era. |
   | Qualifying data from 1994 onward | Present from 1994 but covers only 1–10 of 16–17 races per season in 1996–2002. Complete from 2003. |

---

## 3. Next steps

### Now

1. Review and commit the Task 5–8 cells, the five new figures and the decision-log changes, then push so the others can pull `clean_df`.
2. Approve or change DEC-009 and DEC-010. Changing either one changes the row counts above.
3. Fix the remaining items in Section 2 (`requirements.txt`, machine-specific paths, the three wrong numbers in the docs).

### Rest of the week

The original plan had feature freeze today. This schedule compresses the remaining work into five days and keeps Sunday as buffer.

| Date | M1 Data | M2 Analytics | M3 Features | M4 Modeling |
| :--- | :--- | :--- | :--- | :--- |
| **Mon 12** | Commit and push Tasks 5–8, fixes from Section 2, DEC-009/010 approval | Status → category and nationality → country mappings | Lagged-standings and rolling-form helpers on raw tables | Metric and evaluation harness |
| **Tue 13** | Support M2 and M3 on `clean_df` | Q1 and Q2 | Features v1 (grid, qualifying, form) | `grid ≤ 3` rule and logistic regression on a grid-only table |
| **Wed 14** | Report skeleton | Q3, write up Q1–Q3 | **Feature freeze**, leakage unit test, split | Random forest, gradient boosting |
| **Thu 15** | Report: data sections | XAI on current best model | Pipeline and the two preprocessing-order experiments | Shallow NN, tuning, thresholds |
| **Fri 16** | First Kaggle Run All | XAI final | Ablation by `FEATURE_GROUPS` | Comparison table, `predict_podium()` |
| **Sat 17** | **Code freeze**, final Kaggle Run All, report PDF | Report figures | Report: features and ablation | Report: models |
| **Sun 18** | Rehearsal in the morning, then submit | | | |


---

## 4. Risks to plan around

- **Kaggle environment.** The notebook has never been run on Kaggle. The first Run All should be on Friday at the latest. The dataset on Kaggle may also be a newer version than the local `archive/`, which would shift the row counts.
- **Small validation set.** 775 rows with 117 podiums makes tuning and threshold choices noisy. Prefer simple models and state this limitation in the report.
- **Thin qualifying coverage before 2003.** This affects Q1 (the "pre-2014" era is effectively 2003–2013 for qualifying-based front rows) and the training-window experiment in Step 5.
- **One qualifying outlier.** 1995 Japanese GP (`raceId` 255, `driverId` 87) has `q1 = "16:42.640"`, which parses to 1,002.64 s. Cap gap-to-pole or set this value to `NaN`.
- **Sprint features are optional.** Cut them first if time runs out.
- **Individual defense.** Every member has to defend every stage. Do not drop the Sunday rehearsal.
