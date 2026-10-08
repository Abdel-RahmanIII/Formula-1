# Formula 1 Podium Prediction — Decision Log

This log records all key architectural, scope, cleaning, feature-engineering, and modeling decisions across Milestone 1. Every judgment call is documented with its rationale, owner, and supporting evidence.

---

## Log Entries

| Decision ID | Date | Pipeline Stage | Owner | Decision | Rationale & Evidence | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **DEC-001** | 2026-10-08 | Shared Setup | All | Set global random seed to `42`. | Ensures deterministic behavior across NumPy, Scikit-Learn, and neural network training for perfect reproducibility across team members and Kaggle runs. | **Approved** |
| **DEC-002** | 2026-10-08 | Shared Setup | M3 / All | Temporal split: Train $\le 2019$, Validation $2020\text{–}2021$, Test $\ge 2022$. | F1 evolves under strict multi-year regulatory regimes. Random splitting creates severe temporal leakage and overfits era-specific aero/engine characteristics. 2022 marks the major ground-effect regulatory overhaul, making it an ideal out-of-distribution test horizon. | **Approved** |
| **DEC-003** | 2026-10-08 | Scope / Cleaning | M1 | Exclude Indianapolis 500 races ($1950\text{–}1960$). | Between 1950 and 1960, the Indy 500 counted toward the World Championship points on paper, but was run under completely different USAC regulations, on an oval, with almost no regular European F1 drivers or constructors competing. Including it contaminates qualifying/grid conversion patterns and driver histories. | **Approved** |
| **DEC-004** | 2026-10-08 | Leakage Control | M3 / M4 | Strict pre-race temporal cutoff & Comprehensive 14-Table Leakage Blacklist. | Target is whether a driver finishes on podium (`positionOrder <= 3`). Prediction time is strictly *after qualifying and before race start*. Full schema audit conducted across all 14 tables (see detailed table audit below). All in-race telemetry (`lap_times`, `pit_stops`), post-race outcomes (`results` in-race fields, `status`), and post-race standings (`driver_standings`, `constructor_standings` at race $t$) are strictly blacklisted. Features must be lagged to race $t-1$. | **Approved** |
| **DEC-005** | 2026-10-08 | Modeling Contract | All | Analytical modeling table grain defined as strictly `(raceId, driverId)` with binary target `podium`. | Each driver entering a specific Grand Prix represents one prediction instance. Target is binary: $1$ if `positionOrder <= 3`, $0$ otherwise (podium base rate $\approx 15\%$). Identifiers (`raceId`, `driverId`, `constructorId`, `date`, `year`) are retained for lineage but excluded from training features. | **Approved** |
| **DEC-006** | 2026-10-08 | Environment | M1 | Multi-environment dataset path resolution (Kaggle `/kaggle/input/...` falling back to local `./archive`). | Allows the exact same notebook to be executed seamlessly on local developer workstations and on Kaggle without requiring manual code modifications. | **Approved** |
| **DEC-007** | 2026-10-08 | Analytics / Viz | M2 | Standardized Seaborn/Matplotlib visualization style and automated figure saving to `figures/`. | Enforces visual consistency across all EDA, DE question answers, ablation studies, and XAI figures. High-resolution exports (300 DPI) feed directly into the final PDF report. | **Approved** |

---

## Detailed 14-Table Leakage Audit (DEC-004 Reference)

| Table | Total Columns | Pre-Race Temporal Status | Pre-Race Safe Columns | Blacklisted / Target / In-Race Columns | Notes & Hazards |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `circuits` | 9 | **Fully Pre-Race Safe** | `circuitId`, `circuitRef`, `name`, `location`, `country`, `lat`, `lng`, `alt` | None | Static track properties and geographic location. |
| `constructors` | 5 | **Fully Pre-Race Safe** | `constructorId`, `constructorRef`, `name`, `nationality` | None | Static constructor properties. |
| `drivers` | 9 | **Fully Pre-Race Safe** | `driverId`, `driverRef`, `number`, `code`, `forename`, `surname`, `dob`, `nationality` | None | Static driver demographics; `dob` used with race date to calculate pre-race age. |
| `seasons` | 2 | **Fully Pre-Race Safe** | `year` | None | Calendar year. |
| `races` | 18 | **Fully Pre-Race Safe** | `raceId`, `year`, `round`, `circuitId`, `name`, `date`, `time`, all session dates/times (`fp1_date`, ..., `quali_date`, `sprint_date`) | None | Official scheduled calendar metadata. |
| `qualifying` | 9 | **Fully Pre-Race Safe** | `qualifyId`, `raceId`, `driverId`, `constructorId`, `number`, `position` (as `quali_position`), `q1`, `q2`, `q3` | None | Concluded before race start. **Naming Rule:** Rename `position` to `quali_position` to avoid collision with `results.position`. |
| `results` | 18 | **Hybrid (Leakage Core)** | `constructorId`, `number`, `grid` | **Target:** `positionOrder <= 3`<br>**Blacklisted:** `position`, `positionText`, `points`, `laps`, `time`, `milliseconds`, `fastestLap`, `rank`, `fastestLapTime`, `fastestLapSpeed`, `statusId` | Contains the actual race outcome! Only starting `grid` (and metadata) is known pre-race. |
| `status` | 2 | **Post-Race Leakage (Current Race)** | None for current race | `statusId`, `status` | Describes how the current race ended ("Finished", "Engine", "Collision", etc.). Allowed strictly in historical aggregates. |
| `constructor_results` | 5 | **Post-Race Leakage (Current Race)** | None for current race | `points`, `status` | Records current race constructor points. Must only be used via historical rolling averages prior to race $t$. |
| `constructor_standings` | 7 | **Post-Race Leakage (Current Race)** | Lagged to round $t-1$ | `points`, `position`, `positionText`, `wins` (for current `raceId`) | **Ergast Trap:** Standings in this table are updated *after* `raceId`. Joining on `raceId` leaks current race points! Must be lagged to previous round. |
| `driver_standings` | 7 | **Post-Race Leakage (Current Race)** | Lagged to round $t-1$ | `points`, `position`, `positionText`, `wins` (for current `raceId`) | **Ergast Trap:** Standings in this table are updated *after* `raceId`. Must be lagged to previous round. |
| `lap_times` | 6 | **In-Race Telemetry (100% Leakage)** | None for current race | `lap`, `position`, `time`, `milliseconds` | In-race lap-by-lap telemetry. Completely forbidden for current race. |
| `pit_stops` | 7 | **In-Race Events (100% Leakage)** | None for current race | `stop`, `lap`, `time`, `duration`, `milliseconds` | In-race pit stop events. Completely forbidden for current race. |
| `sprint_results` | 16 | **Conditional Pre-Race (Modern Era)** | If included, must be prefixed with `sprint_` | Raw un-prefixed columns (`position`, `points`, `laps`, etc.) | Sprint race occurs on Saturday before Sunday Grand Prix. Must prefix all features (e.g. `sprint_position`) to prevent collision with Sunday `results`. Exists only $\ge 2021$. |

---

## Log Maintenance Guidelines
1. **Add new entries** as decisions are made during Data Audit (Step 1), Cleaning (Step 2), DE Questions (Step 3), Feature Engineering (Step 4), and Modeling (Step 6).
2. **Never delete** rejected decisions; mark status as `Superseded` or `Rejected` and document why.
3. Every entry should have an associated code assertion or test wherever applicable (e.g., `assert_leakage_safe()`, `validate_data_contract()`).
