"""
Generate python version specifier (variable B2) for python service
method: crate a hardcoded pyproject.toml based on the existing pyproject.toml, then overwrite it
only change the version specifier of internal packages to represent variable B2
Public package version (e.g. Flask) are fixed, experiment condition stays stable.
"""

from pathlib import Path
import tempfile

# Internal packages of python service
INTERNAL_PACKAGES = [
    "xueting-thesis-event-fengfu",
    "xueting-thesis-service-zhuanfa",
]

VERSION_SPECIFIERS = {
    "B2a": "==1.0.0",
    "B2b": ">=1.0.0,<2.0.0",
    "B2c": "",
}


PYPROJECT_TEMPLATE = """\
[project]
name = "process-event-http-api"
version = "1.0.0"
description = "process event service, responsible to add extra fields to events and sends to the java service"
requires-python = ">=3.12,<3.13"

dependencies = [
    
    "Flask==3.1.1",
{internal_deps}
]
"""

def generate_python_version_specifier(B2, pyproject_path):
    if B2 not in VERSION_SPECIFIERS:
        raise ValueError(
            f"Unknown B2 variable: {B2!r}. Expected one of {list(VERSION_SPECIFIERS)}."
        )

    specifier = VERSION_SPECIFIERS[B2]
    internal_lines = ",\n".join(
        f'    "{name}{specifier}"' for name in INTERNAL_PACKAGES
    )
    content = PYPROJECT_TEMPLATE.format(internal_deps=internal_lines)

    path = Path(pyproject_path)
    path.write_text(content, encoding="utf-8")
    print(f"Applied {B2} ({specifier!r}) to internal packages in {path}")

#test case: print the generated pyproject.toml content in a temp file, not change the existing pyproject.toml
if __name__ == "__main__":
    
    for variable in ["B2a", "B2b", "B2c"]:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as tmp:
            tmp_path = Path(tmp.name)
        generate_python_version_specifier(variable, tmp_path)
        print(f"\n===== variable {variable} =====")
        print(tmp_path.read_text(encoding="utf-8"))
        tmp_path.unlink()