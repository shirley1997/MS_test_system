# GitHub Actions self-hosted runner for dependency confusion experiments
# Base image        : Ubuntu 24.04
# Toolchains (pinned) : Node 24.18.0, npm 11.16.0, Python 3.12.4, pip 25.1.1,
#                     Temurin JDK 25.0.3, Maven 3.9.16, Git 2.45.2
# Runner binary     : v2.335.1 (SHA-256 verified)
# Registration mode : persistent (single long-lived runner)
# Token supply      : runtime enviroment variable (token is short-lived, should not be embedded inside container)


FROM ubuntu:24.04

# choose non-interactive apt, so package install don't wait for prompts.
ENV DEBIAN_FRONTEND=noninteractive


# System packages: minimal set for the runner and toolchain installation
# curl, ca-certificates: download toolchain tarballs and runner binary
# gnupg: verify NodeSource + Adoptium apt signatures
# tar, gzip: unpack the runner tarball
# git: GHA needs it for `actions/checkout`
# jq: useful in workflows for parsing JSON
# libicu74: required by the .NET runtime that ships in the runner
# sudo: the runner's install-dependencies script expects it

RUN apt-get update && apt-get install -y --no-install-recommends \
      curl \
      ca-certificates \
      gnupg \
      tar \
      gzip \
      git \
      jq \
      libicu74 \
      sudo \
    && rm -rf /var/lib/apt/lists/*


# need install Node.js 24.18.0 + npm 11.16.0 in ubuntu docker -> nvm is not the right tool for docker!
# Base image Ubuntu 24.04's apt repo doesn't contain node.js v24
# so Install through NodeSource repo (stackoverflow says a community-standard way to pin node versions on Ubuntu docker container)
# will still use apt to install specific nodejs version (24.18.0)
# source of commands: https://askubuntu.com/questions/720784/how-to-install-latest-node-inside-a-docker-container 
# https://nodesource.com/products/distributions

RUN curl -fsSL https://deb.nodesource.com/setup_24.x | bash - \
    && apt-get install -y --no-install-recommends nodejs=24.18.0-1nodesource1 \
    && npm install -g npm@11.16.0 \
    && rm -rf /var/lib/apt/lists/*


# Python 3.12.4 + pip 25.1.1
# Ubuntu 24.04 has Python 3.12 by default. only need to pin the package manager pip explicitly.
# --break-system-packages is required on Ubuntu 24.04 because the system python is marked externally-managed. 
# without this flag, error will be shown. (we can create an venv to solve this problem but not nessasary for the experiment setup)
# source of commands: https://leimao.github.io/blog/Docker-Python-Setup/

RUN apt-get update && apt-get install -y --no-install-recommends \
      python3.12 \
      python3-pip \
      python3-venv \
    && python3 -m pip install --break-system-packages --ignore-installed pip==25.1.1 \
    && python3 -m pip --version \
    && rm -rf /var/lib/apt/lists/*


# install java use eclipse-temurin from Adoptium's apt repo. (openjdk docker image is deprecated)
# Adoptium is the Eclipse Foundation's OpenJDK distribution 
# design decision: base image Ubuntu 24.04 + tool chain on top of it
# so can not directly use eclipse-temurin:25-jdk as base image
# The package "temurin-25-jdk" installs the jdk (needs javac + mvn compilation, not JRE)
# official doc for install commands: https://adoptium.net/installation



RUN apt-get update && apt-get install -y --no-install-recommends wget apt-transport-https gpg \
    && wget -qO - https://packages.adoptium.net/artifactory/api/gpg/key/public \
       | gpg --dearmor \
       | tee /etc/apt/trusted.gpg.d/adoptium.gpg > /dev/null \
    && echo "deb https://packages.adoptium.net/artifactory/deb $(awk -F= '/^VERSION_CODENAME/{print$2}' /etc/os-release) main" \
       > /etc/apt/sources.list.d/adoptium.list \
    && apt-get update && apt-get install -y --no-install-recommends temurin-25-jdk \
    && rm -rf /var/lib/apt/lists/*

ENV JAVA_HOME=/usr/lib/jvm/temurin-25-jdk-amd64
ENV PATH="${JAVA_HOME}/bin:${PATH}"


# Maven 3.9.16
# Downloaded from the official Apache Archive Distribution Directory (versions will be moved to /dist
# archive after new releases come out, so archive is the stable pinning URL).

# What each line does:
# 1. Download the Maven binary tarball to a temp location.
# 2. Extract it into /opt (standard Linux location for optional software).
#    -> /opt/apache-maven-3.9.16/.
# 3. Create a symlink doesn't contain version /opt/maven -> /opt/apache-maven-3.9.16
# no need for hardcoded version
#    so a change of version only changes the ARG.
# 4. Delete the tarball at the end.

ARG MAVEN_VERSION=3.9.16
RUN curl -fsSL "https://archive.apache.org/dist/maven/maven-3/${MAVEN_VERSION}/binaries/apache-maven-${MAVEN_VERSION}-bin.tar.gz" \
      -o /tmp/maven.tar.gz \
    && tar -xzf /tmp/maven.tar.gz -C /opt \
    && ln -s /opt/apache-maven-${MAVEN_VERSION} /opt/maven \
    && rm /tmp/maven.tar.gz

ENV MAVEN_HOME=/opt/maven
ENV PATH="${MAVEN_HOME}/bin:${PATH}"


# set up non-root user for the runner cause GHF runner rejects to to run as root -> create user called "runner"

RUN useradd -m -s /bin/bash runner \
    && echo "runner ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers

USER runner
WORKDIR /home/runner


# choose to use GitHub Actions runner binary v2.335.1 (Linux x64).
# SHA-256 verification means the build fails if the tarball is correpted (protect integrity)
# The checksum source: https://github.com/actions/runner/releases/tag/v2.335.1

# IMPORTANT!: This is the one version in the image that may need to be changed during experiments.
# GitHub enforces a 30-day update window before a runner stops receiving jobs.
# change both RUNNER_VERSION and RUNNER_SHA256 together, then rebuild.
# source about github rules: https://docs.github.com/en/actions/reference/runners/self-hosted-runners
# remove tar.gz file at the end to save space

ARG RUNNER_VERSION=2.335.1
ARG RUNNER_SHA256=4ef2f25285f0ae4477f1fe1e346db76d2f3ebf03824e2ddd1973a2819bf6c8cf

RUN curl -fsSL -o runner.tar.gz \
      "https://github.com/actions/runner/releases/download/v${RUNNER_VERSION}/actions-runner-linux-x64-${RUNNER_VERSION}.tar.gz" \
    && echo "${RUNNER_SHA256}  runner.tar.gz" | sha256sum -c - \
    && tar xzf runner.tar.gz \
    && rm runner.tar.gz

# The runner use "installdependencies.sh" script that installs the
# specific .NET runtime libs the binary needs. Run it once at build time so
# every container start is fast (no per-start apt install).
RUN sudo ./bin/installdependencies.sh

# test: registers on container start, de-registers on stop.

COPY --chown=runner:runner entrypoint.sh /home/runner/entrypoint.sh
RUN chmod +x /home/runner/entrypoint.sh

ENTRYPOINT ["/home/runner/entrypoint.sh"]