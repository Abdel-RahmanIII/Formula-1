# Phase Plan: Steps 1 & 2 — Data Audit, Cleaning & Before/After EDA

> **Owner:** M1 (Data Lead)  
> **Prerequisite:** Shared Components section complete (`raw_dataframes` loaded, leakage guards active, `save_fig()` ready).  
> **Deliverable:** A cleaned, contract-validated analytical base table ready for M2 (DE Questions) and M3 (Feature Engineering).

---

## Task 1: Raw Table Inventory & Structural Inspection

**Goal:** Programmatically confirm that all 14 tables loaded correctly and document their structural properties.

**Deliverables:**
- Summary table showing each table's row count, column count, dtypes breakdown, memory footprint, and null counts.
- Per-table `.info()` and `.describe()` outputs for quick reference.
- Confirm `raw_dataframes` contains exactly 14 keys matching the expected table names.

**Key tables to pay attention to:**
- `results` (26,759 rows × 18 cols — the "spine" of the pipeline)
- `lap_times` (589,081 rows — largest table, 100% forbidden for features)
- `qualifying` (10,494 rows — only covers ~1994 onward)

---

## Task 2: Primary Key & Referential Integrity Checks

**Goal:** Verify that every table's primary key is unique and non-null, and that all foreign keys resolve to valid parent rows.

**Deliverables:**
- **Primary key uniqueness assertions** for each table:
  - Single keys: `circuits.circuitId`, `constructors.constructorId`, `drivers.driverId`, `races.raceId`, `results.resultId`, `qualifying.qualifyId`, `status.statusId`, `seasons.year`, etc.
  - Composite keys: `qualifying (raceId, driverId)`, `lap_times (raceId, driverId, lap)`, `pit_stops (raceId, driverId, stop)`.
  - Flag `results (raceId, driverId)` — this one **will** have duplicates (shared drives). Document the count but don't fix yet.
- **Foreign key anti-join reconciliation** — for each relationship, count orphan rows:
  - `results.raceId` → `races.raceId`
  - `results.driverId` → `drivers.driverId`
  - `results.constructorId` → `constructors.constructorId`
  - `results.statusId` → `status.statusId`
  - `qualifying.raceId` → `races.raceId`
  - `races.circuitId` → `circuits.circuitId`
  - `constructor_standings.constructorId` → `constructors.constructorId`
  - `driver_standings.driverId` → `drivers.driverId`
- Report orphan counts; all should be zero. If any aren't, document and decide.

---

## Task 3: Pre-Cleaning "Before" EDA

**Goal:** Establish the raw data baseline with visualizations, so you can later show the impact of cleaning.

**Deliverables (all saved via `save_fig()`):**

| Plot | What it shows |
| :--- | :--- |
| **Missingness heatmap** | Per-column null rates across the main tables (`results`, `qualifying`, `drivers`). Highlight `\N`-sentinel columns that became `NaN` on load. |
| **Rows per season** | Bar chart of `results` rows grouped by `year` (via join to `races`). Shows field-size evolution from 1950s to 2024. |
| **Entrants per race** | Distribution of drivers per race over time (boxplot or line). |
| **Qualifying coverage per season** | Count of rows in `qualifying` per year vs. total `results` rows per year. Highlights the pre-1994 gap and the Q1/Q2/Q3 introduction in 2006. |
| **Podium base rate per season** | Line chart of `(positionOrder <= 3).mean()` per year. Shows how shrinking/growing fields affect the ~15% rate. |
| **Duplicate `(raceId, driverId)` distribution** | Which seasons/decades have the 176 shared-drive duplicates. |

---

## Task 4: Semantic Typing & Sentinel Eradication

**Goal:** Convert all columns to their correct semantic types. Eradicate any remaining string `\N` sentinels.

**Deliverables (all on `.copy()` working copies):**
- **Date/time conversions:**
  - `races.date` → `datetime64`
  - `drivers.dob` → `datetime64`
  - Race session time columns (`time`, `fp1_time`, `quali_time`, etc.) — parse or leave as string if not needed.
- **Qualifying lap times → float seconds:**
  - `q1`, `q2`, `q3` strings like `"1:23.456"` → numeric seconds using the `lap_time_to_seconds()` pattern from [cleaning_notes.md](cleaning_notes.md).
  - Do **not** drop rows for `NaN` in `q2`/`q3` — those are structurally expected (knockout elimination).
- **Numeric casting:**
  - `results.milliseconds`, `results.fastestLap`, `results.rank`, `drivers.number` — coerce to numeric.
  - `pit_stops.duration` and `pit_stops.milliseconds` — coerce to numeric.
- **Final sentinel check:** Assert that no cell in any cleaned table still contains the literal string `\N`.

---

## Task 5: Scope Filtering & Non-Starter Removal

**Goal:** Remove rows that fall outside the modeling scope, per the decisions in [decision_log.md](decision_log.md).

**Deliverables:**
- **Exclude Indianapolis 500 (1950–1960):** Filter out races where `year ∈ [1950, 1960]` AND `name` contains "Indianapolis 500". Log the number of removed rows.
- **Remove non-starters (DNQ / DNPQ / DNS):** These drivers never took the start — they're not valid prediction instances. Filter using `positionText` codes (`'F'`, `'W'`, `'D'` etc.) or `grid > 0` logic, per the approach chosen. Document the exact criterion.
- **Handle `grid = 0` pit-lane starts:**
  - Create `pit_start = (grid == 0).astype(int)` boolean flag.
  - Recode `grid = 0` to back-of-grid (e.g., max grid position for that race, or `field_size`).

---

## Task 6: Grain Resolution — Shared-Drive Deduplication

**Goal:** Enforce the strict `(raceId, driverId)` composite grain by resolving the historical shared-drive duplicates.

**Deliverables:**
- Apply the deterministic deduplication rule from [cleaning_notes.md § Trap 1](cleaning_notes.md):
  1. Prioritize the car the driver started in (`grid > 0`).
  2. Break ties by best `positionOrder`.
  3. Keep first, drop rest.
- Report the exact number of dropped rows and the season range they came from.
- Assert grain uniqueness: `assert df.duplicated(subset=['raceId', 'driverId']).sum() == 0`
- Add **DEC-008** to the decision log (if not already present) documenting the rule.

---

## Task 7: Construct the Analytical Base Table & Derive Target

**Goal:** Build the initial analytical table by joining the cleaned tables, creating the `podium` target, and attaching identifier columns.

**Deliverables:**
- **Core join:** `results_clean` ← join with `races` (to get `date`, `year`, `round`, `circuitId`) ← join with `circuits` (to get `country`, `name`).
- **Rename `qualifying.position` → `quali_position`** before any merge to avoid the column collision (Trap 2).
- **Prefix sprint columns** with `sprint_` before merging (Trap 3).
- **Derive target:** `podium = (positionOrder <= 3).astype(int)`
- **Verify identifier columns:** `raceId`, `driverId`, `constructorId`, `date`, `year` — all present, all non-null.
- **Run `validate_data_contract()`** on the assembled table with `enforce_grain_only=False` — must pass cleanly.

---

## Task 8: Post-Cleaning "After" EDA & Comparison

**Goal:** Repeat the key plots from Task 3 on the cleaned data to demonstrate and quantify the impact of each cleaning step.

**Deliverables (all saved via `save_fig()`):**

| Comparison | What to show |
| :--- | :--- |
| **Row counts before vs. after** | How many rows were removed by Indy 500 exclusion, non-starter removal, and deduplication. A stacked bar or waterfall chart. |
| **Missingness heatmap (after)** | Same layout as before; should show significantly reduced nulls in typed columns. |
| **Podium base rate (after)** | Line chart per season on cleaned data — compare to pre-cleaning rate (e.g., overlay or side-by-side). |
| **Qualifying coverage (after)** | Updated coverage chart. |
| **Dtype summary (after)** | Confirm all numeric columns are now numeric, dates are datetime, no `object` pollution in columns that should be numeric. |
| **Sentinel eradication assertion** | `assert not (clean_df.astype(str) == r"\N").any().any()` — programmatic confirmation. |

---

## Execution Order Summary

```
Task 1 → Task 2 → Task 3 → Task 4 → Task 5 → Task 6 → Task 7 → Task 8
 ▲                  ▲                                          ▲
 │                  │                                          │
 Raw data loaded    Before EDA baseline                        After EDA comparison
```

> [!IMPORTANT]
> After Task 8, the cleaned base table is ready to hand off to:
> - **M2** for DE Questions (Q1–Q3) in Step 3
> - **M3** for Feature Engineering in Step 4
> - Both should work from the same validated `clean_df` object.

---

## Key References

- [milestone_1_plan.md](milestone_1_plan.md) — Steps 1 & 2 specs
- [cleaning_notes.md](cleaning_notes.md) — All 9 traps and contract rules
- [decision_log.md](decision_log.md) — DEC-001 through DEC-008
- [formula_1_guide.md](formula_1_guide.md) — Domain context for qualifying formats, eras, shared drives
