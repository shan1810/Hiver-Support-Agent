"""All automated metrics -> results/metrics.md (+ metrics.json, failures.csv). No API calls."""
import json

import numpy as np
import pandas as pd
from scipy.stats import spearmanr
from sklearn.metrics import cohen_kappa_score, confusion_matrix, f1_score

from src.config import GOLDEN, RESULTS, SEED
from src.intents import INTENT_NAMES

gold = pd.read_csv(GOLDEN / "golden.csv")
pred = pd.read_csv(RESULTS / "predictions.csv")
judg = pd.read_csv(RESULTS / "judgments.csv") if (RESULTS / "judgments.csv").exists() else None
df = pred.merge(gold[["gid", "stratum", "intent", "escalate", "esc_code"]], on="gid", suffixes=("", "_gold"))
df["escalate"] = df.escalate.astype(str).str.lower().isin(["true", "1"])
df["escalate_gold"] = df.escalate_gold.astype(int).astype(bool)
if judg is not None:
    # agent_noguard is not judged separately: it shares the agent's reply except where a guardrail fired.
    j = judg.set_index(["gid", "system"])
    df = df.merge(judg, on=["gid", "system"], how="left")
    ng = df.system == "agent_noguard"
    for col in ["grounded", "helpful", "tone", "action_ok", "send_ready"]:
        df.loc[ng, col] = [j.loc[(g, "agent"), col] for g in df.loc[ng, "gid"]]
    df.loc[ng & df.guardrail.notna(), ["send_ready", "action_ok"]] = np.nan  # unknown: different reply
SYSTEMS = [s for s in ["trivial", "simple", "agent_noretrieval", "agent_noguard", "agent"] if s in set(df.system)]


def system_metrics(d: pd.DataFrame) -> dict:
    esc, gold_esc = d.escalate.values, d.escalate_gold.values
    auto = ~esc
    m = {
        "n": len(d),
        "intent_acc": (d.intent == d.intent_gold).mean(),
        "intent_macro_f1": f1_score(d.intent_gold, d.intent, labels=INTENT_NAMES, average="macro", zero_division=0),
        "esc_accuracy": (esc == gold_esc).mean(),
        "esc_recall": esc[gold_esc].mean() if gold_esc.any() else np.nan,  # of must-escalate, how many caught
        "esc_precision": gold_esc[esc].mean() if esc.any() else np.nan,
        "auto_rate": auto.mean(),
        "unsafe_auto": (auto & gold_esc).sum(),  # count: auto-handled but policy says escalate
    }
    if "send_ready" in d and d.send_ready.notna().any():
        sr = d.send_ready.astype("boolean")
        m["send_ready"] = sr.mean()
        m["helpful"] = d.helpful.mean()
        m["grounded"] = d.grounded.mean()
        m["tone"] = d.tone.mean()
        # Headline: share of ALL messages the system closes on its own, correctly and well.
        m["safe_automation"] = (auto & ~gold_esc & sr.fillna(False).values).mean()
        m["auto_send_ready"] = sr[auto].mean() if auto.any() else np.nan
    return m


def bootstrap_ci(d: pd.DataFrame, key: str, n=1000) -> tuple[float, float]:
    rng = np.random.default_rng(SEED)
    gids = d.gid.unique()
    vals = []
    by = {g: x for g, x in d.groupby("gid")}
    for _ in range(n):
        sample = pd.concat([by[g] for g in rng.choice(gids, len(gids))])
        vals.append(system_metrics(sample)[key])
    lo, hi = np.nanpercentile(vals, [2.5, 97.5])
    return round(float(lo), 3), round(float(hi), 3)


out, lines = {}, []
fmt = lambda v: "-" if v is None or (isinstance(v, float) and np.isnan(v)) else (f"{v:.3f}" if isinstance(v, float) else str(v))
for scope, mask in [("all (n=200)", df.stratum.notna()), ("random stratum only (n=150)", df.stratum == "random")]:
    rows = {s: system_metrics(df[mask & (df.system == s)]) for s in SYSTEMS}
    out[scope] = rows
    cols = list(next(iter(rows.values())))
    lines += [f"\n### {scope}\n", "| system | " + " | ".join(cols) + " |", "|" + "---|" * (len(cols) + 1)]
    lines += [f"| {s} | " + " | ".join(fmt(r.get(c)) for c in cols) + " |" for s, r in rows.items()]

if judg is not None:
    hist = judg[judg.system == "historical"].merge(gold[["gid", "stratum"]], on="gid")
    lines += ["\n### Historical SpotifyCares reply (human reference), judged with the same rubric\n",
              "| scope | send_ready | helpful | grounded | tone | action_ok |", "|---|---|---|---|---|---|"]
    for scope, h in [("all", hist), ("random", hist[hist.stratum == "random"])]:
        lines.append(f"| {scope} | {h.send_ready.mean():.3f} | {h.helpful.mean():.2f} | {h.grounded.mean():.2f} | {h.tone.mean():.2f} | {h.action_ok.mean():.3f} |")

    a = df[df.system == "agent"]
    lines += ["\n### Agent: 95% bootstrap CIs (all 200, resampling messages)\n"]
    for k in ["intent_acc", "esc_recall", "safe_automation", "send_ready"]:
        lines.append(f"- {k}: {system_metrics(a)[k]:.3f}  CI {bootstrap_ci(a, k)}")

# Per-intent breakdown and confusion matrix for the agent
a = df[df.system == "agent"]
lines += ["\n### Agent per gold intent\n", "| intent | n | intent_acc | esc_recall | auto_rate | send_ready |", "|---|---|---|---|---|---|"]
for it in INTENT_NAMES:
    d = a[a.intent_gold == it]
    if len(d):
        m = system_metrics(d)
        lines.append(f"| {it} | {len(d)} | {m['intent_acc']:.2f} | {fmt(m['esc_recall'])} | {m['auto_rate']:.2f} | {fmt(m.get('send_ready'))} |")
cm = pd.DataFrame(confusion_matrix(a.intent_gold, a.intent, labels=INTENT_NAMES),
                  index=[f"gold:{x[:12]}" for x in INTENT_NAMES], columns=[x[:8] for x in INTENT_NAMES])
lines += ["\n### Agent intent confusion matrix (rows = gold)\n", "```", cm.to_string(), "```"]

# Judge vs human agreement
hr_path = GOLDEN / "human_ratings.csv"
if judg is not None and hr_path.exists():
    hr = pd.read_csv(hr_path).merge(judg, on=["gid", "system"], suffixes=("_h", "_j"))
    agree = {
        "n": len(hr),
        "send_ready_agreement": (hr.send_ready_h == hr.send_ready_j).mean(),
        "send_ready_kappa": cohen_kappa_score(hr.send_ready_h, hr.send_ready_j),
        "action_ok_kappa": cohen_kappa_score(hr.action_ok_h, hr.action_ok_j),
        "helpful_spearman": spearmanr(hr.helpful_h, hr.helpful_j).statistic,
        "grounded_spearman": spearmanr(hr.grounded_h, hr.grounded_j).statistic,
        "human_send_ready_rate": hr.send_ready_h.mean(),
        "judge_send_ready_rate": hr.send_ready_j.mean(),
    }
    out["judge_agreement"] = agree
    lines += ["\n### LLM judge vs human ratings\n"] + [f"- {k}: {fmt(v)}" for k, v in agree.items()]
    ct = pd.crosstab(hr.send_ready_h.rename("human"), hr.send_ready_j.rename("judge"))
    lines += ["", "```", ct.to_string(), "```"]
    lines += ["\nPer system (human vs judge send_ready rate):\n"]
    for s, g in hr.groupby("system"):
        lines.append(f"- {s}: human {g.send_ready_h.mean():.2f} | judge {g.send_ready_j.mean():.2f} (n={len(g)})")
else:
    lines += ["\n### LLM judge vs human ratings\n", "Not computed yet: run `python -m scripts.rate`."]

(RESULTS / "metrics.md").write_text("# Metrics\n" + "\n".join(lines) + "\n", encoding="utf-8")
(RESULTS / "metrics.json").write_text(json.dumps(out, indent=1, default=float), encoding="utf-8")

# Failure table for analysis
g = gold.set_index("gid")
fail = a.assign(customer=a.gid.map(g.customer), historical=a.gid.map(g.reply))
fail["intent_wrong"] = fail.intent != fail.intent_gold
fail["missed_escalation"] = fail.escalate_gold & ~fail.escalate
fail["over_escalation"] = ~fail.escalate_gold & fail.escalate
if "send_ready" in fail:
    fail["not_send_ready"] = fail.send_ready.astype("boolean").eq(False)
flags = [c for c in ["intent_wrong", "missed_escalation", "over_escalation", "not_send_ready"] if c in fail]
fail = fail[fail[flags].any(axis=1)]
keep = ["gid", "stratum", "customer", "intent_gold", "intent", "esc_code", "escalate", "escalation_code", "reason", "reply", "historical"] + flags
keep += [c for c in ["note", "helpful", "grounded"] if c in fail]
fail[keep].to_csv(RESULTS / "failures.csv", index=False, encoding="utf-8")
print((RESULTS / "metrics.md").read_text(encoding="utf-8"))
