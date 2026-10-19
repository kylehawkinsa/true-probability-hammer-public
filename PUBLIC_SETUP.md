# Fast GitHub + private Streamlit setup

Source repo name: `kylehawkinsa/true-probability-hammer-public` (chosen to avoid modifying either existing repository).

## Fastest supported publisher: GitHub CLI on a computer or GitHub Codespace

1. Extract the ZIP. Open a terminal **inside the extracted folder**.
2. Install/authorize GitHub CLI (`gh auth login`) if needed.
3. Execute `bash publish_public_repo.sh`. It creates a **new PUBLIC repo** if the name does not exist, commits and pushes the extracted files without changing existing repositories, and runs the tests locally.
4. Open the new repository's **Actions** tab and verify **Verify True Probability Hammer** passes on push. The odds-refresh workflow is manual-only; do not activate it without budget/permission.

## Browser alternative

1. Create an **empty** PUBLIC repository at https://github.com/new using `true-probability-hammer-public` under `kylehawkinsa`. Do not auto-add README, gitignore, or license (the package already has them).
2. On a computer browser, extract this ZIP and upload all files/folders via **Add file > Upload files**. Retain `.github` and `.streamlit` directories; check dotfiles made it into the repository. GitHub doesn't automatically extract ZIP files uploaded through its website.
3. Check the **Actions** tab for the included unit-test workflow.

## Streamlit, private viewer access even though the GitHub code is public

1. Log in at https://share.streamlit.io with GitHub and select **Create app** > **I have an app**. Select your NEW GitHub repo, branch `main`, app path `app.py`.
2. Before putting any real data/credentials in the app, go to **App settings > Sharing > Who can view this app > Only specific people can view this app** and authorize only yourself. A public source repo defaults to a publicly viewable Streamlit app. **Do not assume the app is private automatically.**
3. In the Streamlit server-side **Secrets** settings, add a scrypt hash only: `TPH_PASSWORD_HASH = "scrypt$..."`. Generate it privately using `python setup_password.py`; never place actual passphrases in a public repository.
4. Verify access controls by testing an unauthorized browser/account and a wrong passphrase. Only then attach private databases or provider keys via hosting Secrets, never via GitHub source.
5. Add the Streamlit URL to your iPhone home screen if desired.

## What is verified

- Included offline unit tests cover authentication, price-math, source verification, and pregame gates.
- The dashboard is a research portal. A live NHL SOG model, fresh bookmaker odds, verified picks, and real-money readiness are **NOT** provided by this package.
- Do not run manually triggered odds workflows, enable scheduling, or activate paid APIs without explicit confirmation of provider entitlements and costs.
