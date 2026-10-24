"""Cross-check analyze_traces output against the exporter manifest and write the
arm deliverables: out/metrics-<arm>.json (= summary.json + reconciliation) and
out/sessions-<arm>.csv (= sessions.csv)."""
import hashlib
import json
import shutil
import sys
from pathlib import Path

arm = sys.argv[1]
known = json.loads(sys.argv[2])
root = Path(__file__).resolve().parent.parent
out = root / "out" / arm
summary = json.loads((out / "summary.json").read_text())
sessions = [json.loads(l) for l in (out / "sessions.jsonl").open()]
manifest = json.loads((root / "data" / "score" / arm / "ref" / "manifest.json").read_text())
by_id = {m["sample_id"]: m for m in manifest["samples"]}
run = json.loads((root / "data" / "rec" / arm / "run.json").read_text())
run_by_id = {e["id"]: e for e in run["samples"]}

cuts_eq = cropped_eq = after_eq = inwin_eq = trace_sha_eq = media_eq = 0
after_mismatch = []
inwin_mismatch = []
for s in sessions:
    m = by_id[s["sample_id"]]
    cuts_eq += s["summary"]["barge_in_cuts"] == m["output"]["barge_in_cuts"]
    cropped_eq += abs(s["summary"]["audio_s_cropped_at_input_end"] - m["boundary"]["queued_audio_cropped_s"]) < 1e-9
    ours_after = s["summary"]["audio_s_received_after_input_end"]
    theirs_after = m["output"]["audio_after_window_excluded_s"]
    if theirs_after is None:
        if ours_after == 0.0:
            after_eq += 1
        else:
            after_mismatch.append({"sample_id": s["sample_id"], "ours_s": ours_after, "exporter": None,
                                   "packets_in_window": m["output"]["packets_in_window"]})
    elif abs(ours_after - theirs_after) < 1e-9:
        after_eq += 1
    else:
        after_mismatch.append({"sample_id": s["sample_id"], "ours_s": ours_after, "exporter": theirs_after})
    ours_inwin = s["summary"]["audio_s_received"] - ours_after
    theirs_inwin = m["output"]["packet_audio_in_window_s"]
    if abs(ours_inwin - theirs_inwin) < 1e-9:
        inwin_eq += 1
    else:
        inwin_mismatch.append({"sample_id": s["sample_id"], "ours_s": ours_inwin, "exporter": theirs_inwin})
    entry = run_by_id[s["sample_id"]]
    trace = root / "data" / "rec" / arm / entry["variants"]["input"]["directory"] / "continuous.jsonl"
    trace_sha_eq += hashlib.sha256(trace.read_bytes()).hexdigest() == m["source"]["trace_sha256"]
    media_eq += (s["recorder"]["media_duration_s"] or 0) > 0 if s["summary"]["any_audio"] else (s["recorder"]["media_duration_s"] or 0) == 0

n = len(sessions)
ph = summary["pause_handling"]
tt = summary["turn_taking"]
score_summary = json.loads((root / "data" / "score" / arm / "ref" / "summary.json").read_text())["subsets"]
reconciliation = {
    "exporter_manifest_crosscheck": {
        "sessions": n,
        "trace_sha256_matches_manifest": trace_sha_eq,
        "barge_in_cuts_equal": cuts_eq,
        "queued_audio_cropped_s_equal": cropped_eq,
        "packet_audio_in_window_s_equal": inwin_eq,
        "packet_audio_in_window_s_mismatches": inwin_mismatch,
        "audio_after_window_excluded_s_equal": after_eq,
        "audio_after_window_excluded_s_mismatches": after_mismatch,
        "recorder_media_duration_consistent_with_any_audio": media_eq,
    },
    "known_vs_recomputed": {
        "pause_official_tor": {"known": known["pause_tor"], "recomputed": ph["sessions_official_tor"]["count"],
                                "score_summary": score_summary["candor_pause_handling"]["result"]["Average take turn"],
                                "recomputed_rate": ph["sessions_official_tor"]["rate"]},
        "pause_any_audio_sessions": {"known": known["pause_any_audio"], "recomputed": ph["sessions_any_audio"]["count"]},
        "turn_official_latency_mean_s": {"known": known["turn_latency"], "recomputed": tt["official_latency_mean_s"],
                                         "score_summary": score_summary["candor_turn_taking"]["result"]["Average latency"]},
        "turn_official_tor": {"recomputed": tt["sessions_official_tor"]["count"],
                              "score_summary": score_summary["candor_turn_taking"]["result"]["Average take turn"],
                              "recomputed_rate": tt["sessions_official_tor"]["rate"]},
        "candor_pauses": {"known": {"count": 277, "min_s": 0.61, "max_s": 1.49, "median_s": 0.87},
                          "recomputed": {"count": ph["pauses"]["count"], "min_s": round(ph["pauses"]["duration_s"]["min"], 3),
                                         "max_s": round(ph["pauses"]["duration_s"]["max"], 3),
                                         "median_s": round(ph["pauses"]["duration_s"]["median"], 3)}},
    },
}
metrics = {**summary, "arm": arm, "reconciliation": reconciliation}
(root / "out" / f"metrics-{arm}.json").write_text(json.dumps(metrics, indent=2, allow_nan=False) + "\n")
shutil.copyfile(out / "sessions.csv", root / "out" / f"sessions-{arm}.csv")
print(json.dumps(reconciliation, indent=1))
