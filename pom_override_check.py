import sys
sys.path.insert(0, "automation_process/config_generator")
# from generate_pom_xml import generate_pom_xml
from check_ID_generate_pom_xml import generate_pom_xml

a, b1, b2, nexus_url, out_path = sys.argv[1:6]
try:
    content = generate_pom_xml(a, b1, b2, nexus_url)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"OK: wrote {out_path}")
except ValueError as e:
    print(f"INVALID: {e}")
    sys.exit(1)
