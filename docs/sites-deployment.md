# Canonical Git and Sites deployment

## Repository roles

- `origin/main` is the only canonical source history. Local `main` tracks it.
- The OpenAI Sites source repository uses its own `main`, but that branch must
  contain the exact same commits as canonical `main`. It is a mirror target,
  not a second place to develop or reconcile changes.
- OpenAI Sites saved versions and production deployments are build artifacts.
  They do not define source history.
- GitHub Pages deploys the `dist-pages` artifact from canonical `main`; it does
  not use a `gh-pages` source branch. It also serves the repository's public
  teaching images at `https://rray1228.github.io/neike-306-tiku/`.
- Sites production uses that GitHub Pages URL as its single external asset
  base. The Sites build deliberately does not copy `public/` into `dist`, while
  local development and the GitHub Pages build continue to use the same source
  images from `public/`.
- Numeric-memory pages under `shared/numeric-memory/` ship with the Site and
  use its own origin. Existing images keep their current CDN addresses.

Never create an orphan commit, initialize a temporary repository, replay a
patch on a snapshot, or force-push a generated tree during normal deployment.

## Safe update and deployment sequence

1. Update and publish canonical source normally:

   ```bash
   git pull --ff-only
   git push
   ```

2. Obtain a short-lived OpenAI Sites source-repository credential. Fetch its
   `main` into `refs/remotes/sites/main` without storing the credential in Git
   configuration.
3. Verify the exact source and history before publishing:

   ```bash
   pnpm run check:deployment-history
   ```

4. Push the current canonical commit to the Sites source repository with a
   normal fast-forward `HEAD:main` push. Do not use `--force` or
   `--force-with-lease` during routine deployment.
5. Build and check the production artifact before upload:

   ```bash
   pnpm run build
   pnpm run check:sites-artifact
   ```

   A result above 30 MiB warns; above 40 MiB fails and must not be uploaded.
6. Package, save, and deploy the Sites version using that exact pushed commit
   SHA. Verify several public image URLs on GitHub Pages before publishing.

The check intentionally fails when either remote ref was not fetched, the two
histories have no merge base, the local source is not exactly `origin/main`, or
the Sites source branch cannot fast-forward. Resolve the source-history problem
instead of bypassing the check.

## Explicit Site release while GitHub writes are unavailable

When the user explicitly requests a public release and GitHub cannot accept
writes, local `main` may be released first to the user-owned Sites source
repository. Preserve the same history: local `main` must descend from both
the last fetched `origin/main` and the fetched Sites source head. Validate the
clean release worktree against that local `main` with
`CANONICAL_REF=main bash scripts/check-deployment-history.sh`, then use only a
normal fast-forward Sites push and publish its exact commit and built archive.
Record GitHub synchronization as pending; later push the same commits normally.
This does not authorize a GitHub write through another account or any force push.
