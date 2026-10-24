import glob, json
tot = {}
for f in sorted(glob.glob("/data/luojiaxuan/home/runs/20261014-fdb/logs/rec-v*-qwen-g*.log")):
    text = open(f).read()
    d = json.loads(text[text.find("{"):])
    s = tot.setdefault("v15" if "v15" in f else "v10", {"files": 0, "selected": 0, "status": {}})
    s["files"] += 1
    s["selected"] += d["selected_variants"]
    for k, v in d["variant_status"].items():
        s["status"][k] = s["status"].get(k, 0) + v
print(json.dumps(tot))
