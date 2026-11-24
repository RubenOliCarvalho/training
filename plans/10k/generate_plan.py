"""Generate the 20-week trail 10K plan as one YAML file per block in plans/10k/.

Goal: FINISH 10 km on trail (no race date, no time goal). Method: run/walk
progression (Galloway-style walk breaks) inside Friel-style periodization
(3 load weeks + 1 recovery week). No threshold/cruise intervals: the only
intensity is short hill repeats and strides. Trail rules in every session:
hike the climbs, walk technical descents, HR <= 140 on the flats.
Week 20 is the 10K finish attempt; the date is flexible: if a long session
felt hard, repeat that week before moving on.
"""
from datetime import date, timedelta
from pathlib import Path

OUT = Path(r'C:\Users\ruben\OneDrive\10_dev\training-load-forecast\plans\10k')
START_MONDAY = date(2026, 11, 23)  # week 1
EASY = "Z1-Z2 HR"                   # <= 140 bpm with current intervals.icu zones


def d(sec):
    return f"{sec // 60}m" if sec % 60 == 0 else f"{sec}s"


WU_WALK = "Warmup\n- Brisk walk 5m\n"
CD_WALK = "Cooldown\n- Easy walk 5m\n"
WU_JOG = f"Warmup\n- Easy jog/walk 10m {EASY}\n"
CD_JOG = f"Cooldown\n- Easy jog/walk 10m {EASY}\n"
STRIDES = "Strides 4x\n- Relaxed pickup 15s\n- Walk 45s\n"
DRILLS = "Drills 2x\n- High knees 20s\n- Walk 40s\n- Butt kicks 20s\n- Walk 40s\n"


def runwalk(note, reps, run_s, walk_s, strides=False, drills=False):
    parts = [note + "\n", WU_WALK]
    if drills:
        parts.append(DRILLS)
    parts.append(f"Run/walk {reps}x\n- Run easy {d(run_s)} {EASY}\n- Walk {d(walk_s)}\n")
    if strides:
        parts.append(STRIDES)
    parts.append(CD_WALK)
    return "\n".join(parts), reps * run_s / 60


def continuous(note, minutes, strides=False, drills=False):
    parts = [note + "\n", WU_WALK]
    if drills:
        parts.append(DRILLS)
    parts.append(f"Main\n- Run easy {minutes}m {EASY}\n")
    if strides:
        parts.append(STRIDES)
    parts.append(CD_WALK)
    return "\n".join(parts), minutes


def hills(note, reps, up_s, strides=False):
    parts = [note + "\n", WU_JOG, f"Hills {reps}x"+"\n"+f"- Uphill {d(up_s)} Z3 HR"+"\n"+"- Walk down 2m"+"\n"]
    if strides:
        parts.append(STRIDES)
    parts.append(CD_JOG)
    return "\n".join(parts), 20 + reps * up_s / 60


def race(note):
    body = f"{note}\n\n{WU_WALK}\nTrail 10K\n- Easy 10km {EASY}\n\n{CD_WALK}"
    return body, 100


N_EASY = "Easy: stay conversational; if HR goes above 140, slow down or walk until it settles. Hike any steep climb."
N_LONG = "Long trail session: time on feet matters, not pace. Hike every climb, walk technical descents, walk 1 min whenever HR goes above 140."
N_RW = "Run/walk: walk breaks are part of the plan, not a failure. Short, light steps; hike the climbs, walk technical descents."
N_REC = "Recovery week: less volume so the last three weeks sink in."

# (week, block, [(day_offset, name, (description, run_minutes)), ...])
W = []
def wk(n, block, tue, thu, sat):
    W.append((n, block, [(1, "Tue", tue), (3, "Thu", thu), (5, "Sat", sat)]))

# Block 1: Base 1 (general preparation / anatomical adaptation)
wk(1, 1, runwalk(N_RW, 8, 60, 120), runwalk(N_RW, 7, 60, 120), runwalk(N_LONG, 10, 60, 120))
wk(2, 1, runwalk(N_RW, 7, 90, 120), runwalk(N_RW, 6, 90, 120), runwalk(N_LONG, 9, 90, 120))
wk(3, 1, runwalk(N_RW, 7, 120, 120), runwalk(N_RW, 6, 120, 120), runwalk(N_LONG, 9, 120, 120))
wk(4, 1, runwalk(N_REC, 6, 90, 120), runwalk(N_REC, 5, 90, 120), runwalk(N_REC, 7, 90, 120))
# Block 2: Base 2 (longer run segments, first strides)
wk(5, 2, runwalk(N_RW, 5, 180, 120, strides=True), runwalk(N_RW, 5, 180, 120), runwalk(N_LONG, 7, 180, 120))
wk(6, 2, runwalk(N_RW, 4, 240, 90, strides=True), runwalk(N_RW, 4, 240, 90), runwalk(N_LONG, 7, 240, 90))
wk(7, 2, runwalk(N_RW, 4, 300, 90, strides=True), runwalk(N_RW, 4, 300, 90), runwalk(N_LONG, 6, 300, 90))
wk(8, 2, runwalk(N_REC, 4, 240, 90), runwalk(N_REC, 4, 240, 90), runwalk(N_REC, 5, 240, 90))
# Block 3: Base 3 (towards continuous running, drills for speed skill)
wk(9, 3, runwalk(N_RW, 4, 360, 60, strides=True, drills=True), runwalk(N_RW, 4, 360, 60), runwalk(N_LONG, 5, 360, 60))
wk(10, 3, runwalk(N_RW, 3, 480, 60, strides=True, drills=True), runwalk(N_RW, 3, 480, 60), runwalk(N_LONG, 4, 480, 60))
wk(11, 3, runwalk(N_RW, 3, 600, 60, strides=True, drills=True), continuous(N_EASY, 20), runwalk(N_LONG, 4, 600, 60))
wk(12, 3, continuous(N_REC, 20, strides=True), continuous(N_REC, 20),
   continuous("Benchmark: 30 min continuous at HR <= 140. Note the distance; we repeat this later to measure aerobic progress.", 30))
N_HILL = ("Hills: run (or power-hike if it is steep) up a 4-8% slope, strong but controlled, "
          "tall posture, short quick steps. Walk back down. HR can go into Z3 on the climbs.")
N_10K = ("Trail 10K finish. Start slower than feels necessary, hike every climb, walk technical descents, "
         "walk 1 min whenever HR goes above 140 on the flats. Finishing is the goal; pace doesn't matter.")
# Block 4: Build 1 (continuous running, hill strength, long sessions on trail)
wk(13, 4, hills(N_HILL, 6, 45), continuous(N_EASY, 25), continuous(N_LONG, 45))
wk(14, 4, hills(N_HILL, 8, 45, strides=True), continuous(N_EASY, 30), continuous(N_LONG, 50))
wk(15, 4, hills(N_HILL, 6, 60), continuous(N_EASY, 30, strides=True), continuous(N_LONG, 60))
wk(16, 4, hills(N_REC, 4, 45), continuous(N_REC, 25), continuous(N_REC, 40))
# Block 5: Build 2 (longest time on feet, longer hills, benchmark repeat)
wk(17, 5, hills(N_HILL, 8, 60), continuous(N_EASY, 35, strides=True), continuous(N_LONG, 70))
wk(18, 5, hills(N_HILL, 6, 90), continuous(N_EASY, 35), continuous(N_LONG, 80))
wk(19, 5, hills("Taper starts: same hills, less volume.", 4, 60),
   continuous("Benchmark repeat: 30 min continuous at HR <= 140 on the same route as week 12; compare distance.", 30),
   continuous(N_LONG, 50))
# Block 6: 10K week
wk(20, 6, continuous("Easy run, legs fresh for Saturday.", 25, strides=True), continuous("Shake-out: very easy, legs only.", 20),
   race(N_10K))

BLOCKS = {
    1: ("base1", "Block 1 - Base 1 (wk 1-4): impact tolerance and habit; run/walk with HR cap."),
    2: ("base2", "Block 2 - Base 2 (wk 5-8): longer run segments, first strides."),
    3: ("base3", "Block 3 - Base 3 (wk 9-12): towards 30 min continuous; drills; benchmark in wk 12."),
    4: ("build1", "Block 4 - Build 1 (wk 13-16): continuous running; hill repeats; long trail sessions to 60 min."),
    5: ("build2-peak", "Block 5 - Build 2 (wk 17-19): longer hills; long trail sessions to 80 min; benchmark repeat."),
    6: ("race", "Block 6 - 10K week (wk 20): trail 10K finish, nominally Sat 10 Apr 2027 (date flexible)."),
}

OUT.mkdir(parents=True, exist_ok=True)
# Runs that were dropped or swapped for another session; they are left out of
# the block files so re-pushing a block doesn't bring them back.
SKIPPED = {
    date(2026, 11, 24): "W1 Tue: couldn't run, replaced by an easy bike ride (plans/adhoc.yaml)",
}

totals = []
for b, (slug, title) in BLOCKS.items():
    lines = [f"# 10K plan - {title}",
             "# Push: venv\\Scripts\\python.exe pipeline\\push_workouts.py plans\\10k\\" + f"{b}-{slug}.yaml",
             f"plan: 10k-{slug}", "workouts:"]
    for n, block, sessions in W:
        if block != b:
            continue
        monday = START_MONDAY + timedelta(weeks=n - 1)
        run_min = 0
        for offset, day, (desc, rmin) in sessions:
            if monday + timedelta(days=offset) in SKIPPED:
                continue
            run_min += rmin
            first = desc.split("\n")[0]
            if first.startswith("Trail 10K"):
                kind = "Trail 10K finish"
            elif "\nHills " in desc:
                kind = "Hill repeats"
            elif "Benchmark" in first:
                kind = "Benchmark 30 min"
            elif "Cruise" in desc:
                kind = "Threshold intervals"
            elif "Steady" in desc:
                kind = "Steady intervals"
            elif day == "Sat":
                kind = "Long run/walk" if "Run/walk" in desc else "Long run"
            elif "Run/walk" in desc:
                kind = "Run/walk"
            else:
                kind = "Easy run"
            if "Drills" in desc:
                kind = "Drills + " + kind.lower()
            if "Strides" in desc and day != "Sat":
                kind += " + strides"
            if first.startswith("Recovery"):
                kind += " (recovery wk)"
            lines.append(f"  - date: {(monday + timedelta(days=offset)).isoformat()}")
            lines.append(f"    name: \"10K W{n} {day} - {kind}\"")
            lines.append("    description: |")
            lines += ["      " + l if l else "" for l in desc.rstrip("\n").split("\n")]
        totals.append((n, b, round(run_min)))
    (OUT / f"{b}-{slug}.yaml").write_text("\n".join(lines) + "\n", encoding="utf-8")

prev = None
for n, b, m in totals:
    chg = f"{(m - prev) / prev * 100:+.0f}%" if prev else ""
    print(f"W{n:>2} B{b} run-min {m:>3} {chg}")
    prev = m
