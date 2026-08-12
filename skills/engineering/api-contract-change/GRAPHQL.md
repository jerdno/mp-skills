# GraphQL specifics

The GraphQL half of [api-contract-change](SKILL.md). Sections are numbered to match the spine's
steps — consult each alongside its step. The schema flows into **two kinds of consumers**: the
server (typed resolvers) and the client(s) (`.graphql` operations with generated hooks) — so
Step 3 runs at least twice.

## Step 1: Modify the schema

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

### Where the version lives

The version typically lives in a `package.json` next to the schema. Some projects use full
semver, others use only minor + major bumps for the non-breaking / breaking distinction.

### Change patterns (non-breaking)

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

## Breaking changes: deprecate → migrate → remove

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

## Step 2: What CI runs and publishes

Two workflows typically run on the schema PR:

1. **Schema validation** — lint, typecheck, merged-schema up-to-date check, breaking-change
   detection (e.g., GraphQL Inspector), version-bump check.
2. **Generated package publication** — builds and publishes SNAPSHOT packages to the project's
   registry. Commonly two packages:
   - The merged schema (consumed by clients for code generation)
   - The server's typed resolver/operation types (consumed by the server)

SNAPSHOT versions commonly look like `<version>-SNAPSHOT.<timestamp>` (e.g.,
`0.4.0-SNAPSHOT.202604231530`) or just `<version>-SNAPSHOT`. Each push to the PR branch
typically produces a new SNAPSHOT.

Wait for **both** workflows, then find the exact SNAPSHOT version either in the workflow logs
or via the registry (e.g., `npm view <schema-package> versions --json`).

## Step 3: Update the consumers

The consumers are the **GraphQL server** (resolvers) and every **client** (web/mobile portal
apps). Update the server first, then the client(s).

### Server: update the dependency versions

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

### Server: implement the resolvers

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

### Client: update the dependency version

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

### Client: add or modify `.graphql` operations

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

### Client: regenerate the typed hooks

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

### Client: use the generated hooks in components

**Example (React + Apollo):**

```tsx
import { useGetApplicationQuery } from '@/gql/generated/generatedTypes'

const { data, loading, error } = useGetApplicationQuery({ variables: { id } })
```
