# Project Status and Next Steps

**As of:** 13 October 2026 · **Deadline:** 18 October 2026, 11:59 PM (5 days left)
**Submit:** Kaggle notebook link, GitHub repo link, report PDF.

## Summary

Steps 1 to 9 of the plan are done (Tasks 1–38 in the notebook), and most of Step 10 is in place: the limitations section of the notebook, the repo setup and a draft of the report PDF. What is left needs the team: the Kaggle Run All, the team names and Kaggle link in the report, the decision approvals and the rehearsal.

Against the plan's timeline the project is ahead: integration and the report were planned for 15–16 October.

The notebook has still never been run on Kaggle.

---

## 1. Where we stand

All work is in [formula-1.ipynb](../formula-1.ipynb). A walk-through of every task and figure is in [notebook_guide.md](notebook_guide.md).

| Step | Owner | Tasks | Notebook section | Status | Decisions |
| :--- | :--- | :--- | :--- | :--- | :--- |
| Shared components | All | | 1 | Done | DEC-001 to DEC-007 |
| 1. Data audit | M1 | 1–3 | 2 | Done | |
| 2. Data cleaning | M1 | 4–8 | 3 | Done | DEC-008 to DEC-010 |
| 3. Data-engineering questions | M2 | 9–11 | 4 | Done | DEC-011 to DEC-014 |
| 4. Feature engineering | M3 | 12–14 | 5 | Done | DEC-015 to DEC-018 |
| 5. Split and preprocessing | M3 | 15–20 | 6 | Done | DEC-019 to DEC-021 |
| 6. Modeling | M4 | 21–28 | 7 | Done | DEC-022 to DEC-030 |
| 7. Ablation | M3 | 29–31 | 8 | Done | DEC-031 |
| 8. Explainable AI | M2 | 32–35 | 9 | Done | DEC-032 |
| 9. Inference function | M4 | 36–38 | 10 | Done | DEC-033 |
| 10. Limitations and future work | All | | 11 | Done | |
| 10. Repo setup (`README.md`, `requirements.txt`, `.gitignore`) | M1 | | | Done | |
| 10. Report PDF | All | | | Draft in [report/](../report/); team names and Kaggle link missing | |
| 10. Kaggle Run All | M1 | | | **Not started** | |
| 10. Rehearsal | All | | | 17 October | |

There are 38 figures in [figures/](../figures/): 11 from the audit and cleaning, 4 from the data-engineering questions, 5 from features, 3 from preprocessing, 5 from modeling, 2 from ablation, 6 from XAI and 2 from inference.

### Headline results

| Result | Number |
| :--- | :--- |
| Selected model | LightGBM (DEC-029) |
| PR-AUC, validation / test | 0.743 / 0.709 |
| Grid ≤ 3 rule, validation / test | 0.648 / 0.647 |
| Logistic regression, validation / test | 0.728 / 0.711 |
| LightGBM test F1 at its tuned threshold | 0.689 (grid rule 0.649) |

- **The features are worth about 0.06 PR-AUC over the grid rule; model complexity adds nothing measurable.** On test, the untuned logistic regression is level with the tuned models.
- **Ablation (Step 7):** no single feature group is significant, because the groups overlap. Removed as blocks: starting position −0.089 validation / −0.123 test, past results −0.061 / −0.042, context 0.000.
- **XAI (Step 8):** `grid` carries 41% of SHAP magnitude; four of the 21 features are never used by the model. SHAP is reliable; LIME fails on low-score rows.
- **Inference (Step 9):** `predict_podium()` rebuilds the features with the training code and reproduces the stored features and scores for 36 held-out rows. The raw score is not a probability (DEC-027), so the function also returns a calibrated one: on test the mean probability is 0.161 against a podium rate of 0.151.

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

## 2. Open problems

1. **Nineteen of the 33 decisions are still "Proposed"** in [decision_log.md](decision_log.md): DEC-009, 010, 012, 015–023, 025–027, 029, and the three new ones, DEC-031 to DEC-033. The team needs to approve or change them. DEC-009 and DEC-010 come first, because changing either changes the row counts above.
2. **The notebook has never been run on Kaggle.** It needs `lightgbm`, `tensorflow`/`keras`, `shap` and `lime`; the steps are in the [README](../README.md). The Kaggle dataset may also be a newer version than the local `archive/`, which would shift the row counts and every number quoted in the notebook's text and in the report.
3. **The report is a draft.** [report/report.md](../report/report.md) still has placeholders for the team names and the Kaggle link. Rebuild the PDF with `python report/build_report.py` after editing.
4. **Older docs quote numbers the data does not support.** Use the notebook's numbers in the report:

   | Older docs say | Data says |
   | :--- | :--- |
   | 176 duplicate rows to remove | 176 rows are *involved* in duplicates (85 groups). Only 91 are surplus, and 64 remain after Task 5. |
   | Podium base rate ≈ 15% | 12.69% raw, 13.67% after cleaning. It is 15% only in the modern 20-car era. |
   | Qualifying data from 1994 onward | Present from 1994 but covers only 1–10 of 16–17 races per season in 1996–2002. Complete from 2003. |

---

## 3. Next steps

### Now

1. M1 does the first Kaggle Run All. Doing it now leaves time to fix environment problems. If any number changes, the notebook text and the report have to be checked against the new outputs.
2. Fill in the team names and the Kaggle link in [report/report.md](../report/report.md) and rebuild the PDF.
3. Each owner reads the step written for them (M3: Step 7, M2: Step 8, M4: Step 9) and its decision, since they will have to defend it. Everyone reads the report.
4. Approve or change the decisions still marked "Proposed".

### Rest of the week (proposed)

| Date | M1 Data | M2 Analytics | M3 Features | M4 Modeling |
| :--- | :--- | :--- | :--- | :--- |
| **Tue 13** | First Kaggle Run All | Review Step 8 and DEC-032 | Review Step 7 and DEC-031 | Review Step 9 and DEC-033 |
| **Wed 14** | Review report sections 1–2; team names and Kaggle link | Review report sections 3 and 8 | Review report sections 4, 5 and 7 | Review report sections 6 and 9 |
| **Thu 15** | Decision approvals (all) | Decision approvals (all) | Decision approvals (all) | Decision approvals (all) |
| **Fri 16** | **Code freeze**, final Kaggle Run All, check numbers | Report review | Report review | Report review |
| **Sat 17** | Final report PDF | Rehearsal: 10 minutes per member, every member questioned on every stage | | |
| **Sun 18** | Buffer, then submit | | | |

---

## 4. Risks to plan around

- **Kaggle environment.** The largest remaining risk, because it is untested and everything is submitted through it.
- **Numbers in the text are typed, not computed.** The result paragraphs in the notebook quote numbers from the local run. If the Kaggle data or library versions shift the results, those paragraphs have to be checked against the new outputs.
- **Small validation and test sets.** 775 validation rows (117 podiums, 39 races) and 68 test races. Differences below about 0.02 PR-AUC are noise; state this in the report.
- **Score vs. probability.** `predict_podium()` returns both. The raw score overstates the chance of a podium by about a factor of two; only the calibrated value may be called a probability in the report.
- **The test seasons have been used.** Any further change to the model or threshold that is judged on the test scores would turn them into a second validation set.
- **Individual defense.** Every member has to defend every stage. Do not drop the rehearsal.
