# Group 11 GitHub repository

The project is published at https://github.com/hsimsek1/secure-art-gallery-group11 on the `main` branch. The repository includes the application, tests, design document, and Phase I report. GitHub is separate from Canvas; students must submit any required files in Canvas themselves.

1. Confirm that you are signed in to the `hsimsek1` GitHub account and that the repository URL is correct. Choose visibility according to the course instructions.
2. Invite Gustavo and the instructor if course instructions require them. Confirm that your partner can access the repository.
3. In PowerShell, enter this project's directory and review files before committing subsequent changes.

```powershell
git check-ignore .env local-credentials.txt instance/gallery.db
git status --short --untracked-files=all
git add <files-to-commit>
git diff --cached --name-only
```

The staged list must not include `.env`, `local-credentials.txt`, any database, `.venv`, cache directories or rendered QA images. `.env.example` is safe because all secret fields are empty. `docs/test-results.xml` contains generated test outcomes, not real passwords.

Then commit and push:

```powershell
git commit -m "Describe the change"
git push origin main
```

Use GitHub's normal authentication prompt; never paste a token into code or the remote URL. If Git requests your identity, configure your own name/email before committing. No identity was invented for you.

4. Open the repository in the browser and verify the required structure, both PDFs, and tests are visible. Check the GitHub Actions test workflow after pushing.
5. Follow Canvas instructions for the Phase I PDF and any Week 5/Week 6 deliverables. A successful push is not a Canvas submission.

If a secret is ever committed, deleting the file in a later commit is insufficient. Rotate the affected secret and address repository history before sharing it.
