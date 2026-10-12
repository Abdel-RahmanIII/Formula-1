# Next Steps Plan — 12 to 18 October

> **Status on 12 Oct:** Step 1 (audit) is done. Step 2 is done up to Task 4. Tasks 5–8 and Steps 3–10 are not started.
> **Deadline:** 18 October 2026, 11:59 PM. The original timeline had cleaning finished on 10 Oct and feature freeze on 12 Oct, so the schedule below is compressed.

---

## 1. Task 4 verification result

The whole notebook was executed top to bottom on a clean copy (Python 3.14, pandas 2.3.3). Every cell ran without error, including the Task 3 and Task 4 cells that were committed without outputs.

| Check | Result |
| :--- | :--- |
| All Task 4 assertions (copies, parser unit test, Q2/Q3 null counts, sentinels, immutability) | Pass |
| Values lost in conversion (raw non-null became `NaN`) across all 15 converted columns | 0 |
| `raw_dataframes` identical to a fresh load of the CSVs after Task 4 | Yes |
| `pit_stops.duration` agrees with `milliseconds / 1000` | Yes, all 11,371 rows |
| `grid`, `positionOrder` and the ID columns are `int64` with no nulls | Yes |

Two things to fix or carry forward:

1. **The notebook fails on pandas 3.x.** Cell 32 asserts `raw_dataframes["races"]["date"].dtype == object`. pandas 3 loads strings as `str`, not `object`, so the assertion fails with "was mutated!" even though nothing was mutated. Check which pandas version Kaggle runs, and make the check version-proof either way:
   ```python
   assert not pd.api.types.is_datetime64_any_dtype(raw_dataframes["races"]["date"])
   assert not pd.api.types.is_float_dtype(raw_dataframes["qualifying"]["q1"])
   ```
2. **One qualifying time is an outlier.** 1995 Japanese GP, `driverId` 87, `q1 = "16:42.640"` parses correctly to 1002.64 s. It is a real value in the source, but it will distort any gap-to-pole feature. M3 should cap the gap or set this one to `NaN`.

---

## 2. Finish Step 2 (today, 12 Oct) — blocks everyone

Row counts below were measured on the current data, so the notebook output can be checked against them.

| Stage | Rows removed | Rows left |
| :--- | ---: | ---: |
| Raw `results` | — | 26,759 |
| Task 5a: drop Indianapolis 500, 1950–1960 (11 races) | 405 | 26,354 |
| Task 5b: drop non-starters (rule below) | 1,724 | 24,630 |
| Task 5c: drop pre-2010 `grid = 0` leftovers | 14 | 24,616 |
| Task 6: shared-drive deduplication (1950–1964) | 64 | 24,552 |

### Task 5 — decisions that need a decision-log entry

- **Non-starter rule (proposed DEC-009).** Drop a row if `status` is one of `Did not qualify`, `Did not prequalify`, `Withdrew`, `Did not start`, or if `positionText` is `F` or `W`. This removes 1,724 rows and no podium finishers.
  - `grid > 0` alone is not enough: 153 rows with a grid slot are still marked `F` or `W`.
  - Do **not** drop `positionText` `N` (not classified), `D` (disqualified) or `R` (retired). Those drivers started the race.
- **Pit-lane starts (proposed DEC-010).** After the non-starter rule, 87 rows still have `grid = 0`.
  - 73 are from 2010 onward and are real pit-lane starts. Set `pit_start = 1` and recode `grid` to the back of that race's grid.
  - 14 are from 1984–1997, completed zero laps, and are almost all excluded or disqualified entries. Drop them as non-starters.

### Task 6 — deduplication

- Apply the DEC-008 rule as written.
- Correct the count in the docs: "176 duplicates" is the number of rows involved. The surplus is 91 rows in the raw data and 64 after Task 5. `validate_data_contract()` will report 91 on raw data, not 176.
- In 60 duplicate groups both rows have `grid > 0`, so the "car the driver started in" step does not decide. `positionOrder` does. Say so in the log.

### Task 7 — base table

- Join `results` → `races` → `circuits`, derive `podium`, run `validate_data_contract()`.
- Expect 15 races with more than three podium rows (13 with four, 2 with five). These are shared drives where both drivers were credited. Keep them and note it.
- **Podium base rate is about 13.7% after cleaning** (12.7% raw), not the ~15% quoted in the docs. By split: train 22,427 rows at 13.5%, validation 774 at 15.1%, test 1,351 at 15.1%.
- Hand off `clean_df` to M2, M3 and M4 as soon as this passes. Do not wait for Task 8.

---

## 3. Compressed schedule

| Date | M1 Data | M2 Analytics | M3 Features | M4 Modeling |
| :--- | :--- | :--- | :--- | :--- |
| **Mon 12** | Tasks 5–7, pandas fix, DEC-009/010, hand off `clean_df` | Status → category and nationality → country mappings | Lagged standings and rolling-form helpers on raw tables | Metric and evaluation harness |
| **Tue 13** | Task 8 "after" EDA | Q1 and Q2 | Features v1 (grid, qualifying, form) | Grid ≤ 3 rule and logistic regression on grid-only table |
| **Wed 14** | Support, report skeleton | Q3, write up Q1–Q3 | **Feature freeze**, leakage unit test, split | Random forest, gradient boosting |
| **Thu 15** | Report: data sections | XAI on current best model | Pipeline and the two preprocessing-order experiments | Shallow NN, tuning, thresholds |
| **Fri 16** | Kaggle Run All dry run | XAI final | Ablation by `FEATURE_GROUPS` | Comparison table, `predict_podium()` |
| **Sat 17** | **Code freeze**, final Kaggle Run All, report PDF | Report figures | Report: features and ablation | Report: models |
| **Sun 18** | Rehearsal in the morning, then submit | | | |

---

## 4. Things that will affect later steps

- **Qualifying coverage is thinner than the docs say.** Data starts in 1994 but covers only 6%–59% of races per season from 1996 to 2002. Coverage is complete from 2003. This affects DE Q1 (the pre-2014 era is effectively 2003–2013 for qualifying-based front rows) and the training-window experiment in Step 5.
- **The validation set is small** (774 rows, about 117 podiums). Tuning and threshold choices on it will be noisy, so prefer simple models and report that limitation.
- **Sprint features are marked optional in the plan.** Drop them first if time runs out.
- **Run on Kaggle early.** The first full Run All there should happen by 16 Oct, not 17 Oct, because of the pandas version risk in Section 1.
