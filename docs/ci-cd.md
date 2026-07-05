# CI/CD Pipeline

Six workflows, each with a distinct, deliberate purpose — designed around
one core idea: **cheap checks run on every push; expensive checks only run
right before something risky (merging to main, or releasing).**

```
push (any branch)         → branch-checks.yml     (~5 min)
PR → main                 → merge-gate.yml         (heavy, full e2e)
PR → main                 → codeql.yml             (~15 min, SAST)
PR → main                 → dependency-review.yml  (CVE gate on new deps)
GitHub Release published  → release.yml            (build, push, GitOps bump)
push → main / manual      → security-audit.yml     (OpenSSF Scorecard)
```

## `branch-checks.yml` — Fast Feedback on Every Push

**Trigger:** `push` to any branch except `main`, plus manual dispatch. Since
this is a `push` trigger (not `pull_request`), it also fires on Dependabot's
own branch pushes — giving Dependabot PRs fast lint/test/integration
feedback without needing the heavier `merge-gate.yml` suite.

**Jobs (sequential):**
1. **`lint`** — Pylint (`--fail-under=8.0`) + Hadolint on the Dockerfile.
2. **`test`** — unit tests (`pytest tests/test_app.py -v`).
3. **`integration-test`** — builds the image locally (`push: false, load: true`,
   tagged `:test`), brings up the full stack via `docker compose`, waits for
   `/version` to respond (retries every 5s, 60s total), then smoke-tests
   every endpoint (`/version`, `/temperature`, `/readyz`, `/store`,
   `/metrics`) with `curl -f` so any 4xx/5xx fails the job. Always tears
   down (`if: always()`).



**Design rationale:** this is the workflow that runs constantly, so it's
kept fast (~5 min) and self-contained — no KIND cluster, no Kubernetes at
all, just Docker Compose. It catches most real bugs (bad code, broken
Dockerfile, broken endpoint wiring) before anyone has to wait for the full
e2e suite.

## `merge-gate.yml` — Full Validation Before Merging to `main`

**Trigger:** `pull_request` targeting `main`, plus manual dispatch.


**Jobs:** `lint` → `test` → `build_and_e2e` → `SonarQube`→`terrascan`, all skipped for
`dependabot[bot]` (Dependabot PRs get `branch-checks.yml` +
`dependency-review.yml` + `codeql.yml` instead — deliberately not the full
KIND suite, to keep dependency-bump PRs fast).

**`build_and_e2e`** is the heavy job:
- Builds the image, tagged `pr-<PR#>-<sha>` (never a version tag — those are
  reserved for actual releases via `release.yml`).
- **Trivy scan** — `CRITICAL` severity, `exit-code: 1`, `ignore-unfixed: true`
  — this is where image vulnerability scanning actually happens (not in
  `security-audit.yml`).
- Spins up a real KIND cluster using the project's own `k8s/kind-config.yaml`.
- Patches CoreDNS to forward to `8.8.8.8`/`8.8.4.4` (works around KIND's
  default DNS sometimes failing to resolve external hosts like
  `api.opensensemap.org` inside CI runners).
- Loads the just-built image directly into KIND (`kind load docker-image`)
  — no registry round-trip needed for a PR build.
- Deploys real Nginx Ingress, creates the `hivebox` namespace and
  `minio-credentials` secret (from `MINIO_USER`/`MINIO_PASS` GitHub
  Secrets — the CI equivalent of the manual `kubectl create secret` step
  documented in `docs/helm.md`), deploys infra via Kustomize, then the app
  via Helm — overriding `image.repository`/`image.tag`/`pullPolicy: Never`
  (so it uses the loaded image rather than trying to pull) and
  `metrics.enabled=false` (no Prometheus/ServiceMonitor CRDs in this
  ephemeral e2e cluster).
- Runs **Venom** e2e tests against the live Ingress.
- On failure, dumps pod status/events/logs for debugging.

**`terrascan`** runs after `build_and_e2e` succeeds, scanning both the
Kustomize infra (`k8s/infrastructure/`) and the Helm chart
(`k8s/app/helm/hivebox/`) — `only_warn: true` on both, so misconfigurations
are visible but don't block the merge.



## `codeql.yml` — Static Analysis (SAST)

**Trigger:** `pull_request` to `main` only. Scans Python source for
vulnerability patterns (hardcoded secrets, injection risks, insecure calls)
without executing anything. No dependabot exclusion here — it runs for
every PR to main, dependency-bump PRs included.

## `dependency-review.yml` — Blocks Vulnerable New Dependencies

**Trigger:** `pull_request` to `main` only — this check only makes sense on
PRs, since it diffs the dependency changes a PR introduces against the base
branch. `fail-on-severity: moderate` blocks the PR if any newly-introduced
dependency has a moderate-or-higher CVE, and posts a summary comment on
every PR run (`comment-summary-in-pr: always`) so the result is visible
without digging into workflow logs. This is also the one check that's
directly useful *for* Dependabot's own PRs, unlike the excluded heavy jobs.

## `release.yml` — Continuous Delivery

**Trigger:** `release: types: [published]` (i.e. creating a GitHub Release
via the UI), plus manual dispatch.

**Jobs (sequential):**
1. **`verify-tag-on-main`** — fetches `main`, compares its SHA against the
   triggering commit's SHA, fails if the release tag doesn't point at
   current `main` HEAD. Prevents releasing a tag pushed against a stale or
   unreviewed commit.
2. **`push`** — builds and pushes **three** image tags to GHCR: `:latest`,
   the version tag (e.g. `:v1.0.2`, matching the GitHub Release), and
   `:sha-<commit>` (exact rollback target).
3. **`update-helm-values`** — checks out `main` using `RELEASE_BOT_TOKEN`
   (a PAT, not the default `GITHUB_TOKEN` — needed because this job pushes
   directly to `main`), installs `yq`, bumps `image.tag` and `app.version`
   in `k8s/app/helm/hivebox/values.yaml`, commits as a bot
   (`chore: bump to <tag> [skip ci]`), and pushes. This requires
   `github-actions[bot]` to be on `main`'s branch-protection bypass list —
   the one accepted, deliberate exception, scoped narrowly to this single
   job touching only `values.yaml`.

This is the accepted "GitOps tag gap": the Git tag and `main`'s actual HEAD
diverge by exactly one commit (the bot's `values.yaml` bump) after every
release — a known, intentional tradeoff rather than an oversight.

## `security-audit.yml` — OpenSSF Scorecard

**Trigger:** `push` to `main`, plus manual dispatch — **not currently on a
weekly schedule**, despite that being the intended cadence. Runs the OpenSSF
Scorecard action, which scores the repo (0–10) against supply-chain security
best practices and uploads results as SARIF to GitHub's Security → Code
scanning tab.

> If a weekly cadence is still wanted, this needs a `schedule: - cron: ...`
> trigger added — right now it only runs when something is pushed to
> `main` or manually triggered.

## Dependabot (`.github/dependabot.yml`)

| Ecosystem | Schedule | Grouping | Limit |
|---|---|---|---|
| `pip` | weekly | all minor/patch pip updates grouped into one PR (`pytest` excluded — reviewed individually) | 5 open PRs |
| `github-actions` | weekly | all Actions version bumps grouped into one PR | 5 open PRs |
| `docker` | weekly | **not grouped** — each base image bump reviewed as its own PR | 3 open PRs |

Docker base image bumps are deliberately kept separate from the grouped
pip/actions updates — a base image change is higher-risk (affects the whole
runtime) and worth reviewing individually rather than bundled with routine
dependency bumps.

## Shared Design Choices Across Workflows

- **`harden-runner` on every job** — audits outbound network traffic from
  the runner for visibility, consistently applied across all six workflows.
- **Pinned action SHAs everywhere** (not `@v4` tags) — protects against a
  tag being force-moved to malicious code upstream; version is kept as a
  trailing comment for readability.
- **`concurrency` + `cancel-in-progress`** on `merge-gate.yml`,
  `release.yml`, and `branch-checks.yml` — a new push/PR update cancels the
  previous in-flight run on the same ref, avoiding wasted runner minutes on
  superseded commits.
- **Image tagging strategy is deliberately different per context**:
  `pr-<number>-<sha>` for PR builds (never resembles a real version),
  `:test` for branch-checks' local-only build, and `:latest` /
  `:<version>` / `:sha-<commit>` only for actual published releases —
  keeping "this was just tested" and "this is a real release artifact"
  visually and structurally distinct at the tag level.