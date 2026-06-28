# Stand: 28.06.2026

# node.js
Node.js: v24.18.0
npm: 11.16.0

# python
Python 3.12.4
pip 25.1.1
requests 2.32.5
build 1.2.2 
twine version 6.1.0 (keyring: 25.7.0, packaging: 26.2, requests: 2.32.5, requests-
toolbelt: 1.0.0, urllib3: 2.7.0, id: 1.6.1)
flask 3.1.1

# java
java 25.0.3 2026-04-21 LTS
Java(TM) SE Runtime Environment (build 25.0.3+9-LTS-195)
Java HotSpot(TM) 64-Bit Server VM (build 25.0.3+9-LTS-195, mixed mode, sharing)
javac 25.0.3    # JDK compiler

# Maven
Apache Maven 3.9.16 (2bdd9fddda4b155ebf8000e807eb73fd829a51d5)
Maven home: C:\Program Files\Apache\apache-maven-3.9.16
Java version: 25.0.3, vendor: Oracle Corporation, runtime: C:\Program Files\Java\jdk-25.0.3
Default locale: de_DE, platform encoding: UTF-8
OS name: "windows 10", version: "10.0", arch: "amd64", family: "windows"

# Sonatype Nexus Repository
pull Nexus community Edition Docker image from docker hub: sonatype/nexus3:3.93.2
[sonatype/nexus3 from docker hub](https://hub.docker.com/r/sonatype/nexus3/)
Nexus anonymous access: disabled  
Nexus access: package managers use configured credentials/tokens
URL: http://localhost:8081

Mapping to experiment variables (Sub-RQ1) 
- A1a (group, public-first) → group-public-first repos 
- A1b (group, private-first) → *-group-private-first repos 
- A2 (hosted + separate proxy) → *-internal-hosted + *-public-proxy URLs 
- A3 (hosted-only) → *-internal-hosted only

# Git
git version 2.45.2.windows.1

# Docker
Docker Desktop with WSL 2 backend

- **Docker Desktop 4.79.0** = the Windows app / GUI.
- **Docker Engine 29.5.3** = the actual Docker backend.
- **Docker Compose v5.1.4** = the Compose tool.
- Test command: `docker run hello-world` succeeded
- Docker Desktop updates disabled during experiment runs.


## WSL
WSL-Version: 2.7.8.0
Kernelversion: 6.18.33.1-1
WSLg-Version: 1.0.73.2
MSRDC-Version: 1.2.6676
Direct3D-Version: 1.611.1-81528511
DXCore-Version: 10.0.26100.1-240331-1435.ge-release
Windows-Version: 10.0.19045.6466



# Github Runner
Install runner once.
Do not update it during official experiments.
Document runner version.


Do not randomly upgrade package manager version, docker version later during the experiment, because it could change dependency resolution behavior. Keep the version fixed.


# VS code Extension (not part of the experiment setup)
==all installed==
 - Extension Pack for Java
 - Python
 - Pylance
 - ESLint
 - Prettier
 - GitHub Actions
 - YAML
 - GitLens
 - REST Client
 - Markdown All in One
 - XML
 - Docker
