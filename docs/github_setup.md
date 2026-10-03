# Push the Group 11 GitHub repository

The repository now exists at https://github.com/hsimsek1/secure-art-gallery-group11. It is public and currently empty. The local project is ready to push. No collaborator permission or Canvas submission was created automatically.

1. Confirm that you are signed in to the `hsimsek1` GitHub account and that the empty repository URL is correct. Choose visibility according to the course instructions before pushing.
2. Invite Gustavo and the instructor if course instructions require them. Confirm that your partner can access the repository.
3. In PowerShell, enter this project's directory and review files before committing. A local repository may already have been initialized by this preparation; `git init` is harmless if repeated.

```powershell
git init -b main
git check-ignore .env local-credentials.txt instance/gallery.db
git status --short --untracked-files=all
git add .
git diff --cached --name-only
```

The staged list must not include `.env`, `local-credentials.txt`, any database, `.venv`, cache directories or rendered QA images. `.env.example` is safe because all secret fields are empty. `docs/test-results.xml` contains generated test outcomes, not real passwords.

Then make the first commit and connect the repository URL:

```powershell
git commit -m "Implement Group 11 gallery through Week 6"
git remote add origin https://github.com/hsimsek1/secure-art-gallery-group11.git
git push -u origin main
```

Use GitHub's normal authentication prompt; never paste a token into code or the remote URL. If Git requests your identity, configure your own name/email before committing. No identity was invented for you.

4. Open the repository in the browser and verify the required structure, both PDFs, and tests are visible. A GitHub Actions test workflow is supplied; its remote execution is not verified until you push.
5. Follow Canvas instructions for the Phase I PDF and any Week 5/Week 6 deliverables. A successful push is not a Canvas submission.

If a secret is ever committed, deleting the file in a later commit is insufficient. Rotate the affected secret and address repository history before sharing it.
