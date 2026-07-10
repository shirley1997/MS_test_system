## 26.06.2026
# Master Thesis Setup Progress

## Local development environment installed

- Node.js v24.18.0 with npm 11.16.0
- Python 3.12.4 with pip 25.1.1
- Java 25.0.3 (JDK)
- Apache Maven 3.9.16
- Git 2.45.2
- Docker Desktop 4.79.0 with WSL2 backend
    - Docker Engine 29.5.3
    - Docker Compose v5.1.4
- VSCode with relevant extensions (Java, Python, ESLint, Prettier, GitHub Actions, YAML, etc.)

## Versions pinned (must not change during experiment)

- npm 11.16.0
- pip 25.1.1
- Maven 3.9.16
- Sonatype Nexus 3.93.2
- Reason: changing these mid-experiment could alter dependency resolution behavior

## Infrastructure decision documented

- Chose local Docker + self-hosted GitHub Actions runner setup
- Reason: free, reproducible, no cloud cost, realistic company pattern
- runner type does not affect package manager resolution behavior

## Sonatype Nexus deployed

- Pulled Docker image `sonatype/nexus3:3.93.2` (Community Edition)
- Created persistent Docker volume `nexus-data`
- Started Nexus container exposed on `http://localhost:8081`
- Retrieved initial admin password from container
- Signed in as admin and changed password
- Disabled anonymous access (more realistic) -> need basic auth

## Created 12 Nexus repositories (3 ecosystems x 4 types)

### npm

- `npm-internal-hosted` (hosted) - stores internal npm packages
- `npm-public-proxy` (proxy) - proxies https://registry.npmjs.org
- `npm-group-public-first` (group) - members: [npm-public-proxy, npm-internal-hosted]
- `npm-group-private-first` (group) - members: [npm-internal-hosted, npm-public-proxy]

### PyPI

- `pypi-internal-hosted` (hosted) - stores internal PyPI packages
- `pypi-public-proxy` (proxy) - proxies https://pypi.org/ (index path: /simple)
- `pypi-group-public-first` (group) - members: [pypi-public-proxy, pypi-internal-hosted]
- `pypi-group-private-first` (group) - members: [pypi-internal-hosted, pypi-public-proxy]

### Maven

- `maven-internal-hosted` (hosted, Release policy) - stores internal Maven packages
- `maven-public-proxy` (proxy) - proxies https://repo1.maven.org/maven2/
- `maven-group-public-first` (group) - members: [maven-public-proxy, maven-internal-hosted]
- `maven-group-private-first` (group) - members: [maven-internal-hosted, maven-public-proxy]

## Non-default settings applied to all proxy repos

- Maximum metadata age: changed from 1440 to 0
- Not found cache TTL: changed from 1440 to 0
- Reason: experiments need always-fresh metadata; default caching would hide newly published packages

## Mapping to experiment variables (Sub-RQ1)

- A1a (group, public-first searched first) -> `*-group-public-first` repos
- A1b (group, private-first searched first) -> `*-group-private-first` repos
- A2 (hosted + separate proxy) -> `*-internal-hosted` + `*-public-proxy` URLs
- A3 (hosted-only) -> `*-internal-hosted` only

## Open questions / decisions still to make

- Whether to publish "malicious" packages to real npm / PyPI / Maven Central or use a local "fake public" registry
    - Note: PyPI and Maven Central do not allow deletion; npm only allows unpublish within 72h
    - Decision to be discussed with supervisor

## Next steps

- [x] Verify group repo member ordering (sanity check)
- [ ] Build the three microservices (Node.js, Python, Java)
- [ ] Set up self-hosted GitHub Actions runner in Docker : https://docs.github.com/en/actions/concepts/runners/self-hosted-runners
- [x] Create GitHub repository for the project
- [ ] Configure per-service CI pipelines
- [ ] Build central automated pipeline for experiment matrix  (preferred language: python)


Link:
npm package documentation: https://docs.npmjs.com/creating-and-publishing-unscoped-public-packages


## 27.06.2026

## Build up npm service
### plan 

1. [ ] **Set up the monorepo structure** ← we'll do this first
2. [ ] **Initialize the Node.js service folder** (`npm init`, install public dependencies)
	1. [ ] npm init -y -> Initialize an npm project with default settings
3. [ ] **Decide what the 2 internal packages will do** (suggest: event validator + service forwarder)
4. [ ] **Build the 2 internal packages** as separate npm projects
5. [ ] **Write the Node.js service code** that uses the 2 internal packages
6. [ ] **Test it runs locally**
7. [ ] **Publish the 2 internal packages to Nexus** 
8. [ ] **Reconfigure the service** to install internal packages from Nexus instead of locally
9. [ ] **Test the end-to-end install from Nexus**

-  content in .gitignore: build artifacts, IDE files, OS files, virtual envs etc.
-  after initalize node.js project, package.json is generated 


## 27.06.2026 Microservice application setup
## Created monorepo directory structure

- Created folders: `.github/workflows/`, `automation_process/`, `docs/`, `packages/{java,nodejs,python}/`, `services/{java,nodejs,python}/`
- Created `.gitignore` with standard ignore patterns (node_modules, **pycache**, target, .venv, etc.)
- Created placeholder `README.md`


## Initialized Node.js service in `services/nodejs/`

- Ran `npm init -y` to create initial `package.json`
- Customized `package.json`:
    - name: `receive-event-http-api`
    - version: `1.0.0`
    - main: `src/index.js`
    - scripts: `start` and `dev`
    - engines: Node pinned exactly to `24.18.0`
- Installed Express 5.2.1 as public dependency (`npm install express`)
- Created `src/index.js` with code

## Wrote the Node.js service code

- `GET /health` endpoint returns service status
- `POST /events` endpoint forwards events to Python service at `http://localhost:5000/process`
- Returns Python's response back to the client (matches Figure 4.1 chain: Node → Python → Java → back)
- Server binds to `0.0.0.0:3000` (explicitly listens on all interfaces, container-ready)


## Successfully tested the Node.js service

- `npm start` runs the service without errors
- `curl http://localhost:3000/health` from a second PowerShell terminal returns:
    - StatusCode: 200
    - Content: `{"status":"ok","service":"receive-event-http-api"}`
- End-to-end verified: service runs, listens correctly, second terminal can reach it
## Package naming decision

- Researched scoped vs unscoped npm packages for the internal packages.
- Confirmed: scoped names on npmjs.com can only be published by the scope owner; unclaimed scopes can be hijacked by attackers.
- Confirmed: `npm init` defaults to **unscoped** package names.
- **Decision: use unscoped names** for all internal packages, because:
    - Matches the npm default ("no extra setup" baseline for Sub-RQ1).
    - Matches the canonical Birsan 2021 dependency confusion attack model.
    - Keeps the experiment matrix clean (avoids hidden `@scope:registry` config variable).
    - Cross-ecosystem consistency with PyPI (flat namespace) and Maven.
    - Claiming a scope publicly would itself be a security mitigation, outside RQ scope.

## Chose specific internal package names

- `xueting-thesis-event-jianding`: event validator
- `xueting-thesis-service-fasong`: HTTP forwarder
- Verified both names against npm naming rules: ≤214 chars, lowercase, unique, descriptive, URL-safe, no Node core conflicts.
- https://docs.npmjs.com/package-name-guidelines
- 

## Built `xueting-thesis-event-jianding` (validator)

- Created `package.json` with name, version `1.0.0`, Node engine `24.18.0`, license `UNLICENSED`, `publishConfig.registry` pointing to Nexus `npm-internal-hosted`.
- Wrote `index.js` exporting `validateEvent()` — checks required fields `id` and `type` (non-empty strings).
- Simplified event shape: removed `timestamp` field to keep the chain logic clean.
- Wrote `test.js` with 4 test cases (valid event, missing type, empty id, non-object input).
- **Tested locally: 4 passed, 0 failed.**

## Built `xueting-thesis-service-fasong` (forwarder)

- Created `package.json` with same conventions as the validator. Zero runtime dependencies (uses Node 24 built-in `fetch`).
- Wrote `index.js` exporting `forwardEvent(targetUrl, event)` — POSTs JSON, throws on non-2xx, returns downstream JSON response.
- Wrote `test.js` using a temporary in-process HTTP server on a random port; 4 test cases (success, 500 response, empty URL, null event).
- **Tested locally: 4 passed, 0 failed.**



## Next steps
- Resolve the Nexus authentication issue and successfully publish both packages.
- Verify both packages appear in Nexus UI under `npm-internal-hosted`.
- Verify packages are served through `npm-group-public-first` and `npm-group-private-first`.
- Update the Node.js service `package.json` to depend on the two internal packages.
- connect `validateEvent` and `forwardEvent` into `src/index.js` of the Node service.



## 28.06.2026: Build npm service and python service and the java internal packages

## Python service setup

- Created a Python virtual environment (`.venv`) in `services/python/` 
- should avoid using `--upgrade pip` in future to keep reproducibility.

## Built `xueting-thesis-event-fengfu` (Python service add fields)

- Created `pyproject.toml` with name, version `1.0.0`
- Wrote `__init__.py` exporting `enrich_event()`, adds `timestamp` and `processed_by_python: true` fields.
- Wrote test cases
- **Tested locally: 5 passed, 0 failed.**

## Built `xueting-thesis-service-zhuanfa` (Python forwarder)

- Created `pyproject.toml` with one dependency: `requests>=2.32.0`.
- Wrote `__init__.py` exporting `forward_event(target_url, event)` 
- Wrote  test cases
- **Tested locally: 5 passed, 0 failed.**

## Published both Python packages to Nexus

- Installed PyPA build tools: `build==1.2.2` and `twine==6.1.0`.
- Configured `.pypirc` with admin credentials for Nexus pypi repo.
- Successfully ran `python -m build` and `twine upload` for both packages.
- Verified in Nexus UI: both packages appear with `.whl`, `.tar.gz`, and auto-generated `.metadata` files.

## Built the Python Flask service (`process-event-http-api`)

- Created `services/python/pyproject.toml` with Flask `3.1.0` and the two internal packages version `1.0.0`.
- Created project-level `pip.ini` pointing to Nexus pypi group repo 
- Configured user-level `pip.ini` with embedded admin credentials. (so credential won't upload in git)
- Installed Flask + both internal packages successfully via `pip install`.
- Wrote `src/app.py` 

## End-to-end test: Node → Python chain

- Started Node service on port 3000 and Python service on port 5000 in separate terminal windows.
- POSTed valid event to Node; verified Python received and enriched the event correctly.
- Confirmed full chain works: Node validates → forwards → Python enriches → tries to forward to Java (fails as expected cause Java doesn't exist yet).



## Java service decisions

- `groupId = com.xueting.thesis`.
- Chose **Javalin** as framework instead of Spring Boot (javalin can realize the planed function or java service but introduce less dependencies compare to spring boot)
- Decided Java service is internal-facing only, so printing aggregation state in response is acceptable.

## Built `xueting-thesis-event-juhe` (Java event aggregator)

- Created Maven directory structure 
- Created `pom.xml` with `groupId=com.xueting.thesis`, Java `25`, JUnit `6.0.2` (test scope) `distributionManagement` pointing to Nexus.
- Wrote `EventAggregator.java` with function `aggregate(state, event)`, adds extra fields to event and increase event type counter, returning a Java `record` with both outputs.
- Wrote Junit testcases
- **Tested locally: 6 passed, 0 failed.**

## Built `xueting-thesis-result-fanhui` (Java response generator)

- Wrote `ResponseGenerator.java` 
- Wrote test cases
- **Tested locally: 5 passed, 0 failed.**

## Published both Java packages to Nexus

- Configured `/.m2/settings.xml` with Nexus admin credentials
- Successfully ran `mvn clean deploy` for both packages.
- Verified in Nexus UI: both packages appear at `com/xueting/thesis/...` with `.jar`, `.pom`, and checksum files.

## Uploaded project to GitHub

- exclude `node_modules/`, `.venv/`, `target/`, IDE files, and secrets.

## Next steps

- Build the Java Javalin service (`aggregate-event-http-api`) on port 8080.
- Combine both Java internal packages into the service.
- Run full end-to-end chain test: Node → Python → Java.
- Then move on to setting up self-hosted GitHub Actions runner in Docker.


# 30.06.2026: Build java service, application testing, Runner/Pipeline Planning


Starting point: Both Java internal packages (`xueting-thesis-event-juhe`, `xueting-thesis-result-fanhui`) already published to Nexus at version 1.0.0.



## Part1: Java Service — `aggregate-event-http-api`

### Framework and library decisions
- **Javalin 7.2.2** 
- **Jackson Databind 2.21.2** for JSON handling (JSON Mapper).
  - Not chosen upfront: discovered via Javalin's runtime error message (while testing the application) which explicitly recommended this exact version.


### `pom.xml`setup
- 3 dependencies: Javalin, both internal Maven packages, Jackson Databind (added after first runtime error).
- 1 plugin: `maven-compiler-plugin` (pinned to 3.15.0 for now).
- 1 property: `maven.compiler.release=25`.
- 1 `<repositories>` entry pointing to `maven-group-public-first` Nexus repo.


### `settings.xml` update
- Added second `<server>` entry with `id="nexus-group-public-first"` (matching the id in `pom.xml`) for installing dependencies through the group repo (package managers has access to public registry + private registry).
- Kept existing `nexus-internal` entry for publishing internal packages.
-  **project file holds the URL (committable), user file holds credentials (private)**  -> no credential is accidentally commited to git

### `Main.java`
- Package: `com.xueting.thesis` (use the same groupId as the java internal packages).
- Two endpoints:
  - `GET /health` — liveness check, returns `"ok"`.
  - `POST /aggregate` — parses incoming JSON event, aggregate it and send back

### Encountered errors and fixes
1. **Compile error: "Symbol nicht gefunden" on `app.get(...)` and `app.post(...)`**.
   - Cause: Javalin 7 redesigned the routing API. Routes are no longer registered on the `Javalin` instance — they must be registered inside the `Javalin.create(config -> { ... })` block using `config.routes.get(...)`.
   - Fix: restructured `Main.java` to register routes inside the config block.
2. **PowerShell error running `mvn exec:java -Dexec.mainClass=...`**.
   - Fix: wrap the `-D` argument in quotes: `mvn exec:java "-Dexec.mainClass=com.xueting.thesis.Main"`.
3. **Runtime error: "You don't have an object mapper configured"**.
   - Javalin 7 needs an external JSON library and told me exactly which one and what version.
   - Fix: added `jackson-databind` 2.21.2 to `pom.xml`, recompiled, restarted service.

### Testing (all passed)
- **`GET /health`** returned `ok`.
- **`POST /aggregate`** with a single event returned correct response with `processed_by_java: true` added and `aggregation_state: {"login": 1}`.
- **Counter increase**: second request with same event type produced `{"login": 2}`, then a request with different type produced `{"login": 2, "login222": 1}` 
- **Full Application testing (Node → Python → Java)**: sent request to Node's `/events` with only `id` and `type`. Response returned nested envelope with all three services' contributions (Node wraps Python wraps Java). Every layer added its expected field, counter incremented correctly. Microservice application build phase is complete.


---

## Part2: Consider options of configure Github Actions runner


### GitHub Actions Runner: in Docker container or on native Windows machine?
- Chose to build a **custom Dockerfile** rather than using a community image (e.g. `myoung34/github-runner`).
- Reasoning: reproducible when running `docker build` 
- Chose Docker over native Windows runner because:
  - **Cache isolation between experiment cells** . when using runner on windows machine, config files need to manually removed between cells, unnoticed cache may pollute other experiment cells. Docker's per-cell `docker rm && docker run` guarantees a fresh filesystem.
  - image is versioned via the Dockerfile. native runner is tied to my personal Windows install.
- Image is built once (~1 GB, contains Node/Python/Java/Maven software at pinned versions + GHA runner binary). Container startup is about 2 seconds. No reinstalling tools between cells.

### Runner count
- **1 runner is enough**. Simpler than parallel.

### Workflow structure
- **4 YAML workflows**: 1 orchestrator + 3 service CIs (one per ecosystem).
- Splitting service CI per ecosystem matches the original proposal (each service has independent CI pipeline), keeps each YAML small and readable.
- The **central automated pipeline is implemented as a Python script**
  - To realize functions such as matrix generation, CSV writing, and result classification 
  - Python script uses GitHub CLI (`gh workflow run`, `gh run watch`, `gh run download`) to trigger service CIs and collect results.

### initial design decisions about central automated pipeline
1. Central Python script invalidates **Nexus proxy repo (proxy) caches** via Nexus REST API (`DELETE /service/rest/v1/repositories/{repo}/invalidate-cache`). internal-hosted repos are untouched, so published packages remain.
2. Script generates config files for this cell based on A, B1, B2, C values.
3. Script triggers the relevant service CI workflow with cell parameters.
4. Runner container starts fresh from prebuilt image (2 sec).
5. Workflow checks out repo, applies generated configs, prepares workspace per C1 (lockfile handling), runs the resolution command.
6. Raw resolution output uploaded as workflow artifact.
7. Container is destroyed. all client-side caches (`~/.npm`, `~/.m2/repository`, pip cache, `node_modules`, `.venv`, `target/`) are gone.
8. Central script downloads artifact, normalizes, classifies (`malicious_resolved` / `private_resolved` / `resolution_error` / `invalid_configuration`), appends to CSV.
9. Loop to next cell.

### Nexus URL parameterization
- `NEXUS_URL` is an environment variable consumed by the central script's config-generation logic (`http://host.docker.internal:8081` in CI, `http://localhost:8081` in local dev).
- The script generates the whole config file per cell (`.npmrc`, `pip.conf`, `settings.xml`), composing `NEXUS_URL` + the right repo path(s) for the current B1. (docker's localhost is not the same as localhost on windows)


### Same infrastructure covers Sub-RQ2
- Same Docker runner image can host SCA tools for subRQ2 experiment
- Scanning is done against the same project state that produced Sub-RQ1 results, Docker keeps reproducibility
- Investment in Docker infrastructure can be used for both research question experiments.


## Next steps
Start Stage 1 of runner setup:
1. Create `.github/workflows/hello-world.yml`  used for testing the configured self-hosted github runners
2. Push to GitHub, observe it sitting in "queued" state (this proves the pull-based architecture: no runner is registered yet, so nothing picks up the job).
3. write the Dockerfile.
4. Register a runner from GitHub, start the container, watch the hello-world workflow complete automatically.

# 01 & 02.07.2026: Set up self-hosted github actions runner in docker container

**Stand: Self-hosted GitHub Actions runner successfully built and run in docker now, registered on github, and verified. (can successfully complete the job of test workflow file hello-world.yml**

## Stage 1: Hello-world workflow (observe the workflow when no self-hosted runner is built yet)

- Created `.github/workflows/hello-world.yml`, a minimal workflow targeting `runs-on: self-hosted`.
- Pushed to GitHub. First push required upgrading the Personal Access Token (PAT) with the `workflow` 
- Job appeared in the Actions tab and shows **Queued** state with "Waiting for a runner to pick up this job." in output.
- **Result:** jobs wait until a matching self-hosted runner comes online.

## Stage 2: implement custom Dockerfile for the self-hosted runner

Design decision: for reproducibility and isolation of experiment cell (cache need to be discarded and must not affect experiment result of other cells), built a github actions self-hosted runner as a Docker container from a custom Dockerfile rather than a community image, so every install step is controllable and only nessasary tools will be installed.

Files created under `infrastructure/runner/`:
- `Dockerfile` : described the base image, which tools should be installed, setup user, setup runner version etc.
- `entrypoint.sh`: the script that register the runner on github and starts the runner when container start

Image contents (all pinned versions) (try to be identical with the dev environment):
- Base image: **Ubuntu 24.04** (widely used and smaller than windows docker)
- Node.js **24.18.0** + npm **11.16.0** (from NodeSource apt repo)
- Python **3.12** + pip **25.1.1** (pip installed via apt then upgraded with `--ignore-installed`)
- Java: Eclipse Temurin **JDK 25** (via Adoptium apt repo)
- Maven **3.9.16** (from Apache archive)
- some nessasary commands: Git, curl, jq, sudo
- GitHub Actions runner binary **v2.335.1** (Linux x64), SHA-256 verified (protect integrity)

Key decisions made:
- **Base OS:** Ubuntu 24.04. Base OS doesn't affect experimental variables anyway (all toolchains already pinned on top).
- **Node install:** NodeSource apt repo, not nvm: nvm is for developer machines that need to switch between versions. a container needs exactly one pinned Node version.
- **Python install:** use commands `pip install --break-system-packages --ignore-installed` to installed pip 25.1.1. 
- **Java install:** Adoptium/eclipse temurin (Eclipse Foundation OpenJDK build). The Docker Hub `openjdk` image is deprecated; Temurin is the recommended alternative.
- **Registration mode:** persistent. no `--ephemeral` flag. The orchestrator will handle cache isolation by destroying/recreating containers per cell in the next phase. (not nessasary correct, will reconsider this because current situation is confused)
- **Token supply:** runtime enviroment variable (`GH_TOKEN`) via `docker run -e`. because the token expired in 1 hour. (short-lived, no need to embed into runner container)
- **De-registration on shutdown:** skipped for simplicity. `--replace` flag in `config.sh` handles re-registration conflicts on next start. offline runners in GitHub's UI can be cleaned up manually.  (will reconsider this)

## Stage 3: Build runner docker image, register on github, and verify through hello-world workflow

- Built the image: `docker build -t thesis-runner:2.335.1 .`, completed in **4m 59s**.
- Debugged one build failure along the way: the initial pip install line conflicted with the Debian-packaged pip (`Cannot uninstall pip 24.0, RECORD file not found`). Fixed by adding `--ignore-installed`.
- Generated a registration token from GitHub → Settings → Actions → Runners → New self-hosted runner.
- Started the container with `docker run -d -e GH_REPO_URL=... -e GH_TOKEN=... thesis-runner:2.335.1`.
- Runner registered successfully. runner logs saves in /infrastructure/runner/runner_log.txt 
- after restart the workflow, the `hello-world` job (queued) was picked up immediately and completed 
  - `Running job: hello`
  - `Job hello completed with result: Succeeded`

## Outcome

- successfully built reproducible self-hosted runner with docker file, it successfully runs in a docker container now.
- test succeeded: Dockerfile → image → container → GitHub registration → workflow execution.


## Next steps

- Design and implement the 3 indepedent service CI pipeline (in seperated YAML files):
  - `service-ci-nodejs.yml` (npm resolution)
  - `service-ci-python.yml` (pip resolution)
  - `service-ci-java.yml` (Maven resolution)


# 06.07.2026

**Starting design of the Node.js service CI pipeline. Surfaced an important npm design constraint that affects the definition of B1b/B1c. No code written yet, design not fully decided.**

## Runner container maintenance

- Deleted yesterday's stale runner container (`docker rm -f thesis-runner`).
- Grabbed a fresh registration token from GitHub → Settings → Actions → Runners → New self-hosted runner.
- Started a new container with `docker run -d -e GH_REPO_URL=... -e GH_TOKEN=... thesis-runner:2.335.1`.
- Verified via `docker logs`: runner connected to GitHub and is idle.
  - **Registration token** (from GitHub UI) = one-time visitor pass, expires in ~1 hour, used only at first registration.
  - **`.credentials` file** (inside container) = long-lived employee badge issued by GitHub after successful registration. Used from then on.
  - `docker stop` / `docker start` on the same container = credentials preserved, no new token needed.
  - `docker rm` on the container = credentials destroyed, new token required next time.
- Confirmed: for the actual 432-cell experiment, the orchestrator will use `docker run --rm` per cell (fresh container each time) because all cache should be discarded, which requires no token management from me. GitHub's registration token is only needed manually during development.

## Node.js service CI pipeline — design work

### Architecture decision: config generator lives in Python, not inline in YAML

- Decided to write `automation_process/config_generators/generate_npmrc.py` as a standalone Python script.
- The workflow YAML will call the script rather than embedding the cell-selection logic in bash.
- Reasons:
  - Can be tested at the terminal without triggering a workflow run
  - Same design pattern will be reused for other ecosystems `generate_pipini.py` and `generate_settings_xml.py` later
  - Cell-selection logic isolated in one place, unit-testable
- Planned file layout:
  ```
  MS_test_system/
  ├── .github/workflows/
  │   └── service-ci-nodejs.yml         ← later
  └── automation_process/
      └── config_generators/
          └── generate_npmrc.py         ← in progress
  ```


Return values decided:
- Valid content → return the `.npmrc` string
- B1d (no .npmrc at all) → return `None`
- Invalid combination → raise `ValueError` (exception)

`nexus_url` is a parameter (not hardcoded) because the value differs between local dev (`http://localhost:8081`) and inside the runner container (`http://host.docker.internal:8081`).

### A → Nexus repo mapping (just like in proposal)

| A | Nexus repo (private-facing) |
|---|---|
| A1a | `npm-group-public-first` |
| A1b | `npm-group-private-first` |
| A2 | `npm-internal-hosted` (with separate `npm-public-proxy` available) |
| A3 | `npm-internal-hosted` only (no proxy exists) |

### A × B1 matrix reviewed

| | B1a (single URL) | B1b (multi, public direct) | B1c (multi, public via proxy) | B1d (no .npmrc) |
|---|---|---|---|---|
| **A1a** | group-public-first | private: group-public-first, public: npmjs.org | private: group-public-first, public: public-proxy | *(no file)* |
| **A1b** | group-private-first | private: group-private-first, public: npmjs.org | private: group-private-first, public: public-proxy | *(no file)* |
| **A2** | internal-hosted *(failure mode — no public path)* | private: internal-hosted, public: npmjs.org | private: internal-hosted, public: public-proxy | *(no file)* |
| **A3** | internal-hosted *(failure mode — no public path)* | private: internal-hosted, public: npmjs.org | **INVALID** (A3 has no proxy repo) | *(no file)* |

- **1 invalid combination**: A3 × B1c (need to consider, might add more later)
- **2 intentional failure-mode cells**: A2 × B1a, A3 × B1a, meant to test what happens when no public path exists at all (expected classification: `resolution_error`)
- **"Private URL" semantics**: resolves to the *group* repo for A1a/A1b, and to `internal-hosted` for A2/A3

## Open design issue: npm registry semantics (needs decision before coding, need to read npm documentation)

While reviewing the matrix, discovered a real npm limitation that affects the definition of B1b and B1c.

**The problem:** npm has exactly one default registry via `registry=...`, plus per-scope registries via `@scope:registry=...`. There is **no built-in mechanism for "check registry A, then registry B" for unscoped packages**. My public dependencies (`express`, etc.) are unscoped — they only have flat names. So an `.npmrc` like:

```
registry=<internal-hosted URL>
@public:registry=https://registry.npmjs.org
```

means: `express` still goes to internal-hosted (default). Only packages named literally `@public/foo` would go to npmjs.org.

**Comparison:**
- pip: has native `--extra-index-url` for fallback registries
- Maven: has native multiple `<repository>` entries with fallback ordering
- npm: only default + scope-based routing, no fallback

**Three possible directions (need to choose):**

1. **Rename public packages to scoped** (`@public/express-wrapper` etc.) — literally reach npmjs.org for public deps, but doesn't match how real Node projects consume unscoped public dependencies.
2. **Redefine B1b/B1c as scope-based routing** — keep unscoped packages, accept that "public URL" only affects `@public/*`. Accurately reflects npm's design constraint. Potentially valuable finding for the thesis: "npm forces scope-based patterns that don't match unscoped real-world dependencies."
3. **Vary the install command per cell instead of the config file** — muddies the "we vary configuration files" methodology story; also npm resolves transitive deps against whatever registry was set globally last.

**Decision deferred**: this is a design decision affecting the research question sub-RQ1 variable definition, not just implementation. Will re-read the original Sub-RQ1 definitions in the thesis proposal tomorrow and possibly consult advisor before proceeding.

## Outcome tonight

- No code written yet — deliberately, because a real design gap surfaced that shouldn't be committed to code prematurely.
- Design of `generate_npmrc.py` is roughly 80% locked (function signature, return contract, A mapping, matrix, failure-mode cells, invalid combinations all confirmed).
- Blocking issue: definition of "multi-URL" for B1b/B1c under npm's registry constraints.
- Runner container is running and ready for tomorrow's development.

## Next session

- Re-read Sub-RQ1 definitions carefully; decide on B1b/B1c semantics (or bring the question to advisor).
- Implement `generate_npmrc.py` once B1b/B1c is settled.
- Test all 16 A×B1 combinations at the terminal (11 content strings + 4 None + 1 exception).
- Then write `service-ci-nodejs.yml` to call the generator.

## Notes for future me

- The npm/pip/Maven registry semantic differences discovered tonight are worth documenting as their own methodology section in the thesis. Different package managers offer fundamentally different registry-routing primitives, which itself affects the space of possible dependency confusion configurations.


# 09.07.2026

Three main things done: fixed the runner container (fixed entrypoint.sh and rebuild the image) so it can restart cleanly, confirm the design decisions for how npm cells will work, and wrote both the `.npmrc` file generator and a draft of the Node.js service workflow (service CI pipeline) (not tested yet).



### Fix inside `entrypoint.sh`
- Added a check: if `.credentials` already exists → skip `config.sh` → go straight to `./run.sh`.
- Moved the `GH_TOKEN` required-check *inside* the "need to register" branch, because on restart there is no registration token available (they expire after ~1 hour).
- Added `exec` in front of `./run.sh`. This makes `run.sh` become the main process of the container, so when `docker stop` sends the SIGTERM signal, it goes directly to `run.sh` instead of bash. Cleaner shutdown.

### Result
- First start: registers normally.
- `docker stop` + `docker start` on the same container: skips registration, no token needed. Works.
- Small cosmetic issue: on restart there's still a brief "A session for this runner already exists" message in the log for ~1 minute, then it clears itself. This happens because run.sh didn't have time to tell GitHub "I'm going offline" during `docker stop`. Not a real problem. the central automated pipeline will use `docker run --rm` for each cell, not restart cycles.

Every change to `entrypoint.sh` or the Dockerfile requires (needs rebuild!):

```
docker build -t thesis-runner:2.335.1 infrastructure/runner/
docker rm -f thesis-runner
docker run -d ... (with fresh registration token)
```



## 2. Reviewed the automation process design

### Classification design (confirmed today)
The workflow uploads **only the raw output**. The central automated pipeline classifies and writes results to CSV (one cell = one row).

if I find a classifier bug later, I can re-run classification over the saved raw files without re-running any cells (which take way longer). Raw resolution output from package managers should be saved as evidence.



### Important in the `private_resolved` rule
An internal package counts as `private_resolved` **only if it came from the Nexus hosted repo**, NOT from the Nexus proxy repo. Proxy repo = fetching from public = still dangerous.

Judging by URL alone is not always enough: for A1a group repo, all resolutions look like they came from the same group URL. Need to combine URL + resolved package version to know whether it came from the hosted side (internal version) or the proxy side (attacker version).

already documented in methodology (during research proposal)


## 3. confirm the B1 design (package manager configuration) for npm

### The npm constraint
npm does NOT support the logic "try registry A, then registry B if not found" for unscoped packages. It only has:
- one default `registry=` line, and
- optional `@scope:registry=` lines for scoped packages.

this characterstic already reported by paper Gu et al. (2024): npm does not meet the first condition for registry-client DCA.

### My constraints (kept)
- Internal packages stay **unscoped**. Scope-based routing is a security-hardening pattern → outside my research scope ("no hardening applied").
- Will not change my research question or variables. B1 stays at abstract level. each ecosystem realizes it in its own way. Where the realizations differ, the differences are also findings.

### Decision for npm
For B1b/B1c, write **two `registry=` lines** in `.npmrc`. This satisfies the B1 definitions ("multiple registry URLs").


### A × B1 mapping 

| A | B1a | B1b | B1c | B1d |
|---|---|---|---|---|
| A1a | group-public-first | Nexus + public URL | Nexus + proxy URL | no file |
| A1b | group-private-first | Nexus + public URL | Nexus + proxy URL | no file |
| A2  | internal-hosted    | Nexus + public URL | Nexus + proxy URL | no file |
| A3  | internal-hosted    | Nexus + public URL | **INVALID** (no proxy repo exists) | no file |



### Open question 
Whether npm's `.npmrc` parser uses first-key-wins or last-key-wins for duplicate `registry=` keys is not yet answered. My empirical tests today failed because of shell-escaping issues with the test command. Will test properly during pilot phase.

Either result is fine for the thesis:
- First-key-wins → B1b/B1c behave like B1a → confirms the "npm has no fallback" finding.
- Last-key-wins → for A2/A3, public packages may fail to resolve → `resolution_error` outcomes (also a valid finding).

Ordering choice doesn't invalidate the matrix — it just changes what exact outcome each cell produces.


## 4. Wrote `generate_npmrc.py` (used to generate .npmrc file)

**Location:** `automation_process/config_generators/generate_npmrc.py`

**Key points:**
- `A → Nexus repo name` mapping is a dict at the top of the file, one place to change if a Nexus repo is renamed later (will not).
- Handles all 16 A × B1 combinations correctly.
- Raises `ValueError` for A3 × B1c (invalid config) and any unknown A or B1 
- Returns `None` for B1d so the caller knows to skip writing a .npmrc file.
- `__main__` 16 cells and prints the output of cells 

 output for all 16 cells looks correct.


## 5. Drafted `service-ci-nodejs.yml` (NOT tested yet)

**Location:** `.github/workflows/service-ci-nodejs.yml`

**Workflow structure:**
- Triggered manually via `workflow_dispatch` with dropdown inputs: `cell_id`, `A`, `B1`, `B2`, `C1`.
- Runs on the self-hosted runner (`runs-on: [self-hosted, thesis-runner]`).
- Steps:
  1. Checkout the repository.
  2. Echo the cell inputs (for a clear record in the log).
  3. Call `generate_npmrc.py` inline via Python, write result to `services/nodejs/.npmrc`. If B1d → delete any existing file to prevent stale state.
  4. B2 placeholder (TODO — not implemented).
  5. C1 placeholder (TODO — not implemented).
  6. Run `npm install --dry-run --json` in `services/nodejs/`, save output to `<cell_id>_npm_raw.json`. `continue-on-error: true` so a resolution failure does not block the upload step.
  7. Upload the JSON as a workflow artifact.

**Not yet implemneted:**
- B2 (version specifier): needs its own generator later (used to create package.json).
- C1 (operation type): needs lockfile handling and possibly a different command per level.

**How to test (tomorrow):**
1. Push to repo 
2. Actions tab → "Service CI - Node.js" → "Run workflow".
3. Fill the input (in github UI, "run workflow"): `cell_id=pilot001`, `A=A1a`, `B1=B1a`, `B2=B2a`, `C1=C1a`.
4. Watch the run. Verify:
   - Runner picks up the job (status changed from "Queued" to "in progress").
   - "Generate .npmrc" step prints the correct file content.
   - "Run npm install" step produces output in the log.
   - "Upload raw resolution output" succeeds. (the uploaded artifact can be downloaded)
5. Download the `pilot001_npm_raw` artifact from the run summary and inspect the JSON.



## Commands used today

```bash
# Debugging the runner container
docker ps -a --filter name=thesis-runner
docker logs thesis-runner
docker rm -f thesis-runner

# Rebuilding and starting fresh
docker build -t thesis-runner:2.335.1 infrastructure/runner/
docker run -d --name thesis-runner \
  -e GH_REPO_URL=placeholder \
  -e GH_TOKEN=<fresh_registration_token> \
  --add-host=host.docker.internal:host-gateway \
  thesis-runner:2.335.1
docker logs -f thesis-runner

# Testing restart behavior
docker stop thesis-runner
docker start thesis-runner
docker logs --tail 20 thesis-runner

# Testing the generator
python automation_process/config_generators/generate_npmrc.py
```



## Next steps

1. **Test `service-ci-nodejs.yml` end-to-end** with one cell (e.g. A1a + B1a + B2a + C1a). Debug whatever comes up in the first real run.
2. Fix the issue and properly test npm's duplicate-`registry=` behavior.
3. Add B2 handling to the workflow (edit `package.json` version specifier).
4. Add C1 handling (delete or keep `package-lock.json`; possibly switch the install command).
5. Write `generate_pipini.py` (same pattern as `generate_npmrc.py`). (for python service)
6. Write `generate_settings_xml.py` (same pattern). (for java service)



## Open questions
- **npm `.npmrc` package manager resolution behavior** (first-key-wins vs last-key-wins for duplicate `registry=` lines), needs a proper test in pilot phase.
- **Nexus cache invalidation between cells**: need to look up the Nexus REST API endpoint for "invalidate cache" on proxy repos.


# 10.07.2026

## What I did today

### npm B1 design reconsidered and defended (unscoped internal packages)
- Confirmed decision to keep internal node.js packages **unscoped**
- Reason 1: scoping is a security mitigation per npm official docs (https://docs.npmjs.com/threats-and-mitigations) → violates "no security hardening" precondition of Sub-RQ1
- Reason 2: scoping + claiming scope on public npm makes DCA structurally difficult,the attacker cannot publish package under that scope → increase unnessasary difficulties and complexity of the thesis experiment (https://github.blog/security/supply-chain-security/avoiding-npm-substitution-attacks/ (which is linked by npm official documentation))


### Fix npm CI pipeline bugs (multiple)
- **YAML nested-mapping error** on placeholder echoes → fixed by adding `|` block symbols
- **(very important) Command didn't include resolved URLs** → `npm install --dry-run --json` output has no URL field → switched to command with another flag `npm install --package-lock-only` which writes `package-lock.json`, the `resolved` field shows the resolved URL of package -> package name + version + URL can be used for determine package source
- **remove the existing `package-lock.json` from git repo to avoid the influence to the resolution experiment** → added to `.gitignore`, kept local copy (disadvantage: runner is in a docker container, the structure of checkout repo can not be seen that easily)
- **E401 auth error after cleanup (e.g. delete .npmrc, package-lock.json file)** → enabled anonymous read on Nexus (consistent with "no hardening" precondition) -> besides: turn off auth to nexus has no effect to the package manager resolution behavior, remove auth reduce the experiment setup load.

### Rebuilt npm service CI pipeline (workflow) structure 
- Added cleanup step at start of the CI pipeline: `rm -f .npmrc package-lock.json`, `rm -rf node_modules`, `npm cache clean --force` (this is only for development phase, in official experiment phase the whole container will be removed, cache will be discarded before next cell run)
- Upload artifact now contains 2 files: `package-lock.json` (for resolution result classification) + npm log file (for inspect resolution errors)

### npm service CI pipeline test: Ran 7 pilot cells + 1 verification test
- Verified all major (A, B1) combinations work correctly
- Verified invalid configuration situation (will raise ValueError for A3 × B1c)
- Confirmed npm resolution behavior in variables B1b and B1c (see findings below)


## Design decisions confirmed today (will not change anymore)

1. situation in variable B1b and B1c with multiple registry URLs and unscoped: **npm resolves duplicate `registry=` keys as LAST-KEY-WINS** (empirically confirmed, both orderings tested using CI pipeline and inspected the pipeline worklog and uploaded artifacts)
2. **npm resolution is NOT partically** — if any package can not be found in a registry, no `package-lock.json` will be generated, only resolution error will be shown → classifier logic confirmed
3. **Anonymous read enabled on Nexus** 
4. **`package-lock.json` stop commiting to git repo** , otherwise it influence the resolution output of variable C1a "initial install"
5. **resolution Command uses flag `--package-lock-only`** (not `--dry-run` anymore ) 
6. **pip stays as the Python package manager** . already decide during research proposal phase. no Poetry, no Pipenv, no pip-tools will be used in this test application.
7. **Python service keeps `pyproject.toml`** , no migration to `requirements.txt` needed
8. **C1c stays as "rebuild with existing lockfile"** : pip and Maven having no lockfile IS the finding, do NOT weaken to just "rebuild" (in this case it will increase the research scope and not clear enough what means "rebuild")
9. **A2/A3 + B1a cells stay in matrix** : (npm behavioral finding, NOT `invalid_configuration`)
10. **`invalid_configuration` in this thesis defined as physical impossibility** (e.g., A3 × B1c: no proxy repo exists. A3 only have one internal hosted repo.  Maven × B2c: maven doesn't support unspecified package version format)
11. **B1b and B1c .npmrc Ordering test done in pilot phase only**: order here means is private registry URL on the first line of .npmrc, or the public /proxy URL on the first line. The official experiment will always uses private-first ordering.



## Key findings from pilot phase today

### 1. finding: npm cannot semantically express B1b/B1c 
- npm parses duplicate `registry=` keys as last-key-wins
- Under locked "private-first" ordering: private URL is effectively **overwritten** by second URL (npm will only look package in the registry which is in the second line of .npmrc)


### other finding
- npm resolution: when error of finding package, no package-lock.json will be generated
- A3 + B1a and A2 + B1a always produce `resolution_error` when app has public dependencies (the public packages can not be found in private registry -> resolution error)
- A3 + B1d will work, because when no .npmrc is there, npm will search in public registry, if no attacker package -> resolution error, if attack packages are on npm registry -> attacker's package will be solved instead of internal packages
- A1b + B1a resolves correctly from `npm-group-private-first` 


## Commands used today

Repo cleanup for `package-lock.json`:
```bash
echo "services/nodejs/package-lock.json" >> .gitignore
git rm --cached services/nodejs/package-lock.json
git add .gitignore
git commit -m "remove package-lock.json from repo"
git push
```

Nexus anonymous read:
- Administration → Security → Anonymous → check "Allow anonymous users to access the server"
- Verified `nx-anonymous` role has `nx-repository-view-npm-*-read` privileges

Trigger pilot cells after push npm service CI pipeline:
- Enter github repo -> GitHub Actions UI → "Service CI - Node.js" → "Run workflow" → fill input, choose variables

manually verify artifact and resolution result:
- Actions run page → Artifacts → download `<cell_id>_npm_raw.zip` → extract → open `package-lock.json` → confirm `resolved` URLs of internal packages


## Next steps 

### 1. Implement `generate_version_specifier.py` for variable B2
- Modifies `services/nodejs/package.json` per B2 value (pinned / ranged / unspecified)
- B2a: pinned (exact version, e.g. `"1.0.0"`)
- B2b: range (e.g. `"^1.0.0"`)
- B2c: unspecified (e.g. `"*"` or omit version)
- similar pattern as `generate_npmrc.py`

### 2. Solve C1b precondition: publish internal package with different versions to Nexus
- Currently only v1.0.0 published
- another package version should be updated to test variable "package update"

### 3. Add B2 handling step to npm CI pipeline (workflow)

### 4. Add C1 handling step to npm CI pipeline (workflow)
- C1a: delete `package-lock.json` before running (current cleanup already does this)
- C1b: keep lockfile, use `npm update --package-lock-only`
- C1c: keep lockfile, use `npm ci` : verify behavior (may actually install packages)
- above approach not confirmed yet. need to consider the specific approach for each variable

### 5. Publish attacker packages (before official experiment)
- Document in thesis: unique names ensure no accidental resolution by others

### Further steps
- Write `generate_pipini.py` for python service
- Write `generate_settings_xml.py` for java service
- implement pip and Maven service CI pipeline (workflows)

## Open questions 
- Nexus cache invalidation approach between cells 
- Does `npm ci` under `--dry-run` actually work, or does C1c always fully install?

