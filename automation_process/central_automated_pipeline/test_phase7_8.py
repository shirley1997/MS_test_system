# this is a test script for testing phase 7 from automation_process\central_automated_pipeline\central_automated_pipeline.py
# all nessasary input is hard coded here for the test

# result: 
# 1. the registration token of runner can be retrived
# 2. runner container can be successfully created and startd 
# 3. the runner is successfully registred on github
# 4. output of command 'gh api repos/shirley1997/MS_test_system/actions/runners' shows the new created runner info with "status == online"
# 5. runner log is observed through docker desktop, runner container starts successfully
#    the runner can receive manually dispatched workflow and execute the job command 'gh api repos/shirley1997/MS_test_system/actions/runners' again
# 6. after finish the job, the container is removed by itself
#    the runner is also de-registered when checking output of 

from central_automated_pipeline import get_registration_token, start_runner_container, wait_for_runner_online, dispatch_cell, find_run_id, wait_for_run_complete, download_artifact, service_pipeline_file, artifact_name_suffix

owner = "shirley1997"
repo = "MS_test_system"
repo_url = "https://github.com/shirley1997/MS_test_system"
image_tag = "thesis-runner:2.335.1"
cell_id = "mvn_A1a_B1a_B2a_C1c"

cell = {
    "cell_id": cell_id,
    "ecosystem": "java",
    "A - private registry configuration": "A1a",
    "B1 - package manager configuration": "B1a",
    "B2 - version specifier": "B2a",
    "C - pipeline operation type": "C1c",
    "valid?": True,
    "invalid_reason": "",
}

#test for phase 7
token = get_registration_token(owner, repo)
print("registration token obtained:", token)   

container_id = start_runner_container(cell_id, token, repo_url, image_tag)
print("runner container just created:", container_id)

online = wait_for_runner_online(owner, repo, f"thesis-runner-{cell_id}", timeout_s=60, check_interval_s=5)
print("is the new created runner online now?:", online)   # should be True within a few seconds


#test for phase 8
# run a cell, dispatch a workflow, obtain the run id of that workflow
# observe the specific workflow log, then download artifacts at the end

dispatch_cell(owner, repo, cell["ecosystem"], cell)
run_id = find_run_id(owner, repo, service_pipeline_file[cell["ecosystem"]], cell_id)
print("run_id of the workflow:", run_id)

wait_for_run_complete(owner, repo, run_id)

dest_dir = f"automation_process/central_automated_pipeline/artifact_download/{cell_id}"
artifact_name = f"{cell_id}_{artifact_name_suffix[cell["ecosystem"]]}"
result = download_artifact(owner, repo, run_id, artifact_name, dest_dir)
print("download artifact produced by service pipeline:", result)

