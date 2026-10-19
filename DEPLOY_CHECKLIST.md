# Public source / private site launch checklist

- [ ] NEW PUBLIC GitHub source repo created, no API keys or personal raw data committed
- [ ] Streamlit viewer access explicitly changed from public default to PRIVATE; restricted to your approved account
- [ ] Dedicated passphrase hashed and secret set (run `python setup_password.py`)
- [ ] Unauthorized viewers and incorrect passphrase rejected
- [ ] Site added to iPhone Home Screen
- [ ] Supabase tables provisioned with RLS enabled; no public policies
- [ ] Supabase service-role secret stored ONLY server-side
- [ ] DK/FD market API entitlement confirmed, usage limits checked
- [ ] Manual odds refresh executes and snapshots two-sided valid quotes with provider timestamps
- [ ] Scheduler cadence enabled only after checking paid API quota
- [ ] Frozen V3 champion/challenger study run and evidence reviewed
- [ ] New prediction job produces independently checked pregame player/event matches
- [ ] All model forecasts remain research-only until explicit promotion
- [ ] NHL final boxscore grading and closing odds ledger implemented separately
- [ ] 30+ days prospective paper test before any money is risked
