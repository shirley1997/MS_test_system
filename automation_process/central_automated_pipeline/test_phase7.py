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

from central_automated_pipeline import get_registration_token, start_runner_container, wait_for_runner_online

owner = "shirley1997"
repo = "MS_test_system"
repo_url = "https://github.com/shirley1997/MS_test_system"
image_tag = "thesis-runner:2.335.1"
cell_id = "test001"


token = get_registration_token(owner, repo)
print("registration token:", token)   

container_id = start_runner_container(cell_id, token, repo_url, image_tag)
print("container just created:", container_id)

online = wait_for_runner_online(owner, repo, f"thesis-runner-{cell_id}", timeout_s=60, check_interval_s=5)
print("is the new created runner online now?:", online)   # should be True within a few seconds
