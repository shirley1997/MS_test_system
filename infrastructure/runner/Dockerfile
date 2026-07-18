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
# Add the Python build packages for later python 3.12.4 installation

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
      build-essential \
      libssl-dev \
      zlib1g-dev \
      libbz2-dev \
      libreadline-dev \
      libsqlite3-dev \
      libffi-dev \
      liblzma-dev \
      xz-utils \
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


# desired version: Python 3.12.4 + pip 25.1.1 (fit the development environment)
# Ubuntu 24.04 provides Python 3.12, but its apt repository does not guarantee the exact CPython patch release (3.12.4) required by the experiment.
# Therefore, CPython 3.12.4 is built from the python official source archive

# Exact CPython version which is required by the experiment (keep consistent with the development environment)
ARG PYTHON_VERSION=3.12.4

# Download Python 3.12.4 source release on official page
# It contains the source code, which can be compiled on Linux
# -f: fail on HTTP errors
# -sS: run quietly but still show errors
# -L: follow redirects
# -o: save the archive file under directory /tmp
RUN curl -fsSL "https://www.python.org/ftp/python/${PYTHON_VERSION}/Python-${PYTHON_VERSION}.tar.xz" \
      -o /tmp/python.tar.xz \
    # extract the downloaded python into directory /tmp
    && tar -xf /tmp/python.tar.xz -C /tmp \

    && cd "/tmp/Python-${PYTHON_VERSION}" \

    # Prepare the build:
    # flag --prefix install Python separately under directory /opt instead of replacing Ubuntu's system Python
    # --with-ensurepip: install pip together with Python
    && ./configure \
         --prefix="/opt/python/${PYTHON_VERSION}" \
         --with-ensurepip=install \

    # Compile CPython using all available CPU cores
    && make -j"$(nproc)" \

    # Install the version-specific command python3.12
    # altinstall avoids replacing Ubuntu's default python3 command
    && make altinstall \

    # Install the exact pip version (25.1.1)
    # python3.12 -m pip ensures that pip belongs to this Python installation
    && /opt/python/${PYTHON_VERSION}/bin/python3.12 \
         -m pip install --no-cache-dir "pip==25.1.1" \

    # Verify that the installed interpreter is exactly Python 3.12.4
    && /opt/python/${PYTHON_VERSION}/bin/python3.12 --version \

    # Remove the downloaded archive and source/build files
    # They are not needed after Python is installed, keep the filesystem clean
    && rm -rf \
         /tmp/python.tar.xz \
         "/tmp/Python-${PYTHON_VERSION}"

# add newly installed Python directory at the beginning of PATH
# This allows python3.12 and pip to be found in commands and workflows
ENV PATH="/opt/python/3.12.4/bin:${PATH}"


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