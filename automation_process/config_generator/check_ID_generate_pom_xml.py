#  Copy of generate_pom_xml.py that never uses "central" as a repository ID 
#  tests whether Super POM's real Central leaks into the effective POM when the id-based override isn't used (see 24.07.2026 log).
# repository in pom.xml generated using configuration combination will not use "central" as repo ID anymore
# instead they use their own ID, like "maven-internal-hosted", "maven-public proxy" etc.

from pathlib import Path
import tempfile


# Internal packages of java service 
INTERNAL_PACKAGES = [
    ("io.github.shirley1997.thesis", "xueting-thesis-event-juhe"),
    ("io.github.shirley1997.thesis", "xueting-thesis-result-fanhui"),
]

# variable A -> private Nexus repo name 
A_TO_PRIVATE_REPO = {
    "A1a": "maven-group-public-first",
    "A1b": "maven-group-private-first",
    "A2":  "maven-internal-hosted",
    "A3":  "maven-internal-hosted",
}

# Maven public proxy repo (proxy to Maven Central public repository) (used by B1c: internal hosted repo + public proxy repo)
MAVEN_PUBLIC_PROXY_REPO = "maven-public-proxy"

# variable B2: Maven version specifier for internal packages
# B2c (unspecified version) intentionally omitted -> generate_pom_xml raises ValueError
VERSION_SPECIFIERS = {
    "B2a": "1.0.0",           # pinned
    "B2b": "[1.0.0,2.0.0)",   # closed range, similar to python, nodejs version specifier
}


def nexus_repo_url(nexus_url: str, repo_name: str) -> str:
    return f"{nexus_url}/repository/{repo_name}/"

# write repository information in pom.xml use variables
def repository_entry(repo_id: str, url: str) -> str:
    return (
        "        <repository>\n"
        f"            <id>{repo_id}</id>\n"
        f"            <url>{url}</url>\n"
        "        </repository>"
    )

# this function is used to build the <repositories>...</repositories> block.
# Returns "" for B1d (means no repository block in pom.xml).
def build_repositories_block(a: str, b1: str, nexus_url: str) -> str:
    if b1 == "B1d":
        return ""

    private_repo_name = A_TO_PRIVATE_REPO[a]
    private_url = nexus_repo_url(nexus_url, private_repo_name)
    entries = []

    if b1 == "B1a":
        # Override <id>central</id> with private URL -> override superPOM
        # Only the private Nexus URL is queried. Id "central" is a Maven mechanism
        # this will be verified in pilot with `mvn help:effective-pom` and `mvn -X` network trace.
        entries.append(repository_entry(private_repo_name, private_url))

    elif b1 == "B1b":
        # Explicit <id>central</id> pointing to real Maven Central + private repo.
        # Technically overrides SuperPOM's central with identical URL (public maven central)
        # done explicitly (rather than inherited) for symmetry with B1a/B1c and readability.
        entries.append(repository_entry("central", "https://repo.maven.apache.org/maven2"))
        entries.append(repository_entry(private_repo_name, private_url))

    elif b1 == "B1c":
        # Override <id>central</id> with nexus maven public proxy + private repo.
        # Direct Central unreachable; public packages resolve through Nexus proxy.
        proxy_url = nexus_repo_url(nexus_url, MAVEN_PUBLIC_PROXY_REPO)
        entries.append(repository_entry(MAVEN_PUBLIC_PROXY_REPO, proxy_url))
        entries.append(repository_entry(private_repo_name, private_url))

    inner = "\n".join(entries)
    return f"    <repositories>\n{inner}\n    </repositories>\n"


def build_dependency_block(b2: str) -> str:
    version = VERSION_SPECIFIERS[b2]
    entries = []
    for group_id, artifact_id in INTERNAL_PACKAGES:
        entries.append(
            "        <dependency>\n"
            f"            <groupId>{group_id}</groupId>\n"
            f"            <artifactId>{artifact_id}</artifactId>\n"
            f"            <version>{version}</version>\n"
            "        </dependency>"
        )
    return "\n".join(entries)


POM_TEMPLATE = """\
<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 https://maven.apache.org/xsd/maven-4.0.0.xsd">
    <modelVersion>4.0.0</modelVersion>

    <groupId>io.github.shirley1997.thesis</groupId>
    <artifactId>aggregate-event-http-api</artifactId>
    <version>1.0.0</version>
    <packaging>jar</packaging>

    <properties>
        <maven.compiler.release>25</maven.compiler.release>
        <project.build.sourceEncoding>UTF-8</project.build.sourceEncoding>
    </properties>

{repositories_block}
    <dependencies>
        <dependency>
            <groupId>io.javalin</groupId>
            <artifactId>javalin</artifactId>
            <version>7.2.2</version>
        </dependency>
{internal_deps_block}
        <dependency>
            <groupId>com.fasterxml.jackson.core</groupId>
            <artifactId>jackson-databind</artifactId>
            <version>2.21.2</version>
        </dependency>
    </dependencies>

    <build>
        <plugins>
            <plugin>
                <groupId>org.apache.maven.plugins</groupId>
                <artifactId>maven-compiler-plugin</artifactId>
                <version>3.15.0</version>
            </plugin>
        </plugins>
    </build>
</project>
"""


def generate_pom_xml(a: str, b1: str, b2: str, nexus_url: str) -> str:
    # 1. Validate inputs
    if a not in A_TO_PRIVATE_REPO:
        raise ValueError(f"Unknown A: {a}")
    if b1 not in {"B1a", "B1b", "B1c", "B1d"}:
        raise ValueError(f"Unknown B1: {b1}")
    if b2 not in VERSION_SPECIFIERS:
        # variable B2c is invalid in Maven: <version> must be set in every dependencies in pom.xml.
        raise ValueError(
            f"Unknown or invalid B2: {b2}. "
            f"B2c is invalid in Maven (<version> must be set)."
        )

    # 2. Invalid combination
    if a == "A3" and b1 == "B1c":
        raise ValueError("combination A3 x B1c is invalid, A3 doesn't have proxy repo")

    # 3. Build content of pom.xml
    repositories_block = build_repositories_block(a, b1, nexus_url)
    internal_deps_block = build_dependency_block(b2)
    return POM_TEMPLATE.format(
        repositories_block=repositories_block,
        internal_deps_block=internal_deps_block,
    )


# show all combinations, print the generated pom.xml content or the error
if __name__ == "__main__":
    NEXUS_URL = "http://host.docker.internal:8081"
    for a in ["A1a", "A1b", "A2", "A3"]:
        for b1 in ["B1a", "B1b", "B1c", "B1d"]:
            for b2 in ["B2a", "B2b", "B2c"]:
                print(f"\n===== configuration combination: {a} x {b1} x {b2} =====")
                try:
                    output = generate_pom_xml(a, b1, b2, NEXUS_URL)
                    print(output)
                except ValueError as e:
                    print(f"INVALID: {e}")