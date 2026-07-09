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



# Set up runner name and runner labels (only needed for registration)
RUNNER_NAME="${RUNNER_NAME:-$(hostname)}"
RUNNER_LABELS="${RUNNER_LABELS:-thesis-runner}"


# Register this container with GitHub




# Check if this container has already been registered before
# The file .credentials is written by config.sh on successful first registration. and will exist inside container
# So next time if the container start again (not removed), it will keep the credential and doesn't need the registration again
# flag "--replace": if a runner with this name already exists in GitHub's list, replace it. 
# avoid "name already taken" error when restart the container.

if [ -f .credentials ]; then
    echo " .credentials found, runner already registered, skipping config.sh"
else
    echo " no .credentials found, registering runner '${RUNNER_NAME}' with ${GH_REPO_URL}..."

    : "${GH_TOKEN:?GH_TOKEN must be set for first-time registration (get one from GitHub UI)}"

    ./config.sh \
        --unattended \
        --url "${GH_REPO_URL}" \
        --token "${GH_TOKEN}" \
        --name "${RUNNER_NAME}" \
        --labels "${RUNNER_LABELS}" \
        --replace
fi


# suitable cases: 1. first start (need registration).  
# 2. restart (container not removed), doesn't need registration token because credential file is already there
# 3. during official experiment phase, we should fully discard cache between cells, so the runner container
# need to be removed again and again when starting testing new cell, in this case we need to register everytime.


# start the runner and keep it running
exec ./run.sh 