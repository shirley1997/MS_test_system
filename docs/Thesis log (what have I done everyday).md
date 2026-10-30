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
  - Reason: the Central Portal validates the deployment first, so the combinations can be checked before the permanent publication.
- Checked both combinations in the Central Portal and manually clicked **Publish**.
  - Result: both public version `1.0.3` packages were successfully published.

## Rebuilt and republished internal Nexus packages

- Design decision: internal and public packages must use the same `groupId` and `artifactId` for the DCA experiment; only their versions and repository locations differ.
- Changed the internal package combinations from `com.xueting.thesis` to:

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
- Problem it solves: Maven doesn't pin *exactly which artifact bytes* a build resolved anywhere by default, only the version string in `pom.xml`. Two builds of the same `pom.xml` can silently resolve different artifacts later (metadata drift, or — relevant to this thesis — a dependency confusion attack serving a different artifact under the same combination).
- Records the fully resolved dependency tree + SHA-256 checksums into `lockfile.json`.
- This plugin has 3 goals, verified plugin facts directly against source code (`GenerateLockFileMojo.java`, `FreezeDependencyMojo.java`, `ValidateMojo.java` on GitHub), 
  - `generate`: normal resolve (via project's configured repositories) + writes `lockfile.json`.
  - `validate`: **does not resolve from the lockfile.** Re-runs normal resolution again and compare checksums (computed from local `~/.m2` cache) against the stored lockfile. It's a drift/integrity check, not a "rebuild".
  - `freeze`: the goal that actually *uses* the lockfile's content — pure in-memory transform (no network calls), reads `lockfile.json` + `pom.xml`, writes `pom.lockfile.xml` with every dependency version hard-pinned. Running a real resolution command against that frozen POM is the actual "rebuild from lockfile" step, the true analog of `npm ci` / `pip install -r pylock.toml`.
- combinations (groupID + artifactID): `io.github.chains-project:maven-lockfile`. Pinned to **5.17.3** (verified as the GitHub-marked "Latest Release" stable version via the [GitHub Releases page](https://github.com/chains-project/maven-lockfile) and [Maven Central page of the plugin ](https://central.sonatype.com/artifact/io.github.chains-project/maven-lockfile/versions)

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
  - Checksums verify **integrity**, not **origin**. The attacker's `1.0.3` has a perfectly valid hash of itself. A hash proves the file was not altered in transit; it cannot tell me whether the combination was satisfied internally or externally. Only the resolved URL carries that.



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
- `A1a` and `A1b` gave the **same outcome in all 96 comparable combinations**, zero differences.
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
combinations where A2 and A3 can be compared:

| ecosystem | identical | different |
|---|---|---|
| npm | 27 | 9 (all B1c rows, where A3 is `invalid_configuration`) |
| pip | 27 | 9 (all B1c rows, where A3 is `invalid_configuration`) |
| Maven | 25 | 11 (the B1c rows **plus B1a rows**) |

So for npm and pip there is **not one combination where both A2 and A3 are valid and they differ**.

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
of remote metadata. The third-party `versions-maven-plugin` could target single combinations, but it
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
combinations come out `malicious_resolved` under C1a and C1c. It must be labelled as a
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

## part 2: Step 7b started - investigated the 5 not-pinned cells with result "private_resolved"

Afternoon. Started Step 7b (schedule day 4). Wrote the function that prints the 5 cells, then went
into the artifact files of two of them to find the **root cause** of why they resolved 1.0.2 - because
`results.csv` only shows *what* was resolved, not *how*. The important findings are in section 3.
the minimal-pair table is not started.

## 1. Decision: Figure D - yes, but as stacked counts, not as rates

Figure D is simple to build (one `ax.barh` panel from `step6_variable_table.csv`, same matplotlib
pattern as Figure C, ~1 hour). Decided to build it **later, after Step 7b**, and to build the
**stacked version** (per variable option: how many cells have result malicious_resolved /
private_resolved / resolution_error) instead of the "attack success rate" version from the plan.
Reason: the intermediate rates (60.4 %, 44.8 %, ...) carry no claim (0 %/100 % rule, 10.09 part 2
section 2), and a bar chart of rates would make them look like effects. The stacked version shows
the two things that *do* carry a claim: the B2a bar has no malicious_resolved part at all, and the
B1d bar has no private_resolved part at all.

## 2. New function `print_not_pinned_private_cells(valid_rows, results)`

Added to `step6_7_variable_table_and_rule.py`, called last in `main()`. It filters the 360 valid
cells to `B2 != "B2a"` and `classification == "private_resolved"` and prints, per cell: the resolved
version of both internal packages, the Nexus repository name taken out of `pk1_url` (the URL is cut
at `/repository/` and the next path segment is the name), and the classification of the **same A, B1,
B2 under C1a and under C1c** (looked up in the `results` dictionary from `read_results()`).
The first version printed the whole URL and was unreadable; rewritten with one labelled line per
fact and a short "how to read this" footer.

Output (5 cells):

| cell | resolved version | from Nexus repository | same config under C1a | same config under C1c |
|---|---|---|---|---|
| `mvn_A2_B1a_B2b_C1b` | 1.0.2 / 1.0.2 | `maven-internal-hosted` | resolution_error | resolution_error |
| `npm_A2_B1a_B2b_C1b` | 1.0.2 / 1.0.2 | `npm-internal-hosted` | resolution_error | resolution_error |
| `npm_A2_B1a_B2c_C1b` | 1.0.2 / 1.0.2 | `npm-internal-hosted` | resolution_error | resolution_error |
| `npm_A3_B1a_B2b_C1b` | 1.0.2 / 1.0.2 | `npm-internal-hosted` | resolution_error | resolution_error |
| `npm_A3_B1a_B2c_C1b` | 1.0.2 / 1.0.2 | `npm-internal-hosted` | resolution_error | resolution_error |

What this table shows: all 5 cells have C1b; the same configuration under C1a and C1c does not complete (resolution error).
They resolved 1.0.2 (higher version of internal packages), not 1.0.0 (what was installed before), from the
internal hosted repository. What it does **not** show is *why* - that needed the artifact files.

## 3. Root cause from the artifact files (the important part)

Looked at one npm cell and the Maven cell by hand - the other three npm cells are the same
configuration family. Folder: `sub-RQ1_result/0809/artifact_download/<cell_id>/`.

### 3.1 npm - `npm_A2_B1a_B2b_C1b`

- **`npm_A2_B1a_B2b_C1b_npm_log.txt` (87 bytes) contains no useful information.** Complete content:
  `up to date in 626ms` + the funding notice. npm prints nothing about which registry it asked or
  which versions it saw. (A re-run with `--loglevel verbose` would print one `http fetch GET 200
  <url>` line per request. Not re-running the experiment for this; if a trace is wanted, do a
  one-off manual reproduction of one cell and label it as a supplementary check, not as experiment
  data.)
- **The evidence is the lockfile pair.** `npm_A2_B1a_B2b_C1b_setup-package-lock.json` (phase 1,
  before the update) has both internal packages at **1.0.0**; `package-lock.json` (phase 2, after
  `npm update`) has both at **1.0.2** with `resolved` URLs in `npm-internal-hosted`.
- **Why 1.0.2 and not 1.0.0** cannot be read from the log; it comes from the documented behaviour
  of `npm update` with a range specifier (it installs the highest version that satisfies the range).
  Cite the npm documentation page for `npm update`, not an inference. The lockfile change
  1.0.0 -> 1.0.2 is the observation that matches the documented behaviour.
- **Why 1.0.3 was not chosen:** the only registry in this cell's configuration is
  `npm-internal-hosted`, which does not contain 1.0.3 
- Still to check (not done today): the `express` entry in both lockfiles should be byte-identical,
  which would show that `npm update <pkg1> <pkg2>` re-resolved only the two named packages and
  never touched the public dependencies. That is why the build completed under C1b although the
  public packages are unreachable from `npm-internal-hosted`. The C1a sibling log
  (`npm_A2_B1a_B2b_C1a_npm_log.txt`) should show which public package fails and against which URL.

### 3.2 Maven - `mvn_A2_B1a_B2b_C1b`

**Phase 1 (`_mvn_setup_log.txt`, 288 KB):** Maven first downloads the `.pom` of every dependency,
then the `.jar` files; every finished download gets a line `... (xx kB at xx kB/s)`. Only **1.0.0**
of both internal packages is downloaded - no 1.0.2, no 1.0.3 - which matches the pinned setup POM.
`_setup-lockfile.json` also records 1.0.0 for both.

**Phase 2 (`_mvn_log.txt`, 20 KB), lines 6-18 - the version selection made visible:**

```
Downloading from central: http://host.docker.internal:8081/repository/maven-internal-hosted/.../xueting-thesis-event-juhe/maven-metadata.xml
Downloaded  from central: ... maven-metadata.xml (364 B at 3.3 kB/s)
Downloading from central: http://host.docker.internal:8081/repository/maven-internal-hosted/.../xueting-thesis-event-juhe/1.0.2/xueting-thesis-event-juhe-1.0.2.pom
```

Maven downloads `maven-metadata.xml` (that file *is* the version list of the repository) and the
very next download is the **1.0.2** `.pom` - not 1.0.0, not 1.0.3. This two-line sequence is the
version computation: read the list, take the highest version inside the range `[1.0.0,2.0.0)`.
Maven does not print the computation itself (`mvn -X` would), but it is not needed: 1.0.3 cannot
appear because the list came from `maven-internal-hosted`, which does not contain it. Cite Maven's
version-range documentation for the "highest in range" rule.

**Proof that the public dependencies came from the local repository (`~/.m2`) in phase 2 - by
absence.** Maven logs *every* remote download, so counting is enough:

| | phase 1 (setup) log | phase 2 log |
|---|---|---|
| `Downloaded from ... javalin` lines | **3** (from `maven-group-public-first`, the repository hard-coded in the setup POM) | **0** |
| completed downloads from `repo.maven.apache.org` | - | **0** |
| completed downloads in total | many | **6**, all internal packages from `maven-internal-hosted` |

Nothing public was downloaded in phase 2, yet the build resolved `javalin` - so it came from the
local repository filled in phase 1. Together with the empty `resolved` field of the public
dependencies in `_lockfile.json` (08.09 entry, point 3) this is two independent pieces of evidence.
So yes, it is proven, and no extra logging option is needed.

### 3.3 The two "Maven Central" lines in phase 2 - explained, not a leak

Lines 131 and 133 of the phase-2 log looked like a contradiction of the A2 x B1a isolation:

```
[INFO] Downloading from central: https://repo.maven.apache.org/maven2/org/eclipse/jetty/tests/jetty-test-multipart/12.1.8/jetty-test-multipart-12.1.8.pom
[WARNING] The POM for org.eclipse.jetty.tests:jetty-test-multipart:jar:12.1.8 is missing, no dependency information available
[INFO] Downloading from central: https://repo.maven.apache.org/maven2/org/eclipse/jetty/tests/jetty-test-multipart/12.1.8/jetty-test-multipart-12.1.8.jar
```

Three observations:

1. Both are `Downloading` **without** a matching `Downloaded` line, followed by "POM ... is missing".
   The requests **failed**. 0 completed downloads from `repo.maven.apache.org` in the whole log.
2. The artifact is `jetty-test-multipart`, a transitive test artifact - not `javalin`, not
   `jackson`, not a project dependency. The surrounding `[WARNING] Artifact checksum ... not found
   in any configured remote repository` lines show this is the lockfile plugin's checksum lookup
   during `configurator:generate`, not the project's dependency resolution.
3. The URL is the real Maven Central although the label is `central` - the same label the project
   dependencies use for `host.docker.internal:8081`. So there are **two different "central"s**.

**Why two "central"s - verified with my own earlier effective-POM test.**
`effective-pom-checks/effective-A2-B1a.xml` (from the repository-ID investigation on 09.08) contains:

| list in the effective POM | id | URL |
|---|---|---|
| `<repositories>` | `central` | `http://host.docker.internal:8081/repository/maven-internal-hosted/` |
| `<pluginRepositories>` | `central` | `https://repo.maven.apache.org/maven2` |

Maven's built-in super POM defines **two** lists, both with `id = central`: `<repositories>` for
dependencies and `<pluginRepositories>` for plugins and what plugins need. My `<repository>
<id>central</id>` override in the cell's `pom.xml` replaces only the entry in the first list (same id
-> same entry replaced). The second list is inherited unchanged, so plugin-side resolution still
knows the real Central. I never configure a `<pluginRepositories>` block in pom.xml file - it is there because every
project inherits it (from SuperPOM). Reference to cite: the super-POM page of the Maven model builder documentation
(`maven.apache.org/ref/3.9.x/maven-model-builder/super-pom.html`).

Note on what is proven and what is not: the effective POM proves the second list exists in this
cell; it does not prove that lines 131/133 went through it (only `mvn -X` would show that). It is
the obvious path and I will write it as such.

**Consequences:**
- No result is affected: the requests failed, the artifact is not a project dependency, and no
  project dependency was fetched from Central in phase 2.
- The isolation claim for A2 x B1a becomes sharper: the *dependency* candidate set was strictly
  `maven-internal-hosted` - which is why 1.0.3 was never a candidate - while the plugin path is not
  part of the dependency resolution the attack targets.
- This is the second half of the 09.08 `id=central` story and belongs next to it in the
  implementation chapter (the override is per repository list, not global). Limitation note for
  section 7.4, not a finding.

## 4. What the three claims for the 5 cells rest on now

| claim | Maven evidence | npm evidence |
|---|---|---|
| the candidate set contained no 1.0.3 | phase-2 log: metadata and all downloads from `maven-internal-hosted` only | lockfile `resolved` URLs: `npm-internal-hosted` only |
| the resolver chose the highest version it could see | metadata-then-`1.0.2.pom` sequence in the phase-2 log + Maven version-range docs | lockfile change 1.0.0 -> 1.0.2 + npm `update` docs (no log trace) |
| the build completed only because the public dependencies did not need to be resolved | 3 `javalin` downloads in phase 1, 0 in phase 2; empty `resolved` in `_lockfile.json` | **still to check**: `express` entry identical in both lockfiles |

## Next steps
- [ ] npm: compare the `express` entry in `_setup-package-lock.json` and `package-lock.json` of
      `npm_A2_B1a_B2b_C1b`; read the C1a sibling log. Then the npm row of the table above is complete.
- [ ] Put the two lockfile comparisons into a small separate script
      (`step7b_five_cells_evidence.py`) so they are reproducible; keep the log excerpts as quotes
      with file name and line number. Do not script the log reading.
- [ ] Look up and cite: npm `update` range behaviour; Maven version-range selection; Maven super POM.
- [ ] Minimal-pair table (the rest of Step 7b).
- [ ] Figure D, stacked version (section 1).
- [ ] Excel cross-check of the per-variable table and the A1a/A1b comparison (still open).

# 14.09.2026 - sub-RQ1 result analysis: find root cause of the 5 not-pinned "private_resolved" cells (evidence from the artifact files), build minimal-pair table

Finished the open items of Step 7b from 11.09: read the npm and Maven artifact
files of the 5 not-pinned cells with result `private_resolved`, made the lockfile comparisons
reproducible in script `step7b_five_cells_evidence.py`, collected the documentation that supports each
claim, found out what an empty `resolved` field in the Maven lockfile *really* means (it corrects my
earlier reading), and built the minimal-pair table in `step7b_minimal_pairs_table.py`.


---

## 1. (Maven cells) why does `maven-metadata.xml` only appear in the phase-2 log? (variable: C1b)

I searched both Maven console logs of `mvn_A2_B1a_B2b_C1b` for `maven-metadata.xml`. It appears **only in
phase 2**

- **Phase 1** (setup, initial install) uses the fixed POM with the version **pinned to 1.0.0**. Maven already knows the
  exact version, so it asks directly for `.../1.0.0/xueting-thesis-event-juhe-1.0.0.pom`. It never
  needs to find out which versions exist.
- **Phase 2** (package update) uses the cell's own POM with the **version range `[1.0.0,2.0.0)`**. Now Maven
  has to find out which versions exist before it can choose one. That list is `maven-metadata.xml`.
  It downloads the list, then the version it chose: 1.0.2. (because the own POM configured repository "maven-internal-hosted")

So the metadata download is the **fingerprint of range resolution**: it only appears when the
version is not pinned, and *where it was downloaded from* tells me the versions Maven found. Here it came
from `maven-internal-hosted` only - a repository that does not contain attacker package version 1.0.3.

**Can the metadata line replace the `~/.m2` evidence? No** - the two answer different questions:

| question | evidence |
|---|---|
| why 1.0.2 was chosen (not 1.0.0, not 1.0.3) | metadata downloaded from `maven-internal-hosted`, followed by the `1.0.2.pom` download |
| why the build completed at all, although `javalin` / `jackson` do not exist in `maven-internal-hosted` | `javalin` downloaded in phase 1, **nothing** downloaded for it in phase 2 -> it came from the local repository `~/.m2`, which javalin is stored there in phase 1 |

The metadata explains the *version*. The `~/.m2` evidence explains why the build succeeded instead of "resolution error". Both are evidence.

---

## 2. npm - `npm_A2_B1a_B2b_C1b` (representative for the 4 npm not-pinned cells with "private resolved")

 Files:
`npm_A2_B1a_B2b_C1b_npm_log.txt` , `npm_A2_B1a_B2b_C1b_setup-package-lock.json`
(phase 1 = before the update), `package-lock.json` (phase 2 = after `npm update`).

### 2.1 The log has no useful information

Complete content of the log:

```
up to date in 626ms

25 packages are looking for funding
  run `npm fund` for details
```

npm prints nothing about which registry it asked or which versions it saw. The reason is in the npm
documentation (section 4): with `--package-lock-only`, `npm update` only rewrites
`package-lock.json` and does not download anything. A re-run with `--loglevel verbose` would print
one `http fetch GET 200 <url>` line per request - **not re-running the experiment for this**. If a
trace is ever wanted, do a one-off manual reproduction of one cell and label it as a supplementary
check, not as experiment data.

### 2.2 observe and compare Lockfile from 2 phases manually

In `_setup-package-lock.json` (phase 1):

```
"node_modules/express": {
  "version": "5.2.1",
  "resolved": "https://registry.npmjs.org/express/-/express-5.2.1.tgz",

"node_modules/xueting-thesis-event-jianding": {
  "version": "1.0.0",
  "resolved": "http://localhost:8081/repository/npm-group-public-first/xueting-thesis-event-jianding/-/xueting-thesis-event-jianding-1.0.0.tgz",
```

In `package-lock.json` (phase 2):

```
"node_modules/express": {
  "version": "5.2.1",
  "resolved": "https://registry.npmjs.org/express/-/express-5.2.1.tgz",


"node_modules/xueting-thesis-event-jianding": {
  "version": "1.0.2",
  "resolved": "http://host.docker.internal:8081/repository/npm-internal-hosted/xueting-thesis-event-jianding/-/xueting-thesis-event-jianding-1.0.2.tgz",
```

The internal package was updated (1.0.0 -> 1.0.2, now from `npm-internal-hosted`); the public dependency `express` has
exactly the same URL as in phase 1 (does not change).

### 2.3 The C1a sibling log - why C1a fails but C1b completes (with result "private_resolved")

`npm_A2_B1a_B2b_C1a/npm_A2_B1a_B2b_C1a_npm_log.txt` :

```
...
npm error 404 Not Found - GET http://host.docker.internal:8081/repository/npm-internal-hosted/express - Package 'express' not found
npm error 404
npm error 404  The requested resource 'express@^5.2.1' could not be found or you do not have permission to access it.
...
```

No lockfile is uploaded for this cell because the phase 1 failed, so this cell has result`resolution_error`.

**My explanation (should be writtn as argument in thesis):** C1a is an initial install - to build
successfully, *every* package listed in `package.json` must be resolved, and public dependency `express` does not
exist in `npm-internal-hosted`, so the build fails with 404. 

C1b (package update) in npm targets only the two
internal packages (`npm update <pkg1> <pkg2>`), so the
update succeeds without touching the public dependencies. The `express` entry is the same in both lockfiles ( before and after)  -> evidence

### 2.4 Reproducible: `compare_npm_lockfiles()` in `step7b_five_cells_evidence.py`

Opens both lockfiles with `json.load`, reads the `"packages"` section (every installed package,
keyed by its path under `node_modules/`), and prints package `version` and `resolved` before and after for
the packages I name. `before == after` compares the both entries, if they are identical then print "unchanged"

Output:

```
[cell]: npm_A2_B1a_B2b_C1b
[dependency name]:    xueting-thesis-event-jianding
        phase 1 (before update): 1.0.0 http://localhost:8081/repository/npm-group-public-first/xueting-thesis-event-jianding/-/xueting-thesis-event-jianding-1.0.0.tgz
        phase 2 (after update):  1.0.2 http://host.docker.internal:8081/repository/npm-internal-hosted/xueting-thesis-event-jianding/-/xueting-thesis-event-jianding-1.0.2.tgz
-> entry (package version / resolved URL) CHANGED
[dependency name]:    xueting-thesis-service-fasong
        phase 1 (before update): 1.0.0 http://localhost:8081/repository/npm-group-public-first/xueting-thesis-service-fasong/-/xueting-thesis-service-fasong-1.0.0.tgz
        phase 2 (after update):  1.0.2 http://host.docker.internal:8081/repository/npm-internal-hosted/xueting-thesis-service-fasong/-/xueting-thesis-service-fasong-1.0.2.tgz
-> entry (package version / resolved URL) CHANGED
[dependency name]:    express
        phase 1 (before update): 5.2.1 https://registry.npmjs.org/express/-/express-5.2.1.tgz
        phase 2 (after update):  5.2.1 https://registry.npmjs.org/express/-/express-5.2.1.tgz
-> entry (package version / resolved URL) not change
```

TODO: check for the other 3 npm cells (not-pinned, have result "private_resolved") too

### 2.5 question 2: why is `express` in the fixed lockfile from `registry.npmjs.org` and not from the group repository?

Checked the fixed file itself, `fixed_setup_file/npm-service-fixed-lock.json`: **all public dependencies
entries** point to `registry.npmjs.org`; **only the 2 internal packages** point to
`localhost:8081/repository/npm-group-public-first`. So it is not only `express`.

Most likely explanation - the same mechanism I just observed: npm keeps the existing `resolved`
URL of every entry it does not re-resolve. If the fixed lockfile was built in two steps (first the
public dependencies installed with an ordinary `npm install` against npmjs.org, then the internal
packages added later with `.npmrc` pointing at the group), only the two entries added in the second
step got group URLs. The log does not record how the fixed file was created, so this stays "most
likely" unless command `git log -- fixed_setup_file/npm-service-fixed-lock.json` is used to check it.


---

## 3. Maven - `mvn_A2_B1a_B2b_C1b`

Folder: `sub-RQ1_result/0809/artifact_download/mvn_A2_B1a_B2b_C1b/`.Checked Files:
`_mvn_setup_log.txt` (phase 1, 288 KB), `_mvn_log.txt` (phase 2, 20 KB), `_setup-lockfile.json`,
`_lockfile.json`

### 3.1 What I saw in the phase-1 log

Maven first downloads the `.pom` of every dependency, then, after that is finished, the `.jar`
files. After each finished download it writes `(xxx kB at xxx kB/s)` - the size and the download
speed. Only **1.0.0** of both internal packages is downloaded, which matches
the pinned package version setup in fixed POM file. `_setup-lockfile.json` also records 1.0.0 for both.

### 3.2 What I saw in the phase-2 log

less dependencies are downloaded: only lines 6-18 are download lines, and they find the internal packages
with version 1.0.2:

```
[INFO] Downloading from central: http://host.docker.internal:8081/repository/maven-internal-hosted/io/github/shirley1997/thesis/xueting-thesis-event-juhe/maven-metadata.xml
[INFO] Downloaded from central:  http://host.docker.internal:8081/repository/maven-internal-hosted/io/github/shirley1997/thesis/xueting-thesis-event-juhe/maven-metadata.xml (364 B at 3.3 kB/s)
[INFO] Downloading from central: http://host.docker.internal:8081/repository/maven-internal-hosted/io/github/shirley1997/thesis/xueting-thesis-event-juhe/1.0.2/xueting-thesis-event-juhe-1.0.2.pom
```

Maven does not print the version computation itself (`mvn -X` would). It is not needed: the
metadata (= the version list) came from `maven-internal-hosted`, the next download is 1.0.2 - that
*is* the selection, and 1.0.3 cannot appear because the list does not contain it. The rule "highest
version inside the range" is documented (section 4).

Every completed download in the phase-2 log, counted: **6**, all internal packages from
`maven-internal-hosted`. Completed downloads from `repo.maven.apache.org`: **0**.



Phase-2 log (`_mvn_log.txt`):  Not one line mentions `javalin`.

Maven prints a `Downloaded from` line for every file it fetches from a remote repository. Phase 1
fetched `javalin`; phase 2 fetched nothing for it - but the build is successful. The only place it can
have come from is the local repository `~/.m2`, filled by phase 1. Quote lines 12 and 156 with their
line numbers in the thesis.

### 3.4 Reproducible: `compare_maven_lockfiles()` in `step7b_five_cells_evidence.py`

The Maven lockfile is JSON with a `"dependencies"` list; each entry has `artifactId`, `version`,
`repositoryId`, `resolved`. Output:

```
[cell]: mvn_A2_B1a_B2b_C1b - phase 1 (setup phase, initial install)
[dependency name]:    jackson-databind  [version]: 2.21.2  [resolved]: http://host.docker.internal:8081/repository/maven-group-public-first/com/fasterxml/jackson/core/jackson-databind/2.21.2/jackson-databind-2.21.2.jar
[dependency name]:    xueting-thesis-event-juhe  [version]: 1.0.0  [resolved]: http://host.docker.internal:8081/repository/maven-group-public-first/io/github/shirley1997/thesis/xueting-thesis-event-juhe/1.0.0/xueting-thesis-event-juhe-1.0.0.jar
[dependency name]:    xueting-thesis-result-fanhui  [version]: 1.0.0  [resolved]: http://host.docker.internal:8081/repository/maven-group-public-first/io/github/shirley1997/thesis/xueting-thesis-result-fanhui/1.0.0/xueting-thesis-result-fanhui-1.0.0.jar
[dependency name]:    javalin  [version]: 7.2.2  [resolved]: http://host.docker.internal:8081/repository/maven-group-public-first/io/javalin/javalin/7.2.2/javalin-7.2.2.jar

[cell]: mvn_A2_B1a_B2b_C1b - phase 2 (package update)
[dependency name]:    jackson-databind  [version]: 2.21.2  [resolved]: (this field is empty - which means it's not downloaded from a remote repository)
[dependency name]:    xueting-thesis-event-juhe  [version]: 1.0.2  [resolved]: http://host.docker.internal:8081/repository/maven-internal-hosted/io/github/shirley1997/thesis/xueting-thesis-event-juhe/1.0.2/xueting-thesis-event-juhe-1.0.2.jar
[dependency name]:    xueting-thesis-result-fanhui  [version]: 1.0.2  [resolved]: http://host.docker.internal:8081/repository/maven-internal-hosted/io/github/shirley1997/thesis/xueting-thesis-result-fanhui/1.0.2/xueting-thesis-result-fanhui-1.0.2.jar
[dependency name]:    javalin  [version]: 7.2.2  [resolved]: (this field is empty - which means it's not downloaded from a remote repository)
```

All 4 are the direct dependencies declared in `pom.xml`. Phase 1: all 4 from
`maven-group-public-first`. Phase 2: the 2 internal packages at 1.0.2 from `maven-internal-hosted`;
the 2 public dependencies have an **empty** `resolved` (and empty `repositoryId`).

**The text in parentheses in this output is my interpretation and it turned out to be imprecise -
see section 5.** The script text must be changed.

---

## 4. official documentation that supports the claims 

### 4.1 npm `update` - highest version inside the range; only the named packages

Source: npm docs, `npm update` (CLI v11) - https://docs.npmjs.com/cli/v11/commands/npm-update

> "This command will update all the packages listed to the latest version (specified by the `tag`
> config), respecting the semver constraints of both your package and its dependencies (if they
> also require the same package)."

> "If no package name is specified, all packages in the specified location (global or local) will
> be updated."



> "So the highest-sorting version that satisfies `~1.1.1` is used, which is `1.1.2`."

For the flag I use, npm docs, config -> `package-lock-only` -
https://docs.npmjs.com/cli/v11/using-npm/config#package-lock-only

> "If set to true, the current operation will only use the `package-lock.json`, ignoring
> `node_modules`. For `update` this means only the `package-lock.json` will be updated, instead of
> checking `node_modules` and downloading dependencies."

This last sentence is also why the npm log is empty and why nothing was downloaded.

### 4.2 Maven - highest version inside a range

Source: Maven POM Reference, "Dependency Version Requirement Specification" -
https://maven.apache.org/pom.html#dependency-version-requirement-specification

> "[1.0,2.0): 1.0 <= x < 2.0; Hard requirement for any version between 1.0 inclusive and 2.0
> exclusive."

> "Maven picks the highest version of each project that satisfies all the hard requirements of the
> dependencies on that project."

### 4.3 Maven - the super POM has two lists, both with id `central`

Maven superPOM has repositores and PluginRepositories blocks, i didn't setup (override) PluginRepositories block because it is not research-relevant, so PluginRepositories can access Maven central

Source: Maven Model Builder, Super POM (3.9.9) -
https://maven.apache.org/ref/3.9.9/maven-model-builder/super-pom.html

> "All models implicitly inherit from a super-POM:"

followed by both blocks: `<repositories><repository><id>central</id> ...
<url>https://repo.maven.apache.org/maven2</url>` and `<pluginRepositories><pluginRepository>
<id>central</id> ... <url>https://repo.maven.apache.org/maven2</url>`. Exactly what my own
`effective-pom-checks/effective-A2-B1a.xml` shows after the override: the first list replaced by
Nexus, the second untouched (11.09 part 2, section 3.3).

### 4.4 Maven - the local repository has precedence than remote repostory 



Source: Maven, Introduction to Repositories -
https://maven.apache.org/guides/introduction/introduction-to-repositories.html

Under "Artifact Repositories":

> "the **local** repository is a directory on the computer where Maven runs. It caches remote
> downloads and contains temporary build artifacts that you have not yet released."

Under "Downloading from a Remote Repository":

> "Downloading in Maven is triggered by a project declaring a dependency that is not present in the
> local repository (or for a `SNAPSHOT`, when the remote repository contains one that is newer)."

The second sentence is the answer.  it says a
download is *triggered by absence* in the local repository 

### 4.5 maven-lockfile plugin - what `resolved` field means (see section 5 for why this matters)

Source: chains-project/maven-lockfile README -
https://github.com/chains-project/maven-lockfile/blob/main/README.md

> "In case the artifact url cannot be resolved or the checksum cannot be calculated or downloaded
> (depending on `checksumMode`) an **empty string** will be recorded in the respective `resolved` or
> `checksum` field."

Source code: `RemoteChecksumCalculator.java` -
https://github.com/chains-project/maven-lockfile/blob/main/src/main/java/io/github/chains_project/maven_lockfile/checksum/RemoteChecksumCalculator.java
(read on the `main` branch, v5.18.x; my build used version **5.17.3** - the warning text matches my log, but cite the `v5.17.3` tag of the repository, not `main`).

---

## 5. Correction: what an empty `resolved` in the Maven lockfile REALLY means

My reading so far (08.09 entry, 11.09 part 2 section 3.2, and the text in my script) was: "empty
`resolved` = the artifact was not downloaded from a remote repository, it came from `~/.m2`". The
README says something more specific - "cannot be resolved" - so I read the plugin source.

**How the plugin fills `resolved`** (from `RemoteChecksumCalculator.java`, the mode my build uses -
the warning `Artifact resolved url ... not found.` in my log is line 265 of that file):

```java
for (ArtifactRepository repository : buildingRequest.getRemoteRepositories()) {
    String url = repository.getUrl().replaceAll("/$", "") + "/" + groupId + "/" + artifactId + "/"
            + baseVersion + "/" + filename;
    ...
    HttpRequest request = ... .method("HEAD", HttpRequest.BodyPublishers.noBody()) ...
    HttpResponse<Void> response = httpClient.send(request, ...);

    if (response.statusCode() >= 200 && response.statusCode() < 300) {
        RepositoryInformation result =
                new RepositoryInformation(ResolvedUrl.of(url), RepositoryId.of(repository.getId()));
        return Optional.of(result);
    }
}
PluginLogManager.getLog().warn(String.format("Artifact resolved url `%s` not found.", artifact));
resolvedCache.put(cacheKey, RepositoryInformation.Unresolved());
```

In words: **the plugin computes `resolved` itself, independently of what Maven downloaded.** For
every repository configured in the POM, in order, it sends an HTTP **HEAD** request for the
artifact file. The first repository that answers 2xx becomes `resolved` / `repositoryId`. If none
does, the field stays empty and the warning is printed. My phase-2 log contains exactly those
warnings (70 of them in total, among them):

```
[WARNING] Artifact resolved url `com.fasterxml.jackson.core:jackson-databind:jar:2.21.2:compile` not found.
[WARNING] Artifact resolved url `io.javalin:javalin:jar:7.2.2:compile` not found.
```

**Correct explanation of the empty field:** *the plugin asked every configured remote repository - in
A2 x B1a that is only `maven-internal-hosted` - and the public dependencies dont exists in this repository.* That is
not the same as "it was not downloaded". But it is the also a statement for my argument: the
lockfile itself proves that `javalin` and `jackson-databind` were **unreachable** from this cell's
configuration - and the build succeeded anyway. The proof that they came from `~/.m2` is the
*log* (no `Downloaded` line in phase 2, lines 12/156 in phase 1, section 3.3), and the maven official documentation, and the lockfile
proves there was nowhere else they could have come from.

**Consequences:**

- **Change the text in `compare_maven_lockfiles()`** from "not downloaded from a remote repository"
  to: *"(empty - the lockfile plugin does not found this dependency in specified repository which is configured in
  the POM.xml)"*. The same sentence in 11.09 part 2 section 3.2 is superseded by this section.
- **Note for the methodology chapter:** for Maven, the `resolved` URL my classifier reads is the
  plugin's own HEAD-check result over the configured repositories, *not* Maven's download record.
  In this cell both agree (Maven's log and the lockfile both say `maven-internal-hosted` for the
  internal packages).
- **check to add to the open items:** across all Maven `malicious_resolved` cells, does the
  repository in Maven's `Downloaded from` line for the internal packages match the lockfile's
  `resolved`? If yes everywhere, the classifier's evidence is confirmed by a second, independent
  source; if not somewhere, that is important.
- This also explains the two `repo.maven.apache.org` lines (131/133) from 11.09 part 2 section 3.3
  from the plugin side: `getPluginResolvedField()` uses the *plugin* building request, i.e. the
  `<pluginRepositories>` list, which still points at the real Central.

**The complete Maven chain for the 5-cell case, with a citation at every step:**

1. Phase 1 downloaded `javalin` from the group repository -> cached in the local repository
   ("It caches remote downloads", 4.4).
2. Phase 2 the cell's own pom.xml declares `javalin` , and it *is* already present locally -> no download is triggered
   ("triggered by a project declaring a dependency that is not present in the local repository",
   4.4) -> matches the 0 `Downloaded` lines (3.3).
3. The lockfile plugin's HEAD check finds `javalin` in none of the configured remote repositories
   -> empty `resolved` field (plugin source, 4.5) -> proves it was unreachable *remotely* in this cell.
4. The build succeeded (private_resolved), without resolution error -> the only possible repository to obtain public dependencies is the local repository (.m2).

---

## 6. The three claims for the 5 cells - what each rests on now

| claim | Maven evidence | npm evidence |
|---|---|---|
| no 1.0.3 in the package candidate set | metadata and all 6 downloads from `maven-internal-hosted` (log); `resolved` URLs (lockfile) | `resolved` URLs `npm-internal-hosted` (lockfile) |
| the highest visible version was chosen | metadata -> `1.0.2.pom` sequence (log lines 6-18) + Maven docs (4.2) | 1.0.0 -> 1.0.2 in the lockfile pair + npm `update` docs (4.1); no log trace exists |
| the build completed only because the public dependencies were not re-resolved | `javalin`: downloaded in phase 1 (lines 12, 156), nothing in phase 2 (log); empty `resolved` = unreachable from the configured repository (lockfile, 4.5); local-first rule (4.4) | `express` entry byte-identical before/after; C1a sibling fails with `E404 express`; `--package-lock-only` docs (4.1) |

---

## 7. The minimal-pair table (`step7b_minimal_pairs_table.py`)

### 7.1 Why is meaningful to build it

The per-variable table only gives me averages like
"B1a: 34 %" . it cannot tell me whether variable B1a *itself* does anything. The rule found tells me *which
combinations* are vulnerable, but not how much each single variable contributes. So I needed a way
to isolate one variable at a time. Because the experiment is a complete, deterministic factorial, I can take every pair of cells that differ in **exactly one
variable option** and simply count how often that one change flips the result. Everything else (variable option) in the
pair is the same, so the result flip is caused by that variable alone.

I split the flips into three types:

| flip | meaning |
|---|---|
| `malicious_resolved` <-> `private_resolved` (**MP**) | the variable turns an attack into a defended build -> a mitigation |
| `malicious_resolved` <-> `resolution_error` (**EM**) | the variable alone turns an attack into a broken build (with error) ->  *not* a mitigation |
| `private_resolved` <-> `resolution_error` (**EP**) | the variable alone turns a defended build into a broken build |

A pair has **no direction**: "M -> P" and "P -> M" are the same pair, so all three result
combinations are counted in both directions .

### 7.2 My worry, and the rule that handles it

Some of my variables contain my own design decisions (the C1b setup phase, the `id=central`
override in maven cells), so a flip in this table may be caused by my design and not by the package manager's characteristics.


This is true: a minimal pair proves *that
variable X changed the result*, it doesn't say about *why*. So the rule is: **for every non-zero
count, trace the mechanism.** If it traces to package-manager behavior, it is an ecosystem result;
if it traces to my design (C1b cache effect - Finding 6; pip B1d x C1b ), it is
labelled as such and *not* reported as ecosystem behavior. If it traces to nothing yet, it is a
finding to investigate before writing. Same rule as everywhere else in this analysis.

Is the table necessary? The **MP column** is the one thing the rule test does not give me: it shows
*which variable alone can turn an attack into a defended build*. The EM /
EP columns are supporting numbers for the fail-closed point.

### 7.3 How I built it (kept simple)

Three small functions:

- `make_partner_key(key, variable_name, new_option)` - takes a key `(ecosystem, A, B1, B2, C1)` and
  gives back the same key with **one** variable replaced (an `if/elif` per variable).
- `get_letter(result)` + `flip_kind(result_1, result_2)` - M / P / E, and "MP"/"PM" -> `MP`,
  "ME"/"EM" -> `EM`, else `EP`.
- `count_pairs_of_one_variable(valid_rows, results, ecosystem, variable_name, column, options)` -
  for every valid cell of this ecosystem and every *other* option of this variable: build the
  partner key, skip if the partner is not a valid cell, count the pair, and if the two results
  differ count the flip by kind. Returns `pairs, MP, EM, EP`.
- `main()` loops over the 3 ecosystems x 4 variables, prints the table and writes it to CSV.

**Counting each pair only once:** a pair would be seen twice, once from each cell. The trick is
`if my_option >= other_option: continue` - the pair is only counted from the cell whose option
comes first alphabetically (`A1a-A2` is counted, `A2-A1a` is skipped). This works because my option
names sort in a sensible order (`A1a < A1b < A2 < A3`, `B1a < ... < B1d`, `B2a < B2b < B2c`,
`C1a < C1b < C1c`).


### 7.5 Final minimal pair table 

- script: sub-RQ1_result\analysis\step7b_minimal_pairs_table.py
- generated CSV file: sub-RQ1_result\analysis\step7b_minimal_pairs_table.csv

| ecosystem | variable | pairs | MP | EM | EP |
|---|---|---|---|---|---|
| npm | A | 189 | 8 | 16 | 8 |
| npm | B1 | 189 | 10 | 20 | 23 |
| npm | B2 | 135 | **12** | 66 | 0 |
| npm | C1 | 135 | **0** | 0 | 12 |
| pip | A | 189 | **0** | 24 | 12 |
| pip | B1 | 189 | **0** | 44 | 36 |
| pip | B2 | 135 | **54** | 16 | 0 |
| pip | C1 | 135 | **0** | 16 | 0 |
| Maven | A | 126 | 3 | 6 | 6 |
| Maven | B1 | 126 | 3 | 6 | 35 |
| Maven | B2 | 45 | **30** | 12 | 0 |
| Maven | C1 | 90 | **0** | 0 | 4 |

Check passed: the MP column reproduces the table in the analysis plan and in
`summary_result_analysis.md` section 6 (npm 8 / 10 / 12 / 0, pip 0 / 0 / 54 / 0, Maven 3 / 3 / 30 /
0). The EM and EP columns are new.

### 7.6 How to read it, and which non-zero cells trace to my design

- **C1 has MP = 0 in all three ecosystems.** The pipeline operation type never turns an attack
  into a defended build. Operation type is not a mitigation.
- **For pip, only B2 has MP > 0** (54). No single change of A, B1 or C1 ever turns a
  `malicious_resolved` pip cell into a `private_resolved` one - only pinning does.
- **EM is larger than MP for A and B1 in every ecosystem** (npm A 16 vs 8, pip B1 44 vs 0, ...).
  Changing the registry topology or the package manager configuration alone mostly turns an attack
  into a *broken build*, not into a defended one. This is the quantitative form of "blocking public
  access protects by breaking the build".
- Non-zero cells that trace to my harness, to be labelled as such:
  - **Maven A: MP = 3 and B1: MP = 3** - the `mvn_A2_B1a_*_C1b` cache cells (Finding 6, C1b setup
    phase fills `~/.m2`). Not Maven behaviour.
  - **Maven C1: EP = 4** - `mvn_A2_B1a_B2{a,b}_C1b` (`private_resolved`) against their C1a and C1c
    siblings (`resolution_error`): 2 cells x 2 pairs = 4. Same cache effect.
  - **pip C1: EM = 16** - the 8 `pip_*_B1d_B2{b,c}_C1b` cells (`resolution_error`, section 0.5)
    against their C1a and C1c siblings (`malicious_resolved`): 8 cells x 2 pairs = 16. Harness,
    not PyPI.
  - **npm C1: EP = 12** - still to trace cell by cell (expected: the 4 npm `A2/A3 x B1a x B2b/c x
    C1b` cells against their C1a/C1c siblings = 8, plus 4 more to identify).

### 7.7 Small things left in this script

- Add the "trace" for the npm C1 EP = 12 cells (a small function that prints the pairs of one
  ecosystem and one variable with their cell ids, so every non-zero count can be listed).

---

## Next steps
- [ ] `step7b_five_cells_evidence.py`: change the empty-field text (section 5); call
      `compare_npm_lockfiles()` for the other three npm cells.
- [ ] add the pair-listing function and trace npm C1 EP = 12.
- [ ] check: Maven `Downloaded from` repository vs lockfile `resolved` for all Maven
      `malicious_resolved` cells (section 5).
- [ ] `git log -- fixed_setup_file/npm-service-fixed-lock.json` to settle how the fixed lockfile
      was created (section 2.5).
- [ ] Excel cross-check of the per-variable table and the A1a/A1b comparison (still open from 10.09).
- [ ] Then Step 9 (Figure G, cross-ecosystem comparison) per the schedule.

# 15.09.2026 - sub-RQ1 result analysis Step 9: cross-ecosystem comparison (Figure G), done in Excel

Schedule day 5 (analysis plan Part 3a): Step 9 - compare, for every configuration combination
(A, B1, B2, C1), what the three ecosystems results, count agreement, and explain every
disagreement with its cause. Decided to do it in **Excel** instead of a script: the data is final,
the `cell_id` column is already a lookup key, and the formatted table is the figure itself.
Everything is in `sub-RQ1_result/analysis/result_analysis_excel.xlsx`, new sheet `step9`.
The sheet with the imported `results.csv` is called `results` below (columns: A = `cell_id`,
C = `ecosystem`, D = A, E = B1, F = B2, G = C1, H = `classification`).



---

## 1. Building the comparison table (sheet `step9`)

**Step 1 - the 144 combinations.** Copied columns D:G (A, B1, B2, C1) of all 432 rows from
`results` to `step9!A1`, then `Daten -> Duplikate entfernen` on the 4 columns. ,
**144 rows remain** = 4 A x 4 B1 x 3 B2 x 3 C1, one row per combination, including the invalid ones.
Note: `Duplikate entfernen` keeps the order of first appearance, so the C1b rows ended up at the
bottom (rows 95+). For the figure the sheet must be sorted A, B1, B2, C1 (not done yet).

**Step 2 - the three ecosystem results per combination.** Headers E1 `nodejs`, F1 `python`,
G1 `java`. The cell_id is rebuilt from the four variable cells and looked up in `results`:

```
E2: =SVERWEIS("npm_"&A2&"_"&B2&"_"&C2&"_"&D2;results!$A:$H;8;FALSCH)
F2: =SVERWEIS("pip_"&A2&"_"&B2&"_"&C2&"_"&D2;results!$A:$H;8;FALSCH)
G2: =SVERWEIS("mvn_"&A2&"_"&B2&"_"&C2&"_"&D2;results!$A:$H;8;FALSCH)
```



**Step 3 - the result agreement column H.**

```
H2: =WENN(ZÄHLENWENN(E2:G2;"<>invalid_configuration")<2;"not comparable";
     WENN(MAX(ZÄHLENWENN(E2:G2;"malicious_resolved");ZÄHLENWENN(E2:G2;"private_resolved");
              ZÄHLENWENN(E2:G2;"resolution_error"))
          =ZÄHLENWENN(E2:G2;"<>invalid_configuration");"agree";"disagree"))
```

How to read it: first count how many ecosystems really executed this combination (cells that are not
`invalid_configuration`) = "executed". if this kind of cell is less than 2 -> "not comparable" (nothing to compare; this
also catches the rows where all three are invalid). Otherwise count the M, P and E in the row and
take the biggest count; if the biggest count equals "executed" cell, that means one single result covers every
executed ecosystem -> "agree"; else "disagree". 

Examples: `P P P` -> 3 = 3 agree;
`M M invalid` -> 2 = 2 agree; `E P P` -> 2 != 3 disagree.

Counts (`=ZÄHLENWENN(H2:H145;"agree")` etc.):

| agreement | combinations |
|---|---|
| agree | **96** |
| disagree | **39** |
| not comparable | **9** |
| total | 144 |

The 9 not-comparable rows are A3 x B1c (3 B2 x 3 C1), invalid in all three ecosystems.
So **135 combinations are comparable; 96 of them (71 %) agree, 39 disagree.** 



---

## 2. Finding the groups inside the 39 disagreements (question by question, like 10.09)

### Step A - which ecosystem is the odd one out?

Column I `npm_result_alone`:

```
I2: =WENN(H2="disagree";WENN(UND(E2<>F2;E2<>G2);"npm alone";
      WENN(UND(F2<>E2;F2<>G2);"pip alone";
      WENN(UND(G2<>E2;G2<>F2);"maven alone";"mixed")));"")
```

Result: **npm alone 28, pip alone 7, maven alone 4, mixed 0** (= 39).

Two imprecisions of this formula, found and handled: (1) the WENN chain checks npm first and the
first true branch wins, so a row where Maven is `invalid_configuration` (e.g. `M / E / -`) is put
into "npm alone" although pip is the odd one; (2) the one row where all three results differ
(`A3 B1a B2b C1b` = `P / E / M`) also lands in "npm alone". So the 28 is too big.

### Step A2 - clean the 28

Filter I = `npm alone` and G <> `invalid_configuration`: **22 rows**. 21 of them look like
`resolution_error / private_resolved / private_resolved`; the 22nd is the special row
`A3 B1a B2b C1b` (`private_resolved / resolution_error / malicious_resolved`).

**Why there is only one row where all three ecosystems differ:** such a row needs an M, a P and an
E at the same combination. Under B2a there is never an M (Finding 1), so pinned rows have at most two
different values. Under B2b/B2c a P occurs only in the 5 positive-control cells
(A2/A3 x B1a x C1b), and of those combinations only A3 x B1a x B2b has a Maven M (the `id=central`
leak). So the single all-different row is where three separate causes meet in one combination.

### Step B - group 1: what the 21 npm-alone rows share (pivot: Zeilen = B2, B1, C1; Filter = npm alone)

- B2: only **B2a** appears.
- B1: only **B1b** and **B1c** (B1a only in the special row). B1d never.
- A: all four. C1: all three, equal counts.

Sentence: *npm alone has result `resolution_error` when B2 = B2a and B1 is B1b or B1c, for every A
and every C1; pip and Maven have `private_resolved` there.* Count: B1b 4 A x 3 C1 = 12,
B1c 3 A x 3 C1 = 9 (A3 x B1c invalid) -> **21**.

**Mechanism (my own pilot finding, log 10.07.2026, "Design decisions confirmed" point 1 and "Key
findings" 1):** npm parses duplicate `registry=` keys in `.npmrc` as **last-key-wins**. My B1b/B1c
`.npmrc` has the private URL on the first line and the public / proxy URL on the second line, so npm
only asks the second one - the public registry (directly under B1b, via the Nexus proxy under B1c).
Version 1.0.0 does not exist there (only 1.0.3), and B2a demands 1.0.0 -> `ETARGET` ->
`resolution_error`. pip and Maven really consult both registries and find 1.0.0 in Nexus ->
`private_resolved`. **Ecosystem property of npm**, not harness.

**Why B1d is not in the disagree list:** filtered H = `agree`, B1 = B1d, B2 = B2a: all 12 rows are
`resolution_error / resolution_error / resolution_error`. So under B1b/B1c npm behaves like *every*
ecosystem does under B1d (default configuration = public registry only). That is the precise form
of "npm B1b = B1c = B1d". **Still to prove pointwise** (see Next steps) - the disagree/agree rows
only show the B2a slice, and the claim must hold for every A, B2, C1. Expected reason: the other
variables do not change which registry npm queries (fixed by B1), only what happens at that
registry (pinned -> E, not pinned -> M), which is the same as under B1d. Note for the write-up: the
*result* is identical, but the *delivery path* is not - under B1c the attacker's package came
through the Nexus proxy, under B1b/B1d directly from npmjs.org (Finding 3).

### Step C1 - group 2: maven alone (4 rows)

Filter I = `maven alone`: all four are **A3 x B1a**, C1a and C1c. Maven: `private_resolved` under
B2a, `malicious_resolved` under B2b; npm and pip: `resolution_error`.

Mechanism: under A3 x B1a I used the repository's own name as repository ID (not `central`), so the
super-POM's real Maven Central is not overridden and is searched as well (09.08 entry, Finding 5
exception 1). Under B2a Maven needs exactly 1.0.0, Central has only 1.0.3, so 1.0.0 comes from
internal-hosted -> P. Under B2b Maven searches both repositories and takes the highest version in
the range -> 1.0.3 from Central -> M. npm and pip see only internal-hosted, where the public
dependencies do not exist -> the build breaks. **My own design decision, not a Maven property.**
The same effect under C1b sits inside the special row.

### Step C2 - group 3 and group 4: pip alone (7 rows) - two different reasons

All seven have **C1b**. Two patterns:

- **4 rows: B1d x B2b x C1b** (A1a, A1b, A2, A3): npm and Maven `malicious_resolved`, pip
  `resolution_error`. Reason: C1b has two phases. Phase 1 (setup) is *my harness* creating the
  starting state "1.0.0 is already installed": it installs the fixed `pyproject.toml` (pinned 1.0.0)
  using the cell's own `pip.conf`. Phase 2 is the operation under test (`pip install --upgrade`).
  Under B1d `pip.conf` points only at PyPI, where 1.0.0 does not exist -> phase 1 fails -> phase 2
  never runs. The `resolution_error` is the harness saying "I could not build the starting state",
  not pip saying "the upgrade failed". Proof it is not a PyPI result: the same configuration under
  C1a and C1c is `malicious_resolved`. **Harness (Finding 5 exception 2, plan section 0.5).**
- **3 rows: A2/A3 x B1a x (B2a, B2b) x C1b** (`A2 B1a B2a`, `A2 B1a B2b`, `A3 B1a B2a`): npm and
  Maven `private_resolved`, pip `resolution_error`. **The trap: "who is different" is not "who has
  the cause".** pip fails phase 1 because the public dependencies do not exist in internal-hosted -
  and pip also fails C1a and C1c for the same configuration, so pip is *consistent*. The odd
  behaviour is that npm and Maven **complete C1b** where they fail C1a/C1c: npm because
  `npm update <pkg1> <pkg2>` re-resolves only the two named packages (Finding 7, an npm property;
  the B2a cells are the no-op cells with inherited URLs, summary section 3), Maven because the public
  dependencies come from the `~/.m2` cache filled in phase 1 (Finding 6, harness). These 3 rows
  belong to the same family as the special row.

### Step C3 - the 6 rows where Maven is invalid (filter H = disagree, G = invalid_configuration) - NOT DONE YET

Expected (to verify tomorrow): look at npm vs pip only. Rows `M / E / -` are B1d x B2c x C1b (4 rows,
A1a, A1b, A2, A3) -> same reason as group 3. Rows `P / E / -` are A2/A3 x B1a x B2c x C1b (2 rows)
-> same reason as group 4. No new group.

### The grouping table (to be verified and completed tomorrow; counts must add up to 39)

| group | pattern (A, B1, B2, C1) | odd ecosystem | cause | label | rows |
|---|---|---|---|---|---|
| 1 | all A, B1b/B1c, B2a, all C1 | npm (E vs P/P) | last-key-wins `.npmrc`: npm asks only the public registry, 1.0.0 not there | ecosystem (npm) | 21 |
| 2 | A3, B1a, B2a/B2b, C1a/C1c | Maven (P or M vs E/E) | repository ID != `central` -> real Central leaks in | implementation (`id=central`) | 4 |
| 3 | all A, B1d, B2b/B2c, C1b | pip (E vs M/M or M/-) | pip C1b phase 1 cannot obtain 1.0.0 from PyPI, phase 2 never runs | harness (C1b phase 1) | 8 (4 + 4 from C3) |
| 4 | A2/A3, B1a, all B2, C1b | npm + Maven complete, pip fails (incl. the all-different row) | npm updates only the named packages; Maven `~/.m2` cache; pip fails like in C1a/C1c | npm property + harness cache (+ `id=central` in the A3 x B2b row) | 6 (3 + 2 from C3 + 1 special) |

21 + 4 + 8 + 6 = 39. **Reading: 21 disagreements are a genuine ecosystem difference (npm), 4 are
my `id=central` decision, 14 are C1b-phase-1 effects. Every disagreement has a named cause.**
This table is the core of section 7.5.

---

## 3. Two by-products

- **Open item "npm C1 EP = 12" (14.09 section 7.6) is closed by this table.** Group 4 shows the 6
  npm cells `npm_{A2,A3}_B1a_B2{a,b,c}_C1b` are `private_resolved` while their C1a and C1c siblings
  are `resolution_error`: 6 cells x 2 pairs = 12. My guess on 14.09 was 4 cells + 4 unknown; the
  unknown 4 are the two B2a no-op cells x 2 pairs.
- **Every C1-related disagreement is a C1b row; C1a and C1c rows always come in identical pairs.**
  Suggests C1a = C1c for every cell. Needs the pointwise check over all 432 cells (Next steps). If it
  holds, Figure G in the thesis can be 36 rows (A, B1, B2) x two blocks of three ecosystem columns
  ("C1a = C1c" and "C1b").

---

## 4. Figure G, Excel version

Conditional formatting on `step9!E2:G145` (`Bedingte Formatierung -> Regeln zum Hervorheben von
Zellen -> Textinhalt`), one rule per result with the Figure C colours: `malicious_resolved` red,
`private_resolved` green, `resolution_error` yellow, `invalid_configuration` grey; column H green
for agree, orange for disagree. Readable at a glance: yellow appears in the npm column only under
B2a; disagree rows cluster.

Still to do: sort A1:I145 by A, B1, B2, C1 (four levels, `Daten -> Sortieren`), so the C1a/C1b/C1c
rows of one combination are consecutive. 144 rows do not fit a thesis page: keep this as the
appendix/log version; the compact 36-row version is easier to draw with the Figure C matplotlib code
than in Excel - decide on the write-up day.

---

## 5. Excel pieces used today (so I do not have to look them up again)

- `Duplikate entfernen`: deletes every row that is an exact repeat of an earlier row in the selected columns.
- `&`: glues texts (`"npm_"&A2&"_"&B2` -> `npm_A1a_B1a`).
- `SVERWEIS(what; where; column; FALSCH)`: search `what` in the first column of `where`, return the
  value from column number `column` of the same row; `FALSCH` = exact match; `$` freezes the range.
- `WENN(test; if_true; if_false)`: yes/no decision; nested = chain of decisions, first true wins.
- `UND(a; b)`: true only if both hold. `<>` = not equal.
- `ZÄHLENWENN(range; condition)`: how many cells meet the condition; `"<>invalid_configuration"`
  counts the executed ecosystems. `ZÄHLENWENNS` = several conditions at once.
- `MAX(x; y; z)`: the largest number.
- `WECHSELN(text; old; new)`: replace a piece of text, used to build a sibling cell_id
  (`WECHSELN(A2;"_C1a";"_C1c")`) for a pointwise comparison via SVERWEIS.
- Filter: hides rows; formulas still see all rows; copying a filtered range copies only visible rows.
- PivotTable (`Einfügen -> PivotTable`, Neues Arbeitsblatt; panel with Filter / Spalten / Zeilen /
  Werte): drag a column into Zeilen to list its values, a column into Werte to count rows; Filter
  restricts the counting. Same job as `count_one_variable_option()` without code.

---

## Next steps (16.09)
- [ ] Step C3 in Excel (6 Maven-invalid disagree rows), then confirm the grouping table counts 21 / 4 / 8 / 6 = 39.
- [ ] Pointwise checks on the `results` sheet, each one formula column + one `ZÄHLENWENN(...;"DIFF")`:
  - C1a = C1c (all ecosystems): `=WENN(G2="C1a";WENN(H2=SVERWEIS(WECHSELN(A2;"_C1a";"_C1c");$A:$H;8;FALSCH);"same";"DIFF");"")` - 144 comparisons.
  - npm B1b = B1d: `=WENN(UND(C2="nodejs";E2="B1b");WENN(H2=SVERWEIS(WECHSELN(A2;"_B1b_";"_B1d_");$A:$H;8;FALSCH);"same";"DIFF");"")` - 36 comparisons.
  - npm B1c = B1b: same with `"_B1c_"` -> `"_B1b_"` and `E2="B1c"` - 27 comparisons.
  - A1a = A1b (the Excel cross-check open since 10.09): `WECHSELN(A2;"_A1a_";"_A1b_")` on the A1a rows - 96 comparisons, must give 0 DIFF like the Python result.
- [ ] Sort `step9` by A, B1, B2, C1; decide the compact Figure G layout after the C1a = C1c result.
- [ ] Tick Step 9 in `docs/summary_result_analysis.md` section 10; add the closed npm C1 EP = 12 trace.
- [ ] The small script fixes from summary section 10 (`step7b_five_cells_evidence.py` empty-field text
      + the other three npm cells; pair-listing function; stale "31 + 4" line in the plan file).
- [ ] Then Step 10 (Figure H, system level) - it is this same `step9` sheet plus one
      `=ZÄHLENWENN(E2:G2;"malicious_resolved")` column.

# 20.09.2026 - sub-RQ1 result analysis: Step 9 finished (Figure G verified), Step 10 done (Figure H, system-level result), all in Excel



## 0a. What Step 10 (system-level analysis) actually does, in plain words

Until Step 10, one row of data = **one service** (one ecosystem with one configuration combination).
Step 10 asks a different question: *the test application runs all three services; the administrator applies one
registry and package-manager policy; what happens to the test application as a whole?*

So the three cells that share the same configuration combination (A, B1, B2, C1) - the npm cell, the
pip cell and the Maven cell - are grouped and looked at as **one system**. Per combination two things
are counted: for how many of the three services this configuration is **valid** (column J), and how
many of them resolved the attacker's package (column K). That is all Step 10 is: a count across the
three ecosystem columns that Figure G already has (figure G is the cross-ecosystem comparison, about result agree or disagree between all three ecosystem).

**The assumption this grouping needs, to be stated once in the thesis:** the three services are
**independent** - separate projects, separate package managers, separate Nexus repositories, separate
CI jobs - so the resolution of one service cannot influence the resolution of another. Only because
of that may three separately measured cells be read as one system.

## Corrections to section 4 (made 08.10.2026)

- **Column names.** The column headers in the sheet are **`valid_cell in this row`** (J) and
  **`count malicious_resolved in this row`** (K); the label for J = 0 is **`all invalid cells`**.
  
- **What column J in sheet really means.** J means  **for how many of
  the three services this configuration combination is valid, i.e. can be applied at all** (3, or 2
  under B2c because a POM cannot express an unspecified version, or 0 for A3 x B1c). A cell with
  result `resolution_error` **is** counted in J: the configuration could be applied, the package
  manager just could not resolve the packages and the build failed. Only *invalid* combinations are
  excluded. (not count)
- **"all compromised" means all **valid** services, not always three.** 


Finished the open items of Step 9 from the 15.09 entry (Step C3, verified grouping
counts, four pointwise checks) and did the whole of Step 10 (system-level aggregation, Figure H).
Everything is in `sub-RQ1_result/analysis/result_analysis_excel.xlsx`: sheet `step9` (the 144
configuration combinations from 15.09, now with new columns J, K, L) and sheet `results` (the imported
`results.csv`, now with new check columns T, U, V, W; ). 



---

## 1. Step C3 - the 6 disagree rows where Maven is `invalid_configuration`

Filter on `step9`: H = `disagree` and G = `invalid_configuration` -> 6 rows. All have **B2c**
(unspecified version), which maven cannot express -> invalid. Only npm (E)
and pip (F) carry information. Two patterns:

| rows | A | B1 | B2 | C1 | npm | pip | belongs to |
|---|---|---|---|---|---|---|---|
| 4 | A1a, A1b, A2, A3 | B1d | B2c | C1b | `malicious_resolved` | `resolution_error` | **group 3** |
| 2 | A2, A3 | B1a | B2c | C1b | `private_resolved` | `resolution_error` | **group 4** |

- Group-3 reading: npm reaches the public registry under B1d and takes 1.0.3, whatever A is; pip
  fails in the C1b setup phase because 1.0.0 does not exist on PyPI (because of B1d) (this is a design effect).
- Group-4 reading: npm under B1a with A2/A3 only sees internal-hosted, `npm update` touches only the
  two internal packages and finds 1.0.2 -> `private_resolved`; pip fails phase 1 because the public
  dependencies are not in internal-hosted repo (it fails C1a/C1c there as well).
- **No new group.** Both patterns are C1b-phase-1 effects already named on 15.09.

## 2. The grouping table - counts verified with `ZÄHLENWENNS` 

Formulas on `step9` (rows 2-145):

```
group 1: =ZÄHLENWENNS($H$2:$H$145;"disagree";$C$2:$C$145;"B2a";$E$2:$E$145;"resolution_error";$F$2:$F$145;"private_resolved")
group 2: =ZÄHLENWENNS($H$2:$H$145;"disagree";$A$2:$A$145;"A3";$B$2:$B$145;"B1a";$D$2:$D$145;"<>C1b")
group 3: =ZÄHLENWENNS($H$2:$H$145;"disagree";$B$2:$B$145;"B1d";$D$2:$D$145;"C1b")
group 4: =ZÄHLENWENNS($H$2:$H$145;"disagree";$B$2:$B$145;"B1a";$D$2:$D$145;"C1b")
```

Output: **21 / 4 / 8 / 6 = 39.** The table from 15.09 is now *verified*, not expected. One sentence
per group (written into the sheet next to the counts):

- **Group 1 (21) - npm property.** Under B2a with B1b/B1c, npm alone has result `resolution_error`
  because its last-key-wins `.npmrc` makes it query only the public registry, where 1.0.0 does not
  exist, while pip and Maven can access both registries and find 1.0.0 in Nexus.
- **Group 2 (4) - my `id=central` design decision.** Under A3 x B1a (C1a/C1c), Maven alone can also
  see real Maven Central because the repository ID is not `central`, so it resolves 1.0.0 (B2a) or
  1.0.3 (B2b) while npm and pip cannot find the public dependencies and break.
- **Group 3 (8) - design effect (pip C1b phase 1).** Under B1d x B2b/B2c x C1b, pip alone has result
  `resolution_error` because the setup phase cannot obtain 1.0.0 from PyPI (because of B1d, pip only sees PyPI), so the package update under test
  never ran. the same configuration is `malicious_resolved` under C1a and C1c.
- **Group 4 (6) - C1b (package update) completes only for npm and Maven.** Under A2/A3 x B1a x C1b, pip fails as it
  does in C1a/C1c (public dependencies unreachable), while npm completes because `npm update`
  re-resolves only the two named packages (npm property) and Maven because the public dependencies
  come from the `~/.m2` cache filled in phase 1 (harness); the A3 x B2b row additionally shows the
  group-2 leak (`malicious_resolved`).

**Summary sentence for section 7.5:** of 135 comparable configuration combinations, 96 agree and 39 disagree; 21
disagreements are a genuine ecosystem difference (npm), 4 are my `id=central` decision, 14 are
C1b-phase-1 effects. Every disagreement has a named cause.

---

## 3. Four pointwise checks on the `results` sheet (columns T, U, V, W)

### 3.1 How one of these formulas works 

Example T2, the row of `npm_A1a_B1a_B2a_C1a`:

```
T2: =WENN(G2="C1a";WENN(H2=SVERWEIS(WECHSELN(A2;"_C1a";"_C1c");$A:$H;8;FALSCH);"same";"DIFF");"")
```

1. `G2="C1a"` -> this row is a C1a cell, so it is the *left side* of a pair. A C1b or C1c row fails
   this test and stays **empty** - it is never a left side; its pair is handled from the C1a row.
2. `WECHSELN(A2;"_C1a";"_C1c")` -> builds the partner's cell_id `npm_A1a_B1a_B2a_C1c`: same
   ecosystem, A, B1, B2 - only C1 changed.
3. `SVERWEIS(<partner id>;$A:$H;8;FALSCH)` -> finds the partner's row and returns its column 8 =
   `classification`.
4. `H2 = <partner's classification>` -> `same` if the two cells of the pair have the same result,
   otherwise `DIFF`.

So every pair is checked exactly once, and the word is written in the left cell's row only. Empty
cells are correct (not tested from that side). `same` = *the two cells of the pair have the same
classification*.

### 3.2 The four columns

```
T (C1a = C1c):    =WENN(G2="C1a";WENN(H2=SVERWEIS(WECHSELN(A2;"_C1a";"_C1c");$A:$H;8;FALSCH);"same";"DIFF");"")
U (npm B1b = B1d): =WENN(UND(C2="nodejs";E2="B1b");WENN(H2=SVERWEIS(WECHSELN(A2;"_B1b_";"_B1d_");$A:$H;8;FALSCH);"same";"DIFF");"")
V (npm B1c = B1b): =WENN(UND(C2="nodejs";E2="B1c";H2<>"invalid_configuration");WENN(H2=SVERWEIS(WECHSELN(A2;"_B1c_";"_B1b_");$A:$H;8;FALSCH);"same";"DIFF");"")
W (A1a = A1b):    =WENN(D2="A1a";WENN(H2=SVERWEIS(WECHSELN(A2;"_A1a_";"_A1b_");$A:$H;8;FALSCH);"same";"DIFF");"")
```

filled down to row 433; counted with `=ZÄHLENWENN(T2:T433;"same")` / `...;"DIFF")`. In V the extra
condition `H2<>"invalid_configuration"` skips the 9 invalid `npm_A3_B1c_*` rows, whose B1b partner
is valid and would otherwise show a false `DIFF`.

### 3.3 Results

| check | pairs (`same`) | `DIFF` | meaning |
|---|---|---|---|
| **C1a = C1c** | 144 | **0** | a fresh install (C1a) and a rebuild from the existing lockfile (C1c) never differ - in any ecosystem, any A, B1, B2. The only operation type that ever deviates is C1b, and every C1b difference was traced to phase 1 on 15.09. |
| **npm B1b = B1d** | 36 | **0** | for npm, configuring two registries (private + public) gives the same result as the default configuration in every A, B2, C1 (because of my design, i put public registry to the second line) |
| **npm B1c = B1b** | 27 | **0** | same via the Nexus proxy; 27 not 36 because A3 x B1c is invalid |
| **A1a = A1b** | 108 | **0** | the Excel cross-check of the 10.09 Python result. 108 = 96 valid pairs + 12 invalid pairs where both cells are invalid (`mvn_A1a_*_B2c_*` vs `mvn_A1b_*_B2c_*`, both `invalid_configuration`, counted as `same`). The Python check compared only the 96 valid pairs -> 0 differences in both. |

What `=` means here: *take every pair of cells that are identical in every variable and differ only
in this one option - all pairs have the same result.* A pointwise identity checked at every
combination of the other variables, not an average (same status as A1a = A1b on 10.09).

- **"npm B1b = B1c = B1d" is now a checked identity**, not an observation on the B2a slice. Reason
  it holds for every B2/C1: the other variables do not change *which registry npm queries* (fixed by
  B1 via last-key-wins `.npmrc`), only what happens at that registry (pinned -> E, not pinned -> M),
  and that is the same as under B1d. **Same result, different delivery path:** under B1c the
  attacker's package came through the Nexus proxy, under B1b/B1d directly from npmjs.org (Finding 3).
- **Figure G decision:** because C1a = C1c holds everywhere, the compact thesis figure can show C1a
  and C1c as **one block**: 36 rows (A, B1, B2) x two blocks of three ecosystem columns
  ("C1a = C1c" and "C1b"). To be drawn later with the Figure C matplotlib code. The full 144-row
  Excel table stays as the appendix/log version.

---

## 4. Step 10 - service level -> system level (Figure H), on `step9` (rewritten 08.10.2026)

**Definition:** in the system-level analysis, the *system* is the three services (npm, pip, Maven) under the **same** configuration
combination (A, B1, B2, C1). The system is compromised if at least one service has result
`malicious_resolved`. Maven's B2c cells are *invalid* (not expressible), not "not compromised" - so
for every combination it is counted explicitly for how many services the configuration is valid.

Three new columns:

```
J (valid_cell in this row):              =ZÄHLENWENN(E2:G2;"<>invalid_configuration")
K (count malicious_resolved in this row): =ZÄHLENWENN(E2:G2;"malicious_resolved")
L (system-level):                         =WENN(J2=0;"all invalid cells";WENN(K2=0;"0 compromised";WENN(K2=J2;"all compromised";"partly compromised")))
```

**What column J means :** J says **for how many of the three services this configuration combination is valid,
i.e. can be applied at all**: 3 normally, 2 under B2c (a POM requires a `<version>`, so Maven cannot
express it), 0 for A3 x B1c. A cell with result `resolution_error` **is counted in J** - the
configuration could be applied, the package manager simply could not resolve the packages and the
build failed. Only *invalid* combinations are left out.

### 4.1 The four labels, defined exactly

| label | definition | in words | combinations |
|---|---|---|---|
| `all invalid cells` | J = 0 | the configuration cannot be applied in any ecosystem (A3 x B1c) - there is no system to judge | 9 |
| `0 compromised` | J >= 1 and K = 0 | the configuration is validly applied to one or more services, and **no** service resolved the attacker's package | 54 |
| `partly compromised` | 0 < K < J | at least one service resolved the attacker's package and at least one did not | 11 |
| `all compromised` | K = J >= 1 | **every service the configuration is valid for** resolved the attacker's package | 70 |

Two things to be able to defend:

- **`partly compromised` does not need an extra condition "J >= 1" - it is implied.** If J = 1 then K
  is either 0 (-> `0 compromised`) or 1 = J (-> `all compromised`), so `0 < K < J` can only happen
  when J >= 2. In my data the 11 rows which has result "partly compromised" all have J = 3 or J = 2.
- **"all compromised" means all services the configuration is valid for, not always three.** 

### 4.2 Breakdown by J (so the labels cannot be misread)

| label | J = 3 (all three ecosystems) | J = 2 (B2c, Maven invalid) | total |
|---|---|---|---|
| `all compromised` | 35 | 35 | 70 |
| `0 compromised` | 48 | 6 | 54 |
| `partly compromised` | 7 (3 with K = 1, 4 with K = 2) | 4 (K = 1) | 11 |

The 11 rows has "partly compromised", named: **3** cells compromised with K = 1 are `mvn_A3_B1a_B2b_C1{a,b,c}` (only Maven cell compromised, the
`id=central` leak); **4** with K = 2 which are compromised are B1d x B2b x C1b (npm and Maven cells compromised, pip has
`resolution_error`); **4** with J = 2, K = 1 are B1d x B2c x C1b (npm cell compromised, pip resolution error, Maven
invalid).

### 4.3 The counts and what they say

```
=ZÄHLENWENN(L2:L145;"0 compromised")                 -> 54
=ZÄHLENWENN(L2:L145;"partly compromised")            -> 11
=ZÄHLENWENN(L2:L145;"all compromised")               -> 70
=ZÄHLENWENN(L2:L145;"all invalid cells")             ->  9    (A3 x B1c; 54 + 11 + 70 = 135 valid configuration combinations)
=ZÄHLENWENNS(L2:L145;"all compromised";J2:J145;3)    -> 35    (one configuration make all three service compromised (count only when J = 3))
```

- **Uniform policy:** of the 135 valid configuration combinations, **81 (60 %) leave the system
  compromised** (70 all + 11 partly); 54 leave it with no compromised service ("0 compromised"). Those 54 are the
  **45 pinned combinations (B2a)** plus **9 non-pinned ones where no service can reach a public
  source** (A2 x B1a: 6; A3 x B1a x B2c: 3) - IMPORTANT: those 9 configuration have no compromised service only because
  the builds **broke** (resolution error), not because a service resolved the private package. The label
  `0 compromised` must always be reported with this split; it does not mean "secure".
- **Among the 90 non-pinned configuration combinations, 81 (90 %) compromise the system.** 
- **one configuration make all three service compromised (count only when J = 3) = 35.**  means: how many single organisation-wide configuration
  decisions compromise **all three** services at once. The formula adds the condition `J = 3` on
  purpose, so that B2c combinations - where Maven does not exist at all - cannot be counted as "all
  three"; that is why it is 35 and not 70. These are the B2b combinations with a public path (B1b,
  B1c, B1d under C1a/C1c, and B1a with a group repository A1a/A1b). This is the multi-ecosystem
  observation
- **Partly compromised = 11, every one traces to a known cause:** 8 x pip C1b phase 1
  (B1d x B2b/B2c x C1b) and 3 x Maven `id=central` (A3 x B1a x B2b, all C1). Without those
  two effects the system-level outcome would be strictly **all-or-nothing**: a configuration combination that
  lets one service reach a public source lets every service reach it.



### 4.5 Figure H, Excel version

Conditional formatting on column K of `step9`: 0 -> green, 1-2 -> orange, 3 -> red, `all invalid
cells` rows grey. This is the "system-level outcome grid" from the plan. The compact version
(rows = A x B1, columns = B2, two blocks "C1a = C1c" / "C1b" now that C1a = C1c is proven) can be
drawn with the Figure C matplotlib code later.

---

## 5. Status of the analysis schedule after today

| step | produces | status |
|---|---|---|
| 5 | Figure C | done (08.09) |
| 6 + 7a | per-variable table + rule tested, 0 wrong on 360 | done (10.09) |
| 7b | minimal pairs + 5-cell write-up | done (14.09); npm C1 EP = 12 traced (15.09) |
| 9 | Figure G + disagreement list with causes | **done** (15.09 + 20.09; compact figure pending) |
| 10 | Figure H, system level | **done** (20.09; compact figure pending) |
| 8 | Figure F, delivery path | open (numbers already in summary Finding 3) |
| 1 + 2 + 3 | section 7.1 write-up | open |
| 11 | synthesis, answer to sub-RQ1 | open |
| 4 | error-cause taxonomy | optional |

## Next steps
- [ ] Sort `step9` by A, B1, B2, C1 (Daten -> Sortieren, four levels) so C1a/C1b/C1c of one coordinate are consecutive.
- [ ] Tick Steps 9 and 10 in `docs/summary_result_analysis.md` section 10; record the closed open
      item "npm C1 EP = 12 = 6 cells x 2 pairs" and the four pointwise identities (C1a = C1c,
      npm B1b = B1c = B1d, A1a = A1b in Excel).
- [ ] Compact Figure G and Figure H with the Figure C matplotlib code (36 rows x two blocks).
- [ ] The small script fixes from summary section 10 (`step7b_five_cells_evidence.py` empty-field
      text + the other three npm cells; pair-listing function in `step7b_minimal_pairs_table.py`;
      stale "31 + 4" line in the analysis plan file).
- [ ] Step 8 (Figure F) - one `SEARCH()` helper column on `pk1_url` + a pivot, plan Step 8.


# 08.10.2026 - sub-RQ2 SCA tool selection: wrote down the whole screening result (work itself was done 29.08 - 08.09.2026)

**Why this entry exists.** The log entry `# 29.08.2026` documents only the *design* of the tool
selection (the 4 stages, the candidate sources - 3 then, 2 now, see section 2 - the 6 hard
requirements, the search queries). The
*outcome* - who was dropped, who survived, and which 3 tools were chosen - was written into two
working files but never into this log. This entry closes that gap. Nothing here is new work; it is
the content of those files, verified against the spreadsheet today.

**The evidence files:**

| File | What it holds |
|---|---|
| `sub-RQ2_tool_selection/dc_repos_github_290826.csv` | frozen raw GitHub API output, 46 repos (never regenerated) |
| `sub-RQ2_tool_selection/gitlab_dc_repos_290826.csv` | frozen raw GitLab output, 10 projects |
| `sub-RQ2_tool_selection/sca_tool_screening_v2.xlsx` | the working screening sheet, one row per tool, 16 columns |
| `sub-RQ2_tool_selection/theoretical_evaluation_tables.md` | Stage 2, the 14-column table per surviving tool |
| `sub-RQ1_result/analysis/sub-RQ1_RQ2_process.md` (Parts 6-9) | the short, plain-English version of the same story |

Documentation data for Stage 2 was collected on **2026-09-06**. No tool was executed for any of it -
every entry comes from the tool's own documentation, its repository, or its package metadata.

---

## 1. The definition I filter with, and the 3 screening questions

I read 8 papers for a definition of "SCA tool". They fall into two groups: (1) a tool that lists a
project's third-party components and then checks some security or licence property of them, and
(2) a scanner **plus a vulnerability database**. **I use group 1.** Group 2 describes how a tool
works, not what it does, and it would throw out papers that are plainly about SCA (Ombredanne 2020
is licence-only). It would also throw out **Syft**, which has no vulnerability database but which I
took from Ding and Cui long before I looked at any GitHub tool - so group 2 breaks my *literature*
tools too, not only the GitHub ones.

Stage 1 therefore asks three questions, one per part of the definition:

| # | Function | Question | Fail means |
|---|---|---|---|
| Q1 | inventory | Is a **software project** the unit of analysis, and is the dependency list taken from the project's own files (manifest, lockfile, source, build output)? | unit is one package name, a domain, a URL or a wordlist -> not an SCA tool |
| Q2 | analyse | Does it check the components against a **decision criterion** - a public registry, an advisory database, a licence list, or a stated policy/consistency rule? | listing only -> inventory-only, drop |
| Q3 | report | Does it report over the **project's whole dependency set**? | a single answer about one supplied package -> drop |

The three Source A tools do **not** go through this filter: the paper already calls them SCA tools.

## 2. The candidate pool: 66 rows, and where each one comes from

`sca_tool_screening_v2.xlsx`, sheet `dc_repos`, rows 2-67:

| Source | How found | Rows |
|---|---|---|
| **A** - literature, first pool | Ding and Cui (ICFTIC 2024): Syft, OpenSCA-cli, OWASP Dependency-Check | 3 |
| **A** - literature, fallback pool | Rasheed et al. (2026), arXiv:2604.21278: Grype, Trivy, CVE-Bin-Tool, OSV-Scanner. **Drawn only after the first pool failed** (section 7) | 4 |
| **B** - GitHub full-text search | `"dependency confusion" fork:false archived:false pushed:>2024-01-01 stars:>=1`, 46 hits on 29.08.2026 | 46 |
| **B** - snowballing inside the GitHub results | found inside a link-collection repo that the GitHub search itself returned: `synacktiv/DepFuzzer`, `benjamin-mauss/depenfusion`, `doyensec/confuser`. The column `found_via` records the source link | 3 |
| **B** - GitLab search | exact search `"dependency confusion"`, projects scope, archived excluded, 10 hits | 10 |
| | | **66** |

**Correction - there are 2 candidate sources, not 3. This supersedes sections 1 and 7 of the
`# 29.08.2026` entry**, which introduced snowballing as a separate "Source C". The three snowball
finds are GitHub repositories like all the other Source B rows, so they belong to Source B. The
split that matters is only **A = named in a paper** vs **B = found by platform search**.

What this does *not* change:

- **Snowballing stays a named, documented search method** inside Source B (backward reference
  search, citable to Wohlin 2014), and the `found_via` column still records the source repo for each
  of the 3 finds, so they remain distinguishable from the 46 phrase-search hits.
- `source = "B - Github"` on those 3 rows in `sca_tool_screening_v2.xlsx` is therefore **correct as
  it stands** - nothing in the sheet needs fixing.
- The **metadata-bound blind spot stays its own limitation**: GitHub repo search indexes only name,
  description and topics, never the README. `DepFuzzer` has an empty description and no topics, so
  no phrase search could ever have found it, whatever wording I used. That is a different blind spot
  from the terminology-bound one (missed because of different wording), and both still have to be
  reported.

Note on the numbers: Parts 7-8 of `sub-RQ1_RQ2_process.md` say 62 tools / 24 dropped / 38 read.
Those are the numbers **before** the 4 Rasheed tools were added and before `depenfusion` was moved
into the dropped group for being outside the time window (last push 2023-07-25; my window starts
2024-01-01). The sheet as it stands today gives 66 / 25 / 41. Same screening, later state of the file.

## 3. Stage 1 result: 25 dropped on sight, 41 read, 32 are SCA tools

- **25 dropped without reading the README** (column `drop reason`): slide decks, attack demos,
  proof-of-concept exploits, RCE payloads, written guides, empty repositories, GitLab copies of a
  GitHub project that is already in the list, and one repo outside the time window. Nine of the ten
  GitLab hits are in this group (0 stars, demos or duplicates) - **GitLab contributed no tool that
  survived Stage 1.**
- **41 read** -> **32 yes**, **8 no**, **1 unknown**.
  - The 32 "yes" are 25 Source B tools + the 7 Source A tools.
  - The 8 "no" are bug-bounty helper tools: they take **one package name** or **a website address**
    as input, not a project, so they fail Q1. Example from the sheet: `0xDepCheck`, run as
    `0xDepCheck <package-name>` - there is no project anywhere in that command.
  - The 1 "unknown" is `supplyshark/supplyshark`: its README never says which manifest files it
    parses, so Q1 cannot be answered without reading the code.
- **No keyword pre-filter was used.** I tested one (drop anything containing "poc"/"exploit"/"demo")
  and it would have wrongly dropped `snyk-labs/snync`, a real Snyk detection tool whose description
  says "mitigate". Manual screening with one recorded reason per row stays auditable; a keyword
  filter does not.

## 4. Stage 3, part 1: HR2 cuts the 25 Source B tools down to 10

HR2 = must support **all three** ecosystems (npm, Python, Maven), because the experiment matrix is
3 x n. **Only 10 of the 25 claim all three** (column `supported ecosystems`):

`visma-prodsec/confused`, `th3-j0k3r/DepConfuse`, `6mile/super-confused`,
`InTruder-Sec/dependency-confusion-tool`, `serhanwbahar/dep-hallucinator`, `cognitivegears/depgate`,
`D3Ext/dep-scanner`, `BlackHatExploitation/depcheck`, `robotshell/konfusio`, `synacktiv/DepFuzzer`.

The other **15 fail HR2**, nearly all for the same reason: they are npm-only or npm + PyPI with no
Maven support at all (`snync`, `dustilock`, `DCHero`, `Loki`, `DeCAF`, `depen-find`, `Gitox`,
`DeepConfusion`, `DepRaptor`, `lockaudit`, `doyensec/confuser` and others). Dependency-confusion
tooling on GitHub is overwhelmingly built for npm; Maven support is the rare one.

## 5. Stage 3, part 2: HR3 cuts those 10 down to 3

HR3 = must read **the files my application really has**. I did not add or change any file in
`services/` to make a tool work - that rule was fixed in the screening plan.

| Ecosystem | Files that actually exist |
|---|---|
| npm | `services/nodejs/package.json`, `package-lock.json` (+ `.npmrc`) |
| Python | `services/python/pyproject.toml`, `pylock.test.toml`, `pylock.test3.toml` (+ `pip.ini`) |
| Maven | `services/java/pom.xml` |

Rule applied: **one readable manifest per ecosystem is enough.** The decisive file is
`pyproject.toml` - it is the *only* place my Python service declares its dependencies.

| Tool | HR3 outcome | Why |
|---|---|---|
| `super-confused` | **PASS** | npm `package.json` + `package-lock.json`; Python **`pyproject.toml`**; Maven `pom.xml` |
| `DepGate` | **PASS** | the same three; Python side is `requirements.txt` + **`pyproject.toml`** per its own `docs/supported-package-managers.md` |
| `DepCheck` | **PASS** | the same three, and it can be pointed at a directory and find them itself |
| `confused` | fail | Python side is `requirements.txt` only |
| `dep-hallucinator` | fail | Python side is `requirements.txt`, `poetry.lock`, `Pipfile.lock` - no `pyproject.toml` |
| `konfusio` | fail | Python side is `requirements.txt` only; it also reaches files by crawling a URL instead of reading a local project |
| `InTruder-Sec/dependency-confusion-tool` | fail | a wrapper around `confused`, so the same Python gap; it also fetches files from GitHub instead of a local checkout |
| `DepConfuse` | fail | parses **no** manifest at all - its input is a CycloneDX SBOM or a PURL list produced by another tool |
| `dep-scanner` | not verifiable | the README never names the manifest filenames it reads, so HR3 cannot be decided from documentation |
| `DepFuzzer` | not verifiable | the README says "files where dependencies are declared, for example ..." and gives no complete list |

**Gap in the sheet, recorded here on purpose:** in `sca_tool_screening_v2.xlsx` the column
`hard-requirement filter reason` is filled in only for the 10 tools that reached Stage 2 - the 3
above plus the 7 Source A tools. For the 7 tools in the lower half of the table the reason sits
implicitly in the `supported ecosystems` and `input manifest files` columns. The table above is that
reasoning written out; if I am asked about those 7, this log entry is where the answer is recorded.

## 6. The main finding: all three Source A tools from Ding and Cui fail - for the same reason

**None of them analyses `pyproject.toml` on its own**, and that is my only Python manifest. All three
pass HR2, HR4, HR5 and HR6, and pass npm and Maven inside HR3. They die on Python:

- **Syft** - has no `pyproject.toml` parser at all. Its Python cataloger globs are
  `*requirements*.txt`, `poetry.lock`, `Pipfile.lock`, `setup.py`, `uv.lock`, `pdm.lock` and
  installed `dist-info` / `egg-info` metadata. Checked in the source, not in the README:
  `syft/pkg/cataloger/python/cataloger.go`.
- **OpenSCA-cli** - its Python files are `Pipfile`, `Pipfile.lock`, `setup.py`, `requirements.txt`,
  `requirements.in`. A code search of the repository for "pyproject" returns **zero** hits.
- **OWASP Dependency-Check** - the clearest case: it *sees* the file and then deliberately refuses
  it. Source comment in `PoetryAnalyzer.java`: *"exit as we can't analyze pyproject.toml -
  insufficient version information"*, and the tool logs *"Python 'pyproject.toml' found and there is
  not a 'poetry.lock' or 'requirements.txt' - analysis will be incomplete"*
  (https://github.com/dependency-check/DependencyCheck/issues/6303). Its Python analyzer is also
  marked *experimental* in its own documentation.

**Two workarounds I rejected, on purpose:**

1. Point Syft at `services/python/.venv/**/site-packages/*dist-info/METADATA`. That reads what is
   *installed*, not what the project *declares*, and it is not a manifest. It would be a different
   measurement.
2. Add a `requirements.txt` or a `poetry.lock` to the Python service. All three first-pool tools
   would then work - but the screening plan says the application's configuration files are not
   changed to accommodate a tool. The application is the object under test.

## 7. The fallback the plan foresaw, and what it produced

The 29.08 design already said: the general-purpose slot is a **tool category**, not those three
specific tools, and if none of them passes the hard requirements, a replacement is drawn from
another academic source. That contingency fired here.

**Replacement source:** Rasheed, McPhee, Patterson, MacDonell & Dietrich (2026), *Hidden Dependencies
and Component Variants in SBOM-Based Software Composition Analysis*, arXiv:2604.21278, which
evaluates four tools and describes them as "state-of-the-art and used in several studies".

| Tool | Outcome | Reason |
|---|---|---|
| **Grype** | FAIL HR3 | it builds its inventory *with Syft*, so it inherits Syft's gap exactly - no `pyproject.toml`, and a search of the Syft repo for "pylock" returns zero hits. What Grype adds over Syft is the analysis half, but it cannot build the Python inventory in the first place |
| **CVE-Bin-Tool** | FAIL HR3 | built around compiled binaries and SBOM input; its Python parser declares exactly one filename, `requirements.txt` (`cve_bin_tool/parsers/python.py`). It is also the only GPL-3.0 tool in the pool |
| **Trivy** | **PASS** | see section 8 |
| **OSV-Scanner** | **PASS** | but through the *lock file*, not the manifest |

**Limitation I must state plainly wherever this source is cited: it is an arXiv preprint, not
peer-reviewed.** I checked the peer-reviewed alternatives first and none of them can supply a
fallback: the nine tools in Imtiaz et al. are all account-bound, single-ecosystem, or unnamed
commercial products, and *Tool or Toy* evaluates neither Trivy nor OSV-Scanner. One point in the
preprint's favour: Jens Dietrich is already in my bibliography as an author of the SCORED '24
blind-spots paper.

Second thing to state honestly: **the second pool was drawn after the first one failed**, not chosen
in parallel. That order is legitimate because the plan names it as a contingency, but it must be
visible in the write-up, not presented as if both pools had been planned from the start.

## 8. Why Trivy and not OSV-Scanner

| | Trivy | OSV-Scanner |
|---|---|---|
| reads `pylock.test.toml` | yes - **documented**, footnote *"Also `pylock.<identifier>.toml` per PEP 751"* | `pylock.toml` is documented; the **named** variant appears only in `osv-scalibr` source |
| reads `pyproject.toml` | yes - documented, parsed next to the lock file to mark **direct** dependencies | **not documented** for OSV-Scanner itself |
| adoption | 37,803 stars | 10,986 stars |
| claims DC detection | no | no |

Three grounds for Trivy: much wider adoption; it documents exactly the two things I need (PEP 751
named lock files, and `pyproject.toml` next to the lock file to identify **direct** dependencies -
which matters, because my two internal packages are declared as direct dependencies in
`[project].dependencies`); and everything can be reviewed from documentation. For OSV-Scanner, the
two facts that matter most rest on the source of a *different* repository, `google/osv-scalibr`.

Correction already recorded in `theoretical_evaluation_tables.md`: an earlier draft credited
OSV-Scanner with its own `pyproject.toml` extractor. That extractor belongs to `osv-scalibr`; a
search of the `osv-scanner` repository returns no reference to it. OSV-Scanner stays as the backup,
but its `pylock.test.toml` filename matching would have to be confirmed by a trial run first.

One practical note: Trivy's rendered documentation site was **stale** when I checked it and omitted
`pylock` entirely. Use `docs/guide/coverage/language/python.md` in the repository, not
`trivy.dev/latest`.

## 9. The three tools selected

| Tool | Category | Why it is in |
|---|---|---|
| **super-confused** (`6mile/super-confused`) | claims DC detection | passes every requirement that can be checked from documentation |
| **DepGate** (`cognitivegears/depgate`) | claims DC detection | the only candidate in the whole pool with no recorded limitation - 11 PyPI releases with matching git tags, a documented JSON/CSV output schema, and an API token that is explicitly optional |
| **Trivy** (`aquasecurity/trivy`) | general-purpose SCA | replacement for the failed Ding and Cui tools; OSV-Scanner stays as backup |

**The composition the plan asked for is intact: 2 tools that claim dependency-confusion detection +
1 general-purpose tool that claims nothing of the kind.** Trivy's documentation never mentions
dependency confusion, which is exactly what keeps the comparison meaningful - and it is the reason I
refused to call this third slot a "negative control" back on 29.08: whether general-purpose SCA
tools detect DC is the unknown that sub-RQ2 measures, so naming it a control would presuppose the
answer.

**Close, but not selected: DepCheck** (`BlackHatExploitation/depcheck`). It passes HR2-HR5 and reads
all three of my manifests. Two reasons it lost the slot:

1. **HR6 only partly.** No releases, no tags, not published on PyPI or npm. It can be pinned **only
   by git commit SHA**. That is reproducible, but it is not a version number, and it is inconsistent
   with how every other component in this setup is pinned.
2. It ships an auto-exploit mode (`--exploit`) that generates and **publishes malicious packages to
   public registries** (npm, PyPI, RubyGems, crates.io, NuGet, Packagist, Go, Maven). Only scan mode
   would ever be used here, but the capability is in the tool. The repository also has no licence
   file at all, so the reuse terms are undefined.

Limitation to state for **super-confused** if it is kept: its GitHub repo has **no licence file**
(the GitHub API reports none) while its npm package metadata declares ISC. It is free to use either
way, but the licence status is ambiguous. It is also pinnable through npm only
(`npm install super-confused@1.2.0`), not by a git tag, because the repo has no releases and no tags.
10 stars, single maintainer.

## 10. What is deliberately still open (it belongs to the technical evaluation, not here)

- **HR1 was never evaluated** for any tool. "Runs inside my per-service CI pipeline" cannot be
  decided from documentation - it is the one requirement that needs the tool actually executed.
  That is by design: HR2-HR6 were used as a cheap documentation filter first, so the expensive
  hands-on step stays small.
- **Column 11 of every Stage 2 table - "reports resolved package origin URL" - is still TBD, and it
  is the decisive column for the whole mechanism argument.** If a tool's output carries no
  resolved-registry field, then a same-name-higher-version substitution is structurally invisible to
  it. The *input* definitely carries it: `pylock.test.toml` records
  `url = "http://localhost:8081/repository/pypi-group-public-first/packages/..."` per wheel. Whether
  Trivy keeps that field in its JSON output is unverified.
- **Column 13 - exit code / build-breaking behaviour - is TBD** for everything except
  Dependency-Check (`--failOnCVSS`) and Trivy (`--exit-code`), and those are documented claims, not
  measured behaviour.
- **The input mode must be fixed and written down per tool before the measurement run**, because it
  changes which packages get flagged:
  - *super-confused* and *DepCheck*: both read `package.json` and `package-lock.json` - direct
    declared dependencies vs. the full resolved tree including transitive ones.
  - *DepGate*: for npm, if a lock file is present it analyses the **lock file** (direct +
    transitive); `--direct-only` forces direct dependencies from `package.json` instead.
  - *Trivy*: `pyproject.toml` gives the declared direct dependencies, `pylock.*.toml` gives the
    resolved set **together with the origin URLs**. Which one is used must be stated.
- **Figure 5.4** (the funnel) still has to be redrawn to show the corrected non-circular gate and
  the **two** sources (A = literature, B = platform search, with snowballing as a second search
  method inside B) - open since 29.08.
- The `--cells` subset-rerun option of `central_automated_pipeline.py` is still not built; sub-RQ2
  needs it to re-run only the cells that came out `malicious_resolved`.



### 11.1 Correction: HR2 is a **Stage 1** criterion, not Stage 3

Sections 4 and 5 above call the ecosystem filter "Stage 3, part 1" and the file filter "Stage 3,
part 2". **That labelling is wrong and this supersedes it.** The ecosystem check (HR2) was moved from
Stage 3 to Stage 1 on **30.08.2026**. The counts in sections 4 and 5 are unaffected - only the stage
name is.

Why it was moved: the original design assumed Stage 1 would leave 15-20 survivors, so checking
ecosystems after the table was affordable. The real Stage 1 survivor count came out at **40**, more
than double. (That 40 is the plan file's figure, a snapshot taken on 30.08. The actual spreadsheet
today gives **41 read / 32 "yes"** - see section 3 - because the 4 Rasheed tools were added later and
`depenfusion` moved into the dropped group. Use the spreadsheet's numbers in the write-up; the 40 is
only the reason the decision was taken.) Filling a 14-column table for 40 tools before checking a
fact that is usually one line
in a README is not efficient, and a tool without all three ecosystems is excluded anyway whatever the
other 13 columns say. The check costs a 1-2 minute documentation skim per tool.

**Transparency was kept:** a tool dropped here still gets a full row in the screening spreadsheet
(name, URL, which ecosystems it really supports, reason). It just does not get a 14-column table
entry. So the appendix table holds only tools that passed, while the spreadsheet stays the complete
record of every candidate found.

Which requirement is checked where, in full:

| Hard requirement | Checked from | Applied at |
|---|---|---|
| HR2 - all 3 ecosystems | README skim | **Stage 1** (moved 30.08, was Stage 3) |
| HR3 - reads this project's config files | table column 4 | Stage 3 filter |
| HR4 - machine-parseable output | table column 8 | Stage 3 filter |
| HR5 - free, no mandatory account | table columns 7, 9 | Stage 3 filter |
| HR6 - version can be pinned | table column 10 | Stage 3 filter |
| HR1 - actually integrates and runs | nothing on paper | **technical evaluation only** |

**Limitation written into the plan:** documentation can be wrong or incomplete. A tool may claim
Maven support and fail in practice, or not advertise Maven and still work. Both the Stage 1 ecosystem
check and the Stage 3 filter are therefore *provisional* - technical evaluation can still disqualify
a tool that passed on paper, and that has to be recorded when it happens.

### 11.2 Stage 1 is five criteria in a fixed order, not one question

I only recorded the three-question SCA test above. That test is **criterion 4 of five**, and the
order matters: cheapest and most decisive first, so the expensive table stays small.

| # | Criterion | Drops |
|---|---|---|
| 1 | Is it a tool at all? | blog posts, talk notes, writeups, awesome-lists / link collections (skim those once for tool names, then discard the repo) |
| 2 | Is it a *detection* tool? | PoC / exploit scripts, deliberately vulnerable demo or lab apps |
| 3 | Does it support npm **and** pip **and** Maven? | tools scoped to one or two ecosystems (promoted from Stage 3 on 30.08) |
| 4 | Is it plausibly an SCA tool per Foundations 3.4? | applied via the Q1/Q2/Q3 test - **Stream B only** |
| 5 | Is it maintained? | last push before **2024-01-01**, or **0 stars** |

**Criterion 5 applies to every candidate from every stream**, not only as a side effect of the GitHub
query. The reasoning: an abandoned tool is unlikely to still install against current npm/pip/Maven
tooling (the same risk HR1 checks later), and one star from someone other than the author is a
minimal external-validity signal. Applying those bars only where the search enforces them
automatically, and skipping them for hand-found candidates, would hold searched tools to a stricter
standard than snowballed ones for no reason.

That rule was decided on 29.08.2026 because of a concrete case: `benjamin-mauss/depenfusion`, found by
snowballing from the same guide repo as DepFuzzer - 14 stars (passes the star bar) but last pushed
2023-07-25 (fails recency). It is recorded in the spreadsheet with its reason rather than silently
left out, because the point of documenting Stage 1 is that every candidate that was *found* appears
in the trail, kept or dropped.

**Borderline cases on criterion 4** are admitted to the table and decided once column 5 (detection
mechanism) is filled, since judging a thin tool often needs its mechanism.

### 11.3 Why Stream A skips the SCA-definition test - the exact wording

Section 1 above says only that the Stream A tools do not go through the filter. The justification
matters, because otherwise it looks like one arm got an easier ride:

> *Stream A tools are classified as SCA tools by the source from which they were drawn; that
> classification is inherited rather than re-derived. Stream B candidates carry no such external
> classification, so the definition of Section 3.4 is applied to each directly via the operational
> test below. The criterion is the same in both cases; only the evidence supporting it differs.*

Everything else is identical: **both streams enter the theoretical table, and both must pass the
hard-requirement filter.** There is no Stream A exception anywhere else. Technically evaluating a
tool that structurally cannot run against these services would produce no finding about DC detection
- it would only re-establish an incompatibility the table already documents.

Also: the DC-detection claim is **not a separate screening step**. For Stream B it is built into the
search query, so every Stream B candidate satisfies it by construction. For Stream A it is not
required at all. It is recorded per tool in column 6, where **typosquatting does not count as a DC
claim** - different attack (misspelled name, not same-name-higher-version across a public and a
private registry), and detecting one implies nothing about detecting the other.

### 11.4 The definition argument in full (6 papers vs 2)

Section 1 gives the short version. The real argument:

**The dividing line is whether a definition makes the vulnerability database *constitutive* of the
category - not how many properties it names.** That distinction does the work: Ombredanne names only
licence compliance and Zhao et al. name only vulnerabilities, yet both are Family 1, because neither
builds the database into the definition.

- **Family 1 - functional / mechanism-neutral** (inventory + analysis, no database required):
  Imtiaz/Thorn/Williams ESEM '21, Foo et al. ASE '19, Ombredanne *Computer* 2020, Ning et al. IEEE
  Access, *Tool or Toy* JSS 2025, Zhao et al. ESEC/FSE '23.
- **Family 2 - database-bound** (scanner + vulnerability DB): Dietrich et al. SCORED '24, Liu et al.
  *Dirty-Waters* 2024.

**Five reasons for Family 1** - I had only recorded three:

1. Family 2 binds SCA to a *mechanism* rather than a *function*, so it excludes work published under
   the SCA name - Ombredanne (peer-reviewed *IEEE Computer*, "Software Composition Analysis" in the
   title, licence compliance only, no database) and Ning et al. (binary SCA, neither manifest nor
   database). A definition that excludes acknowledged members of its own category is too narrow.
2. The Family 2 statements are **self-scoping sentences inside vulnerability-reporting studies**, not
   attempts at a general definition. Imtiaz et al. show the move inside one paper: §2 gives the
   general definition, and the very next sentence narrows it *for that study* - "By the vulnerability
   detection capability of SCA tools, we mean...". The authors flag the narrowing themselves.
3. Family 2 would also disqualify **Syft**, which has no vulnerability database, yet Ding and Cui
   evaluate it as one of "the current mainstream SCA tool[s]". So Family 2 breaks the
   *literature-derived* Stream A, not only the DC arm - which is exactly why this choice cannot be a
   tailored one. Inverted: Syft is positive evidence for Family 1.
4. Dietrich et al.'s paper is titled *On the Security Blind Spots of Software Composition Analysis*:
   it gives the sharpest Family 2 definition and then documents what that architecture misses. Cite
   it for the narrow definition **and** for treating the database as current practice rather than a
   defining property. Connect to the research gap in Chapter 4.
5. **(missing from my earlier note, and the strongest)** Adopting Family 2 would answer sub-RQ2
   **analytically instead of empirically**. A vulnerability database records facts about *published
   package versions*; DC susceptibility is a property of the *consuming project's resolution
   configuration* - an internal name being claimable on a public registry the resolver also consults.
   Under Family 2 the answer follows from the definition and the experiment becomes pointless.
   Present this as **circularity, not convenience**. Do not overclaim: an advisory database *can*
   record a specific malicious package after publication; what it cannot record is that an internal
   name is claimable.

**Section 3.4 of the thesis still has to be rewritten.** The wording finalized on 30.08 still reads
*"The main goal of SCA tools is to automate this process to identify and report vulnerabilities..."*
- that is a Family 2 sentence and will be quoted back in the defence. The proposed replacement:

> *An SCA tool takes a software project as input, generates an inventory of the third-party
> components and dependencies the project is composed of, analyses one or more security- or
> compliance-relevant properties of those components, and reports the result. Known vulnerabilities
> are the most frequently analysed property, but the literature also treats license compliance and
> component provenance as SCA functions.*

The only phrase doing definitional work is **"one or more ... properties"** - that is the single
point the argument has to defend. **Zhao et al. is the example to walk through by name in 3.4**: it
is the hardest case for Family 1 and still lands there - a paper titled *Software Composition
Analysis for Vulnerability Detection* that never makes the database constitutive and explicitly
criticises Imtiaz's database-centrism.

### 11.5 The Q1/Q2/Q3 test was deliberately changed - record it as a loosening

Three changes from the earlier draft of the test, each for a reason unrelated to DC:

1. Old Q2 ("a result for every dependency it found") was **too strong** - real SCA tools, including
   OWASP Dependency-Check, report *findings*, not one row per clean dependency. Reworded as Q3.
2. Old Q3 required comparison against an *external* source. **Broadened to "decision criterion"**,
   because a tool may analyse an intrinsic property with no lookup at all (`kriskimmerle/lockaudit` -
   "zero deps, no network"). Requiring a lookup would smuggle a Family 2 assumption back in. This is
   a **genuine loosening that admits more tools - record it as such, not as a clarification.**
3. The "borderline, keep" escape hatch on old Q3 is **removed**. It existed to protect
   inventory-only tools, i.e. Syft; Stream A no longer passes through this test, so it is unnecessary.

**Q1 borderline rule - decide recon-style tools by feasibility, not by definition.** Several
candidates crawl a *deployed target* and rebuild a dependency list from fetched JS (`DepScout`,
`konfusio`, `0xJS`, `Gitox`). Arguably they do inventory a project, so forcing a definitional verdict
invites argument. The rule: do not litigate it - if a tool cannot be pointed at a local project
checkout it fails **HR3** and drops there, as an integration failure. Reserve definitional drops for
unambiguous cases whose unit of analysis really is a bare package name or domain -
`KingOfBugbounty/Dependency-Confusion-Hunter`, `0xPedrop/0xDepCheck`, `supplyshark/supplyshark`.

**Non-circularity, stated as two separate questions:**
1. *"Is dependency confusion a vulnerability?"* - settled in 3.2 via Bos et al.'s classification of
   DC as a package manipulation attack. Not reopened at screening.
2. *"Can this specific tool detect dependency confusion?"* - this is sub-RQ2 itself, measured at
   technical evaluation, never gated at Stage 1.

Q2 asks only whether a tool evaluates its inventory against *some* decision criterion - not whether it
has already been shown to catch DC. A tool needs only to be structurally the *kind* of tool that
technical evaluation can meaningfully test.

**Two supporting citations for 5.4.1, both external to me:** Ding and Cui's introduction cites
`snync` as a tool that *"detects dependency obfuscation in npm by utilizing whether the package name
is registered in a public registry"*, and describes Orca as parsing `requirements.txt` /
`package.json`, extracting the dependency list, comparing it against the public PyPI and npm
registries, and alerting on unregistered packages - that is exactly the Q1 -> Q2 -> Q3 pattern, in a
published paper. Corroborating: `snyk-labs/snync` and `Checkmarx/dustilock` are published by
commercial SCA vendors, so industry itself treats DC checking as within SCA scope. Lead with the
peer-reviewed citation, use the vendor one second.

### 11.6 Search details I had not recorded

- **Sort by stars, not "Best match."** Best-match ranking is opaque and non-deterministic, so it
  cannot be reproduced; star order is stable.
- **Quoting the phrase drops exactly two repos** (48 -> 46), and the plan names them:
  `andrewruba/potato` ("Zero *dependencies*. Infinite *confusion*.") and `wangsiyi7/cogloop`
  ("surface *confusion* hotspots... Zero-*dependency* Node").
- **Cross-platform deduplication rule:** the same tool can appear on both platforms (`confused` is
  `visma-prodsec/confused` on GitHub and a low-star copy on GitLab). Treat the canonical/upstream
  repo as the candidate, note the duplicate, and do not count it twice in the screening flow.
- **Planned reproducibility figure:** record the screening as a flow with counts and an exclusion
  reason per stage - `232 -> 153 -> ... -> n candidates -> shortlist -> 3 selected`.
- **Stage 3 tie-break, never needed but pre-stated:** if more tools pass the filter than can be
  evaluated in the time available, rank survivors by maintenance signal (column 10) and adoption
  (stars), and record the cut-off applied.

⚠️ **Number discrepancy to settle before the write-up.** The star distribution in the plan file and
the one in my `# 29.08.2026` entry do not agree:

| Threshold | plan file | log entry 29.08 |
|---|---|---|
| stars >= 0 | **153** | **134** |
| stars >= 1 | 48 unquoted / 46 quoted | 48 unquoted / 46 quoted |
| stars >= 2 | 29 | 28 |
| stars >= 5 | 20 | 19 |
| stars >= 10 | 12 | 11 |
| stars >= 50 | 3 | 3 |

**Neither figure is backed by an actual file.** The only number in this table that
`sub-RQ2_tool_selection/` can evidence is the **46**: `dc_repos_github_290826.csv` holds exactly 46
data rows plus a header, frozen on 2026-08-29. The whole `stars >= 0 ... >= 50` distribution was
never exported - it exists only as prose in the plan file and in the 29.08 log entry, which is why
the two drifted apart.

So: **report the 46 and cite the CSV.** If the distribution is needed in 5.4.1 to justify the
`stars:>=1` cut, it has to be re-measured and re-exported to a file, and the new measurement date
stated - **re-running the query today will not reproduce either old number**, because stars and push
dates drift and the `pushed:>2024-01-01` window keeps moving relative to them. Internally the plan is
more consistent (it uses 153 twice and "105 of the 153 repos have zero stars" only works with 153),
but that is an argument about the plan's own prose, not evidence from a file, so it does not settle
anything.

### 11.7 Stage 4: what happens if a DC tool is too thin to be an SCA tool

The priority order I recorded on 29.08 has a consequence I had not written down. If a purpose-built
DC checker is too thin to qualify as an SCA tool - e.g. it only checks whether package names exist on
a public registry - **it cannot enter the final 3, even if that means the composition shifts to
1 DC-specific + 2 general-purpose, or another mix.** The shift and its reason get recorded. Table
column 5 (detection mechanism) is what exposes this during screening.

"DC-specific" is also defined: **purpose-built for dependency-confusion detection**, which is what
the Stream B search surfaces - not a general tool that merely mentions DC somewhere.

The fallback rule had one clause I did not record: **check the replacement tool's own DC claim
(column 6).** If the general-purpose replacement *also* claims DC detection, the final 3 becomes
three DC-claiming tools and the intended category spread collapses. Prefer a fallback that does
**not** claim DC detection; if none is viable, record that the spread could not be achieved and why.
This is why Trivy's "no DC claim" (section 8 above) was a selection criterion and not just a nice
property.

### 11.8 Why the general-purpose tool is there - and how far its result may be pushed

**What it is NOT: a population sample.** One tool cannot support "mainstream SCA tools cannot detect
DC". The plan says in capitals: never write that sentence.

**What it IS:** a second tool *category* in the comparison, whose outcome is genuinely unknown going
in, and which is literature-anchored (Ding et al.) rather than an arbitrary pick.

**The payoff is mechanism, not statistics.** If it does not detect, the finding is not "0/n detected"
but *why*: an SBOM-inventory tool emits package name and version with no resolved-registry-origin
field, so a same-name-higher-version substitution is structurally invisible to it - no data in its
output could tell the internal package from the attacker's. That argument generalizes on
architectural grounds rather than sample size, supporting a hedged claim such as: *"this suggests SCA
tools whose output model omits resolved package origin cannot detect DC as a class, independent of
vulnerability-database coverage."* This is the same move already used in sub-RQ1 on 09.08.2026
(`dependency:tree` lacks resolved URLs, so `lockfile.json` was adopted instead) - applied to
detection tooling instead of to evidence collection.

**Claim bounding for the write-up.** The sampling does not support "SCA tools generally do/do not
detect dependency confusion". It supports: *"among tools that advertise DC detection, [result]; for
[named baseline tool], drawn from prior work, [result]."* Report the general-purpose tool as a named
specific result (*"Trivy produced no DC alert in any vulnerable cell"*), never as a population claim,
and generalize only through the mechanism argument.

### 11.9 Defending the search platforms (anticipated question at the defence)

Expected question: *"why only GitHub and GitLab - why not Bitbucket, or just Google?"*

**Do not argue "because I use GitHub Actions."** The plan flags this as weak and easily rebutted - a
CLI tool hosted on GitLab runs perfectly well inside a GitHub Actions runner. Hosting platform and CI
compatibility are unrelated. Use these three instead, strongest first:

1. **A bounded sampling frame is standard method.** Systematic literature reviews select specific
   databases (IEEE Xplore, ACM DL, Scopus) rather than searching the whole internet. A defined,
   indexed, documented source *is* the methodology, not a shortcut.
2. **Reproducibility.** Both platforms give a structured project search with a stable, reportable
   result count, and GitHub additionally has documented query qualifiers and an API, so anyone can
   re-run the exact query. A Google search is personalized, non-deterministic, opaquely ranked and
   has no stable count - a per-stage screening flow with verifiable counts would be impossible.
3. **Coverage of where open-source tooling actually lives.** GitHub and GitLab are the two widely
   used platforms on which developers and organizations publish open-source tools.

### 11.10 The six limitations to document explicitly

Sections 1-10 carry only two of these (terminology-bound and metadata-bound). The full list:

1. **`n = 3`** is a feasibility constraint, not a statistically motivated sample size.
2. **Terminology-bound search.** Tools that detect the DC signal but describe it with other wording
   (namespace collision, package substitution) are absent from the candidate pool.
3. **Metadata-bound search.** GitHub repo search indexes name, description and topics - never the
   README. A repo with an empty description and no topics is invisible whatever its terminology
   (confirmed: `synacktiv/DepFuzzer`, 96 stars, `description: null`, `topics: []`). `in:readme`
   returns 608 instead of 46, infeasible to screen by hand. Snowballing partially mitigates this but
   does not guarantee completeness.
4. **Positive-only dataset.** *(not recorded anywhere before - important)* Only `malicious_resolved`
   cells are scanned, so only **recall and false-negative rate** are computable. `private_resolved`
   cells are deliberately not included, so **no false-positive rate and no precision are reported.**
5. **Platform-bound search.** GitHub and GitLab only; tools hosted solely on Bitbucket or self-hosted
   forges are not represented.
6. **Popularity threshold.** `stars:>=1` removed 105 zero-star repositories; a capable but obscure
   tool with no stars would not appear in the pool.
7. **Literature-bound Stream A.** Stream A covers only the SCA tools used by Ding and Cui, because
   that is the single paper addressing an attack class comparable to DC. SCA tools evaluated in other
   papers - which assess CVE/database detection rather than this attack class - are not in the pool.

### 11.11 Verification checklist and the two edits 5.4.1 still needs

The plan's own verification list, none of which is ticked yet:

- [ ] Confirm the GitHub query reproduces the recorded result count on the recorded date.
- [ ] Confirm every excluded repo has a recorded exclusion reason mapping to one of the pre-stated
      criteria.
- [ ] Confirm the three selected tools each support npm, pip and Maven.
- [ ] Confirm each selected tool's claimed input files (column 4) are **actually present in the
      sub-RQ1 artifact outputs** for all three services.

Two sentence-level edits the existing 5.4.1 text still needs:

1. Change the removal rule (*"tools producing no DC alerts will be removed from the candidate list"*)
   into a recorded capability-screen outcome that informs, but does not by itself decide, final
   selection.
2. State that the final-3 gate is **integration feasibility**, and that the composition deliberately
   spans tool categories: 2 DC-specific + 1 general-purpose mainstream SCA tool.

Plus, from 11.1 and 11.4: Figure 5.4 must show the ecosystem check at **Stage 1**, and Section 3.4
must be rewritten to the Family 1 wording.

### 11.12 One terminology note

The plan file says **"Stream A" / "Stream B"**, while the spreadsheet column and sections 1-10 above
say **"Source A" / "Source B"**. Same thing. The spreadsheet's `source` column values are
`B - Github` (49 rows) and `B - Gitlab` (10 rows) - **those two values only**. The plan file says the
column also carries a third value `B (snowball)`; **it does not** (`sca_tool_screening_v2.xlsx`
wins - it is the actual file). In the real sheet the three snowball finds sit under `B - Github`
and are distinguished by the **`found_via`** column, which holds the referring repo's URL. That is
also consistent with the decision recorded in section 2 above: the snowball finds *are* GitHub
repositories, so `B - Github` is correct for them.

Pick one word before writing 5.4.1 and use it everywhere, including in Figure 5.4.

### 11.13 Conflict register - where the plan file disagrees with the actual files

**Rule applied throughout section 11: where the recovered plan file and the files in
`sub-RQ2_tool_selection/` (or the real `services/` tree) disagree, the actual files win.** The plan
was written on 05.09 and describes what was *intended*; the files record what *is*. **Three**
conflicts found, all resolved in favour of the files.

**Not a conflict - the HR3 file list. The plan file's list is the correct one and is what the
write-up should use:**

| Ecosystem | Files HR3 is tested against |
|---|---|
| npm | `package.json`, `package-lock.json` (+ `.npmrc`) |
| pip | `pyproject.toml`, `pip.conf`, `pylock.toml` (PEP 751, generated by `pip lock` for C1c) |
| Maven | `pom.xml`, `lockfile.json`, `pom.lockfile.xml` (maven-lockfile plugin) |

Several of these are **absent from the git checkout on the development machine, and that is normal**:
the experiment runs on the **self-hosted GitHub Actions runner**, and the configuration is applied
*there*, not here. `lockfile.json`, `pom.lockfile.xml` and the `pylock` files are produced during the
run, inside the runner, and `pip.conf` is the Linux-container config file (the `pip.ini` lying in the
repo is its Windows-side counterpart on the dev machine). So an `ls services/` on this laptop showing
only `pom.xml` for Maven says nothing about what a scanner will find at scan time.

**Why this matters for HR3 specifically:** HR3 asks whether a tool can read *the files that exist
when the tool runs*, which is inside the runner, mid-pipeline. Judging it from the dev checkout would
understate what is available - especially for Maven, where the two lock files carry exactly the
resolved-origin information that table column 11 is about. The
`sub-RQ2_tool_selection/theoretical_evaluation_tables.md` row "Files present in this project" is a
**dev-machine snapshot**, narrower than the runtime picture, and section 5 above inherits that
narrower view.

It does not change any outcome recorded above: every HR3 failure in sections 5 and 6 was a **Python**
failure (`pyproject.toml`), and no tool was ever excluded on Maven grounds. But the thesis text
should name the plan's list, not the laptop's.

One detail from the evaluation table is still worth keeping, because it decided a selection:
the Python lock files appear under the PEP 751 **named** form (`pylock.test.toml`,
`pylock.test3.toml`), not the plain `pylock.toml`. That is the exact fact behind choosing Trivy over
OSV-Scanner in section 8 - Trivy documents the `pylock.<identifier>.toml` pattern, OSV-Scanner
documents only `pylock.toml`.

**1. The `source` column has no `B (snowball)` value** - see 11.12. Spreadsheet wins: 49 ×
`B - Github`, 10 × `B - Gitlab`, snowball finds marked by `found_via`.

**2. The star distribution (153 vs 134)** - see 11.6. No file evidences either; only the 46 in
`dc_repos_github_290826.csv` is citable.

**3. The Stage 1 survivor count (40)** - see 11.1. The spreadsheet's 41 read / 32 "yes" governs; 40
is a 30.08 snapshot that explains why the ecosystem check was moved.

**No conflict found** in the theoretical table's column numbering: the plan's 14 columns and the
columns actually used in `theoretical_evaluation_tables.md` line up one-to-one, so every "column N"
reference in section 11 is valid against the real file. Only two headings were reworded in the actual
file (plan "GitHub link" → "Repository", plan "License / free & open-source" → "Licence / FOSS").

## Next steps

- [ ] Technical evaluation of the 3 selected tools: install them pinned, run them against real
      cells, and fill column 11 (origin URL in the output) and column 13 (exit code) for each.
- [ ] Fix and record the input mode per tool (the list in section 10).
- [ ] Redraw Figure 5.4.
- [ ] Section 5.4.1 of the thesis names Syft, OpenSCA and Dependency-Check - it must now also report
      that all three failed, which requirement each failed on, where the replacement came from, and
      that the replacement claims no DC detection.

# 10.10.2026 - sub-RQ2 technical evaluation: Trivy probe round (first tool, first cell)

**Stand:** built a second, separate self-hosted runner image with Trivy baked in, added a
switchable step (for using SCA tool or not) to all three service CI pipelines, and ran the first probe cell
(`pip_A1a_B1a_B2b_C1c`, a cell that sub-RQ1 classified `malicious_resolved`). Trivy installs, runs
and produces parseable output inside the pipeline, it can be integrated to the CI pipeline / github workflow. It lists
the attacker version `1.0.3` as an ordinary direct dependency and reports **nothing** about
dependency confusion. The decisive table column 11 (resolved package origin URL in the output) is
now answered: **no, in neither output format** 

## 1. technical evaluation

- The 08.10 entry closed the *selection* of the three tools (super-confused, DepGate, Trivy) but
  left three things open that documentation cannot answer:
  - **HR1** - does the tool actually install and run inside the per-service CI pipeline?
  - **Column 11** - does its output carry the *resolved package origin URL*? This is the decisive
    column: with no origin field, a same-name-higher-version substitution is structurally invisible.
  - **Column 13** - does it break the build (exit code) when it finds something?
- Decision: start with **Trivy**, one cell, one ecosystem, and look at the raw output before
  building any classifier logic on top of it.

## 2. Infrastructure: a second runner, without touching the sub-RQ1 runner

- Copied `infrastructure/runner/` -> **`infrastructure/runner_sca/`** (`Dockerfile`,
  `entrypoint.sh`, `settings.xml`). Filenames kept identical on purpose.
- **Two changes** in the copy:
  1. Trivy **0.75.0** installed from the official release tarball, SHA-256 verified
     (`c6e65abd...16b3f3f`), into `/usr/local/bin/trivy` so it is on `PATH` for every user.
     
  2. **`--ephemeral` removed** from `config.sh` in `entrypoint.sh` -> this runner stays registered
     and takes job after job. Reason: for a probe round I want to dispatch cells by hand, and a
     persistent container keeps Trivy's downloaded database between jobs instead of re-downloading
     it per cell.
- The runner **label is still `thesis-runner`**, because all three workflows say
  `runs-on: [self-hosted, thesis-runner]`. 
- `infrastructure/runner/` and `central_automated_pipeline.py` are left untouched.

## 3. Problem found on the way: the pinned runner version expired

- First start of the new container log:
  `An error occurred: Runner version v2.335.1 is deprecated and cannot receive messages.`
- Cause: `--disableupdate` in `entrypoint.sh` (decided 08.08.2026) stops the runner from
  self-updating, and **GitHub enforces a 30-day update window**. 
- Fix: bumped **both** ARGs together to the current release:
  - `RUNNER_VERSION=2.338.0`
  - `RUNNER_SHA256=af4b794c1bc41d73d40535e3fe092a39f9679cd8d965954c2aca25a05ca41d32`
  . 
- ** reporting as a limitation:** every component of this experiment can be pinned
  permanently *except* the GitHub Actions runner binary, because GitHub forces an upgrade every 30
  days. The three main experiment runs (25.08, 28.08, 08.09) all ran on 2.335.1, so **the sub-RQ1
  data is unaffected** - but a re-run today necessarily uses a different runner version than the
  one recorded. This is outside my control and should be stated rather than left for a reader to
  spot as an inconsistency between the Dockerfile and the log.

## 4. Commands used

Build the SCA runner image (from inside `infrastructure/runner_sca/`; the trailing `.` is the build
context):

```powershell
docker build -t sca-thesis-runner:2.338.0 .
```

Start it. Registration token taken by hand from GitHub UI. No `--rm` used, so the container will not delete itself automatically after stop.

```powershell
docker run -d --name sca-probe-runner ^
  -e GH_REPO_URL=https://github.com/shirley1997/MS_test_system ^
  -e GH_TOKEN=<token from GitHub UI> ^
  -e RUNNER_NAME=sca-thesis-runner ^
  -e RUNNER_LABELS=thesis-runner ^
  sca-thesis-runner:2.338.0
```

(in PowerShell the line-continuation character is the backtick, not `^`)


container log shows "Connected to GitHub" followed by "Listening for Jobs".

Download the artifact of the finished cell (through github actions workflow log)



## 5. Pipeline change: one new switch, one new step

- Added a **new input** to all three service workflows:

```yaml
      run_sca:
        description: "sub-RQ2 probe: also run the SCA tool scan after dependency resolution"
        required: false
        type: choice
        default: "off"
        options: ["off", "on"]
```

- **Why `type: choice` with "off"/"on" and not `type: boolean`:** a `workflow_dispatch` boolean
  input arrives as the *string* "false" when dispatched through the API/CLI, and a non-empty
  string is truthy in a GitHub `if:` expression - so `if: inputs.run_sca` would fire even when the
  switch is off. A two-value choice compared with `== 'on'` cannot go wrong either way.
  The quotes around off/on are also necessary: unquoted, YAML turns them into `false`/`true`.

- The new step sits **after the C1a/C1b/C1c steps and before the artifact upload**, guarded by
  `if: inputs.run_sca == 'on'` and `continue-on-error: true`. Three scans per cell:
  1. **declared only, JSON** - the SCA report that would be classified
  2. **declared only, CycloneDX** - the only output format that could carry an package origin URL
  3. **everything, JSON** - same as scan 1 but without `--skip-dirs`, i.e. installed packages in directory are visible
- `--skip-dirs` per ecosystem: `py_dependency .venv build` / `node_modules` / `target`.
  Reason: the screening plan (08.10, section 6) explicitly rejected "read what is *installed*" as a
  different measurement. Scan 3 exists so that difference can be shown with evidence instead of
  argued.
- Exit codes are captured with `${PIPESTATUS[0]}`, not `$?`, because the command is piped into
  `tee` and `$?` would return *tee's* status. 
- The Trivy output files added to each `upload-artifact` path list.

## 6. The probe cell and its output

Dispatched by hand from the GitHub UI: **`pip_A1a_B1a_B2b_C1c`** (A1a / B1a / B2b / C1c,
`run_sca = on`), run on 2026-10-10 18:44-18:45. Chosen because sub-RQ1 classified this exact cell
`malicious_resolved`, so the attacker version really is in the files Trivy reads.

What came out:

- **Target:** `pylock.pip_A1a_B1a_B2b_C1c.toml` -> Trivy matched the **PEP 751 named lock file**.
  The documented footnote *"Also `pylock.<identifier>.toml` per PEP 751"* holds against a filename I
  generate myself, not only against the documented example. This was the single fact that chose
  Trivy over OSV-Scanner on 08.10, and it is now verified behaviour rather than a documentation
  claim.
- **9 packages**, with the attacker version present, but no warning is shown:
  - direct: `flask@3.1.1`, **`xueting-thesis-event-fengfu@1.0.3`**,
    **`xueting-thesis-service-zhuanfa@1.0.3`**
  - indirect: `blinker`, `click`, `itsdangerous`, `jinja2`, `markupsafe`, `werkzeug`
- **Exactly one vulnerability is in the output:** `CVE-2026-27205` in `flask@3.1.1`, severity LOW, fixed in 3.1.3 -
  a real, unrelated CVE in a public third-party dependency.
- **Zero findings about the two substituted packages. The words "dependency confusion" appear
  nowhere in the output.**
- **Exit code 0 on all three scans**, even with that LOW finding present -> column 13 answered:
  Trivy does **not** break the build by default; the documented `--exit-code` flag is what changes
  that. Measured, not claimed.
- **Scan 3 added nothing** - `_all.json` and `_declared.json` are identical in content (both 6544
  bytes, same 9 packages, same 1 CVE). Reason: C1c uses `pip install --dry-run`, so
  `py_dependency/` is never created and there are no installed packages to find. The
  declared-vs-installed comparison can only produce a difference in **C1b** cells.
- The vulnerability database download was **121.03 MiB and took 54 seconds**.

## 7. Main finding

The resolved origin URL was **physically present in the scanned directory, in two separate files**,
and none of it shows in the trivy output:

| File in the scanned directory | What it contained | What Trivy did |
|---|---|---|
| `pylock.pip_A1a_B1a_B2b_C1c.toml` | `url = "http://host.docker.internal:8081/repository/pypi-group-public-first/packages/..."` per wheel | read the file, **discarded the `url` field** |
| `pip_A1a_B1a_B2b_C1c_install-report.json` | pip's own `download_info.url` per package | **never read at all** |

- **JSON output** gives each package only `ID`, `Name`, `Identifier` (PURL + UID), `Version`,
  `Relationship`, `AnalyzedBy`. No URL field of any kind.
- **CycloneDX output** gives `purl`, `bom-ref` and two Trivy properties.
- Verified in the source code why this is not a flag I could flip:
  - `pkg/dependency/parser/python/pylock/parse.go` declares a struct with only `name`, `version`,
    `dependencies` and `directory.path`. The `[[packages.wheels]]` table, where the URL lives, is
    **never decoded**. The field is dropped at parse time.
  - `pkg/fanal/types/package.go` tags `ExternalReferences []ExternalRef` with `json:"-"`, so even
    where Trivy *does* keep a URL (the npm parser keeps `resolved`), it cannot appear in
    `--format json`.
- **The part that is stronger than an omission:** the PURL is
  `pkg:pypi/xueting-thesis-event-fengfu@1.0.3`. PURL has a `repository_url` qualifier for exactly
  this case and Trivy emits none. So the output does not leave the origin blank - **it asserts a
  public-PyPI origin, which for this cell is factually wrong**: the package came from my Nexus
  group repository. An output model like that cannot *represent* the distinction sub-RQ2 is about.


## 8. Second finding: there are no vulnerabilities for my own packages

- Trivy reports only what a vulnerability database already records: it takes name + version and
  looks them up in GHSA/NVD. `blinker`, `click`, `jinja2` etc. simply have no advisory at those
  versions.
- `xueting-thesis-event-fengfu` and `xueting-thesis-service-zhuanfa` do **not exist in any advisory
  database at all** - nobody has ever reported them, including the `1.0.3` I published as the
  attacker. So there is nothing to match against.
- This is the **Family 1 vs Family 2 definition argument** (section 11.4) showing up as data: a
  database-bound scanner can only see facts about *published package versions*. "This internal name
  is claimable on a public registry" is not such a fact, so **no database could record it**. The
  flask CVE is the only thing in the whole report that a vulnerability database could contribute,
  and it is irrelevant to dependency confusion.

## 9. Third finding: for Python, Trivy only has input in C1c cells

- Checked in the source code, not only in the docs table. The analyzers under
  `pkg/fanal/analyzer/language/python/` are six files: `packaging`, `pip` (requirements.txt),
  `pipenv`, `poetry`, `pylock`, `uv`. **There is no stand-alone `pyproject.toml` analyzer.**
- `pylockAnalyzer.Required()` *does* return true for `pyproject.toml`, so Trivy collects the file.
  But `PostAnalyze()` loops over **lock files only**, and `pyproject.toml` is used solely inside
  `mergePyProject()`, which is called once per lock file found, to relabel packages `Direct` /
  `Indirect`. if there is no lock file -> the loop body never runs -> `pyproject.toml` is collected and then
  never parsed into any result. The `poetry` and `uv` analyzers have exactly the same structure.
- So in this cell Trivy **did** read `pyproject.toml` - that is where `"Relationship": "direct"`
  came from - but **only because the lock file was next to it**. The log line
  `Number of language-specific files num=1` and the single `Target` are that showing in my own
  output.
- Consequence: C1a and C1b Python cells give Trivy **no parseable file at all**. Still to be
  confirmed empirically by running `pip_A1a_B1a_B2a_C1a` and checking that `Results` comes back
  empty.
- This is the first case where **a tool passed the Stage 3 documentation filter and turned out
  narrower in practice** - exactly the limitation written into the screening plan (section 11.1:
  "both the Stage 1 ecosystem check and the Stage 3 filter are provisional"). HR3 itself still
  passes on its own stated rule ("one readable manifest per ecosystem is enough"), because the lock
  file *is* readable; the narrowing is about which **cells** can be measured, not about the tool
  failing a requirement.

## 10. Decision: "no parseable input" still counts as "did not detect"

- First idea was a three-way outcome (detected / not detected / no input) with **recall computed
  only over cells where Trivy had input**. **Rejected.** That excludes the cells the tool handles
  worst and then reports success over what is left - the same circularity I removed from section
  5.4.1 on 29.08 (selecting for success, then measuring success). It would inflate recall.
- **Rule fixed instead:** the denominator is **every `malicious_resolved` cell**. A cell where the
  tool was run, the attack had succeeded, and no alert came out is a **miss**, whatever the reason.
- The *reason* is recorded in a **separate column next to the outcome**, not as a different
  outcome, because the two failure modes are architecturally different and the mechanism argument
  needs them apart:

| cell | detected | reason |
|---|---|---|
| `pip_A1a_B1a_B2b_C1c` | no | parsed 9 packages incl. `1.0.3`; no origin field anywhere in the output |
| `pip_A1a_B1a_B2a_C1a` (expected) | no | no parseable input file present in this cell |


## 11. Two fixes applied before running the remaining cells

1. **`--no-progress`** added to every `trivy fs` call. The database download progress bar had
   written progress lines into `_trivy_log.txt`, burying the three lines that
   actually matter.
2. **Both databases baked into the image** at build time, after `USER runner` so the cache lands in
   `/home/runner/.cache/trivy` where the workflow looks for it:

```dockerfile
ENV TRIVY_CACHE_DIR=/home/runner/.cache/trivy

RUN trivy image --download-db-only --no-progress \
    && trivy image --download-java-db-only --no-progress \
    && trivy version --format json
```

   plus `--skip-db-update` on every scan (and `--skip-java-db-update` as well in the Java
   workflow), so no cell ever reaches the network for a database.
   - **Two reasons** 1. Speed: 121 MiB and ~1 minute per cell
     would otherwise be paid in every fresh container of the measurement run. 2. **Reproducibility:**
     the database version becomes part of the image and is pinned like every other component -
     without this, which CVEs a scan reports depends on whatever the database held that day.
   - The Java index database is pinned too, because Java scan 3 (the one that may see the JARs
     under `target/`) needs it to identify them; without it that scan would be identical to scan 1
     and the comparison would be empty.
1. `trivy --version` replaced by **`trivy version --format json`** (file renamed
   `_trivy_version.json`). The plain form records only the binary version; the JSON form also
   records the **database version and when it was built**, so each cell's artifact carries the full
   provenance of what produced its result.
- Checked what is in the cache directory: only the two databases. For `trivy fs` the scan cache
  defaults to memory, so **no scan results are cached on disk** 
  The database affects only which CVEs appear.

## 12. the six hard requirements for Trivy

| | Status after this probe |
|---|---|
| **HR1** integrates and runs in the CI pipeline | **PASS, measured** - for Python. npm and Maven still to run |
| **HR2** all three ecosystems | documentation-level pass; Python now verified by a real run |
| **HR3** reads this project's real files | **PASS** on its own rule - `pylock.<cell_id>.toml` was read |
| **HR4** machine-parseable output | **PASS, measured** - valid JSON and valid CycloneDX |
| **HR5** free, no mandatory account | **PASS, measured**, no account or authentication needed |
| **HR6** version can be pinned | **PASS** - 0.75.0 by tarball + SHA-256, and now the databases too |

Trivy is usable for the main sub-RQ2 experiment. HR1 is complete once the npm and Maven cells have
run.

## important links
- scan a filesystem using trivy: https://trivy.dev/docs/latest/target/filesystem/ -> command:  trivy fs /path/to/project
- adding a `trivy-action` step to your GitHub Actions workflow: https://medium.com/@vincenthartmann/how-to-add-a-security-scan-with-trivy-in-github-actions-8f16642aa82b
- trivy github action: https://github.com/aquasecurity/trivy-action
- trivy CI/CD integration: https://trivy.dev/docs/latest/ecosystem/cicd/  (trivy can integrate in github action / github workflow)  -> **trivy-action**

## Next steps

- [ ] `pip_A1a_B1a_B2a_C1a` - confirm Trivy finds **no input at all** in a Python C1a cell
      (expect `num=0`, empty `Results`).
- [ ] `pip_A1a_B1a_B2b_C1b` - the only Python case that can give scan 3 a real
      declared-vs-installed difference, because `py_dependency/` is actually populated there.
- [ ] `npm_A1a_B1a_B2b_C1c` - **the real test of column 11.** Trivy's npm parser *does* keep the
      `resolved` tarball URL as an external reference, so the CycloneDX output may carry the Nexus
      URL for npm. If it does, column 11 becomes a **per-ecosystem** answer instead of one yes/no,
      and the mechanism argument sharpens: the blindness sits in the Python parser specifically,
      not in Trivy's data model as a whole.
- [ ] `mvn_A1a_B1a_B2b_C1c` - watch whether Trivy resolves `pom.xml` against my Nexus or against
      Maven Central (it reads `<repositories>` from the pom and `<mirrors>` from `settings.xml`),
      and whether the baked HTTP-blocker mirror interferes. `--offline-scan` is the knob if it does.
- [ ] Fill columns 11 and 13 in `theoretical_evaluation_tables.md` for Trivy (lines 203 and 205),
      replacing the "TBD - needs technical evaluation" text with the measured result.
- [ ] Then the same probe round for **super-confused** and **DepGate** (their columns 11 and 13 are
      still TBD too), and fix the input mode per tool before the measurement run.

# 11.10.2026 - sub-RQ2: baked the other two SCA tools into the runner image, integrate DepGate into CI pipelines

**Stand:** super-confused 1.2.0 and DepGate 0.10.0 are now installed in the SCA runner image
together with Trivy 0.75.0, the image is rebuilt and the persistent runner container recreated. Read
DepGate's full documentation and its own CLI source to decide which commands actually fit this
application, and commit + pushed the Trivy + DepGate steps to all three service CI pipelines. The
super-confused pipeline step is **not written yet** (planned for 12.10). The most important result
of the day is not about a tool at all: I checked whether the SCA tools should be allowed to look at
the *installed* directories, and found from my own C1b (package update) evidence that doing so would produce a
false negative.

## 1. super-confused: where the version number actually comes from

- The GitHub repo `6mile/super-confused` has **no releases and no tags**, so there is nothing to pin
  there. The pinnable version comes from the **npm registry** (super-confused is a npm package):

  https://www.npmjs.com/package/super-confused -> `latest = 1.2.0`, published versions `1.0.0`, `1.1.0`, `1.2.0`. 



### change the Dockerfile to install super-confused into image

```dockerfile
ARG SUPER_CONFUSED_VERSION=1.2.0
RUN npm install -g "super-confused@${SUPER_CONFUSED_VERSION}" \
    && npm cache clean --force
```

- **Why `-g`.** The npm page shows only `npm install super-confused`, which installs *locally* into
  `./node_modules` of whatever directory you happen to be in. In an image there is no project
  directory and the binary would not be on `PATH`. `-g` puts it at `/usr/bin/super-confused`.

- **Why the cache clean.** Keeps root's build-time npm cache out of the image.
- Installed **before `USER runner`**, because a global npm install writes to `/usr`.

## 2. DepGate: installed in its own virtual environment to keep experiment environment clean and stable

- Version **0.10.0** from PyPI, requires Python >= 3.10.


### Dockerfile block

```dockerfile
ARG DEPGATE_VERSION=0.10.0
RUN /opt/python/${PYTHON_VERSION}/bin/python3.12 -m venv /opt/depgate \
    && /opt/depgate/bin/pip install --no-cache-dir "depgate==${DEPGATE_VERSION}" \
    && ln -s /opt/depgate/bin/depgate /usr/local/bin/depgate
```

- **Why a separate venv and not just `pip install depgate`.** Those 11 dependencies of DepGate would land
  in the experiment's own Python 3.12.4 `site-packages` - the environment that is itself under
  measurement. **The tool should not alter the environment it measures.** The venv is built from the
  pinned CPython 3.12.4, so no second interpreter enters the image.

- **Why pip inside the venv is not upgraded.** Same reproducibility reason noted on 28.06.2026 for
  the service venv.


## 3. Commands used

```powershell
# rebuild (from inside infrastructure/runner_sca; the trailing "." is the build context)
docker build -t sca-thesis-runner:2.338.0 .

# replace the container; registration token taken from the GitHub UI 

docker run -d --name sca-thesis-runner `
  -e GH_REPO_URL=https://github.com/shirley1997/MS_test_system `
  -e GH_TOKEN=<token> `
  -e RUNNER_NAME=sca-thesis-runner `
  -e RUNNER_LABELS=thesis-runner `
  sca-thesis-runner:2.338.0
```


## 4. What DepGate reads, and what it outputs

Read: README, `docs/supported-package-managers.md`, `docs/analysis-levels.md`,
`docs/output-formats.md`, `docs/configuration.md`, `docs/version-resolution.md`

### Input per service

`-t` names **one** ecosystem per run, so one run per service. Non-recursive by default, which is
what I want: it looks only in the directory given and does not check into `py_dependency/`,
`node_modules/` or `target/`.

| Service | `-t` | What it reads | Which C1 cells it works in |
|---|---|---|---|
| `services/python` | `pypi` | `pyproject.toml` (preferred over `requirements.txt`); no `uv.lock` / `poetry.lock` here, so it falls back to the manifest -> direct dependencies only | **all of them** |
| `services/nodejs` | `npm` | `package-lock.json` when present (direct + transitive), otherwise `package.json` | all |
| `services/java` | `maven` | `pom.xml`, `<dependencies>` only, direct only (DepGate has no Maven lockfile support) | all |

- **That Python row matters: DepGate covers the cells where Trivy is blind.** Trivy needs
  `pylock.*.toml` and therefore only sees Python C1c cells (finding from 10.10); DepGate reads
  `pyproject.toml` and therefore works in C1a, C1b and C1c.
- flag: `-l` (list file), `-d` (directory) and `-p` (single package) are **mutually
  exclusive and exactly one is required**.

### Output field names - CSV and JSON differ

[`docs/output-formats.md`](https://github.com/cognitivegears/depgate/blob/main/docs/output-formats.md) documents both. The names are **not** the same, which matters because the
pipeline parses JSON:

| CSV column | JSON field |
|---|---|
| `Exists on External` (col 3) | `exists` |
| `Risk: Missing` (col 8) | `risk.isMissing` |
| `Version Count` (col 6) | `versionCount` |
| `Risk: Min Versions` (col 10) | `risk.minVersions` |
| `Risk: Too New` (col 11) | `risk.isNew` |
| `Risk: Any Risks` (col 15) | `risk.hasRisk` |

**Use the JSON names in the write-up.** Also noted: `requested_spec` and `resolved_version` appear
as CSV columns 16-17 but are **not** in the documented JSON "Core Fields" list, although they do
appear in `src/cli_io.py`, which serves both exporters. The pilot will show whether they are in the
JSON.

### Exit codes (column 13, measured by design)

From `src/constants.py`: `0` success, `1` file error, `2` connection error, **`3` warnings present**.
Without `--error-on-warnings` DepGate exits `0` even when it flags risks.

### Default thresholds

From `docs/configuration.md`: `min_versions: 2`, `min_release_age_days: 2`, `score_threshold: 0.6`.

## 5. Which commands I chose to use

```bash
depgate scan -t pypi -d . -a compare \
  -o "${depgate_write_file}_compare.json" --loglevel DEBUG
depgate scan -t pypi -d . -a heur --error-on-warnings \
  -o "${depgate_write_file}_heur.json" --loglevel DEBUG
```

(`-t maven` for Java; `-t npm` for Node plus a third run with `--direct-only`.)

- **Two analysis levels, run separately.** `compare` only asks "does this name exist publicly, and
  how many versions does it have". The risk flags are documented under *"Risk Fields (heuristics
  analysis)"*, so `compare` alone does not produce them. Running both shows what a plain presence
  check reports versus what the risk engine adds.
- **`--loglevel DEBUG` for the pilot phase.** The console log is where DepGate states *which manifest it
  picked*. 
- **`--error-on-warnings` on the heuristics run.** This makes column 13 a **measured** value instead
  of a documented claim, and exit `3` is itself a cheap machine-readable "this tool flagged
  something" signal. `continue-on-error: true` on the step means it still cannot fail a cell.
- **`--direct-only`, is an option in npm only.** It forces direct dependencies from `package.json` even when a lock
  file exists. The question it answers: does DepGate see the **resolved 1.0.3** from
  `package-lock.json`, or only the **B2 range** from `package.json`? The docs state the flag has no
  effect for Maven, and the Python side has no lock file DepGate understands, so it is pointless
  there.



### What deps.dev is, and why it is noted

- **deps.dev** is Google's *Open Source Insights* service (`api.deps.dev`): a public database of
  package metadata - versions, licences, dependency graphs, OpenSSF Scorecard results, advisories.
  DepGate queries it to enrich each package before scoring.
- It is **not in the README**; it appears only in `docs/configuration.md` (the `DEPGATE_DEPSDEV_*`
  environment variables) and in the CLI flags (`--depsdev-disable`, `--depsdev-base-url`,
  `--depsdev-cache-ttl`, `--depsdev-max-concurrency`). **It is enabled by default.**
- Two consequences: my attacker packages are brand new, so their deps.dev fields will probably come
  back empty (absence, not error); and it is a **third-party service whose data changes over time**,
  so it is a reproducibility factor for the measurement run. `--depsdev-disable` is the switch.
  **Decision: leave it ON for the pilot** (the point of a pilot is to see full capability) and
  record that it was enabled.
- Related: the heuristics also query the GitHub API for repository signals, rate-limited to 60
  requests/hour without a token. Fine for two packages per cell; worth knowing if repo fields ever
  come back empty.

## 6. Main findin today: letting a tool read the installed directories would create a false negative

I questioned my own earlier rule ("scan declared dependencies, skip installed directories"), because
sub-RQ1 is about the **resolution result** and in some cells packages genuinely are installed. So I
checked the actual evidence of `pip_A1a_B1a_B2b_C1b` instead of arguing about it.

| | what is actually there | version |
|---|---|---|
| `py_dependency/` on disk | written by **phase 1**, which installs `fixed_setup_file/fixed_pyproject.toml` with `xueting-thesis-event-fengfu==1.0.0` **pinned** | **1.0.0** |
| the cell's measured outcome in `results.csv` | **phase 2**, `pip install --dry-run --upgrade`, resolved with the cell's own config | **1.0.3** |

The setup log proves it: `Successfully installed ... xueting-thesis-event-fengfu-1.0.0`. Phase 2 is a
dry run, so it never touches the disk.

- **So a tool pointed at `py_dependency/` would report 1.0.0 - clean - in a cell classified
  `malicious_resolved`.** That is not "a different measurement", it is the **wrong** one, and it
  would manufacture a false negative by construction.
- The other two ecosystems make it moot anyway: every npm command uses `--package-lock-only` or
  `npm ci --dry-run`, so `node_modules/` is **never populated**; and Java's `target/` holds the
  service's own jar, while the resolved dependency jars live in `~/.m2/repository`, outside the
  service directory entirely.
- **Where the resolution result actually lives** is the resolution *record*, not the installed tree:
  `install-report.json`, `package-lock.json`, `pylock.<cell>.toml`, `lockfile.json`. So the real
  axis is not "declared vs installed" but **"resolution record vs installed tree"**, and the record
  is what lines up with sub-RQ1.
- **Cross-ecosystem consequence:** the tools only ever get a resolution record in **Python
  C1c** (`pylock.*.toml`, which Trivy reads) and **npm with a lock file** (`package-lock.json`).
  Java's `pom.xml` is declared-only, and no tool reads third party plugin maven-lockfile's `lockfile.json`.
- **Keep Trivy's scan 3 anyway.** In `pip_A1a_B1a_B2b_C1b`, scan 1 will find nothing (no lock file)
  while scan 3 will report **1.0.0** out of `py_dependency/*.dist-info/METADATA`. That is this whole
  argument demonstrated with evidence instead of asserted - much stronger in the thesis. Run that
  cell deliberately.
- **Note on the earlier rejection.** The 08.10 entry (section 6) rejected pointing Syft at installed
  metadata. That was an **HR3** argument - a tool must not be allowed to pass "reads this project's
  manifests" by being pointed at installed metadata instead. It still stands, and it is a *different*
  point from this one.

## 7. DepGate does read the manifests

[Supported Package Managers](https://github.com/cognitivegears/depgate/blob/main/docs/supported-package-managers.md)
- **It DOES read the cell's manifest:** `pyproject.toml` / `requirements.txt`, `package.json` +
  `package-lock.json`, `pom.xml`. Those files carry variable **B2**, the version specifier, and
  `requested_spec` is exactly that value.
    requested_spec meaning: docs/output-formats.md:55 : requested_spec "Original requested version/range"
- **It does NOT read the registry configuration:** `.npmrc`, `pip.conf`, and the pom's
  `<repositories>` are never consulted. Those are variables **A** and **B1**.
- Also a correction to myself: the registry endpoints are **not hard-coded**.
  `docs/configuration.md` documents `registry.pypi_base_url`, `registry.npm_base_url`,
  `registry.maven_search_url` in a `depgate.yml`, overridable by env vars and CLI.
- **But they must stay pointed at the public registry.** The DC check works by asking "is this name
  absent from the *public* registry, i.e. claimable by an attacker". -> use default settings

**So the real limitation is not configurability.** It is that DepGate checks **one registry at a
time** and has no concept of two registries with a resolution order between them - which is exactly
variables **A** and **B1**, the two that sub-RQ1 showed decide the outcome. It reads B2 and is
structurally blind to A and B1.

- **This is testable, not just arguable:** compare DepGate's `resolved_version` against
  `results.csv`'s `pk1_version` across cells with different `A` values. Where they agree it is
  coincidence (the cell resolved from public anyway); 

## 8. Finding or tool characteristic? And no, the application is not changed

- It is a **characteristic** of the tool. It becomes a **finding** only when measured against my
  research question. The difference matters for how it is written:
  - Do **not** present "DepGate checks only one registry" as a discovery - it is in its own
    documentation and a reviewer who reads the docs will say so.
  - **Do** present it as: *because* DepGate checks one registry and has no resolution-order concept,
    it cannot distinguish an `A1a` cell from an `A3` cell, **and here is the measured consequence**.
    The characteristic is the premise; my evidence is the finding.
- **The test application is not modified to fit any tool.** Two reasons:
  1. My own screening rule says so, and that rule is what makes the failures of Syft, OpenSCA and
     Dependency-Check legitimate findings rather than setup mistakes. Breaking it for DepGate would
     retroactively undermine those.
  2. Sub-RQ2's whole value is that it scans **the same application in the same cells** that produced
     sub-RQ1's results. Change the application and the two halves no longer refer to the same object.
- Short version: **if a tool cannot see something, that is data about the tool.**



## 11. Still to write: the super-confused pipeline step

Planned for 12.10. Design already fixed:

- It writes JSON to **stdout** and has no `-o` flag, so stdout is redirected to the output file and
  stderr appended to the log. No pipe on the tool call, so plain `$?` is the correct exit code here.
- Targets named explicitly per ecosystem: `pyproject.toml` / `pom.xml`, and for npm **both**
  `package.json` and `package-lock.json`, with a `[ -f package-lock.json ]` guard because that file
  is deliberately removed on the C1b and C1c failure paths.



## Next steps

- [ ] Fix `-a heuri` -> `-a heur` in all three workflows, rename `_heuri.json` -> `_heur.json`
      (step + upload list), and add the missing DepGate entries to the nodejs upload list.
- [ ] Write the super-confused step in all three workflows, including the positive control.
- [ ] Then run the pilot cells with `run_sca = on`:
      - `pip_A1a_B1a_B2b_C1c` - all three tools on a known `malicious_resolved` cell
      - `pip_A1a_B1a_B2a_C1a` - expect Trivy to find no input; DepGate should still read
        `pyproject.toml`
      - `pip_A1a_B1a_B2b_C1b` - the declared-vs-installed demonstration (Trivy scan 3 should report
        **1.0.0** from `py_dependency/` while the cell's real outcome is 1.0.3)
      - `npm_A1a_B1a_B2b_C1c` - the real test of column 11, and of DepGate's lock file vs manifest
        input mode
      - `mvn_A1a_B1a_B2b_C1c`
- [ ] Per cell, record for each tool: did it run, did it name `1.0.3`, is any origin URL present,
      what exit code, and did the positive control fire.
- [ ] Compare DepGate's `resolved_version` against `results.csv`'s `pk1_version` across different
      `A` values, to show the A/B1 blindness empirically.
- [ ] Fill columns 11 and 13 in `theoretical_evaluation_tables.md` for all three tools.


# 12.10.2026 - sub-RQ2: integrated tool super-confused, fixed error in pipeline

**Stand:** all three selected SCA tools are now integrated into all three service CI pipelines. the `-a heuri` typo and the missing nodejs
upload entries are fixed, and the files are reviewed and ready to push. The important result of the day is **not** a tool detail: reading super-confused's source
and DepCheck's output format showed that **purpose-built dependency-confusion tools test for the
attack's precondition, not for the attack**, which means they may be silent in exactly the
cells my experiment measures. it is the finding.


## 2. Two defects from yesterday's push, fixed

1. **`-a heuri` is not a valid analysis level.** DepGate's `src/constants.py` has
   `LEVELS = ["compare", "comp", "heuristics", "heur", "policy", "pol", "linked"]`. Fixed
   to `-a heur` in all three workflows.



## 3. Decision: transitive dependencies of the tools are NOT pinned

- **The image is the frozen artifact.** It is built once and every cell runs against that same image,
  so transitive versions cannot drift *between* cells. Whatever variation exists is identical across
  the entire experiment.
- **Only one tool even has a dependency tree.** Trivy, Maven, Node, the runner binary are single
  pinned downloads with SHA-256 checks; CPython is built from a pinned source tarball;
  **super-confused has zero dependencies**. DepGate is the only one with range-declared dependencies.
- **And it is already recorded.** The `/opt/depgate/bin/pip freeze` line in the DepGate step writes
  the actual resolved set into every cell's artifact.
- The only thing not guaranteed is that someone rebuilding from the Dockerfile in two years gets
  byte-identical DepGate dependencies -> **one sentence in Limitations**

Terminology note I had wrong: **`pip freeze` does not record pip's own version.** It lists the
*installed packages* with `==` versions, and by default excludes pip itself (`pip freeze --all`
would include it). 

## 4. super-confused: checked the source file 

### Why explicit file targets, not a directory scan

My first instinct was `super-confused --json .`, i.e. the directory scan. However in source file:

```js
if (stats.isDirectory() && !entry.startsWith('.') && entry !== 'node_modules') {
    await this.scanDirectory(fullPath);     // recurses
}
```

- `scanDirectory` **recurses**, and its exclusion list is hardcoded: directories starting with `.`
  plus the directorz name `node_modules`. It does **not** exclude other directories like `py_dependency`, `target` or
  `build`. So a directory scan may deliver the wrong or incorrect result.
- scan `package.json` and `package-lock.json` as **separate runs** - the
  same direct-vs-transitive question `--direct-only` answers for DepGate.
- In practice the two would mostly agree, because `supportedFiles` only matches known filenames and
  `py_dependency/` contains only `<pkg>/` and `<pkg>-1.0.0.dist-info/` directories - no
  `pyproject.toml`, no `requirements.txt`. So the directory scan was **dropped**

###  no findings means a empty file

```js
if (vulnerabilities.length > 0) {
    console.log(JSON.stringify(output, null, 2));
}
return;
```

- In `--json` mode, **when it finds nothing it prints nothing at all** - not `[]`, not `{}`. The
  result file will be **0 bytes**.
- A 0-byte file is indistinguishable from "the binary was missing", "the redirect failed" or "it
  crashed". `if-no-files-found: warn` does not help, because the file exists and is merely empty.
- **Therefore the positive control is mandatory, not optional.** It is the evidence the tool
  works properly. the step ends with `ls -l`: file **sizes** are the evidence here.


### Two table columns answerable from the source, before running pilot cells

- **Column 11 (origin URL): NO, by construction.** The JSON holds only
  `{ "<package name>": "<version>" }` pairs. No registry field, no URL field exists in the schema.
- **Column 13 (exit code): does not break the build.** `process.exit(1)` fires only for a missing path
  or a scan error; findings never change the exit code. And `main().catch(console.error)` means even
  an unhandled rejection exits 0.
- Its registries are **hardcoded** - `registry.npmjs.org`, `pypi.org/pypi/`, `search.maven.org` +
  `repo1.maven.org`. 

### The step design

super-confused has **no `-o` flag**: its result goes to **stdout**. So:

```bash
super-confused --json pyproject.toml \
  2>> "${sc_write_file}_log.txt" | tee "${sc_write_file}.json"
echo "scan 1 exit code: ${PIPESTATUS[0]}" | tee -a "${sc_write_file}_log.txt"
```

- stdout -> the result file **and** the GitHub Actions console (via `tee`)
- stderr -> the log file
- `${PIPESTATUS[0]}` -> the tool's real exit code
- **The one difference that must stay: `2>>`, NOT `2>&1`.** For Trivy and DepGate stdout is just
  chatter and the result goes to `-o`, so folding stderr in does not have huge influence. Here **stdout is the data we need to check**,
  and `2>&1 | tee file` would mix error messages into the JSON and produce a file the parser can't read.

### Why two output files per tool and not one

- **`.json`** holds *only* stdout - the result - so it stays machine-parseable.
- **`_log.txt`** holds information about which scan ran, stderr, the exit code, the `ls -l`
  results. The JSON result is **not** in it (`tee` sends stdout to the `.json` file and to the
  *browser* workflow log, not into `_log.txt`).
- delete log.txt or delete .json file: only `.json` loses the exit code, stderr, and any way to
  interpret an empty result; only `_log.txt` loses a parseable result file.

### command: `npm ls -g --depth=0 super-confused` 

 the version record, the equivalent of
`trivy version --format json` and `pip freeze` in the other two SCA tool step. `ls` lists installed
packages, `-g` looks in the global location where `npm install -g` put it, `--depth=0` prints top
level only. show the version of installed super-confused



## 5. finding: DC tools test the attack's precondition, not the attack

### What I noticed

DepCheck's own output reads:

> `[!] VULNERABLE - Not found on public registry:` ... *"An attacker **can** register these on the
> public npm registry with a higher version -> Remote Code Execution!"*

The DC-claimed Tool on github such as `confused`, `dustilock`, `snync`, super-confused, DepCheck and DepGate at `compare`
level all implement the **same primitive**:

> for each dependency name in the manifest, query the public registry; if the name is **absent**,
> report it as hijackable.

That is a **precondition test**. It detects *exposure* (the attack is possible), **not** *compromise*
(the attack happened).

### The inversion, stated precisely

The detection condition is "name absent from the public registry". I published version 1.0.3 of
every internal name, so **the condition is false in every cell of my matrix** and the tool is
silent. A tool's detection capability is therefore **inversely related to attack progress**: it
fires before the attack and goes quiet the moment the attack succeeds.

That is not a bug in the tools and not a mistake in my setup. It is what the primitive does.



- **"The experiment is not invalid"** - It is well defined either way: run the tools against pipeline
  states that sub-RQ1 showed to be compromised, and record what they report. A null result is a
  result, *provided* the tool actually works properly (which is what the positive control establishes).
- **"The experiment measures something other than I assumed"**


### What is still empirical

- **DepGate's heuristics level.** `risk.minVersions`, `risk.isNew`, trust-score and provenance
  regression are **not** precondition tests. My attacker packages have exactly one published
  version, recent, unsigned. If `minVersions` fires, DepGate flags the attack - **through a
  different mechanism than the one it advertises.** Testable tomorrow.
- **Input mode** per tool and ecosystem: whether a tool reads the file carrying the *resolved*
  version (lock file) or only the declared range.
- **Trivy's output model** - already measured on 10.10: no origin field in either format.
- **Whether each tool runs at all** (HR1) - which is what the positive control is for.



1. **It answers the research question with a mechanism instead of a rate.** *The tools that claim DC
   detection test for the attack's precondition, so they are structurally blind to a realized
   substitution; the general-purpose tool has no origin field in its output model and no advisory
   exists for an attacker package, so it is blind for a different reason.* Both claims rest on tool
   architecture and are verifiable from source

2. **It turns the answer into a capability taxonomy** 

| | what it can see | why it misses my attack |
|---|---|---|
| DC-specific, name-existence check | *exposure*: an internal name nobody has claimed | the name is claimed now, so the check inverts to "safe" |
| DC-specific, heuristic signals | version-count / age / provenance anomalies | open - may actually fire, by a different mechanism than claimed |
| general-purpose SCA (Trivy) | package name + version matched against advisories | no origin field in the output; no advisory exists for the attacker package |

1. Sub-RQ1 established *which pipeline
   configurations cause an internal name to resolve from a public source*. Sub-RQ2 now establishes
   that what these tools actually reported. The gap is not "tools are bad" -
   it is that the available tooling checks a precondition and does not checks resolved origin. need to consider classification logic.

### Decisions taken

- **Do not change the application, and do not change the research question.** 

- **Report per tool: outcome + reason + the signal it tested**

- **Record the tool scan logic as a finding**


## 6. Are super-confused and DepGate the only DC-specific tools that passed? No - there is a third

From `sca_tool_screening_v2.xlsx`, column J (hard-requirement verdict), the Source-B tools that
reached Stage 2:

| Tool | Verdict | Why it is / is not in the final 3 |
|---|---|---|
| `cognitivegears/depgate` | **PASS**, no caveats | selected |
| `6mile/super-confused` | **PASS**, 2 caveats | selected |
| `BlackHatExploitation/depcheck` | **PARTIAL PASS** | passes HR2-HR5 and reads all three of my manifests. Lost on **HR6**: no releases, no tags, not on PyPI or npm, so pinnable only by git commit SHA. Also ships `--exploit`, which publishes malicious packages to real registries, and has no licence file |

And **two more** whose HR3 was recorded as **"not verifiable"** rather than failed, because their
READMEs never name the manifest filenames: `D3Ext/dep-scanner` and `synacktiv/DepFuzzer`. Their HR3
can only be settled by *running* them - DepFuzzer has **96 stars** against super-confused's 10.

So if super-confused fails the technical evaluation there are documented fallbacks, and the plan
already contains a pre-stated tie-break (rank survivors by maintenance signal and adoption, record
the cut-off applied).


(expected) super-confused prints nothing when clean. But **"reports nothing" is the measurement.** the gate
for the final 3 is **integration feasibility only**.

- It **runs**, produces a parseable (even empty) result, and the positive control is used -> **it
  stays**, and "no DC alert in any cell" is the result.
- It **fails HR1** - will not run, or output cannot be parsed at all -> *then* replace it from
  DepCheck / dep-scanner / DepFuzzer, and record why.

among DC-claiming tools on GitHub that support all three
ecosystems and read specific manifests, this is what the field actually offers. That is a result about
the state of DC tooling, not a weakness in the selection.

## 7. Pipeline review before the push

Reviewed all three workflow files. All three parse as valid YAML; all three SCA steps are guarded by
`if: inputs.run_sca == 'on'` with `continue-on-error: true` and the correct `working-directory`. some small errors are fixed.


## Next steps

- [ ] run the pilot cells with `run_sca = on`, in this order:
      1. `pip_A1a_B1a_B2b_C1c` - all three tools on a known `malicious_resolved` cell
      2. `npm_A1a_B1a_B2b_C1c` 
      3. `pip_A1a_B1a_B2b_C1b` - the declared-vs-installed demonstration (Trivy scan 3 should report
         **1.0.0** out of `py_dependency/` while the cell's real outcome is 1.0.3)
      4. `pip_A1a_B1a_B2a_C1a` 
      5. `mvn_A1a_B1a_B2b_C1c`

- [ ] Record, per tool per cell: did it run, did it name `1.0.3`, is any origin URL present, what
      exit code, which signal did it test, and did the positive control fire.
- [ ] Write up the inversion (section 5) as a named finding, with the capability taxonomy table.


# 13.10.2026 - sub-RQ2: installed all SCA tools locally on Windows, ran the pipeline commands by hand, inspected output file / terminal log

**Stand:** installed Trivy, DepGate, super-confused (and additionally DepCheck, which is only a
fallback SCA tool candidate) on Windows machine, at the **same versions as in the runner image**, in a
directory outside of github repo -> didn't change my development environment. Then I ran the
commands for scan by hand, against `services/python`. test locally makes output of tools easier to see and does not need to run pipeline.




## 2. local directory for installed SCA tools

Scan outputs go into `sub-RQ2_tool_selection/tool_scan_pilot/`. 

- **DepGate went into its own venv**, so that the experiment envrionment keep stable. I call
  `depgate_venv/Scripts/pip.exe` by full path. 
- **`export TRIVY_CACHE_DIR=...`** to fix the trivy db download directory. The variable lives in one terminal window and
  disappears when I close it. 

Isolation check: `npm ls -g --depth=0` does not list super-confused, my normal Python has
no `depgate` (because it is installed in its own venv), and `where trivy depgate super-confused` finds nothing.

### Setup file, so variables are not empty

I lost time three separate times to the same bug: a variable was empty (didn't set), so a path collapsed. 

Fix - one file, sourced at the start of every new terminal:

```bash
# D:\Master_Winfo\MA_Supply_chain_security\sca_tool_install\env.sh
SCA=/d/Master_Winfo/MA_Supply_chain_security/sca_tool_install
SCAW="D:/Master_Winfo/MA_Supply_chain_security/sca_tool_install"
REPO=/d/Master_Winfo/MA_Supply_chain_security/MS_test_system
TRIVY="$SCA/trivy/trivy/trivy.exe"
DEPGATE="$SCA/depgate_venv/Scripts/depgate.exe"
SC="$SCA/superconfused/node_modules/super-confused/super-confused.js"
OUT="$REPO/sub-RQ2_tool_selection/tool_scan_pilot"
export TRIVY_CACHE_DIR="$SCAW/trivy_cache"
```

before start running scan commands:
```bash
source /d/Master_Winfo/MA_Supply_chain_security/sca_tool_install/env.sh
```

`source` runs it **inside** the current shell so the variables stay; 


### Two Windows-only details

  - Git Bash automatically rewrites `/d/...` into `D:\...` when
  it passes a path as a **command argument**, but **not** for environment variables. So the
  `--cache-dir` flag takes `$SCA` (`/d/...` form) while `TRIVY_CACHE_DIR` needs `$SCAW` (`D:/...`
  form). In the Ubuntu container this problem does not exist.
- **`./trivy.exe` works, `trivy.exe` does not.** 

## 3. Installing the tools - commands and version pins

### 3.1 Trivy 0.75.0

Same version is used in runner container. `ARG TRIVY_VERSION=0.75.0` (in Dockerfile: infrastructure\runner_sca\Dockerfile). 

```bash
curl -fsSL -o "$SCA/trivy/trivy.zip" \
  https://github.com/aquasecurity/trivy/releases/download/v0.75.0/trivy_0.75.0_windows-64bit.zip


unzip trivy.zip -d trivy
./trivy.exe --version        # -> Version: 0.75.0
```
- Trivy is a **single .exe**: no installer, no registry entry, nothing on `PATH`.

Then fix the vulnerability database (otherwise the db updated itself and may affect the experiment result) (already implemented in Dockerfile):

```bash
TRIVY_CACHE_DIR="$SCAW/trivy_cache"
"$TRIVY" --cache-dir $TRIVY_CACHE_DIR image --download-db-only
```

Output:

```
INFO [vulndb] Downloading artifact...  repo="mirror.gcr.io/aquasec/trivy-db:2"
INFO [vulndb] Artifact successfully downloaded
```

- the cache directory holds `db/trivy.db` and `db/metadata.json`.

- I did **not** download the Java DB yet. It is only used to identify `.jar` files by hash; I scan
  `pom.xml`, which is a text file.
- The local DB is from **today**, the image's DB was baked on 11.10. Same binary, different DB -> the
  **package list** is comparable, the **CVE list** is not. Local output is for understanding, not for
  thesis numbers.

the pipeline steps pass **no** cache flag used, they rely on the `ENV`. 


### 3.2 DepGate 0.10.0

Same version as `ARG DEPGATE_VERSION=0.10.0` (in Dockerfile.

```bash
py -3.12 -m venv "$SCA/depgate_venv"
"$SCA/depgate_venv/Scripts/pip.exe" install --index-url https://pypi.org/simple "depgate==0.10.0"
"$SCA/depgate_venv/Scripts/pip.exe" show depgate | head -2    # -> Version: 0.10.0
```

- **`--index-url` is necessary. so pip can reach pypi to get the package** My laptop's pip is  configured to use my Nexus group
  repo, so the venv inherited it and tried
  `http://admin:****@localhost:8081/repository/pypi-group-public-first/simple/`, which failed with
  (connection refused) because the Nexus container was not running. 
- **DepGate has no `--version` flag.** Its CLI goes straight into the `scan` sub-command, so
  `depgate --version` prints the `scan` usage. The version check needs to use pip in depgate's own venv.

### 3.3 super-confused 1.2.0

Same version as `ARG SUPER_CONFUSED_VERSION=1.2.0` (Dockerfile).

```bash
npm install --prefix "$SCA/superconfused" super-confused@1.2.0
npm ls --prefix "$SCA/superconfused" --depth=0        # -> super-confused@1.2.0
SC="$SCA/superconfused/node_modules/super-confused/super-confused.js"
"$SC"
```

- `--prefix` tells npm to treat that folder as the project root; it creates `node_modules` and a
  `package-lock.json` there 
- I call the `.js` file directly. (./super-confused.js)
- Its usage line is the whole configuration surface:

```
Usage: super-confused [--json] <path|url>
```


### 3.4 DepCheck (extra - fallback candidate, not one of the selected three)

https://github.com/BlackHatExploitation/depcheck

Not installed in the runner, not in the pipelines. I ran it locally first , to see what the third
DC-specific candidate from the screening table actually does.

```bash
curl -fsSL -o "$SCA/depcheck/depcheck.py" \
  https://raw.githubusercontent.com/BlackHatExploitation/depcheck/3c55d2905c8f1852e98e8ba96f38fbd9a3ed91b0/depcheck.py

python -I "$SCA/depcheck/depcheck.py" --version
```

- The git repo of this tool does not have ** releases and no tags**, so a **commit SHA is the only way to pin it** - this is
  exactly the HR6 problem recorded in the screening table. I pinned by SHA
- Repo facts as of today: language Python, 3 files (`depcheck.py`, `web.py`, `README.md`),
 
- **Safety:** this tool has an offensive part. `--exploit` **publishes malicious packages to real
  public registries**; there are also `--callback`, `--npm-token`, `--pypi-token`, `--github-token`,
  `--save-creds`, and a `--web` UI 
  **I only used the read-only scan.**
- `python -I` = isolated mode, so Python cannot import modules out of the current folder 
- 


## 4. Reference links collected today

Trivy (the README and the docs only explain part of the flags; the **complete** flag list per
sub-command is under References -> Configuration -> CLI):

- scan filesystem: https://trivy.dev/docs/latest/target/filesystem/
- scan code repository: https://trivy.dev/docs/latest/target/repository/
- **all flags of `trivy fs`**: https://trivy.dev/docs/latest/references/configuration/cli/trivy_filesystem/
- **same page pinned to my version 0.75.0** :
  https://github.com/aquasecurity/trivy/blob/v0.75.0/docs/guide/references/configuration/cli/trivy_filesystem.md
- skipping files and directories (`--skip-dirs`, `--skip-files`, glob syntax):
  https://trivy.dev/docs/latest/configuration/skipping/
- SBOM formats (`cyclonedx`, `spdx`, `spdx-json`): https://trivy.dev/docs/latest/supply-chain/sbom/
- trivy vulnerability database: https://trivy.dev/docs/latest/configuration/db/
- release assets + checksums file: https://github.com/aquasecurity/trivy/releases/tag/v0.75.0

DepGate:

- analysis levels and scoring (two analysis level used in scan command): https://github.com/cognitivegears/depgate/blob/main/docs/analysis-levels.md
- package metadata (how I counted its 11 declared dependencies):
  https://pypi.org/pypi/depgate/0.10.0/json -> field `info.requires_dist`

super-confused:

- npm page: https://www.npmjs.com/package/super-confused


DepCheck:

- the pinned commit: https://github.com/BlackHatExploitation/depcheck/commit/3c55d2905c8f1852e98e8ba96f38fbd9a3ed91b0

**the flag reference can be checked using the tool** - `trivy fs --help`, `depgate scan --help`,
`python -I depcheck.py --help` 

## 5. Trivy - the pipeline command, flag by flag

The exact flag list from the v0.75.0 docs (and from `trivy fs --help`):

```
      --list-all-pkgs        output all packages in the JSON report regardless of vulnerability (default true)
      --skip-dirs strings    specify the directories or glob patterns to skip
      --scanners strings     comma-separated list of what security issues to detect
                             (allowed values: vuln,misconfig,secret,license) (default [vuln,secret])
      --skip-db-update       skip updating vulnerability database
      --no-progress          suppress progress bar
  -f, --format string        format (json / SBOM / csv etc.)
  -o, --output string        output file name
```

selected flag in my pipeline for obtaining a clear scanning output:

| flag | why |
|---|---|
| `fs .` | scan the folder as it is on disk |
| `--skip-dirs py_dependency .venv build` | exclude the *installed* packages, avoid incorrect output, keep the *declared/resolved* record |
| `--scanners vuln` | the default is `[vuln,secret]`, so this switches the **secret** scanner off. Without it Trivy would also search for leaked credentials, not relevant for my research|
| `--list-all-pkgs` | list **every** package, not only vulnerable ones. It is `(default true)` in 0.75.0, but I pass it explicitly |
| `--no-progress` | removes the progress bar only |
| `--skip-db-update` | use the DB baked into the image, so the db version is fixed, does not affect the output|
| `--format` + `--output` | `--format` makes it machine-readable, `--output` sends the result to a **clean file** while log messages go to the screen. Without `--output`, the JSON would be printed mixed with log lines and `tee` would save a file no parser can read |
| `2>&1 \| tee` | put stderr into the log file. Safe **because** the result went to `--output`, not to stdout |
| `${PIPESTATUS[0]}` | the exit code of **trivy**, not of `tee`. `$?` after a pipe returns tee's status, always 0 |


**Why `trivy fs` and not `trivy repo`:** `trivy repo <url>` clones a git repository. The files that
matter in each cell (`pylock.<cell_id>.toml`, `package-lock.json`, the generated `pyproject.toml`)
are created **during the job** and are not committed, so `trivy repo` pointed at my GitHub URL would
scan the committed source and measure the wrong thing.

**Why not scan a single file** (`trivy fs <file>` is possible): the filename is not known in advance,
C1a cells have no lock file, C1c Python cells have `pylock.<cell_id>.toml` with a changing name, and
the npm failure paths delete `package-lock.json`. `trivy fs .` scan a whole project/ service and adapts by itself; 

**Why three separate scans for three formats:** `--format` takes **one** value. One run = one format.
Scans 1-4 are not redundant, they are the same scan with different formats and produce the output files I want to compare.

### What I ran

```bash
cd "$REPO/services/python"
PFX="$OUT/python_trivy"
FLAGS="--scanners vuln --list-all-pkgs --no-progress --skip-db-update"
SKIP="--skip-dirs py_dependency --skip-dirs .venv --skip-dirs build"

"$TRIVY" fs . $SKIP $FLAGS --format json       --output "${PFX}_declared.json"      2>&1 | tee    "${PFX}_log.txt"
"$TRIVY" fs . $SKIP $FLAGS --format cyclonedx  --output "${PFX}_declared_cdx.json"  2>&1 | tee -a "${PFX}_log.txt"
"$TRIVY" fs . $SKIP $FLAGS --format spdx-json  --output "${PFX}_declared_spdx.json" 2>&1 | tee -a "${PFX}_log.txt"
"$TRIVY" fs .       $FLAGS --format json       --output "${PFX}_all.json"           2>&1 | tee -a "${PFX}_log.txt"
```

Putting the flags in `$FLAGS` and `$SKIP` makes it impossible to give one scan a
different flag set by accident. Only **one** thing differs per scan - the format in 1-3, the
directory scope in 4 (no skip dirs, the installed package is also be checked).


### Output files
sub-RQ2_tool_selection\tool_scan_pilot

```
python_trivy_declared.json        
python_trivy_declared.cdx.json    
python_trivy_declared.spdx.json   
python_trivy_all.json             
python_trivy_log.txt
```

### Observations

**(a) What Trivy took as input.** The log says `Number of language-specific files num=2` and the JSON
has two `Results` entries: `pylock.test.toml` (16 packages) and `pylock.test3.toml` (15). Those are
two leftover test lock files from August that still sit in `services/python`.

`pyproject.toml` is **not** counted - if it were a target, the number would be 3. But it **was
read **: my `pyproject.toml` declares exactly `Flask`, `xueting-thesis-event-fengfu` and
`xueting-thesis-service-zhuanfa`, and those are exactly the three packages Trivy marks
`"Relationship": "direct"` while the other 12 are `indirect`. That direct/indirect split can only
come from `pyproject.toml`. So for Python, `pyproject.toml` is a **helper**, not a target -
consistent with what I read in the source on 10.10 (`pylockAnalyzer.PostAnalyze()` loops over lock
files only).

**(b) The complete record of one attacker package in JSON:**

```json
{ "ID": "xueting-thesis-event-fengfu@1.0.0",
  "Name": "xueting-thesis-event-fengfu",
  "Identifier": { "PURL": "pkg:pypi/xueting-thesis-event-fengfu@1.0.0", "UID": "27afb2f323f61120" },
  "Version": "1.0.0", "Relationship": "direct", "AnalyzedBy": "pylock" }
```

No origin field of the package.

**(c) CycloneDX 1.7** - 33 components, and **0 of them have an `externalReferences` array**. Each
component carries only `purl` plus two Trivy-internal properties (`aquasecurity:trivy:PkgID`,
`aquasecurity:trivy:PkgType`).

**(d) SPDX 2.3** - 34 packages:

```json
"supplier": "NOASSERTION",
"downloadLocation": "NONE",
"externalRefs": [{ "referenceType": "purl",
                   "referenceLocator": "pkg:pypi/xueting-thesis-event-fengfu@1.0.0" }]
```

`downloadLocation: "NONE"` for **all 34**. (Trivy's own SBOM documentation shows the same `"NONE"` in
its example output.)

**(e) The JSON file has no package origin URL. The output records
in detail where to *read about* a vulnerability

**(f) The origin was in the input and was discarded.** `pylock.test.toml` contains lins:

```toml
url = "http://localhost:8081/repository/pypi-group-public-first/packages/blinker/1.9.0/blinker-1.9.0-py3-none-any.whl"
```

Trivy parsed that file successfully (every name and version is correct) and did not carry the `url`
into any of the three outputs.

**(g) Nexus was stopped for the whole session.** All scans completed normally, which shows that
`trivy fs` makes **no registry calls**, it reads files and the local DB. So "the registry was
unreachable" cannot explain the missing URL. The only possible source was the file on disk.

**(h) Why Trivy's own documentation shows a `repository_url` and mine does not.** The doc example

```
pkg:oci/alpine@sha256:19b4...?arch=amd64&repository_url=index.docker.io%2Flibrary%2Falpine
```

is the purl of the **container image** - the artifact Trivy itself pulled from a registry. The
packages *inside* that image (`pkg:apk/alpine/zlib@1.2.11-r3?distro=3.15.0`) have **no**
`repository_url` either. So Trivy records an origin only for what it downloaded itself; for language
packages it reads a file and does not fetches anything. 

**(i) Scan 4 (no `--skip-dirs`) has byte-identical file to scan 1**, apart from `ReportID` and
`CreatedAt` - while `services/python/.venv/Lib/site-packages` contains **39** `*.dist-info/METADATA`
files, and both scans logged `num=2`. So in this local folder Trivy did not read the installed
packages. **This is not transferable to the cells**: `.venv` is hidden and nests under
`Lib/site-packages`, while `py_dependency/` is a visible, flat `pip install --target` folder. It has
to be decided in the pilot.


**(k) From the SBOM documentation:** *"`--format cyclonedx` disables security scanning"* - to include
vulnerabilities, `--scanners vuln` must be added. With it, my CycloneDX file contains both the
components **and** a `vulnerabilities` section with 5 entries; the SPDX file has only `packages` and
`relationships` and **no vulnerability section at all** (because i didn't add option `--scanners vuln`).


## 6. DepGate - the pipeline command, flag by flag

| flag | why |
|---|---|
| `scan` | the only sub-command |
| `-t pypi` | which **public** registry to query (`npm` / `maven` in the other two pipelines) |
| `-d .` | read manifests from this directory |
| `-a compare` / `-a heur` | the two analysis levels I compare |
| `-o <file>` | results as JSON - same role as Trivy's `--output` |
| `--loglevel DEBUG` | prints the actual HTTP requests, so I can see which services it contacts |
| `--error-on-warnings` | turns a finding into a non-zero exit code |

### What I ran

```bash
cd "$REPO/services/python"
DPFX="$OUT/python_depgate"

"$DEPGATE" scan -t pypi -d . -a compare \
  -o "${DPFX}_compare.json" --loglevel DEBUG 2>&1 | tee "${DPFX}_log.txt"
echo "depgate scan 1 exit code: ${PIPESTATUS[0]}" | tee -a "${DPFX}_log.txt"

"$DEPGATE" scan -t pypi -d . -a heur --error-on-warnings \
  -o "${DPFX}_heur.json" --loglevel DEBUG 2>&1 | tee -a "${DPFX}_log.txt"
echo "depgate scan 2 exit code: ${PIPESTATUS[0]}" | tee -a "${DPFX}_log.txt"
```

Each scan must be pasted **together with its `echo`**: `PIPESTATUS` is overwritten by the very next
command. I ran one of them separately by mistake and got `exit: 127` ("command not found") although
the scan had worked perfectly - the `echo` had reported some other command's status. In the pipeline
this will not happen because the `echo` is on the next line.

### Observations

**(a) Which input it used:**

```
discovered_files ecosystem=pypi manifests=['.\pyproject.toml'] lockfiles=[]
selection manifest=.\pyproject.toml lockfile=None rationale=no lockfile
```

`lockfiles=[]` - the two `pylock.test*.toml` files are in the same folder and DepGate does not
recognise PEP 751 lock files at all. In this run it read the **declared** manifest, not the
resolution record. (Trivy did the opposite: only the lock files, not `pyproject.toml` on its own.)

**(b) Which services it contacted** (counted from the DEBUG log):

sub-RQ2_tool_selection\tool_scan_pilot\python_depgate_log.txt

```
24  https://pypi.org
12  https://api.github.com
 9  https://pypistats.org
 6  https://api.deps.dev
```

`localhost`, `pip.ini` and `nexus` appear **0 times**. DepGate didn't looks at my registry
configuration. Nexus container is not started the whole time and it did not care.

Two of those services (`pypistats.org`, `api.deps.dev`) are not mentioned in the README. Note also
that running DepGate sends my **internal package names** to four third-party services, and that
`[WARNING] pypistats fetch failed; skipping weekly downloads` appeared in this run - one enrichment
source failed, so the data is assembled from whatever answers that day.

**(c) `-a compare` output** - 3 packages (the direct ones only):

```json
"packageName": "xueting-thesis-event-fengfu",
"exists": true,  "versionCount": 1,
"resolved_version": "1.0.3",  "requested_spec": null,  "resolution_mode": "latest",
"risk": { "hasRisk": false, "isMissing": false, "hasLowScore": null, "minVersions": null, "isNew": null }
```

- `exists: true`, `isMissing: false` - the warning "this name is unclaimed, an attacker could take it"
  is **off**, because attacker packages with version 1.0.3 of these names is published on public PyPI.
- Every heuristic field is `null`: `-a compare` does **not** evaluate the heuristics. That is what
  `-a heur` is for.
- Exit code **0**.

**(d) `resolved_version` does not mean what the name suggests.** My `pyproject.toml` declares
`Flask==3.1.1` and `xueting-thesis-event-fengfu==1.0.0`. DepGate reports `3.1.3` and `1.0.3`, with
`requested_spec: null` and `resolution_mode: "latest"`. The string `1.0.0` appears **0 times** in the
entire DEBUG log. So `resolved_version` = "the newest version on the public registry", not "the
version this project would install". flask is the clearest case: a perfectly ordinary public package,
declared `==3.1.1`, reported `3.1.3`.

This **contradicts** what I wrote in section 6 of `docs/summary_sca_test.md`, where I said DepGate
sees variable **B2** through `requested_spec`. In this run it did not, at either analysis level.

**(e) `-a heur` output:**

```
flask                        score 0.86   hasRisk false
xueting-thesis-event-fengfu  score 0.00   hasRisk true   hasLowScore true   minVersions true   isNew false
xueting-thesis-service-zhuanfa score 0.00 hasRisk true   hasLowScore true
```

and in the log:

```
[WARNING] [ANALYSIS] .... [RISK] package scored LOW - 0.0. Mid set to 0.6)
[WARNING] [ANALYSIS] .... [RISK] package history is SHORT. Total 1 versions committed.
[WARNING] One or more packages have identified risks.
[ERROR] Warnings present, exiting with non-zero status code.
```

Exit code **3**, as documented for `--error-on-warnings`.

So **two** signals showed: `minVersions` and `hasLowScore` (**not** predicted). `isMissing` - the dependency-confusion related signal
itself - stayed `false` throughout.

**(f) What the score actually measures.** From the DEBUG breakdown:

```
weights = {repo_version_match: .43, repo_stars: .21, repo_contributors: .14,
           repo_last_activity: .14, repo_present_in_registry: .07}
```

All five inputs are `repo_*` values fetched from the GitHub API. The chain, visible in the log:

- flask: `Found explicit repository URLs in project_urls ... count=1` -> three GitHub calls
  (`/repos/pallets/flask`, `/contributors`, `/releases`) -> all inputs filled -> 0.86
- my packages: `Extracted fallback repository candidates ... count=0` -> **no GitHub call at all**
  (the only GitHub calls in the whole log are flask's) -> all inputs `None`, `weights={}` -> 0.0

So in this run, score 0.0 arose because **no git repository URL could be found in the PyPI metadata**, not
because anything suspicious was detected. DepGate's own documentation describes 0.0 as "high risk
(malicious packages, missing packages, or critical issues)" - none of which applies here; the
mechanism in my case was simply missing metadata.

**How I attributed log lines to packages:** the `count=0` line does **not** name the package. But it
sits between two lines that do - `target=https://pypi.org/pypi/xueting-thesis-event-fengfu/json`
above it and `deps.dev enrichment start ... pkg=xueting-thesis-event-fengfu` below it. General rule
for DEBUG logs: if a line has no identifier, look at the nearest named line above *and* below; if
both name the same thing, the attribution is safe.

The wording difference is also visible: flask gets *"Found **explicit** repository URLs"* and
*"Extracted repository candidates **with docs**"*, my packages get *"Extracted **fallback** repository
candidates"* with `count=0`.

**(g) `repo_version_match` is the interesting one of the five**: it asks whether the version published
on PyPI corresponds to a tag or release in the source repository the package claims to come from. A
package that claims a source repo but publishes a version that exists in no release is a classic sign
that the artifact was not built from that source.

**(h) Structural note:** this scoring cannot work for internal packages at all - a private company
package has no public GitHub repository, so it has no `project_urls` entry, so it scores 0.0. Whether
that makes the warning useful or not in my matrix is a question for the pilot data.


## 7. super-confused - what I ran and what I found in the source

```bash
cd "$REPO/services/python"
SPFX="$OUT/python_superconfused"
echo "scan 1: pyproject.toml" | tee "${SPFX}_log.txt"
"$SC" --json pyproject.toml 2>> "${SPFX}_log.txt" | tee "${SPFX}.json"
echo "scan 1 exit code: ${PIPESTATUS[0]}" | tee -a "${SPFX}_log.txt"
```

**Why `2>>` and never `2>&1`**: super-confused writes its **result to stdout** (it has no `-o` flag),
unlike Trivy and DepGate which write to a file. `2>&1` would mix error text into the JSON stream and
corrupt the file.

### Observations

**(a) `--json` suppresses every error message.** Source lines 1009-1024:

```js
if (!fs.existsSync(targetPath)) {
    if (!jsonMode) { console.error(`Path does not exist: ${targetPath}`); }
    process.exit(1);
}
...
catch (error) {
    if (!jsonMode) { console.error(`Scan failed: ${error.message}`); }
    process.exit(1);
}
```

My first run gave `exit code: 1` with a **completely empty** log, because the working directory was
not `services/python` and `pyproject.toml` did not exist there. The `2>>` redirect was correct -
there was simply nothing written to stderr. 

Running the same command **without `--json`** immediately
printed the human-readable result, so that is the way to diagnose it:

```
$ "$SC" pyproject.toml
Scanning pyproject.toml for dependency confusion opportunities...
No Dependency Confusion Opportunities found.
```

**(b) The result file is 0 bytes when nothing is found** - in `--json` mode it prints nothing at all,
not `[]`, not `{}`. That is
the step checks the file size at the end with command `ls -l`: the file **size** is the evidence.

**(c) The positive control did not fire.** `python_superconfused_positive_control.json` was also
**0 bytes**, although `xueting-thesis-not-published` returns **404** on PyPI (checked directly).

**(d) Why: there is a name filter before any registry call.** `super-confused.js:768`:

```js
isPotentiallyVulnerable(packageName) {
    const suspiciousPatterns = [
        /^[a-z0-9]+[-_][a-z0-9]+$/i,          // exactly one hyphen: "word-word"
        /^[a-z0-9]{3,8}$/i,                    // short, no hyphens
        /^(lib|utils?|helper|common|core|base|tools?|sdk)$/i,
        /^(test|demo|example|sample)[-_]?/i,   // must START with these
        /^[a-z0-9]*[-_]?(test|demo|example|sample)$/i,   // must END with these
        /^[0-9]+[a-z]+[-_]?[a-z0-9]*$/i,       // starts with digits
    ];
    ...
    return suspiciousPatterns.some(p => p.test(packageName)) || packageName.length <= 4;
}
```

It is called from every parser (`scanPackageJson`, `scanPyprojectToml`, `scanPomXml`, ...) **before**
`checkPyPiPackageExists` / `checkNpmPackageExists`. A name that does not match is never looked up to public registry.

`xueting-thesis-not-published` has **three hyphens**, so pattern 1 (which allows exactly one) does not
match, it does not start or end with test/demo/example/sample, does not start with a digit, and is 28
characters long. It matches nothing -> never checked.

**(e) Experiment that isolates the cause.** One file, two dependency names, **both 404 on PyPI**, the
only difference being their shape:

```bash
mkdir -p "$SCA/sc_control2" && cd "$SCA/sc_control2"
# pyproject.toml with dependencies:
#   "xueting-notpublished==1.0.0"            -> 1 hyphen  -> passes the filter
#   "xueting-thesis-not-published==1.0.0"    -> 3 hyphens -> fails the filter
"$SC" pyproject.toml
```

Result:

sub-RQ2_tool_selection\tool_scan_pilot\superconfused_positive_control.txt

```
DEPENDENCY CONFUSION OPPORTUNITY!
xueting-notpublished (pypi) in pyproject.toml
Version: ==1.0.0
```

Only the one-hyphen name was reported. So the silence on my packages is caused by the **name-shape
filter**, not by the registry.

The same filter applies to all three ecosystems (it is shared by all parsers), and all my internal
names have three hyphens: `xueting-thesis-event-fengfu` etc.

**(f) Consequence for the pilot:** my current positive control name cannot fire, so a 0-byte result
file would be uninterpretable. The control name has to be changed **before** the pilot.
This is **not** an HR1 failure - the tool installs, runs, parses `pyproject.toml` and exits cleanly.


## 8. DepCheck - local run only (backup candidate)

```bash
cd "$REPO/services/python"
python -I -X utf8 "$SCA/depcheck/depcheck.py" pyproject.toml --no-banner \
  --export "$OUT/python_depcheck.json" 2>&1 | tee "$OUT/python_depcheck_log.txt"
echo "depcheck exit code: ${PIPESTATUS[0]}" | tee -a "$OUT/python_depcheck_log.txt"
```

**`-X utf8` is needed on Windows.** The first attempt crashed with `UnicodeEncodeError` in
`cp1252.py` while drawing its progress bar (it uses block characters); through a pipe on Windows,
Python falls back to the legacy cp1252 encoding. so it has to be
the command-line option `-X utf8`. This is a Windows-local artifact; the Ubuntu container runs in a
UTF-8 locale.

### What I read in the source

- 19 parsers (`PARSERS` dict): `package_json`, `package_lock_json`, `yarn_lock`, `pnpm_lock`,
  `requirements_txt`, `pipfile`, `pipfile_lock`, `pyproject_toml`, `composer_json`, `composer_lock`,
  `gemfile`, `gemfile_lock`, `pom_xml`, `build_gradle`, `go_mod`, `cargo_toml`, `cargo_lock`,
  `nuget_packages_config`, `csproj`.
- `check_package()` queries the registry for **every** parsed name - there is **no name-shape filter**.
- Directory mode excludes `node_modules`, `.git`, `__pycache__`, `vendor`, `.venv`, `venv` - but
  **not** `target`, `build` or `py_dependency`.

- Exit code is meaningful: `sys.exit(1 if any_vulns else 0)`.

### Output on services/python

```
  Total:      3
  Safe:       3
  Vulnerable: 0

  [OK] All 3 packages exist on the public pip registry.
  No dependency confusion vulnerability found.
```

```json
{ "vulnerable": [], "safe_count": 3, "error_count": 0, "errors": [] }
```

- The exported JSON in the clean case contains **no package names at all**, only a count. So for this
  tool the console log is the only record of *which* packages were checked.

### Output on the two-name control file (positive control)

```
  [!] xueting-notpublished - NOT FOUND on pip
  [!] xueting-thesis-not-published - NOT FOUND on pip
  Safe: 0   Vulnerable: 2

  An attacker can register these on the public pip registry
  with a higher version -> Remote Code Execution!
```

```json
"vulnerable": [ { "name": "xueting-notpublished", "version": "==1.0.0" },
                { "name": "xueting-thesis-not-published", "version": "==1.0.0" } ]
```

### Observations

- **Both** names were flagged, where super-confused flagged only one. Same file, same two names, same
  registry - a measured difference between two tools that advertise the same check, with the
  mechanism known from both sources.
- Even on the result the JSON has `name` and `version` only - **no URL field anywhere in
  the schema**.
- The two messages from the same tool on the same project, ten minutes apart, are worth quoting
  verbatim side by side:
  - name **published** on public PyPI -> `[OK] ... No dependency confusion vulnerability found.`
  - name **not published** -> `An attacker can register these ... -> Remote Code Execution!`

  The wording is **future tense** ("an attacker *can*"), i.e. the tool reports an *opportunity*, not
  an attack event. This is the clearest illustration so far, and it
  comes from my own run rather than from a README.
- Maintenance picture for the screening table, with today's date: 1 star, no LICENSE file, no releases
  or tags (pinnable only by commit SHA), last push 2026-02-19.
- **Decision deferred:** whether DepCheck should become a fourth measured tool is left until after
  Thursday's supervisor meeting. Nothing in the runner image or the pipelines was changed for it.


## 9. Changes made to the pipelines today

1. **`pip freeze` -> `pip show depgate`** in all three workflows. I only need as a version record for the tool itself.
2. **`service-ci-python.yml`: the Trivy step now has 4 scans instead of 3**, and `--scanners vuln` was
   added to the CycloneDX scan:

   | scan | what varies | format | file |
   |---|---|---|---|
   | 1 | - | json | `_trivy_declared.json` |
   | 2 | format only | cyclonedx | `_trivy_declared_cdx.json` |
   | 3 | format only | spdx-json | `_trivy_declared_spdx.json` |
   | 4 | **scope**: no `--skip-dirs` | json | `_trivy_all.json` |

   Reason for adding `--scanners vuln` to scan 2: previously scan 1 and scan 2 differed in **two**
   things (format *and* whether vulnerability scanning ran), so a difference between the files could
   not be attributed to either. Now scans 1-3 differ in exactly **one** variable, the output format,
   and scan 4 differs from scan 1 in exactly one variable, the directory scope.

   Reason for adding SPDX: it has a dedicated `downloadLocation` field, which CycloneDX does not, so
   it is a second independent place where an origin URL could appear.

3. **The upload list** of the python workflow gained `..._trivy_declared_spdx.json`.

The nodejs and java workflows still have the old 3-scan Trivy block - they are only changed after the
python pilot shows whether SPDX and scan 4 are worth keeping.


## 10. Open points carried into tomorrow's pilot

- [ ] **Change the super-confused positive-control name in all three workflows.**
      `xueting-thesis-not-published` cannot pass the name filter, so it can never fire, and a 0-byte
      result file would be uninterpretable. `xueting-notpublished` passes the filter and is 404 on
      PyPI (npm side still to be verified with `npm view xueting-notpublished`).
      Idea: put **both** names in each control file, so every cell's artifact proves two things by
      itself - the tool ran and can report, and my naming convention is excluded by the filter.
- [ ] **`service-ci-java.yml`: the positive control is written but never scanned.** The step creates
      `/tmp/sc_control/pom.xml` with a heredoc and then jumps straight to
      `echo "positive control exit code: ${PIPESTATUS[0]}"` - `super-confused` is never invoked on it,
      so that exit code belongs to the preceding command, and the file requested by the upload list
      can never exist.
- [ ] **Scan 4 check in cell `pip_A1a_B1a_B2b_C1b`:** compare `_trivy_declared.json` with
      `_trivy_all.json`. If `_all.json` has an extra `Results` entry under `py_dependency/`, scan 4
      earns its place; if the two files are identical apart from `ReportID`/`CreatedAt`, scan 4
      produces nothing and should be reconsidered. The local `.venv` observation (i) cannot decide
      this.
- [ ] **Correct section 6 of `docs/summary_sca_test.md`:** the claim that DepGate sees variable B2
      through `requested_spec` is contradicted by today's run; and super-confused's "name-existence
      primitive" description has to be extended with the name-shape pre-filter.
- [ ] **npm cell:** DepGate prefers `package-lock.json` over `package.json`, so npm may be the one
      ecosystem where its input differs between cells - worth watching in pilot cell 2.
- [ ] Record the local Trivy DB date next to the image's (11.10) whenever local output is cited, so
      local and CI results are never mixed.


# 15.10.2026 - sub-RQ1 experiment repeat run: whole matrix executed again, same result with the 08.09 run, runner wait timeout raised to 90 s

**Stand:** the complete sub-RQ1 matrix was executed a second time. The new result file is
is was compared cell by cell using the script automation_process\central_automated_pipeline\compare_results.py with the
first run from 08.09.2026 , and the two files are **identical in
every measured column**. One change was made to the central pipeline (runner wait timeout 60 s ->
90 s)

script output in terminal: (the difference file results_diff.csv has only headers, no rows)
```
Summary:
Rows in file A: 432
Rows in file B: 432
Matching rows: 432
Differing rows: 0
Matching rows: 432
Differing rows: 0
Differing rows: 0
Rows only in file A: 0
Rows only in file B: 0
check file automation_process/central_automated_pipeline/results_diff.csv for differences
```

## 1. Why the matrix was run a second time

- This repeat run is **part of the sub-RQ1 result analysis**
- It answers the question: does the same cell - same private registry configuration (A), same
  package manager configuration (B1), same version specifier (B2), same pipeline operation type (C)
  - produce the **same** result again weeks later?
- If yes, then the dependency resolution behaviour of the three package managers (npm, pip, Maven)
  is **consistent and reproducible**


## 2. The one cell that crashed, and the cause

- Cell `mvn_A1a_B1d_B2a_C1a` failed three times before it finally successfully ran:
  1. During the night run, recorded in
     `automation_process/central_automated_pipeline/crashed_cells.txt`:

     ```
     2026-10-15 01:17:26.748434: mvn_A1a_B1d_B2a_C1a - Command '['gh', 'workflow', 'run',
     'service-ci-java.yml', '--repo', 'shirley1997/MS_test_system', '-f',
     'cell_id=mvn_A1a_B1d_B2a_C1a', '-f', 'A=A1a', '-f', 'B1=B1d', '-f', 'B2=B2a', '-f',
     'C1=C1a']' returned non-zero exit status 1.
     ```

  2. First manual rerun in the morning: the runner was again reported as not online.
  3. Second manual rerun: the job stayed stuck at the **Checkout repository** step. The workflow run
     had to be stopped and the offline runner deleted before the cell could be dispatched again.
- **Cause found:** the runner container *did* register with GitHub, but it needed **more than 60
  seconds** to reach status `online`. The pipeline waited only 60 s, gave up, and treated the runner
  as "not online" -> then does not dispatch a workflow job to the runner.

## 3. Change in `central_automated_pipeline.py` (kept)

- `wait_for_runner_online(...)` send requests the GitHub runners API until the ephemeral runner for this cell
  reports status `online`, and only then is the workflow dispatched.
- The timeout was raised from **60 s to 90 s** 
- After this change the cell was dispatched again and **worked**. 


# 25.10.2026 - pipeline review: 4 Maven cells (B1d × B2a × C1b) kept the cached 1.0.0, but are labelled resolution_error

**Stand:** I reviewed the three service pipelines (`.github/workflows/service-ci-*.yml`) and the classifier
(`classify_logic()` in `central_automated_pipeline.py`) against the evidence files of the final run
(`automation_process/central_automated_pipeline/artifact_download/`, identical to `sub-RQ1_result/0809`).
The classifier is correct. But **4 Maven cells** have a label that does not describe what really happened.

## 1. What I checked

- All 99 `resolution_error` cells: **95 have no evidence file at all** (real failure). Only **4** have one.
- Every `malicious_resolved` and `private_resolved` cell has a real version **and** a real source URL.
- -> **npm and pip have no wrongly labelled cell.** Only these 4 Maven cells are special.

## 2. The 4 maven cells

- `mvn_A1a_B1d_B2a_C1b`, `mvn_A1b_B1d_B2a_C1b`, `mvn_A2_B1d_B2a_C1b`, `mvn_A3_B1d_B2a_C1b`
  = Maven cells, default configuration (B1d, only Maven Central), pinned 1.0.0 (B2a), package update (C1b).
- Phase-2 log: `BUILD SUCCESS`. The lockfile contains **1.0.0** for both internal packages.
- But the `resolved` URL is **empty** (log: `Artifact resolved url ... not found`).
- Classifier logic in central automation pipeline: no package origin URL -> origin is not hosted / group -> **resolution_error**.
- Reality: the build succeeded and used the internal package with version 1.0.0 -> the attack **failed**. The label `resolution_error`
  ("build failed / output incomplete") does not fit well. The logic is not wrong - it simply has no class for
  "kept from the local installation", because I did not expect this case.

## 3. Why it happened

- **My design:** phase 1 of C1b uses fixed setup files in all ecosystems. The goal: version 1.0.0 is installed,
  no matter from where, as the starting point for the update.
- For Maven, phase 1 replaces the cell's `pom.xml` with `fixed_setup_file/fixed_pom.xml`. This file has
  **one repository with id `central`**, pointing to `maven-group-public-first` (the A1a group) - for every cell.
  - setup log: `Downloaded from central: .../maven-group-public-first/.../xueting-thesis-event-juhe-1.0.0.pom`
  - -> 1.0.0 is now in the local repository `~/.m2`.
- **Maven behavior:** Maven always looks in `~/.m2` (local repository) first. For a fixed release version (1.0.0) it only downloads from remote repository
  if the package is missing.
- Maven also remembers **which repository** a cached package came from, and reuses it only if that repository is
  configured in the current build (Maven 3 compatibility notes, "Resolution from Local Repository").
- In **Maven 3.9** (runner uses 3.9.16) this is tracked **by repository id only** - the Maven Resolver docs call it
  the "impostor problem": two repositories with the same id but different URLs are treated as the same.
- **Phase 2 under default configuration B1d:** Maven Central also has the id `central` -> Maven thinks the cached 1.0.0 came from a
  configured repository -> **no download**, use the cache -> `BUILD SUCCESS`.
- The `maven-lockfile` plugin computes `resolved` by checking the configured remote repositories. Maven Central
  has no 1.0.0 -> the URL stays **empty**.
- **So the cause = my setup (id `central` in the fixed pom) + documented Maven behavior.** It is not a general rule
  "Maven keeps the installed version". With a different id, Maven would reject the cached copy, and try to connect Maven Central,
  fail -> a real `resolution_error`, like npm.

### Maven behavior: search Local repository first - for pinned versions and for version ranges

The local repository comes first in **both** cases. The difference is what Maven needs before it can decide.

**What the official documentation says:**
- Repositories guide: the local repository "caches remote downloads", and "Downloading in Maven is triggered by a
  project declaring a dependency that is **not present in the local repository**".
- POM reference, version ranges: "Maven picks the **highest version** ... that satisfies all the hard requirements."
- POM reference, `updatePolicy`: "how often Maven tries to update its local repository from the remote repositories
  ... compare ... **maven-metadata** ... to the remote. ... `daily` (default) ... `never` (only downloads if not yet
  existing in the local repository). ... this affects **both artifacts and metadata**."

**What this means:**

| | pinned `1.0.0` | range `[1.0.0,2.0.0)` |
|---|---|---|
| Step 1: which version? | already known: 1.0.0 | Maven needs the **list of versions** (`maven-metadata.xml`). It refreshes this list from the remote repositories according to `updatePolicy` (once a day by default; **every time with `-U`**, which my phase 2 uses) |
| Step 2: the file of that version | **local first**, download only if missing | **local first**, download only if missing |

- "Local first" is true for the **files** in both cases. With a range, Maven additionally refreshes the **version list**
  from the remote repositories, and only that list can reveal 1.0.3.
- My own evidence (meeting notes 22.09, `mvn_A2_B1a_B2b_C1b`): in phase 2, Maven first downloads `maven-metadata.xml`
  from the hosted repository, then the `1.0.2.pom`. `maven-metadata.xml` appears only in phase 2, because the pinned
  phase 1 asks for the file directly.
- Wording for the thesis: "Maven always looks in the local repository first. For a fixed version it only needs the
  file, so a cached 1.0.0 is used directly. For a version range it first refreshes the version list from the remote
  repositories (forced by `-U`), picks the highest matching version, and then takes that file from the local
  repository or downloads it."

**Sources:**
- [Maven - Introduction to Repositories](https://maven.apache.org/guides/introduction/introduction-to-repositories.html)
- [Maven - POM Reference (version requirements, updatePolicy)](https://maven.apache.org/pom.html)


## 4. Why npm and pip do not have this

- **npm:**(cells are pinned (B2a)) phase 1 only copies a fixed lockfile - nothing is installed, and the npm cache is cleaned.
  `npm update` always asks the configured registry which versions exist. Under B1d that is npmjs, which only has 1.0.3, and the version is pinned to 1.0.0 -> `ETARGET` -> lockfile removed -> a real `resolution_error`.
- **pip:** phase 1 already uses the cell's own `pip.conf`. Under B1d that is only PyPI, which has no 1.0.0
  -> phase 1 fails -> phase 2 is skipped (= exception 2 of my rule).
  In addition, `--target` makes pip ignore already installed packages **(this is a problem i need to fix)** (pip source, `commands/install.py`:
  `if options.target_dir: options.ignore_installed = True`), so pip always resolves fresh from the index.
- npm pinned C1b cells (B1a × B2a): npm says `up to date`, so the lockfile keeps the URL from my fixed setup
  lockfile -> `private_resolved`. This matches my design (installed 1.0.0 is kept), and npm did ask the cell's
  registry -> correct label.

### Why npm does not take a cached 1.0.0 like Maven

npm has **no cached 1.0.0**, and `npm update` does not decide from local files anyway - two differences to Maven:

| | Maven (phase 2) | npm (phase 2) |
|---|---|---|
| What phase 1 left behind | the real 1.0.0 **files** in `~/.m2` (downloaded in phase 1) | only a **copied lockfile** - text saying "1.0.0, from this URL". No package files: `--package-lock-only` downloads nothing, and the npm cache was cleaned |
| How phase 2 decides | for a fixed version: "is the file already in my local repository?" -> yes -> use it, no registry asked | `npm update <the 2 packages>` asks the **configured registry** for the list of versions, then picks the highest one that matches `package.json` |
| Under B1d (npmjs / Maven Central only) | the cached copy counts as available (same id `central`) -> `BUILD SUCCESS` | npmjs lists only 1.0.3; pinned `1.0.0` matches nothing -> `ETARGET` |

- The key point: **"update" means something different.**
  - npm **always re-checks the registry** for the packages I name - that is the purpose of `npm update`. So the
    registry configuration decides the result.
  - Maven only re-checks the registry if the file is **missing locally** (`-U` only forces re-checking version lists
    and snapshots, not an already downloaded fixed release version).
- Evidence that npm really asks the registry, from my other pinned C1b cells:
  - B1a with A2/A3: npm asked the hosted repository, found 1.0.0 -> `up to date` -> `private_resolved`.
  - B1d: the same command fails, because npmjs has no 1.0.0.

### Do npm and pip also use a local cache? Yes - but it cannot cause the Maven problem

**Between cells: no cache in any ecosystem.** Every cell runs in a fresh runner container, and every pipeline cleans
its cache first: `npm cache clean --force`, `pip cache purge`, `rm -rf ~/.m2/repository`.

**Inside one cell (phase 1 -> phase 2):**

| | cache used in phase 2? | evidence |
|---|---|---|
| **pip** | **yes**, in all 27 C1b cells with evidence: `Using cached ...` for Flask etc., and in **9 pinned cells** also for the internal **1.0.0** (e.g. `pip_A1a_B1a_B2a_C1b`) | phase-2 logs |
| **npm** | C1b: no - phase 1 only copies a lockfile and downloads nothing, so the cache is empty. C1c: possible, but the evidence is the phase-1 lockfile anyway | no cache lines in npm logs (default log level does not show them) |
| **Maven** | yes, the internal 1.0.0 from `~/.m2` | the 4 B1d × B2a × C1b cells |

**Why pip's cache cannot cause the Maven problem:**
- pip's cache is a download cache, looked up by the **exact URL**. A cached file is only used if the **current**
  configuration asks for that same URL.
- In the 9 pinned cells, phase 2 asked the same Nexus index as phase 1 (log: `Looking in indexes:
  ...pypi-group-public-first...`) -> same 1.0.0 file -> same result as a new download -> correct.
- Maven's local repository is looked up by **repository id** -> a file from the Nexus group was accepted for
  "Maven Central" (different URL, same id `central`).
- Under B1d, pip would ask PyPI URLs -> cached Nexus files cannot be used (and phase 1 fails there anyway).
- Detail from pip source (`pip/_internal/index/collector.py`, pip 26.2.1): pip forces a fresh version list from the
  index only with the option `--refresh-package`. By default it may reuse a cached index page. Inside one cell this is
  the same index with the same content -> no effect on my results.

**Why only Maven's cached package has no origin URL:**

| | where the URL in the evidence file comes from | if the file comes from the cache |
|---|---|---|
| **pip** (`--report`) | the download link pip picked from the **configured index** | URL known -> filled (e.g. the Nexus URL in the 9 pinned cells) |
| **npm** (lockfile) | the registry metadata, or kept from the setup lockfile | URL known -> filled |
| **Maven** (`maven-lockfile`) | the plugin does **not** record the real origin. It **checks afterwards** which configured remote repository has the file (HTTP HEAD request) | under B1d only Maven Central is configured, and it has no 1.0.0 -> **empty** |

How pip finds a file, step by step (this is why the URL is always filled):
1. Ask the configured index: "which files exist for this package?" -> the index answers with a list of download links,
   e.g. `.../pypi-group-public-first/.../fengfu-1.0.0.whl`.
2. Pick one link (the version that matches).
3. Check the cache: "do I already have the file from exactly this link?" -> yes: use the cached copy, no: download.
4. Write this link into the report as the URL.

- The URL is decided in step 2, **before** the cache is used -> always filled.
- Maven skips step 1 for a fixed version: it takes the file from `~/.m2` directly, and `maven-lockfile` only looks for
  a URL afterwards.
- In short: npm and pip record the URL they **used**. `maven-lockfile` **re-checks** the configured repositories and
  ignores where the cached file really came from (the Nexus group).

### pip C1b: `--target` makes pip ignore the installed 1.0.0 - finding and what to change

**My intention for C1b (package update):** like a developer - 1. version 1.0.0 is installed in the project,
2. the developer runs the update command, 3. I observe what the package manager really does.

**What the pipeline does now (`service-ci-python.yml`, C1b step):**
- Phase 1: `pip install --target ./py_dependency --report <cell>_setup-install-report.json .` (fixed pyproject, 1.0.0)
- Phase 2: `pip install --dry-run --target ./py_dependency --upgrade <2 internal packages> --report <cell>_install-report.json .`

**Finding:**
- `--target` makes pip's resolver **ignore already installed packages**. pip source
  (`pip/_internal/commands/install.py`, line 414, pip 26.2.1): `if options.target_dir: options.ignore_installed = True`.
- The pip documentation does **not** say this. It only describes the file side of `--target`: "Install packages into
  <dir>. By default this will not replace existing files/folders in <dir>. Use --upgrade to replace existing packages
  in <dir> with new versions." (https://pip.pypa.io/en/stable/cli/pip_install/) -> documentation ≠ behaviour.
- -> In phase 2, pip does **not know** that 1.0.0 is installed in `py_dependency`. It resolves as if nothing were
  installed. This explains why all 27 pip C1b cells with evidence are identical to C1a.
- Phase 1 with `--target` is correct (it only installs 1.0.0 into the directory). Only phase 2 is the problem.

**Local test (pip 26.2.1, package `six`, 1.16.0 installed into `py_dependency` with `--target`, dry-run only):**

| phase 2 command | pinned `==1.16.0`, index **without** 1.16.0 (`--no-index`) | range `>=1.16`, real index |
|---|---|---|
| `--target py_dependency --upgrade` (current pipeline) | `No matching distribution found` -> installed copy ignored | `Would install six-1.17.0` |
| `PYTHONPATH=py_dependency`, **no** `--target` | `Requirement already satisfied: six==1.16.0 in ...\py_dependency` -> installed copy seen | `Would install six-1.17.0` -> real update |

- Removing `--target` alone is not enough: pip then only looks in the runner's own site-packages, where 1.0.0 is not.
  `PYTHONPATH=./py_dependency` is needed so pip finds the installed packages.

**Check of my earlier log (15.07 design + "Checked, but decided NOT to change: missing PYTHONPATH"):**
- The 15.07 design was `--target ./deps --upgrade` **plus** `PYTHONPATH=./deps`. That could not have worked: as long as
  `--target` is in the command, pip ignores installed packages, so `PYTHONPATH` has no effect.
- The pilot then compared `A1a×B1a×B2b` C1a vs C1b (both 1.0.3) -> "no change needed". But a **range** cell gives 1.0.3
  in both cases anyway; the difference can only show with a **pinned** version and an index without a matching version.

**Effect on my current results: none expected.**
- The installed version only matters if the index has **no** matching version, but the installed one matches.
- Phase 1 and phase 2 use the **same `pip.conf`**. If phase 1 could install 1.0.0, that index still has 1.0.0 in phase 2.

| cell type | real update (pip sees 1.0.0) | current pipeline (pip ignores 1.0.0) | same? |
|---|---|---|---|
| pinned `==1.0.0` | keeps 1.0.0 ("already satisfied") | takes 1.0.0 from the same index | yes |
| range / unspecified, public registry reachable | updates to 1.0.3 | takes 1.0.3 | yes |
| phase 1 failed (B1d, A2/A3 × B1a) | no installed state, update skipped | update skipped | yes |

**Alternative checked: virtual environment.** pip would also see the installed 1.0.0 -> the same classifier extension
is needed. The runner Dockerfile needs no change (CPython built with `--with-ensurepip=install`, line 86), but a new venv
brings the pip version bundled with Python 3.12.4, not 26.2.1. -> `PYTHONPATH` is simpler. I do not want a venv.

**Decision: implement the real update flow (after the middle presentation, 27.10.2026).**

**What to change in the code:**
1. `service-ci-python.yml`, C1b phase 2: remove `--target ./py_dependency`, add `PYTHONPATH=./py_dependency`
   (env of the command). Keep `--dry-run`, `--upgrade`, `--report`. Do **not** add `--ignore-installed`.
   Phase 1 stays unchanged.
2. `service-ci-python.yml`, upload step: add `services/python/<cell>_setup-install-report.json` to the artifact paths.
   It is created in phase 1 (line 171) but **not uploaded** now (upload list lines 356-363).
3. `central_automated_pipeline.py`, `read_pip_evidence()` (C1b only): in pinned cells pip says "Requirement already
   satisfied" and does **not** list the internal packages in `--report`. Rule: if an internal package is missing in the
   phase-2 report **and** the phase-2 log says `Requirement already satisfied: <package>`, take its version + URL from
   the phase-1 report `<cell>_setup-install-report.json`. (Same idea as npm: a kept package keeps its URL from the
   setup file.) Without this, the pinned pip C1b cells would become `resolution_error`.
4. Keep sub-RQ1 reproducible: keep the current `results.csv` and artifacts; write the new run to a separate result file.

**How to verify (goal: 0 differences):**
1. Re-run only the 36 pip C1b cells with the new pipeline.
2. Compare the resolved **versions** of the internal packages with the current run (log / report) - no classifier needed.
3. Re-classify all 432 cells offline with the extended classifier from the saved evidence files and compare with
   `results.csv`.
4. Expected: same labels everywhere. If not, the difference itself is a finding and must be analysed.

**What to change in the master thesis:**
- Methodology / implementation (C1b, pip): describe phase 2 with `PYTHONPATH=./py_dependency` (pip sees the installed
  1.0.0, like a real developer update); phase 1 with `--target`.
- Classification: state that a package kept from the installed state takes its evidence from the setup phase (pip and
  npm).
- Results: if the re-run shows 0 differences, write "verified with a real update from the installed state".
- Remove my old 15.07 statement that `PYTHONPATH` was not needed (wrong reasoning, see above).

**C1c (rebuild from lockfile) checked at the same time: correct, no change needed.**
- Phase 1: `pip lock --only-deps --output pylock.<cell>.toml .` with the cell's `pip.conf` (log shows the cell's indexes).
- Phase 2: `pip install --dry-run --ignore-installed -r pylock.<cell>.toml --report ...` - pip really installs from
  the lockfile (log: `Using pylock.toml as a requirements source`, collects exactly the locked versions; report URLs
  = lockfile URLs in 35 of 35 cells). `--ignore-installed` is right here: a CI rebuild starts from a clean environment.

## 5. What changes and what does not

- **Unchanged:** 190 `malicious_resolved`, pinning never bypassed, the two-condition rule (these 4 cells are pinned,
  the rule predicts "not attacked" -> correct), A1a ≡ A1b, C1a ≡ C1c, B1b ≡ B1c, system level 90 %.
- **Changes only if I relabel the 4 cells:**
  - private 71 -> 75, resolution_error 99 -> 95
  - B1d: 0 -> 4 of 96 cells keep the internal package (still **none from Nexus**)
  - pair checks Maven: B1b vs B1d 12 -> 16 of 24 same, B1c vs B1d 9 -> 12 of 18 same (every "holds?" stays the same)
  - cross-ecosystem: agree 96 -> 92, disagree 39 -> 43
  - heatmap: 4 Maven cells E -> P*

## 6. Possible solutions (decision open, asked on the "Open Questions" slide)

- **Option A - keep `resolution_error` + explanation.** No change to the data; one footnote / sentence in the analysis.
- **Option B - rule-based sub-class `private_resolved (local)`.**
  - Rule: build succeeded + evidence file exists + both internal packages at 1.0.0 / 1.0.2 + no remote URL.
  - Applied to all 360 cells, it matches **exactly these 4** -> the rule chooses the cells, not me (defensible).
  - Keep the original `results.csv`, report numbers before and after (sensitivity analysis), and describe how it
    was found (evidence audit after the experiment) in threats to validity.
- **Option C - change the id in the fixed pom and re-run the 4 cells.** Then Maven behaves like npm
  (real failure), but this changes my "install 1.0.0 from anywhere" design for Maven only.
- For the middle presentation: keep the current numbers, add a footnote on the heatmap slide, ask supervisor.

## 7. Other points from the same review (no wrong label)

- C1c evidence is identical to C1a in all ecosystems **by construction**: the lockfile is created in the same run,
  after the attacker published, so it already contains the attacker's version -> explains C1a ≡ C1c.
  A lockfile created *before* the attack is not tested.
- pip C1b phase 2 is effectively a fresh install (`--target`, see above) -> limitation.
- `.npmrc` is missing in the npm artifacts (`upload-artifact` skips hidden files) -> config evidence incomplete.
- Java pipeline: the super-confused positive control never runs (only sub-RQ2, no effect on sub-RQ1).

**Sources:**
- [Maven 3.x Compatibility Notes - Resolution from Local Repository](https://cwiki.apache.org/confluence/display/MAVEN/Maven+3.x+Compatibility+Notes)
- [Maven Resolver - EnhancedLocalRepositoryManagerFactory (Javadoc, "impostor" problem)](https://maven.apache.org/resolver/maven-resolver-impl/apidocs/org/eclipse/aether/internal/impl/EnhancedLocalRepositoryManagerFactory.html)
- [Maven Resolver - Local Repository](https://maven.apache.org/resolver/local-repository.html)



# 29.10.2026 - make plan for the rest 2 months until final submission

details in file: D:\Master_Winfo\MA_Supply_chain_security\plan_archive\thesis_master_plan_2910_to_submission.md


## Technical work after the plan was confirmed (evening)

### 1. pip C1b (package update) fix

- **Problem:** phase 2 used `pip install --dry-run --target ./py_dependency --upgrade ...`. With `--target`, pip internally sets `ignore_installed = True` (pip source `commands/install.py`). So pip never saw the 1.0.0 installed in phase 1 and phase 2 behaved like a fresh install.
- **Change in `service-ci-python.yml`:** phase 2 is now `PYTHONPATH=./py_dependency pip install --dry-run --upgrade <2 internal packages> --report ... .`
  - `PYTHONPATH` adds `py_dependency` to Python's import path, so pip sees the packages installed in phase 1.
  - `PYTHONPATH=...` is written in front of the command, so it only applies to phase 2. Phase 1 (`--target`) is unchanged.
  - `<cell_id>_setup-install-report.json` (phase 1) is now uploaded as an artifact.
- **New observation (pilot):** when an installed internal package still satisfies the version specifier, pip keeps it. It writes `Requirement already satisfied: <name> in ./py_dependency (1.0.0)` in the log, but the package is **not** listed in the phase-2 `install-report.json`. pip docs: the report lists the packages that are (to be) installed (https://pip.pypa.io/en/stable/reference/installation-report/).
- **Change in `read_pip_evidence(install_report, setup_report, pip_log)`** (central pipeline):
  - first look for the internal package in the phase-2 report (as before)
  - if it is missing there **and** the log contains `Requirement already satisfied: <name>` -> take name, version and URL from the phase-1 setup report
  - otherwise the package is missing -> `resolution_error` (strict)
- **Why the setup report:** the log has name + version but no URL; the classifier needs name + version + URL. Phase 1 used the same `pip.conf` as phase 2, so the URL in the setup report is the cell's own origin.
- **Why both conditions:** with `--upgrade`, pip prints "already satisfied" in every C1b cell whose phase 1 succeeded, also when it then upgrades. The deciding signal is "missing from the phase-2 report"; the log line confirms that an installed version existed.
- **Checks:**
  - offline re-classification of all 135 valid pip cells from the 15.10 artifacts with the new function: **0 differences** (old C1b logs have no "already satisfied" line for the internal packages)
  - pilot `pip_A1a_B1a_B2a_C1b` (pinned): internal packages kept, not in the phase-2 report -> will be `private_resolved` via the setup report
  - pilot `pip_A1a_B1a_B2b_C1b` (range): 1.0.3 in the phase-2 report -> `malicious_resolved`
- **Thesis wording:** describe it as a pilot observation + pip documentation. The `--target` story is not mentioned in the thesis.
- **Decision:** full 432-cell re-run tonight (simpler than editing checkpoint/results by hand, and a third reproducibility check). The 15.10 run is archived first as `sub-RQ1_result/1510/`. Expected: 0 label changes.

### 2. "Kept package" during package update - one phenomenon in three ecosystems

- During C1b the package manager finds that the existing state already satisfies the version specifier and keeps the package. The existing state is: pip = installed package, npm = lockfile entry, Maven = local repository `~/.m2`.
- What differs is the origin evidence:

| | origin evidence of the kept package | inside the cell's configuration? |
|---|---|---|
| pip (pinned C1b cells) | phase-1 setup report, same `pip.conf` | yes -> `private_resolved` |
| npm (4 no-op cells `npm_{A1a,A1b,A2,A3}_B1a_B2a_C1b`) | URL inherited from the static setup lockfile | not always -> label correct, URL not used for origin statements |
| Maven (4 cells B1d x B2a x C1b) | maven-lockfile sends HTTP HEAD requests to the **configured** remote repositories; under B1d only Maven Central, which has no 1.0.0 -> `resolved` empty | no -> stays `resolution_error` + explanation |

- Root cause: only pip's baseline file (`fixed_pyproject.toml`) contains no registry information (finding 08.09 / 10.09). npm's lockfile and Maven's POM also fix the registry.
- Methodology sentence: "For packages kept from the installed state during a package update, the origin is the repository from which they were installed in the setup phase."

### 3. DepCheck integrated (replaces super-confused, decided 16.10)

- **Runner image `infrastructure/runner_sca/Dockerfile`:**
  - DepCheck has no releases or tags -> pinned by git commit `3c55d2905c8f1852e98e8ba96f38fbd9a3ed91b0` + SHA-256 `235f267a...8a96` of `depcheck.py` (same file as my local copy from 13.10)
  - only Python standard library -> no pip install, no venv; the experiment's Python stays untouched
  - run with `python3.12 -I`: isolated mode, Python ignores `PYTHON*` variables (e.g. `PYTHONPATH`), the user site-packages and the current folder -> DepCheck can never import an experiment package
  - super-confused install commented out with the reason; image rebuilt, persistent runner `sca-thesis-runner` recreated
- **Workflows:** super-confused step removed from all three workflows. New DepCheck step in each, scanning explicit files:
  - pip: `pyproject.toml`
  - npm: `package.json` (declared) + `package-lock.json` (resolved; only if the file exists, it is missing in failed cells)
  - Maven: `pom.xml`
- **Why explicit files, not a directory scan:** the directory scan is recursive and does not skip `py_dependency/` or `target/`; and each result must belong to one known input file.
- **Command details:** `--export <file>.json` writes the result to its own file, so `2>&1 | tee` can collect the console output in the log; `${PIPESTATUS[0]}` = DepCheck's own exit code (1 = something reported, 0 = nothing).
- **Positive control** (per ecosystem): a fake manifest in `/tmp/depcheck_control/` with one name that does not exist on the public registry (`xueting-thesis-not-published`; Maven `io.github.shirley1997.notpublished:xueting-thesis-not-published`). Checked today: 404 on PyPI and npm, 0 hits in the Maven search. If DepCheck reports it, the tool really asked the registry, so its silence on the real packages means "name exists", not "tool broken".
- **From the source:** network errors are counted as `error` (not as safe); other HTTP errors (e.g. 500) are treated as "exists".
- **Test `pip_A1a_B1a_B2b_C1c` (run_sca=on):**
  - scan 1: 3 packages, 3 safe, 0 vulnerable, exit code 0 -> silent because the internal names exist on PyPI (attacker 1.0.3)
  - positive control: `xueting-thesis-not-published` NOT FOUND -> vulnerable, exit code 1
  - in a clean result neither the JSON nor the log names the checked packages (only "Packages: 3") -> the names come from the uploaded `pyproject.toml`
  - output wording is future tense: "An attacker **can** register these ..." -> the tool reports an opportunity (S1), not the attack that already happened
- npm and Java steps written and checked; test cells: `npm_A1a_B1a_B2b_C1c`, `mvn_A1a_B1a_B2b_C1c`.

### 4. Finding before the Java test: DepCheck checks Maven through a search index

- DepCheck asks `search.maven.org/solrsearch` (a search API), not the Maven repository itself.
- Checked today:
  - `io.javalin:javalin` -> found (numFound 1)
  - `io.github.shirley1997.thesis:xueting-thesis-event-juhe` and `:xueting-thesis-result-fanhui` -> **numFound 0**
  - but `repo1.maven.org/maven2/io/github/shirley1997/thesis/xueting-thesis-event-juhe/maven-metadata.xml` serves version **1.0.3** (published 02.08.2026)
- **Prediction (written before the Java test):** in every Maven cell DepCheck reports both internal packages as "NOT FOUND -> vulnerable" (exit code 1), although the attacker package exists on Maven Central. This warning is wrong by the tool's own rule, and it is the same in every Maven cell, so it is not cell-dependent and does not open the gate for the 190-cell run.
- Why the search index has no entry for my packages is not verified - only the observation is recorded.




# 30.10.2026 - sub-RQ2: probe run of 9 cells, gate decision: no 190-cell main experiment

Starting point: the 3rd full sub-RQ1 run (with the pip C1b fix) is identical to the runs of 14.10 and 08.09 -> sub-RQ1 dataset is reproducible.

## 1. Why a probe run and a gate rule

- Open question: should I run all 190 vulnerable (`malicious_resolved`) cells with the SCA tools (the planned sub-RQ2 main experiment)? This needs a modified copy of the central automation pipeline (cell filter, `run_sca=on`, 5-bucket classifier, new result file) -> 2-3 days of work.
- Supervisor + professor: the qualitative comparison of detection mechanisms is more important; the main experiment only if it can show something new.
- Solution: run a few **probe cells** by hand (existing service CI pipelines, `run_sca=on`, persistent runner `sca-thesis-runner`), and decide with a **gate rule** that is written down **before** the run.

## 2. Probe design

| ecosystem | vulnerable (`malicious_resolved`) | control (`private_resolved`) |
|---|---|---|
| npm | `npm_A1a_B1a_B2b_C1a`, `npm_A1a_B1a_B2b_C1c` | `npm_A1a_B1a_B2a_C1c` |
| pip | `pip_A1a_B1a_B2b_C1b`, `pip_A1a_B1a_B2b_C1c` | `pip_A1a_B1a_B2a_C1c` |
| Maven | `mvn_A1a_B1a_B2b_C1a`, `mvn_A1a_B1a_B2b_C1c` | `mvn_A1a_B1a_B2a_C1c` |

- Same A1a x B1a in all cells -> only ecosystem, B2 and C1 change.
- The 2 vulnerable cells differ in C1 -> different input files for the tools (with / without lock file).
- The control is the "twin" of a vulnerable cell: same configuration, but pinned version (B2a), not attacked.
- Why one control per ecosystem: a warning that also appears in the non-vulnerable twin cannot be about the attack.

## 3. Gate rule and predictions (written before the run)

- Written in `sub-RQ2_tool_selection/candidate_detection_logic.md`, section 15.
- Basis: local tests, documentation and source code indicate that the tools' DC-related warnings depend on the package names in the scanned file and on the state of the public registry (is this name available on public registry?) -> these 2 things are the same in all vulnerable cells of an ecosystem. currently only python service is tested. but the tool is Not yet tested in the pipeline for npm and Maven.
- **Gate rule:** run the 190 cells only if a DC-related warning (name free / wrong registry origin / anything about dependency confusion, whatever it is based on)
  - (a) appears in a vulnerable cell but not in its control cell (which has result private_resolved), or
  - (b) differs between the two vulnerable cells of one ecosystem.
  - Other unexpected outputs are analysed first. if output changed depend on different A/B1, more probes with other A/B1 values are run before deciding. Known exception: Trivy reads `<repositories>` of `pom.xml`.
  - Not counted: inventory differences (e.g. 1.0.3 vs 1.0.0) and an package origin URL without any warning.
- **Predictions (short):** Trivy: `nothing_found` / `other_warning`, no origin URL (open question: npm CycloneDX), no input in pip C1b. DepGate: `compare` silent, `heur` -> `metadata_warning` also shows in controls cell. for Maven (java pipeline): field `isMissing` may be true. DepCheck: silent for npm/pip, Maven cells show "NOT FOUND" (which is false result, the tool search maven index, not maven central) also appear in the control cell (because in both cell the attacker package actually exist on public registry). Positive controls fire --> these tools actually work properly. Expected: `attack_detected` = 0, gate stays closed.-> no main experiment needed
- New finding before the run: (source code review) DepGate uses the same Maven search API as DepCheck (`REGISTRY_URL_MAVEN = https://search.maven.org/solrsearch/select` in DepGate `constants.py`).

## 4. Running the probes

- the first npm cell took 10-15 min (yesterday's sub-RQ1 cells: 1 min, because `run_sca` was off). Reason: DepGate reads the whole `package-lock.json` (70 packages) 3 times (for different scan / analysis levels)(`compare`, `heur`, `heur --direct-only`) and send request to npm, deps.dev and the GitHub API for each package.


## 5. Checks that the outputs are valid (but not caused by network problems)

- All 9 cells resolved as in sub-RQ1: 1.0.3 in vulnerable cells, 1.0.0 in control cells.
- All DepCheck positive controls fired. DepCheck `error_count` = 0 in every cell.
- The Maven search API answered with HTTP 200 (with 0 results) -> package "NOT FOUND" / `isMissing` field is True -> are real answers of the index search.
- GitHub API `403` (rate limit) appeared in DepGate npm logs (115-133 lines per cell) -> only DepGate's `heur` metadata is affected, the DC check is not affected.

## 6. Results

results file \ raw output files of the tools and cells: D:\Master_Winfo\MA_Supply_chain_security\pilot_test_sub-RQ2\probe_run_3010

| | npm | pip | Maven |
|---|---|---|---|
| Trivy | lists internal packages, no warning, no origin URL in output format JSON / CycloneDX | C1c: lists 1.0.3 from `pylock`; C1b: **no input file pylock**; only the Flask CVE; SPDX `downloadLocation: NONE` -> no package origin URL | CVEs in public packages only (jackson, jetty); internal packages listed **without version** under a range |
| DepGate `compare` | `isMissing=false` | `isMissing=false` | `isMissing=true` (this is a false warning because attacker package has published), it is also shown in the control cell |
| DepGate `heur` | `metadata_warning` (score 0.0, pacakge has one version), exit 3, also shown in the control cell | same | `hasRisk=true`, also shown in the control cell |
| DepCheck | `vulnerable: []` (manifest + lock file, all packages show "safe") | `vulnerable: []` | both internal packages "NOT FOUND" (this is a wrong output), exit 1, also shown in the control cell |

- No tool reported where a package came from: no origin URL in any output format (the open question for npm CycloneDX is now answered: no `externalReferences`, no `repository_url`).
- No tool reported that the attacker package is resolved: `attack_detected` = 0 in all probe cells.
- Outcome levels: everything is counted as `not_detected`, except Maven cells with DepCheck / DepGate = `risk_reported`, --> it is a wrong output. and it also shown in control cell. somehow they can't find attacker package through maven search index API.

## 7. Gate decision: CLOSED -> no 190-cell main experiment

- No DC-related warning differs between a vulnerable cell and its control cell, and none differs between the two vulnerable cells of an ecosystem.
- The rest vulnerable cells differ only in A and B1, which the tools do not use for producing their warnings (documentation + source code reviewed). The probes covered the variables the tools do read (B2, C1).
- -> Running all 190 cells would not show anything new. **Decision: the main experiment is not run, and the central automation pipeline is not changed for sub-RQ2.**
- To write in the thesis: the probes measured only A1a x B1a. the other A/B1 combinations are covered by the argument above, not by measurement. recall over all 190 cells is not computed, because the tools' outcome does not change between cells.
- Findings: (scope = the three measured tools + the 24-tool review for hypothesis, not "SCA tools in general"): none of the three tools reported that the attacker's package is resolved. in these 3 tools, Depcheck and depgate checks dependency confusion only based on ask whether a package name from manifest / lockfile exists on the public registry. for Maven two tools (depcheck, depgate) even gave a false "package name missing on public registry" warning, because they query a search index instead of the repository (maven central).

## 8. Not predicted (findings)

- **DepGate Maven - two sources disagree.** `exists=false` and `isMissing=true` say the same thing (name not found); both come from the search API `search.maven.org`. A search API answers HTTP 200 even when it finds nothing - the result is in the body (`"numFound": 0`). At the same time DepGate reads `maven-metadata.xml` and the 1.0.3 `.pom` from the real repository `repo1.maven.org` (HTTP 200) and the GitHub repo of the attacker package (log: `Invoking Maven enrichment without search result`). So one output says "the name does not exist" and `resolved_version: 1.0.3`.
- **DepGate Maven control cell:** spec is exact `1.0.0` (not on Maven Central), but `resolved_version` = 1.0.3. In the npm control (same situation) it is `None`.
- **`resolved_version` is not the project's resolution result:** DepGate resolves the spec against the **public** registry (npm/Maven: matched against the spec; pip: always the latest, `requested_spec: null`). For npm, `requested_spec` is filled (e.g. `>=1.0.0 <2.0.0`), unlike pip.
- **Trivy Maven cell:** with a version range `[1.0.0,2.0.0)` Trivy cannot determine the version (log: `Dependency version cannot be determined`) and lists the internal packages without version; in the pinned control it shows 1.0.0.
- None of these depends on A/B1 -> no extra probes needed.

## Files

- Probe artifacts: `D:\Master_Winfo\MA_Supply_chain_security\pilot_test_sub-RQ2\probe_run_3010\` (one folder + zip per cell)
- Result table (27 rows = 9 cells x 3 tools, with bucket and outcome level): `...\probe_run_3010\probe_results_3010.csv` and `probe_run_results.xlsx`
- Gate rule + predictions: `sub-RQ2_tool_selection/candidate_detection_logic.md`, section 15
- Plan for thesis: `D:\Master_Winfo\MA_Supply_chain_security\plan_archive\thesis_master_plan_2910_to_submission.md`
