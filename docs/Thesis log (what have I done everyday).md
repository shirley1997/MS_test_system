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