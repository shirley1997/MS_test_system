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

# 11.07.2026

### Built `generate_npm_version_specifier.py` (for variable B2)
- Location: `automation_process/config_generator/`
- Method: modifies version specifier in `services/nodejs/package.json` in the service directory (unlike `generate_npmrc.py`, which creates a new file)
- Only changes the version specifier of internal packages. public dependencies (`express`, etc.) will stay like it originally is. so experiment environment is stable and fixed.
- B2 mapping: `B2a="1.0.0"` (pinned), `B2b=">=1.0.0 <2.0.0"` (closed range, using primitive operator syntax), `B2c="*"` (unspecified)
- write a test in `__main__` to print the changed content from a temp package.json file, so the real file is untouched during test:
  `python automation_process\config_generator\generate_npm_version_specifier.py`

### Updated `service-ci-nodejs.yml`
- Added `Apply version specifier (B2)` step: calls the generator script for changing version of internal packages, prints the whole modified `package.json` in the workflow log
- Replaced the single `npm install --package-lock-only` step (for dependency resolution) with 3 conditional C1 steps:
  - **C1a**: initial install (`npm install --package-lock-only`)
  - **C1b**: copy the fixed lockfile from `fixed_package_lock/npm-service-fixed.lock.json` to service directory, build the scenario that the developer already installed once. then runs `npm update command only for internal packages.
  - **C1c**: use setup step to generates a fresh lockfile, representing initial install. then runs `npm ci` on it, represent rebuild, then upload the artifacts.
- **C1c edge case**: if setup produces no lockfile (e.g. A3 can't resolve `express`, then resolution error), the step writes resolution error to the log and skips running `npm ci` (because rebuild will also produce the same resolution error.)
- Artifact upload step updated to include both the main log and the C1c setup log. 

### Nexus cache reset + publish v1.0.2 of internal packages (especially for package update situation)
- Chose "delete + recreate `npm-public-proxy`" over cleanup policy or REST API script: simplest way for dev phase, doesn't touch `npm-internal-hosted`
- Had to manually re-add `npm-public-proxy` as a member of both group repos (`npm-group-public-first`, `npm-group-private-first`) with correct ordering
- Published internal packages with version 1.0.2 to nexus


### Pilot cells run: all four passed
| Cell | Result | Meaning |
|---|---|---|
| A1a + B1a + B2b + C1a | Resolved 1.0.2 | B2b + initial install picks highest version which fits the version range |
| A1a + B1a + B2b + C1b | Resolved 1.0.2, express unchanged | `npm update <pkg>` command works |
| A1a + B1a + B2b + C1c | initial install ok, `npm ci` OK, both resolve 1.0.2 | C1c steps works |
| A3 + B1a + B2b + C1c | E404 on express, showd resolution error, no lockfile generated | Edge case |

Also verified B2a distinctly resolves to 1.0.0 (not 1.0.2): B2 has observable effect.

---

## confirmed design decisions 
- **npm version Range syntax for B2b: primitive operators, closed range** — `>=1.0.0 <2.0.0` for npm, analogous per ecosystem (pip: `>=1.0.0,<2.0.0`; Maven: `[1.0.0,2.0.0)`). Same semantics, different notation → cross-ecosystem consistency. other npm version range advanced syntax like Tilde, caret, X-range, hyphen documented as limitation / future work.
- **C1 logic lives in YAML, no Python script needed**: C1 (CI operation type) chooses *which command to run*, no need to write python script. 
- **C1c initial install failure classification**: `resolution_error`. Skips `npm ci` with printing error output. C1c can only be observed when the sinitial install phase succeeds. some A configurations (nexus repo) make rebuil not meaningful because it will produce error during initial install.
- **C1b targets only internal packages** — `npm update <name1> <name2>` explicitly. Keeps environment fixed except for the variable being measured. need to document in methodology.
- **set up the fixed file**: `fixed_package_lock/npm-service-fixed-lock.json`, pinned to internal packages to version 1.0.0. Represent the scenario "developer installed some time ago, now runs package update."
- **Internal package's own `package.json`** : only changed version before republish. already describe the version change from 1.0.0 to 1.0.2 in a commit.

---

## Open questions (for later)

- **pip / Maven C1b design**: without lockfiles, `pip install --upgrade` on an empty env behaves the same as `pip install`. Two options:
  - **Option A**: add "simulate prior install" setup step (like C1c setup) — matrix stays uniform.
  - **Option B**: document as `invalid_configuration` or "C1b degenerates to C1a for pip/Maven".
  - prefer **A**. 
- **Attacker packages** need to publish.
- **Nexus REST API for cache invalidation** , need to implement in the central automated pipeline


## Next steps

**Priority order:**
1. Publish attacker packages
2. Run one B1b or B1c cell end-to-end after publish
3. Start implementing python service CI pipeline (keep the package manager as pip):
   - `generate_pip_version_specifier.py` (modify `pyproject.toml`)
   - `generate_pip_config.py` (create `pip.conf`, Linux runner, INI syntax same as `pip.ini`)
   - Note: pip does NOT auto-discover `pip.conf` in cwd: need `PIP_CONFIG_FILE=./pip.conf pip install …` in workflow
   - `service-ci-python.yml`
   - Decide pip C1b design (Option A vs B)
4. **Maven service** — `generate_maven_version_specifier.py` (modify `pom.xml`), `generate_settings_xml.py`, `service-ci-java.yml`. Remember: Maven × B2c (unspecified version) invalid, Maven × C1c (rebuild with lockfile) invalid.
5. Then central automated pipeline (Python script on Windows dev machine)
6. **Then official experiment run.**

# 13.07.2026

## Published malicious packages (v1.0.3) to public registries


Payload is harmless (single line, `console.log("hello world")` / `print("hello world")`) . matches the thesis proposal: DCA success depends on package manager resolution behavior, not on the payload.

### npm registry: published to `registry.npmjs.org`

- same Package names as internal packages -> intentionally selected, will not accidentally used by others
- Files per package: `package.json` + `index.js`
- Steps:
  1. Created npm account + enabled 2FA
  2. Logged in from terminal:
     ```
     npm login --registry https://registry.npmjs.org/
     ```
  3. Published from each package folder:
     ```
     npm publish --access public --registry https://registry.npmjs.org/
     ```
- Verified on account

### PyPI: published to `pypi.org`

- same Package names as internal package of python service
- Files per package: `pyproject.toml` (no dependencies) + `README.md` + `src/<module_name>/__init__.py`
- Note: hyphens used in package distribution name, **underscores** in Python module folder
- Steps:
  1. Created PyPI account + enabled 2FA 
  2. Generated API token using pypi UI (scope: entire account)
  
  3. Built the malicious package from each folder:
     ```
     python -m build
     ```
     → produces `.whl` and `.tar.gz` in `dist/`
  4. Uploaded from each folder use twine (need to activate venv of python service because all tools like twine are installed in python venv):
     ```
     twine upload dist\*
     ```
     - Username: `__token__`
     - Password: PyPI API token (`pypi-...`)
- Verified on account


- Every `npm publish` / `twine upload` uses explicit `--registry` / public repository URL to prevent sending to the wrong registry.

### Also published today: internal v1.0.2 for Python service in Nexus

- changed version number in pyproject.toml `version = "1.0.2"` in each (described in a commit)
- Rebuilt with `python -m build` 
- only uploaded v1.0.2 to Nexus `pypi-internal-hosted` via `twine upload --repository-url http://localhost:8081/repository/<pypi-hosted-repo-name>/ dist\*1.0.2*`

### Experimental validation

Ran cell `A1a (group repo) + B1b (multiple URL) + B2b ((closed range) + C1a (initial install)` in the npm CI pipeline → both internal package names resolved to attacker version `1.0.3` from `registry.npmjs.org` 


# 14.07.2026

## Built `generate_pipconf.py` (for variable B1, Python service)


- Same pattern as `generate_npmrc.py`: takes `A`, `B1`, `nexus_url` → returns pip.conf string / `None` (B1d) / raises `ValueError` (invalid combo or A3 × B1c)
- `A → Nexus repo` mapping is a dict at top of file (single source of truth if repo renamed)
- Runner is Ubuntu 24.04 → generated file is `pip.conf` (Linux name). Local dev on Windows uses `pip.ini` — same INI syntax, just OS-specific filename.


## Key design decisions

### 1. URLs must end with `/simple/`
- pip talks to a PEP 503 "Simple Repository API", not the human-browsable website
- `https://pypi.org/` = website, `https://pypi.org/simple/` = index pip actually reads
- Same for Nexus: `/repository/<repo>/simple/`
- Refs: PEP 503 (https://peps.python.org/pep-0503/), pip docs `--index-url` (https://pip.pypa.io/en/stable/cli/pip_install/)

### 2. pip semantics ≠ npm semantics (important for later interpretation)
- npm: last-key-wins for duplicate `registry=` → cannot express multi-URL fallback (already found in npm pilot phase)
- pip: `index-url` + `extra-index-url` are queried **in parallel**, pip picks highest version across all indexes
- → pip B1b/B1c will produce real multi-URL resolution behavior. 
- Ref: pip docs `--extra-index-url` ("Extra URLs of package indexes to use in addition to --index-url")

### 3. A × B1 matrix (analogous to npm)
| A | B1a | B1b (Nexus + pypi.org) | B1c (Nexus + proxy) | B1d |
|---|---|---|---|---|
| A1a | `pypi-group-public-first` | + pypi.org/simple | + `pypi-public-proxy` | no file |
| A1b | `pypi-group-private-first` | + pypi.org/simple | + `pypi-public-proxy` | no file |
| A2  | `pypi-internal-hosted` | + pypi.org/simple | + `pypi-public-proxy` | no file |
| A3  | `pypi-internal-hosted` | + pypi.org/simple | **INVALID** (no proxy) | no file |

- Same 1 invalid combination (A3 × B1c) 

### 4. Where the generated `pip.conf` will live in CI
- **Written to `services/python/pip.conf`** in the workspace 
- **YAML set envirnoment variable `PIP_CONFIG_FILE=${{ github.workspace }}/services/python/pip.conf`** so pip can find pip.conf
- Reason: pip does **NOT** auto-discover `pip.conf` in cwd. It only reads Global / User / Site (venv) paths, or whatever `PIP_CONFIG_FILE` points to.
- Ref: pip docs Configuration (https://pip.pypa.io/en/stable/topics/configuration/)
- implementing the path explicit in YAML also makes it visible (for debugging)



## Commands used

```powershell
# Verify where pip actually reads config from
pip config debug

# Run the pip.conf generator (prints the file content of all cells)
python automation_process\config_generators\generate_pip_conf.py
```

## Next steps

1. Write `generate_python_version_specifier.py` (for variable B2 , modifies `pyproject.toml` : pinned / closed range / unspecified)
2. Draft `service-ci-python.yml`
3. Decide pip C1b design (Option A "simulate prior install" vs Option B "degenerates to C1a") 
4. Pilot cells for Python service


# 15.07.2026 Implement python service CI pipeline

## Built `generate_python_version_specifier.py` (variable B2, Python service)

Method: **generate whole `pyproject.toml` from a hardcoded template**, not partly edit of the existing file (already add the existing pyproject.toml file into .gitignore -> otherwise it will affect the experiment)

Reason: TOML editing needs a package `tomlkit` . Template = pure stdlib, no install step in runner.


### version specifier syntax comparison
| B2 | npm form | Python form |
|---|---|---|
| B2a pinned | `"1.0.0"` | `==1.0.0` |
| B2b closed range | `">=1.0.0 <2.0.0"` (space) | `>=1.0.0,<2.0.0` (**with comma**) |
| B2c unspecified | `"*"` | `""` (only package name, no version needed) |

- Refs:
  - python version specifier syntax: https://packaging.python.org/en/latest/specifications/version-specifiers/
  - Dependency spec / unspecified version: https://packaging.python.org/en/latest/specifications/dependency-specifiers/
  - pyproject.toml guide: https://packaging.python.org/en/latest/guides/writing-pyproject-toml/
- Key sentence for B2c (unspecified): "Sometimes this is very loose, just specifying a name" ([Link](https://packaging.python.org/en/latest/specifications/dependency-specifiers/))

### Structural difference from npm
- npm: `"pkg": "1.0.0"` → package name is JSON key, version is separate value → `json` module swaps values directly
- Python: `"pkg==1.0.0"` → name + specifier in one string in a list

## Built pip CI pipeline (to C1a done)

### Steps done today:
1. **Cleanup step** : clears cache between cells: (installed packages also need to be removed between cells)
   ```bash
   rm -f pip.conf pyproject.toml
   pip cache purge || true
   ```
2. **Generate pip.conf step** :calls `generate_pip_conf(A, B1, nexus_url)`, writes to `services/python/pip.conf`, or no file generated if variable B1d
3. **Generate pyproject.toml step** : calls `generate_python_version_specifier(B2, path)` -> generate file
4. **C1a step (initial install )**: see command below

### The pip resolution command (C1a)
```bash
pip install --dry-run --ignore-installed --report install-report.json .
```
- `--dry-run` → resolve only, no download/install
- `--ignore-installed` 
- `--report install-report.json` → structured JSON output per resolved package: name, version, and **`download_info.url`** -> can determine resolved package source
- `.` → resolves packages from `pyproject.toml` in cwd
- Piped with `2>&1 | tee` to also show human-readable log for debugging
- Refs:
  - https://pip.pypa.io/en/stable/cli/pip_install/
  - https://pip.pypa.io/en/stable/reference/installation-report/
- Docs quote: "The install command has a `--report` option that will generate a JSON report of what pip has installed. In combination with the `--dry-run` and `--ignore-installed` it can be used to _resolve_ a set of requirements without actually installing them."

### Design decision: `PIP_CONFIG_FILE` as a env var set at YAML env level (not in "run: script" part)
let this env var point to the pip.conf file inside the python service directory
- Set as `env:` visible to the pip process. for B1a, B1b, B1c.
- Conditional trick using `&&`/`||` (GitHub Actions has no ternary):
  ```yaml
  env:
    PIP_CONFIG_FILE: ${{ inputs.B1 != 'B1d' && format('{0}/services/python/pip.conf', github.workspace) || '' }}
  ```
  - B1a/B1b/B1c → path to generated pip.conf
  - B1d → empty (pip falls back to default discovery = no user config = plain https://pypi.org/simple/)
- Ref: https://docs.github.com/en/actions/how-tos/write-workflows/choose-what-workflows-do/use-variables#defining-environment-variables-for-a-single-workflow   (Github: for set up env in a workflow)

### Artifacts uploaded per cell (need to consider)
| Role | npm | pip |
|---|---|---|
| Config input | `.npmrc` | `pip.conf` |
| Manifest input | `package.json` | `pyproject.toml` |
| Structured resolution output | `package-lock.json` | `install-report.json` |
| Log (for debugging) | `_npm_log.txt` | `_pip_log.txt` |



## Open questions for tomorrow (C1b, C1c)

### C1b (package update) — design agreed, needs to be implemented
- Idea: 2-phase in one workflow step
  - Phase 1 (setup, REAL package install): copy fixed file `pyproject.toml` (internal packages pinned `==1.0.0`) → `pip install --target ./deps .` → creates "already-installed 1.0.0" state on disk
  - Phase 2 (observe package update resolution, DRY-RUN): `pip install --dry-run --target ./deps --upgrade <internal packages> .` with `PYTHONPATH=./deps` so pip's resolver sees the installed state
- Why setup phase is necessary:
  - Docs quote: "Without `--upgrade`, the resolver will only see the installed version as a candidate."
  - Without prior installed state, `--upgrade` has no effect → C1b would be identical to C1a → not a distinct experimental condition
  - **Still need to confirm empirically in pilot!!** 
- `--upgrade-strategy` NOT specified → default option is `only-if-needed`, upgrades only listed packages, leaves everything else alone (avoid `eager`; docs explicitly warn away from `to-satisfy-only`)
- Refs:
  - https://pip.pypa.io/en/stable/cli/pip_install/
  - https://pip.pypa.io/en/stable/development/architecture/upgrade-options/
- TODO tomorrow: write C1b YAML block

### C1c (rebuild with lockfile): INVALID for pip
- pip has no native lockfile equivalent to `package-lock.json`
- → C1c is an ecosystem-asymmetry finding

- TODO tomorrow: extend validation step

# 23.07.2026 start building java service CI pipeline

## What I have done today
- Decided the Java-side config strategy: put **everything (A × B1 × B2) into `pom.xml`**, do **not** use `settings.xml`. Reason: Maven's resolver builds one "effective repo list" regardless of source. Keeping it in one file avoids risk of `settings.xml` and `pom.xml` disagreeing, and CI step becomes plain `mvn <goal>` (no `-s` flag).
- Checked existing `settings.xml` on host machine:
  - `Get-Item ~\.m2\settings.xml` → found at  (user-level
  
  - Host `settings.xml` files are irrelevant for the CI pipeline: self-hosted runner container has its own filesystem and only sees the checked-out repo.
- Implemented `generate_pom_xml.py` (at `automation_process\config_generator\`). Hardcoded template approach, pure stdlib, similar to the style of `generate_pip_conf.py` + `generate_python_version_specifier.py` combined into one script.
- Untrack `pom.xml` from git but kept locally -> keep experiment environment clean and stable

## Design decisions and reasons
- **A → Nexus repo mapping** :
  - `A1a → maven-group-public-first`
  - `A1b → maven-group-private-first`
  - `A2 → maven-internal-hosted`
  - `A3 → maven-internal-hosted`
- **B1 via `<repositories>` block in `pom.xml`**:
  - `B1a`: `<id>central</id>` override → Nexus private URL (blocks direct Maven Central) + private repo entry
  - `B1b`: only private repo entry; super POM's Central stays (= internal + direct Central alongside)
  - `B1c`: `<id>central</id>` override → `maven-public-proxy` URL + private repo entry (internal + Nexus proxy of Central)
  - `B1d`: no `<repositories>` block → super POM's Central applies 
- **B2 via `<version>` on internal deps**:
  - `B2a`: `1.0.0` (pinned)
  - `B2b`: `[1.0.0,2.0.0)` (closed range)
  - `B2c`: **invalid combination in Maven** — `<version>` is a required element per POM schema. Ecosystem asymmetry finding 
- **Invalid combinations** flagged by the generator (raise `ValueError` with descriptive message, central pipeline will skip before official experiment):
  - `A3 × B1c` (A3 has no proxy repo)
  - any cell with `B2c` (Maven cannot express "unspecified version")
- **Both internal packages**version specifier need to be changed per cell.

## Findings / notes worth capturing
- **Ecosystem asymmetry #3 candidate — Maven B2c**: pip has `""`, npm has `"*"`, Maven has no true "unspecified" version. Alternatives are not equivalent:
  - Open range `[0,)` — still a formal specifier, not "no constraint"
  - `LATEST` / `RELEASE` — deprecated in Maven 3+, uses `maven-metadata.xml` markers, different resolution mechanism
  - Truly empty `<version>` — rejected by POM schema (`'dependencies.dependency.version' for X is missing`)
  - Root cause: Maven's version model treats specifiers as **declarative hard requirements**, not filters over available versions. "Unspecified" is structurally not meaningful.
- **Maven mirror mechanism**: not used in the experiment (holds config mechanism constant across B1 cells via `<repositories>` in `pom.xml`). Worth noting descriptively in the foundation chapter as an ecosystem-descriptive observation.
- **Maven repository lookup order** (step 4 of resolution): official documentation does not clearly specify the ordering rule for remote-repo iteration. Verify empirically in pilot phase and cite own observation.

## Next steps
- Continue B2c / version specifier discussion (read lockfile docs first).
- Decide on `maven-lockfile` plugin for C1c (main matrix stays invalid for Maven; plugin as supplementary study, parallel to pip 26.1 plan). **Discuss with supervisor.**
- Upload internal `1.0.2` to Nexus and attacker `1.0.3` to Maven Central 
- Run pilot cells for the Java pipeline once the CI YAML is built.
- Consider custom `InvalidCombination(ValueError)` exception class so the central pipeline can distinguish "structural skip" from "unknown value / caller bug" 

## Reference links collected today
### Maven official documentation
- Setting up Multiple Repositories: https://maven.apache.org/guides/mini/guide-multiple-repositories.html
- Super POM: https://maven.apache.org/guides/introduction/introduction-to-the-pom.html#Super_POM
- Introduction to the Dependency Mechanism: https://maven.apache.org/guides/introduction/introduction-to-dependency-mechanism.html
- Dependency Management: https://maven.apache.org/guides/introduction/introduction-to-dependency-mechanism.html#Dependency_Management
- Introduction to Repositories: https://maven.apache.org/guides/introduction/introduction-to-repositories.html
- POM Reference: https://maven.apache.org/pom.html
- Dependency Version Requirement Specification: https://maven.apache.org/pom.html#dependency-version-requirement-specification
- Version Order Specification: https://maven.apache.org/pom.html#version-order-specification
- Settings Reference: https://maven.apache.org/settings.html
- Mirror settings guide (not used, needed for foundation chapter): https://maven.apache.org/guides/mini/guide-mirror-settings.html
- Enforcer plugin version ranges: https://maven.apache.org/enforcer/enforcer-rules/versionRanges.html

### Community / supporting sources
- GitHub issue on unspecified version (sqlbrite #193): https://github.com/square/sqlbrite/issues/193
- Stack Overflow — Maven dependency without version: https://stackoverflow.com/questions/29476472/maven-dependency-without-version
- OpenRewrite — list effective Maven repositories: https://docs.openrewrite.org/recipes/maven/search/effectivemavenrepositories
- Oracle blog — Mastering Maven resolving dependencies: https://blogs.oracle.com/developers/mastering-maven-resolving-dependencies

### non-official maven Lockfile Doc
- maven-lockfile plugin: https://github.com/chains-project/maven-lockfile
- maven-lockfile on Sonatype Central: https://central.sonatype.com/artifact/io.github.chains-project/maven-lockfile
- Paper: Maven-Lockfile: High Integrity Rebuild of Past Java Releases: https://arxiv.org/abs/2510.00730


# 24.07.2026 continue building `generate_pom_xml.py` (used for java service CI pipeline)

## What I have done today
- Verified yesterday's `generate_pom_xml.py` output: ran it across all 48 combinations (4 A × 4 B1 × 3 B2), all 30 valid outputs are well-formed XML, all 18 invalid combinations correctly raise `ValueError` (16 with B2c, 2 with A3 × B1c).
- Refactored `build_repositories_block()` to fix two issues:
  - **B1a**: dropped the redundant second `<repository>` entry. Now single entry with `<id>central</id>` → private URL.
  - **B1c**: kept `<id>central</id>` as the *override mechanism* (not renamed to `maven-public-proxy` as I initially wanted), Maven merges repositories by id — renaming would let Super POM's real Central sneak back into the effective repo list. (need to verify this in pilot phase!!)
  - **Private repo `<id>`**: renamed from generic `nexus-private` to the actual Nexus repo name (e.g. `maven-group-public-first`) so the generated `pom.xml` self-documents which variable A it maps to.
- **B1b**: explicit `<id>central</id>` → `https://repo.maven.apache.org/maven2` + private repo entry. Technically overrides Super POM with identical URL, but declared explicitly for readability.


## Design decisions and reasons
- **Uniform mechanism across B1a/B1b/B1c**: every non-B1d variant uses `<id>central</id>` override + optional private repo entry. Only URLs differ. B1d = no `<repositories>` block (which means Super POM inherit)
- merging by id is how you overwrite Super POM's Central from inside `pom.xml` (without `settings.xml` or `<mirrors>`). This is now documented in code comments and will justified in the thesis methodology chapter.
- **New finding candidate — id mismatch as silent misconfiguration**: if a developer names their private repo entry anything other than `central`, Super POM's Central maybe stays inherited, so their attempt to "replace Central" silently becomes "add another repo alongside Central." This makes the `<id>` itself part of variable B1 (package manager configuration), not just an implementation detail. Worth its own sub-finding. (need to verify this!!)

## Verification commands (for pilot phase)
- Show merged effective POM (verifies id-merge worked):
  ```bash
  mvn help:effective-pom
  ```
- Or targeted (only the repositories section):
  ```bash
  mvn help:evaluate -Dexpression=project.repositories
  ```
- Confirm no real network hit to Central under B1a / B1c:
  ```bash
  mvn -X <goal> 2>&1 | grep repo.maven.apache.org
  ```
  (expect zero hits when `<id>central</id>` is overridden away from real Central)


## Next steps
- Run pilot cells with all four B1 variants × one A value to empirically verify override behavior matches intent (especially B1a and B1c "no real Central" claim).
- Add a small companion experiment: same URL, same block, only `<id>` differs (`central` vs. e.g. `nexus-private`) — measure whether resolution outcome changes. Turns the id-mismatch observation into a measured result.
- Start writing the Java service CI YAML (`.github/workflows/service-ci-java.yml`), similar to the structure of the nodejs and python service pipeline.
- Continue discussion on `maven-lockfile` plugin for C1c supplementary study.

## Reference links collected today
### Maven official
- Super POM content(Maven 3.9.16): https://maven.apache.org/ref/3.9.16/maven-model-builder/super-pom.html

### Semi-official / supporting sources for override mechanism
- Sonatype "Maven: The Complete Reference", Ch. 3 – The Project Object Model: https://www.sonatype.com/maven-complete-reference/project-object-model#mavenref3-2-3
  - Confirms Super POM's Central can be overridden, but only shows `settings.xml` example; does NOT explicitly document the `pom.xml` id-merge override.
- Sonatype Central – Consume Central with Apache Maven: https://central.sonatype.org/consume/consume-apache-maven/
  - Shows the override technique with the inline comment "Override the repository (and pluginRepository) 'central' from the Maven Super POM" — but uses `settings.xml`, not `pom.xml`.
- Apache Maven JIRA MNG-6772: https://issues.apache.org/jira/browse/MNG-6772
  - Developer-level confirmation of the id-merge override mechanism ("My projects define a repository with `<id>central</id>`, which is meant to specifically override the entry in the Super POM").

# 25.07.2026 Publishing java internal Packages (version 1.0.2) to Nexus

## Goal
Publish two internal Java packages to self-hosted Nexus as version **1.0.2** (previously published as 1.0.0).

## Steps 

- **Bumped the version** in each `pom.xml` from `1.0.0` to `1.0.2`
- **Checked `distributionManagement`** in `pom.xml` points to my Nexus repo (maven-internal-hosted)
- **Started the Nexus container** (forgot at first → got `Connection refused` error)
- **Ran `mvn clean deploy`** in each package directory

## Result
Both packages now show versions **1.0.0** and **1.0.2** in Nexus 

## Lesson Learned
Always make sure the Nexus container is running **before** deploying.


# 26.07.2026 Build Java service CI pipeline (`.github/workflows/service-ci-java.yml`)

## What I have done today
- Built the Java service CI YAML, use the similar structure and steps of the Python, nodejs pipeline (same steps, same input variables A / B1 / B2 / C1, same artifact uploaded). 
- not tested yet
- **Cleanup step**: shared `~/.m2/repository` kept across cells (plugins + public deps stay cached → fast), only internal packages purged between cells:
  ```bash
  rm -rf ~/.m2/repository/<INTERNAL_GROUPID_PATH> || true
  ```
- **Generate `pom.xml` step**: calls `generate_pom_xml(A, B1, B2, nexus_url)`. On `ValueError` (A3×B1c or any B2c), writes `_invalid.txt` instead and moves on, no `pom.xml` written for that cell.
- **C1a step** (initial resolve)
  ```bash
  mvn -B org.apache.maven.plugins:maven-dependency-plugin:3.11.0:tree \
    -DoutputFile="<cell_id>_dependency-tree.json" \
    -DoutputType=json
  ```
- **C1b step** (2-phase, first install, then update)
  - Phase 1: change `pom.xml` → `fixed_pom.xml` (pinned `1.0.0`), run `dependency:tree` → populates `~/.m2` with 1.0.0 state.
  - Phase 2: restore cell `pom.xml` (with B2 specifier), run `dependency:tree` with `-U` to force metadata re-check against Nexus.
- **C1c step** (INVALID for Maven main matrix, mirrors Python C1c): writes `_invalid.txt` inline. No separate `check_invalid` step (removed for symmetry with Python pipeline).
- **Upload artifacts**: `pom.xml`, mvn logs, dep-tree JSONs, invalid marker.

## Design decisions and reasons
- **`dependency:tree` instead of `dependency:resolve`**: walks transitive graph, downloads POMs (small XML) but not JARs → fast, no package build/install. Closest thing to pip and npm's `--dry-run` for Maven.
- **JSON output**: supported since `maven-dependency-plugin` 3.7.0. easier for the central automated pipeline's classifier than other format
- **dependency Plugin version pinned to 3.11.0** through fully-qualified `groupId:artifactId:version:goal` form. Reason: short-form `dependency:tree` uses whichever version Super POM binds → could be < 3.7.0 → JSON silently fails. Also matches the "pin every tool version" rule from 26.06.
- **`-B` (batch mode)**: no ANSI colors, no progress bar animation → clean, grep-friendly CI logs (needed for parsing `Downloading from <repoId>: <URL>` lines).
- **`-U` in C1b phase 2**: forces metadata re-check. Without it, client-side release-metadata cache (default 24h TTL) could silently short-circuit the update, even though Nexus proxy's metadata TTL is already 0.
- **Shared `~/.m2` + remove internal packages only before each cell run**: keeps plugins/public deps cached (fast pilot iteration), but forces re-resolution of internal packages every cell.
- **Classifier signal**: (1) `dependency-tree.json` → resolved package name + version (2) `mvn_log.txt` → `Downloading from <repoId>: <URL>` lines → resolution source.

## Open question / to discuss with supervisor 
- **C1c strategy**: whether to keep C1c invalid for pip and Maven (current) or include lockfile technologies in the **main matrix** — npm `package-lock.json` (native) + pip `pylock.toml` (pip v26, PEP 751, experimental) + Maven `maven-lockfile` plugin (third-party, from arxiv paper 2510.00730). Trade-off:
  - Adds ecosystem coverage + "lockfile maturity " as an explicit finding.
  - Costs: rebuild runner container image (for new pip version), read + defend maven-lockfile plugin in methodology chapter, add paper to related work. add short paragraph to foudation chapter
  - Rough estimate: ~3–5 days for pip pylock, ~4–6 days for maven-lockfile.

## Next steps

- [ ] **Discuss C1c lockfile strategy with supervisor** before touching pipelines further.
- [ ] **Run pilot cells** for the current Java CI pipeline:
  - Start with a valid combination, e.g. `A=A1a, B1=B1a, B2=B2a, C1=C1a`.
  - Then verify invalid combinations correctly produce `_invalid.txt`: `A3×B1c`, any `B2c`, any `C1c`.
- [ ] **Verify override behavior empirically** (from 24.07 next steps, still open):
  ```bash
  mvn help:effective-pom
  mvn -X <goal> 2>&1 | grep repo.maven.apache.org
  ```

## Reference links collected today
- Maven Dependency Plugin `tree` mojo (JSON output format since 3.7.0): https://maven.apache.org/plugins/maven-dependency-plugin/tree-mojo.html
- Dependency tree output formats: https://maven.apache.org/plugins/maven-dependency-plugin/examples/tree-mojo.html


# 01.08.2026 Java namespace verification question (before uploading attacker packages to Maven Central)

## What I have done today
- Investigated Maven Central's **namespace verification rule**. Confirmed there are only **two** verification methods:
  1. **DNS TXT record** — for domain-shaped groupIds like `com.xueting.thesis`. Requires proof of domain ownership.
  2. **Code-hosting verification** — for `io.github.<user>`, `io.gitlab.<user>`, `io.bitbucket.<user>`, `io.gitee.<user>`. Auto-verified via OAuth if you signed up on Sonatype Central with that platform.
- Ruled out DNS-based verification for the experiment: I don't own `xueting.com`, and buying a short-term domain would expire → harms reproducibility of the thesis artifacts.
- Ruled in **code-hosting verification with my own GitHub account** → groupId `io.github.shirley1997.thesis`.
- Worked through the story problem: since `io.github.<user>.*` namespaces are structurally 1:1 bound to a GitHub identity, the ONLY way this collision (of namespace) can arise in the real world is via GitHub account takeover, which is **dependency hijacking**, not Birsan-style dependency confusion. I initially thought this made the experiment invalid.
- Resolved this by **reframing the threat model** to be resolver-centric rather than attack-centric (details below).

## Design decision
- **Use `io.github.shirley1997.thesis` as groupId for BOTH internal packages (published to Nexus) AND attacker packages (published to Maven Central).**
  - Reason: my GitHub account is the only namespace I can verify persistently and reproducibly, without any recurring cost or dependency on domain renewal.
  - Reason: dual-role of the same identity is an experimental artifact, not a modeling claim about the attacker's real-world capability.
- **Reframe threat model from attack-centric to resolver-centric.**
  - Instead of claiming "the attacker performs dependency confusion", claim: *the resolver operates on a collision state at Maven Central; multiple upstream threat models (Birsan-style confusion, dependency hijacking, insider threats, expired-domain namespace transfer) all produce the same collision state; resolver behavior is invariant to which mechanism caused the collision*.
  - This makes using my own account for both roles fully consistent with the threat model.

## Where to justify in the thesis (chapter mapping)
- **Foundation chapter** (short paragraph): introduce dependency confusion (Birsan) and explain why Maven's hierarchical + verified namespace is structurally more resistant than npm/PyPI's flat namespaces. → ecosystem asymmetry finding candidate.
- **Threat model section** (early in methodology chapter): explicit resolver-centric framing. State clearly what is in scope (resolver behavior given a collision) and what is out of scope (registration-side attacks: how the collision was created, MFA bypass, PGP forgery, Sigstore forgery, etc.).
- **Implementation chapter** (short note when documenting Maven Central publishing): one or two sentences explaining that `io.github.shirley1997.thesis` was verified via GitHub OAuth code-hosting verification, and that the same namespace is used for both victim and attacker packages as motivated in the threat model section.

## Sub-finding candidate (internal ecosystem asymmetry within Maven Central)

  - Code-hosting namespaces are 1:1 bound to an OAuth-verifiable account → inherit account-security risks (takeover, session hijack).
  - Domain-shaped namespaces are bound to a transferable domain → inherit domain-market risks (expiry, resale, DNS takeover).
- Worth noting in the findings chapter as an INTERNAL asymmetry within Maven Central, orthogonal to the cross-ecosystem asymmetries with npm/PyPI.

## Next steps
- [ ] **Change groupId** in both internal package `pom.xml` files: `com.xueting.thesis` → `io.github.shirley1997.thesis`. Then republish versions `1.0.0` and `1.0.2` to Nexus.
- [ ] Verify the namespace on Sonatype Central Portal:
  - Sign in with GitHub OAuth on https://central.sonatype.com
  - Check for the auto-verified `io.github.shirley1997` namespace on the Namespaces page
- [ ] Prepare the attacker version of internal packages (bump to `1.0.3`, keep same groupId + artifactIds, distinguishable content for the classifier).
- [ ] Configure `distributionManagement` in attacker package `pom.xml` to point to Sonatype Central (staging).
- [ ] Add PGP signing (Maven Central requires signed artifacts) — new step, not needed for Nexus deploys.
- [ ] `mvn clean deploy` the attacker packages to Maven Central staging, then release.

## Reference links collected today
- Why verify project ownership (Sonatype FAQ): https://central.sonatype.org/faq/verify-ownership/
- Register a namespace (Sonatype docs): https://central.sonatype.org/register/namespace/
  - Notes the automatic `io.github.<username>` provisioning when signing up via GitHub OAuth
  - Documents the two verification paths: DNS TXT for domains, code-hosting for `io.github` / `io.gitlab` / etc.



# 02.08.2026 upload package to maven & republish internal java package using new groupID

## Published public Java packages to Maven Central

- Logged in to [Maven Central Portal](https://central.sonatype.com/) with my GitHub account.
- Verified the namespace `io.github.shirley1997` by following the [namespace verification guide](https://central.sonatype.org/register/namespace/).
  - This namespace also permits the child namespace `io.github.shirley1997.thesis`.
- Prepared both harmless public research packages as version `1.0.3`:
  - `io.github.shirley1997.thesis:xueting-thesis-event-juhe:1.0.3`
  - `io.github.shirley1997.thesis:xueting-thesis-result-fanhui:1.0.3`
- Updated each `pom.xml` according to the [Maven Central publishing requirements](https://central.sonatype.org/publish/requirements/):
  - Removed the internal Nexus `<distributionManagement>` block.
  - Added project URL, MIT licence, developer information, and GitHub SCM information.
  - Added source JAR, Javadoc JAR, artifact signing through GPG, and Central publishing configuration.
- Used these Maven plugins:
  - [Maven Source Plugin](https://maven.apache.org/plugins/maven-source-plugin/usage.html) to generate `-sources.jar`.
  - [Maven Javadoc Plugin](https://maven.apache.org/plugins-archives/maven-javadoc-plugin-3.8.0/usage.html) to generate `-javadoc.jar` (plugin version `3.12.0` was used).
  - [Maven GPG Plugin](https://maven.apache.org/plugins/maven-gpg-plugin/usage.html) to sign the POM and JAR files.
  - [Central Publishing Maven Plugin](https://central.sonatype.org/publish/publish-portal-maven/) to upload packages to the Central Portal.
- Installed [GnuPG](https://gnupg.org/download/index.html#sec-1-2), generated a signing key, and uploaded only its public key to keyserver for verification:

  ```powershell
  gpg --keyserver keyserver.ubuntu.com --send-keys KEY-ID-STRING
  ```

  Output:

  ```text
  gpg: sending key 62B0CB49CA62BECB to hkp://keyserver.ubuntu.com
  ```

- Created the Maven Central user token `xueting-maven-publishing` on the [Central Portal token page](https://central.sonatype.com/usertoken) and stored it locally in `~/.m2/settings.xml` under server ID `central`.
- Verified both packages before deployment:

  ```powershell
  mvn clean verify
  ```

  Important output:

  ```text
  Signer 'gpg' is signing 4 files with key default
  BUILD SUCCESS
  ```

  Four signature files were generated for each package: main JAR, sources JAR, Javadoc JAR, and POM.
- Committed only source-controlled files such as `.gitignore`, `README.md`, `LICENSE`, `pom.xml`, and `src/`.
  - Ignored `**/target/` and did not commit generated JARs, `.asc` files, credentials, tokens, or private GPG material.
- Uploaded each package for validation:

  ```powershell
  mvn clean deploy
  ```

- Kept `<autoPublish>false</autoPublish>` as a safety decision.
  - Reason: the Central Portal validates the deployment first, so the coordinates can be checked before the permanent publication.
- Checked both coordinates in the Central Portal and manually clicked **Publish**.
  - Result: both public version `1.0.3` packages were successfully published.

## Rebuilt and republished internal Nexus packages

- Design decision: internal and public packages must use the same `groupId` and `artifactId` for the DCA experiment; only their versions and repository locations differ.
- Changed the internal package coordinates from `com.xueting.thesis` to:

  ```text
  io.github.shirley1997.thesis
  ```

- Final version design:
  - Internal Nexus packages: `1.0.0` and `1.0.2`.
  - Public Maven Central packages: `1.0.3`.
- Deleted the four old components from `maven-internal-hosted`, but kept the Nexus repository itself.
- Changed Java source directories and package declarations to:

  ```text
  src/main/java/io/github/shirley1997/thesis/
  ```

  ```java
  package io.github.shirley1997.thesis;
  ```

- Deleted generated `target/` directories with `mvn clean`; Maven regenerated them during the builds.
- Built, tested, and deployed versions `1.0.0` and `1.0.2` of both internal packages:

  ```powershell
  mvn clean test
  mvn deploy
  ```

- Successful Nexus deployment output included:

  ```text
  Uploaded to nexus-internal: http://localhost:8081/repository/maven-internal-hosted/io/github/shirley1997/thesis/xueting-thesis-event-juhe/maven-metadata.xml
  BUILD SUCCESS
  ```

- Verified in Nexus that both packages contain versions `1.0.0` and `1.0.2` under `io/github/shirley1997/thesis/`.

## Configuration-isolation decision

- Maven automatically reads the current machine's `~/.m2/settings.xml`, but the Windows settings file is not available inside the GitHub Actions runner container.
- Therefore, the local Maven Central credentials do not affect the experiment pipeline.
- Repository blocks generated in the service `pom.xml` control dependency resolution during the experiment.
- Before the official experiment, the runner should still be checked for unexpected user settings:

  ```bash
  ls -la ~/.m2
  mvn help:effective-settings
  ```

##  Java service rebuild

- Changed both internal dependency declarations in the Java service to the new group ID:

  ```xml
  <groupId>io.github.shirley1997.thesis</groupId>
  ```

- Planned clean rebuild commands:

  ```powershell
  mvn clean
  Remove-Item -Recurse -Force "$HOME\.m2\repository\io\github\shirley1997\thesis\xueting-thesis-event-juhe" -ErrorAction SilentlyContinue
  Remove-Item -Recurse -Force "$HOME\.m2\repository\io\github\shirley1997\thesis\xueting-thesis-result-fanhui" -ErrorAction SilentlyContinue
  mvn -U clean verify
  mvn dependency:tree
  ```


- After a successful build, the Spring Boot service can be started.


# 08.08.2026 Upgrade pip to 26.2.1, fix runner version auto-update bug, implement `pip lock` for Python C1c

**Stand: pip 26.2.1 instead of pip 25.1.1 running in both the runner image and my Windows dev environment. Runner no longer force-updates itself. Python CI pipeline variable C1c ("rebuild with existing lockfile") is no longer `invalid_combination`. it now uses pip's experimental `pip lock` command (PEP 751). Node.js CI pipeline also got two small consistency fixes while reviewing artifacts.**

## 1. Upgraded pip to 26.2.1 (runner image + Windows dev env)

- Reason: `pip lock` (generating a lockfile) has existed since pip **25.1**, but reading a lockfile while installing packages with command `pip install -r pylock.toml` — the actual piece C1c needs for "rebuild from existing lockfile" was only added in pip **26.1**, with further fixes in **26.2**. Checked against pip's own changelog.
- Decision: pin to **26.2.1** (latest stable), **in place** in the existing `thesis-runner:2.335.1` image: replacing 25.1.1 as the new pinned version going forward, not a parallel image.
- This directly contradicts my own 26.06 rule ("pip 25.1.1 must not change during experiment") — accepted knowingly, documented here as the reason the pin moved (methodology transparency), same as every other version decision in this log.
- Confirmed python compatible first: pip 26.2.1 requires Python ≥3.10, still supports 3.12 → no conflict with pinned CPython 3.12.4.
- Edited `infrastructure/runner/Dockerfile`: header comment + the `pip install "pip==25.1.1"` line → `"pip==26.2.1"`.
- Rebuilt image and recreated the runner container (same cycle as every prior Dockerfile change):
  ```powershell
  docker build -t thesis-runner:2.335.1 infrastructure/runner/
  docker rm -f thesis-runner
  docker run -d --name thesis-runner -e GH_REPO_URL=... -e GH_TOKEN=<fresh token> thesis-runner:2.335.1
  ```
- Verified: `docker exec thesis-runner pip --version` → `pip 26.2.1`; `python3.12 -m pip lock --help` shows the `lock` subcommand.
- Also upgraded pip on the Windows dev machine. Had to explicitly bypass my own user-level `pip.ini` (which points to Nexus) for this time:
  ```powershell
  python -m pip install --index-url https://pypi.org/simple pip==26.2.1
  ```

## 2. Fixed a runner bug: GitHub forced an auto-update and crashed the container

- the runner log showed GitHub silently force-updating the runner binary (2.335.1 → 2.336.0) mid-session:
  ```
  Runner update in progress, do not shutdown runner.
  Downloading 2.336.0 runner
  ...
  Restarting runner...
  /home/runner/run-helper.sh: line 36: /home/runner/bin/Runner.Listener: No such file or directory
  Exiting with unknown error code: 127
  ```
  → infinite crash loop (missing binary after the in-place swap) , the runner container can not be started anymore.
- **Root cause**: `infrastructure/runner/entrypoint.sh` registers via `config.sh` without the `--disableupdate` flag, so GitHub's backend is free to auto-update the runner whenever it considers it outdated. This directly contradicts the Dockerfile's own stated design (pinned, SHA-256-verified runner version, bumped deliberately via `RUNNER_VERSION`/`RUNNER_SHA256` ARGs).
- **Fix**: added `--disableupdate` to the `config.sh` call in `entrypoint.sh`, rebuilt the image, removed the broken container, and registered a fresh one with a new token.
- Verified: log now stays at `Listening for Jobs`, no more forced update messages.
- Clarified for myself: with `--disableupdate` set, tool versions inside the container never change automatically at runtime — the only thing that can still force action is GitHub's documented **30-day out-of-date cutoff**, visible as a warning directly on the runner's entry under Settings → Actions → Runners.
- if the runner version truly deprecated, then I manually edit the dockerfile and rebuild the image + recreate the container again

## 3. Implemented `pip lock` for Python service's C1c ("rebuild with existing lockfile")

- Context: C1c was `invalid_combination` for pip since 10.07 (no native lockfile). The 26.07 log reopened study using pip's experimental `pip lock` (PEP 751) — same idea as npm's `package-lock.json` and the `maven-lockfile` plugin planned for Java.
- Read pip's own CLI reference for `pip lock` (https://pip.pypa.io/en/stable/cli/pip_lock/): confirms it locks packages from PyPI/other indexes via requirement specifiers, VCS URLs, local project directories, or local/remote source archives — plus locking from requirements files.
- Read the pylock.toml spec for the exact file format: https://packaging.python.org/en/latest/specifications/pylock-toml/
- Read pip's repeatable-installs page for the broader hash/lock context: https://pip.pypa.io/en/stable/topics/repeatable-installs/
- Cross-checked a community write-up (pydevtools handbook) that independently confirmed the same filename rule I'd already hit empirically: https://pydevtools.com/handbook/how-to/how-to-install-from-a-pylock-toml-lockfile-with-pip/

### Pilot tests run locally (in `services/python/`), in order
1. **`pip lock -o test_pylock.toml .`** → succeeded. Confirmed it reads `pyproject.toml` (same mechanism as `pip install .`) and resolves through my configured index (local `pip.ini` → Nexus `pypi-group-public-first`). Also got: `WARNING: test_pylock.toml is not a valid lock file name.`
2. **Filename rule investigation** → PEP 751 requires the file be named exactly `pylock.toml` or match `^pylock\.([^.]+)\.toml$`. Confirmed this isn't just a cosmetic warning: reading a non-conforming name back with `-r` **hard-fails**: chokes on the first TOML line (`ERROR: Invalid requirement: 'lock-version = "1.0"'`).
3. **Hash conflict** → `pip install -r pylock.test.toml` (correctly renamed) still failed: `Can't verify hashes for these file:// requirements because they point to directories`. Cause: the lockfile always includes the service's own package as a `[packages.directory] path = "."` entry, which can't be hashed — and once any entry in the file has a hash, pip's hash-checking mode requires every entry to have one.
4. **Fix: `--only-deps`** → *"Take only the dependencies of the provided requirements into account, not the requirements themselves"* (official flag description). `pip lock --only-deps -o pylock.test3.toml .` drops the self-referencing directory entry entirely. Retested `pip install --dry-run --ignore-installed -r pylock.test3.toml --report test-install-report3.json` → installed cleanly, and the report has package name, version, resolved URL field, good for classifying result in central automated pipeline later.

### Final design decided for C1c (2 phases, similar to npm's C1c pattern)
- **Phase 1 (setup)**: `pip lock --only-deps --output "pylock.<cell_id>.toml" .` — generates the lockfile from the cell's actual `pyproject.toml` + `pip.conf`.
- **Edge case**: if phase 1 produces no lockfile (resolution error), log it and skip phase 2 — same rule as npm's C1c from 11.07.
- **Phase 2 (rebuild, observation)**: `pip install --dry-run --ignore-installed -r "pylock.<cell_id>.toml" --report "<cell_id>_install-report.json"` — dry-run only, no real download/install, so the classifier gets the same JSON shape as C1a/C1b and need less time per-cell.
- Filename convention confirmed: `pylock.<cell_id>.toml` (never `<cell_id>_pylock.toml`).
- Implemented into `service-ci-python.yml`, replacing the old "INVALID FOR PIP" block.

### Artifact list cleanup (python pipeline)
Went through the upload-artifact list against one principle: keep only what the classifier needs (Tier 1) plus what's needed to debug a failing cell (Tier 2), drop the rest.
- **Tier 1 (classification)**: `<cell_id>_install-report.json`, `<cell_id>_pip_log.txt` (fallback when resolution fails and no JSON report exists).
- **Tier 2 (evidence)**: `pip.conf`, `pyproject.toml`, new `pylock.<cell_id>.toml`, `<cell_id>_pip_setup_log.txt`.
- **Dropped as redundant/dead**: `<cell_id>_setup-install-report.json` (JSON of C1b's fixed, non-varying baseline install — `_pip_setup_log.txt` already covers debugging with no added value from a second JSON copy) and `<cell_id>_invalid.txt` (nremoved).

### Thesis-relevant finding
Hash-checking (`--require-hashes`, auto-triggered whenever any entry has a hash) defends against a source serving **different bytes under the same name+version after the lockfile was generated** , it does **not** defend against dependency confusion **at lock-generation time**. If a DCA-vulnerable A/B1 config resolves the attacker's package while running `pip lock`, the hash just pins and reinstalls that attacker package forever, no error. Worth framing explicitly in the C1c results section: locking only freezes whatever resolution outcome already happened, good or bad.

## 4. Node.js pipeline: two small consistency fixes found while reviewing artifacts

- **Added `--dry-run` to `npm ci` in C1c**: previously ran a real install. Confirmed safe — the classifier's evidence file (`package-lock.json`) is already fully written by phase 1 (`npm install --package-lock-only`) *before* `npm ci` runs; `npm ci` only verifies against the existing lock, it never rewrites it. So `--dry-run` skips real downloads/`node_modules` writes with zero loss of classifier data, and brings npm's C1c in line with pip's resolution-only design.
- **Found a gap in the npm upload-artifact list**: it was missing config evidence. Python's list explicitly keeps `pip.conf` + `pyproject.toml`, but npm's list had no equivalent for `.npmrc` (B1) or `package.json` (B2). Added both for consistency between the two pipelines.

## Reference links collected today
- `pip lock` CLI reference: https://pip.pypa.io/en/stable/cli/pip_lock/
- pylock.toml file format spec: https://packaging.python.org/en/latest/specifications/pylock-toml/
- PEP 751 (lock file standard, filename rule): https://peps.python.org/pep-0751/
- pip repeatable installs (hash-checking mode background): https://pip.pypa.io/en/stable/topics/repeatable-installs/
- Community write-up confirming the filename rule independently: https://pydevtools.com/handbook/how-to/how-to-install-from-a-pylock-toml-lockfile-with-pip/
- pip release history (25.1 lock introduction, 26.1/26.2 `-r pylock.toml` support): https://pip.pypa.io/en/stable/news/  
  - pip 26.1 explicit said added new feature: "Add experimental support to read requirements from standardized pylock.toml files" 

## Next steps
- Start integrating the `maven-lockfile` plugin for Java service's C1c (parallel supplementary study to pip's pylock work, same open question noted on 26.07).
- Run real pilot cells for testing across the A×B1×B2 matrix for Python's new C1c and java service CI pipeline.

# 08.08.2026 Integrate `maven-lockfile` plugin into Java service C1c ("rebuild with existing lockfile")

**Stand: Java service CI pipeline's C1c is no longer `invalid_combination`. It now uses the third-party `maven-lockfile` plugin (chains-project, subject of arXiv paper 2510.00730) to generate a lockfile and rebuild against it. Ran the very first real pilot cell of the whole Java pipeline (`Service CI - Java #1`) — found and partly fixed two pre-existing infrastructure bugs unrelated to maven-lockfile itself. One fix (settings.xml HTTP-blocker override) still open for tomorrow.**

## 1. What `maven-lockfile` is (researched today)

- Third-party Maven plugin from `chains-project`, subject of the paper "Maven-Lockfile: High Integrity Rebuild of Past Java Releases" (arXiv 2510.00730).
- Problem it solves: Maven doesn't pin *exactly which artifact bytes* a build resolved anywhere by default, only the version string in `pom.xml`. Two builds of the same `pom.xml` can silently resolve different artifacts later (metadata drift, or — relevant to this thesis — a dependency confusion attack serving a different artifact under the same coordinate).
- Records the fully resolved dependency tree + SHA-256 checksums into `lockfile.json`.
- This plugin has 3 goals, verified plugin facts directly against source code (`GenerateLockFileMojo.java`, `FreezeDependencyMojo.java`, `ValidateMojo.java` on GitHub), 
  - `generate`: normal resolve (via project's configured repositories) + writes `lockfile.json`.
  - `validate`: **does not resolve from the lockfile.** Re-runs normal resolution again and compare checksums (computed from local `~/.m2` cache) against the stored lockfile. It's a drift/integrity check, not a "rebuild".
  - `freeze`: the goal that actually *uses* the lockfile's content — pure in-memory transform (no network calls), reads `lockfile.json` + `pom.xml`, writes `pom.lockfile.xml` with every dependency version hard-pinned. Running a real resolution command against that frozen POM is the actual "rebuild from lockfile" step, the true analog of `npm ci` / `pip install -r pylock.toml`.
- Coordinates (groupID + artifactID): `io.github.chains-project:maven-lockfile`. Pinned to **5.17.3** (verified as the GitHub-marked "Latest Release" stable version via the [GitHub Releases page](https://github.com/chains-project/maven-lockfile) and [Maven Central page of the plugin ](https://central.sonatype.com/artifact/io.github.chains-project/maven-lockfile/versions)

## 2. Design decisions made today (C1c for Java)

- **2-part pattern (initial setup with cell's combination input + rebuild), no `validate` step, no cache purge in between.**
  - Setup (`generate`): resolves the cell's real `pom.xml` (A/B1/B2 config), writes `lockfile.json`.
  - Rebuild (`freeze` + `dependency:tree`): `freeze` pins every dependency to the lockfile's recorded version into `pom.lockfile.xml`; `dependency:tree` (same plugin/version as C1a) then resolves against that frozen POM. This is the primary classifier evidence for C1c, parallel to C1a's `dependency-tree.json`.
- **No cache purge between generate and rebuild**: Maven's `~/.m2` local repo *is* the resolved state (unlike npm's `node_modules`, there's no separate install target to reset). Purging it before rebuild would just turn "rebuild" back into a second "initial install". Matches how npm/pip's C1c also don't purge cache between their setup and rebuild phases.
- **`validate` intentionally left out for now** — documented as a known gap, not an oversight: `freeze`+`dependency:tree` only pins the *version number*, not the source/checksum. A same-version collision (out of scope) between the private and public repo at rebuild time (attacker republishes the exact pinned version) would slip through undetected by this design, since `validate` is the only checksum-aware goal in the plugin and it isn't wired in. Revisit later if this gap needs closing for the findings chapter.
- **Kept `${cell_id}_setup-dependency-tree.json` in C1b's artifact list** (reviewed whether to drop it, mirroring the pip cleanup from earlier today). Decided against dropping it: unlike pip's case (pure debug convenience, log already covers it), this JSON is the only structured, scriptable way to verify that C1b's baseline setup phase really resolved internal packages to a specific version like `1.0.0` before phase 2 runs — a hard experimental precondition for C1b's validity, not just debugging convenience.
- **`${cell_id}_pom.lockfile.xml` flagged as a Tier-2 (debug) artifact**, candidate to drop after pilot phase once `freeze`'s behavior is confirmed reliable — its content is already implied by `lockfile.json` + the effect is already visible in `rebuild-dependency-tree.json`.

## 3. Implemented in `service-ci-java.yml`

- Replaced the old `C1c) - INVALID FOR MAVEN` step with the real 2-phases flow above.
- Added new artifact files to the upload list: `${cell_id}_lockfile.json`, `${cell_id}_pom.lockfile.xml`, `${cell_id}_rebuild-dependency-tree.json`, `${cell_id}_mvn_lockfile_log.txt`.
- No change needed to `generate_pom_xml.py`/other generators. `C1` logic stays entirely in YAML (per the 11.07.2026 decision), and the plugin is invoked via fully-qualified goal (`mvn io.github.chains-project:maven-lockfile:5.17.3:generate`), same pattern as `maven-dependency-plugin` in C1a --> no extra plugin declaration needed in `pom.xml` at all.

## 4. Installed and configured GitHub CLI (`gh`)

- Wasn't installed on the Windows dev machine at all. Needed it to inspect GitHub Actions run logs/artifacts directly instead of relying on the VS Code GitHub Actions extension's UI (which lags behind actual run state / doesn't reliably auto-refresh).
- This is also required infrastructure for the central automated pipeline's design from 09.07.2026 (`gh workflow run`, `gh run watch`, `gh run download`), not just a one-off convenience.
- Installed via `winget install --id GitHub.cli`, authenticated via `gh auth login` (GitHub.com, HTTPS, browser login).

## 5. First real pilot test of the Java CI pipeline

- Triggered via the VS Code "GitHub Actions" extension: `Service CI - Java` workflow, `workflow_dispatch` inputs `cell_id=pilot_c1c_001, A=A1a, B1=B1a, B2=B2a, C1=C1c`.
- This was `Service CI - Java #1`
- **Result: `BUILD FAILURE`** at the `generate` step, before even reaching `freeze`/`dependency:tree`.

### Commands used to inspect it
```powershell
gh auth status
gh run list --workflow="service-ci-java.yml" --limit 5
gh run view <run-id>
gh run view <run-id> --job=<job-id> --log
```

### Root causes found (two, both pre-existing, unrelated to maven-lockfile itself)

1. **Fixed today** — updated the generator's groupId. **old groupId in `generate_pom_xml.py`.** The generated `pom.xml` still used `com.xueting.thesis` (the old groupId, before the 01–02.08.2026 migration to `io.github.shirley1997.thesis`). The old Nexus components were deleted during that migration, so `com.xueting.thesis:xueting-thesis-event-juhe:1.0.0` no longer exists anywhere. 
2. **Maven's built-in HTTP-blocker mirror.** Maven 3.8.1+ (runner is pinned to 3.9.16) refuses plain `http://` repositories by default via a built-in mirror (`maven-default-http-blocker`, redirects to a dummy `http://0.0.0.0/` sink) unless explicitly unblocked. Nexus is served over plain HTTP (`http://host.docker.internal:8081`), and no `settings.xml` exists anywhere in the runner image (confirmed: not referenced in `Dockerfile` or `entrypoint.sh` at all) — so nothing was overriding the block. This affects **all** C1 variants (C1a/C1b/C1c), not just C1c or maven-lockfile — it just happened to surface first here because this was the pipeline's first real run.

### Fix designed for tomorrow (not yet applied)
- Add `infrastructure/runner/settings.xml` with a mirror override that excludes the known Nexus repo IDs (`central`, `maven-group-public-first`, `maven-group-private-first`, `maven-internal-hosted`, `maven-public-proxy` — pulled directly from `generate_pom_xml.py`'s `A_TO_PRIVATE_REPO`/`MAVEN_PUBLIC_PROXY_REPO`) from the blanket HTTP block, using Maven's `!repoId` mirrorOf exclusion syntax, while keeping the block active for everything else.
- `COPY` it into the image at `/home/runner/.m2/settings.xml` in the `Dockerfile`, rebuild image, recreate container, re-run the pilot cell.
- No credentials needed in this file (Nexus anonymous read should cover GET requests) — safe to commit to git, unlike the Windows-side `settings.xml`.

## Next steps
- [ ] Apply the `settings.xml` mirror fix + `Dockerfile` `COPY` line.
- [ ] Rebuild runner image, recreate container.
- [ ] Re-run `pilot_c1c_001`-style cell, confirm `generate` succeeds, then `freeze` + `dependency:tree` against `pom.lockfile.xml`.
- [ ] Once green, run the rest of the pilot matrix from the plan's Verification section (vulnerable cell, resolution-error cell, invalid-combination regression check).
- [ ] Also verify anonymous read is actually enabled for Maven repos specifically on Nexus (only confirmed for npm on 10.07.2026) in case a new auth error appears after the HTTP-block fix.

# 09.08.2026 fix bug & pilot test of java pipeline
- Fixed remaining runner bugs, verified the id=central override in pom.xml empirically, redesigned C1c around lockfile.json, first real DCA success in the main matrix

- **Stand: Java C1c pipeline fully working end-to-end. Confirmed that the `id=central` override mechanism is correct, via source code + an official Maven doc + an empirical test. Made and implemented a final design decision on repository IDs for the main experiment matrix. Got a real, reproducible dependency-confusion success in the pilot data. Redesigned C1c's evidence file after discovering `dependency-tree.json` doesn't carry resolved URLs. Found and explained a cache-related pilot-testing confound (not a real experiment bug).**

## 1. Applied yesterday's settings.xml fix, found one more bug, got the first fully green C1c run

- Rebuilt the runner image with the `settings.xml` mirror override designed yesterday, recreated the container. (fix the maven built-in HTTP blocker mirror problem)
- Hit a **new** bug while re-testing: a C1c run took 6+ minutes and had to be cancelled. Root cause: `maven-lockfile:generate`'s `includeMavenPlugins` parameter defaults to `true`, so it was also resolving + checksumming the full transitive dependency tree of every Maven default lifecycle plugin (`maven-install-plugin`, `maven-core`, `plexus-*`, etc.) — out of scope of thie thesis
- Fixed with `-DincludeMavenPlugins=false` on the `generate` calls.
- Result: `pilot_c1c_003` (`A1a×B1a×B2a×C1c`) went fully green in 37s 

## 2. Verified the `id=central` override mechanism in pom.xml is actually correct 

- Ran `mvn help:effective-pom` locally (offline, no Docker needed) against generated `pom.xml` for all combination of A x B1. (see directory "effective-pom-check")
- Confirmed: `<repositories>` (controls dependency resolution) has exactly **one** `central` entry, pointing at the Nexus URL, successful override of superPOM.


## 3. Found the official Maven documentation for the id-merge mechanism

- It's not in a prose guide, but it **is** documented at the schema level: the Maven 4.0.0 POM XSD (`https://maven.apache.org/xsd/maven-4.0.0.xsd`), in the `<id>` field's description under `RepositoryBase`: *"the identifier is used during POM inheritance and profile injection to detect repositories that should be merged."*


## 4. Ran a deliberate ablation test: what if `id=central` is *not* used?

- Copied the real generator pom script to `check_ID_generate_pom_xml.py` (kept the real one untouched), changed it to use each repo's own name instead of `id=central` for the override slot.
- Ran the same effective-pom check loop against both versions, compared output.
- **Confirmed**: without `id=central`, Super POM's real Central leaks in as an *additional* repository every time — `A1a×B1a`/`A2×B1a`/`A3×B1a` all go from 1 repository to 2; `A2×B1c` from 2 to 3.
- This settles a question flagged back on 24.07.2026

## 5. Design decision: repository-ID strategy for the main experiment matrix

- Can't vary ID as its own matrix dimension (would explode the cell count, and npm/pip have no equivalent "ID variable" — would break cross-ecosystem comparability). One fixed choice has to go into the real generator.
- **Decision**: `id=central` override everywhere **except `A3×B1a`**, which now uses the repo's own ID (`maven-internal-hosted`) instead — meaning real Central leaks in *only* for that one cell.
- Reasoning: `id=central` isn't an arbitrary choice — it's literally what Sonatype's own Nexus+Maven integration guide recommends, so it's the realistic default. `A3` is uniquely defined as "no public path" (unlike `A2`, whose definition always implies a public path exists *somewhere* even if this specific pairing doesn't expose it). so `A3×B1a` using its own ID models a company that *believes* they're fully isolated but isn't, which is exactly the insecure-configuration condition for this thesis
- Implemented as a one-line conditional in `generate_pom_xml.py`'s `build_repositories_block()`, keyed on `a == "A3"`.
- Consequence: `A3×B1a` is no longer a guaranteed `resolution_error` cell (that was the old expectation, from 06.07.2026, when A2 and A3 behaved identically under B1a). `A2×B1a` produce resolution error; `A3×B1a` now depends on B2 and whatever's live on real Central.

## 6. Pilot cell run: real, reproducible dependency confusion success

- Ran `A3×B1a×B2b×C1c` — the interesting combination: B2b is a version *range*, and the attacker package (`1.0.3`) is published on real Maven Central, only reachable now because of the design decision above.
- **Result: both internal packages resolved to `1.0.3` from `https://repo.maven.apache.org/...`** — the attacker's package, not the real one from Nexus. A genuine DCA success, directly in the main matrix.
- Confirmed via the raw Maven log this isn't Nexus caching: Maven queries `maven-metadata.xml` from *both* configured repos, picks the highest version across the combined pool (`1.0.3`), tries fetching it from each repo in turn — the Nexus hosted repo 404s (never had `1.0.3`), real Central serves it.
- Ran `A3×B1a×B2a×C1c` (pinned version) as the paired negative control — resolved cleanly from Nexus, `1.0.0`, unaffected by the leak, since `1.0.0` was never published to real Central. Clean minimal pair for the findings chapter: same leaked config, safe under a pin, vulnerable under a range.

## 7. Redesigned C1c's rebuild evidence: dropped `dependency:tree`, use `lockfile.json` twice instead

- While reviewing the rebuild output, noticed `dependency-tree.json` (from `maven-dependency-plugin:tree`, same as C1a) only records name/version/scope — no resolved URL. Not useful enough for the classifier on its own.
- Checked `lockfile.json`'s actual schema (confirmed via a real generated file): it already has `resolved` (URL) and `repositoryId` per dependency, on top of version/checksum,  everything `dependency-tree.json` has, plus provenance.
- Considered keeping `dependency:tree` alongside a second lockfile capture, but realized both are **independent, full resolutions** against the same frozen POM (not "one resolution + a view of it") — running both is redundant work for no extra evidence.
- **Final design**: 3 `mvn` calls, no `dependency:tree`: `generate` (setup) → `freeze` → `generate` again against the frozen POM (`_rebuild-lockfile.json`). Classifier reads `_rebuild-lockfile.json` only: package name + version + resolved URL + checksum.

## 8. Found and explained a cache-only confound in `A2×B1a` pilot testing (not a real bug)

- `A2×B1a` pilot run showed `BUILD SUCCESS`, but in `_rebuild-lockfile.json`, public dependencies (`javalin`, `jackson-databind`, etc.) all have **empty** `resolved`/`repositoryId` fields, with matching `[WARNING] Artifact resolved url ... not found` lines in the log — while the two internal packages have fully populated fields.
- Explanation: `A2×B1a`'s repo list genuinely has no path to public packages, but Maven's core build phase silently reused a copy of `javalin` already sitting in the persistent dev container's local cache (left over from an earlier `A1a`/`A3` pilot cell) — so the overall build doesn't hard-fail. The `maven-lockfile` plugin's own remote-checksum verification is stricter and correctly flags these as unresolved from the *current* config.
- **Conclusion**: the classifier signal should be per-dependency `resolved`/`repositoryId` (empty = not genuinely resolvable from this cell's config), not overall build status.
- This cache-reuse issue is specific to pilot testing on the shared, persistent dev runner (only internal packages get purged between cells). The real experiment already avoids it — the existing design destroys the whole Docker container between cells, wiping `~/.m2` completely.

## Commands used today

```powershell
# Effective-POM check (single combo, offline)
python -c "import sys; sys.path.insert(0,'automation_process/config_generator'); from generate_pom_xml import generate_pom_xml; print(generate_pom_xml('A1a','B1a','B2a','http://host.docker.internal:8081'))" | Out-File -Encoding utf8 pom-test.xml
mvn help:effective-pom -f pom-test.xml "-Doutput=effective-pom.xml"
```
```powershell
# Full A x B1 effective-pom sweep (both the real generator and the ID-ablation copy)
# see dump_pom_checks.ps1 + pom_override_check.py / check_ID_generate_pom_xml.py
```

## Next steps

- [ ] Continue the pilot matrix: `A2×B1a` resolution-error regression (now understood correctly, see confound note above), invalid-combination checks (`A3×B1c`, any `B2c`).
- [ ] Add the per-dependency `resolved`/`repositoryId` classifier rule to the actual central automated pipeline's classifier script (not just documented in the plan).
- [ ] Consider whether the cache-confound insight is worth its own short note in the methodology chapter (pilot-testing artifact vs. real-experiment behavior).

# 13 & 14.08.2026 central automated pipeline: requirements, design, and Phase 1-5 implementation

- **Stand: Worked out the technical requirements and design for the central automated pipeline (the last unbuilt piece from the 30.06.2026 design), then implemented and pilot-tested Phase 1 through Phase 5 of it (matrix generation, checkpoint, result CSV, classification logic, Nexus cache invalidation). Found and fixed a real logic bug in `service-ci-java.yml`'s C1b step along the way.**

## 1. Determined the technical requirements for the central automated pipeline

- Went through my requirements: generate the full experiment matrix as CSV, mark invalid cells first and they don't go further steps, support running the whole matrix / one cell / a subset (needed later for sub-RQ2, to rerun only the vulnerable cells), a checkpoint file so an interrupted run can resume, centralized classification (not inside the service pipelines), and cache isolation between cells (Nexus cache invalidation + runner container destruction).
- Used section 5.3 (methodology) of the thesis (the original, implementation-light pipeline design) plus the 30.06.2026 dev-log design as the starting point, then refined it together based on my review.


## 2. Key design decisions made today

- **Checkpoint file**: `checkpoint.json`, a plain JSON array of finished `cell_id`s (no per-cell status). A cell counts as done just by being in the file, matches the fact that every cell only ever gets one attempt.
- **Single script file**:`automation_process/central_automated_pipeline/central_automated_pipeline.py`. All phases are functions in one file, so shared setup and variables (Nexus URL, repo owner/name, constants, file paths) only has to be written once.
- **`cell_id` format**: `{ecosystem_short}_{A}_{B1}_{B2}_{C1}`, e.g. `npm_A1a_B1a_B2a_C1a` — descriptive, stable across re-generating the matrix.
- **`results.csv` is the single source of truth** — every one of the 432 cells gets a row, valid or invalid, no cross-reference two files. Invalid cells' rows get appended once, AFTER the whole experiment finishes, from `experiment_matrix.csv`'s invalid rows.
- **Classification categories stay exactly `malicious_resolved` / `private_resolved` / `resolution_error` / `invalid_configuration`** — if even one of the two internal packages resolves to the attacker's version, that's already a successful attack on that cell, regardless of what the other package did , check that status with priority, before anything else.
- **Nexus cache invalidation**: the real Sonatype API uses **POST**, and I also need to invalidate the **group repo's own cache** (not just the proxy repo) for `A1a`/`A1b` cells, since group repos have their own metadata-merge cache layer on top of their members'.
- **Ephemeral runner (`--ephemeral`)** in entrypoint.sh
- **Classification never needs `repositoryId`** — only package name (artifact ID), resolved version, and resolved URL are recorded or used for classification. Confirmed via `maven_lockfile_example.json`: for my two internal packages, `repositoryId` came back as `"central"` (not `"maven-internal-hosted"`) — a side effect of the `id=central` override design in `generate_pom_xml.py` — proving the field isn't a reliable source indicator on its own.

## 3. Implemented Phase 1 - 5 of `central_automated_pipeline.py`

- **Phase 1 (matrix generation)**: `is_valid_combination()`, `generate_matrix()`, `write_matrix_csv()`. Verified: 432 rows total, 360 valid / 72 invalid, matches the hand-calculated expectation (`A3×B1c` = 27 rows, `java×B2c` = 48 rows, 3 rows counted in both).
- **Phase 2 (checkpoint)**: `load_finished_cells()`, `mark_cell_as_finish()`, `is_finished()`. Verified by marking two fake cell_ids finished and checking `is_finished()` returns `True`/`True`/`False` correctly.
- **Phase 3 (results.csv writer)**: `write_result_file()`, appends one row per cell using placeholder test data.
- **Phase 4 (classification)**: `read_npm_evidence()`, `read_pip_evidence()`, `read_java_evidence()`, `classify_logic()`. Verified against hand-built fake evidence lists (None / private / malicious / partial-count / unrecognized-version), and against two real sample files already in the repo (`services/python/test-install-report3.json`, `maven_lockfile_example.json`).
- **Phase 5 (Nexus cache invalidation)**: `invalidate_nexus_cache()`. Tested against the real local Nexus repositories.

## 4. Bugs found and fixed while implementing (implement and test one function/phase at a time)

- `=` vs `==` mixups (assignment vs comparison) in `is_valid_combination`.
- `&` vs `and` for combining conditions.
- `{}` creates an empty dict, not an empty set — needed `set()` for the checkpoint's in-memory representation.
- `.add()` (and other in-place methods like `.append()`) return `None`, not the updated object — a very easy trap.
- `json.loads()` (parses a string) vs `json.load()` (reads directly from a file object) mixed up in several places.
- A `path` function parameter that was defined but never actually used inside the function (fell back to a hardcoded/global path instead) — same file referenced three different ways in one function.
- `csv.DictWriter` needs append mode (`'a'`) to add rows without erasing the file; checking "does the file exist" has to happen *before* opening in append mode, since opening in append mode creates the file immediately.
- A classic operator-precedence bug: `if value == "C1a" or "C1b":` always evaluates true, regardless of `value`, because a non-empty string is always truthy on its own — needed `value == "C1a" or value == "C1b"`.
- Wrong field-name casing (`artifactID` vs the real `artifactId`) when reading the Maven lockfile JSON.
- A spelling typo (`classificaton_result` vs `classification_result`) silently created a second, unused variable — the function always returned an empty string regardless of the branches, since Python doesn't error on typo'd variable names, it just makes a new one.
- Classification logic first drafted as a per-package loop that overwrote its own result each iteration, silently losing a `malicious_resolved` verdict if the other package happened to be checked last. Fixed by checking malicious across *all* evidence first (with an early return), before deciding `private_resolved`.
- A Windows-specific `UnicodeDecodeError` (`'charmap' codec can't decode byte...`) from opening files without `encoding='utf-8'` — Windows' default codec can't read UTF-8 content (the JSON test fixture had emoji/special characters embedded in it). Fixed by adding `encoding='utf-8'` to every `open()` call.
- `invalidate_nexus_cache` bugs: used the global `A` list instead of the function's own `A` parameter (would have crashed trying to use a list as a dict key); computed the group-repo URL unconditionally instead of only for `A1a`/`A1b` (would have crashed with `KeyError` for `A2`/`A3` cells); called the proxy invalidation twice; had two `return` statements in a row, so the group-repo response was always silently discarded (the second `return` is unreachable dead code).

## 5. Bug found in `service-ci-java.yml`'s C1b step (not part of the central pipeline script, found while reviewing the workflow for Phase 4/8 groundwork)

- The comment right before Phase 2 says "Restore the cell's actual pom.xml for phase 2", but the actual restore command (`mv pom_cell.xml pom.xml`) was missing on the success path — only present in the earlier failure-path branch. So when setup succeeds, Phase 2 was silently resolving against the leftover *fixed/pinned setup* pom.xml instead of the cell's real A/B1/B2 configuration, for both the dependency-tree output and the `maven-lockfile:generate` call right after it.
- Fix identified: add `mv pom_cell.xml pom.xml` right before Phase 2 starts. Not yet applied to the workflow file.
- Decided the failure-path restore (before the early `exit 0`) isn't strictly necessary for correctness (Phase 2 never runs after that exit anyway) — it only affects whether the *uploaded artifact* for a failed cell shows the right pom.xml for manual debugging, not classification (the classifier never reads pom.xml).

## 6. Nexus authentication

- Assumed anonymous access might cover cache invalidation (per the 10.07.2026 finding that anonymous *read* was enabled) — turned out to be wrong. Got `403 Forbidden` on both the proxy and group repo invalidation calls.
- Added `python-dotenv`, created a gitignored `.env` file at the repo root with `NEXUS_ADMIN_USER`/`NEXUS_ADMIN_PASS`, loaded via `load_dotenv()`, and passed `auth=(user, pass)` into the `requests.post()` calls (POST request to nexus).

## Commands used today

```powershell
# test Nexus cache invalidation (see central_automated_pipeline.py phase 5: nexus invalidation)
request.post(api, auth=(username, password))

# command for obtain registration token for a new runner (needed for automated main experiment)
gh api --method POST -H "Accept: application/vnd.github+json" repos/shirley1997/MS_test_system/actions/runners/registration-token --jq .token

# install python-dotenv in order to read .env file (for nexus authentication, otherwise cache invalidation api returns code 403)
pip install python-dotenv
```

## Links & resources collected today

- [GitHub Docs — self-hosted runner software updates](https://docs.github.com/en/actions/reference/runners/self-hosted-runners#runner-software-updates-on-self-hosted-runners): explains the `--disableupdate` flag on `config.sh`, used to stop GitHub silently auto-updating the runner binary (already applied in `entrypoint.sh` on 08.08.2026, this is just the source doc for it).
- [Sonatype REST API reference](https://help.sonatype.com/en/api-reference.html): confirms the actual cache-invalidation endpoint is `POST /v1/repositories/{repositoryName}/invalidate-cache` servers: /service/rest
- [GitHub REST API — self-hosted runners](https://docs.github.com/en/rest/actions/self-hosted-runners?apiVersion=2026-03-10): how to automatically obtain a runner registration token for a repository via the github API. needed so the central pipeline can register a fresh ephemeral runner per cell without manual steps.
  - gh api \
  --method POST \
  -H "Accept: application/vnd.github+json" \
  -H "X-GitHub-Api-Version: 2026-03-10" \
  /repos/OWNER/REPO/actions/runners/registration-token
- [`gh workflow run` manual](https://cli.github.com/manual/gh_workflow_run):  run a workflow file using github CLI. how to trigger a `workflow_dispatch` workflow with inputs from the command line. Inputs can be given interactively, via `-f`/`-F` (raw-field/field flags — this is what the pipeline uses), or as JSON via stdin.
- [`gh run list` manual](https://cli.github.com/manual/gh_run_list): list recent workflow runs. `--limit <int>` (default 20) caps how many are fetched — used right after dispatching a cell to find that workflow's run ID of the corresponding cell.
- [`gh run watch` manual](https://cli.github.com/manual/gh_run_watch): watches a workflow log run until it finishes, showing progress. used to block the central pipeline until a cell's CI run completes before downloading its artifact.
- [`argparse` examples](https://stackoverflow.com/questions/7427101/simple-argparse-example-wanted-1-argument-3-results) and [official Python `argparse` HOWTO](https://docs.python.org/3/howto/argparse.html): for building the pipeline's command-line interface (run the whole matrix / one cell / a subset of cells). the subset option is specifically needed for sub-RQ2, to rerun only the cells that came out `malicious_resolved`.
- [Git Tower — `git rev-parse` FAQ](https://www.git-tower.com/learn/git/faq/git-rev-parse): Git Rev-Parse: `git rev-parse` is a command that takes a Git reference (like a branch name, tag, or commit hash) as input and outputs the corresponding object ID. In simpler terms, it translates human-readable Git references into their internal object representations. this command is used to record which exact commit produced each row in `results.csv`. (a unique reference)

## Next steps

- [ ] Continue manual pilot dispatches against the service pipelines to catch remaining logic errors before adding `--ephemeral`.
- [ ] Phase 6: add `--ephemeral` to `entrypoint.sh`, rebuild the runner image, once pilot testing is done.
- [ ] Phase 7: runner lifecycle functions (obtain registration token, start container, wait for online).
- [ ] Phase 8: workflow dispatch + artifact download functions.
- [ ] Phase 9: full orchestration loop + CLI (`--matrix` / `--run-all` / `--cell` / `--cells`).
- [ ] build central automated pipeline, run pilot test

# 14.08.2026: Pilot-tested and fixed bugs in all three service CI pipelines

**Stand: Did the "continue manual pilot dispatches" step from the list above. Went through Node.js, Python, and Java pipelines one by one, found and fixed several real bugs (some pre-existing, one introduced by my own first-pass fix), and pilot-tested two things that turned out fine (didn't need a code change). Every fix below was confirmed by actually running a cell and checking the result, not just by reading the code. this is what caught most of the follow-up bugs.**

## Java pipeline (`service-ci-java.yml`)

### Bug 1: wrong Maven flag, lockfile.json never actually created
- C1a and C1b called the `maven-lockfile:generate` plugin with `-DoutputFile=...` to name the output file. Checked the plugin's real source code on GitHub — the actual parameter is `-DlockfileName=...`. `-DoutputFile` isn't a real option, so Maven quietly ignored it and wrote to the default `lockfile.json` instead of `<cell_id>_lockfile.json` — meaning the artifact upload could never find it, and this file has the resolved-URL info the classifier actually needs (more useful than `dependency-tree.json`, which has no URL).
- Fix: changed both calls to `-DlockfileName="${{ inputs.cell_id }}_lockfile.json"`.
- My own first fix introduced a new bug: forgot the closing quote, so the line read `-DlockfileName="${{ inputs.cell_id }}_lockfile.json -DincludeMavenPlugins=false` (no `"` before the next flag). This is a bash syntax error ("unexpected EOF") — the command silently never ran at all (hidden by `continue-on-error: true`).
- Fixed: added the missing `"`.
- Pilot test: `A1a × B1a × B2a × C1a` → **Result: `<cell_id>_lockfile.json` generated correctly, with `resolved` and `repositoryId` filled in (`repositoryId: "central"`), confirming the `id=central` override approach still works with the lockfile plugin in the mix.**

### Bug 2: `fixed_pom.xml` didn't work inside the runner container (2 separate problems)
- `fixed_setup_file/fixed_pom.xml` (only used by C1b's setup phase) had `http://localhost:8081/...` hardcoded. Inside a Docker container, "localhost" means the container itself, not my Windows machine running Nexus. → `Connection refused`.
- Fix: changed to `http://host.docker.internal:8081/...`.
- Second problem, found right after fixing the first: the repository `<id>` in that same file was `nexus-group-public-first` — a name I made up that doesn't match anything in the runner's `settings.xml` HTTP-blocker exclusion list (`!central, !maven-group-public-first, ...`). So Maven's built-in "block all plain HTTP repos" rule still caught it → `Blocked mirror for repositories: [nexus-group-public-first ...]`.
- Diagnosed using `mvn help:effective-settings` on my dev machine — turns out the same blocker mirror is present there too (nothing special is overriding it), but it never fires locally because my `.m2` cache already has everything cached from months of manual builds, so Maven never needs to actually reach out over the network. This is exactly why the bug only ever showed up on the runner (which purges its cache every cell) and never on my own machine.
- Fix: changed `<id>` from `nexus-group-public-first` to `central` — matches what `generate_pom_xml.py` actually uses for A1a×B1a.
- Pilot test: `A1a × B1a × B2b × C1b` → **Result: full 2-phase run succeeded, internal packages resolved to `1.0.3` (the public/attacker version) in phase 2 — expected, because `maven-group-public-first` merges versions from all its members, and the B2b range picks the highest one available.**

### Design change (not a bug): purge the whole `/.m2` cache between cells
- Changed the cleanup step from only deleting the internal packages' cache folder to deleting the entire `~/.m2/repository`. This makes pilot runs behave like the real experiment (fresh container per cell) and stops old cached artifacts from silently hiding real problems — this is actually *why* both bugs above only became visible now.
- Trade-off: slower pilot runs, since Maven plugins and public dependencies re-download every single cell.

### Small fix: no log for `lockfile:generate` failures, then reverted on purpose
- The `lockfile:generate` calls in C1a/C1b had no `tee`/`|| true`, so a failure left zero trace in any uploaded file.
- Fix: added `2>&1 | tee "${{ inputs.cell_id }}_mvn_lockfile_log.txt" || true` to both. Reused a filename that was already in the upload list (previously only ever produced by C1c) — no other changes needed.
- Pilot test: reran an already-tested cell → **Result: `<cell_id>_mvn_lockfile_log.txt` showed up with real content.**
- Later decided the log was too noisy to be useful for a quick manual check, so removed the `tee` again — **kept `|| true`** so a failure still can't break the step, just accepted that C1a/C1b won't have a diagnostic log if `lockfile:generate` fails.

### Small fix: adjust outdated comment
- Rewrote the C1a step's header comment, which only mentioned `dependency-tree.json`/`mvn_log.txt`, to also mention the `lockfile.json` output.

## Node.js pipeline (`service-ci-nodejs.yml`)

### Bug: crashes the whole job on the invalid A3×B1c combination
- `generate_npmrc()` raises an error for A3×B1c (physically impossible: A3 has no proxy repo), but the workflow called it with no error handling → the whole step crashes → **no artifact gets uploaded at all** for that cell. Java already handled this properly (writes an `_invalid.txt` marker and continues); Node.js and Python didn't.
- Fix: wrapped the call in `try/except`, writing an `_invalid.txt` marker file on error; added a skip-check at the top of C1a/C1b/C1c (`if [ -f "..._invalid.txt" ]; then exit 0; fi`); added the marker to the upload list.
- First attempt had 3 bugs, all caught during review before testing:
  1. A Python syntax error (`""services/nodejs/...` — a stray empty string glued onto unquoted text) that would have broken **every single cell**, not just the invalid one.
  2. Used the wrong variable for the filename (`${{ inputs.C1 }}` instead of `${{ inputs.cell_id }}`).
  3. In the error-handling block: opened the file `as file` but then called `f.write(...)` — `f` didn't exist (`NameError`); and the last `print(...)` was missing its closing quote (another syntax error).
- Fixed all three.
- Pilot test: `A1a×B1a×B2a×C1a` (checks normal cells still work) + `A3×B1c×B2c×C1a` (checks the invalid case) → **Result: both worked. Normal cells unaffected; invalid cell now writes `_invalid.txt`, gets skipped cleanly, no crash.**

## Python pipeline (`service-ci-python.yml`)

### Bug 1: same invalid-combination crash as Node.js, plus a copy-paste mistake
- Applied the same fix pattern as Node.js (try/except, `_invalid.txt` marker, skip-checks, upload list entry).
- Bug found: the marker was being written to `services/nodejs/${{ inputs.cell_id }}_invalid.txt` — wrong service folder, a leftover from using the npm fix as my reference while writing this one. The write itself didn't fail (that folder exists too), so nothing errored — the file was just landing in the wrong place, which looked exactly like "it's not being generated" from where I was checking.
- Fix: corrected the path to `services/python/...`.
- Pilot test: `A3×B1c×B2a×C1a` → **Result: marker now appears in the right place, gate catches it, run finishes cleanly.**

### Checked, but decided NOT to change: `PIP_CONFIG_FILE` set to an empty string for B1d
- Worry: B1d means "no config file at all," and the workflow expresses that as `PIP_CONFIG_FILE: ''`. pip's own docs say the *documented* way to disable config loading is `os.devnull`, not an empty string — so I wasn't sure if `''` actually behaves the same.
- Instead of guessing, pilot-tested it directly:
  - `A1a×B1d×B2a×C1a` (pinned to `1.0.0`, which only exists on my private Nexus, never published publicly) → **Result: correctly FAILED — pip said the only version it could see was `1.0.3` (the public one). Proves it never saw Nexus at all.**
  - `A1a×B1d×B2b×C1a` (a version range) → **Result: correctly resolved to the public `1.0.3` from `files.pythonhosted.org`, with zero Nexus URLs anywhere in the output.**
- Conclusion: pip treats an empty `PIP_CONFIG_FILE` the same as "no config" in real life, even though it's not the officially documented value. **No code change needed.**

### Checked, but decided NOT to change: missing `PYTHONPATH` in C1b's "package update" phase
- My design notes from 15.07.2026 said C1b's phase 2 (the "upgrade" step) needs `PYTHONPATH=./py_dependency` so pip can see the package version installed in phase 1 — this was never actually implemented or tested.
- Pilot-tested instead of guessing:
  - `A1a×B1a×B2b×C1a` (plain, single-phase resolve) → **Result: resolved to `1.0.3`.**
  - `A1a×B1a×B2b×C1b` (2-phase: install `1.0.0` baseline, then "upgrade") → **Result: also resolved to `1.0.3` — identical.**
- Conclusion: `PYTHONPATH` doesn't change the actual result here, because `--upgrade` combined with the project's own version-range requirement already pushes pip toward "highest version in range" regardless of what's already installed. **No code change needed.** Side note for later: this means C1b's Python "update" phase might not really be testing a different scenario than a plain resolve — worth a sentence in the methodology chapter someday, not urgent.
- While testing this, also noticed phase 1's setup log (`_pip_setup_log.txt`) was coming back completely empty — turned out the `pip install` command there uses `--quiet`, which suppresses all the normal progress text. Removed `--quiet` so the log actually shows what got installed.

## Other things fixed along the way (not pipeline bugs)
- Hit a workflow stuck in "Queued" for several minutes — turned out the runner container had reconnected to GitHub right when the job was dispatched, so the job never got delivered to the runner's new session. Not a pipeline bug — just cancelled the stuck run and re-dispatched once the runner showed idle again (checked with `docker ps` + `gh run list`).
- Found where the repo actually lives inside the runner container, for browsing files directly in Docker Desktop: `/home/runner/_work/MS_test_system/MS_test_system/` (found with `docker exec ... find ... -iname "_work"`).

## Commands used today

```bash

# Compare dev-machine Maven settings against the runner's (HTTP-blocker investigation)
mvn help:effective-settings

```

## Next steps
- [ ] All bugs found during this pilot-testing pass are fixed and re-verified. Ready to continue the "continue manual pilot dispatches" step with any remaining untested cells, then move on to Phase 6 (`--ephemeral`) from the earlier next-steps list.
- [ ] Optional: re-run one Java C1c cell to double check the earlier 09.08.2026-verified behavior still holds after today's `fixed_pom.xml` fixes and the full `/.m2` purge change (shouldn't be affected, but cheap to confirm).
- [ ] The central automated pipeline (`central_automated_pipeline.py`) and the config generator scripts haven't had this same close, pilot-tested review yet — only the three service CI YAMLs were covered today.


# 18.08.2026 maven central (for foundation chapter)
- important link to read: relationship between namespace and groupId: https://central.sonatype.org/faq/namespaces-vs-groupids/#groupid
	- "Namespaces are prefixes of `groupId`s. If you are authorized to publish on the `com.example` namespace, you may publish a `groupId` of `com.example`, `com.example.child`, `com.example.child.subproject`"

# 21 & 22.08.2026 central automated pipeline: Phase 6-9 implementation, pilot testing, fix bugs

**Stand: Implemented and pilot-tested Phase 6 through 9 of `central_automated_pipeline.py`: ephemeral runner infrastructure, runner lifecycle functions, workflow dispatch/artifact download, and the full per-cell orchestration + main loop. Ran 3 real npm cells end-to-end (results show private_resolved). Adjusted the classification logic to also check the resolved URL, not just version, which is described in my methodology chapter. Found one real infrastructure finding (Nexus metadata caching) and one real correctness gap (Ctrl+C doesn't safely stop the pipeline), the second one is still open, planned for next session.**

## 1. Phase 6 — ephemeral runner

- One-line edit to `infrastructure/runner/entrypoint.sh`: added `--ephemeral` to the `config.sh` call.
- **Bug**: forgot to add `\`  after `--disableupdate`, so `--ephemeral` landed on its own line and got interpreted as its own (nonexistent) shell command: `entrypoint.sh: line 76: --ephemeral: command not found`. Fixed by adding the missing `\`.
- Rebuilt the image (`docker build -t thesis-runner:2.335.1 infrastructure/runner/`), manually verified: container registers, picks up a dispatched workflow, then **both** the GitHub-side registration and the container disappear on their own afterward.
- Confirmed (by testing `docker start` on a stopped ephemeral container): `--ephemeral` also deletes the local `.credentials`/`.runner` files as part of its self-cleanup — so restarting a stopped ephemeral container isn't a real workflow, only fresh `docker run --rm` + a fresh token is. Matches the pipeline's actual design (always fresh containers), so not a problem, just noted for my own understanding.
- Cleaned up 6 old "offline" runner registrations left over from earlier persistent-mode testing, via https://docs.github.com/en/rest/actions/self-hosted-runners?apiVersion=2026-03-10#delete-a-self-hosted-runner-from-an-organization:
  ```powershell
  gh api --method DELETE -H "Accept: application/vnd.github+json" -H "X-GitHub-Api-Version: 2026-03-10" repos/shirley1997/MS_test_system/actions/runners/RUNNER_ID
  ```

## 2. Phase 7 — runner lifecycle functions (`get_registration_token`, `start_runner_container`, `wait_for_runner_online`)


- **Bug in both `get_registration_token` and `start_runner_container`**: returned the raw `CompletedProcess` object instead of `.stdout.strip()` — despite the `-> str` type hint, neither function actually returned a string.
- **Design correction to `wait_for_runner_online`**: Redesigned to match by a unique **runner name** instead: added `-e RUNNER_NAME=thesis-runner-{cell_id}` to `start_runner_container`, and `wait_for_runner_online` now takes an `expected_runner_name` parameter and checks `runner["name"] == expected_runner_name`.
- **Bug during that fix**: first attempt wrote `"-e", f"thesis-runner-{cell_id}"` — missing the `RUNNER_NAME=` prefix, so it wasn't a valid env-var assignment at all. `RUNNER_NAME` stayed unset, the runner registered under a random container-ID name instead, and `wait_for_runner_online` correctly returned `False` (looked like a timing bug, wasn't). Fixed to `"-e", f"RUNNER_NAME=thesis-runner-{cell_id}"`.
- **Verified end-to-end** via test script `test_phase7.py`: obtained token → started container → `wait_for_runner_online` returned `True`, correctly matching by runner name → manually dispatched `hello-world`workflow → confirmed both the container and the GitHub runner registration disappeared.

## 3. Phase 8 — dispatch & artifact download (`dispatch_cell`, `find_run_id`, `wait_for_run_complete`, `download_artifact`)

- **f-string syntax error** `f"cell_id={cell}["cell_id"]"`Fixed by doing the dict lookup *inside* the braces with the opposite quote style: `f"cell_id={cell['cell_id']}"`.
- **Bug in `find_run_id`**: `gh run list --json ...` returns a JSON **array**, but the code indexed it like a dict (`workflow_data["databaseId"]`), fixed to `workflow_data[0]["databaseId"]` (most recent run, since `gh run list` returns newest-first).
- **Three bugs in `download_artifact`**: `str(run_id)` was mistakenly written into the function's own *parameter list* (not valid — parameters must be plain names, not function calls); `return dest_dir` was indented to the same level as `try:` itself instead of inside it, breaking the `try`/`except` pairing; and a missing `str(run_id)` conversion at the actual call site (same reasoning as `find_run_id`'s int-vs-str return type — `databaseId` is a JSON number, not a string, despite the `-> str` hint).
- **Design change to `wait_for_run_complete`**: removed `capture_output=True` so its `--compact` progress actually streams to the terminal live instead of being silently captured and thrown away, and added explicit `print()`s after so there's always a clear "finished waiting" marker.
- **Verified end-to-end** via `test_phase7_8.py`, chaining Phase 7 straight into Phase 8 for a real `npm_A1a_B1a_B2a_C1a` cell, artifact downloaded successfully.
- **Important empirical correction**: originally assumed a downloaded artifact preserves the `services/{ecosystem}/` folder prefix from the workflow's `upload-artifact` step. Wrong — `actions/upload-artifact` strips the common leading directory shared by every listed path, so since every workflow's upload list lives entirely under `services/{ecosystem}/...`, that whole prefix gets flattened away. Downloaded files sit directly at the top level (e.g. `{cell_id}_lockfile.json`, `package-lock.json`), confirmed by inspecting a real downloaded Java cell's folder. Corrected all Phase 9 evidence-file paths accordingly.

## 4. Phase 9 — full orchestration (`run_one_cell`, `build_result_row`, `copy_invalid_rows`, `experiment_loop`)

- **`classification` never actually captured**: `classify_logic(...)`'s return value was discarded at the call site; and inside `build_result_row`, the dict literal called `classify_logic()` a *second* time with **zero** arguments instead of using the `classification` parameter the function already receives. Fixed both.

- **`build_result_row` ignored its own `git_commit` parameter** — the dict literal called `get_git_commit()` fresh internally instead of using the value the caller already computed and passed in. Wasteful (ran `git rev-parse HEAD` twice) and made the parameter dead. Fixed to use the parameter.
- **`read_java_evidence` needed a `base_dir` parameter added** : it previously opened a bare filename assuming the script's own working directory, which doesn't work once the file actually lives inside a downloaded artifact folder.

- **Design decision — new classification category `runner_offline_error`**: added as a 5th category (distinct from `resolution_error`) specifically for cells where `wait_for_runner_online` times out — deliberately kept separate to distinguish "infrastructure failed before the experiment could even run" from "the experiment ran and produced an ambiguous/failed resolution." Considered folding it into `resolution_error` for simplicity, decided against it for clearer results reporting.

## 5. Classification logic adjustment — added URL as real evidence, not just recorded data

- My methodology says classification should be based on package name, version, **and** URL together (that's the whole reason I use the lockfile as evidence in the first place — otherwise the resolved URL is invisible). The original `classify_logic` only ever checked `version`.
- Added `is_from_nexus(url)`: checks whether `"8081"` (Nexus's fixed port) appears in the URL — deliberately hostname-agnostic (works for both `localhost:8081` and `host.docker.internal:8081`).
- **`private_resolved` now requires both** `version in internal_version` **and** `is_from_nexus(url)`.
- **`malicious_resolved` deliberately stays version-only, on purpose** — requiring `is_from_nexus` there would be wrong: a malicious package can arrive either via Nexus's proxy (still shows `8081`) *or* by leaking straight from the real public registry, completely bypassing Nexus (no `8081` at all) — I already have a real, confirmed example of the second case, the `A3×B1a×B2b×C1c` pilot cell from 09.08.2026 that resolved `1.0.3` directly from `repo.maven.apache.org`. Requiring Nexus-origin for `malicious_resolved` would have wrongly excluded that already-confirmed attack success.
- Considered (and explicitly dropped) a same-version experiment idea (internal package and malicious package both published as e.g. `1.0.2`) — decided against it, since it doesn't match the canonical dependency-confusion definition (Birsan 2021: attacker wins via a *higher* version number under default resolution, not a same-version race).

## 6. Real infrastructure quirk found: Nexus caches computed npm metadata, not just files

- Noticed one internal package's resolved URL showed `localhost:8081` while everything else showed `host.docker.internal:8081`, despite all cells using the same `.npmrc`/`NEXUS_URL` config generated the same way.
- Likely explanation: npm registry metadata (including the `dist.tarball` URL) is normally computed dynamically per-request based on the request's `Host` header — if Nexus caches that *computed* response rather than recomputing it every time, whichever host first triggered that specific package@version's metadata (e.g. my own manual `localhost:8081` testing back in June/July, before the Docker runner pipeline existed) stays baked into the cached response indefinitely. `npm-internal-hosted` is deliberately excluded from my Phase 5 cache-invalidation calls (it's permanent storage, not a proxy cache), so this particular cache was never touched.
- Not a real problem: `classify_logic` never used `url` at all before this session, and the new `is_from_nexus` check only looks for the port number `"8081"`, which both hostnames satisfy — so this quirk can't cause a misclassification. Recorded here for methodology transparency, not something I fixed.

## 7. Pilot tests run for real (first live cells through the whole pipeline)

- Ran 3 real npm cells, same `A1a×B1a×B2a`, varying only `C1` (`C1a`/`C1b`/`C1c`) — all three completed successfully and classified `private_resolved`.
- Example real output from one run:
  ```
  cache of npm-public-proxy discarded
  cache of npm-public-proxy and npm-group-public-first discarded
  registration token obtained: AEG5DSRJIRYKDGUAIVDNTM3KRHJRO
  runner container just created: 36fddaad208f8e9747b4c117756bcb7106e0fd88a71ff8b531de17a78721555c
  is the new created runner online now?: True
  dispatching cell: npm_A1a_B1a_B2a_C1a
  run_id of the workflow: 32582870556
  ✓ Run Service CI - Node.js (32582870556) completed with 'success'
  pipeline run 32582870556 finished
  download artifact produced by service pipeline: automation_process/central_automated_pipeline/artifact_download/npm_A1a_B1a_B2a_C1a
  ```
- Confirmed `checkpoint.json` and `results.csv` both filled in correctly after each cell, and the runner container + GitHub registration cleaned themselves up automatically each time.

## 8. Found (not yet fixed): Ctrl+C doesn't safely stop the pipeline

- Tested crash-recovery by pressing Ctrl+C mid-run, during the "observing workflow" step (`wait_for_run_complete`). Expected the in-progress cell to be absent from `checkpoint.json` afterward — it wasn't; the cell was still marked done.
- **Root cause**: on Windows, Ctrl+C is delivered to the whole console process group, including the `gh` subprocess `wait_for_run_complete` is blocking on. `gh run watch` exits/aborts quickly on the signal, and since that call uses `check=False`, `subprocess.run()` just returns normally — no exception raised. The Python script then keeps running (download → classify → write → mark done) and races to completion within a second or two, which looks like "I pressed Ctrl+C and it stopped" but actually means the interrupt only killed the `gh` subprocess, not the pipeline itself.
- **Fix designed, not yet applied**: register a custom `SIGINT` handler that sets a `stop_requested` flag immediately, then explicitly check that flag right after the two genuinely long-running waits (`wait_for_runner_online`, `wait_for_run_complete`) inside `run_one_cell`, bailing out *before* `mark_cell_as_finish` if it's set; also check it at the top of each `experiment_loop` iteration so no *new* cell starts after a stop is requested.
- Known limitation even with the fix: the runner container for a mid-way-interrupted cell may be left orphaned (Ctrl+C stops the next Python steps, not an already-started `docker run -d`) — matches my own original Phase 6 decision not to build automatic container teardown; `docker ps -a` + manual `docker rm` covers it.

## Next steps

- [ ] Implement the Ctrl+C / graceful-stop fix designed above (signal handler + `stop_requested` checks).
- [ ] Run the still-missing pilot coverage: one Python cell and one Java cell through the real pipeline (never tested for real yet, only via hand-fed fixtures), a cell expected to produce `malicious_resolved`, the flagged untested `A2×B1a×C1c` Maven edge case from Phase 4, one invalid cell + confirm `copy_invalid_rows` writes its row correctly, and a real crash-recovery test using the fixed Ctrl+C handling.
- [ ] Only after all of the above passes: a small (~dozen-cell) pilot subset spanning all three ecosystems, then the full 432-cell official run.
- [ ] CLI (`--matrix` / `--run-all` / `--cell` / `--cells`) still not built — deliberately deferred this session to focus on getting `run_one_cell`/`experiment_loop` correct first.

# 23 - 25.08.2026, 28.08.2026 central automated pipeline: Ctrl+C fix applied, full 432-cell run completed

**Stand: Applied the Ctrl+C/script interruption fix designed on 21-22.08, found and fixed one more bug while wiring it in. Learned several real-world lessons about self-hosted-runner infrastructure while stress-testing interrupts. Survived two uninteractive-run incidents (a GitHub API rate-limit incident, a WiFi outage) using the checkpoint/results.csv design. Committed and pushed the pipeline, then ran the full 432-cell experiment successfully. `results.csv` is complete (with 432 lines now).**

## 1. Applied the Ctrl+C fix, found one more bug while doing it

- Added `import signal`, a module-level `stop_requested` flag, and a `handle_stop_signal(signum, frame)` handler registered via `signal.signal(signal.SIGINT, handle_stop_signal)`.
- Added `stop_requested` checks in `run_one_cell` (after the two genuinely slow waits) and in `experiment_loop`'s main `for` loop.
- **Bug found while wiring this in**: first version combined the check into the existing `if runner_online == False:` branch as `if runner_online == False or stop_requested:`. Problem: if Ctrl+C happened to land right as the runner *did* come online successfully, this branch is still true — writing a false `runner_offline_error` row into `results.csv` and permanently marking the cell done, even though nothing actually failed. Fixed by splitting into two independent checks: a plain `if stop_requested: return` (no row written, not marked done) placed *before* the separate, untouched `if runner_online == False:` branch.
- **Verified for real**: interrupted a cell during `wait_for_runner_online`'s `time.sleep()` — got a clean `KeyboardInterrupt` traceback, and `checkpoint.json` correctly did **not** contain that cell afterward. Confirmed this is a different situation from the earlier-diagnosed case (Ctrl+C landing inside a `gh` subprocess call and getting silently absorbed). a plain Python `sleep()` is reliably interruptible on its own, no custom handler needed for that specific case; the handler is what's needed for the subprocess-absorption case.

## 2. Learned: `--rm` alone doesn't stop anything, it only cleans up after a stop

- Found via Docker Desktop: after Ctrl+C interrupted a cell, its runner container was still "Running", idle, "Listening for Jobs" — `--rm` only deletes a container *after* its process exits; Ctrl+C on the Python script has zero effect on an already-launched Docker container, since they're independent processes.
- Decided **not** to add automatic container teardown to `run_one_cell` for this — deliberately kept the pipeline's scope focused on the actual research logic rather than infra robustness features, consistent with the original Phase 6 decision. Manual `docker stop`/`docker rm -f` when needed is enough.
- Learned a cleaner manual cleanup: `docker stop thesis-runner-{cell_id}` alone (no `-f`/`rm` needed) — since the container was started with `--rm`, a graceful stop signal makes the runner process exit, which then triggers `--rm`'s automatic removal on its own.

## 3. Repeated manual interrupt/kill testing caused a real GitHub-side runner conflict mess

- Rapidly interrupting and force-killing runner containers during testing (without letting GitHub's backend release the old session first) caused new registrations under the same `cell_id`-based name to get stuck: runner logs showed `"A session for this runner already exists... Conflict. Retrying until reconnected."` — the runner never reached "Listening for Jobs," so dispatched workflow runs just piled up stuck in **Queued**.
- **Full cleanup procedure used** to recover:
  ```powershell
  # cancel stuck workflow runs directly through GitHub UI, without using command

  # remove all leftover thesis-runner container. when the container is stopped, it will automatically disappear. (stop through docker desktop, no commnd used)

  # delete old runner registration on GitHub's side using GitHub API
  # first check which old runner is still there, manully observe the id
  gh api repos/shirley1997/MS_test_system/actions/runners 
  #then delete the runner with corresponding runner ID
  gh api --method DELETE repos/shirley1997/MS_test_system/actions/runners/{id}
  ```
- Also learned: request of cancel a workflow doesn't work immediately on a job whose runner was already force-killed mid-execution — there's no runner left to acknowledge the cancel request, so the job just sits "in progress" until GitHub's own dead-runner timeout eventually catches it (can take a while). Not a pipeline bug, a known self-hosted-runner characteristic.
- Considered removing the checkpoint logic entirely out of frustration with this mess — but decide to keep the checkpoint logic: the mechanism itself was already proven correct, and the actual pain was from deliberately stress-testing mid-job container kills (a testing artifact), not something the real unattended run would trigger the same way, since `--ephemeral` only ever kills a runner after normal job completion in real use.

## 4. Re-verified the checkpoint + classification logic with a clean, uninterrupted pilot rerun (24.08)

- Reran the same 5 target cells from before, uninterrupted this time. 4 of 5 were already done and correctly skipped; only `mvn_A3_B1a_B2b_C1c` (never completed before) actually ran.
- **Result: `mvn_A3_B1a_B2b_C1c` → `malicious_resolved`**, both packages at `1.0.3`, resolved from `https://repo.maven.apache.org/...` , matches the 09.08 manual pilot finding exactly, now reproduced through the real automated pipeline with the `is_from_nexus` classification fix in place. Also nicely confirms the classification design: this URL has no Nexus port in it at all, but still correctly classified `malicious_resolved`, exactly as intended.
- `npm_A3_B1c_B2a_C1a`'s `invalid_configuration` row also appeared correctly via `copy_invalid_rows` this time, since the run wasn't interrupted before reaching it.

## 5. Pre-full-run (24.08)

- Deleted all generated files (`checkpoint.json`, `results.csv`, `experiment_matrix.csv`, everything under `artifact_download/`) for a clean slate.
- Committed and pushed `central_automated_pipeline.py` — noticed every `results.csv` row so far still recorded `git_commit=5e7ab9a...`, a old commit from *before* all of the Phase 9 bug-fixing and the Ctrl+C work, since the script itself had never been committed since then. Pushing brought provenance back in sync for the real run.
- Changed `__main__` from the filtered `target_cell_ids`/`test_cells` subset to the full matrix: `experiment_loop(all_matrix_rows, owner, repo, repo_url, image_tag, checkpoint_path, result_file_path)`.

## 6. Incident during the whole experiment run: `KeyError: 'runners'` crash

- Script crashed with `KeyError: 'runners'` inside `wait_for_runner_online`, at `for runner in runners_data["runners"]:`: the reason is that the `gh api .../actions/runners` call returned JSON without the expected key `"runners"`
  - script asks GitHub "is my runner online yet?" every 5 seconds while waiting. Do that check hundreds of times over many hours, and eventually GitHub either has a brief glitch answering one of those requests, or notices you're asking very often and briefly refuses to answer normally. Either way, that one answer comes back looking different than expected, missing the piece of information ("runners") your code assumed would always be there, and your code didn't know how to handle that unexpected shape, so it crashed instead of just trying again a few seconds later.
- This crashed the *whole script*, not just one cell — a real gap beyond the original "no retry framework, bad cells are left for manual rerun" design intent, which was about not auto-retrying a genuinely failed cell, not about the entire unattended run dying on one flaky API response.
- **Verified the checkpoint handled it correctly anyway**: the cell being processed when it crashed was confirmed absent from `checkpoint.json`, so resuming picked it up cleanly. Decided to accept this as a known, low-priority risk for now rather than add defensive handling (e.g. checking for the `"runners"` key before indexing) — noted as a possible future improvement, not applied this session.
- Cleanup before resuming: stopped the orphaned container, checked/removed any old GitHub-side registration for that cell, reran. (commands see above)

## 7. Incident 2 during the whole experiment run: WiFi outage caused a silently-wrong result

- WiFi dropped mid-cell for `mvn_A3_B1d_B2b_C1b`. `gh run watch` failed with a connection error but didn't raise (`check=False`), so the script continued; `gh run download` also failed (no internet) and returned `None`; the evidence file was never downloaded.
- Because nothing actually raised an exception, the cell completed its full path anyway — writing a **spurious `resolution_error` row** (caused by the network outage, not a real dependency-resolution outcome) and **permanently marking the cell done**, meaning it would never be retried automatically.
- A *separate* cell right after it crashed on `get_registration_token`'s `check=True` (also because wifi is done) — that one was correctly left unmarked and resumed fine on its own.
- **Manual fix applied**: removed `mvn_A3_B1d_B2b_C1b` from both `checkpoint.json`'s array and its row from `results.csv` by hand, so the next run would give it a legitimate attempt.


## 8. Full 432-cell experiment run completed

- Ran to completion (with the two incidents above handled via manual intervention and resume, not a single unbroken run).
- Post-run integrity check: `results.csv` had 434 lines instead of the expected 433 (432 data rows + header). Investigated, found it was **one single harmless blank line** (line 360), left over from manually deleting the spurious `mvn_A3_B1d_B2b_C1b` row by hand in section 7. exactly 432 real data rows, matching the full matrix exactly, no duplicates, no missing cells. Deleted the blank line.
- `results.csv` is now the complete, correct dataset for the full experiment matrix.

## 9. Real finding: explained an `npm_A1a_B1b_B2a_C1a` `resolution_error` result

- Checked the actual downloaded artifact/log for this cell instead of guessing — found a real `npm error code ETARGET: No matching version found for xueting-thesis-event-jianding@1.0.0`. Not a pipeline bug.
- Explanation: `A1a×B1b` writes two `registry=` lines into `.npmrc` (private group URL, then real public `npmjs.org`). npm has no true fallback for unscoped packages — it just picks one. Here it looks like npm used the **public** line: on real public npm this package only exists at the malicious version `1.0.3` (the one published for the DCA experiment), never at `1.0.0` — and since this cell pins exactly `1.0.0` (`B2a`), npm found the name but not that version and errored out.
- This looks like the empirical answer to the open question flagged back on 09-10.07.2026 (does npm's duplicate `registry=` use first-wins or last-wins?) — result suggests **last-wins**. Worth checking a couple more `B1b`/`B1c` cells to confirm the pattern holds, but this specific result is legitimate data, not something to fix.

## 10. Started a second full experiment run — two more unattended-run crashes, both recovered cleanly

- **Crash A**: `dispatch_cell`'s `gh workflow run` call failed with `CalledProcessError` (non-zero exit, transient GitHub API hiccup) — same general class as the `KeyError: 'runners'` crash from before, just a different call. Runner had registered fine but no job was ever dispatched to it, so it was just sitting there idle. Cleaned up the orphaned container + any stale GitHub registration, reran — `checkpoint.json` correctly did not contain the crashed cell, resumed cleanly.
- **Crash B**: `invalidate_nexus_cache`'s `requests.post` to local Nexus (`http://localhost:8081`) failed with `ConnectionResetError [WinError 10054]` — this one wasn't GitHub at all, a local connection to my own Nexus container got reset. Checked `docker ps`: Nexus itself was still healthy (`Up 4 hours`, no crash/restart) — likely a transient connection blip from sustained load over many hours, not an outage. Since this crash happens right at the *start* of `run_one_cell` (before any runner/container work begins), there was nothing to clean up this time — confirmed no orphan container/runner existed, just reran directly.
- **Pattern now confirmed across 3 separate incidents** (the earlier `KeyError`, plus these two): different root causes (GitHub API response shape, `gh` CLI transient failure, local Nexus connection reset), same underlying gap — any single network call failing anywhere in `run_one_cell` currently crashes the *entire* unattended run, not just that one cell. Decided **not** to patch each one individually as it comes up — instead planning one general fix (wrap the risky part of `run_one_cell` so an unexpected exception gets logged as a failed cell and the loop continues, instead of dying) before starting a third full run.

## 11. Organizational decision: separate result folders per experiment run

- Storing each experiment run's output under its own subfolder inside a `sub-RQ1_result` directory, rather than always overwriting the same `results.csv`/`checkpoint.json`/`artifact_download` in place — keeps each run's data separately reviewable/archivable given the run has had to be restarted multiple times already.

## Next steps

- [ ] Analyze the completed `results.csv` — classification counts, breakdown by A/B1/B2/C1, cross-check against expected-failure cells (`A2×B1a`, `A3×B1a`).
- [ ] CLI (`--matrix`/`--run-all`/`--cell`/`--cells`) still not built — only ever needed the full-matrix path this session; revisit if Sub-RQ2 needs the `--cells` subset-rerun capability.
- [ ] Consider (low priority): defensive handling for the `KeyError: 'runners'` case if it recurs, and/or a way to distinguish genuine `resolution_error` from a network-outage-caused one in future runs.
- [ ] Before a third full run: add general error handling around `run_one_cell`'s network calls, so any one transient failure (GitHub API, `gh` CLI, local Nexus) fails just that cell instead of crashing the whole unattended run — now hit 3 separate times with 3 different root causes.
- [ ] Check a couple more `B1b`/`B1c` cells (any ecosystem) to confirm the npm duplicate-`registry=` last-wins finding from section 9 holds consistently.

# 29.08.2026 Sub-RQ2 SCA tool selection: designed and refined the screening process, started Source B screening

**Stand:**  refined the full tool-selection screening process for sub-RQ2 methodology, corrected a circular selection-gate flaw in the original section 5.4.1 design, ran the GitHub/GitLab searches, exported candidate tool metadata to CSV, and started manual screening. Found one tool via snowballing that the primary search could not surface.

## 1. Designed the screening funnel (4 stages, 3 candidate sources)

- Three candidate sources, reported separately:
  - **Source A (literature)**: Syft, OpenSCA, OWASP Dependency-Check — from Ding et al. via Related Work. No DC-claim required; general-purpose SCA arm.
  - **Source B (GitHub + GitLab search)**: tools whose name/description explicitly claims dependency confusion detection.
  - **Source C (snowballing, added later today)**: tools found via guide/link-collection repos inside the Source B results.
- Stages: Stage 1 screening (is it an SCA tool? drop PoCs/demos/writeups) -> Stage 2 build theoretical table (documentation review) -> Stage 3 hard-requirement filter (doc-verifiable) -> technical evaluation -> final 3 tools selected.

## 2. Fixed a circularity flaw in the original methodology

- Original 5.4.1 text: a tool producing no DC alert "will be removed from the candidate list" -> this would inflate recall by construction (selecting for success, then measuring success).
- **Fix**: separated the gate from the measurement.
  - Gate for entering the final 3 = **integration feasibility** only (installs, runs, produces parseable output against the actual services).
  - Whether a tool actually detects DC = the measurement, never grounds for exclusion.
- Applies identically to Source A and Source B; all Source needs to go through the hard-requirement filter. otherwise the further technical evaluation is meaningless.

## 3. Defined 6 hard requirements (gate for final 3)

1. Integrates into the per-service CI pipeline (can run against a specific experiment cell)
2. Supports all 3 ecosystems (npm, pip, Maven) — matrix is 3 x n
3. Reads this application's actual config/lock files — npm: package.json, package-lock.json, .npmrc; pip: pyproject.toml, pip.conf, pylock.toml; Maven: pom.xml, lockfile.json, pom.lockfile.xml (not changing the services to fit a tool)
4. Produces machine-parseable output (JSON/SARIF) — needed for building the per-tool rule classifiers in central automated pipeline
5. Free, no mandatory account/API key — matches the ephemeral, reproducible runner design
6. Version can be pinned — consistent with every other pinned component / tools

5 of 6 (all except #1) are answerable from documentation alone -> used as a Stage 3 filter before technical evaluation, to keep the expensive hands-on step (technical evaluation) small.

## 4. Final-3 composition decision

- **2 DC-specific tools + 1 general-purpose mainstream SCA tool.**
- Rejected framing the third slot as a "negative control": a negative control must be known in advance to produce nothing, but whether general-purpose SCA tools detect DC is exactly the unknown sub-RQ2 investigates — calling it a control would presuppose the answer.
- The general-purpose slot is a **tool category**, not fixed to the 3 Ding et al. tools -> if none passes the hard-requirement filter, a replacement is drawn from widely-adopted OSS SCA tools (exact source deferred; preference for an academic source, e.g. Imtiaz et al., if triggered).
- Priority order when in conflict: (1) must fit the SCA tool definition (Foundations 3.4) > (2) hard requirements > (3) composition preference. research question wording will not be changed to fit tool availability.

## 5. Source B: GitHub + GitLab search, star threshold decision

- Checked GitHub topic `dependency-confusion`: only 38 repos -> too narrow, switched to full-text repo search.
- GitHub query (after correcting a bug — `in:name,description` and `-language:Markdown` are no-ops, verified via API, do not use):
  ```
  "dependency confusion" fork:false archived:false pushed:>2024-01-01 stars:>=1
  ```
  -> **46 results** (2026-08-29). Phrase must be quoted — unquoted matches the two words separately and pulls in false hits (e.g. a repo about "Zero dependencies. Infinite confusion." unrelated to the attack).
- Star threshold `>=1` chosen intentionally:  `>=1` just requires one person besides the author to have starred it. Distribution checked before picking: stars>=0 -> 134, >=1 -> 48 (unquoted)/46 (quoted), >=2 -> 28, >=5 -> 19, >=10 -> 11, >=50 -> 3. Threshold fixed BEFORE looking at which specific tools survive it.
- GitLab: query `"dependency confusion"` (exact search) (Projects scope, archived excluded) -> 10 results. GitLab has some syntax options like exact search, but no qualifier syntax like GitHub's, so all results are screened by hand instead of pre-filtered.
- `gh search repos` (the CLI's own flag-based search) does NOT reliably reproduce the web-UI query — tested, got 46 vs 43 vs other counts depending on flag combination. Do not use it for anything that needs to match a reported query string; use `gh api search/repositories` directly instead, since it takes the literal query string.

## 6. Exported Source B candidates to CSV

Command (in PowerShell; inner quotes need `\"` escaping for gh's raw-field flag):
```powershell
gh api -X GET search/repositories -f q='\"dependency confusion\" fork:false archived:false pushed:>2024-01-01 stars:>=1' -f per_page=100 --jq '([\"name\",\"url\",\"stars\",\"last_push\",\"license\",\"language\",\"description\"], (.items[] | [.full_name, .html_url, .stargazers_count, .pushed_at, (.license.spdx_id // \"none\"), (.language // \"\"), (.description // \"\")])) | @csv' | Out-File -Encoding utf8 dc_repos.csv
```
- Output: covers important information of each repo: `name, url, stars, last_push, license, language, description` for 46 repos, use CSV file as output file format.
- Opened in Excel via Data -> From Text/CSV (UTF-8, comma delimiter) 
- Saved as `.xlsx` for editing/screening (added extra columns: `source`, `drop reasons`, `found_via`). The original CSV (raw output of github api about repositories metadata) is kept untouched as the frozen/reproducible evidence file; the xlsx file is the working screening document and is never regenerated from a fresh export, which may silently update star counts/dates and break reproducibility of the reported numbers.

## 7. Source C: added snowballing as a formal supplementary source

- Discovered `synacktiv/DepFuzzer` (96 stars, actively maintained, MIT, Python) via a guide/link-collection repo (`BlackHatExploitation/dependency-confusion-exploitation-guide#scanning-tools` https://github.com/BlackHatExploitation/dependency-confusion-exploitation-guide#scanning-tools) that appeared inside the Source B results. (this link collection is not a detection tool so it will be dropped, but a tool is found inside this link collection repo)
- Root cause it was missed by Source B: GitHub repo search indexes only name/description/topics, never the README — DepFuzzer's repo has an empty description and no topics at all, so no phrase search could ever find it, regardless of terminology.
- Checked whether `in:readme` fixes this: yes, finds DepFuzzer, but expands the result set from 46 -> 608 repos — infeasible for manual screening in the available time.
- **Decision**: keep the 46-result primary search as-is, add snowballing (backward reference search, citable to Wohlin 2014 "Guidelines for snowballing in systematic literature studies") as a named, documented supplementary source (Source C). Record source repo + date for each snowball find.
- This is a important different blind spot from the earlier-documented "terminology-bound search" limitation (missed due to different wording) — this one is metadata-bound (missed due to empty description/topics, independent of terminology). Both now recorded as separate limitations.
- Command to pull any single repo's metadata into the same CSV row format:
  ```powershell
  gh api repos/OWNER/REPO --jq '[.full_name, .html_url, .stargazers_count, .pushed_at, (.license.spdx_id // \"none\"), (.language // \"\"), (.description // \"\")] | @csv'
  ```

## 8. Started manual Stage 1 screening on the 46 + 10 + (Source C) candidates

- Decided against any keyword-based pre-filter (e.g. excluding repos containing "poc"/"exploit"/"demo") — tested, and it would have wrongly dropped `snyk-labs/snync` (a real Snyk detection/mitigation tool whose description uses "mitigate" rather than any tested keyword). **Manual screening** with a recorded reason per repo stays fully auditable; a keyword filter is not, and risks silent false exclusions.
- Screening principle: we need to determine this tool is actually an SCA tool. questions like: does the tool analyze a project's own dependency/manifest files, or does it just check whether package names are unclaimed on a public registry (bug-bounty recon pattern)? The latter fails the SCA-tool definition and/or the "reads our config files" hard requirement.
- Concrete example dropped at Stage 3, not Stage 1, since it does pass the SCA-tool/detection-tool/ecosystem screen: `KingOfBugbounty/Dependency-Confusion-Hunter` — Chrome extension (can't run in the CI runner), npm/PyPI only (no Maven), reads live web pages/source maps rather than project config files, outputs via Discord webhook (not machine-parseable). Fails hard requirements 1, 2, 3, and 4.

## Reference links collected today

- GitHub CLI `gh search repos` manual: https://cli.github.com/manual/gh_search_repos
- GitHub REST API - Search repositories: https://docs.github.com/en/rest/search/search?apiVersion=2026-03-10#search-repositories
- GitHub CLI `gh api` manual: https://cli.github.com/manual/gh_api
- dependency confusion guide repo used for snowballing: https://github.com/BlackHatExploitation/dependency-confusion-exploitation-guide#scanning-tools

## Next steps

- [ ] Finish Stage 1 screening of all Source B (46) + Source C candidates, screen the 10 GitLab results
- [ ] Populate the theoretical evaluation table (14 columns) for everything that survives Stage 1, including Source A (Syft, OpenSCA, OWASP Dependency-Check — note: correct repo is `dependency-check/DependencyCheck`, the old `jeremylong/DependencyCheck` is archived)
- [ ] Apply the Stage 3 doc-verifiable hard-requirement filter to produce the technical-evaluation shortlist
- [ ] Redraw Figure 5.4 (simplified + detailed versions) to reflect the corrected non-circular gate and the 3-source funnel
- [ ] Decide GitLab star/quality threshold if the 12 results turn out to need one (currently screening all 12 by hand, no threshold applied)

# 05.09.2026

## Changed PIP_CONFIG_FILE's B1d fallback from empty string to /dev/null

- `service-ci-python.yml`: in all three C1 steps (C1a, C1b, C1c), `PIP_CONFIG_FILE`'s B1d fallback changed from `''` to `/dev/null` — this is pip's own officially documented way to disable config loading. The empty string worked too (pilot-tested and confirmed equivalent on 14.08), but wasn't the documented method, so switched to the documented value directly.

# 06.09.2026

## Removed redundant dependency:tree command from Java C1a/C1b, found a real confound in the process

### The problem
- Java's C1a and C1b (phase 2) ran two separate Maven commands per cell: `mvn dependency:tree` (writes dependency-tree.json: name+version+tree shape only) followed by `mvn maven-lockfile:generate` (writes lockfile.json: name+version+checksum+resolved URL+repositoryId).
- Checked the maven-lockfile plugin's own source (GenerateLockFileMojo.java) and its paper (arXiv:2510.00730): generate performs its own full dependency resolution (`@Mojo(requiresDependencyResolution=..., requiresOnline=true)`), completely independent of dependency:tree.
- This means every C1a/C1b cell was resolving dependencies twice against the network, and dependency-tree.json's content is a strict subset of what lockfile.json already provides.
- Worse: since both commands ran in the same step, same container, same cell, with no cache clear between them, dependency:tree populated ~/.m2 moments before generate ran for that same cell — meaning generate's resolution was never actually observed from a clean cache within that cell. This is a different confound from the one found on 09.08 (a persistent, cross-cell pilot container reusing artifacts from an earlier, different cell — solved by ephemeral per-cell containers). This new one is within one cell, and ephemeral containers do not solve it, since both commands share the same container instance for that one cell.
- Checked: `mvn -X` (verbose mode) is the only built-in way to see a resolved URL at all, and it's unstructured log text that doesn't even print for already-cached artifacts — confirming there is no built-in Maven alternative that gives structured name+version+URL, which is why the third-party plugin was needed in the first place.

### Design decisions
1. Remove dependency:tree entirely from C1a and C1b — rely solely on maven-lockfile:generate for both resolution and evidence. (C1c never used dependency:tree, unaffected.)
2. C1b's phase 1 (setup) now uses maven-lockfile:generate too instead of dependency:tree, producing `<cell_id>_setup-lockfile.json` (renamed from `<cell_id>_setup-dependency-tree.json`); the phase-2-gating sanity check now tests for this file's existence instead.
3. `-U` (force metadata re-check) — confirmed via Maven's own CLI reference (https://maven.apache.org/ref/current/maven-embedder/cli.html) that this is a core Maven flag, not plugin-specific, so it applies the same way regardless of which goal is running. Moved from the now-removed dependency:tree call onto generate directly in C1b's phase 2, so the "force fresh check" behavior isn't silently lost.
4. Added `2>&1 | tee` (into `_mvn_log.txt` / `_mvn_setup_log.txt`) directly onto the generate calls — previously only dependency:tree's output was captured to log files; generate itself was never logged at all.
5. Updated the artifact upload list: removed `<cell_id>_dependency-tree.json` and `<cell_id>_setup-dependency-tree.json` (files that no longer get produced), added `<cell_id>_setup-lockfile.json`.

### Where this gets documented in the thesis
- Implementation chapter (6.4.5.3): the full "why removed" story — implementation-only content, same treatment as other empirical findings already documented there.
- Results chapter: only if a planned re-run (the 3. time main experiment run) (comparing the old double-resolution data/result against a clean single-resolution re-run) shows an actual difference in classification outcomes or evidence completeness. Not decided yet — pending that comparison.

### Next steps
- [ ] Re-run the full 432-cell experiment tonight with the corrected pipeline (third run).
- [ ] Compare classification outcomes + evidence completeness (resolved/repositoryId fields) between this run and the original two runs.
- [ ] Decide, based on that comparison, whether this needs to also appear in the Results/Limitations chapters.

# 07.09.2026

**Stand: Before starting the 3. full experiment run, reworked the classification logic in `central_automated_pipeline.py` so it no longer depends on the Nexus port number, added general crash handling so one flaky network call can no longer kill an entire unattended run, and fixed a small evidence bug in `service-ci-java.yml`'s C1b failure path.**

## 1. Rewrote the classification logic: repository names instead of the port number

### The problem (why reconsider is needed)
- The old helper `is_from_nexus(url)` decided "did this come from Nexus?" by checking whether the string `"8081"` appeared in the resolved URL.
- Two things wrong with that:
  - **Fragile**: the whole classification depends on a port number. If I ever change the Nexus port, every cell silently reclassifies and I would not notice.
  - **Throws away information**: it collapsed all four repository types into one yes/no. But "came from Nexus" is not the interesting question — *which* Nexus repository served it is.

### What I changed
- Replaced `is_from_nexus(url)` with `get_repo_origin(ecosystem, url)`, which matches the actual **repository name** inside the URL and returns one of four origins:
  - `hosted` -> `*-internal-hosted` (my own internal repository)
  - `group` -> `*-group-public-first` / `*-group-private-first`
  - `proxy` -> `*-public-proxy` (public registry, reached through Nexus)
  - `external` -> anything else, including `url is None` (public registry reached directly, bypassing Nexus)
- Added an `internal_hosted_repo` dict next to the existing `group_repo` / `proxy_repo` dicts, so all repository names live in one place and the classifier reads them from there instead of hard-coding anything.
- `classify_logic` now uses **package name + version + resolved URL together**:
  1. evidence file missing/unreadable -> `resolution_error`
  2. any package with version in `malicious_version` and origin not `hosted` -> `malicious_resolved` (checked first, with priority)
  3. all internal packages with version in `internal_version` and origin `hosted` or `group` -> `private_resolved`
  4. otherwise -> `resolution_error`

### Design decisions and why

- **Why `group` still counts as `private_resolved`, even though a group URL is ambiguous.**
  - A group repo URL genuinely cannot tell me which member served the artifact — that is what a group repo *is*. So the URL alone is not enough.
  - It is the **version** that disambiguates it, not the URL.
  - I checked this against the real run-2 data instead of just assuming it, and the numbers make the point better than any argument:
    - the group repo served internal `1.0.0` **110 times** and attacker `1.0.3` **60 times**, from the same URL prefix -> **URL alone cannot decide origin**
    - internal `1.0.0` arrived via `hosted` **42 times** and via `group` **110 times** -> **version alone cannot decide path**
    - `1.0.3` never once came from `hosted`; `1.0.0`/`1.0.2` never once came from `proxy` or `external`
  - So neither field is sufficient on its own, and together they resolve every cell in the matrix unambiguously. This is exactly the empirical justification for why I went to the trouble of obtaining a lockfile with resolved URLs for all three ecosystems — without the URL I would have had no way to show this.

- **Why I added `origin != "hosted"` to the malicious rule (this overrides my 21-22.08 decision).**
  - On 21-22.08 I wrote that `malicious_resolved` should stay version-only, because a malicious package can arrive either through the Nexus proxy **or** straight from the public registry, and requiring "must come from Nexus" would wrongly exclude the second case (the confirmed `A3 x B1a x B2b x C1c` Maven cell that resolved `1.0.3` directly from `repo.maven.apache.org`).
  - That reasoning still holds and is **not** violated: the new guard does not exclude `external` or `proxy`. It only excludes `hosted`.
  - Why excluding `hosted` is safe: `maven-internal-hosted` / `npm-internal-hosted` / `pypi-internal-hosted` are my own repositories, and I never uploaded version `1.0.3` to any of them. A `1.0.3` from `hosted` is impossible by construction.
  - In run 2 the guard fired **0 times** across 540 evidence entries, so it changes nothing empirically — it only makes the rule use all three signals consistently.

- **Why I do not use `repositoryId`, and why not checksums.**
  - `repositoryId` is unreliable: because of the `id=central` override in `generate_pom_xml.py`, internally hosted Maven artifacts report `repositoryId = "central"`. Already documented earlier, still true.
  - Checksums verify **integrity**, not **origin**. The attacker's `1.0.3` has a perfectly valid hash of itself. A hash proves the file was not altered in transit; it cannot tell me whether the coordinate was satisfied internally or externally. Only the resolved URL carries that.



## 2. Added crash handling so one flaky call cannot kill the whole run

### The problem: three crashes, three different causes, one shared gap
During experiment runs 1 and 2 the script died completely three separate times:
- **`KeyError: 'runners'`** in `wait_for_runner_online` — the `gh api .../actions/runners` response came back without the `"runners"` key (GitHub glitch, or a soft rate-limit response). This check runs every 5 seconds for hours, so sooner or later one response has an unexpected shape.
- **`CalledProcessError`** in `dispatch_cell`'s `gh workflow run` — a transient GitHub API hiccup. The runner had registered fine, but no job was ever dispatched to it.
- **`ConnectionResetError [WinError 10054]`** in `invalidate_nexus_cache`'s `requests.post` — not GitHub at all, but my **local** Nexus. `docker ps` showed Nexus itself was healthy and never restarted, so this was a transient connection blip under sustained load.

The three root causes are unrelated, but the gap is the same: **any single network call failing anywhere in `run_one_cell` crashed the entire unattended run**, not just that one cell. The checkpoint always recovered correctly afterwards (the in-progress cell was never in `checkpoint.json`, so a rerun resumed cleanly) — but only if I noticed and restarted the script, which defeats the purpose of running overnight.

### What I added and why
- **Wrapped the whole body of `run_one_cell` in `try / except Exception`.** On any unexpected exception: append `timestamp: cell_id - error` to `crashed_cells.txt`, `return`, and let the loop continue with the next cell. The crashed cell is deliberately **not** marked in `checkpoint.json`, so simply re-running the script re-attempts it after everything else has finished.
- **Why one general fix instead of patching each call as it breaks.** I hit three different failure points already; patching them one by one only ever protects against the failures I have already seen. Wrapping the cell protects against the ones I have not seen yet.
- **This does not contradict my "no retry framework" decision.** That decision was about not auto-retrying a cell that *genuinely* failed to resolve — a real `resolution_error` is data, not an error. This is about transient infrastructure failures killing the run, which is a different thing entirely.
- **`except Exception`, not a bare `except:` — chosen deliberately.** `KeyboardInterrupt` inherits from `BaseException`, not from `Exception`, so a bare `except:` would have swallowed Ctrl+C and silently broken the graceful-stop mechanism I built on 23-25.08. The narrower clause keeps the two mechanisms independent of each other.
- **Made `copy_invalid_rows` conditional.** It used to run at the end of *every* loop, so a run that stopped early (crash or Ctrl+C) still appended the 72 invalid rows, and the next resume appended them a second time. Now the loop reloads `checkpoint.json` afterwards and only writes the invalid rows once every valid cell is actually finished — which, now that crashed cells survive to a later rerun, is the only moment `results.csv` is genuinely complete.

### How this fits together with the Ctrl+C handling from 23-25.08
- The SIGINT handler sets a `stop_requested` flag instead of raising, and both `if stop_requested: return` checks sit **before** `write_result_file` and `mark_cell_as_finish`. So an interrupted cell is never marked done and is picked up cleanly on the next run.
- The new `except Exception` cannot catch the interrupt itself, so the two mechanisms do not interfere. Confirmed by reasoning through both paths rather than only testing one.

### Accepted limitation (unchanged decision, but a new consequence)
- Still **no automatic Docker container teardown** in the script — consistent with my original Phase 6 decision to keep the pipeline focused on research logic rather than infrastructure robustness. Cleanup stays manual (`docker ps` + `docker rm -f`).
- **New consequence to be aware of during run 3**: a crash no longer stops the script, so nothing prompts me to clean up. A crashed cell's orphaned runner container is still running when I rerun, and that cell will fail again on `docker run --name thesis-runner-<cell_id>` ("name already in use") until I remove the orphan by hand. So: check `docker ps` and `crashed_cells.txt` before each resume.
- Decided **not** to add a duplicate-row guard to `copy_invalid_rows` for re-invocations after a fully completed run, because before run 3 I delete `checkpoint.json`, `results.csv`, `experiment_matrix.csv` and `artifact_download/` and start from a clean state anyway.

## 3. Bug fixed in `service-ci-java.yml`: C1b failure path did not restore the real pom.xml

### The problem
- C1b works in two phases: phase 1 moves the cell's `pom.xml` aside to `pom_cell.xml`, copies in `fixed_setup_file/fixed_pom.xml` (pinned `1.0.0`) and resolves it; phase 2 moves the real pom back and re-resolves with `-U`.
- The **success** path restores the real pom correctly. The **failure** path did not: if the setup-phase sanity check found no `_setup-lockfile.json`, the step did `exit 0` immediately, leaving `pom.xml` = the fixed setup pom and the cell's real pom still sitting in `pom_cell.xml`.
- Consequence: for those failed cells, the uploaded artifact contained the **wrong pom.xml** — the generic fixed setup pom instead of the one with that cell's actual A/B1/B2 configuration. This does not affect classification (the classifier never reads `pom.xml`), but it makes the artifact useless for manually debugging exactly the cells that failed and most need debugging.


### The fix
- Added `mv pom_cell.xml pom.xml` immediately before the `exit 0` in C1b's setup sanity-check block, mirroring what python's C1b already does.
- C1a and C1c are unaffected — they never swap the pom at all.

## 4. Reviewed the C1b design as a whole and tested one validity threat

- Checked whether the hard-coded repository in `fixed_pom.xml` could contaminate the measurement. `fixed_pom.xml` points at `maven-group-public-first` (A1a) for **every** cell, and phase 1 populates `~/.m2` from it. If maven-lockfile recorded the *cached* origin rather than the cell's own resolution, then every C1b cell would show `maven-group-public-first` and the whole URL signal would be an artefact of my setup phase rather than a real result.
- Checked all 48 Java C1b rows from run 2: every recorded URL matches the **cell's own** A/B1 — `A1b` -> `maven-group-private-first`, `A2`/`A3` -> `maven-internal-hosted`, `B1d` -> `repo.maven.apache.org`, and `maven-group-public-first` only where the cell really is A1a. **The setup phase does not leak into the measured evidence.** Worth writing up as a threat to validity that I tested and ruled out empirically, rather than one I just asserted was fine.
- Confirmed `-U` in phase 2 is necessary, not decorative: Maven's default `updatePolicy` for releases is `daily`, so a cached `maven-metadata.xml` could otherwise hide `1.0.3` from a version range during a multi-hour run. It matters specifically for the A1a cells, where phase 1 and phase 2 hit the same repository.
- Noted one cross-ecosystem asymmetry for the methodology chapter: npm and pip name the two internal packages explicitly in their update commands (`npm update <pkg1> <pkg2>`, `pip install --upgrade <pkg1> <pkg2>`) — a **targeted** update. Maven has no update verb, so `-U` + re-resolve is a **whole-project** update. The effect on the internal packages is equivalent, but the scope differs, and a reader comparing C1b across the three ecosystems will notice.

## 5. Bug found in `service-ci-nodejs.yml`: C1b uploaded the setup lockfile as the cell's evidence -> leading incorrect classification of 1. and 2. experiment run!!

### How I found it
- While planning the result analysis, I added one check: for every cell, does the evidence file that the classifier reads really come from the **operation under test**, and not from the setup phase?
- I compared each C1b cell's `_npm_log.txt` with its classification in `results.csv`.
- Found **11 npm C1b cells labelled `private_resolved` even though their log clearly says `npm error code ETARGET`**. The update had failed, but the cell looked safe.
- Extra clue that confirmed it: the string `localhost:8081` appears in the resolved URL of **exactly 15 nodejs C1b rows and nowhere else** in the whole result file. `localhost` is the old hostname stored inside the fixed setup lockfile.
- This also **corrects my earlier note from 21-22.08**, where I assumed `localhost:8081` came from Nexus caching computed metadata. That was wrong. It comes from the fixed setup lockfile.
- The affected cells are all npm, all B2a: `npm_{A1a,A1b,A2,A3}_{B1b,B1c,B1d}_B2a_C1b` (A3 x B1c is invalid, so 11 and not 12).

### The problem
- C1b phase 1 copies `fixed_setup_file/npm-service-fixed-lock.json` to `package-lock.json`.
- C1b phase 2 ran `npm update ... 2>&1 | tee log || true`, which writes to **the same file name** `package-lock.json`.
- Two things went wrong together:
  1. In a pipeline `A | B`, bash returns the exit code of the **last** command. That is `tee`, and `tee` always succeeds, because writing a file works even when the text it copies is an error message. So a failed `npm update` looked successful. The `|| true` at the end hid it even more.
  2. When the update failed, `package-lock.json` was still the **untouched setup file**, and it was uploaded as this cell's evidence.
- The central pipeline then read that setup lockfile, saw internal version `1.0.0` coming from a Nexus repository, and wrote `private_resolved`.
- Direction of the error is **"false safe"**: these cells look protected, although the update actually failed. It never produces a false `malicious_resolved`, so my main findings do not change. (basically it should be classify as "resolution error" but turns out to "private_resolved". this is also wrong classification and need to be fixed immediately)
- Important: **this is a CI workflow bug, not a classifier bug.** The classifier only receives a file. It cannot know which phase produced it. The new `get_repo_origin` logic I wrote earlier today could not have prevented this.

### The fix
- Keep the setup state under its own name so nothing is lost: `cp package-lock.json "<cell_id>_setup-package-lock.json"`, and add that file to the upload list.
- Add `set -o pipefail` so the pipeline reports **npm's** exit code instead of `tee`'s.
- Replace `... || true` with `if ! npm update ...; then ... fi`, and delete `package-lock.json` inside that block when the update failed.
- Result: no evidence file is uploaded, `read_npm_evidence` returns `None`, and the classifier writes `resolution_error`. This is the correct outcome, because if the operation under test did not run, the cell holds no valid observation.
- **No Python change was needed.** The classifier already handles a missing evidence file correctly.
- Note on syntax: a command used as an `if` condition is not affected by the default `set -e` of GitHub Actions, so the step does not abort early.

## 6. Applied the same fail-closed rule to npm C1c (defensive, no data changed)

- After finding the C1b bug I checked whether C1c has the same weakness, because C1c also touches `package-lock.json` in both phases.
- Checked the official npm documentation for `npm ci`: *"It will never write to `package.json` or any of the package-locks: installs are essentially frozen."*
- So for C1c the phase-1 lockfile **is** the correct evidence, because `npm ci` performs no dependency resolution at all. It only installs what the lockfile already decided. This is the same point I noted for pip C1c on 08.08: locking only freezes whatever resolution outcome already happened.
- But there is still a gap: if `npm ci --dry-run` itself failed, the phase-1 lockfile would still be uploaded, and the cell would be scored as if the rebuild had succeeded.
- Decision: apply the same rule as C1b, mainly for **cross-ecosystem consistency**. pip C1c and java C1c already fail closed, because their phase 2 writes its own evidence file. npm should behave the same way, otherwise the same situation would be labelled differently in different ecosystems, which would damage the cross-ecosystem comparison.
- Important difference from C1b: here I keep the phase-1 lockfile as `<cell_id>_setup-package-lock.json`, because it is real resolution evidence and must not be lost.
- This changed nothing in the data: **0 of 45 npm C1c cells have ever failed** in any run. So npm C1c does **not** need to be re-run.

### One sentence for the methodology chapter (now true for all three ecosystems)
> If the operation under test (for example package update, rebuild with lockfile failed in phase 2) does not complete, then the cell doesn't produce valid observation file (e.g. lockfile) and is recorded as `resolution_error`.

## 7. Checked the python and java pipelines for the same kind of bug - none found

- The npm bug happened because phase 1 and phase 2 wrote the **same** file name. So I checked whether the other two ecosystems do the same. They do not:

| pipeline | phase 1 writes | phase 2 / 3 writes | classifier reads |
|---|---|---|---|
| pip C1b | `_setup-install-report.json` | `_install-report.json` | `_install-report.json` |
| pip C1c | `pylock.<cell_id>.toml` | `_install-report.json` | `_install-report.json` |
| mvn C1b | `_setup-lockfile.json` | `_lockfile.json` | `_lockfile.json` |
| mvn C1c | `_lockfile.json` | `_rebuild-lockfile.json` | `_rebuild-lockfile.json` |

- In all four cases the classifier reads **only** the file written by the phase under test. So if phase 2 fails, there is simply no evidence file and the cell correctly becomes `resolution_error`.
- The java pipeline also deletes `${cell_id}_*.json` in its cleanup step, so there is no carry-over between cells either.
- I also checked this against the real run 2 data, not only by reading the code:
  - Rule "`resolution_error` if and only if the evidence file is missing": **0 violations** across all 360 valid cells.
  - pip writing a `--report` file even though pip failed: **0 cases**.
  - java lockfile present but internal packages missing, or with an empty `resolved` field: **0 cases**.
- Extra check: I re-ran today's rewritten classifier over the **archived run-2 artifacts**. All 360 valid cells came out exactly the same as stored: 190 `malicious_resolved` / 80 `private_resolved` / 90 `resolution_error`, **0 mismatches**. This proves two things at once:
  1. The saved artifacts are complete enough to rebuild `results.csv` from scratch, so I can re-classify offline without re-running any cell.
  2. Today's classifier rewrite really is outcome-identical to the old port-based version on run-2 data. Earlier I only argued this; now it is measured.
- Honest limit of this check: it proves that no bug **shows up in the data**, and that the file naming design is sound. It cannot prove that a code path which never ran is correct. The path "phase 1 succeeds, phase 2 fails" has never happened for pip C1c and java C1b / C1c. The npm bug was findable exactly because it did happen, 11 times.

## 8. A second, smaller npm C1b problem that the fix does NOT solve

- 4 further cells also carry `localhost:8081` in their URL: `npm_{A1a,A1b,A2,A3}_B1a_B2a_C1b`.
- Here `npm update` really **succeeded**, but it did **nothing**: B2a pins version `1.0.0`, and the lockfile already contained `1.0.0`, so there was nothing to update.
- Because npm did not rewrite the file, the `resolved` URL stayed exactly as it was inside the fixed setup lockfile: `npm-group-public-first`.
- For the A2 and A3 cells that repository does not even exist in their configuration.
- So the **classification is correct** (`private_resolved`, because version `1.0.0` really did come from Nexus), but the **recorded URL does not belong to this cell**.
- The fix from point 5 does not help here, because npm exits with code 0. This is a property of the static setup lockfile, not a failure.
- How I will handle it: mark these 4 cells during result analysis and never use them for any statement about **where** a package came from. They are not used in the malicious-origin analysis anyway, because that analysis only looks at `malicious_resolved` cells.
- Counter example proving the normal C1b path still works: `npm_A2_B1a_B2b_C1b` prints the same short `up to date` message, but really did rewrite the lockfile (`1.0.0` -> `1.0.2` from `npm-internal-hosted`). So `up to date` alone is not a failure signal. The URL is what tells the two cases apart.

## 9. How I will re-run the experiment after this fix

- Run 3 had already finished **all 135 npm cells** before I found the bug, so the npm C1b cells in run 3 are affected too.
- Decision: **do not stop run 3.** The pip and java cells are not affected by this bug, and stopping now would throw them away for nothing. The npm cells would need re-running either way.
- After run 3 finishes:
  1. Archive run 3 into `sub-RQ1_result/` like the previous runs.
  2. Delete the 45 `npm_*_C1b` entries from `checkpoint.json`.
  3. Delete the same 45 rows from `results.csv`.
  4. Start the central automated pipeline normally.
- I do **not** need to build the `--cells` subset option for this. The existing checkpoint logic already skips finished cells, so it will skip the other 387 and only run the 45 missing ones.
- Regression check for the re-run (this is how I will know the fix worked):
  - Exactly **11 cells** must change from `private_resolved` to `resolution_error`.
  - The other **34 cells must come out exactly the same** as before. If any of them changes, something else is wrong.
  - After the re-run, `localhost:8081` must appear in exactly **4 rows** of `results.csv` - only the no-op cells from point 8.
- npm C1c does **not** need to be re-run (0 failures ever).
- pip and java do **not** need to be re-run for this bug.

### What this means for the thesis text
- Implementation chapter 6.4: describe the two-phase C1b design, and why phase 1 and phase 2 must never write the same file name.
- Methodology chapter: the one-sentence rule from point 6, that an incomplete operation is recorded as `resolution_error` in all three ecosystems.
- Limitations: the 4 no-op cells from point 8, and the fact that npm establishes the "existing lockfile" state with a **static file**, while pip and java do a **live resolve using the cell's own configuration**. This is a real construct asymmetry between the ecosystems and should be stated, not hidden.


## Next steps
- [ ] Delete `checkpoint.json`, `results.csv`, `experiment_matrix.csv` and `artifact_download/` (after archiving run 2 into `sub-RQ1_result/`), then start the third full 432-cell run from a clean state.
- [ ] Check `docker ps` and `crashed_cells.txt` before each resume of run 3.
- [ ] Compare run 3's classification outcomes and evidence completeness against runs 1 and 2, and decide whether the 06.09 double-resolution finding needs to appear in the Results/Limitations chapters.
- [ ] Write the name + version + URL justification into the methodology chapter, including the three caveats: a group URL identifies the serving repository and not the ultimate upstream; `repositoryId` is deliberately unused; checksums verify integrity, not origin.

# 08.09.2026

Today: re-ran the 45 npm C1b cells after yesterday's fix, verified the fix worked, compared the Java
results across all three runs, and investigated one unexpected Java result. Ended with a design
decision about the C1b baseline that I decided **not** to change.

## 1. Re-ran the 45 npm C1b cells and verified the fix

### How I did the re-run
`checkpoint.json` is a flat JSON list of 432 cell IDs written from a Python `set`, so it is unordered
and all on one line. Editing it by hand is not practical. I used a small throwaway script instead,
which did three things:
1. removed the 45 valid `npm_*_C1b` IDs from `checkpoint.json` (432 -> 387),
2. removed the same 45 rows from `results.csv` (432 -> 387),
3. **deleted the 45 matching directories in `artifact_download/`**.

Step 3 turned out to be essential. `download_artifact()` calls `gh run download ... -D dest_dir` and
**does not clear the directory first**. After the fix a failed cell uploads no `package-lock.json`,
but the stale one from the previous run would still have been sitting in the directory, and
`read_npm_evidence()` would have read it. The bug would have survived the re-run and looked fixed.

I left the 3 invalid `npm_A3_B1c_*_C1b` rows alone. They never ran, and `copy_invalid_rows()` reads
from `experiment_matrix.csv` and does not check the checkpoint, so all 72 invalid rows get appended
again automatically once every valid cell is finished.

### Result: the fix works, exactly as predicted
Compared the new `results.csv` against the archived pre-fix version
(`sub-RQ1_result/0709_backup_wrongresult/results.csv`):

- **Exactly 11 cells changed**, all `private_resolved` -> `resolution_error`. Their package name,
  version and URL fields are now empty, which is correct: the stale setup lockfile is no longer
  uploaded, so there is no evidence and the cell is an error.
  The 11: `npm_{A1a,A1b}_{B1b,B1c,B1d}_B2a_C1b`, `npm_A2_{B1b,B1c,B1d}_B2a_C1b`,
  `npm_A3_{B1b,B1d}_B2a_C1b`.
- **The other 34 valid npm C1b cells came out byte-identical.** This is the important half of the
  check: the fix only fired where the update really failed and changed nothing else.
- `localhost:8081` dropped from **15 rows to exactly 4** — only the known no-op cells
  `npm_{A1a,A1b,A2,A3}_B1a_B2a_C1b`, where `npm update` succeeded but had nothing to do.
- 432 rows before and after, identical cell ID sets, no duplicates.

**The headline number did not move: 190 `malicious_resolved`, unchanged.** This confirms the bug was
purely "false safe" — it inflated `private_resolved` and never created a false attack success.

## 2. Compared the Java results across all three runs (effect of removing `dependency:tree`)

- Run 1 vs run 2: **0 Java cells differ** (identical pipeline code).
- Run 3 vs runs 1/2: **6 Java cells differ, all C1b** — exactly the operation the 06.09 change
  touched. Nothing outside C1b moved, which is the result I wanted.

The evidence became **more complete**, not less:

| cells | runs 1 & 2 | run 3 |
|---|---|---|
| 4 cells (`B1d`) | error, version field empty | error, version `1.0.0` now recorded |
| `mvn_A2_B1a_B2a_C1b` | `resolution_error`, no evidence | `private_resolved`, `1.0.0` from `maven-internal-hosted` |
| `mvn_A2_B1a_B2b_C1b` | `resolution_error`, no evidence | `private_resolved`, `1.0.2` from `maven-internal-hosted` |

**Explanation:** this confirms the confound I identified on 06.09. Previously `dependency:tree` ran
first and warmed `~/.m2`, so when `maven-lockfile:generate` ran afterwards it resolved from the local
cache instead of downloading, and recorded an **empty `resolved` field**. Now `generate` runs from a
cold cache, actually downloads, and records the real URL. Same mechanism as the cached `javalin`
observation from 09.08. So removing `dependency:tree` improved measurement validity in a way I can
now demonstrate with data, not only argue.

Java totals moved from 30/42/18 to **32 private / 42 malicious / 16 error**. The malicious count
did not change.

## 3. Investigated `mvn_A2_B1a_*_C1b` — why does a hosted-only config resolve successfully?

This looked wrong at first. A2 = internal hosted + a separate public proxy, B1a = the package manager
points **only** at the internal hosted repo. The public dependencies (`javalin`, `jackson-databind`)
cannot exist there, so the build should fail — and indeed C1a and C1c for the same configuration are
both `resolution_error`. Only C1b succeeded.

I compared the two lockfiles of that cell:

| dependency | phase 1 (`fixed_pom.xml`) | phase 2 (cell's A2 x B1a pom) |
|---|---|---|
| `jackson-databind` | `maven-group-public-first` | **empty** — served from local `~/.m2` |
| `javalin` | `maven-group-public-first` | **empty** — served from local `~/.m2` |
| `xueting-thesis-event-juhe` | `maven-group-public-first` | `maven-internal-hosted` |
| `xueting-thesis-result-fanhui` | `maven-group-public-first` | `maven-internal-hosted` |

So: `fixed_pom.xml` hardcodes `<url>.../maven-group-public-first/</url>`. Phase 1 downloads the public
dependencies through the group repository into `~/.m2`. Phase 2 then resolves the two internal
packages correctly from `maven-internal-hosted` and finds the public ones already cached, so the build
succeeds. Phase 2 downloaded only 2 artifacts, both unrelated Jetty test jars.

The clean contrast is: **C1a and C1c fail for this configuration, C1b succeeds, and C1b is the only
operation with a phase 1.**

## 4. Design decision: keep the C1b baseline design as it is

I spent a while questioning whether the C1b design is wrong. Conclusion: **it is not, and I am not
changing it.** Writing down the reasoning because it belongs in the methodology chapter.

### What the design actually is
C1b fixes **what** should already be installed (version 1.0.0) using a baseline file, while **where**
it is fetched from stays the experiment cell's own configuration. Phase 1 is allowed to fail: a
configuration that cannot obtain 1.0.0 genuinely cannot reach the "update an existing installation"
scenario, so skipping phase 2 there is the correct behaviour, not a defect.
C1c has no baseline file at all — phase 1 resolves under the cell's own configuration and produces
the lockfile that phase 2 then rebuilds from. If phase 1 fails there, the rebuild is meaningless and
is skipped.

### Why it is defensible even though the three ecosystems do it differently
The starting state is defined at the **abstract level** ("version 1.0.0 is the current resolved
state") and each ecosystem realises it with its own native mechanism. This is normal
operationalisation: state the construct once, then state how each ecosystem implements it, and
disclose where the implementations differ. Forcing all three to use identical mechanics would be
**less** valid, because it would measure my harness instead of the real package managers.

- **npm**: the lockfile *is* the record of what is installed, so a fixed `package-lock.json` plus
  `--package-lock-only` represents "1.0.0 is current" exactly. No installation needed. Consequence:
  npm's phase 1 can never fail.
- **pip**: no such record exists, so phase 1 really installs into `./py_dependency`.
- **Maven**: no lockfile either, so phase 1 resolves a fixed pom.

### The one thing that must be disclosed — and it is a finding, not a weakness
Only **pip** can separate "what to install" from "where to get it" cleanly. I checked
`fixed_pyproject.toml`: it contains **zero** registry information, so pip's "where" lives entirely in
the cell's `pip.conf`. The other two cannot do this:
- `package-lock.json` records `resolved` URLs,
- `pom.xml` declares `<repositories>` in the same file as `<dependencies>`.

So in npm and Maven the baseline file unavoidably fixes part of the registry configuration too.
**This is a structural property of the ecosystems, not a choice I made.** It is exactly the kind of
ecosystem asymmetry this thesis is about, so it belongs in the results, not only in limitations.

### Concrete consequence: 2 cells
`mvn_A2_B1a_B2a_C1b` and `mvn_A2_B1a_B2b_C1b` are `private_resolved` because `fixed_pom.xml` let
phase 1 fetch the public dependencies through the group repository. pip's equivalent cells are
`resolution_error`, which is what the design intends. I am reporting these 2 cells as they are and
noting that C1a and C1c give the uncontaminated answer for that configuration. Two cells out of 360,
fully explained.

Optional future fix (not doing it now): generate the C1b phase-1 pom with pinned `1.0.0` **plus the
cell's own A/B1 repositories**, reusing `generate_pom_xml`. That would make Maven match pip exactly
and would probably turn those 2 cells into `resolution_error`. Not worth another 45-cell run, because
C1a and C1c already give the clean answer.

### Paragraph drafted for the methodology chapter
> The starting state for the package update operation is defined at the level of the resolved
> dependency state: version 1.0.0 is current. Each ecosystem establishes this state with its own
> native mechanism, because no single mechanism exists across all three. In npm the lockfile is
> itself the record of the resolved state, so a fixed `package-lock.json` is sufficient and no
> installation is required. In pip and Maven no such record exists, so the state is created by
> resolving a fixed dependency declaration. The registry configuration remains that of the
> experiment cell in all three cases, except that `package-lock.json` and `pom.xml` also carry
> registry information, so in those two ecosystems the baseline additionally fixes part of the
> registry configuration. This is a structural property of the ecosystems rather than a choice in
> the experiment design.

## 5. A finding that came out of all this: cache state is a hidden variable

The same registry configuration (A2 x B1a) gives three different outcomes in Maven depending only on
the CI operation:

- **C1a** (fresh install, cold cache) -> build fails
- **C1b** (update from an existing installation) -> succeeds, safely, `1.0.0` from the private repo
- **C1c** (rebuild with a lockfile generated under this configuration) -> phase 1 fails, skipped

This is the resolution-level version of "it works on my machine", and it is attributable to a **test
variable** (C1), not to an artefact. It also has a realistic reading: it models an organisation that
previously used a group repository with public access and later locked down to hosted-only. Under
that history the build keeps working. Worth a paragraph in the results chapter.

## 6. Final numbers after all fixes (this is the dataset I will analyse)

432 rows, 360 executable cells, 72 not expressible.

| classification | cells |
|---|---|
| `malicious_resolved` | **190** (52.8 % of 360) |
| `resolution_error` | 99 |
| `private_resolved` | 71 |
| `invalid_configuration` | 72 |

Per test variable, valid cells only:

| variable | level | n | malicious | rate |
|---|---|---|---|---|
| B2 | B2a pinned | 135 | **0** | **0.0 %** |
| B2 | B2b range | 135 | 116 | 85.9 % |
| B2 | B2c unspecified | 90 | 74 | 82.2 % |
| A | A1a public-first group | 96 | 58 | 60.4 % |
| A | A1b private-first group | 96 | 58 | 60.4 % |
| A | A2 hosted + separate proxy | 96 | 43 | 44.8 % |
| A | A3 hosted-only | 72 | 31 | 43.1 % |
| B1 | B1a single private URL | 96 | 33 | 34.4 % |
| B1 | B1b multi-registry, direct public | 96 | 60 | 62.5 % |
| B1 | B1c multi-registry, public via proxy | 72 | 45 | 62.5 % |
| B1 | B1d default | 96 | 52 | 54.2 % |
| C1 | C1a / C1b / C1c | 120 each | 66 / 58 / 66 | 55.0 / 48.3 / 55.0 % |

Note for myself: only the rates that are exactly **0** carry a claim. Everything between 0 and 100 is
an average over an unbalanced set of the other variables and must not be used to claim that one
variable causes the attack. The analysis unit is the configuration combination.

## 7. The rule that answers sub-RQ1 (tested on the final data)

> The attack succeeds **if and only if** both hold:
> 1. the version specifier is **not pinned** (B2b or B2c), **and**
> 2. the resolver **can reach a public source** — directly, through the Nexus proxy, or through a
>    group repository that has a public member.
>
> Condition 2 fails only when the package manager points at a single repository with no public
> upstream (B1a with A2 or A3). Two documented exceptions:
> - **Maven A3 x B1a still reaches Central**, because the `id=central` override does not apply there
>   and the super-POM's real Central leaks in (my design decision, 09.08).
> - **pip B1d x C1b** never reaches phase 2, which is the intended C1b behaviour (see point 4).

**Tested against all 360 executable cells of the final dataset: 0 misclassifications.**

Supporting numbers:
- Pinned cells: 135, of which **0** were attacked (66 safe, 69 build errors).
- Non-pinned cells: 225. Of these 30 failed to resolve anything, leaving 195 where the build produced
  a result — and **190 of those 195 (97.4 %)** got the attacker's package.
- `A1a` and `A1b` gave the **same outcome in all 96 comparable coordinates**, zero differences.
- Of the successful attacks, **150 of 380 package resolutions (39 %) were served by Nexus itself**
  (group or proxy), and 230 (61 %) came directly from the public registry.

Note the extra point in condition 2: when the resolver cannot reach a public source, the cell does
**not** simply become safe — usually the build fails. In npm and pip this is a fail-closed failure.
Maven A2 x B1a under C1b is the one place where it is genuinely safe, and only because of the cache
(see point 3).

## 8. Minimal-pair counts (how I isolate a single variable without statistics)

Counting cell pairs that are identical except in one variable and flip between "attacked" and "safe":

| ecosystem | flips from A | B1 | B2 | C1 |
|---|---|---|---|---|
| npm | 8 | 10 | 12 | 0 |
| PyPI | 0 | 0 | 54 | 0 |
| Maven | 3 | 3 | 30 | 0 |

For pip, **no single change of A, B1 or C1 ever turns an attacked cell into a safe one — only B2
does.** Maven's 3 + 3 come from the `mvn_A2_B1a_*_C1b` cache cells discussed in point 3, so they must
be read together with that explanation. npm's counts dropped after the C1b fix (34 -> 12 for B2)
because 11 cells moved from "safe" to "build error", which removes them from safe/attacked pairs.

- important links for drawing graph for result analysis: https://matplotlib.org/stable/gallery/images_contours_and_fields/image_annotated_heatmap.html

## Next steps
- [ ] Archive the corrected run 3 into `sub-RQ1_result/` as the final dataset.
- [ ] Report to supervisor: the findings above, the C1b baseline design decision, and the four open
      questions in `sub-RQ1_result/analysis/sub-RQ1_analysis_plan_for_supervisor.md`.
- [ ] Start the result analysis: Figure C (outcome map), then the rule test, then the cross-ecosystem
      comparison and the system-level aggregation.
- [ ] Amend the 07.09 point 4 entry: that validity check verified the **internal** packages' URLs,
      which are correct. It did not check the **public** dependencies, which is where the phase-1
      cache effect shows up.
- [ ] Write the methodology paragraph from point 4 and the C1 / cache finding from point 5.

# 10.09.2026

Today: audited the config generator scripts (the last part of the pipeline I had never
checked line by line), found two things worth documenting, wrote down how the "package update"
operation is realised in each of the three ecosystems, and built the first result figure.

## 1. Audited all five config generator scripts

Until now I had verified the **classification** path (classifier replay, evidence invariants) but
never read the scripts that turn the abstract test variables A, B1 and B2 into real config files.
Read all five in `automation_process/config_generator/`:
`generate_npmrc.py`, `generate_pipconf.py`, `generate_pom_xml.py`,
`generate_npm_version_specifier.py`, `generate_python_version_specifier.py`.

**Result: syntax and logic are correct.** Every invalid combination is guarded with `ValueError`,
and A, B1 and B2 are faithfully realised:

- **A** maps to the right Nexus repository names in all three ecosystems
  (`*-group-public-first`, `*-group-private-first`, `*-internal-hosted`).
- **B1a** = one private URL, **B1b** = private + real public, **B1c** = private + Nexus proxy,
  **B1d** = no config file written at all. Correct in all three.
- **B2** = npm `1.0.0` / `>=1.0.0 <2.0.0` / `*`; pip `==1.0.0` / `>=1.0.0,<2.0.0` / empty;
  Maven `1.0.0` / `[1.0.0,2.0.0)` and B2c correctly rejected.
- The invalid guards (A3 x B1c everywhere, B2c in Maven) produce exactly the 72 invalid cells.
- Public dependencies are pinned in all three services (`express`, `Flask==3.1.1`,
  `javalin 7.2.2` + `jackson 2.21.2`), so only the internal packages vary between cells.

## 2. Finding from the audit: for npm and pip, A2 and A3 are experimentally indistinguishable

Both A2 and A3 map to `*-internal-hosted`, so under **B1a, B1b and B1d the generated config file is
byte-identical** for the two. Only B1c separates them, and there A3 is invalid by definition.

Checked this against the results as well, not only in the code. Per ecosystem there are 36
coordinates where A2 and A3 can be compared:

| ecosystem | identical | different |
|---|---|---|
| npm | 27 | 9 (all B1c rows, where A3 is `invalid_configuration`) |
| pip | 27 | 9 (all B1c rows, where A3 is `invalid_configuration`) |
| Maven | 25 | 11 (the B1c rows **plus B1a rows**) |

So for npm and pip there is **not one coordinate where both A2 and A3 are valid and they differ**.

**This is not an error.** A2 and A3 differ only in whether a proxy repository *exists* in Nexus, and
a client that is never pointed at it cannot observe it. The correct reading is a finding in its own
right: *a proxy repository that the package manager is not configured to use has no effect on
resolution.* But it must be stated in the results chapter, otherwise a reader will wonder why the A2
and A3 rows look the same.

**Maven is the exception, and only because of my `id=central` decision (09.08).** Under A3 x B1a the
repository entry uses its own repository name as the ID, so the super-POM's real Maven Central is not
overridden and leaks in; under A2 x B1a the ID is `central` and it is overridden. That is why Maven
has 2 extra differing rows. Add this to the list of documented cross-ecosystem disagreements.

## 3. Second finding: `.npmrc` was never uploaded as an artifact

While checking a cell folder I noticed that **no npm cell directory contains `.npmrc`**, although it
is listed in the upload step of `service-ci-nodejs.yml`.

Cause: `actions/upload-artifact` v4.4+ **excludes hidden files by default** unless
`include-hidden-files: true` is set, and `.npmrc` starts with a dot. `pip.conf` and `pom.xml` are not
dotfiles, so they were uploaded normally.

**No effect on any result**: the classifier never reads `.npmrc`, and the resolved URLs in the
lockfiles prove the configuration was applied correctly. But it means I cannot show the generated
`.npmrc` of a specific cell afterwards. If I ever want that evidence in the appendix, the fix is one
line in the upload step. Not re-running anything for this.

## 4. Two small robustness notes in the generators (no effect on results, not fixed)

- `generate_npm_version_specifier.py` uses `if name in deps`, so if an internal package were missing
  from `package.json` the B2 specifier would be silently skipped instead of raising an error. Both
  packages are present, so this never happened. A `raise` would be safer.
- `generate_pipconf.py` hardcodes `trusted-host = host.docker.internal` while `nexus_url` is a
  parameter. Harmless for the experiment (the runner always uses that host), but the two values could
  drift apart in local development.

## 5. Correction to my own notes: Maven C1c **does** have a setup phase

I had written in a few places that C1a and C1c "have no setup phase". That is wrong for C1c.
Maven C1c has three phases: `generate` (produce the lockfile) -> `freeze` (pin every dependency into
`pom.lockfile.xml`) -> `generate` again against the frozen POM.

**The real difference is not whether there is a setup phase, but which configuration it runs under:**

- **C1b phase 1** uses `fixed_pom.xml`, a fixed file that carries its own `<repositories>` block
  pointing at the group repository. It can therefore pull packages the cell's own configuration could
  never reach.
- **C1c phase 1** uses **the cell's own `pom.xml`**. It can only reach what the cell's A x B1
  configuration can reach, so nothing foreign enters `~/.m2`.

Evidence for `mvn_A2_B1a_B2a_C1c` (log `..._mvn_lockfile_log.txt`):

```
[ERROR] Could not find artifact io.javalin:javalin:jar:7.2.2
        in central (http://host.docker.internal:8081/repository/maven-internal-hosted/)
[ERROR] Could not find artifact com.fasterxml.jackson.core:jackson-databind:jar:2.21.2
        in central (http://host.docker.internal:8081/repository/maven-internal-hosted/)
```

Phase 1 fails, no `lockfile.json` is produced, so the freeze and rebuild phases are skipped and the
cell is correctly `resolution_error`. The cell folder contains only the log and the pom, no lockfile,
which confirms the guard fired. The `~/.m2` cache is also wiped at the start of every Java cell
(`rm -rf $HOME/.m2/repository`), so phase 1 runs cold.

## 6. Overview: how "package update" (C1b) is realised in the three ecosystems

This belongs in the methodology chapter. The abstract idea is the same everywhere: **first put the
project into a fixed starting state (version 1.0.0 is already installed), then run the update using
the cell's own registry configuration.** But the three ecosystems have to realise it differently,
because their files and commands are different.

| | npm | pip | Maven |
|---|---|---|---|
| baseline file used in phase 1 | `npm-service-fixed-lock.json` | `fixed_pyproject.toml` | `fixed_pom.xml` |
| does phase 1 really resolve/install? | **no** - only a file copy | **yes** - real install into `./py_dependency` | **yes** - real resolve into `~/.m2` |
| can phase 1 fail? | **no** | yes | yes |
| does the baseline file also fix the registry? | **yes** (lockfile stores `resolved` URLs) | **no** - clean separation | **yes** (`<repositories>` is in the same file) |
| phase 2 command | `npm update <pkg1> <pkg2> --package-lock-only` | `pip install --dry-run --upgrade <pkg1> <pkg2>` | `mvn -U ...:generate` |
| can it update only the internal packages? | **yes** | **yes** | **no** - whole project only |
| are the public dependencies touched in phase 2? | no, entries are carried over unchanged | yes, re-resolved | yes, but usually served from the `~/.m2` cache |
| evidence file of phase 2 | `package-lock.json` | `<cell_id>_install-report.json` | `<cell_id>_lockfile.json` |

### The two consequences worth writing down

**(a) Only pip can fully separate "what to install" from "where to get it".**
I checked `fixed_pyproject.toml`: it contains **zero** registry information, so pip's "where" lives
entirely in the cell's own `pip.conf`. npm and Maven structurally cannot do this -
`package-lock.json` records `resolved` URLs and `pom.xml` declares `<repositories>` next to
`<dependencies>`. **This is a property of the ecosystems, not a choice in my design**, and it is
therefore a result and not only a limitation.

**(b) Maven has no per-package update command.**
There is no equivalent of `npm update <pkg>` or `pip install --upgrade <pkg>`. In Maven the version
lives in the POM, so "updating" means editing the POM, and `-U` only forces a project-wide re-check
of remote metadata. The third-party `versions-maven-plugin` could target single coordinates, but it
**rewrites the POM** and would replace the B2 version specifier I am testing, so it is unusable here.
Effect on the internal packages is equivalent across the three; the **scope** is not.

### Paragraph drafted for the methodology chapter

> The starting state for the package update operation is defined at the level of the resolved
> dependency state: version 1.0.0 is current. Each ecosystem establishes this state with its own
> native mechanism, because no single mechanism exists across all three. In npm the lockfile is
> itself the record of the resolved state, so a fixed `package-lock.json` is sufficient and no
> installation is required. In pip and Maven no such record exists, so the state is created by
> resolving a fixed dependency declaration, and the setup phase may fail if the cell's configuration
> cannot obtain that version. The registry configuration remains that of the experiment cell in all
> three cases, except that `package-lock.json` and `pom.xml` also carry registry information, so in
> those two ecosystems the baseline additionally fixes part of the registry configuration. This is a
> structural property of the ecosystems rather than a choice in the experiment design.

## 7. Built the first result figure (Figure C)

Wrote `sub-RQ1_result/analysis/figure_c_outcome_map.py`. It draws all 432 experiment cells on one
page: 3 panels (npm / Pip / Maven), rows = A x B1 (16), columns = B2 x C1 (9), colour = result, and a
letter (M / P / E / -) inside every cell so the figure is still readable in black-and-white print.

- Built with `imshow()`, following the official matplotlib example
  ["Annotated heatmap"](https://matplotlib.org/stable/gallery/images_contours_and_fields/image_annotated_heatmap.html),
  so the script is a small adaptation of a documented example rather than custom code.
- Outputs `figure_c_outcome_map.pdf` (vector, for Overleaf) and `.png` (for slides).
- The script **prints the result counts every time it runs** (432 / 190 / 71 / 99 / 72) and compares
  them with the expected values, so the figure can never silently drift away from the data.
- Also built the same figure in Excel first (`result_analysis_excel.xlsx`) as an independent check.
  Both agree.

Small thing that cost me time and is worth remembering: a Windows path written as a normal Python
string, `"sub-RQ1_result\0809\results.csv"`, is broken, because `\0` is a null character and `\r` is a
carriage return. The script now builds the path from `Path(__file__).resolve().parent`, which also
makes it independent of the folder you start it from.

## Next steps
- [ ] Continue the result analysis following the plan (see `docs/summary_result_analysis.md` for the
      current state and the day-by-day schedule).
- [ ] Write the A2/A3 observation from point 2 into the results chapter, and add the Maven A3 x B1a
      case to the cross-ecosystem disagreement list.
- [ ] Write the C1b overview table from point 6 into the methodology chapter.
- [ ] Decide whether the `.npmrc` upload gap from point 3 is worth fixing for the appendix.

# 10.09.2026 - part 2: result analysis day 3 (Step 6 and Step 7a)

day 2 was
Figure C, which I had already finished on 08.09 - so today I did **day 3: Step 6 (per-variable
table) and Step 7a (derive the rule and test it against every cell)**.

Everything below is written down in the order I actually did it. Each part is: the question I asked, the
code I wrote to check results and try to answer it, the output I got, and what that made me ask, or explore next.

Written into one new script: `sub-RQ1_result/analysis/step6_7_variable_table_and_rule.py`.
It follows the same conventions as `figure_c_outcome_map.py`: the path to `results.csv` is built from
`Path(__file__).resolve().parent` (a plain string `"...\0809\..."` would break, `\0` is a null
character), plain `csv.DictReader` instead of pandas, and the same `column_*` constants.
Input is the final dataset `sub-RQ1_result/0809/results.csv`.

---

## 1. Decisions taken before starting

- **Python script + Excel cross-check**, same as for Figure C. The script is written; the Excel
  cross-check (pivot table for the per-variable table, VLOOKUP for the A1a/A1b comparison) is
  **still open** and is carried to tomorrow.
- **Figure D is deliberately not built today.** The plan lists it as optional, and under the
  0 %/100 % rule (below) the intermediate bars carry no claim at all - so a bar chart would give a
  visual weight to numbers that are not allowed to be used as evidence. Decided to keep the table and
  decide about the figure later.
- **The 72 invalid cells are removed once, at the start** (`extract_valid_rows`), so no later count
  can accidentally include them. Every number in this entry is over the **360 executed cells**.

---

## 2. Step 6 - the per-variable table

`variable_table()` loops over the four test variables and calls `count_one_variable_option()` for
every option. That helper counts, inside one option, how many cells there are and how many ended as
`malicious_resolved` / `private_resolved` / `resolution_error`.

Output (also written to `sub-RQ1_result/analysis/step6_variable_table.csv`):

| variable | option | valid cells | malicious | private | error | malicious rate |
|---|---|---|---|---|---|---|
| A | A1a | 96 | 58 | 21 | 17 | 60.4 % |
| A | A1b | 96 | 58 | 21 | 17 | 60.4 % |
| A | A2 | 96 | 43 | 17 | 36 | 44.8 % |
| A | A3 | 72 | 31 | 12 | 29 | 43.1 % |
| B1 | B1a | 96 | 33 | 29 | 34 | 34.4 % |
| B1 | B1b | 96 | 60 | 24 | 12 | 62.5 % |
| B1 | B1c | 72 | 45 | 18 | 9 | 62.5 % |
| B1 | B1d | 96 | 52 | **0** | 44 | 54.2 % |
| B2 | B2a | 135 | **0** | 66 | 69 | **0.0 %** |
| B2 | B2b | 135 | 116 | 3 | 16 | 85.9 % |
| B2 | B2c | 90 | 74 | 2 | 14 | 82.2 % |
| C1 | C1a | 120 | 66 | 21 | 33 | 55.0 % |
| C1 | C1b | 120 | 58 | 29 | 33 | 48.3 % |
| C1 | C1c | 120 | 66 | 21 | 33 | 55.0 % |

**Built-in check:** inside one variable every valid cell is counted exactly once, so the malicious
column must always add up to 190. 

**What I am allowed to claim from this table - the 0 %/100 % rule.** The analysis unit is the
configuration *combination* and the variables interact, so a rate like "B1b = 62.5 %" is only an
average over an unbalanced set of values of the other variables. It cannot support "B1b causes the
attack". A marginal of exactly **0** or exactly **100** in a complete factorial is a different kind
of statement: it is universally quantified over the whole space, and no interaction can hide inside
it. So the table is **descriptive orientation only**, and exactly two entries carry a claim:

- **B2a = 0 maicious of 135.** Not "pinning helps on average" but: *in every one of the 135 pinned cells,
  across all three ecosystems and all A, B1 and C1 combinations, the dependency confusion attack never succeeded.*
- **B1d = 0 private.** Under the default configuration a cell has either result "malicious resolved"
  or result "resolution error" (the build breaks) - it never has result "private resolved". This is the fail-closed point in concrete form: blocking or
  not configuring public access does not defend the build, it breaks it.

Also to be stated once in the chapter: the options have **unequal n** (A3 = 72 not 96, B2c = 90 not 135
1)   because of the invalidity rules, so the rates are shares of *valid* cells and are not
comparable across options without that caveat. And **no significance testing** - this is an
exhaustive deterministic census of the defined space with verified run-to-run reproducibility, so
there is no sampling variability and chi-square / p-values / confidence intervals would be
meaningless.

---

## 3. Step 6, second result: A1a and A1b are identical in all 96 comparable cells

`compare_A1a_A1b()` uses the dictionary that `read_results()` already builds, keyed by
`(ecosystem, A, B1, B2, C1)`. For every valid A1a cell it rebuilds the same key with `"A1b"` and
compares the two classifications - so exactly one variable differs between the two cells of a pair.

```
A1a / A1b valid cells are compared  96  times
A1a / A1b cells have difference result:  0
```

**Why 96 and not 108:** there are 3 ecosystems x 4 B1 x 3 B2 x 3 C1 = 108 A1a cells, but 12 of them
are Maven x B2c, which is not expressible in a POM. 108 - 12 = 96, and the loop runs only over valid
rows. **Why the partner cell always exists:** the two invalidity rules are Maven x B2c and A3 x B1c,
and neither mentions A1a or A1b - so both cells of a pair are always valid together or invalid
together. I never compare a valid cell against an invalid one.

**Mechanism (need to verify and obtain evidence) (needed - a pattern without a mechanism is not a result):** a Nexus group repository **merges the version metadata of all
members**, and the package manager then picks the highest version. Member order therefore only
decides between members offering the *same* version. The attacker's 1.0.3 is strictly higher than
1.0.0 / 1.0.2, so it wins no matter which member is listed first. Evidence I can quote next to this:
the Maven log fetches one merged `maven-metadata.xml` from the group URL and then evaluates the
candidate `.pom` files. (not verified)

**Consequence:** "just put the private registry first in the group" is **not** a mitigation that works in all cases. This
also directly qualifies the "virtual repository-side" attack type from Gu et al. in section 5.3.1.

This result survives the objection against the table above, because it is **not an average**: it is
96 individual comparisons, each of which came out equal - a pointwise identity.

---

## 4. Step 7a - how I actually found the rule (question by question)

This is the part I have to be able to defend, so it is written as the sequence of questions I asked.

I started from investigating the meaningful entry in the per-variable table.


### Q1: pinning is *necessary* to defend dependency confusion attack - is it also *sufficient*? (is it enough?)

The per-variable table says: no B2a cell has result "malicious resolved" (the 135 B2a cells have
result "private resolved" in 66 cases and result "resolution error" in 69 cases - never "malicious
resolved"). The honest next question is the reverse direction:
**are all not-pinned cells (B2b, B2c) have result "malicious resolved" ?** if this question has answer "yes", then the rule would already be finished with one condition.

`check_not_pinned_cells()` counts the cells with `B2 != "B2a"`, splits them into cells with result
"malicious resolved" and cells with another result ("private resolved" or "resolution error"), and
returns the cells with another result for the next question.

output of this function:
```
number of not pinned valid cells (have B2b or B2c): 225
Number of not pinned valid cells with result malicious_resolved: 190
Number of cells which don't have result malicious_resolved result: 35
in these 35 cells,  5 has result private_resolved.  30 cells has result resolution_error
```

**Answer: no.** 190 of 225 cells have result "malicious_resolved", not 225 of 225. So a second condition should exist, those **35 cells should be keep checking

Two numbers worth keeping from this output:

- Of the 225 not-pinned cells, **30 has "resolution error" (failed to build)**, leaving **195 that produced a result** (either private resolved or malicious resolved), and
  **190 of those 195 = 97.4 %** has result "malicious_resolved". In plain words: *once you stop pinning,
  if your build still works, it has high probability to resolve the attacker's package.*
- The 35 split into **30 resolution_error + 5 private_resolved**. This **corrects a stale line in my
  analysis plan file**, which says "35 (31 errors + 4 private)". 

The private/error split matters on its own: most of the 35 cells without result "malicious resolved"
do not have result "private resolved" (defended), they have result "resolution error" (the build
fails). A cell with result "resolution error" can therefore not be regarded as a defended cell.

### Q2: what do those 35 cells have in common?

Idea: build the same per-variable table again, but only inside the 35 cells. `count_one_variable_option()`
takes any list of rows, so `group_cells_by_variable()` just points it at the 35 instead of at all 360.

Im looking for a uneven distribution, and try to find:
which variable options appear very often (e.g. B1a: 27 of 35), and
options that appear zero times (B1b, B1c).

A variable whose options are spread roughly evenly (C1: 9 / 17 / 9; B2: 19 / 16) implicit means it is not the cause.

output: 
```
   A A1a : 2      B1 B1a : 27      B2 B2a : 0       C1 C1a : 9
   A A1b : 2      B1 B1b : 0       B2 B2b : 19      C1 C1b : 17
   A A2  : 17     B1 B1c : 0       B2 B2c : 16      C1 C1c : 9
   A A3  : 14     B1 B1d : 8
```

from the output: in B1: **27 of 35 are B1a**, and **B1b and B1c contribute 0**, which is
consistent, because those two always have a public path. A is not evenly spread either (A2 = 17,
A3 = 14, but A1a and A1b only 2 each). B2a is 0 is normal because these 35 cells only has B2b or B2c. C1 is spread over all three options, so C1 is not likely the cause.

### Q3: is B1a alone the condition? No - so check the combination

This was the reasoning step where I could have gone wrong. "27 of the 35 are B1a" does **not** mean
"B1a leads to a result other than malicious resolved" - that is only one direction. The Step 6 table
says **33 of 96 B1a cells have result "malicious resolved"**, so B1a on its own clearly does not
protect anything. but it may be B1a **in combination**
with something else.

`group_cells_by_A_and_B1()` counts the 35 cells per (A, B1) combination, using a dictionary where the
**key** is the combination of A and B1, and the **value** is how often it occurs:

```
   A = A1a  B1 = B1d  cells: 2
   A = A1b  B1 = B1d  cells: 2
   A = A2   B1 = B1a  cells: 15
   A = A2   B1 = B1d  cells: 2
   A = A3   B1 = B1a  cells: 12
   A = A3   B1 = B1d  cells: 2
```

observation:

- **27 cells = B1a combined with A2 (15 cells) or A3 (12 cells).** B1a means one single registry URL is configured in package manager configuration file, pointing at the internal
  hosted repository. Since the attacker's 1.0.3 exists only
  on the public registry, so in these cells, the malicious package is **never even a candidate** to be resolved because package manager is not configured to reach public registry. That is a mechanism,
  not a correlation, and it becomes **condition 2: the package manager must be able to reach a public
  source**.
- **8 cells has B1d, spread 2 / 2 / 2 / 2 over all four A options.** it tells, A is
  irrelevant to the result, so this is not a private-registry-topology (variable A) effect, so it cannot belong to
  condition 2. This is Handled in Q5.

### Q4: does condition 2 hold in the other configuration combinations?
**condition 2 we just found: the package manager must be able to reach a public
  source**

Same trap as Q3, so I checked it explicitly: I had shown "27 of the 35 cells without result
malicious resolved are A2/A3 x B1a", but not the other direction: "**all** not-pinned A2/A3 x B1a
cells have a result other than malicious resolved (resolution error, or private resolved)". If some
A2/A3 x B1a cell has result "malicious resolved" after all, condition 2 has a hole. the function `check_combination()` counts, among **all** not-pinned
cells of each (A, B1) combination (combination 1: A2 x B1a, combination 2: A3 x B1a), how many has malicious result after all, and prints the cell ids.

```
A = A2  B1 = B1a : not pinned cells = 15 , cells which have result malicious_resolved = 0
A = A3  B1 = B1a : not pinned cells = 15 , cells which have result malicious_resolved = 3
      : mvn_A3_B1a_B2b_C1a
      : mvn_A3_B1a_B2b_C1b
      : mvn_A3_B1a_B2b_C1c
```

- **A2 x B1a: 0 of 15 have result "malicious resolved".** Condition 2 holds perfectly here.
- **A3 x B1a: 12 of 15** - three cells have results "malicious resolved", all Maven, all cell have B2b.

**These three are exception 1, and the mechanism to explained this is written in  09.08 entry:** under A3 x B1a
the repository entry uses `maven-internal-hosted` as its repository ID, so it does **not** override the
super-POM's `central`, and the real Maven Central leaks in as an additional repository. This is an interntional design. So these
cells do not contradict condition 2 - they *satisfy* it: the resolver could reach a public source
after all, even though the A and B1 labels suggest it could not. It must be written up as an
**implementation consequence of my own `id=central` design decision, not as an  Maven native
property**. Only B2b appears because Maven cannot express B2c at all (invalid combinations).

### Q5: the leftover cells

**What "leftover" means - follow the count:**

1. Q1: 35 not-pinned cells do **not** have result "malicious resolved". The rule "not pinned ->
   malicious resolved" is wrong (can not summerize all cells) for exactly these 35 cells, so all 35 have to be explained.
2. Q3: grouping the 35 by (A, B1) split them into two piles:
   - **27 cells** = A2/A3 x B1a -> explained by condition 2 (one single private registry URL, the
     attacker's package is unreachable).
   - **8 cells** = B1d -> **not** explained by condition 2, because B1d is the default
     configuration and *can* reach the public registry.
3. 35 - 27 = **8 cells still unexplained**. These are the "leftover" cells because we must explain it or to find out what happens
4. I had no theory for these 8 cells yet, so the only honest move was to look at them one by one and
   print their cell ids. That is all . Function `print_cells_of_B1_option(cells_not_malicious, "B1d")` does:
   out of the 35 cells, show me the ones with B1d.

The 8 cells were inside the 35 cells from Q1: they are the
`B1 B1d : 8` line in the Q2 output, and the 4 times `B1 = B1d cells: 2` lines in the Q3 output. Q5 only
show up their corresponding cell IDs.

`print_cells_of_B1_option()` prints them one by one:

```
    pip_A1a_B1d_B2b_C1b resolution_error      pip_A2_B1d_B2b_C1b resolution_error
    pip_A1a_B1d_B2c_C1b resolution_error      pip_A2_B1d_B2c_C1b resolution_error
    pip_A1b_B1d_B2b_C1b resolution_error      pip_A3_B1d_B2b_C1b resolution_error
    pip_A1b_B1d_B2c_C1b resolution_error      pip_A3_B1d_B2c_C1b resolution_error
```

All pip, all B1d, all C1b - **exception 2**, and it is section 0.5 of the analysis plan. In python C1b the
setup phase installs the fixed `1.0.0` using the cell's own `pip.conf`; under B1d that version is
unreachable (because 1.0.0 only exist in nexus repositories), so the setup fails and phase 2 never runs. **The cell never reached the operation under
test. (package update phase)** That is a property of my package update design, not a characteristic of pip - and the proof is that the same
coordinates come out `malicious_resolved` under C1a and C1c. It must be labelled as a
artefact associated with the thesis, otherwise it becomes a false ecosystem finding.

Reading the names is what gives the answer: every one of the 8 is `pip_..._B1d_..._C1b`. Same
ecosystem, same B1 option, same C1 option. Only A varies (A1a, A1b, A2, A3), so A is irrelevant to the result - which is exactly
what the even 2 / 2 / 2 / 2 spread in Q3 already implies.

**Why the whole chain Q1 -> Q5 is logical and not fitted to the data:**

> rule is wrong for 35 cells (Q1) -> condition 2 explains 27 of them (Q2, Q3) -> 8 cells remain (Q5) ->
> all 8 are one pattern -> we need exception 2.

Every one of the 35 cells is accounted for by exactly one explanation: condition 2 (27 cells) or
exception 2 (8 cells). And Q4 checked the *other* direction, so nothing is hiding outside the 35
either: the only not-pinned A2/A3 x B1a cells that have result "malicious resolved" are the 3 Maven
cells, which became exception 1. The test in section 5 over all 360 valid cells then confirms that
nothing was missed: 0 wrong.

---

## 5. The rule obtained, and the test against all 360 cells

> A dependency confusion attack succeeds **if and only if** both hold:
> 1. the version specifier is **not pinned** (configuration combinations contain B2b or B2c), **and**
> 2. the resolver **can reach a public source** - directly, through the Nexus proxy, or through a
>    group repository that has a proxy repository as member.
>
> Condition 2 fails only when the package manager points at a single private repository URL with no public
> repository access (B1a with A2 or A3). However, Two named exceptions:
> - **Maven cells which contain A3 x B1a still reaches Maven Central** (`id=central` override, an implementation consequence
>   of my design decision from 09.08, not an Maven native property);
> - **pip cells which contain B1d x C1b fails in phase 1 (setup phase) and never reaches phase 2 (package update)** 

The function `rule_about_malicious(row)` writes this as five `return` lines for one cell (condition 1,
exception 2, exception 1, condition 2, and the final "both conditions hold"). Each returns two values:
the answer (`True` = the rule says this cell has result `malicious_resolved`, `False` = the rule says
it has another result) and a short reason text saying which of the five lines handled the cell.
**The order of the blocks matters and is not arbitrary:** exception 1 must stand *before* condition 2,
because a Maven A3 x B1a cell matches both, and the exception is the more specific statement. Python
returns at the first match, so the more specific rule has to come first.

`test_rule()` asks the rule for every one of the 360 valid cells and compares its answer with the
real classification. It counts how many cells each of the five `return` lines handled (a dictionary
keyed by the reason text) and the four possible combinations of "what the rule says" x "what the cell
really has". Current output (updated 11.09, see that entry for why the output was extended):

```
What the rule predicts: only whether a cell has result malicious_resolved or not.
('not' means: private_resolved OR resolution_error - the rule does not separate these two)

how many cells each part of the rule handled:
    condition 1: version pinned : 135
    both conditions hold : 187
    condition 2: A2/A3 x B1a : 27
    exception 2: pip B1d x C1b : 8
    exception 1: mvn A3 x B1a : 3
    total: 360

rule says malicious_resolved, cell really has malicious_resolved : 190
rule says malicious_resolved, cell really has another result     : 0  (rule doesn't match real situation)
rule says another result,     cell really has malicious_resolved : 0  (rule doesn't match real situation)
rule says another result,     cell really has another result     : 170

cells tested: 360
cells which don't follow the rule: 0
```

135 + 187 + 27 + 8 + 3 = 360: every cell is handled by exactly one of the five lines. 190 + 170 = 360:
the rule is right on both sides, and the two zeros are the cells where the rule does not match the
real result.

It also writes `sub-RQ1_result/analysis/step7_rule_misclassifications.csv` (columns `cell_id`,
`classification`, `rule_about_malicious`, `reason`). That file now contains
**only its header row**, and that is exactly the result: it is the auditable form of "0 mistakes",
and anyone can re-run the script and get the same empty file. A rule is only accepted at 0 misconfiguration cases.

---

## 6. The academic aspect about this rule need to pay attention (must be in the thesis)

The rule was **derived from the same 360 valid cells it was tested on**. That is *not* independent
validation and must not be described as if it were. It is legitimate here only because those 360
valid cells are not a sample - they are the **complete population** of the defined configuration space, so
there is no held-out set to validate against and none is needed.



---

## 7. Smaller decisions made while writing the script


- Idea worth five minutes tomorrow: a second copy of the rule function **with the two exception
  blocks removed**, tested the same way. The number of cells it then gets wrong measures exactly what
  the two exceptions account for, which turns "I added two exceptions" into a measured statement.

---

## 8. Status after today

Finished: **Step 6** (per-variable table, B2a = 0 of 135, A1a = A1b in 96 of 96) and the Python half
of **Step 7a** (rule derived, tested, 0 wrong on 360 cells).
New files: `sub-RQ1_result/analysis/step6_7_variable_table_and_rule.py`,
`step6_variable_table.csv`, `step7_rule_misclassifications.csv` (contains only header, no misclassification rows).

## Next steps
- [ ] **Excel cross-check** of today's two results (still open): PivotTable of the per-variable table,
      and the A1a/A1b comparison via a `key = ecosystem & B1 & B2 & C1` helper column + VLOOKUP.
      Must give the same 14 rows and the same 0 differences out of 96. If Excel and Python disagree,
      the disagreement is the finding.
- [ ] **Step 7b** (schedule day 4): minimal-pair table + the write-up of the 5 non-pinned cells with
      result "private resolved" as a **positive control**. Today's data already staged it - those 5 cells resolved
      **1.0.2, not 1.0.0**, which proves "highest version wins" was fully active and the attack failed
      *only* because the attacker was unreachable.
- [ ] Fix the stale "31 errors + 4 private" line in the analysis plan file - it is **30 + 5**.
- [ ] Tick step 6 + 7a as done in `docs/summary_result_analysis.md` section 6.

# 11.09.2026

Re-read yesterday's rule derivation (10.09 part 2) with fresh eyes and asked three questions about
it: what exactly the rule predicts, why I looked at all 35 cells instead of only the 5 with result
"private_resolved" (the ones my supervisor asked about), and whether the whole chain of steps is
logical enough to defend. All three are answered below. Also improved the output of `test_rule()` so
it shows *what* was predicted instead of only "0 wrong".

## 1. Precisely: what does the rule predict?

The rule predicts a **two-way** outcome for every cell, not the three-way classification:

| the rule says | the cell's real result may be |
|---|---|
| "malicious_resolved" | `malicious_resolved` |
| "not malicious_resolved" | `private_resolved` **or** `resolution_error` |

It does **not** try to tell `private_resolved` and `resolution_error` apart. That is on purpose:
sub-RQ1 asks *under which configuration combinations the attack succeeds*, so the only thing the
rule has to decide is "attack succeeded or not". Whether a cell where the attack did not succeed
resolved the private package or broke the build is a separate question (the fail-closed point, and
the error taxonomy in step 4 of the plan). Yesterday's entry says "0 wrong" without stating this,
which can be misread as "the rule reproduces all three result categories". It does not. It
reproduces, for all 360 cells, whether the result is `malicious_resolved` or not.

New output of `test_rule()`, so this is visible instead of implied:

**(a) Which part of the rule handled how many cells.** Every cell goes through exactly one of the
five `return` lines in `rule_about_malicious()`:

```
condition 1  (pinned, B2a)         -> not malicious_resolved   135
condition 2  (A2/A3 x B1a)         -> not malicious_resolved    27
exception 2  (pip B1d x C1b)       -> not malicious_resolved     8
exception 1  (mvn A3 x B1a)        -> malicious_resolved          3
both conditions hold               -> malicious_resolved        187
                                                        total   360
```

135 + 27 + 8 + 3 + 187 = 360: every cell has exactly one reason. This is the line that shows the rule
is not "one condition plus a few tricks".

**(b) Rule against reality, four boxes:**

```
rule says malicious_resolved, cell really has malicious_resolved : 190
rule says malicious_resolved, cell really has another result     :   0   (rule doesn't match real situation)
rule says another result,     cell really has malicious_resolved :   0   (rule doesn't match real situation)
rule says another result,     cell really has another result     : 170
```

The two zeros are the "0 wrong" from yesterday. The 190 and 170 show the rule is right on both
sides, not only for the attack cases.

Implementation: `rule_about_malicious()` now returns two values, the answer (`True`/`False`) and a
short reason text; `test_rule()` counts the reasons in a dictionary and counts the four boxes. The
misclassification CSV gets the reason as a fourth column.

## 2. Why all 35 cells were examined, not only the 5 with result "private_resolved"

At Q1 (yesterday) the question was: *does "not pinned" always lead to result `malicious_resolved`?*
Every not-pinned cell that does **not** have that result is a counter-example to that question - and
that includes the 30 cells with result `resolution_error` just as much as the 5 with result
`private_resolved`. If I had only looked at the 5, the other 30 would have stayed unexplained and the
rule would still have been wrong for them. The rule has to reproduce all 360 cells, so all 35 had to
be looked at.

The 5 cells are a **different question**, and it is a good one. They sit inside the 27 cells of
A2/A3 x B1a, so the rule already explains *why the attacker's package did not arrive* - it was
unreachable. What the rule does **not** explain is why these 5 completed the build while the other 22
cells in the same A2/A3 x B1a pile ended with result `resolution_error`. That is what my supervisor
is asking, and it is step 7b of the plan (the next step).

## 3. The 5 cells - what happened in them (read from results.csv)

| cell | resolved version | from repository |
|---|---|---|
| `mvn_A2_B1a_B2b_C1b` | 1.0.2 | `maven-internal-hosted` |
| `npm_A2_B1a_B2b_C1b` | 1.0.2 | `npm-internal-hosted` |
| `npm_A2_B1a_B2c_C1b` | 1.0.2 | `npm-internal-hosted` |
| `npm_A3_B1a_B2b_C1b` | 1.0.2 | `npm-internal-hosted` |
| `npm_A3_B1a_B2c_C1b` | 1.0.2 | `npm-internal-hosted` |

Three things to notice, all readable from `results.csv`:

- **All five are C1b** (update an existing installation). The same configurations under C1a and C1c
  end with result `resolution_error`. So what made these five complete is the pipeline operation
  type, not the registry setup. (Why C1b can complete when C1a/C1c cannot differs per ecosystem and
  is written in the 08.09 entry: npm's `npm update <pkg>` touches only the two named packages and
  never re-resolves the public dependencies; Maven's public dependencies came from the `~/.m2` cache
  filled by the setup phase.)
- **They resolved 1.0.2, not 1.0.0.** The version was not pinned, so the package manager took the
  highest version it *could see* - and our own 1.0.2 was the highest, because the attacker's 1.0.3
  was not reachable. This proves that "highest version wins" was fully active in these cells. The
  attack failed *only* because the attacker was out of reach, not because the package manager
  behaved differently.
- **So they are a positive control for condition 2.** They show that "can reach a public source" is
  genuinely necessary for the attack, not just something that happens to go together with it.

For step 7b: a small function that filters `valid_rows` to `B2 != "B2a"` and
`classification == "private_resolved"` and prints `cell_id`, `pk1_version`, `pk1_url` produces
exactly this table.

## 4. Is the chain of steps logical and defensible? 

The chain, one sentence per step

1. Input is only `results.csv`. I removed the 72 cell with invalid configuration combination ( never executed), leaving 360 valid cells.
2. I counted results per variable option (the per-variable table). **one** entry is interesting :
   **no B2a cell has result `malicious_resolved` (0 of 135 cells).** Every other entry was a mix, and a
   mixed rate cannot be a condition, because the variables interact.
3. So pinning is *necessary* to avoid the attack. I then asked whether it is also *sufficient*: do
   all 225 not-pinned cells have result `malicious_resolved`? **No: 190 cells.** So a second condition
   should exist, and it is hidden in the 35 cells that do not have result "malicious_resolved".
4. I counted those 35 per variable option. **B1a: 27 of 35; B1b and B1c: 0.** B1 is involved.
5. But B1a alone cannot be the condition - 33 of 96 B1a cells *do* have result `malicious_resolved`. So I
   counted the 35 per (A, B1) pair: **27 are A2/A3 x B1a** - the configurations with only one private
   registry URL and no path to a public registry. The attacker's package cannot be a candidate there.
   That is condition 2, and it has a mechanism.
6. I checked condition 2 in the other direction: of all 30 not-pinned A2/A3 x B1a cells, do any have
   result `malicious_resolved`? **3 do, all Maven A3 x B1a, all B2b.** That is exception 1; its
   mechanism is my own `id=central` decision (09.08 entry).
7. **8 cells were left over** (35 - 27). Printing their cell ID show: all cells contain pip x B1d x C1b, their A options differs. I define it as
   exception 2 - the C1b setup phase in pip fails under B1d, so the tested operation never ran. A
   design effect, not a PyPI effect, proven by the same configurations having result
   `malicious_resolved` under C1a and C1c.
8. I wrote the rule as code and tested it against all 360 cells. **0 wrong**, and each cell is
   handled by exactly one branch (135 / 27 / 8 / 3 / 187).

Every step is a question caused by the previous answer, and every step is one filter or one count
over `results.csv` that a reader can repeat. Nothing jumps.

Two things to say honestly in the thesis (they are not weaknesses - they are what makes the argument
correct):

- **The cells of each exception were found from the data; the *explanation* of each exception comes
  from my implementation knowledge** (the POM repository-ID decision, the C1b design). That is normal:
  the data says *which* cells, the implementation says *why*. But it must be said clearly, so nobody
  thinks the mechanism was read out of `results.csv`.
- **The rule was found from these 360 cells and tested again on the same 360 cells.** That is not an
  independent test. It is acceptable here only because the 360 cells are the **complete**
  valid configuration space I defined - there is no other data to test on. So the rule should be called
  "a compact description that reproduces every executed cell", not "a validated model".

## Next steps
- [x] Finish the `test_rule()` output change (reasons + four boxes) and re-run: must print
      135 / 27 / 8 / 3 / 187 and 190 / 0 / 0 / 170. **Done and confirmed** - the full output is
      in the 10.09 part 2 entry, section 5. `main()` now runs all functions in derivation order
      (table, A1a/A1b, not-pinned question, grouping, both-direction check, leftovers, rule test).
- [ ] Step 7b: the function for the 5 cells (section 3), then the minimal-pair table.
- [ ] Excel cross-check of the per-variable table and the A1a/A1b comparison (still open from 10.09).
