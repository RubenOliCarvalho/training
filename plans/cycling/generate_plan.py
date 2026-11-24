"""Generate the 12-week indoor cycling plan as one YAML file per block.

Method: Joe Friel's periodization (Preparation -> Base, 3 load weeks + 1 recovery
week, abilities added in order: aerobic endurance -> force -> muscular endurance)
with Chris Carmichael's (CTS) workout set: EnduranceMiles, FastPedal, Tempo,
SteadyState. Carmichael's Time-Crunched program is intensity-heavy and assumes
a base, so it is NOT used here; this is a slow start for an unfit rider.

Mon/Wed/Fri, sessions <= 60 min, Wahoo KICKR Core in ERG controlled by the Edge 830.
Targets are % of FTP so they rescale when FTP is updated in intervals.icu.
CTS defines its ranges against the CTS field test (8-min efforts), not FTP; the
mapping to %FTP below is a conservative approximation (UNVERIFIED):
  EnduranceMiles 58-67%, FastPedal ~58% at 100-110 rpm, Tempo 76-80%,
  SteadyState 88%, Friel force (seated climbing) 75-82% at 65 rpm.

  Block 1 (wk 1-4)  Preparation: EnduranceMiles + FastPedal only, 35-50 min.
  Block 2 (wk 5-8)  Base 1/2: + Tempo (Wed), + seated force climbing (Mon, from wk 6).
  Block 3 (wk 9-12) Base 3: + SteadyState (Wed), force progresses, tempo finish (Fri).
Fri stays easy (EnduranceMiles) because Saturday is the long run.
Ramp FTP tests: wk 1 Mon (done 23 Nov 2026, FTP 181), wk 8 Fri, wk 12 Fri.

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


def fastpedal(reps, on_min, off_min):
    return f"FastPedal {reps}x\n- FastPedal {on_min}m 58% 100-110rpm\n- Easy {off_min}m 55% 85-90rpm\n"


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

N_END = ("Aerobic endurance (EnduranceMiles): conversational, steady; you could ride like this for hours. "
         "Ride to heart rate: if HR goes above 140, let the watts drop until it settles. "
         "FastPedal: high cadence, smooth and quiet upper body, no bouncing.")
N_FORCE = ("Force (seated climbing): low cadence, high torque. Stay seated, steady pedal stroke; "
           "stop a rep if knees complain.")
N_TEMPO = "Tempo: comfortably hard, steady breathing, you can speak in short sentences."
N_SS = ("SteadyState: hard but controlled, even power for the whole interval; "
        "this builds the power you can hold on long climbs.")
N_REC = "Recovery week: easy riding only, let the last three weeks sink in."

PLAN = []  # (week, block, mon, wed, fri)
def wk(n, b, mon, wed, fri):
    PLAN.append((n, b, mon, wed, fri))

TEMPO_FINISH = "- Tempo finish {}m 78% 85-95rpm\n"

# Block 1 - Preparation: aerobic endurance and pedalling skill only
wk(1, 1, RAMP_TEST,
   session(N_END, endurance(12, 62), fastpedal(3, 1, 2)),
   session(N_END, endurance(25, 62)))
wk(2, 1, session(N_END, endurance(15, 62), fastpedal(4, 1, 2), endurance(3)),
   session(N_END, endurance(25, 63)),
   session(N_END, endurance(30, 63)))
wk(3, 1, session(N_END, endurance(15, 63), fastpedal(4, 2, 3)),
   session(N_END, endurance(30, 65)),
   session(N_END, endurance(35, 65)))
wk(4, 1, session(N_REC, endurance(15, 58)),
   session(N_REC, endurance(15, 58), fastpedal(3, 1, 2)),
   session(N_REC, endurance(20, 60)))
# Block 2 - Base 1/2: tempo (Wed), seated force climbing (Mon from wk 6)
wk(5, 2, session(N_END, endurance(15, 65), fastpedal(4, 2, 3), endurance(5)),
   session(N_TEMPO, endurance(10), intervals("Tempo", 2, 8, 78, 4), endurance(5)),
   session(N_END, endurance(40, 65)))
wk(6, 2, session(N_FORCE, endurance(10), force(4, 3, 75, 65, 3), endurance(6)),
   session(N_TEMPO, endurance(8), intervals("Tempo", 2, 10, 80, 4), endurance(5)),
   session(N_END, endurance(45, 66)))
wk(7, 2, session(N_FORCE, endurance(8), force(4, 4, 78, 65, 3), endurance(5)),
   session(N_TEMPO, endurance(5), intervals("Tempo", 3, 8, 80, 3), endurance(5)),
   session(N_END, endurance(45, 67)))
wk(8, 2, session(N_REC, endurance(20, 58)),
   session(N_REC, endurance(15, 58), fastpedal(3, 1, 2)),
   RAMP_TEST)
# Block 3 - Base 3: SteadyState (Wed), longer force reps (Mon), tempo finish (Fri)
wk(9, 3, session(N_FORCE, endurance(8), force(4, 5, 80, 65, 3)),
   session(N_SS, endurance(10), intervals("SteadyState", 3, 6, 88, 4)),
   session(N_END, endurance(30, 66), TEMPO_FINISH.format(10), endurance(3)))
wk(10, 3, session(N_FORCE, force(5, 5, 80, 65, 3), endurance(3)),
   session(N_SS, endurance(8), intervals("SteadyState", 3, 8, 88, 4)),
   session(N_END, endurance(25, 66), TEMPO_FINISH.format(15), endurance(3)))
wk(11, 3, session(N_FORCE, endurance(8), force(4, 6, 82, 65, 3)),
   session(N_SS, endurance(10), intervals("SteadyState", 2, 12, 88, 5)),
   session(N_END, endurance(20, 66), TEMPO_FINISH.format(20), endurance(3)))
wk(12, 3, session(N_REC, endurance(20, 58)),
   session(N_REC, endurance(15, 58), fastpedal(3, 1, 2)),
   RAMP_TEST)

BLOCKS = {1: "base1", 2: "base2", 3: "base3"}


def kind(desc):
    first = desc.split("\n")[0]
    for key, label in (("FTP ramp test", "FTP ramp test"), ("Recovery", "Recovery ride"), ("SteadyState:", "SteadyState"),
                       ("Tempo:", "Tempo"), ("Force", "Force / climbing"), ("Aerobic", "Endurance")):
        if first.startswith(key):
            if key == "Aerobic":
                if "\nFastPedal " in desc:
                    label += " + FastPedal"
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
