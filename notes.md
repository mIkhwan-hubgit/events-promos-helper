Channel added to eval, 29 Oct 2026
Channel 31% -> 96% after: fixing 9 sheet labels, restricting channel to in_store/online/both (enum),
and a clearer rule (bookfairs = in_store, "valid for webstore orders" = online)
Finding: when the main model was busy, the fallback (flash-lite) missed 1 of 3 BookXcess promos.
Fallback answers are no longer cached, so the main model is retried next time.