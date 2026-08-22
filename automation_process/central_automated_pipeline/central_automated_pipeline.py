# this is the file of central_automated_pipeline
# the central automated pipeline is divided into several phases, each phase is implemented in order 
# so the function of the whole pipeline can be determined and checked more clean
# and only implement next phase when the current phase is tested and function properly
# this central automated pipeline is used to automatically conduct the experiment for sub-RQ1


import csv
import itertools
import json
from pathlib import Path
import datetime
import subprocess
import requests
import dotenv    # need this to read .env file (for nexus authentication)
import os
import time


A = ["A1a", "A1b", "A2", "A3"]     # nexus repository
B1 = ["B1a", "B1b", "B1c", "B1d"]  # package-manager configuration (which repo URL in A it points to)
B2 = ["B2a", "B2b", "B2c"] # version specifier (pinned / range / unspcified)
C1 = ["C1a", "C1b", "C1c"] # CI pipeline operation type: initial install / package update / rebuild with lockfile
ecosystem = ["nodejs", "python", "java"]
ecosystem_short = {"nodejs":"npm", "python":"pip", "java":"mvn"}  # a dict

internal_version = {"1.0.0", "1.0.2"}    # a set
malicious_version = {"1.0.3"}
internal_packages = {
    "nodejs": ["xueting-thesis-event-jianding", "xueting-thesis-service-fasong"],
    "python": ["xueting-thesis-event-fengfu", "xueting-thesis-service-zhuanfa"],
    "java": ["xueting-thesis-event-juhe", "xueting-thesis-result-fanhui"],
}   # a dict
nexus_url = "http://localhost:8081"
proxy_repo = {
    "nodejs": "npm-public-proxy",
    "python": "pypi-public-proxy",
    "java": "maven-public-proxy"
}# a dict

group_repo = {"nodejs": {"A1a": "npm-group-public-first", "A1b": "npm-group-private-first"}, 
              "python": {"A1a": "pypi-group-public-first", "A1b": "pypi-group-private-first"}, 
              "java": {"A1a": "maven-group-public-first", "A1b": "maven-group-private-first"}
              }

dotenv.load_dotenv()
nexus_username = os.environ.get("nexus_username")
nexus_password = os.environ.get("nexus_password")

service_pipeline_file = {"nodejs": "service-ci-nodejs.yml", 
                         "python": "service-ci-python.yml", 
                         "java": "service-ci-java.yml"}






# phase 1: determine invalid combination & generate experiment matrix
# assume all combinations are valid, only for specific condition it will become invalid
def is_valid_combination(ecosystem, A, B1, B2, C1) -> tuple[bool, str]:
    combi_valid_status = True
    invalid_reason = ""
    if A == "A3" and B1 == "B1c":
        combi_valid_status = False
        invalid_reason = "A3 doesn't have proxy repo"
    if ecosystem == "java" and B2 == "B2c":
        combi_valid_status = False
        invalid_reason = "the version must be specified in each maven dependencies / plugin. maven can't express unspecified version"
    return combi_valid_status, invalid_reason


def generate_matrix() -> list[dict]:
    experiment_matrix = []   # need initilization
    combinations = itertools.product(ecosystem, A, B1, B2, C1)
    for eco, a_option, b1_option, b2_option, c_option in combinations:
        combi_valid_status, invalid_reason = is_valid_combination(eco, a_option, b1_option, b2_option, c_option)
        cell_id = ecosystem_short[eco] + "_" + a_option + "_" + b1_option + "_" + b2_option + "_" + c_option
        row = {
            "cell_id": cell_id,
            "ecosystem": eco,
            "A - private registry configuration": a_option,
            "B1 - package manager configuration": b1_option,
            "B2 - version specifier": b2_option,
            "C - pipeline operation type": c_option,
            "valid?": combi_valid_status,
            "invalid_reason": invalid_reason
        }
        experiment_matrix.append(row)

    return experiment_matrix



def write_matrix_csv(rows_in_matrix, path):
    columns = ["cell_id", "ecosystem", "A - private registry configuration", "B1 - package manager configuration", "B2 - version specifier", "C - pipeline operation type", "valid?", "invalid_reason"]
    with open(path, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=columns)
        writer.writeheader()
        for cell in rows_in_matrix:
            writer.writerow(cell)

    
# phase 2: create checkpoint.json 
# so even the script is suddenly interrupted, it can still can still run from where it left over

def load_finished_cells(checkpoint_path) -> set:
    if Path(checkpoint_path).is_file() == False:   # check if checkpoint file exist
        return set()
    else:
        with open(checkpoint_path, encoding='utf-8') as f:
            checkpoint_list = json.load(f)   #json.load(f) return a python list

        return set(checkpoint_list)     # convert loaded list to a set, set can prevent duplication

def mark_cell_as_finish(checkpoint_path, cell_id):
    finished_cells = load_finished_cells(checkpoint_path)
    finished_cells.add(cell_id)               # set should add new element in place!
    with open(checkpoint_path, "w", encoding='utf-8') as f:
        json.dump(list(finished_cells), f)    # the updated set needs to convert back to list before dump back to checkpoint.json file


def is_finished(cell_id, finished_cells) -> bool:    # check if a cell_id exist in current checkpoint file
    return cell_id in finished_cells

#phase 3: write result in result.csv file
# this function should receive the row_to_append
# this function append the row it receives to the results.csv, which saves in result_file_path

def write_result_file(result_file_path, row_to_append):
  
    columns = ["cell_id", "timestamp", 
               "ecosystem", "A - private registry configuration", 
               "B1 - package manager configuration", 
               "B2 - version specifier", 
               "C - pipeline operation type", 
               "classification",
               "pk1_name", "pk1_version", "pk1_url",
               "pk2_name", "pk2_version", "pk2_url",
                "artifact_path", "git_commit", "github_run_id"]

    #check if file exist first! if the file is already opened, it will always return true
    file_already_exist = Path(result_file_path).is_file()
    with open(result_file_path, 'a', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=columns)
        if file_already_exist == False:     # only write header if file doesn't exist yet, otherwise more than one row header
            writer.writeheader()
        writer.writerow(row_to_append)


# phase 4: the classification logic
# the following 3 ecosystem-specific functions are used to check artifact uploaded from service pipeline
# will return a list[dict] for found internal package information
#example return value: [{"name": str, "version": str, "url": str}, {"package": str, "version": str, "url": str}]

def read_npm_evidence(package_lock_path) -> list[dict]:
    try:
        with open(package_lock_path, 'r', encoding='utf-8') as json_File:
            package_lock_data = json.load(json_File)
    except:
        return None
    
    npm_package_found = []     # create an empty list
    package_area = package_lock_data["packages"]

    for npm_package_name in internal_packages["nodejs"]:
        for package_key, info in package_area.items():
            if package_key == f"node_modules/{npm_package_name}":
                npm_package_found.append(
                    {"name": npm_package_name,
                     "version": info.get("version"),
                     "url": info.get("resolved"),}
                )
    return npm_package_found

def read_pip_evidence(install_report_path) -> list[dict]:
    try:
        with open(install_report_path, 'r', encoding='utf-8') as json_File:
            install_report_data = json.load(json_File)   
    except Exception as e:
        print(e)
        return None

    pip_package_found = []     # create an empty list
    package_area = install_report_data["install"]   # "install" is a list

    for pip_package_name in internal_packages["python"]:
        for item in package_area:
            if item["metadata"].get("name") == pip_package_name:
                pip_package_found.append(
                    {   "name": pip_package_name,
                        "version": item["metadata"].get("version"),
                        "url": item["download_info"].get("url"),}
                )
    return pip_package_found

def read_java_evidence(java_cell) -> list[dict]:
    cell_id = java_cell["cell_id"]
    java_c1_value = java_cell["C - pipeline operation type"]
    try:
        if java_c1_value == "C1a" or java_c1_value == "C1b":
            with open(f"{cell_id}_lockfile.json", 'r', encoding='utf-8') as json_file:
                mvn_lockfile_data = json.load(json_file)    # json_file is a file object, json.load() should be used here
        else:
            with open(f"{cell_id}_rebuild-lockfile.json", 'r', encoding='utf-8') as json_file:            
                mvn_lockfile_data = json.load(json_file)
    except:
        return None

    mvn_package_found = []     # create an empty list
    package_area = mvn_lockfile_data["dependencies"]   # "dependencies" is a list
    
    for mvn_package_name in internal_packages["java"]:
        for item in package_area:
            if item["artifactId"] == mvn_package_name:
                mvn_package_found.append(
                    {   "name": mvn_package_name,
                        "version": item["version"],
                        "url": item["resolved"],
                    }
                )
    return mvn_package_found
    
# package_evidence is the list[dict] (or None) which is the return value from the 3 functions above
# the classification logic need to be checked again

def classify_logic(ecosystem, package_evidence) -> str:
    
    if package_evidence == None:
        return "resolution_error"
    for evidence in package_evidence:
        if evidence["version"] in malicious_version:
            return "malicious_resolved"

    expected_count = len(internal_packages[ecosystem])
    count_in_evidence = 0
    for evidence in package_evidence:
        if evidence["version"] in internal_version:
            count_in_evidence += 1
    if count_in_evidence == expected_count:
            return "private_resolved"
        

    return "resolution_error"



# phase 5: nexus cache invalidation for group repo and proxy repo
# the requests for cache invalidation needs authentication! otherwise obtain code 403

def invalidate_nexus_cache(ecosystem, cell_A_option):
    proxy_invalidate_url = f"{nexus_url}/service/rest/v1/repositories/{proxy_repo[ecosystem]}/invalidate-cache" 
    proxy_invalidate_response = requests.post(proxy_invalidate_url, auth=(nexus_username, nexus_password))
    if proxy_invalidate_response.status_code != 204:
        print(f"proxy repo cache invalidation did not succeed. code {proxy_invalidate_response.status_code} for {proxy_repo[ecosystem]}")
    print(f"cache of {proxy_repo[ecosystem]} discarded")

    if cell_A_option == "A1a" or cell_A_option == "A1b":
        group_invalidate_url = f"{nexus_url}/service/rest/v1/repositories/{group_repo[ecosystem][cell_A_option]}/invalidate-cache"
        group_invalidate_response = requests.post(group_invalidate_url, auth=(nexus_username, nexus_password))
        if group_invalidate_response.status_code != 204:
            print(f"group repo cache invalidation did not succeed. code {group_invalidate_response.status_code} for {group_repo[ecosystem][cell_A_option]}")
        print(f"cache of {proxy_repo[ecosystem]} and {group_repo[ecosystem][cell_A_option]} discarded")

# phase 7: set up connection between central automated pipeline and github actions runner
# 1. use gh api to get registration token, which is needed for connect a runner with github
# 2. use gh api to start the runner, put the obtained token as a parameter in the start command
# 3. use gh api to check if the self-hosted runner is online before dispatch a workflow
# Note: the git repo address is not hard coded here, so this code can still be used for other user / repository
def get_registration_token(owner, repo) -> str:
   token = subprocess.run(["gh", "api", 
                           "--method", "POST", "-H", 
                           "Accept: application/vnd.github+json",
                           "-H", 'X-GitHub-Api-Version: 2026-03-10', 
                           f"repos/{owner}/{repo}/actions/runners/registration-token",
                           "--jq", ".token"],
                        check=True,
                        capture_output=True,
                        text=True,).stdout.strip()
   return token

# add --rm option so container can be self-removed after ephemeral runner de-registered
def start_runner_container (cell_id, token, repo_url, image_tag) -> str:
    start_runner = subprocess.run(
    [
        "docker", "run", "-d", "--rm",
        "--name", f"thesis-runner-{cell_id}",   # set up container name
        "-e", f"GH_REPO_URL={repo_url}",
        "-e", f"GH_TOKEN={token}",
        "-e", "RUNNER_LABELS=thesis-runner",
        "-e", f"RUNNER_NAME=thesis-runner-{cell_id}",   # set up the runner name, so we can look for specific runner to check online status
        image_tag,
    ],
    check=True,
    capture_output=True,
    text=True,
).stdout.strip()
    return start_runner

# "docker run -d" returns as soon as the container process starts (create a new runner container),
# not once the runner inside has actually finished registering with GitHub 
# there's a gap between "container started" and "runner ready to accept jobs,"
# so dispatching a workflow immediately risks a race condition (two things happening at once, in an unpredictable order relative to each other)
# Without this check: if a runner's registration/startup fails (bad token, container crash, network issue etc.),
#  the later gh run watch step (obeserve workflow run) has no timeout of its own and would hang forever
# waiting for a runner that never shows up. 
# This function is what catches that within a defined time interval so the pipeline can move on to the next cell.
def wait_for_runner_online(owner, repo, expected_runner_name, timeout_s=60, check_interval_s=5) -> bool:
    current_time = 0
    while current_time <= timeout_s:
        runner_info = subprocess.run(
            ["gh", "api", f"repos/{owner}/{repo}/actions/runners"],
            capture_output=True,
            text=True,
        )
        runners_data = json.loads(runner_info.stdout)   # loads a string

        for runner in runners_data["runners"]:
            if runner["name"] == expected_runner_name and runner["status"] == "online":
                return True   
            
        time.sleep(check_interval_s)   # run the command every 5 seconds
        current_time += check_interval_s

    return False

# phase 8: dispatch service pipeline (workflow) according to the cell
# and download the artifacts (a zip file containing evidence) produced by service pipeline

def dispatch_cell(owner, repo, ecosystem, cell):
    subprocess.run(
    [
        "gh", "workflow", "run", service_pipeline_file[ecosystem],
        "--repo", f"{owner}/{repo}",
        "-f", f"cell_id={cell["cell_id"]}",
        "-f", f"A={cell["A - private registry configuration"]}",
        "-f", f"B1={cell["B1 - package manager configuration"]}",
        "-f", f"B2={cell["B2 - version specifier"]}",
        "-f", f"C1={cell["C - pipeline operation type"]}",
    ],
    check=True,
    capture_output=True,
    text=True,
)

def find_run_id(owner, repo, service_pipeline_file, cell_id) -> str:
    workflow_run_info = subprocess.run(
    [
        "gh", "run", "list",
        "--repo", f"{owner}/{repo}",
        "--workflow", service_pipeline_file,
        "--limit", "1",
        "--json", "databaseId,status,createdAt",
    ],
    check=True,
    capture_output=True,
    text=True,
)
    workflow_data = json.loads(workflow_run_info.stdout)
    workflow_run_id = workflow_data[0]["databaseId"]
    return str(workflow_run_id)   # return an int!! need to wrap it as str(run_id)

# observe workflow (service pipeline) run 
# check = False: a failed run should still go to classification, not raise. 
# if check = True, it raise an exception and kill the loop on the first failed cell
def wait_for_run_complete(owner, repo, run_id, timeout_s):
    subprocess.run(
    ["gh", "run", "watch", str(run_id), "--repo", f"{owner}/{repo}", "--exit-status", "--compact"],
    check=False,   
    capture_output=True,
    text=True,
)

def download_artifact(owner, repo, run_id, artifact_name, dest_dir):
    try:
        subprocess.run(
            [
                "gh", "run", "download", str(run_id),
                "--repo", f"{owner}/{repo}",
                "-n", artifact_name,
                "-D", dest_dir,
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        return dest_dir
    except:
        return None

    








if __name__ == "__main__":

    # a test for phase 1
    full_experiment_matrix = generate_matrix()
    write_matrix_csv(full_experiment_matrix, "automation_process/central_automated_pipeline/experiment_matrix.csv")
    print(f"finish generating experiment_matrix.csv , {len(full_experiment_matrix)} rows in total")
    checkpoint_path = Path('automation_process/central_automated_pipeline/checkpoint.json')

    # a test for phase 2
    mark_cell_as_finish(checkpoint_path, "npm_A1a_B1a_B2c_C1a")
    mark_cell_as_finish(checkpoint_path, "mvn_A1a_B1a_B2b_C1a")
    checkpoint_load= load_finished_cells(checkpoint_path)

    print(is_finished("npm_A1a_B1a_B2c_C1a", checkpoint_load))
    print(is_finished("mvn_A1a_B1a_B2b_C1a", checkpoint_load))
    print(is_finished("pip_A1a_B1a_B2b_C1a", checkpoint_load))
        

    # a test for phase 3
    result_file_path = Path('automation_process/central_automated_pipeline/results.csv')

    test_row = {
    "cell_id": "npm_A1a_B1a_B2a_C1a",
    "timestamp": datetime.datetime.now(),
    "ecosystem": "nodejs",
    "A - private registry configuration": "A1a",
    "B1 - package manager configuration": "B1a",
    "B2 - version specifier": "B2a",
    "C - pipeline operation type": "C1a",
    "classification": "private_resolved",
    "pk1_name": "xueting-thesis-event-jianding",
    "pk1_version": "1.0.0",
    "pk1_url": "http://localhost:8081/repository/npm-internal-hosted/fake/path",
    "pk2_name": "xueting-thesis-service-fasong",
    "pk2_version": "1.0.0",
    "pk2_url": "http://localhost:8081/repository/npm-internal-hosted/fake/path2",
    "artifact_path": "fake/path",
    "git_commit": "adfiuahfdfihvfoih",
    "github_run_id": "99999999999999999",
}

    write_result_file(result_file_path, test_row)


    #  test for phase 4
    print(classify_logic("nodejs", None))    # verified result: resolution_error

    print(classify_logic("nodejs", [
    {"name": "xueting-thesis-event-jianding", "version": "1.0.0", "url": "x"},
    {"name": "xueting-thesis-service-fasong", "version": "1.0.0", "url": "x"},
]))

    print(classify_logic("nodejs", [
    {"name": "xueting-thesis-event-jianding", "version": "1.0.3", "url": "x"},
    {"name": "xueting-thesis-service-fasong", "version": "1.0.0", "url": "x"},
]))

    print(classify_logic("nodejs", [
    {"name": "xueting-thesis-event-jianding", "version": "1.0.0", "url": "x"},
]))     
    print(classify_logic("nodejs", [
    {"name": "xueting-thesis-event-jianding", "version": "2.5.0", "url": "x"},
    {"name": "xueting-thesis-service-fasong", "version": "1.0.0", "url": "x"},
]))


    package_evidence = read_pip_evidence(Path("services/python/test-install-report3.json"))
    print(classify_logic("python", package_evidence))

# a test for phase 5
    invalidate_nexus_cache("nodejs", "A1a")

# no code test needed for phase 6, only manually operation, the output is already observed, test passed

# phase 7: test file in automation_process\central_automated_pipeline\test_phase7.py


