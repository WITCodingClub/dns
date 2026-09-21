# Contributing

Thank you for helping run the club's DNS. This file covers the rules. The
[README](./README.md) covers how to add a record.

## For everybody

1. Fork the repository and make your change on a branch.
2. One pull request does one thing. Do not add three unrelated subdomains in
   one pull request.
3. Keep records in alphabetical order inside a zone file.
4. Give every record an owner in a comment on the same line as its name.
5. Read the `octoDNS plan` comment on your pull request before you ask for a
   review. It is the exact list of changes the merge will make.
6. Answer review comments on the same pull request. Do not close it and open a
   new one.

### Commit messages

Use [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: add docs.witcc.dev for the club handbook
fix: point api.witcc.dev at the new host
chore: bump octodns to 1.14.0
```

Pull requests are squash merged, so the pull request title becomes the commit
message on `main`. Write the title the same way.

## For DNS Managers

You are on the [DNS Managers
team](https://github.com/orgs/WITCodingClub/teams/dns-managers). A pull request
cannot merge without an approving review from one of you.

### Reviews go round the team

A workflow asks one person per pull request, in rotation. The rotation is
[`.github/dns-reviewers.txt`](./.github/dns-reviewers.txt). It skips the author
of the pull request.

Being asked does not make it only your job. Anybody on the team can approve.
If you cannot get to a review, say so on the pull request so that somebody else
picks it up.

To change the rotation, edit the file and open a pull request. Comment out a
line to pause somebody. Add a line to bring somebody in.

### What to check in a review

- **Read the plan comment.** It is the truth about what merging will do. The
  diff is not. A small diff can produce a large plan.
- **Does the record have an owner?** Reject it if not. An unowned record is one
  nobody can clean up later.
- **Does the name belong to a club thing?** See the README.
- **Does the plan delete anything?** A delete that the author did not mention
  is the most common sign of a mistake or a stale branch.
- **Did the pull request touch `config/`, `bin/`, `.github/` or `tools/`?**
  Those are not in the plan comment. Read them by hand.

Approve, then squash merge. The deploy runs by itself.

### Never change DNS in the Cloudflare dashboard

Use a pull request. A dashboard change is invisible to everybody who is not
looking at the dashboard, and the next deploy would undo it.

The nightly sync catches a dashboard change and opens a pull request for it.
That is a safety net, not a workflow. Treat a `cloudflare-drift` pull request
as a thing to explain, not a thing to rubber stamp.

If you need an emergency change and you cannot wait for a review, make it in
the dashboard, then say so in the club Discord straight away. Merge the sync
pull request the next morning.

## Changing the tooling

`tools/` has tests. Run them and keep them passing:

```console
$ python -m unittest discover -s tools -p 'test_*.py' -v
```

Add a test with any change to `tools/merge_live.py`. That script edits the zone
files by itself every night, so a bug in it is a bug in production DNS.

Never loosen the security note at the top of
[`.github/workflows/plan.yml`](./.github/workflows/plan.yml) without
understanding it. That workflow can read secrets on a pull request from a fork.
