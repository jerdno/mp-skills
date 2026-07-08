---
name: api-contract-change
description: >
  Use when the user asks to modify, add, or remove a REST/microservice endpoint, request/response
  model, or OpenAPI contract that lives in a shared schemas repository and is consumed by other
  services via a generated SDK. Triggers on changes to REST service APIs defined as OpenAPI
  specs — adding new endpoints, changing request/response schemas, deprecating fields, or
  creating new API versions — across separate contract and service repositories. Also triggers
  when the user mentions OpenAPI specs, REST contracts, generated SDK clients/servers, or wants
  to update a service's REST API interface — even without saying "contract" or "OpenAPI". Do NOT
  use for GraphQL schema changes — use the graphql-api-change skill instead.
---

# OpenAPI Contract Change Workflow

This skill guides you through the end-to-end process of changing a REST (OpenAPI) microservice
API in projects that split the OpenAPI contract and the service implementation into separate
repositories. REST API changes always start with the OpenAPI contract and flow into the service
implementation through a generated SDK. This two-PR approach keeps generated SDK clients in sync
with service code.

For GraphQL schema changes, use the `graphql-api-change` skill instead.

> **Project conventions are NOT in this skill.** Version policy (semver vs. minor-only), branch
> naming, commit message format, ticket prefixes, and CI workflow names belong in the project's
> `CLAUDE.md` / `AGENTS.md`. Follow whatever the project documents; if nothing is documented,
> follow what `git log` and recent merged PRs show.

## Overview

Every API change follows this sequence, **in order**:

1. Modify the OpenAPI contract in the project's schemas repository
2. Commit, push, and **open a PR** on the contract repo — pushing alone usually does not trigger
   the SDK generation workflow; the `pull_request` event is typically required
3. **Wait for the SDK generation workflow to finish successfully** and publish the SNAPSHOT
   artifact to the project's package registry
4. Only then update the consuming service to use the new SNAPSHOT SDK
5. Open a service PR that references the contract PR

**The order of these steps is mandatory — it is not a suggestion.** You cannot start server or
client implementation before the generated SDK artifact is available. The service build will
fail to resolve the new types, types will be missing in your IDE, and any code you write against
types that "should exist" will be guesswork. Never skip the contract step — even for "small"
changes. The generated SDKs are the source of truth for request/response types across services.

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
        "/absolute/path/to/another-service"
      ],
      "schemas_repository": "/absolute/path/to/contracts-repo",
      "registry_login_command": "<command to refresh registry token, optional>"
    }
  }
}
```

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
   (both OpenAPI and GraphQL typically live in the same repo). If the current repo IS the
   schemas repo, use the current path.
3. **Other consumer repos** (optional) — absolute paths to other repositories in the same
   project that depend on the schemas. Can be left empty and added later.
4. **Registry login command** (optional) — the shell command that refreshes the auth token for
   the package registry that hosts the generated SDKs (e.g., `aws codeartifact login --tool
   gradle --domain ... --repository ...`, or a project-specific wrapper). Leave empty if there
   is no token to refresh.

Then write `~/.claude/api-projects.json`, creating the file or merging into the existing one.
**Always show the user the final config and confirm before writing.**

### After discovery

You now have:

- `<schemas-repo>` — absolute path to the OpenAPI contracts repository
- `<registry-login-command>` — the registry refresh command, or empty

The rest of this skill assumes both are known. Use `<schemas-repo>` for all `cd` commands into
the contracts repo.

---

## Step 1: Modify the OpenAPI Contract

### Find the right file

Contracts live inside `<schemas-repo>`. Layouts vary by project — typical paths look like
`schemas/openapi/contracts/<service>/` or `openapi/<service>/`. Explore the repo to find the
relevant file:

```bash
ls <schemas-repo>
```

**Always edit the file with the highest major version number.** For example, if a directory
contains both `v0.yml` and `v1.yml`, work in `v1.yml`. Lower versions are legacy and should not
be modified for new work.

### Bump the version

Every contract change requires a version bump in the `info.version` field of the YAML file.
Projects typically enforce this in CI — PRs without a bump will fail. **Follow the project's
documented version scheme**; semver is a common default:

| Change type | Example bump | When to use |
|---|---|---|
| Patch | `1.19.0` → `1.19.1` | Non-breaking, cosmetic (typo, description, example) |
| Minor | `1.19.0` → `1.20.0` | Backward-compatible additions (new optional field/endpoint) |
| Major | `1.19.0` → `2.0.0` | Breaking changes (removal, type change, rename) |

**If working on a branch that already has a PR open**, do not bump again — a single bump
compared to the default branch is enough. The new snapshot overwrites the existing one. Check
first:

```bash
git diff origin/HEAD -- <contract-file> | grep 'version:'
```

**For major version bumps**, follow [Major Version Release](#major-version-release) — it
involves more than just a file copy.

### Make the changes (minor/patch)

Common patterns:
- **New sub-domain**: Create a new folder based on the domain name. Create `<domain>-v0.yaml`
  with an initial structure.
- **New endpoint**: Add the path under `paths`, define request/response schemas under
  `components/schemas`.
- **New field**: Add the property to the relevant schema. If optional, do NOT add it to
  `required`.
- **Deprecate a field**: Mark it with `deprecated: true` rather than removing it (removing is
  breaking).

### Commit, push, and open a PR

Follow the project's branch and commit conventions (see project `CLAUDE.md` / `AGENTS.md`).

**Pushing the branch is not enough.** On most setups, the SDK generation workflow is triggered
by the `pull_request` event, so a PR must be opened before any SNAPSHOT artifact is built or
published. Open the PR immediately after pushing — see
[Step 2](#step-2-open-contract-pr-and-wait-for-ci). Do not start any service-side work before
the PR is open and its CI has succeeded.

---

## Major Version Release

A major version bump is more involved than a minor/patch change. It is an opportunity to clean
up accumulated deprecations while introducing the breaking change, and it requires a
side-by-side deployment strategy on the service side.

### 1. Create the new contract file

Do NOT edit the existing version file. Create a new one:

```bash
# Example: promoting v1.yml to v2.yml
cp <schemas-repo>/<path>/<sub-path>/v1.yml \
   <schemas-repo>/<path>/<sub-path>/v2.yml
```

### 2. Clean up deprecations

Before making any new changes, review the copied file thoroughly and **remove everything marked
as `deprecated: true`**. This includes:

- Deprecated endpoints (entire path entries)
- Deprecated query/path/header parameters on remaining endpoints
- Deprecated fields in request/response schemas
- Deprecated enum values
- Any `description` text that references the deprecated elements (e.g., "Use X instead")

This cleanup is the whole point of a major version — it's the one chance to shed legacy
baggage. Do it before adding new changes so the diff stays readable.

### 3. Make the intended breaking changes

Now apply the changes that motivated the major version in the first place (renamed fields,
changed types, restructured endpoints, etc.). Set `info.version` to `<N+1>.0.0` (e.g.,
`2.0.0`).

### 4. Service-side: support old and new versions side by side

When a breaking contract change is released, the service cannot simply swap to the new
artifact. Other consumers (other microservices, external clients, frontends) may still depend
on the old version. The service must support both versions simultaneously during a transition
period.

**Example (Kotlin + Gradle `build.gradle.kts`)** — add the new artifact alongside the old one:

```kotlin
// Keep the old version for backward compatibility
implementation("com.example.openapi:<service>-server-v1:1.19.0")
// Add the new version
implementation("com.example.openapi:<service>-server-v2:2.0.0-SNAPSHOT")
```

**Implement the new version's interfaces** while keeping the old ones functional. This means:

- Both sets of controllers (v1 and v2) are active and serve traffic
- Shared business logic lives in the service layer — controllers are thin adapters that map
  between their respective API models and the domain
- Both versions need their own tests

**Accept the temporary duplication.** During the transition period there will be duplicated
controller code and tests for the overlapping functionality. This is expected and intentional —
it ensures zero downtime for consumers migrating at their own pace.

### 5. Plan the cleanup

Once all consumers have migrated to the new version:

- Remove the old server artifact dependency from the build file
- Delete the old version's controllers, mappers, and dedicated tests
- Remove any compatibility shims in the service layer

This cleanup can be a separate PR/ticket after migration is confirmed complete.

---

## Step 2: Open Contract PR and Wait for CI

**Opening the PR is mandatory — it is what triggers SDK generation** on most setups. The SDK
generation workflow typically runs on the `pull_request` event, not on branch push. Until the
PR exists, no SNAPSHOT is produced and downstream services have nothing to resolve.

Open the PR immediately after pushing using whatever PR convention the project uses
(`gh pr create`, GitLab MR, etc.).

**Then wait for the SDK generation workflow to complete successfully.** This workflow typically:

- Detects which OpenAPI files changed
- Generates client and server SDKs (Kotlin, TypeScript, etc., depending on the project)
- Publishes them as SNAPSHOT artifacts to the project's package registry

For example, if you bumped `info.version` to `1.20.0`, the workflow typically publishes version
`1.20.0-SNAPSHOT` to the registry.

Check workflow status with `gh pr checks <pr-number> --watch` or the project's equivalent.

**Do not proceed to Step 3 until this workflow succeeds.** Server / client implementation work
depends on the generated SDK artifact:

- The service build will fail to resolve the new SNAPSHOT version
- Generated interfaces, request/response models, and types will be missing
- IDE autocomplete and type checks will be based on the old version, hiding incompatibilities

Starting implementation before the artifact exists forces rework. Wait for the green check.

---

## Step 3: Update the Service

**Prerequisite: the contract PR is open and the SDK generation workflow has finished
successfully.** If either condition is not met, stop and go back to Step 2 — the SNAPSHOT
artifact required below will not exist yet.

### Refresh the registry token (if applicable)

If the project's config includes a `registry_login_command`, run it before building. Tokens for
private registries often expire (e.g., AWS CodeArtifact tokens expire every ~12 hours):

```bash
<registry-login-command>
```

Skip this step if no `registry_login_command` is configured for the project.

### Update the dependency version

In the consuming service's build file, find the API contract dependency and update its version
to the new SNAPSHOT.

**Example (Kotlin + Gradle):**

```kotlin
// Example: updating from 1.19.0 to 1.20.0-SNAPSHOT
implementation("com.example.openapi:<service>-client:1.20.0-SNAPSHOT")
// or for server interfaces:
implementation("com.example.openapi:<service>-server-v1:1.20.0-SNAPSHOT")
```

The exact artifact name depends on the SDK generator and project conventions. Common patterns:
- Client: `<service>-client` (e.g., `crm-service-client`)
- Server: `<service>-server-v<N>` (e.g., `crm-service-server-v1`)

**If making a change to an already-published snapshot** (same version string, newer content),
the version does not need to be changed — refreshing dependencies (e.g., `./gradlew
--refresh-dependencies` or `npm install`) is usually sufficient.

**For major version changes**, follow the side-by-side approach described in the
[Major Version Release](#major-version-release) section — add the new artifact alongside the
old one rather than replacing it.

### Implement the changes

Now implement the service-side logic — controllers, services, repositories — to match the new
contract. The generated SDK interfaces and models will be available from the SNAPSHOT
dependency.

For major versions, implement the new version's interfaces as a separate set of controllers
while keeping the old ones intact.

### Verify the build

Run the project's standard build/test command (e.g., `./gradlew build`, `npm run checkAll`,
`mvn verify`).

If the build fails with a dependency resolution error, verify:
1. The contract CI workflow completed successfully
2. The registry token is fresh (re-run `<registry-login-command>` if applicable)
3. The version in the build file matches the SNAPSHOT (e.g., `1.20.0-SNAPSHOT`)

---

## Step 4: Open Service PR

Create a branch and PR for the service changes following the project's conventions. **Always
reference the contract PR** in the service PR description — this creates a clear link between
the two changes and helps reviewers understand the full scope.

Typical body content:

```
Implements the API changes from #<contract-PR-number>.

Depends on: <link-to-contract-PR>
```

---

## After Both PRs Are Approved

Once both PRs are approved and ready to merge:

1. Merge the **contract PR first** — this publishes the release (non-SNAPSHOT) version to the
   registry
2. Update the service PR to reference the **release version** (remove `-SNAPSHOT` suffix)
3. Merge the **service PR**

This ordering ensures the service always depends on a published release artifact in production.

---

## Improve This Skill

If you run into a blocker, a gotcha, an unexpected CI behaviour, or a missing step while working
through this skill, **fix it and update this skill before finishing the task**. The skill should
encode every hard-won detail so the next person (or the next session) doesn't have to rediscover
it.

Concretely:
- Hit a new failure mode? Add it to the troubleshooting bullets in the relevant step.
- Found a project-specific detail that isn't in `~/.claude/api-projects.json`? Either add it to
  the config schema (and document it here) or note it in the project's `CLAUDE.md`.
- Spotted a wrong assumption in the skill? Correct the prose.

Self-improvement is part of the workflow — not an afterthought.
