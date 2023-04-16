import argparse
import os
import requests
import json
import time
import sys
from pathlib import Path

outputs_path = Path(os.environ['GITHUB_OUTPUT'])
summary_path = Path(os.environ['GITHUB_STEP_SUMMARY'])


def str_to_int(value):
    try:
        return int(value)
    except ValueError:
        raise argparse.ArgumentTypeError(f"{value} is not a valid integer")


def write_to_summary(message, is_error=False):
    with summary_path.open(mode='a') as summary_file:
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
    with open(outputs_path, 'a') as outputs_file:
        print(f'{name}={value}', file=outputs_file, end="\n")


def get_status():
    response = requests.get(api_endpoint)
    state = json.loads(response.text)[0]["state"]
    return state


def get_context():
    response = requests.get(api_endpoint)
    context = json.loads(response.text)[0]["context"]
    return context


def main(args):
    response = requests.get(api_endpoint)
    statuses_length = len(json.loads(response.text))
    if statuses_length == 0:
        write_to_summary(f"{args.context} failed to start! Stopping.", is_error=True)
        set_gha_output('result', 'failure')
        sys.exit(1)
    status = get_status()
    context = get_context()
    if context != args.context:
        write_to_summary(f"{args.context} failed to start! Stopping.", is_error=True)
        set_gha_output('result', 'failure')
        sys.exit(1)
    counter = 0
    write_to_summary(f"Waiting for {args.context} to complete...")
    while status != "success" and status != "failure":
        if counter > args.count:
            write_to_summary(f"{args.context} Timeout! Stopping.", is_error=True)
            set_gha_output('result', 'failure')
            sys.exit(1)
        time.sleep(args.wait)
        status = get_status()
        write_to_summary(f"{args.context}: {status}")
        counter += 1

    if status != "success":
        write_to_summary(f"{args.context}: {status}")
        write_to_summary("::error PRT failed", is_error=True)
        set_gha_output('result', 'failure')
        sys.exit(1)
    else:
        write_to_summary(f"{args.context} Passed Successfully!")
        set_gha_output('result', 'success')


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="GitHub Actions that waits for the GitHub Status API result")
    parser_github = parser.add_argument_group("Status API")
    parser_github.add_argument("--context", required=True, type=str, help="Context of Status API")
    parser_github.add_argument("--wait-interval", type=str_to_int, default=300, dest="wait",
                               help="Time to wait between polling (in seconds)")
    parser_github.add_argument("--count", type=str_to_int, default=12, help="Number of times to poll before timing out")
    parser_github.add_argument("--ref", type=str, help="Github commit head ref.")
    arguments = parser.parse_args()
    api_endpoint = f"https://api.github.com/repos/{os.environ['GITHUB_REPOSITORY']}/statuses/{arguments.ref}"
    main(arguments)
