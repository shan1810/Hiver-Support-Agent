# Helper guide: checking tweets and rating replies

Thanks for helping! No coding needed. You'll read customer tweets sent to Spotify's support account and answer simple questions about them. You only need the keyboard: type a number or letter and press **Enter**.

**Total time:** about 1.5 hours. You can stop at any time; your work is saved after every answer.

---

## Start

1. Open the folder **D:\Hiver** in File Explorer.
2. Double-click **`review.bat`**. A black window opens with a menu.
3. Type a number and press **Enter**.

> If you see red error text, close the window, open `review.bat` again, choose **4** (setup), wait for it to finish, then try again.

---

## Task 1: Check the labels (menu option 1)

You'll see one customer tweet at a time, with a **suggested answer** made by a computer. Your job is to say whether the suggestion is right.

Each tweet looks like this:

```
[g020] (random)  CUSTOMER: I cancelled my subscription but was still charged 🙁
          historical reply: Hi there! Can you DM us your account's email...
   draft -> 1 billing_payment  E1
   Enter=accept | '<n> <code>' | q >
```

The suggestion is the line `draft -> 1 billing_payment E1`. It has two parts:

**Part A: What is the tweet about?** (the number and word)

| # | Topic | Examples |
|---|---|---|
| 1 | billing_payment | charged, refund, payment failed, cancel, prices, special offers |
| 2 | plan_student_family | student discount, family plan invites/members/address |
| 3 | account_access | can't log in, forgot password, email/Facebook login |
| 4 | account_security | **hacked**, a stranger is using my account |
| 5 | playback_technical | app broken, songs won't play, downloads, Spotify is down |
| 6 | content_availability | a song/album/artist is missing or not out yet |
| 7 | feature_feedback | "please add…", complaints about how the app works, compliments about the app |
| 8 | other | too vague, "check my DM", jokes, "when will you launch in my country?" |

Small rules: if the tweet is about **money**, pick 1, even if it mentions student/family. If **someone else is in the account**, pick 4.

**Part B: Can a robot answer it, or does it need a human?** (the code)

| Code | Meaning |
|---|---|
| **A** | A robot can answer it publicly (how-to question, missing song, feedback, praise, vague tweet) |
| **E1** | A human must look at the person's account (refunds, wrong charges, fixing their plan, recovering an account) |
| **E2** | Security: hacked account, or the person posted private info (email, card number) |
| **E3** | Risky: angry legal threats, fraud, very upsetting situation, "your support failed me again and again" |
| **E4** | Not written in English |

Ignore the "historical reply" line when deciding. It shows what Spotify actually did, which was not always right.

### What to type

- Suggestion is **right** → just press **Enter**.
- **Topic** is wrong → type the topic number, e.g. `3`, then Enter.
- **Code** is wrong → type the code, e.g. `A`, then Enter.
- **Both** are wrong → type both with a space, e.g. `3 E1`, then Enter.
- Want to **stop** → type `q`, then Enter. Next time it continues where you left off.

When unsure, go with your gut. Don't overthink it.

---

## Task 2: Rate the replies (menu option 2)

You'll see a customer tweet and a **reply** someone wrote. You won't be told who wrote it (robot or human); that's on purpose. Answer four questions:

| Question | Type | Meaning |
|---|---|---|
| **grounded 1-5** | a number | Is everything in the reply true and safe? **5** = nothing made up. **1** = makes up facts or promises (like "we refunded you" or "it's fixed"). |
| **helpful 1-5** | a number | Does it deal with *this* person's problem? **5** = clear answer or next step. **3** = generic but okay. **1** = misses the point. |
| **action_ok y/n** | `y` or `n` | Did it do the right thing? Account/money/hacked problems should go to a private message (DM). Simple questions should be answered right there. |
| **send_ready y/n** | `y` or `n` | If you were Spotify's support manager, would you send this reply exactly as it is? |

Type `q` at any question to stop and save.

---

## Task 3: Calculate the results (menu option 3)

When both tasks are done, choose **3**. It takes about a minute and says **Done!** Then choose **5** to quit.

That's it. Tell the owner you're finished. 🎉
