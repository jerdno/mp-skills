---
name: api-contract-change
description: >
  Use when the user asks to add, change, or remove part of an API contract that lives in a
  shared schemas repository and is consumed by other repositories through generated packages —
  covers both REST/OpenAPI (endpoints, request/response models, generated SDK clients/servers)
  and GraphQL (queries, mutations, types, fields, enums, resolvers, a merged schema, a
  frontend's .graphql operations). Also triggers on deprecating fields, bumping a contract or
  schema version, or creating a new API version — even when the user never says "contract",
  "OpenAPI", or "schema".
---

# API Contract Change Workflow

This skill guides you through the end-to-end process of changing an API in projects that split
the contract and its consumers into separate repositories. Changes are **contract-first**: they
start in the schemas repository and flow into every consuming repository through generated
packages. The multi-PR approach keeps generated code in sync with the contract everywhere.

The workflow below is protocol-agnostic. The protocol-specific half — where contracts live, how
to edit and version them, the breaking-change process, and each consumer's update steps — lives
in two reference files in this skill folder:

- [OPENAPI.md](OPENAPI.md) — REST/OpenAPI contracts consumed via generated SDKs
- [GRAPHQL.md](GRAPHQL.md) — GraphQL schemas consumed by a server (resolvers) and clients
  (generated operations/hooks)

> **Project conventions are NOT in this skill.** Version policy (semver vs. minor-only), branch
> naming, commit message format, ticket prefixes, and CI workflow names belong in the project's
> `CLAUDE.md` / `AGENTS.md`. Follow whatever the project documents; if nothing is documented,
> follow what `git log` and recent merged PRs show.

## Overview

Every API change follows this sequence, **in order**:

1. Discover the project configuration and read the protocol reference file
2. Modify the contract in the project's schemas repository
3. Commit, push, and **open a PR** on the schemas repo — pushing alone usually does not trigger
   the generation workflow; the `pull_request` event is typically required
4. **Wait for the generation workflow to finish successfully** and publish the SNAPSHOT
   artifacts to the project's package registry
5. Only then update the consuming repositories to the new SNAPSHOT
6. Open one PR per consuming repo, each referencing the contract PR

**The order of these steps is mandatory — it is not a suggestion.** You cannot start consumer
implementation before the generated artifacts are available. The build will fail to resolve the
new types, types will be missing in your IDE, and any code you write against types that "should
exist" will be guesswork. Never skip the contract step — even for "small" changes. The generated
packages are the source of truth for request/response types across all consumers.

---

## Step 0: Discover Project Configuration

Before doing anything else, locate the schemas repository for the current project.

### Read the projects config

The skill stores per-project repository layouts in `~/.claude/api-projects.json`. Read it first:

```bash
cat ~/.claude/api-projects.json 2>/dev/null
```

Expected structure:

```json
{
  "projects": {
    "<project-name>": {
      "repositories": [
        "/absolute/path/to/contracts-repo",
        "/absolute/path/to/some-service",
        "/absolute/path/to/web-client"
      ],
      "schemas_repository": "/absolute/path/to/contracts-repo",
      "registry_login_command": ["<command to refresh registry token>", "<optional additional command>"]
    }
  }
}
```

`registry_login_command` may be a single string **or a list of commands**. When present, run
**every** command in order (see Step 3). A consuming repo's `CLAUDE.md` can override this: if it
documents a specific setup/registry command, run only that one.

### Identify the current project

Resolve the git root of the current working directory and match it against each project's
`repositories` list:

```bash
git rev-parse --show-toplevel
```

If exactly one project's `repositories` list contains the git root, that's the current project —
use its `schemas_repository` path and `registry_login_command`.

### If the config is missing or the current repo is not registered

Run an ad-hoc setup. Ask the user, in order:

1. **Project name** — short identifier (e.g., `acme-platform`). If a config already exists, list
   the known projects and ask whether this repo belongs to one of them or to a new one.
2. **Schemas repository path** — absolute path to the repository that holds the API schemas
   (OpenAPI and GraphQL typically live in the same repo). If the current repo IS the schemas
   repo, use the current path.
3. **Other consumer repos** (optional) — absolute paths to the other repositories in the same
   project that consume the schemas: services, a GraphQL server, web/mobile clients. Can be
   left empty and added later.
4. **Registry login command(s)** (optional) — the shell command(s) that refresh the auth token
   for the package registry that hosts the generated packages (e.g., `aws codeartifact login
   --tool gradle ...` or `--tool npm ...`, or a project-specific wrapper). May be a single
   string, or a **list** when a project needs several (all are run, in order). Leave empty if
   there is no token to refresh.

Then write `~/.claude/api-projects.json`, creating the file or merging into the existing one.
**Always show the user the final config and confirm before writing.**

### Determine the protocol

Decide from the user's request (endpoints, OpenAPI specs, SDK clients vs. queries, mutations,
resolvers, `.graphql` operations) and confirm against the schemas repo layout (an `openapi/`
vs. a `graphql/` tree).

**Then read the matching reference file — [OPENAPI.md](OPENAPI.md) or [GRAPHQL.md](GRAPHQL.md)
— in full before touching the contract.** Its sections are numbered to match the steps below;
each step here states the shared mechanics and delegates the protocol specifics to the matching
section of the reference file.

### After discovery

You now have:

- `<schemas-repo>` — absolute path to the schemas repository
- `<registry-login-command>` — the registry refresh command(s): a string, a **list** (run all
  in order), or empty
- The protocol reference file, read in full

The rest of this skill assumes all three. Use `<schemas-repo>` for all `cd` commands into the
schemas repo. Consumer repo paths are looked up from the same project's `repositories` list
(ask the user which is which if it's not obvious from naming).

---

## Step 1: Modify the Contract

Work inside `<schemas-repo>`. The reference file's **Step 1** section covers where the contract
files live, which file to edit, and the change patterns for common edits.

### Bump the version

Every contract change requires a version bump — the reference file says where the version lives
and what scheme is typical. Projects commonly enforce the bump in CI; PRs without one will
fail. **Follow the project's documented version scheme.**

**If working on a branch that already has a PR open**, do not bump again — a single bump
compared to the default branch is enough. The new snapshot overwrites the existing one. Check
first:

```bash
git diff origin/HEAD -- <version-file> | grep -i version
```

### Breaking changes need their own process

A breaking change is never just a bigger version bump. Each protocol has a dedicated process —
a side-by-side major-version release for OpenAPI, a deprecate → migrate → remove cycle for
GraphQL — described in the reference file's **Breaking changes** section. Follow it from the
start; retrofitting it after the edit is rework.

### Make the changes

Apply the reference file's change patterns, then regenerate any committed artifacts it calls
for (e.g., a merged schema) — a pre-commit hook commonly blocks the commit when they are out of
sync with the source.

### Run local checks, commit, push

Before pushing, run whatever full check the schemas repo documents (commonly `npm run
checkAll`) — it catches typos, validation errors, and breaking-change flags early. Then commit
and push following the project's branch and commit conventions.

---

## Step 2: Open the Contract PR and Wait for CI

**Opening the PR is mandatory — it is what triggers artifact generation** on most setups. The
generation workflow typically runs on the `pull_request` event, not on branch push. Until the
PR exists, no SNAPSHOT is produced and the consumers have nothing to resolve.

Open the PR immediately after pushing, using whatever PR convention the project uses
(`gh pr create`, GitLab MR, etc.). The reference file's **Step 2** section lists which
workflows run, what they publish, and what the SNAPSHOT version strings look like.

Check workflow status with `gh pr checks <pr-number> --watch` or the project's equivalent.

**Do not proceed to Step 3 until every workflow succeeds** and you know the exact SNAPSHOT
version published to the registry. Starting implementation before the artifact exists forces
rework — wait for the green check.

---

## Step 3: Update the Consumers

**Prerequisite: the contract PR is open and its generation workflow has finished
successfully.** If either condition is not met, go back to Step 2 — the SNAPSHOT artifacts
required below do not exist yet.

The reference file's **Step 3** section names the consumers (a consuming service for REST; the
GraphQL server, then its clients, for GraphQL) and their update order. Run the sub-steps below
once per consuming repo.

### Refresh the registry token (if applicable)

If the project's config includes a `registry_login_command`, run it before installing or
building — tokens for private registries often expire (e.g., AWS CodeArtifact tokens expire
every ~12 hours).

`registry_login_command` may be a single string or a **list**. Run **every** command in the
list, in order.

**Override:** if the consuming repository's `CLAUDE.md` documents a specific setup/registry
command (e.g. in its Commands section), run **only that one** instead of the list — the repo's
own docs win. Skip this sub-step entirely if neither the config nor the repo documents a
command.

### Update the dependency and implement

Bump the contract/schema dependency in the consumer's build file to the new SNAPSHOT version
and install. Package names, install commands, the refresh quirk for re-published SNAPSHOTs, and
the implementation conventions (controllers, resolvers, client operations) are in the reference
file's **Step 3** section.

### Verify the build

Run the repo's standard check command (e.g., `./gradlew build`, `npm run checkAll`,
`mvn verify`).

If the build fails with a dependency resolution error, verify:

1. The contract CI workflow completed successfully
2. The registry token is fresh (re-run the registry login command(s) if applicable)
3. The version in the build file matches the exact SNAPSHOT string in the registry

---

## Step 4: Open the Consumer PRs

Create a branch and PR in each consuming repo following the project's conventions. **Always
reference the contract PR** in each consumer PR description — it keeps the PRs traceable as a
single logical change and shows reviewers the full scope.

Typical body content:

```
Implements the contract changes from <contract-PR-link>.

Depends on: <contract-PR-link>
```

---

## After All PRs Are Approved

Once every PR is approved and ready to merge:

1. Merge the **contract PR first** — this publishes the release (non-SNAPSHOT) versions of the
   generated packages to the registry
2. Update each consumer PR to reference the **release version** (remove the
   `-SNAPSHOT[.<timestamp>]` suffix), re-run the install and commit the updated lockfile where
   the ecosystem has one, push, and wait for CI to go green
3. Merge the **consumer PRs**

This ordering ensures consumers always depend on a published release artifact in production.

---

## Improve This Skill

If you run into a blocker, a gotcha, an unexpected CI behaviour, or a missing step while working
through this skill, **fix it and update this skill before finishing the task**. The skill should
encode every hard-won detail so the next person (or the next session) doesn't have to rediscover
it.

Route each lesson to its single home:

- **Shared machinery** — the projects config, registry login, PR/CI mechanics, merge order —
  belongs in this file.
- **Protocol specifics** — contract editing, breaking changes, consumer implementation —
  belong in the matching reference file, [OPENAPI.md](OPENAPI.md) or [GRAPHQL.md](GRAPHQL.md).
- **Project-specific details** — add them to the config schema (and document the field here) or
  note them in the project's `CLAUDE.md`.

Self-improvement is part of the workflow — not an afterthought.
