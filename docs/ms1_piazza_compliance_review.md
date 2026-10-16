# MS1 Piazza Compliance Review and Fix Plan

**Purpose.** This review checks every decision in [`formula-1.ipynb`](../formula-1.ipynb) against the instructor answers collected in [`piazza_ms1_q_a_and_decisions_summary.md`](piazza_ms1_q_a_and_decisions_summary.md). It flags each decision that breaks a Piazza ruling or lacks the evidence a ruling asks for, and gives the fix with its edge cases.

**Method.** Each Piazza ruling was compared with the code and outputs of the matching task. Where a decision depends on the data, it was re-checked against the raw CSVs in `archive/`. The counts quoted below come from that check (2026-10-16), not from the notebook text.

**Scope.** Cell numbers are 0-based indices in the notebook as committed at `e3becf9`. Task numbers match the notebook headings.

---

## 1. Summary

| # | Flag | Piazza rule | Severity | Where | Cascade |
| :-- | :--- | :--- | :--- | :--- | :--- |
| F1 | Q3 classes `Puncture`, `Tyre` and `Tyre puncture` as *regulatory/other* | DE Q3: these three are **Mechanical** | **High (wrong answer)** | Task 11 (cells 57, 58), DEC-013 | Q3 only |
| F2 | Q1 reports conversion for **both** grid and qualifying front rows, and drops 1950–2002 because qualifying is missing | DE Q1: **grid only**. Use the entire dataset | **High (wrong answer)** | Task 9 (cells 46–50), DEC-011 | Q1 only |
| F3 | Shared-drive deduplication keeps the best-finishing car, which mixes another driver's grid slot with the result | Combining driver A's pre-race data with driver B's post-race result is **data leakage** | **High (leakage)** | Task 6 (cells 31, 32), DEC-008 | Everything downstream |
| F4 | `W` (withdrawn) rows are removed with no experiment | Removing `W` is allowed **only with an experiment** showing that keeping or removing them gives the same results | **Medium-High (missing evidence)** | Task 5.2 (cell 29), DEC-009 | Everything downstream if the result says keep |
| F5 | The Indianapolis 500 (11 races, 405 rows) is excluded with no experiment | You **must use the entire dataset**. Every decision needs evidence | **Medium (risk)** | Task 5.1 (cell 28), DEC-003 | Everything downstream if the result says keep |
| F6 | Sprint exclusion is justified only by data availability. The leakage question was never answered | Sprint: **explore and decide whether it leaks**, explain, and handle it | **Medium (missing analysis)** | Task 12.7 (cells 72, 73), DEC-016 | Text and one check cell |
| F7 | Report is built from Markdown and printed to PDF through Chrome | Report must be **Word or LaTeX**, exported to PDF | **Medium (confirm with TA)** | `report/build_report.py` | Report only |
| F8 | 15 `E`/`D`/`R` rows are removed using `laps == 0`, a post-race column | `R`, `E` and `D` are post-race outcomes. Every removal needs a justification | **Low** | Task 5.2 (cell 29) | Small |
| F9 | Final model (LightGBM) receives `NaN`. Some imputations in the other models have weak meaning | Leaving nulls can hurt. Experiment and justify | **Low (framing and edge cases)** | Tasks 16, 24, 38 | Optional |
| F10 | Renamed constructors restart their history in the features but are merged in Q3. Neither choice is justified | Constructor renames: depends on the merge. **Justify** | **Low (missing justification)** | Task 12.4, DEC-014 | Optional |

**Compliant decisions** (no action needed beyond citing Piazza in the text) are listed in [Section 4](#4-decisions-that-comply-with-piazza).

**Do the work in this order** (details in [Section 5](#5-implementation-order-and-cascade-checklist)): F1 and F2 first, because they are isolated. Then the cleaning experiments F4 and F5 and the F3 rewrite, followed by one full re-run. F6 to F10 and the report come last.

---

## 2. High-Severity Flags

### F1. Q3: tyre failures are classed as non-mechanical

**Piazza ruling (Farida Helmy).** *"Consider all of them as Mechanical retirements EXCEPT `Refuelling`."*

| Status | Piazza | Notebook (`categorise_status`, cell 58) | Verdict |
| :--- | :--- | :--- | :--- |
| `Puncture` | Mechanical | `REGULATORY_OTHER_STATUSES` | ❌ Wrong |
| `Tyre` | Mechanical | `REGULATORY_OTHER_STATUSES` | ❌ Wrong |
| `Tyre puncture` | Mechanical | `REGULATORY_OTHER_STATUSES` | ❌ Wrong |
| `Fire` | Mechanical | `MECHANICAL_STATUSES` | ✅ |
| `Safety belt` | Mechanical | `MECHANICAL_STATUSES` | ✅ |
| `Refuelling` | Not mechanical | `REGULATORY_OTHER_STATUSES` | ✅ |

The comment in cell 58 (`# tyres and fuel load: no car component failed`) and the category table in the Task 11 markdown (cell 57: "`Puncture`" under regulatory/other) state the rejected reading.

**Impact on the data.** From 2014 on, 11 rows are affected: 7 `Puncture` and 4 `Tyre`, all in 2014–2021 (none in 2022–2024). They belong to Ferrari 2, Red Bull 2, Williams 2, and 1 each for Lotus F1, Mercedes, Racing Point, Sauber and Toro Rosso. The field-wide 2014–2021 mechanical rate should rise from 9.43% to about 9.77%. The top three for 2014–2021 (Lotus F1, Toro Rosso, Renault) should hold, but every rate and the lineage table change. Confirm all of this on the re-run.

**Fix (cell 58).**

```python
REGULATORY_OTHER_STATUSES: Set[str] = {
    # steward and rule decisions
    "Disqualified", "Excluded", "Underweight", "107% Rule", "Did not qualify", "Did not prequalify", "Safety", "Safety concerns",
    # generic labels that give no cause
    "Retired", "Withdrew", "Not classified", "Not restarted", "Handling", "Damage", "Debris",
    # fuel load and refuelling: not mechanical (Piazza ruling on Q3)
    "Out of fuel", "Fuel", "Refuelling", "Fuel rig",
}
MECHANICAL_STATUSES: Set[str] = {
    ...,
    # tyres: mechanical by instructor ruling (Piazza, DE Q3)
    "Puncture", "Tyre", "Tyre puncture",
}

# Instructor ruling on Q3, enforced so that a later edit cannot undo it
PIAZZA_MECHANICAL: Set[str] = {"Puncture", "Tyre", "Tyre puncture", "Fire", "Safety belt"}
PIAZZA_NOT_MECHANICAL: Set[str] = {"Refuelling"}
assert PIAZZA_MECHANICAL <= MECHANICAL_STATUSES, "Piazza: these statuses are mechanical"
assert not (PIAZZA_NOT_MECHANICAL & MECHANICAL_STATUSES), "Piazza: Refuelling is not mechanical"
```

**Edge cases.**
- **`Tyre puncture`** has no rows from 2014 on, but it is a status in `status.csv` and must still be mapped (the `unmapped` assertion covers this).
- **`Fuel rig`** is not in the ruling. It is the refuelling equipment, so keep it with `Refuelling` (not mechanical). Say so in one line.
- **`Out of fuel` and `Fuel`** are also not in the ruling. Keep them as not mechanical and say that the team chose this, by analogy with `Refuelling`.
- **`Engine fire` and `Heat shield fire`** are already mechanical, which matches the ruling on `Fire`.
- **Rewrite the "strict rule" sentence.** "The label must name a failed car component" no longer describes the mapping. Use: *"the label names a failed car component or system; tyre failures, fire and safety-belt failures count as mechanical by instructor ruling; refuelling and fuel-load labels do not."*

**Also update.**
- The Task 11 category table (cell 57).
- The Q3 answer (cell 63): numbers, top and bottom teams, and the lineage paragraph.
- The sensitivity cell 62, which re-runs automatically.
- DEC-013: mark it *Superseded* and add a new entry that cites Piazza.
- The report's Q3 section.

---

### F2. Q1: the answer must use grid position only, and it should cover all seasons

**Piazza ruling (Farida Helmy).** *"What matters in this question is the grid starting position, not the qualifying position. The note is simply a reminder that the two columns do not map 1-to-1."*

**What the notebook does.**
- Cells 46–50 compute the conversion rate under **two** definitions (`front_row_grid`, `front_row_quali`). The ranking tables, the dumbbell chart (two panels) and the Q1 answer report both.
- **DEC-011 limits Q1 to 2003 onward** for one reason: "2003 is the first season where both definitions can be computed on the same races." Grid is the only definition the question needs, and it exists for every season. That removes the reason for the cut. The rule against dropping old eras (Farida Helmy) is also a reason to use the full range.

**Fix (cells 46–50).**

```python
# Task 9.1: front-row starts by grid slot (DEC-011 revised: grid only, per Piazza)
HYBRID_ERA_START: int = 2014
Q1_FIRST_SEASON: int = int(clean_df["year"].min())   # grid exists for every season
Q1_ERAS: List[str] = [f"{Q1_FIRST_SEASON}–{HYBRID_ERA_START - 1}", f"{HYBRID_ERA_START}–{clean_df['year'].max()}"]

q1_df = clean_df[GRAIN + ["year", "circuitId", "circuit_name", "grid", "pit_start", TARGET_COLUMN]].copy()
q1_df["era"] = np.where(q1_df["year"] >= HYBRID_ERA_START, Q1_ERAS[1], Q1_ERAS[0])
q1_df["front_row"] = q1_df["grid"].isin([1, 2]) & q1_df["pit_start"].eq(0)
```

- Remove `FRONT_ROW_DEFINITIONS`, the qualifying panel of the chart, the "grid vs. qualifying" table and the between-definition Spearman check.
- Keep **one sentence** at most: "Grid, not qualifying, is used because penalties move cars between the two." The instructor called that note a reminder, not a task.
- Rank circuits on the grid definition only.

**Edge cases.**
- **Front rows were 3 or 4 cars wide until the early 1970s.** Keep the definition "grid slot 1 or 2", state it, and add one line that this compares the same *slots* across eras, not the same physical row. If the team wants a sensitivity check, also report "grid ≤ 3", but do not make it the main answer.
- **Pit-lane starts recoded to the back (DEC-010)** can never reach grid 1–2. The `pit_start.eq(0)` guard documents this rather than relying on it.
- **Races with fewer than two front-row rows.** These occur when a front-row car was removed as a non-starter (for example the 2005 United States GP) or after F3 removes shared drives. Keep listing them under "Missing values".
- **Circuits renamed or rebuilt** keep their `circuitId`. With a pre-hybrid era back to 1950, more circuits pass `MIN_FRONT_ROW_STARTS = 10`. Report how many circuits pass.
- **Circuit layout changes over 60 years.** Mention this as a limit. An optional sensitivity check: also show a 2003–2013 window of equal length, but only as a secondary table.
- **Shared-drive rows of the 1950s** now enter Q1. Apply F3 first so that a car's front-row slot is not credited to two drivers.

**Also update.**
- The Q1 answer (cell 50).
- The Joins/Grain/Missing table: "Seasons before 2003 are left out" must go.
- Figure `de_q1_front_row_conversion`.
- DEC-011: mark it *Superseded*.
- The report's Q1 section and Figure 4 caption.

---

### F3. Shared-drive deduplication leaks another driver's data into the kept row

**Piazza rulings.**
- *Salma Kishk:* combining the pre-race info of the driver who started with the post-race result of the driver who took over **is data leakage**.
- *Mayar Osama:* using the car the driver **finished in** does not break the cutoff.
- *Farida Helmy and Salma Kishk:* removing duplicates or keeping one is the team's choice **if justified**.

**What the notebook says it does** (cell 31, DEC-008): *"keep the car the driver started in, break ties by the best `positionOrder`."*

**What it actually does.** Its own output in cell 32 shows the rule never fires: `Groups where 'started on the grid' separates the rows: 0`. Every remaining shared-drive row holds a grid slot, so all 61 groups are resolved by **best finishing position alone**. The check against the raw data shows what that keeps:

- In 60 of the 61 groups, the kept row's `(constructorId, grid)` car is also listed under **another driver** in the same race. The grid slot in the kept row is the starting position of the car, not necessarily of this driver.
- 21 of the kept rows are podiums, and only 2 dropped rows were podiums.

**Worked example: 1957 British GP.**

| driverId | constructor | grid | laps | positionOrder |
| :--- | :--- | ---: | ---: | ---: |
| 475 (Moss) | 118 | 1 | 51 | 12 (R) |
| 475 (Moss) | 118 | 3 | 90 | **1** |
| 479 (Brooks) | 118 | 3 | 90 | **1** |
| 479 (Brooks) | 118 | 1 | 51 | 12 (R) |

The current rule keeps `grid 3, P1` for **both** drivers:
- **Brooks's kept row** pairs his starting slot with the win Moss drove to. That is exactly the stitching Salma Kishk called leakage.
- **Moss's kept row** is the car he finished in, which Mayar Osama allowed. But its `grid = 3` is Brooks's pre-race slot, so the pre-race features (`grid`, `front_row`, `teammate_grid_diff`) describe another driver.

`results.csv` cannot tell us which driver started which car: both drivers are listed with both grid slots, and `laps` is per car, not per driver. So no rule built on these columns can keep a row with the driver's own pre-race state and own result.

**Fix (recommended): remove the shared-drive entries completely.** Piazza explicitly allows this option.

```python
# Task 6: shared drives (DEC-008 revised, per Piazza)
# A shared drive pairs one car's result with the grid slot of whichever driver started that car.
# results.csv does not say who started which car, so no row of the group can be kept without
# pairing one driver's pre-race state with another driver's result (data leakage, Piazza).
is_shared = results_work.duplicated(subset=GRAIN, keep=False)
shared_drives = results_work[is_shared]
print(f"Shared-drive rows removed: {len(shared_drives)} ({shared_drives.groupby(GRAIN).ngroups} driver entries, "
      f"{shared_drives['raceId'].nunique()} races, seasons {shared_drives['year'].min()}–{shared_drives['year'].max()})")

# Field size is the number of drivers who took the start, so count it before any row is removed
results_work["field_size"] = results_work.groupby("raceId")["driverId"].transform("nunique")
results_clean = results_work[~is_shared].sort_values("resultId").reset_index(drop=True)
```

**Edge cases.**
1. **Races now have fewer than three podium rows.** The assertion in Task 7.2 (`podiums_per_race >= 3`) will fail. Replace it with `assert (podiums_per_race <= 3).all()` and report how many races have 0, 1 or 2 podium rows. The "Fifteen races have four or five podium rows" statements (Hand-Off cell 43, Limitations cell 202, report) no longer hold.
2. **`field_size` must not shrink.** `add_context_features` counts rows per race. After the removal, that would undercount the starters of those races. Carry the `field_size` computed above into `clean_df` and `feature_base`, and stop recomputing it in `add_context_features`. `pre_race_features()` (Task 37) builds its entry list from `feature_base`, so it inherits the stored value. Check that Task 37.2 still reproduces `model_df`.
3. **`teammate_grid_diff`** for a teammate whose partner row was removed becomes `NaN` or uses fewer cars. This is acceptable. Mention it.
4. **History features** (driver and constructor form, career and circuit rates) lose these races for the drivers involved. This is consistent: an outcome that cannot be attributed is not used as history either.
5. **Single-row partners.** A driver who handed a car over and drove nothing else has **one** row, so `duplicated()` does not catch them, yet that row has the same problem. The raw-data check finds 89 single-row entries whose `(raceId, constructorId, grid)` car is also listed under another driver (1950–1975, 13 of them podiums). Some are data-entry collisions rather than handovers. Example: 1975 Brazilian GP, where two cars of constructor 3 are both at grid 11 with different results. **Inspect the 13 podium rows by hand.** Remove the genuine handovers with the same rule and log the collisions. Do not remove all 89 blindly.
6. **Size of the change.** About 125 rows (61 driver entries, 1950–1964) plus any confirmed single-row partners, which is about 0.5% of training rows. Put one line in the text so that nobody reads it as dropping an era.

**Alternatives considered (say why they were rejected).**
- *Keep the car the driver finished in (Mayar Osama's case).* The result is attributable, but the grid slot is not, as in the Moss row above. It still pairs another driver's pre-race slot with this driver.
- *Keep the row with the driver's best grid slot.* There is no evidence that this is the car the driver started in.

**Also update.**
- The Task 6 markdown.
- DEC-008: mark it *Superseded*, citing both Piazza answers.
- The report's cleaning table (row "Shared drives").
- Every row count and metric downstream (see [Section 5](#5-implementation-order-and-cascade-checklist)).

---

## 3. Medium- and Low-Severity Flags

### F4. `W` (withdrawn) removal has no keep-vs-remove experiment

**Piazza rulings.**
- *Mayar Osama:* remove only `F`.
- *Farida Helmy:* removing `W` is a design choice **that you must justify through experiments**, by showing that keeping and removing give the same results.

**What the notebook does.** Task 5.2 removes 331 `W` rows (zero laps) along with the `F` rows, and the only justification is in prose. `W` rows by split: train 324, validation 5, test 7.

**What is already right.**
- The rule correctly keeps the 24 rows labelled `F`, `W` or `Withdrew` that completed racing laps. They are mid-race withdrawals, which are post-race outcomes.
- The one `F` row that raced (1977 German GP, grid 25, 9 laps) is a data inconsistency. Keeping it is right, but name it in the text.
- The removed `W` rows carry statuses such as `Accident`, `Injury` and `Engine`. These are practice or qualifying incidents that happened before the race, which supports "known before the race".

**Fix: add a keep-vs-remove experiment** (new Task 17.3, next to the training-window experiment, using the same bootstrap helper).

1. Put the cleaning and feature build in one function, so that the table can be rebuilt with one flag changed:
   ```python
   def build_model_table(drop_withdrawn: bool = True, exclude_indy: bool = EXCLUDE_INDY_500) -> pd.DataFrame:
       """Tasks 5–7 and 12 in one call: cleaning, deduplication, base table and features."""
   ```
2. Build `model_df_removed` (current) and `model_df_kept` (zero-lap `W` rows kept).
3. Train the logistic regression **and** LightGBM with fixed hyperparameters on each training split.
4. Score on the **same validation rows**: the rows present in both tables, which excludes the 5 `W` rows. Also show the score on each table's own validation rows.
5. Report the PR-AUC difference with its 95% race-bootstrap interval, as in Task 19.
6. **Fix the decision rule before running.** If the interval includes 0 and |Δ| is below the seed noise measured in Task 29 (about 0.006), removal is justified. If not, keep the `W` rows.

**Edge cases for the "kept" variant.**
- **`grid == 0` on a kept `W` row is not a pit-lane start.** Change `is_pit_start` to `(results_work["grid"] == 0) & ~is_withdrawn`. Give the row the approved `last_grid + 1` encoding with `pit_start = 0`. The assertion in Task 5.3 (`laps > 0` for every `grid == 0` row) must exclude withdrawn rows.
- **Do not add a `withdrawn` flag as a feature.** The target of a withdrawn row is always 0, so the model would learn the label from the flag and the comparison would be meaningless.
- **History features change too.** Each kept `W` row counts as a non-podium race in that driver's and constructor's rolling form and career rate. This is the main way that keeping `W` can change the results for *other* rows. The experiment measures it only if the features are rebuilt from the kept table, which is why the build must run end to end.
- **`field_size`** should still count starters only. Compute it from rows that are not withdrawn.
- **Inference.** `predict_podium()` is never asked about a driver who withdrew, so it needs no change.

**Also update.**
- DEC-009 (still *Proposed*): set it to *Approved* or *Superseded* and cite Piazza and the experiment.
- The report's cleaning section: one sentence plus the result table.

---

### F5. Indianapolis 500 exclusion has no evidence beyond prose

**Piazza rulings.**
- *Farida Helmy:* *"You must find a way to utilize the entire dataset."*
- *Golden rule:* every decision needs evidence.

The ruling was given about dropping eras, not single races, so the exclusion is not clearly forbidden. But it removes 405 rows, the largest removal after `F`. The decision log cites only regulations, with no data evidence.

**Facts from the raw data.**
- 103 of the 107 Indy 500 drivers never started another championship race.
- The Indy 500 shares `circuitId = 19` with the 2000–2007 United States GP, which ran on the Indianapolis road course.

**Fix.** Reuse the F4 harness with `exclude_indy=False`, because `EXCLUDE_INDY_500` already exists in the config. Report the same Δ table. Then:
- **If the result is the same:** keep the exclusion, now backed by an experiment. Cite the Piazza rule and explain that this is a race-level scope decision, not dropping an era.
- **If it differs:** keep the Indy 500 rows and add `is_indy500` (known before the race) to the context group.

**Edge cases when the rows are kept.**
- **Split the circuit key.** If you do not, `circuit_historical_podium_rate` mixes the oval with the road course. Use `circuit_key = circuitId`, but `"19-oval"` for Indy 500 races. A driver's Indy history must not count at the USGP.
- **Fields of 33 cars** raise `field_size` and the `grid` range in the 1950s. This is already handled by the grid features, but check the `last_grid + 1` encoding.
- **Indy-only drivers and constructors** (such as Kurtis Kraft and Watson) build form histories from Indy alone. That is fine, but mention it.
- **Standings.** Indy points counted toward the championship, so `driver_standings` already includes them whether the race is kept or dropped. The standings features do not change. Say so, because a reader may assume they are affected.
- **Q2 (home advantage)** would gain 400+ American drivers at an American race. Re-run Q2 and say whether its answer changes.

**Also update.** DEC-003 (cite the experiment) and the report.

---

### F6. Sprint: the leakage question is not answered

**Piazza ruling (Farida Helmy and Salma Kishk).** *"Explore and decide whether including Sprint results creates a data leakage problem or not, explain your reasoning, and decide how to handle/fix it."*

**What the notebook does.** DEC-016 drops the sprint group because the training seasons hold 0 sprint rows. That is a valid reason to exclude it, but it does not answer the question the brief asks. The table audit in cell 4 says "PRE-RACE SAFE (CONDITIONAL)" without showing the evidence.

**Fix.** Add a short check cell and a verdict paragraph before Task 12.7.

```python
# Task 12.7a: is a sprint result known before the Grand Prix of the same weekend?
sprint_weekends = races.loc[races["sprint_date"].notna(), ["raceId", "year", "date", "sprint_date"]]
assert (sprint_weekends["sprint_date"] < sprint_weekends["date"]).all(), "A sprint is dated on or after its Grand Prix"

# 2021–2022: the sprint set the Grand Prix grid, so its result is already inside `grid`
s = sprint_clean.merge(clean_df[GRAIN + ["year", "grid"]], on=GRAIN, how="inner")
display(s.assign(format=np.where(s["year"] <= 2022, "2021–22: sprint sets grid", "2023+: separate sprint"))
         .groupby("format").apply(lambda g: pd.Series({
             "rows": len(g),
             "grid == sprint finishing order (%)": (g["grid"] == g["sprint_positionOrder"]).mean() * 100,
             "Spearman(grid, sprint position)": g[["grid", "sprint_positionOrder"]].corr("spearman").iloc[0, 1]})))
```

**Verdict to write (adjust once the numbers are in).**
1. **Same-weekend sprint results are not leakage for the Grand Prix.** The sprint ends before the race starts (asserted above), so it falls before the prediction cutoff.
2. **Where leakage *could* enter, and how it is prevented:**
   - **Raw sprint columns.** `sprint_results` uses the Grand Prix `raceId`, so an unprefixed merge would overwrite `positionOrder` and `points` with sprint values, or the other way round. The `sprint_` prefix (Task 7.1) prevents this.
   - **Standings.** Ergast's standings for a `raceId` include the sprint *and* Grand Prix points of that weekend. They are safe only lagged to round r−1, which `add_standings` does (asserted).
   - **Sprint `statusId`, `laps` and `fastestLap`** are sprint outcomes, which is safe. They must not be confused with Grand Prix outcomes.
3. **Why the sprint is still excluded:**
   - 0 training rows, 57 validation rows and 283 test rows.
   - In 2021–2022 the sprint result already sets `grid`.

   This makes the exclusion a coverage decision, not a leakage decision.

**Also update.**
- DEC-016 (still *Proposed*).
- The `TABLE_TEMPORAL_AUDIT` entry for `sprint_results`.
- The report's feature section.

---

### F7. Report format

**Piazza ruling (Salma Kishk).** A separate report is required. *"Both Word and LaTeX are accepted, but the final report must be exported and submitted as a PDF."*

**What the repo does.** `report/report.md` → HTML → Chrome PDF (`report/build_report.py`). This produces a PDF, but the source is neither Word nor LaTeX.

**Fix.** Choose one:
- **(a) Recommended:** port `report.md` to LaTeX (Overleaf) or Word and export to PDF. `pandoc report/report.md -o report/report.tex` (or `.docx`) gives a starting point. Re-insert the figures from `figures/` and check the tables.
- **(b)** Ask a TA on Piazza whether a Markdown-sourced PDF is acceptable. Keep the reply in the Piazza summary file.

Either way, the content changes from F1–F6 have to go into the report.

---

### F8. Fifteen `E`/`D`/`R` rows removed with a post-race column

**Piazza ruling (Mayar Osama).** `R`, `E` and `D` are post-race outcomes. Only `F` was approved for removal without further evidence.

**What the notebook does.** DEC-009 also removes rows with `grid == 0 & laps == 0` and no non-starter label: 6 `E`, 6 `D`, 2 `R` and 1 `E/Underweight`, from 1981 to 2017. Examples:
- 1988 Monaco GP: driver 131 excluded.
- 2017 Malaysian GP: Räikkönen's battery failed before the start.

These entries never took the start. But the rule identifies them through `laps`, which is on the leakage blacklist, and the text never explains this.

**Fix.**
- Print the 15 rows in Task 5.2 and add one paragraph: *"No grid slot (`grid == 0`) and not a pit-lane start means the car did not take the start (excluded at scrutineering, disqualified before the race, or failed before the start). This is known before lights out. `laps == 0` is used only to confirm it, not as information about the race."*
- Add an assertion that no removed row of this kind has a grid slot.

**Edge case.** A pit-lane starter that stops on lap 1 before completing it would also show `grid == 0, laps == 0`. Check that none of the 15 is a pit-lane start: from 2014 on, the zero-lap `grid == 0` rows are the 2017 Räikkönen DNS plus `W` rows.

---

### F9. Missing values reach the final model as `NaN`. Some imputations have weak meaning

**Piazza ruling (Salma Kishk).** Leaving nulls can hurt the model. Experiment with imputation versus dropping and justify the choice with results.

**What is already right.** Task 24.2 compares the raw input (NaN), the grid fallback and imputed-and-scaled features for LightGBM: no measurable difference. Task 17 compares median imputation with the grid fallback. The notebook therefore has evidence for its choice.

**Fixes.**
- **Framing (required).** In Task 24 and Task 38, state that LightGBM's native handling of missing values was chosen *because* the Task 24.2 experiment showed no loss against imputation, and cite the Piazza rule. As written, "missing stays missing" (cell 64) reads like the leave-nulls practice the instructor warned against.
- **Optional.** The "raw + grid fallback" variant scored +0.0035, within noise. Either adopt it or say why the simpler input was kept.

**Edge cases in the imputations used by the logistic regression, forest and network** (optional; add an experiment only if time allows):

| Feature | Missing when | Current fill | Problem | Suggested fill |
| :--- | :--- | :--- | :--- | :--- |
| `q3_reached` | Race had no Q3 (before 2006) | 0 | Conflates "no Q3 session" with "knocked out before Q3" | Keep `NaN` → 0, but add `has_q3_session`, or fill with `quali_position <= 10` |
| `driver_pre_race_rank`, `constructor_pre_race_rank` | Round 1, or a driver's first race of the season | Training median (mid-field) | Calls a newcomer "mid-field" | Fill with `field_size` (last place) or add a missing flag |
| `circuit_historical_podium_rate` | Driver's first visit (31% of training rows) | Median | Usually 0, which is acceptable | Add a `first_visit` flag |
| `teammate_grid_diff` | Constructor entered one car | Median | Close to 0, which is acceptable | Fill with 0 explicitly |
| `constructor_pre_race_*` | Before 1958 (no constructors' championship) | Median | Era-dependent | Mention it, or use a missing flag |

---

### F10. Constructor renames: different choices in Q3 and in the features, neither justified

**Piazza ruling (Farida Helmy and Salma Kishk).** Whether a renamed team keeps its history depends on how you merge the data, so **justify it**.

**What the notebook does.** Q3 merges renamed teams (DEC-014). The features key on `constructorId`, so a renamed team starts from zero. This appears only under Limitations and Future Work.

**Fix (minimum).** Add a justification paragraph to Task 12:
- The rolling window is 5 races, so a rebrand costs at most 5 races of constructor form.
- Most rebrands also changed ownership and budget (for example Toro Rosso to AlphaTauri, or Force India to Racing Point), so the old form is not clearly the right prior.
- Season standings are unaffected, because rebrands happen between seasons.

**Fix (stronger, optional).** Run a lineage experiment. Extend `CONSTRUCTOR_LINEAGE` to the whole dataset and rebuild the constructor-form features keyed by lineage, then compare PR-AUC as in F4.

**Edge cases for a full lineage map.**
- **The same name means different teams:** Lotus (1958–94), Lotus Racing (2010–11) and Lotus F1 (2012–15); Renault (1977–85, 2002–11, 2016–20).
- **Chains:**
  - Tyrrell → BAR → Honda → Brawn → Mercedes
  - Jordan → Midland → Spyker → Force India → Racing Point → Aston Martin
  - Minardi → Toro Rosso → AlphaTauri → RB
  - Stewart → Jaguar → Red Bull
  - Toleman → Benetton → Renault → Lotus F1 → Renault → Alpine
  - Sauber → BMW Sauber → Sauber → Alfa Romeo → Sauber

Map by `constructorId` and season, never by name.

---

## 4. Decisions That Comply with Piazza

To make these defensible, cite the Piazza answer next to each decision in the notebook and the report.

| Topic | Piazza | Notebook | Status |
| :--- | :--- | :--- | :--- |
| Use the whole dataset for training; no era truncation | Strict no to dropping pre-2003/2006 | DEC-019: trains on 1950–2019. Shorter windows appear only as comparisons in Task 17 | ✅ Cite the ruling in Task 17 |
| `grid == 0` → last grid slot + 1 | Approved | DEC-010: `max(grid) + 1` per race, `pit_start` flag; inference (Task 37) uses the same rule | ✅ After F4, exclude kept `W` rows from `pit_start` |
| Remove `F` rows | Approved (known pre-race) | Removed (1,367) when zero laps; the one `F` row that raced is kept | ✅ Name the 1977 German GP row |
| Temporal split; `≤ 2019` is only an example | Team's choice, no leakage | Split by season, justified in Task 15; preprocessing fitted on training only (Task 19) | ✅ Optional: rolling-origin comparison (already in Future Work) |
| Baseline is not linear regression and not deliberately weak | LR invalid for classification; no strawman | Grid rule + **logistic** regression (C swept, not crippled); NN chosen among 8 architectures | ✅ |
| Features backed by EDA **and** experiments | Use both | Task 14 (EDA, single-feature AUC) + Steps 7–8 (ablation, permutation, SHAP) | ✅ |
| Tyre compounds and other data not in the dataset | Not required | Not used; listed as future work | ✅ |
| No ResNet or vision models | Must be justified if used | Not used | ✅ |
| Q3: `Fire`, `Safety belt` mechanical; `Refuelling` not | Ruling | As ruled | ✅ (but see F1 for the tyre labels) |

---

## 5. Implementation Order and Cascade Checklist

### Order

1. **F1 (Q3 mapping)** and **F2 (Q1 grid only).** These are isolated, with no effect on the model.
2. **Wrap Tasks 5–7 and 12 in `build_model_table(...)`** so that F4 and F5 can rebuild the table with one flag changed.
3. **F3 (shared drives)**, including the `field_size` change and the relaxed podium assertion.
4. **F4 (`W`) and F5 (Indy 500) experiments.** Fix the decision rule first, run both, then set the flags to the result.
5. **Run all cells** (Restart & Run All). All row counts, metrics, thresholds and SHAP numbers will change.
6. **F6, F8, F9, F10.** These are text and check cells.
7. **Update the run check (cell 205),** every result paragraph that quotes a number, `docs/decision_log.md`, and the report (F7).

### Numbers and statements that will change

| Where | What |
| :--- | :--- |
| Task 5–8 outputs, Hand-Off (cell 43) | Ledger (removals per stage), 24,575 rows, split sizes and podium rates, "Fifteen races have four or five podium rows" |
| Task 7.2 | `podiums_per_race >= 3` assertion: change to `<= 3` |
| Q1 (cells 46–50) | All tables, figure, answer, DEC-011 |
| Q3 (cells 57–63) | All rates, rankings, lineage table, sensitivity table, answer, DEC-013 |
| Step 4 Hand-Off (cell 86) | `model_df` shape and the feature-validation numbers |
| Steps 5–8 | Every PR-AUC, ROC-AUC, F1, chosen hyperparameters, thresholds, ablation and XAI numbers |
| Task 25 markdown (cell 132) | **Already inconsistent.** The text says the chosen network is "64 → 32, validation PR-AUC 0.738", but the committed output shows `Chosen: {'units': (32,), 'dropout': 0.2}` with 0.7327. Re-sync the text after the re-run |
| Limitations (cell 202) | Shared-drive bullet, qualifying-coverage bullet (Q1 no longer uses qualifying) |
| Run check (cell 205) | Every expected value |
| `docs/decision_log.md` | New entries for the revised DEC-008, 009, 011, 013 and 016 (and 003 if it changes). Mark the old ones *Superseded* (the log's own rule: never delete). DEC-009, 010 and 016 are still *Proposed*: settle them |
| `report/report.md` → PDF | Cleaning table, Q1, Q3, features (sprint), all metrics; source format (F7) |

### Checks to add so the fixes stay fixed

```python
# Q3: instructor ruling
assert {"Puncture", "Tyre", "Tyre puncture", "Fire", "Safety belt"} <= MECHANICAL_STATUSES
assert "Refuelling" not in MECHANICAL_STATUSES

# Q1: grid only, all seasons
assert "quali_position" not in q1_df.columns and q1_df["year"].min() == clean_df["year"].min()

# Shared drives: no driver appears twice in a race, and no car is credited to two drivers
assert not clean_df.duplicated(GRAIN).any()
assert (clean_df.groupby("raceId")[TARGET_COLUMN].sum() <= 3).all()

# Pit-lane flag only on drivers who started
assert (clean_df.loc[clean_df["pit_start"] == 1, "positionText"] != "W").all()
```
