"""
this script is used to generate pom.xml for java service
pom.xml contains variable B1: package manager configuration -> registry URL configuration
AND dependency version specifier
so in java service CI pipeline, there is no need to produce settings.xml for package manager configuration


Method: hardcoded template overwritten per cell.
- package manager configuration (<repositories> block) represents combination A x B1.
- Version specifier of internal packages (<version> in <dependency>) represents B2.
Public package versions (Javalin, Jackson) are fixed, so that experiment condition stays stable.

Returns:
    str: the pom.xml content.
Raises:
    ValueError for unknown A/B1/B2 or invalid combinations
    (A3 x B1c: A3 has no proxy repo; any B2c: Maven requires <version>).

Note on B2c (unspecified version):
   
    Alternative: "[0,)" (open range) or "LATEST"/"RELEASE" (deprecated).
    but they doesn't mean "unspecified", so can not be used
      this combination should be kept invalid
"""

from pathlib import Path
import tempfile


# Internal packages of Java service (both are DCA-targeted, same specifier per cell)
INTERNAL_PACKAGES = [
    ("com.xueting.thesis", "xueting-thesis-event-juhe"),
    ("com.xueting.thesis", "xueting-thesis-result-fanhui"),
]

# A -> private Nexus repo name (mirrors generate_pip_conf.py A_TO_PRIVATE_REPO)
A_TO_PRIVATE_REPO = {
    "A1a": "maven-group-public-first",
    "A1b": "maven-group-private-first",
    "A2":  "maven-internal-hosted",
    "A3":  "maven-internal-hosted",
}

# Nexus repo that proxies Maven Central (used by B1c)
MAVEN_PUBLIC_PROXY_REPO = "maven-public-proxy"

# B2 -> Maven version string for internal packages
# B2c intentionally omitted -> generate_pom_xml raises ValueError
VERSION_SPECIFIERS = {
    "B2a": "1.0.0",           # pinned
    "B2b": "[1.0.0,2.0.0)",   # range
}


def _nexus_repo_url(nexus_url: str, repo_name: str) -> str:
    return f"{nexus_url}/repository/{repo_name}/"


def _repository_entry(repo_id: str, url: str) -> str:
    return (
        "        <repository>\n"
        f"            <id>{repo_id}</id>\n"
        f"            <url>{url}</url>\n"
        "        </repository>"
    )


def _build_repositories_block(a: str, b1: str, nexus_url: str) -> str:
    """
    Build the <repositories>...</repositories> block.
    Returns "" for B1d (no block -> super POM's Central applies).
    """
    if b1 == "B1d":
        return ""

    private_url = _nexus_repo_url(nexus_url, A_TO_PRIVATE_REPO[a])
    entries = []

    if b1 == "B1a":
        # Only private repo. Override <id>central</id> to private URL -> blocks direct Central.
        entries.append(_repository_entry("central", private_url))
        entries.append(_repository_entry("nexus-private", private_url))

    elif b1 == "B1b":
        # Private repo added. Super POM's Central stays -> direct Maven Central alongside.
        entries.append(_repository_entry("nexus-private", private_url))

    elif b1 == "B1c":
        # Private repo + Nexus proxy of Central (override central -> proxy).
        proxy_url = _nexus_repo_url(nexus_url, MAVEN_PUBLIC_PROXY_REPO)
        entries.append(_repository_entry("central", proxy_url))
        entries.append(_repository_entry("nexus-private", private_url))

    inner = "\n".join(entries)
    return f"    <repositories>\n{inner}\n    </repositories>\n"


def _build_internal_deps_block(b2: str) -> str:
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

    <groupId>com.xueting.thesis</groupId>
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
        # B2c is invalid in Maven -- <version> is a required element per POM Reference.
        raise ValueError(
            f"Unknown or invalid B2: {b2}. "
            f"B2c is invalid in Maven (<version> is required)."
        )

    # 2. Invalid combination
    if a == "A3" and b1 == "B1c":
        raise ValueError("combination A3 x B1c is invalid, A3 doesn't have proxy repo")

    # 3. Build content
    repositories_block = _build_repositories_block(a, b1, nexus_url)
    internal_deps_block = _build_internal_deps_block(b2)
    return POM_TEMPLATE.format(
        repositories_block=repositories_block,
        internal_deps_block=internal_deps_block,
    )


# test case: iterate all combinations, print the generated pom.xml content (or the error)
if __name__ == "__main__":
    NEXUS_URL = "http://host.docker.internal:8081"
    for a in ["A1a", "A1b", "A2", "A3"]:
        for b1 in ["B1a", "B1b", "B1c", "B1d"]:
            for b2 in ["B2a", "B2b", "B2c"]:
                print(f"\n===== {a} x {b1} x {b2} =====")
                try:
                    output = generate_pom_xml(a, b1, b2, NEXUS_URL)
                    print(output)
                except ValueError as e:
                    print(f"INVALID: {e}")