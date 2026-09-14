import json
from pathlib import Path


script_folder = Path(__file__).resolve().parent
artifact_folder = script_folder.parent / "0809" / "artifact_download"

# ----------------------------- for npm cells------------------------------------
# Compare the phase-1 (setup phase) lockfile (after initial install, before running "npm update") with the phase-2 lockfile (after package update)
# compare lockfiles in one npm cell, observe the entry change of one public dependency and one internal package
# uncover why not-pinned cell npm_A2_B1a_B2b_C1b is "private_resolved"
# but npm_A2_B1a_B2b_C1a (only C1 option is different) has "resolution error"
def compare_npm_lockfiles(cell_id, package_names):

    cell_folder = artifact_folder / cell_id
    setup_file = cell_folder / (cell_id + "_setup-package-lock.json")
    final_file = cell_folder / "package-lock.json"

    # load json file to a dictionary, easier to get specific content based on their key
    setup_lock = json.load(open(setup_file, encoding="utf-8"))
    final_lock = json.load(open(final_file, encoding="utf-8"))

    print("[cell]:", cell_id)
    for name in package_names:
        key = "node_modules/" + name
        before = setup_lock["packages"][key]
        after = final_lock["packages"][key]

        print("[dependency name]:   ", name)
        print("        phase 1 (before update):", before["version"], before["resolved"])
        print("        phase 2 (after update): ", after["version"], after["resolved"])
        if before == after:
            print("-> entry (package version / resolved URL) not change")
        else:
            print("-> entry (package version / resolved URL) CHANGED")

# ----------------------------- for maven cells------------------------------------

# Compare the phase-1 lockfile (setup phase, used a pinned POM.xml) with the phase-2 lockfile (after package update)
# phase 2 uses the cell's own POM, and use command "mvn -U"
# compare the lockfiles from 2 phases in one Maven cell. Prints the information of all direct dependencies.
def compare_maven_lockfiles(cell_id):

    cell_folder = artifact_folder / cell_id
    setup_file = cell_folder / (cell_id + "_setup-lockfile.json")
    final_file = cell_folder / (cell_id + "_lockfile.json")

    for phase_name, lock_file in [("phase 1 (setup phase, initial install)", setup_file), ("phase 2 (package update)", final_file)]:
        maven_lock = json.load(open(lock_file, encoding="utf-8"))

        print("[cell]:", cell_id, "-", phase_name)
        for dependency in maven_lock["dependencies"]:
            resolved = dependency["resolved"]
            if resolved == "":
                resolved = "(this field is empty - which means it's not downloaded from a remote repository)"
            print("[dependency name]:   ", dependency["artifactId"],
                  " [version]:", dependency["version"],
                  " [resolved]:", resolved)
        print()





# check the entry (package version / resolved URL) of one public dependency, one internal package
# check npm cell and maven cell seperately
def main():
    #compare_npm_lockfiles("npm_A2_B1a_B2b_C1b",
                          #["xueting-thesis-event-jianding", "xueting-thesis-service-fasong", "express"])
    compare_maven_lockfiles("mvn_A2_B1a_B2b_C1b")


main()