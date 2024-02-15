import argparse
import json
import os
import sys
import time
from pathlib import Path

import requests

outputs_path = Path(os.environ["GITHUB_OUTPUT"])
summary_path = Path(os.environ["GITHUB_STEP_SUMMARY"])


def make_api_call(endpoint):
    write_to_summary(f"api call to {endpoint}")
    return requests.get(api_endpoint)


def str_to_int(value):
    try:
        return int(value)
    except ValueError:
        raise argparse.ArgumentTypeError(f"{value} is not a valid integer")


def write_to_summary(message, is_error=False):
    with summary_path.open(mode="a") as summary_file:
        if is_error:
            sys.stderr.write(message + "\n")
        else:
            sys.stdout.write(message + "\n")
        summary_file.write(message + "\n")


def set_gha_output(name, value):
    """Set an action output using an environment file.

    Refs:
    * https://hynek.me/til/set-output-deprecation-github-actions/
    * https://docs.github.com/en/actions/using-workflows/workflow-commands-for-github-actions#setting-an-output-parameter
    """
    with open(outputs_path, "a") as outputs_file:
        print(f"{name}={value}", file=outputs_file)


def get_status():
    response = make_api_call(api_endpoint)
    state = json.loads(response.text)[0]["state"]
    return state


def get_context():
    response = make_api_call(api_endpoint)
    context = json.loads(response.text)[0]["context"]
    return context


def main(arguments):
    response = make_api_call(api_endpoint)
    statuses_length = len(json.loads(response.text))
    if statuses_length == 0 or response.status_code == 404:
        write_to_summary(
            f"{arguments.context} failed to start or not triggered! Stopping."
        )
        set_gha_output("result", "not_found")
    else:
        status = get_status()
        context = get_context()
        if context != arguments.context:
            write_to_summary(
                f"{arguments.context} failed to start! Stopping.", is_error=True
            )
            set_gha_output("result", "not_found")
            sys.exit(0)
        counter = 0
        write_to_summary(f"Waiting for {arguments.context} to complete...")
        while status != "success" and status != "failure":
            if counter > arguments.count:
                write_to_summary(
                    f"{arguments.context} Timeout! Stopping.", is_error=True
                )
                set_gha_output("result", "failure")
                sys.exit(1)
            time.sleep(arguments.wait)
            status = get_status()
            write_to_summary(f"{arguments.context}: {status}")
            counter += 1

        if status != "success":
            write_to_summary(f"{arguments.context}: {status}")
            write_to_summary("::error PRT failed", is_error=True)
            set_gha_output("result", "failure")
            sys.exit(1)
        else:
            write_to_summary(f"{arguments.context} Passed Successfully!")
            set_gha_output("result", "success")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="GitHub Actions that waits for the GitHub Status API result"
    )
    parser.add_argument(
        "--context", required=True, type=str, help="Context of Status API"
    )
    parser.add_argument(
        "--wait-interval",
        type=str_to_int,
        default=300,
        dest="wait",
        help="Time to wait between polling (in seconds)",
    )
    parser.add_argument(
        "--count",
        type=str_to_int,
        default=12,
        help="Number of times to poll before timing out",
    )
    parser.add_argument("--ref", type=str, help="Github commit head ref.")
    arguments = parser.parse_args()
    global api_endpoint
    api_endpoint = f"https://api.github.com/repos/{os.environ['GITHUB_REPOSITORY']}/statuses/{arguments.ref}"
    main(arguments)
