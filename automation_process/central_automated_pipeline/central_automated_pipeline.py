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


A = ["A1a", "A1b", "A2", "A3"]     # nexus repository
B1 = ["B1a", "B1b", "B1c", "B1d"]  # package-manager configuration (which repo URL in A it points to)
B2 = ["B2a", "B2b", "B2c"] # version specifier (pinned / range / unspcified)
C = ["C1a", "C1b", "C1c"] # CI pipeline operation type: initial install / package update / rebuild with lockfile
ecosystem = ["nodejs", "python", "java"]
ecosystem_short = {"nodejs":"npm", "python":"pip", "java":"mvn"}  # a dict

internal_version = {"1.0.0", "1.0.2"}    # a set
malicious_version = {"1.0.3"}
internal_packages = {
    "nodejs": ["xueting-thesis-event-jianding", "xueting-thesis-service-fasong"],
    "python": ["xueting-thesis-event-fengfu", "xueting-thesis-service-zhuanfa"],
    "java": ["xueting-thesis-event-juhe", "xueting-thesis-result-fanhui"],
}   # a dict


# phase 1: determine invalid combination & generate experiment matrix
# assume all combinations are valid, only for specific condition it will become invalid
def is_valid_combination(ecosystem, A, B1, B2, C) -> tuple[bool, str]:
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
    combinations = itertools.product(ecosystem, A, B1, B2, C)
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
    with open(path, 'w', newline='') as csvfile:
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
        with open(checkpoint_path) as f:
            checkpoint_list = json.load(f)   #json.load(f) return a python list

        return set(checkpoint_list)     # convert loaded list to a set, set can prevent duplication

def mark_cell_as_finish(checkpoint_path, cell_id):
    finished_cells = load_finished_cells(checkpoint_path)
    finished_cells.add(cell_id)               # set should add new element in place!
    with open(checkpoint_path, "w") as f:
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
    file_already_exist = Path(result_file_path).is_file()
    with open(result_file_path, 'a', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=columns)
        if file_already_exist == False:     # only write header if file doesn't exist yet, otherwise more than one row header
            writer.writeheader()
        writer.writerow(row_to_append)


# phase 4: the classification logic

def read_npm_evidence(package_lock_path) -> list[dict]:
    try:
        with open(package_lock_path, 'r') as json_File:
            package_lock_data = json.load(json_File)
        
    except:
        return None
def read_pip_evidence(install_report_path) -> list[dict]:
    try:
        with open(install_report_path, 'r') as json_File:
            pinstall_report_data = json.load(json_File)
        
    except:
        return None
def read_java_evidence(java_cell) -> list[dict]:
    try:
        if java_cell["C - pipeline operation type"] == "C1a" or java_cell["C - pipeline operation type"] == "C1b":
            mvn_lockfile_data = json.load(f'{java_cell.cell_id}_lockfile.json')
        else:
            mvn_lockfile_data = json.loads(f'{java_cell.cell_id}_rebuild_lockfile.json')

        return list[dict]
    except:
        return None
    
def classify_logic(ecosystem, evidence_files) -> str:
    classification_result = ""
    if evidence_files == None:
        classificaton_result = "resolution_error"
    if package.version in malicious_version:
        classificaton_result = "malicious_resolved"
    if package.version in internal_version:
        classificaton_result = "private_resolved"
    else:
        classificaton_result = "resolution_error"
    return classification_result








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
