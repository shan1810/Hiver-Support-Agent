"""Interactive review of golden labels. Run: python -m scripts.label

Shows each message with its current (draft) label. Press Enter to accept, or type a correction:
  <intent number> [A|E1|E2|E3|E4]     e.g. "3 E1"  or just "E2" to change only escalation.
Progress is saved after every item, so you can quit (q) and resume.
Rows you reviewed get label_source = human_confirmed / human_changed.
"""
import pandas as pd

from src.config import GOLDEN
from src.intents import ESCALATION_POLICY, INTENT_NAMES, INTENTS, TIE_BREAKS

PATH = GOLDEN / "golden.csv"
CODES = {"A", "E1", "E2", "E3", "E4"}


def main():
    g = pd.read_csv(PATH, dtype=str)
    todo = g.index[~g.label_source.str.startswith("human")]
    print(ESCALATION_POLICY, "\n\nTie-breaks:\n" + TIE_BREAKS + "\n")
    for i, name in enumerate(INTENT_NAMES, 1):
        print(f"  {i} {name:22s} {INTENTS[name][:90]}")
    print(f"\n{len(todo)} rows left to review.\n")
    for idx in todo:
        r = g.loc[idx]
        print("-" * 100)
        print(f"[{r.gid}] ({r.stratum})  CUSTOMER: {r.customer}")
        print(f"          historical reply: {r.reply}")
        print(f"   draft -> {INTENT_NAMES.index(r.intent) + 1} {r.intent}  {r.esc_code}")
        ans = input("   Enter=accept | '<n> <code>' | q > ").strip()
        if ans.lower() == "q":
            break
        intent, code = r.intent, r.esc_code
        for tok in ans.upper().split():
            if tok in CODES:
                code = tok
            elif tok.isdigit() and 1 <= int(tok) <= len(INTENT_NAMES):
                intent = INTENT_NAMES[int(tok) - 1]
            else:
                print(f"   ignored token {tok!r}")
        changed = (intent, code) != (r.intent, r.esc_code)
        g.loc[idx, ["intent", "esc_code"]] = [intent, code]
        g.loc[idx, "escalate"] = str(int(code != "A"))
        g.loc[idx, "label_source"] = "human_changed" if changed else "human_confirmed"
        g.to_csv(PATH, index=False, encoding="utf-8")
    print(g.label_source.value_counts().to_string())


if __name__ == "__main__":
    main()
