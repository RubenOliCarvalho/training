"""Generate the 20-week 10K plan as one YAML file per block in plans/10k/."""
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


def intervals(note, reps, on_min, zone, off_min):
    body = f"{note}\n\n{WU_JOG}\nMain set {reps}x\n- {'Steady' if zone == 'Z3' else 'Cruise'} {on_min}m {zone} HR\n- Easy jog/walk {off_min}m\n\n{CD_JOG}"
    return body, 20 + reps * (on_min + off_min * 0.5)


def race(note):
    body = (f"{note}\n\n{WU_JOG}\nStrides 3x\n- Relaxed pickup 15s\n- Walk 45s\n\n"
            "Race\n- First 5k even 5km Z3 HR\n- Second 5k 5km Z3-Z4 HR\n\nCooldown\n- Easy walk 10m\n")
    return body, 85


N_EASY = "Easy: stay conversational; if HR goes above 140, slow down or walk until it settles."
N_LONG = "Long aerobic session: time on feet matters, not pace. Walk 1 min whenever HR goes above 140."
N_RW = "Run/walk: walk breaks are part of the plan, not a failure. Short, light steps; soft surface if possible."
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
# Block 4: Build 1 (continuous running, steady Z3 work = muscular endurance)
wk(13, 4, intervals("Steady running: comfortably hard, you can speak in short sentences.", 3, 5, "Z3", 2), continuous(N_EASY, 25), continuous(N_LONG, 40))
wk(14, 4, intervals("Steady running: comfortably hard, you can speak in short sentences.", 4, 5, "Z3", 2), continuous(N_EASY, 30, strides=True), continuous(N_LONG, 45))
wk(15, 4, intervals("Steady running: comfortably hard, you can speak in short sentences.", 3, 8, "Z3", 2), continuous(N_EASY, 30), continuous(N_LONG, 50))
wk(16, 4, intervals(N_REC, 2, 8, "Z3", 2), continuous(N_REC, 25), continuous(N_REC, 35))
# Block 5: Build 2 + peak (threshold / cruise intervals, longest runs)
wk(17, 5, intervals("Cruise intervals at threshold: hard but controlled, even effort on every rep.", 4, 6, "Z4", 2), continuous(N_EASY, 35, strides=True), continuous(N_LONG, 55))
wk(18, 5, intervals("Cruise intervals at threshold: hard but controlled, even effort on every rep.", 3, 8, "Z4", 2), continuous(N_EASY, 40), continuous(N_LONG, 65))
wk(19, 5, intervals("Taper starts: same intensity, less volume.", 4, 5, "Z4", 2), continuous(N_EASY, 30, strides=True), continuous("Benchmark repeat: 30 min continuous at HR <= 140; compare distance with week 12.", 30))
# Block 6: race week
wk(20, 6, intervals("Race week: short and sharp, finish fresh.", 3, 3, "Z4", 2), continuous("Shake-out: very easy, legs only.", 20, strides=True),
   race("10K race / time trial. Start controlled (Z3), only push in the second half. Walk breaks are fine if HR runs away early."))

BLOCKS = {
    1: ("base1", "Block 1 - Base 1 (wk 1-4): impact tolerance and habit; run/walk with HR cap."),
    2: ("base2", "Block 2 - Base 2 (wk 5-8): longer run segments, first strides."),
    3: ("base3", "Block 3 - Base 3 (wk 9-12): towards 30 min continuous; drills; benchmark in wk 12."),
    4: ("build1", "Block 4 - Build 1 (wk 13-16): continuous running; steady Z3 intervals."),
    5: ("build2-peak", "Block 5 - Build 2 + peak (wk 17-19): threshold cruise intervals; longest runs; benchmark repeat."),
    6: ("race", "Block 6 - Race week (wk 20): taper and 10K on Sat 10 Apr 2027."),
}

OUT.mkdir(parents=True, exist_ok=True)
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
            run_min += rmin
            first = desc.split("\n")[0]
            if first.startswith("10K race"):
                kind = "10K race"
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
