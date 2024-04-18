import os
import requests
import time

HOST = "http://127.0.0.1:5000"
GT_STRUCTURE_ID = os.environ["GT_STRUCTURE_ID"]


def run_structure(input: str) -> str:
    # Start a run with the args.
    # These args will be passed into our Structure program as standard input.
    response = requests.post(
        f"{HOST}/api/structures/{GT_STRUCTURE_ID}/runs",
        json={
            "env": {},
            "args": [input],
        },
    )
    response.raise_for_status()

    # Runs are asynchronous, so we need to poll the status until it's no longer running.
    run_id = response.json()["run_id"]
    status = response.json()["status"]
    while status == "RUNNING":
        response = requests.get(f"{HOST}/api/runs/{run_id}")
        response.raise_for_status()
        status = response.json()["status"]

        time.sleep(1)  # Poll every second.

    content = response.json()
    if content["status"] == "COMPLETED":
        print(f"STDOUT: {content['stdout']}")
        return content["output"]["value"]
    else:
        print(f"***FAILED***\n")
        print(f"STDOUT: {content['stdout']}")
        raise Exception(content["stderr"])


structure_args = '{"frl": "https://www.openjpeg.org/assets/images/opj_logo_full.png", "style": "Pixel Art", "prompt": "Generate a variation of the image that depicts two men harried by unnatural forces while climbing a mountain"}'
output = run_structure(structure_args)
print(f"\n\nOUTPUT: {output}")
