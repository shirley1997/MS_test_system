# this python script is used to generate pip.conf for python service while conducting the sub-RQ1 experiment
"""
Generates pip.conf content for combination (A × B1) (for python service).

Return:
    str: the pip.conf content
    None: if variable B1d (no config file should be generated)
Raises:
    ValueError for invalid combinations (A3 × B1c) (A3 doesn't have proxy repo) or unknown A/B1 values.
"""


# define the private repo (Nexus)
A_TO_PRIVATE_REPO = {
    "A1a": "pypi-group-public-first",
    "A1b": "pypi-group-private-first",
    "A2":  "pypi-internal-hosted",
    "A3":  "pypi-internal-hosted",
}


# because Pypi's simple repository URL, nexus python repo also need to add /simple/ to its URL
# nexus URL as variable but not hard coded: http://localhost:8081 locally, 
# http://host.docker.internal:8081 in the runner container 
def _nexus_index_url(nexus_url: str, repo_name: str) -> str:
    return f"{nexus_url}/repository/{repo_name}/simple/"

PUBLIC_PYPI_URL = "https://pypi.org/simple/"


# main function to generate pip.conf (because the runner is based on Linux)
# structure similar to generate_npmrc.py
def generate_pipconf(a: str, b1: str, nexus_url: str) -> str | None:
    # 1. Validate inputs
    if a not in A_TO_PRIVATE_REPO:
        raise ValueError(f"Unknown A: {a}")
    if b1 not in {"B1a", "B1b", "B1c", "B1d"}:
        raise ValueError(f"Unknown B1: {b1}")

    # 2. B1d: no file will be generated
    if b1 == "B1d":
        return None

    # 3. Invalid combination
    if a == "A3" and b1 == "B1c":
        raise ValueError("combination A3 x B1c is invalid, A3 doesn't have proxy repo")

    # 4. Build content
    private_url = _nexus_index_url(nexus_url, A_TO_PRIVATE_REPO[a])
    lines = ["[global]", f"index-url = {private_url}"]

    # configurate configurate second registry URL: public registry URL or Nexus pypi public proxy repo URL
    if b1 == "B1b":
        lines.append(f"extra-index-url = {PUBLIC_PYPI_URL}")
    elif b1 == "B1c":
        lines.append(f"extra-index-url = {_nexus_index_url(nexus_url, 'pypi-public-proxy')}")
    # B1a: only one single URL for repo, no extra-index-url line needed

    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    NEXUS_URL = "http://host.docker.internal:8081"   
    for a in ["A1a", "A1b", "A2", "A3"]:
        for b1 in ["B1a", "B1b", "B1c", "B1d"]:
            print(f"\n===== {a} × {b1} =====")
            try:
                output = generate_pipconf(a, b1, NEXUS_URL)
                print(output if output is not None else "no pip.conf will be generated: variable B1d)")
            except ValueError as e:
                print(f"INVALID: {e}")