Channel added to eval, 29 Oct 2026
Channel 31% -> 96% after: fixing 9 sheet labels, restricting channel to in_store/online/both (enum),
and a clearer rule (bookfairs = in_store, "valid for webstore orders" = online)
Finding: when the main model was busy, the fallback (flash-lite) missed 1 of 3 BookXcess promos.
Fallback answers are no longer cached, so the main model is retried next time.
Tech filter eval, 31 Oct 2026
Precision 4/4 = 100% | Recall 4/4 = 100% (13 events, labelled blind before running)
Rule: tech = mainly about software, AI, data, security, hardware, digital design, or a dev community;
startup/business events only if tech is the main focus. Startup School labelled not tech because [your reason].
Caveat: small set, only 4 tech events and 1 borderline case. Most cases were easy (dance vs. AI agents).
## 12 Nov 2026: switched to a pinned model
Main model: gemini-3.6-flash | Fallback: gemini-3.5-flash-lite
Why: gemini-flash-latest (a nickname that always points to the newest Flash) was overloaded for days,
and a nickname can change model without warning. Pinned a specific model instead.
Also added the model name to the cache key, so a different model's answers are never reused.

Bookstore promos (29 promos, 11 Oct snapshot + banner images)
Recall 100% | Precision 100% | Dates 100% | Key details 100% | Channel 28/29 = 97%
- Only error: MADANI voucher channel. The model says "online"; the sheet says null, because the page
  only says the voucher is obtained "Via Kota Buku". A judgement call, not a clear mistake.

Tech filter (13 Luma KL events, labelled before running)
Recall 4/4 = 100% | Precision 4/5 = 80%
- Only error: Startup School Malaysia 2026 picked as tech (my label: not tech).
  The prompt fix that solved this on gemini-flash-latest doesn't fully hold on gemini-3.6-flash.
- Decision: not changing the prompt again for one borderline event. That would be overfitting
  a 13-event test set. Revisit once the test set is bigger.
## 13 Nov 2026: orchestra/workshop classifier test set (gemini-3.6-flash)
90 CloudJoi events, labelled from the event pages before running the model.
Label fixes after checking pages: Etsy 101, public speaking bootcamp, D&D, Huayuetuan talk,
Rainforest Wellness Weekend, Simple Mind workshop, Holiday Playground -> none (rules say no
business/career courses, games nights, talks or fairs). Mini Paint Jam -> workshop.

Before (homepage data only): orchestra recall 1/4, precision 100% | workshop recall 7/7, precision 100%
Problem: for "The 9th" the model only saw "Category: Music". Missing information, not bad reasoning.
Fix: read each vague-category event's page summary once and cache it forever.
After: orchestra recall 3/4, precision 100% | workshop recall 7/7, precision 100% | overall 89/90
Remaining: Calista Lim (opera + Broadway recital, borderline). Mini Paint Jam: [what its summary says].

## 19 Nov 2026: added video_games kind (gemini-3.6-flash), regression check
Orchestra 3/4, precision 100% | Workshop 6/7, precision 100% | Video games: 0 false picks | Overall 88/90
Echoes of Light & Memory (Final Fantasy music, orchestra) stayed under orchestra - the new rule works.
Mini Paint Jam flipped to none. Its whole page summary is "Let's Paint! (and Play?)", so it's
borderline with very little information. It has flipped before; not tuning the prompt for it.

## 19 Nov 2026: regression check after "skip sales abroad" rule (gemini-3.6-flash)
Recall 100% | Precision 100% | Dates 100% | Key details 100% | Channel 28/29 = 97% (MADANI, as before)
No change from the baseline. Model was busy, not out of quota: the patient retries succeeded on the 4th try.