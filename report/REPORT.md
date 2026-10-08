# SpotifyCares AI support agent: report

> **Status of the numbers.** Every number below is computed by `python -m scripts.05_metrics` from committed files. The golden labels are currently **AI first-pass drafts awaiting my hand review** (`label_source` column), and the judge–human agreement section is **pending my blind ratings** (`scripts/rate.py`). Both steps are cheap to rerun (no API calls), and this report is updated after them. See "What is misleading about my headline number?".

## 1. Problem framing

**Brand.** SpotifyCares (43k replies in the dataset). It is English-only, its issues fall into a few clear types, and unlike AppleSupport (52% "DM us") or AmazonHelp (multilingual boilerplate) it solves a good share of issues in public (`scripts/00_profile_brands.py`).

**Task.** For a thread-opening customer tweet: (1) classify it into one of 8 intents, (2) decide auto-handle vs escalate with a policy reason, (3) draft the public reply.

**What "good" means for this brand.** On Twitter the reply is public and the account is the brand. The costs are asymmetric:

| Error | Cost |
|---|---|
| Auto-handling something that needs a human (a charge dispute, a hacked account, posted card data) | High: public harm, wrong advice, security risk. **Must be ~0.** |
| Inventing facts ("refunded", "fixed", "out Friday", fake links) | High: a public, screenshot-able false promise. |
| Escalating something the bot could have answered | Medium: wastes agent time; the customer waits for a DM about a how-to. |
| Wrong intent label, but right action and reply | Low: intents are for routing/analytics. |

So the **headline metric is the *safe automation rate***: the share of all incoming tweets the agent auto-handles, where the policy agrees it may be auto-handled and the reply is judged send-ready. It is reported with **unsafe automations as a hard count** beside it. The escalation policy (E1 account action, E2 security/PII, E3 high-risk tone, E4 non-English) is in `src/intents.py`. It was written before labelling and deliberately differs from historical behaviour: Spotify sent many simple how-to questions to DM, and I don't treat that as the target.

**What I chose not to build.**
- **Multi-turn conversations.** Only the opening tweet is handled. Follow-ups ("Still nothing") need thread state.
- **Acting on accounts.** No tools for refunds or lookups. Escalation *is* the action.
- **Images.** About 15.6% of opening tweets carry a screenshot (`<URL>`) that the agent cannot see.
- **Live link resolution.** `t.co` links in the data are dead, so replies use `[link: …]` placeholders.
- **Non-English replies.** Detected and escalated (E4), not answered.
- **Fine-tuning or embeddings.** At this data size and on a free tier, TF-IDF retrieval plus prompting is the right first step. Everything is measured, so a fine-tuned model can be compared later.

## 2. System

```
tweet ─► TF-IDF retrieval (6 most similar pre-cutoff tweets + SpotifyCares' actual replies; max 1 pure "see DM" reply)
      ─► one Gemini call (gemini-3.5-flash-lite, JSON schema): intent, confidence, escalate, policy code, reason, reply
      ─► guardrails (regex: posted PII tokens, hack/compromise words, non-English) — can only ADD escalations
```

- **Data.** 40,333 (customer tweet → first SpotifyCares reply) pairs. **Time split at 2017-11-25**: the knowledge base is 34,025 pairs before it, and the golden set is drawn from 4,205 opening tweets after it. Retrieval can never surface the answer being graded.
- **Intents** (8) came from KMeans (k=25) over 12k pre-cutoff tweets, then merged by *resolution path*: billing_payment, plan_student_family, account_access, account_security, playback_technical, content_availability, feature_feedback, other. Tie-break rules are written down.
- **Golden set.** 200 tweets: 150 uniform-random + 50 risk-oversampled (`data/golden/README.md`).

## 3. Results

**Baselines.**
- *Trivial:* majority intent, escalate everything, and send SpotifyCares' most common hand-off reply ("Hi there! Can you DM us your account's email address or username? We'll take a look backstage"). This is close to what the brand actually did a third of the time, so it is a meaningful floor.
- *Simple:* keyword-rule intent, rule-based escalation (money/account intents + PII + security words), reply = the verbatim historical reply to the nearest past tweet.
- *Ablations:* `agent_noretrieval` (same prompt, no examples) and `agent_noguard`.

**Reply quality** is scored by an LLM judge (`gemini-3.1-flash-lite`, a different model from the agent) on a 1–5 rubric (grounded, helpful, tone) plus `action_ok` and a binary `send_ready`. All five candidates for a tweet are judged in one call, blinded and shuffled. One candidate is **the real historical SpotifyCares reply**, which gives a human reference point on the same scale.

### Random stratum (n=150): estimates real traffic

| system | intent acc | macro-F1 | esc. recall | esc. precision | auto rate | **unsafe auto** | send-ready | **safe automation** |
|---|---|---|---|---|---|---|---|---|
| trivial | 0.22 | 0.05 | 1.00 | 0.34 | 0.00 | 0 | 0.32 | 0.00 |
| simple | 0.61 | 0.57 | 0.90 | 0.62 | 0.51 | **5** | 0.42 | 0.18 |
| agent, no retrieval | 0.83 | 0.84 | 0.98 | 0.77 | 0.57 | 1 | 0.91 | 0.55 |
| **agent** | **0.90** | **0.91** | **1.00** | 0.80 | 0.57 | **0** | 0.93 | **0.56** |
| *policy ceiling* | | | | | *0.66* | | | *0.66* |

### All 200 (incl. risk oversample)

| system | intent acc | esc. recall | unsafe auto | send-ready | safe automation |
|---|---|---|---|---|---|
| trivial | 0.31 | 1.00 | 0 | 0.41 | 0.00 |
| simple | 0.66 | 0.94 | 5 | 0.43 | 0.15 |
| agent, no retrieval | 0.86 | 0.99 | 1 | 0.93 | 0.47 |
| **agent** | **0.91** (95% CI 0.87–0.94) | **1.00** (86/86) | **0** | 0.94 (0.91–0.97) | **0.47** (0.40–0.55) |
| historical SpotifyCares reply | – | – | – | 0.68 | – |

**Reading it.**
1. The agent auto-resolves **56% of real traffic** with zero unsafe automations. The policy ceiling is 66% (the share of tweets that *may* be automated), so it captures ~85% of the automatable volume.
2. The 10-point gap to the ceiling is **over-escalation**: 18/200 tweets sent to DM that the policy says to answer publicly (failure mode 1).
3. **Retrieval** buys +5 to 7 points of intent accuracy and removes the one unsafe automation of the no-retrieval agent. It does *not* improve judged reply quality. It is mainly a classification aid.
4. **Guardrails never fired.** The LLM escalated every case they would have caught, so on this set they contributed nothing measurable. I keep them because they are cheap insurance on exactly the cases where an LLM slip matters most. The metric can't show their value here.
5. The judge rates the agent (0.94) *above the real human replies* (0.68). That's a warning about the judge, not a result. See §5.

### Judge reliability

- **vs. a stronger judge.** `gemini-2.5-flash` judged 19 items (95 replies) before its free quota ran out (`scripts/06_judge_crosscheck.py`, cache-only). Send-ready agreement: **0.895**. The stronger judge ranks systems the same way but is stricter on the agent (0.89 vs 1.00 send-ready, helpful 3.95 vs 4.63).
- **vs. a human.** `PENDING`: ~51 blind ratings via `scripts/rate.py`. `05_metrics.py` reports Cohen's κ on send_ready/action_ok and Spearman on helpful/grounded.
- **Known judge failure.** Of the agent's 18 over-escalations, the judge marked **12 send-ready**, and it is inconsistent: it sometimes faults "DM us your email" as "asking for personal data publicly". It also passed a plain "DM us" reply to a customer who had posted transaction screenshots (g005). So **escalation correctness is measured against the human labels, not the judge.** The headline uses the judge only for reply quality on tweets that were correctly auto-handled.

## 4. Failure analysis: top 5

Full list: `results/failures.csv` (agent rows with a wrong intent, a missed or extra escalation, or not send-ready).

**F1. Over-escalation by imitating history (18/200; 14 in billing/account).**
- g151 *"I'm having trouble resetting my password, can anyone help"* → "Could you DM us your account's username or email address?"
- g189 *"can I cancel my monthly premium and take out the new annual subscription?"* → DM request. This is a how-to; the public answer is "cancel monthly, then buy annual on the Premium page".

*Hypothesis:* for billing tweets, 67% of the retrieved SpotifyCares replies are "DM us" (even after capping pure "see DM" replies). The few-shot examples outvote the policy text, and E1 ("account-specific action") is vague enough to stretch over how-tos. *Fix to try:* drop pure hand-off examples from retrieval for the reply step, add policy-contrastive examples ("how-to → answer"), and route billing *questions* vs billing *disputes* explicitly.

**F2. Claiming actions the agent never took (5 replies).**
- g135 *"I've sent the DM a while ago, has it been received?"* → "We just sent you a bit more info over DM… **f642**", which is false and ends in a garbage token.
- g186 *"Your site is down"* → "Our developers are looking into this, and we'll keep everyone updated."

*Hypothesis:* retrieved replies narrate actions the human agent had *actually* taken ("we've replied to your DM"), and the model copies the form without the facts. The judge doesn't catch it because the claim is plausible. *Fix:* a post-check regex for state claims ("we've sent / replied / fixed / refunded") that forces a rewrite, plus the same check as a rubric item.

**F3. Outage blindness (11 golden tweets fall in one 50-minute incident on 2017-11-28, 20:44–21:33 UTC).**
- g070 *"is Spotify down? How long has it been down?"* → "Can you let us know what device you're using?"
- g118 *"My [Spotify] is down and I am in DISTRESS"* → "Try restarting your app and checking your connection."

SpotifyCares replied "We had a little hiccup earlier, it should be running now." The agent sees one tweet at a time and has no incident signal. The time split means the knowledge base never saw this outage. *Fix:* a burst detector (spike in "down / not working" tweets over 10 minutes) that flips the playbook to an incident template, gated by a human-confirmed status flag.

**F4. PII and privacy handling is shallow.**
- g005 *"charged twice… The first pic is the monthly card bill. The second pic is the receipts"* → plain "DM us". Spotify's human told them to delete the screenshots.
- g090 is the reverse error: *"I can provide my bank details"* (they didn't post any) → "please delete this tweet since you shared sensitive details".

The agent can't see images, and the guardrail only knows the dataset's anonymisation tokens (`__email__`). *Fix:* treat "pic / screenshot / receipt + `<URL>`" in billing as possible PII; add an OCR step in production.

**F5. Intent confusion on low-information tweets ("other": 72% accuracy).**
- g009 *"is this ever going to be available? \<URL>"* → content_availability.
- g051 *"hey hire me I'm a graphic designer"* → feature_feedback.

Most confusions are between other / feature_feedback / content_availability, which share the same action (auto-reply). So the cost is analytics noise, not customer harm. Part of it is label ambiguity: my own drafts were unsure on several of these.

*Minor:* 2 outputs had `escalate=true` with `escalation_code="none"` (inconsistent structured output). One reply (g117) included a real URL despite the no-links rule.

## 5. What is misleading about my headline number?

"56% safe automation, 0 unsafe" is true under its definitions, and each of these makes it look better than reality:

1. **The labels and the agent share an author: the policy text.** The escalation policy written for labelling is pasted into the agent's prompt. The agent is graded on following instructions it was given verbatim, which is easier than the real question: "is this policy what Spotify's support leads want?".
2. **The labels are AI drafts (for now).** The first-pass labels came from Claude, another LLM. LLMs may share blind spots (e.g. how to read "password reset" under E1), which would inflate agent–label agreement. My hand review records `human_changed` per row; a high change rate would itself be a finding.
3. **"0 unsafe" is 0 out of 86** escalation-worthy tweets, 35 of them from a keyword-oversampled stratum that *looks* risky by construction. The 95% upper bound on the true miss rate with 0/86 is about 3.5% (rule of three). That is not "never".
4. **Send-ready comes from a lenient judge.** It rates the agent above Spotify's real human replies (0.94 vs 0.68). Partly this is real: humans over-used "DM us". Partly it is style bias: an LLM judge favours fluent, LLM-like, slightly longer replies (agent average 137 chars vs 115 historical). It passed 12 of 18 wrongful escalations. A stronger judge scored the agent 11 points lower on the items it could see.
5. **The judge sees the reply, not the outcome.** No customer ever read these replies. "Send-ready" is not "resolved". The historical data shows 28.5% of SpotifyCares' first replies to an opening tweet got a further customer reply; we have no outcome signal for ours.
6. **One week of test data, including an outage.** All golden tweets are from 25 Nov to 3 Dec 2017: Black Friday promos, an annual-plan launch, an outage. Intent mix and failure modes are specific to that window. Today's product (2017 iPhone X / Apple Watch app gaps) has also changed.
7. **Opening tweets only.** Real queues include follow-ups, which are harder and need context.

## 6. What I'd do with one more week

1. **Make the labels mine and measure their reliability.** Have a second person label 50 tweets and report inter-annotator κ for intent and escalation. That is the noise floor any agent metric should be read against.
2. **Calibrate the judge properly.** Get 100+ human ratings, tune the rubric until κ ≥ 0.6, and add a "claims an action / state the agent can't know" criterion (F2). Re-judge with a stronger model on a paid tier (≈$1 total).
3. **Fix F1 and F2 in the pipeline**: retrieval that drops pure hand-off examples for the reply step, contrastive policy examples, a post-generation state-claim checker, and escalation-confidence thresholds tuned on a dev split to trade automation for safety explicitly (a precision–recall curve instead of one point).
4. **Incident mode (F3)**: burst detection over the live stream plus an operator-confirmed status flag.
5. **Bigger, fresher evaluation**: 500+ tweets across several weeks, multi-turn threads, and a shadow-mode plan (the agent drafts, humans send, and we log edit distance and customer follow-up rate as the outcome metric the judge can't give).

## Appendix: reproduce

`README.md`. With the committed cache, `03_run_systems → 04_judge → 05_metrics` regenerates every number in this report in about 2 minutes without an API key.
