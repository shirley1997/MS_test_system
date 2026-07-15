"""
Generate npm version specifier (variable B2) for npm service
methode: directly modify the original services/nodejs/package.json: but only change the version specifier of internal packages
public packages (e.g. express) are not touched, keep the experiment condition and environment stable
"""

import json
from pathlib import Path
import shutil
import tempfile

# Internal packages of npm service
INTERNAL_PACKAGES = [
    "xueting-thesis-event-jianding",
    "xueting-thesis-service-fasong",
]

# specific value for each version specifier for internal packages
VERSION_SPECIFIERS = {
    "B2a": "1.0.0",   # pinned (exact version)
    "B2b": ">=1.0.0 <2.0.0",  # range (closed, primitive operators)
    "B2c": "*",       # unspecified (matches any version)
}


def generate_npm_version_specifier(B2, package_json_path):
    # Modify original package.json file. Only internal packages' version are changed.
    if B2 not in VERSION_SPECIFIERS:
        raise ValueError(
            f"Unknown B2 variable: {B2!r}. Expected one of {list(VERSION_SPECIFIERS)}."
        )

    specifier = VERSION_SPECIFIERS[B2]
    path = Path(package_json_path)

    with path.open("r", encoding="utf-8") as f:
        npm_package_json = json.load(f)

    deps = npm_package_json.get("dependencies", {})
    for name in INTERNAL_PACKAGES:
        if name in deps:
            deps[name] = specifier

    with path.open("w", encoding="utf-8") as f:
        json.dump(npm_package_json, f, indent=2)
        f.write("\n")  # trailing newline (matches typical package.json style)

    print(f"Applied {B2} ({specifier!r}) to internal packages in {path}")


if __name__ == "__main__":
    # for inspeciftion: create a temp fil to apply these change, 
    # show the changed content of B2a, B2b, B2c without touching the real package.json yet (for debugging).
   

    REPO_ROOT = Path(__file__).resolve().parent.parent.parent
    source = REPO_ROOT / "services" / "nodejs" / "package.json"
    #source = Path("services/nodejs/package.json")

    if not source.exists():
        print(f"package.json not found at: {source.resolve()}, check the path again")
    else:
        #  Create an empty temp file with a random name, copy original package.json content there
        # then apply the changes, finally print the whole content for inspection
        for variable in ["B2a", "B2b", "B2c"]:
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".json", delete=False
            ) as tmp:
                tmp_path = Path(tmp.name)
            shutil.copy(source, tmp_path)
            generate_npm_version_specifier(variable, tmp_path)
            print(f"\n===== {variable} =====")
            print(tmp_path.read_text(encoding="utf-8"))
            tmp_path.unlink()