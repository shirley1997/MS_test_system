#!/bin/bash

# A script that runs every time the container starts.
# A GitHub Actions self-hosted runner needs to do 3 things:
#     1. Tell GitHub "hi, I exist, send me jobs" (REGISTERING)
#     2. wait for GitHub to send jobs, then run the jobs


#   Without step 3, every time restart the container, GitHub thinks the old runner is still around. 
# After a few restarts (e.g. during experiment or testing), GitHub's UI will show a lot of "offline" dead runners in the list.

# About this script:
# Every time `docker run` starts a new container from image.
# The Dockerfile ends with `ENTRYPOINT ["/home/runner/entrypoint.sh"]` 
# means "run this script when the container starts, and keep the container alive as long as this script is running."
#
# things must be provided:
#   GH_REPO_URL   github repo of thesis
#   GH_TOKEN      A one-time registration token from GitHub. expires in 1 hour

# Optional things to pass:
#   RUNNER_NAME   What to call this runner in GitHub's UI. Default: the container's hostname (some random Docker ID).

#   RUNNER_LABELS Labels are how workflows say "run me on THIS kind of runner"
# (e.g. `runs-on: thesis-runner`). Default: thesis-runner



# Flag:
#   -e  : stop the script immediately if any command fails (without this, errors would be silently ignored and things would get weird later)
#   -u  : stop if the script tries to use a variable that doesn't exist, prevent typos in variable names
#   -o pipefail : if a chain of a piped command (a | b | c) has any failure, treat the whole chain as failed

set -euo pipefail


# Check the required env variables are set. -> stop the script early with clear error message

: "${GH_REPO_URL:?GH_REPO_URL must be set}"
: "${GH_TOKEN:?GH_TOKEN must be set (registration token from GitHub UI)}"


# Set up runner name and runner labels
RUNNER_NAME="${RUNNER_NAME:-$(hostname)}"
RUNNER_LABELS="${RUNNER_LABELS:-thesis-runner}"


# Register this container with GitHub
# flag "--replace": if a runner with this name already exists in GitHub's list, replace it. 
# avoid "name already taken" error when restart the container.

echo "[entrypoint] registering runner '${RUNNER_NAME}' with ${GH_REPO_URL}..."
./config.sh \
    --unattended \
    --url "${GH_REPO_URL}" \
    --token "${GH_TOKEN}" \
    --name "${RUNNER_NAME}" \
    --labels "${RUNNER_LABELS}" \
    --replace   



# start the runner and keep it running.
./run.sh 