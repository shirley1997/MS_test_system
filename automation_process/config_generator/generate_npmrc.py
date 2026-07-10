"""
This script generates the content of an .npmrc file for one experiment cell (for npm service),
based on variables A (Nexus repo type) and B1 (package manager configuration)

This script is used by node.js CI pipeline YAML file before running `npm install --dry-run --json` to obtain resolution output

Some Design decisions:

- The internal npm packages in this thesis are UNSCOPED.
  This is intentional: package with scoped names and scope-based routing is a security-hardening method which can mitigate dependency confusion,
  this is out of scope for the research question sub-RQ1

- The test Variable B1b and B1c contain TWO `registry=` lines and doesn't use scope-routing.



"""



# Mapping from variable A to the Nexus repo that .npmrc's `registry=` line will point to (the "private-facing entry point" for the cell)
# These names exactly match the Nexus repo names configured manually in Nexus during the one-time setup step

A_TO_PRIVATE_REPO = {
    "A1a": "npm-group-public-first",
    "A1b": "npm-group-private-first",
    "A2":  "npm-internal-hosted",
    "A3":  "npm-internal-hosted",
}

# Name of the public-proxy repo in Nexus (used only for B1c).
# A3 only has internal hosted repo, does NOT have proxy repo -> combination A3 x B1c is invalid.
PUBLIC_PROXY_REPO = "npm-public-proxy"

# The public npm registry, used in B1b.
PUBLIC_REGISTRY_URL = "https://registry.npmjs.org"


def generate_npmrc(A, B1, nexus_url):
    """
    This function return .npmrc content for a given (A, B1) cell.

    nexus_url : str
    Base URL of the Nexus server, e.g. "http://localhost:8081" for local dev, 
    or "http://host.docker.internal:8081" for use inside the runner container.


    Returns:
    str  -> the .npmrc file content to write.
    None -> no .npmrc file is written (B1d = "default", meaning no config file).

    
    If A or B1 is unknown, or if the combination is invalid (currently only A3 x B1c) 
    -> raise value error
    """

    #1. Validate the A value and look up the private-hosting repo
    # get clear error message earlier if A is typed wrong
    if A not in A_TO_PRIVATE_REPO:
        raise ValueError(f"Unknown A value: {A!r}")

    private_repo = A_TO_PRIVATE_REPO[A]

    # set up the Nexus repo URL that will appear in the `registry=` line (in .npmrc file)
    private_registry_url = f"{nexus_url}/repository/{private_repo}/"

    #2. construct the file content for corresponding test variables
    # B1a: single private registry URL.
    # B1a only  has one line of `registry=` , which points at the A-derived Nexus repo (group repo URL, or internal-hosted repo URL).
    if B1 == "B1a":
        return f"registry={private_registry_url}\n"

    # B1b: multiple registry URLs with direct public access.
    if B1 == "B1b":
        #return (
        #    f"registry={private_registry_url}\n"
        #    f"registry={PUBLIC_REGISTRY_URL}\n"
        #)
        return (
            f"registry={PUBLIC_REGISTRY_URL}\n"
            f"registry={private_registry_url}\n"
            
        )

    # B1c: multiple registry URLs with public access via Nexus proxy.
    if B1 == "B1c":
        # A3 has only internal-hosted repo, no proxy repo -> the combination (A3 x B1c) is invalid.
        if A == "A3":
            raise ValueError(
                "Invalid combination: variable A3 does not have public-proxy repo, so B1c cannot be constructed"
                
            )
        proxy_url = f"{nexus_url}/repository/{PUBLIC_PROXY_REPO}/"
        return (
            f"registry={private_registry_url}\n"
            f"registry={proxy_url}\n"    
        )

    # B1d: default (no .npmrc set up) -> no .npmrc file is generated -> return None 
    if B1 == "B1d":
        return None

    # if unknown B1 value -> raise error
    raise ValueError(f"Unknown B1 value: {B1!r}")



# print the generator's output for every (A, B1) cell for inspection

if __name__ == "__main__":
    test_nexus_url = "http://host.docker.internal:8081"

    A_values  = ["A1a", "A1b", "A2", "A3"]
    B1_values = ["B1a", "B1b", "B1c", "B1d"]

    for A in A_values:
        for B1 in B1_values:
            print("=" * 60)
            print(f"Cell: A={A}, B1={B1}")
            print("-" * 60)
            try:
                result = generate_npmrc(A, B1, test_nexus_url)
                if result is None:
                    print("(no .npmrc file generated -> variable B1d)")
                else:
                    # for each combination, print the file content of .npmrc 
                    print(result, end="")
            except ValueError as e:
                print(f"INVALID: {e}")
            print()