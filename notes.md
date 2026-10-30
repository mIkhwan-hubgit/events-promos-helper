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