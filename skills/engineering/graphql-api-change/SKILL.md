---
name: graphql-api-change
description: >
  Use when the user asks to modify, add, or remove a GraphQL query, mutation, type, field, or
  enum in a project where the schema lives in a shared schemas repository and is consumed via
  generated packages by separate server and client repositories. Triggers on changes to GraphQL
  schemas — adding new queries/mutations, changing inputs/outputs, deprecating fields, or
  bumping the schema version. Also triggers when the user mentions a merged GraphQL schema,
  generated GraphQL service types, GraphQL resolvers, or a frontend's `.graphql` operations —
  even without saying "schema". Do NOT use for REST/OpenAPI contract changes — use the
  api-contract-change skill instead.
---

# GraphQL API Change Workflow

This skill guides you through the end-to-end process of changing a GraphQL API in projects that
split the schema, the server, and the client into separate repositories. GraphQL changes always
start with the schema and flow into both the **server** (resolvers) and the **client**
(operations and generated hooks). This multi-PR approach keeps the schema, resolvers, and
generated client hooks in sync.

For REST/OpenAPI contract changes, use the `api-contract-change` skill instead.

> **Project conventions are NOT in this skill.** Version policy, branch naming, commit message
> format, ticket prefixes, and CI workflow names belong in the project's `CLAUDE.md` /
> `AGENTS.md`. Follow whatever the project documents; if nothing is documented, follow what
> `git log` and recent merged PRs show.

## Overview

Every GraphQL change follows this sequence:

1. Modify the GraphQL schema in the project's schemas repository
2. Regenerate any merged schema artifacts the repo expects (a pre-commit hook commonly enforces
   this)
3. Open a PR for the schema, wait for the SDK generation CI workflow
4. Update the **server** (GraphQL service): implement / adjust resolvers against the new types
5. Update the **client(s)** (web/mobile): add / adjust `.graphql` operations and regenerate
   typed hooks
6. Open one PR per consuming repo and cross-reference the schema PR

Never skip the schema step — even for "small" changes. The generated packages are the source of
truth for types on both the server and the client.

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
        "/absolute/path/to/graphql-server",
        "/absolute/path/to/web-client"
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
3. **Other consumer repos** (optional) — absolute paths to the GraphQL server and any client
   repos (web portal, mobile app, etc.). Can be left empty and added later.
4. **Registry login command** (optional) — the shell command that refreshes the auth token for
   the package registry that hosts the generated packages (e.g., `aws codeartifact login --tool
   npm --domain ... --repository ...`, or a project-specific wrapper). Leave empty if there is
   no token to refresh.

Then write `~/.claude/api-projects.json`, creating the file or merging into the existing one.
**Always show the user the final config and confirm before writing.**

### After discovery

You now have:

- `<schemas-repo>` — absolute path to the GraphQL schemas repository
- `<registry-login-command>` — the registry refresh command, or empty

The rest of this skill assumes both are known. Use `<schemas-repo>` for all `cd` commands into
the schemas repo. The server and client repo paths are looked up from the same project's
`repositories` list (ask the user which is which if it's not obvious from naming).

---

## Step 1: Modify the GraphQL Schema

### Find the right files

Schemas live inside `<schemas-repo>`. Layouts vary by project — typical paths look like
`schemas/graphql/schema/<context>/`. The directory is usually split by domain context (e.g.,
`application/`, `userManagement/`, `shared/`). Each context typically has:

- `Query.graphql` — query operations for that context
- `Mutation.graphql` — mutation operations for that context
- One or more type files with object types, inputs, and enums

To list available contexts:

```bash
ls <schemas-repo>/schemas/graphql/schema/ 2>/dev/null || ls <schemas-repo>
```

### Bump the version

Every schema change requires a version bump (typically in a `package.json` next to the schema).
Projects commonly enforce this in CI — PRs without a bump will fail. **Follow the project's
documented version scheme**; some projects use full semver, others use only minor + major
bumps for any non-breaking / breaking distinction.

**If working on a branch that already has a PR open**, do not bump again — a single bump
compared to the default branch is enough. Check first:

```bash
git diff origin/HEAD -- <package.json-path> | grep '"version"'
```

### Make the changes (non-breaking)

Common patterns:

- **New context**: Create a new folder under `<schemas-repo>/schemas/graphql/schema/<context>/`
  and add `Query.graphql`, `Mutation.graphql`, and a types file. Use `extend type Query` and
  `extend type Mutation` — the root `Query` and `Mutation` types are typically defined once in
  a shared file.
- **New query / mutation**: Add the operation under `extend type Query` or
  `extend type Mutation` in the relevant context file. Add any new input/output types to the
  context's types file.
- **New field**: Add the field to the existing type. Make it nullable (no trailing `!`) unless
  every consumer will be updated immediately — non-nullable new fields are a breaking change
  for server implementations.
- **Deprecate a field / operation**: Add the `@deprecated(reason: "...")` directive rather than
  removing. Removal is a breaking change.

### Regenerate the merged schema

Any change to `.graphql` files typically requires regenerating a merged schema artifact (often
named `MERGED_SCHEMA.graphql` and a TypeScript companion). Run whatever script the project
documents — commonly `npm run schema-gen`:

```bash
cd <schemas-repo>/schemas/graphql
npm install    # only if dependencies changed
npm run schema-gen
```

Commit any regenerated files alongside the schema changes. A pre-commit hook commonly blocks
the commit if these files are out of sync with the source schema.

### Run local checks

Before pushing, run the project's full check locally — this catches typos, breaking changes,
and validation errors early (commonly `npm run checkAll`).

### Commit and push

Follow the project's branch and commit conventions (see project `CLAUDE.md` / `AGENTS.md`).

---

## Breaking Changes (Major Version Bump)

Breaking changes require more planning than a minor bump because both the server and all
clients must be migrated before the old API is removed. Many projects run GraphQL Inspector
(or similar) in CI to flag breaking changes — this is a multi-step process.

### 1. Deprecate before removing

Do NOT remove a field / query / mutation directly. Instead, add `@deprecated(reason: "Use X
instead")` and introduce the new replacement alongside it:

```graphql
type Application {
  # Deprecate old field
  legacyStatus: String @deprecated(reason: "Use `status` instead")
  # Add new field
  status: ApplicationStatus!
}
```

This keeps the schema backward-compatible and allows a gradual migration.

### 2. Migrate all consumers

With the new field / operation in place:

- Update the **server** to populate / handle both old and new forms
- Update the **client(s)** to use the new form
- Deploy client updates to production

Only after every consumer has migrated can the deprecated elements be removed.

### 3. Whitelist a breaking change (if truly unavoidable)

In rare cases (e.g., during active development, pre-release schemas), a breaking change is
acceptable without full migration. If the project's breaking-change guard supports an
exception list, edit it to allow the specific path. **Always clean this list up after the PR
merges** — stale exceptions weaken the guard for future changes.

### 4. Removing deprecations (major bump)

Once all consumers are off the deprecated elements, open a separate PR that:

- Removes the deprecated fields / queries / mutations
- Bumps the **major** version in the schema package
- Regenerates the merged schema artifacts

For schemas consumed by mobile apps, the server must also signal `minAppVersion` (or the
project's equivalent) so old app builds can force-update before the removal rolls out.

---

## Step 2: Open Schema PR and Wait for CI

Open a PR for the schema changes using the project's PR tooling (`gh pr create`, GitLab MR,
etc.).

Two workflows typically run on the PR:

1. **Schema validation** — lint, typecheck, merged-schema up-to-date check, breaking-change
   detection (e.g., GraphQL Inspector), version-bump check.
2. **Generated package publication** — builds and publishes SNAPSHOT packages to the project's
   registry. Commonly two packages:
   - The merged schema (consumed by clients for code generation)
   - The server's typed resolver/operation types (consumed by the server)

SNAPSHOT versions commonly look like `<version>-SNAPSHOT.<timestamp>` (e.g.,
`0.4.0-SNAPSHOT.202604231530`) or just `<version>-SNAPSHOT`. Each push to the PR branch
typically produces a new SNAPSHOT.

Check workflow status with `gh pr checks <pr-number> --watch` or the project's equivalent.

**Do not proceed to Step 3 until both workflows succeed.** The SNAPSHOT artifacts must be
available in the registry before the server and client can resolve them.

After the workflow completes, find the exact SNAPSHOT version either in the workflow logs or
via the registry (e.g., `npm view <schema-package> versions --json`).

---

## Step 3: Update the GraphQL Service (Server)

### Refresh the registry token (if applicable)

If the project's config includes a `registry_login_command`, run it before installing. Tokens
for private registries often expire:

```bash
<registry-login-command>
```

Skip this step if no `registry_login_command` is configured.

### Update the dependency versions

In the GraphQL server's `package.json`, bump the relevant packages to the new SNAPSHOT
version. The exact package names depend on project conventions.

**Example:**

```jsonc
{
  "dependencies": {
    // ...
    "@example/graphql-schema": "0.4.0-SNAPSHOT",
    "@example/graphql-service-types": "0.4.0-SNAPSHOT"
  }
}
```

Then install:

```bash
cd <graphql-server-repo>
npm install
```

**If making a change to an already-published SNAPSHOT** (same version string, newer
timestamp), you may need to delete the cached package directories under `node_modules/` and
run `npm install` again to force a refresh, since npm caches SNAPSHOT versions by name.

### Implement the resolvers

Resolvers live wherever the project organizes them — commonly under `src/resolvers/`:

- `Query.ts` — query resolvers (one function per field in `extend type Query`)
- `Mutation.ts` — mutation resolvers (one function per field in `extend type Mutation`)
- `index.ts` — assembles the full `Resolvers` object

For each new or changed operation:

1. Add the resolver function. Generated `QueryResolvers` / `MutationResolvers` types from the
   service-types package enforce the correct signature.
2. Delegate business logic to the project's API/data layer and map to the GraphQL shape using
   a dedicated mapping layer (commonly called "facades" or "mappers").
3. Never leak downstream REST/data-source response models into resolvers — always go through
   a mapper that converts data-source types → GraphQL types.

### Verify the build

Run the project's standard check command (commonly `npm run checkAll`, which combines
type-check + lint + test + build).

If the build fails with a dependency resolution error, verify:
1. The schema CI workflow completed successfully
2. The registry token is fresh (re-run `<registry-login-command>` if applicable)
3. The version in `package.json` matches the exact SNAPSHOT string from the registry

---

## Step 4: Update the Client (Web/Mobile)

### Update the dependency version

In the client's `package.json`, bump the schema package. The schema package is typically a
`devDependency` on the client — it's used only for code generation, not at runtime:

```jsonc
{
  "devDependencies": {
    // ...
    "@example/graphql-schema": "0.4.0-SNAPSHOT"
  }
}
```

Then install:

```bash
cd <client-repo>
npm install
```

### Add or modify `.graphql` operations

Client operations (queries and mutations the frontend actually sends) live wherever the
project keeps them — commonly under `src/gql/operations/*.graphql`, organized by context
(e.g., `application.graphql`, `user.graphql`).

Add the operation in the relevant file, selecting only the fields the UI needs:

```graphql
query GetApplication($id: ID!) {
  application(id: $id) {
    id
    status
    # ... only fields the component renders
  }
}
```

### Regenerate the typed hooks

Run the project's GraphQL code-generation script (commonly `npm run gql-gen`):

```bash
cd <client-repo>
npm run gql-gen
```

This regenerates the typed operations file (e.g., `src/gql/generated/generatedTypes.ts`),
producing:
- TypeScript types for all operation inputs / outputs
- Framework hooks (React Apollo `useGetApplicationQuery`, etc., depending on the project)

Commit the regenerated file alongside the `.graphql` operation changes.

### Use the generated hooks in components

**Example (React + Apollo):**

```tsx
import { useGetApplicationQuery } from '@/gql/generated/generatedTypes'

const { data, loading, error } = useGetApplicationQuery({ variables: { id } })
```

### Verify the build

Run the project's standard check command (commonly `npm run checkAll`).

---

## Step 5: Open Service and Client PRs

Create a branch and PR in each repo following the project's conventions. **Always reference
the schema PR** to keep the three (or more) PRs traceable as a single logical change.

Typical body content:

```
Implements the schema changes from <schema-PR-link>.

Depends on: <schema-PR-link>
```

---

## After All PRs Are Approved

Once all PRs are approved and ready to merge:

1. Merge the **schema PR first** — this publishes the release (non-SNAPSHOT) versions of the
   generated packages to the registry
2. Update the **server PR** and **client PR(s)** to reference the **release versions**
   (remove the `-SNAPSHOT[.<timestamp>]` suffix)
3. Run the install command in each repo, commit the updated lockfiles, push, and wait for CI
   to go green
4. Merge the **server PR** and the **client PR(s)**

This ordering ensures the server and client always depend on a published release artifact in
production.

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
