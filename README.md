# True Probability Hammer — Public Source / Private NHL SOG Portal

**Project:** Open-source-ready repository for a separately restricted mobile-first Streamlit site and authenticated research/price-data scaffold derived from the preserved NHL SOG V3 research package.

**Current state (2026-10-18):** Working source code, local automated validation, and static visual preview are packaged. **NOT deployed.** **NOT connected to an account, live sportsbook feed, or scheduled prediction engine.** **NO verified live betting edges or V3 improvement claims.**

## 1. What you get

- `app.py` — five mobile-responsive views: Board, Players, Model, Ledger and Setup; protected by a dedicated scrypt password hash. **A separate hosting-level private-viewer restriction is mandatory.**
- `tph_core.py` — pure Python verified-data gates, price/probability utilities, no-vig comparison and password verification.
- `odds_worker.py` — callable actual NHL SOG odds collector for **The Odds API** `player_shots_on_goal` market and DraftKings/FanDuel only. API key, market entitlements, quota, and coverage required. Not invoked by the browser.
- `storage.py` and `schema/supabase.sql` — append-only price snapshots in backend Supabase/Postgres, RLS enabled with no public policies.
- `publish_forecasts.py` — validates an independently produced forecast CSV, but **always stores it as RESEARCH / data_verified false**, until a human validates/publishes a model. No unchecked “approved” forecasts.
- `.github/workflows/odds_refresh.yml` — manually triggered quote-update action with future cron template deliberately disabled until provider quotas are understood.
- `research/` — **genuine archived Pittsburgh V2** calibration output, 2023–24. Hypothetical fixed-line study, not sportsbook wagers; used only for the Player Lab / health examples.
- `tests/` — security/math/price gate tests. Example players in tests are unit-test fixtures, never live content.

**The original V3 notebook and historical Parquet files were not modified or repackaged into a publicly reachable web app.** Your separate V3 archive remains unchanged.

## 2. Deploy a private site with two layers of protection

This is the lowest-complexity starting point because your previous project already uses Streamlit.

### Stage A — Private code and authentication

1. Run `python -m unittest discover -s tests -v` in this folder. For local UI execution: `pip install -r requirements.txt` then `streamlit run app.py`.
2. Run `python setup_password.py`. Choose a long, unique passphrase and copy the **scrypt hash**, not the password.
3. In a new **PUBLIC GitHub repository**, upload this source only. `.gitignore` protects locally ignored files, but audit staged content before pushing. Never commit `secrets.toml`, API keys, personal tracking files, raw Parquet datasets, or any service-role credentials. Public code does **not** grant viewers app access if hosting restrictions are properly enabled.
4. At [Streamlit Community Cloud](https://share.streamlit.io), connect that private repo, main script `app.py`, and create the app. Under app sharing settings, select **only specific people can view**; add your personal email account only. A private repo is not by itself the security boundary: verify *viewer* restrictions.
5. In the app's server-side Secrets, add `TPH_PASSWORD_HASH = "scrypt$..."` exactly as printed by `setup_password.py`.
6. Open your unique Streamlit app URL on your iPhone. The platform first checks your viewer authorization through its login; then the site requests your dedicated passphrase. In Safari, use Share → Add to Home Screen.
7. Verify denial from an unapproved account and verify that the secondary passphrase rejects the wrong password. Never disable either layer for production.

**Security note:** The app password is a secondary convenience gate. Its per-session attempt counter is not a global anti-brute-force control; Streamlit Cloud's private viewer controls are required. For future multi-user access, migrate to a managed identity provider plus server-side authorization. Streamlit sessions and secrets never belong in client-side HTML.

### Stage B — Genuine timestamped DK/FD odds and private storage

1. Create a private [Supabase](https://supabase.com) project. In SQL Editor, run `schema/supabase.sql`.
2. In Streamlit Cloud **Secrets** add `SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY`. Treat this service-role key as highly privileged: do not expose it in JS or public source, and rotate it after leaks.
3. Register a **The Odds API** key, confirm your plan exposes `icehockey_nhl` / `player_shots_on_goal`, and confirm DK/FD book availability. The product's documented endpoint is `/v4/sports/icehockey_nhl/events/{eventId}/odds` with `markets=player_shots_on_goal` and `bookmakers=draftkings,fanduel`.
4. In your **GitHub repo's private Actions secrets**, configure `THE_ODDS_API_KEY`, `SUPABASE_URL`, and `SUPABASE_SERVICE_ROLE_KEY`. Trigger **NHL SOG odds refresh** using workflow_dispatch once to inspect a run. Verify rows in the `sog_prices` table and `sog_refresh_runs` table.
5. **Only after confirming provider billing/quotas**, enable an Actions cron near game start. A frequent all-day cron can consume substantial paid API credits, especially one event-odds call per game. Observe API 401/403/429 and halt appropriately. Choose cadence based on your API budget. A price is *stale* after 15 minutes in the app, regardless of scheduled intent.
6. Keep both sides (Over/Under) of the same book/player/line, timestamps, provider attribution and the quote snapshot. `NULL` or unsupported odds mean unavailable, not zero.

**Be aware:** The odds collector has static correctness tests, but no live authorized API request was executed here. Bookmaker/player-prop coverage may be incomplete, and API quotas apply.

### Stage C — Turn research forecasts into a real daily model

This is **not already complete** in V3, so the deployed dashboard deliberately blocks picks.

1. Run the V3 historical evaluation in Colab using the original Parquet data. Freeze preprocessing, feature versions, hyperparameters, distribution parameters, calibrator, and source checksums.
2. Use a separately scheduled trusted Python forecasting worker (not the web UI) to pull latest **completed-game history** and verified pregame ice-time/lineup inputs, then generate forecasts from the frozen model artifact. **Do not retrain or infer on future/current-game stats.**
3. Give every forecast an immutable `model_version`, provider `event_id` after exact event matching, player identity, game start time, forecast timestamp, line, projected SOG and calibrated Over probability. Do not infer or guess mismatched events. Save candidate forecast rows first as `research`, `data_verified=false`.
4. Validate the complete source lineage, timestamp, historical holdout and prospective model performance. A controlled separate promotion process can change the `model_status` to `approved` and `data_verified=true` after signoff, not through the website or a user-editable field.
5. Match only trusted two-sided DK/FD prices from the same game/player/line, captured **before puck drop and updated within 15 minutes**, to the approved forecast. The app computes model EV, proportional no-vig market probability, percentage-point gap, and clearly distinguishes these metrics.
6. Save every generated paper selection and bankroll decision *before* the game (immutable/append-only). Add official NHL boxscore settlement and CLV capture after games. **Automatic grading and CLV are not implemented in this package.**

`publish_forecasts.py` is an importer and remains research-only by design. Example: `python publish_forecasts.py prospective_forecasts.csv`. It requires columns:

`event_id,game_start_utc,player_name,line,prob_over,forecast_created_utc,model_version` 

Optionally `projected_sog`. Every timestamp must contain UTC offset and the forecast must precede puck drop. Event IDs must match The Odds API, not NHL game IDs.

### Stage D — Long-term reliability / Pizzola-inspired disciplined process

- **Each pregame slate:** Validate injury/lineup, projected TOI, role, opponent suppression, quoted odds age and complete join; do not fill gaps with guesses.
- **After games:** Fetch NHL boxscore skater shots by documented API, link NHL game IDs to forecast event IDs using an independently verified mapping; handle no-shows, voids, scratches and overtime consistently; preserve original predictions.
- **Weekly:** Dashboard diagnostics for data coverage, price freshness, Brier/log loss, reliability curves and calibration by player role/line. Alert on degradation; never auto-rewrite history.
- **Monthly:** Stage one candidate model change at a time (TOI sub-model, PP usage, opponent effect, current-season shrinkage, Poisson-vs-NB dispersion, market shrinkage). Compare prospectively or on pre-registered chronology; preserve the champion.
- **Model promotion:** Require meaningful out-of-sample improvement with uncertainty intervals, stable subgroup diagnostics, correct quote provenance, and no feature leakage.
- **Financial validation:** Track actual profit separately from paper, never treat hits or theoretical EV as cash realized; monitor fees, bet limits, fill ability, and CLV.

## 3. Local run

```bash
python -m pip install -r requirements.txt
python setup_password.py
# Paste hash into .streamlit/secrets.toml as TPH_PASSWORD_HASH = "scrypt$..."
streamlit run app.py
```

The Streamlit app must **not** be exposed publicly without verified authenticated hosting and transport security. A public source repository alone does not make private app data public. If Supabase credentials are missing, the board correctly remains empty; archived player lab works once authenticated.

## 4. Test and verification result

As shipped: `python -m unittest discover -s tests -v` reports **13 passing unit tests**; Python files compiled. Browser/Streamlit interactions were **not run in this environment** because Streamlit is not installed. Quote connector is **not end-to-end tested** against the provider; no API key is available. No model accuracy uplift can be claimed from a UI refresh.

## 5. Source references, reviewed October 18, 2026

- Streamlit private deployments: https://docs.streamlit.io/deploy/streamlit-community-cloud/share-your-app
- Streamlit OIDC alternative: https://docs.streamlit.io/develop/concepts/connections/authentication
- The Odds API NHL props: https://the-odds-api.com/sports/nhl-odds.html
- The Odds API V4 event market details: https://the-odds-api.com/liveapi/guides/v4/
- Supabase Auth and row security: https://supabase.com/docs/guides/auth
- NHL API gamecenter endpoints, unofficial endpoint reference: https://github.com/Zmalski/NHL-API-Reference

**Never interpret empty/live-missing feeds as zero projected probability.** This system explicitly fails closed.


## Public repository / private Streamlit deploy

The GitHub source is intentionally public, but **the Streamlit app must be set to Only specific people can view it before handling private information**. On Community Cloud a site built from a public repository is public by default. The app requires `TPH_PASSWORD_HASH` as a second gate. Verify host-level privacy separately. Follow `PUBLIC_SETUP.md` before publishing anything.
