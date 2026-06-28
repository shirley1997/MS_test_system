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



## 28.06.2026 Build npm service and python service

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
- Chose **Javalin** instead of Spring Boot for lightweight smaller dependency graph 
- Decided Java service is internal-facing only, so exposing aggregation state in response is acceptable.

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