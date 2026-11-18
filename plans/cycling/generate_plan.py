"""Generate the 12-week indoor cycling plan (Friel base period) as one YAML file per block.

Mon/Wed/Fri, sessions <= 60 min, Wahoo KICKR Core in ERG controlled by the Edge 830.
Targets are % of FTP (intervals.icu power zones: Z1 <=55, Z2 56-75, Z3 76-90,
Z4 91-105, SS 84-97), so they rescale whenever FTP is updated in intervals.icu.

Weekly roles (Friel base abilities):
  Mon - muscular force: low-cadence (60-65 rpm) high-torque work = seated climbing
        (weeks 1-4 Mon is endurance + speed skills while force is introduced on Wed)
  Wed - key session: force (base 1), tempo (base 2), sweet spot (base 3)
  Fri - aerobic endurance + speed skills (spin-ups); kept moderate before Saturday's run
3 load weeks + 1 recovery week; ramp FTP tests in weeks 1, 8 and 12.

Run: venv\\Scripts\\python.exe plans\\cycling\\generate_plan.py   (overwrites the block YAMLs)
"""
from datetime import date, timedelta
from pathlib import Path

OUT = Path(__file__).resolve().parent
START_MONDAY = date(2026, 11, 23)

WU = "Warmup\n- Warm up 10m ramp 45%-65% 90rpm\n"
CD = "Cooldown\n- Cool down 5m ramp 60%-45% 85rpm\n"


def d(sec):
    return f"{sec // 60}m" if sec % 60 == 0 else f"{sec}s"


def endurance(minutes, pct=65):
    return f"- Endurance {minutes}m {pct}% 85-95rpm\n"


def spinups(reps):
    return f"Spin-ups {reps}x\n- Spin 30s 60% 105-110rpm\n- Easy 90s 55% 90rpm\n"


def force(reps, on_min, pct, rpm, off_min):
    return f"Force {reps}x\n- Climb {on_min}m {pct}% {rpm}rpm\n- Easy {off_min}m 55% 90rpm\n"


def intervals(label, reps, on_min, pct, off_min, rpm="85-95rpm"):
    return f"{label} {reps}x\n- {label} {on_min}m {pct}% {rpm}\n- Easy {off_min}m 55% 90rpm\n"


def session(note, *blocks):
    return "\n".join([note + "\n", WU, *blocks, CD])


RAMP_TEST = "\n".join([
    "FTP ramp test. ERG holds each step; ride until you can no longer hold the watts at a steady cadence, then stop. "
    "FTP = 75% of the last FULL minute you completed (e.g. last full step 190 W -> FTP 142 W). "
    "Send Claude the result: FTP gets updated in intervals.icu (and on the Edge) and the plan rescales.\n",
    "Warmup\n- Warm up 10m ramp 45%-65% 90rpm\n- Easy 3m 50% 90rpm\n",
    "Ramp test\n" + "".join(f"- Ramp 1m {w}w\n" for w in range(70, 326, 15)),
    "Cooldown\n- Cool down 10m 45% 85rpm\n",
])

N_END = "Aerobic endurance: conversational, steady. Spin-ups: smooth, quiet upper body, no bouncing."
N_FORCE = "Force (seated climbing): low cadence, high torque. Stay seated, steady pedal stroke; stop a rep if knees complain."
N_TEMPO = "Tempo: comfortably hard, steady breathing, you can speak in short sentences."
N_SS = "Sweet spot: hard but sustainable; this builds the power you can hold for long efforts."
N_REC = "Recovery week: easy riding only, let the last three weeks sink in."

PLAN = []  # (week, block, mon, wed, fri)
def wk(n, b, mon, wed, fri):
    PLAN.append((n, b, mon, wed, fri))

# Block 1 - Base 1: aerobic endurance, speed skills, force introduced
wk(1, 1, RAMP_TEST,
   session(N_END, endurance(25), spinups(4)),
   session(N_END, endurance(35)))
wk(2, 1, session(N_END, endurance(20), spinups(6), endurance(3)),
   session(N_FORCE, endurance(10), force(5, 1, 80, 60, 2), endurance(10)),
   session(N_END, endurance(40, 67)))
wk(3, 1, session(N_END, endurance(25), spinups(8)),
   session(N_FORCE, endurance(8), force(6, 2, 80, 60, 2), endurance(8)),
   session(N_END, endurance(45, 68)))
wk(4, 1, session(N_REC, endurance(25, 60)),
   session(N_REC, endurance(20, 60), spinups(4)),
   session(N_REC, endurance(30, 62)))
# Block 2 - Base 2: force becomes seated climbing (Mon), tempo (Wed)
wk(5, 2, session(N_FORCE, force(4, 4, 80, 60, 3), endurance(12)),
   session(N_TEMPO, intervals("Tempo", 3, 8, 82, 3), endurance(7)),
   session(N_END, endurance(30, 67), spinups(6), endurance(3)))
wk(6, 2, session(N_FORCE, force(5, 4, 80, 60, 3), endurance(5)),
   session(N_TEMPO, intervals("Tempo", 3, 10, 83, 3), endurance(6)),
   session(N_END, endurance(45, 68)))
wk(7, 2, session(N_FORCE, force(4, 6, 80, 60, 3), endurance(9)),
   session(N_TEMPO, intervals("Tempo", 2, 15, 85, 5), endurance(5)),
   session(N_END, endurance(30, 68), spinups(6), endurance(3)))
wk(8, 2, session(N_REC, endurance(25, 60)),
   session(N_REC, endurance(20, 60), spinups(4)),
   RAMP_TEST)
# Block 3 - Base 3: sweet spot (Wed), sweet-spot climbing (Mon)
wk(9, 3, session(N_FORCE, force(3, 6, 88, 65, 4), endurance(10)),
   session(N_SS, intervals("Sweet spot", 2, 12, 90, 5), endurance(11)),
   session(N_END, endurance(30, 68), "- Tempo finish 10m 80% 85-95rpm\n", endurance(5)))
wk(10, 3, session(N_FORCE, force(4, 6, 88, 65, 4), endurance(5)),
   session(N_SS, intervals("Sweet spot", 2, 15, 90, 5), endurance(5)),
   session(N_END, endurance(25, 68), "- Tempo finish 15m 80% 85-95rpm\n", endurance(5)))
wk(11, 3, session(N_FORCE, force(3, 8, 88, 65, 4), endurance(9)),
   session(N_SS, intervals("Sweet spot", 3, 11, 90, 4)),
   session(N_END, endurance(20, 68), "- Tempo finish 20m 80% 85-95rpm\n", endurance(5)))
wk(12, 3, session(N_REC, endurance(25, 60)),
   session(N_REC, endurance(20, 60), spinups(4)),
   RAMP_TEST)

BLOCKS = {1: "base1", 2: "base2", 3: "base3"}


def kind(desc):
    first = desc.split("\n")[0]
    for key, label in (("FTP ramp test", "FTP ramp test"), ("Recovery", "Recovery ride"), ("Sweet spot:", "Sweet spot"),
                       ("Tempo:", "Tempo"), ("Force", "Force / climbing"), ("Aerobic", "Endurance")):
        if first.startswith(key):
            if key == "Aerobic":
                if "\nSpin-ups " in desc:
                    label += " + spin-ups"
                elif "Tempo finish" in desc:
                    label += " + tempo finish"
            return label
    return "Ride"


def minutes(desc):
    total = 0
    reps = 1
    for line in desc.split("\n"):
        if line.rstrip().endswith("x") and not line.startswith("-"):
            reps = int(line.rstrip().split()[-1][:-1])
            continue
        if line.startswith("- "):
            tok = [t for t in line.split() if t[-1] in "ms" and t[:-1].isdigit()]
            if tok:
                t = tok[0]
                total += (int(t[:-1]) * (60 if t.endswith("m") else 1)) * reps
        elif not line.strip():
            reps = 1
    return total / 60


if __name__ == "__main__":
    for b, slug in BLOCKS.items():
        lines = [f"# Cycling plan (Friel base) - block {b} ({slug}). Generated by plans/cycling/generate_plan.py",
                 f"# Push: venv\\Scripts\\python.exe pipeline\\push_workouts.py plans\\cycling\\{b}-{slug}.yaml",
                 f"plan: bike-{slug}", "workouts:"]
        for n, block, *days in PLAN:
            if block != b:
                continue
            monday = START_MONDAY + timedelta(weeks=n - 1)
            week_min = 0
            for offset, day, desc in zip((0, 2, 4), ("Mon", "Wed", "Fri"), days):
                m = minutes(desc)
                week_min += m
                assert m <= 61 or "ramp test" in desc.lower(), (n, day, m)
                lines += [f"  - date: {(monday + timedelta(days=offset)).isoformat()}",
                          f"    name: \"Bike W{n} {day} - {kind(desc)}\"",
                          "    type: VirtualRide",
                          "    description: |"]
                lines += ["      " + l if l else "" for l in desc.rstrip("\n").split("\n")]
                print(f"W{n:>2} {day} {m:4.0f} min  {kind(desc)}")
            print(f"     week total {week_min:.0f} min")
        (OUT / f"{b}-{slug}.yaml").write_text("\n".join(lines) + "\n", encoding="utf-8")
