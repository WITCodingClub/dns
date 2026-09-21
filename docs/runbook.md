# DNS runbook

For DNS Managers. It covers the one time setup and the things that go wrong.

## One time setup

Do these in order. The order matters twice over. A required check that has
never run on `main` blocks every merge. And the zone files do not yet hold what
Cloudflare holds, so the drift check fails until the first sync pull request
lands.

> **The zone files are nearly empty and Cloudflare is not.** As of this
> writing, `witcc.dev` has 14 records in Cloudflare and one in the zone file.
> `hackwit.org` has 4 records in Cloudflare and none in the zone file. Those
> include the `MX`, SPF, DMARC and DKIM records for club email. Step 3 is what
> fixes this. Do not run `./bin/sync --force` before it.

### 1. Secrets

| Secret | What it is | Used by |
|---|---|---|
| `CLOUDFLARE_TOKEN` | Cloudflare API token, **edit** DNS for both zones | `deploy` |
| `CLOUDFLARE_TOKEN_READ_ONLY` | Cloudflare API token, **read** DNS for both zones | `plan`, `sync-from-cloudflare` |
| `DNS_BOT_PRIVATE_KEY` | Private key of the WITCC DNS Bot GitHub App, the whole `.pem` | `sync-from-cloudflare` |

There is also one repository **variable**, not a secret:

| Variable | What it is |
|---|---|
| `DNS_BOT_CLIENT_ID` | Client ID of the same App. An identifier, not a credential |

The two Cloudflare tokens already exist. Create them at
**Cloudflare > My Profile > API Tokens** with the `Edit zone DNS` template, and
scope each one to `witcc.dev` and `hackwit.org` only.

> **Rotate `CLOUDFLARE_TOKEN_READ_ONLY` once.** The workflow it replaces ran
> scripts from a pull request while holding it, so anybody who opened a pull
> request could have read it. See [`SECURITY.md`](../SECURITY.md).

### 1b. The bot App

The nightly sync opens its pull request as a GitHub App. Two reasons, and both
of them rule out the simpler options:

- **Not `GITHUB_TOKEN`.** GitHub does not start workflows for commits pushed
  with the built in token, so that pull request would get no checks and could
  never satisfy a required check.
- **Not a person's token.** Nobody can approve their own pull request. If the
  sync ran on a DNS Manager's personal access token, every sync pull request
  would be authored by that person and they could never review it. On a two
  person team that leaves exactly one possible reviewer.

An App is neither. It triggers checks, and it is not a person, so anybody on
the team can approve its pull requests. It also has no expiry to forget.

1. Go to
   <https://github.com/organizations/WITCodingClub/settings/apps/new>.
2. **Name**: `WITCC DNS Bot`. **Homepage URL**: this repository is fine.
3. Turn **Webhook > Active** off. The App never receives events.
4. **Repository permissions**: `Contents: Read and write`,
   `Pull requests: Read and write`, `Issues: Read and write`. Nothing else.
5. **Where can this App be installed**: only this account.
6. Create it, then **Generate a private key**. A `.pem` downloads.
7. **Install App** on the left, install it on `WITCodingClub/dns` only. The App
   can do nothing until this step.
8. Record the client id and the key:

   ```console
   $ gh variable set DNS_BOT_CLIENT_ID --repo WITCodingClub/dns --body 'Iv23...'
   $ gh secret set DNS_BOT_PRIVATE_KEY --repo WITCodingClub/dns < ~/Downloads/witcc-dns-bot.*.pem
   ```

   The client id is on the App's settings page. The private key is the whole
   `.pem` file, `BEGIN` and `END` lines included.
9. Delete the `.pem` from your Downloads folder.

To check that it worked:

```console
$ gh api orgs/WITCodingClub/installations --jq '.installations[].app_slug'
$ gh workflow run sync-from-cloudflare.yml && gh run watch
```

### 2. Team access

The `dns-managers` team needs **write** access or better on this repository.
GitHub ignores a `CODEOWNERS` entry for a team that cannot write.

```console
$ gh api orgs/WITCodingClub/teams/dns-managers/repos/WITCodingClub/dns \
    --jq .permissions
```

### 3. Pull Cloudflare into git

Run the nightly sync by hand, then review and merge the pull request it opens.
Expect it to be large. Cloudflare holds the real records today.

```console
$ gh workflow run sync-from-cloudflare.yml
$ gh run watch
```

Give every record marked `TODO owner unknown` an owner before you merge.

Once it has merged, confirm that Cloudflare and `main` agree:

```console
$ export CLOUDFLARE_TOKEN=...   # the read-only token
$ ./bin/plan
```

It should print `## No changes were planned`. Until it does, the
`cloudflare in sync` check fails on every pull request, which is the point.

### 4. Required checks and code owner review

**This is already applied.** Ruleset `23783065` on `main` requires one
approving review from a code owner, squash merge, resolved review threads, and
these five checks:

`yaml syntax`, `dns records`, `tools tests`, `plan the change`,
`cloudflare in sync`.

`docs/ruleset-main.json` is a copy of it. Restore it with:

```console
$ gh api -X PUT repos/WITCodingClub/dns/rulesets/23783065 \
    --input docs/ruleset-main.json
```

Read it back with:

```console
$ gh api repos/WITCodingClub/dns/rulesets/23783065 --jq '.rules[] | select(.type=="pull_request" or .type=="required_status_checks")'
```

> **The ruleset went on before the workflows did.** `plan.yml` runs on
> `pull_request_target`, which reads the workflow from `main`. Until it is on
> `main`, `plan the change` and `cloudflare in sync` never start, so any pull
> request open right now waits on checks that cannot run. A repository admin
> has `bypass_mode: always` and can merge the first one anyway. Every pull
> request after that gets real checks.

The nightly schedule starts by itself once the workflow is on `main`. There is
nothing else to turn on.

## The checks

### `cloudflare in sync` failed

Cloudflare does not match `main`. Somebody changed DNS in the dashboard, or a
deploy failed.

1. Look at the failed check. It prints the difference.
2. If there is an open `cloudflare-sync` pull request, review and merge it.
3. If there is not, make one:

   ```console
   $ gh workflow run sync-from-cloudflare.yml
   ```

4. Re-run the failed check on the blocked pull request.

Do not merge past this check. Merging undoes whatever is in Cloudflare and not
in `main`.

### `plan` failed

Read the workflow log. The usual causes:

- **A record is not valid.** octoDNS names the record and says why.
- **The Cloudflare token expired.** The log shows a 401 or 403 from the API.
- **A root `NS` change.** octoDNS refuses these without `--force`. Cloudflare
  owns the nameservers for a zone. The zone files must not contain root `NS`
  records. `tools/merge_live.py` leaves them out for this reason.

### `deploy` failed

The zone files and Cloudflare now disagree. Fix it, do not leave it.

- **`Too many deletes`.** The deploy refuses a plan that deletes more than
  `MAX_DELETES` records. Read the plan in the job summary. If every delete is
  correct, run the deploy by hand:

  ```console
  $ gh workflow run deploy.yml -f allow_mass_delete=true
  ```

  This guard exists because octoDNS's own guard has a hole. octoDNS refuses a
  plan that updates or deletes more than 30% of a zone, but only for a zone
  that already has at least 10 records. `MIN_EXISTING_RECORDS` is a constant in
  octoDNS and cannot be configured. `hackwit.org` has fewer records than that,
  so octoDNS would delete every one of them without complaining.

- **`TooMuchChange`.** This is octoDNS's own guard, for a zone with 10 records
  or more. Read the plan. If the change really is correct, apply it by hand:

  ```console
  $ export CLOUDFLARE_TOKEN=...   # the edit token
  $ ./bin/plan                    # read this first
  $ ./bin/sync --force
  ```

- **Rate limited.** octoDNS retries five times and waits ten minutes. Re-run
  the workflow.
- **The apply half finished.** Run the `deploy` workflow again. octoDNS works
  out what is left to do.

## Common jobs

### Roll a Cloudflare token

1. Create the new token in Cloudflare.
2. Update the repository secret.
3. Run `gh workflow run deploy.yml` and confirm it passes.
4. Delete the old token in Cloudflare.

### Add somebody to the rotation

1. Add them to the `dns-managers` team.
2. Add their GitHub username to `.github/dns-reviewers.txt` in a pull request.

### Remove a subdomain

Delete the record from the zone file in a pull request. The deploy removes it
from Cloudflare. Tell the owner first.

### Check that a deploy landed

```console
$ dig +short TXT octodns-meta.witcc.dev
```

The `time=` value is when octoDNS last changed that zone.

### See the live Cloudflare state

```console
$ export CLOUDFLARE_TOKEN=...   # the read-only token is enough
$ ./bin/dump .live
$ cat .live/witcc.dev.yaml
```

`.live/` is ignored by git. It never touches the zone files.

## If everything is broken

DNS for both zones is in Cloudflare. Cloudflare is the live system. This
repository is how we change it, not how it serves.

1. Fix the record in the Cloudflare dashboard. The site comes back.
2. Post in the club Discord that you did it.
3. Run `gh workflow run sync-from-cloudflare.yml` and merge the pull request it
   opens, so the repository catches up.
