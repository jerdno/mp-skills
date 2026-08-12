# OpenAPI specifics

The REST/OpenAPI half of [api-contract-change](SKILL.md). Sections are numbered to match the
spine's steps — consult each alongside its step. The contract flows into consumers as generated
SDKs: a client SDK for callers, a server SDK (interfaces + models) for the implementing
service.

## Step 1: Modify the contract

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

### Where the version lives

The version is the `info.version` field of the contract YAML. Semver is a common default:

| Change type | Example bump | When to use |
|---|---|---|
| Patch | `1.19.0` → `1.19.1` | Non-breaking, cosmetic (typo, description, example) |
| Minor | `1.19.0` → `1.20.0` | Backward-compatible additions (new optional field/endpoint) |
| Major | `1.19.0` → `2.0.0` | Breaking changes (removal, type change, rename) |

For a major bump, follow [Breaking changes](#breaking-changes-major-version-release) — it
involves more than editing the version field.

### Change patterns (minor/patch)

- **New sub-domain**: Create a new folder based on the domain name. Create `<domain>-v0.yaml`
  with an initial structure.
- **New endpoint**: Add the path under `paths`, define request/response schemas under
  `components/schemas`.
- **New field**: Add the property to the relevant schema. If optional, do NOT add it to
  `required`.
- **Deprecate a field**: Mark it with `deprecated: true` rather than removing it (removing is
  breaking).

## Breaking changes: major version release

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

## Step 2: What CI runs and publishes

One SDK generation workflow typically runs on the contract PR. It:

- Detects which OpenAPI files changed
- Generates client and server SDKs (Kotlin, TypeScript, etc., depending on the project)
- Publishes them as SNAPSHOT artifacts to the project's package registry

The SNAPSHOT version mirrors the contract version: bumping `info.version` to `1.20.0` typically
publishes `1.20.0-SNAPSHOT`.

## Step 3: Update the consuming service

The consumers are the service(s) that implement or call this API — typically one service repo
per contract, consuming the server SDK (and other services consuming the client SDK).

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

**For major version changes**, follow the side-by-side approach from
[Breaking changes](#breaking-changes-major-version-release) — add the new artifact alongside
the old one rather than replacing it.

### Implement the changes

Implement the service-side logic — controllers, services, repositories — to match the new
contract. The generated SDK interfaces and models will be available from the SNAPSHOT
dependency.

For major versions, implement the new version's interfaces as a separate set of controllers
while keeping the old ones intact.
