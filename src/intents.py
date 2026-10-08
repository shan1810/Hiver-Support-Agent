"""Intent taxonomy and escalation policy for SpotifyCares.

Derived by clustering ~12k opening tweets (TF-IDF + KMeans, k=25) and merging clusters
by *what the support agent has to do*, not by topic words. See report/REPORT.md.
"""

INTENTS = {
    "billing_payment": "Charges, double/unexpected billing, refunds, payment failing, paid but Premium not active, cancelling, prices/promos.",
    "plan_student_family": "Student discount verification/renewal, Premium Family invites, addresses, members, plan switching between Family/Student/Individual.",
    "account_access": "Can't log in, password reset, email change, Facebook login, username, duplicate/merged accounts (no sign of compromise).",
    "account_security": "Account hacked/compromised, unknown devices or playlists, someone else using the account, email/password changed by someone else.",
    "playback_technical": "App/web player/desktop bugs, crashes, songs not playing, offline downloads, devices (iPhone X, Apple Watch, TV, car, Connect), ads glitches.",
    "content_availability": "A song/album/artist/podcast missing, greyed out, region-locked, wrong metadata, when will X be released on Spotify.",
    "feature_feedback": "Feature requests, complaints about product decisions (shuffle, ads, recommendations, UI), compliments, general opinions.",
    "other": "Too vague to act on, 'check my DM' nudges, market-launch questions ('when in India?'), jokes, image-only tweets, praise/complaints about support itself.",
}
INTENT_NAMES = list(INTENTS)

# Tie-break rules used when labelling (and given to the model):
TIE_BREAKS = """- Money (charged, refund, wrong price) -> billing_payment, even if it is a student/family plan.
- Membership/verification without a money complaint -> plan_student_family.
- Any sign another person is in the account -> account_security, not account_access.
- Label non-English messages by their content; language is handled by escalation, not intent."""

# Policy the golden escalation labels follow. Written before labelling, refined once during the first pass (see DECISIONS.md #6).
ESCALATION_POLICY = """Escalate to a human when ANY of these hold:
E1 Account-specific action is needed that a public reply cannot do: look up/refund/reverse a charge, change account data, recover an account, fix a plan membership.
E2 Security: suspected hacked/compromised account, or the customer posted personal data (email, card, phone) publicly.
E3 High-risk tone: legal/regulatory threats, fraud claims, harassment, self-harm or distressing personal circumstances, complaints about support staff, or a customer who says previous support already failed them repeatedly.
E4 The message is not in English (we can only verify English replies).
Otherwise auto-handle (a clarifying question is a valid auto-reply for vague messages): general how-to, known troubleshooting steps, content-availability questions, feature feedback, praise, 'check my DM' nudges (acknowledge and route).
Note: asking the customer to DM is itself a form of escalation (a human picks the DM up). An auto-handled reply must be useful on its own."""
