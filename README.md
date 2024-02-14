# wait-for-status-checks
This GitHub Action waits for a specified GitHub Status Check to complete before continuing the workflow. It uses the GitHub Status API to check the status of the specified context on the head commit of the current branch. The action will poll the API until the status is either "success", "failure", "not found", or until the specified timeout is reached.

## Inputs

| Input         | Description                                  | Required| Default |
|---------------|----------------------------------------------|---------|---------|
| `ref`         | Github commit head ref                       | Yes     | ${{ github.head_ref }}    |
| `context`     | Context string to filter the statuses API    | Yes     |         |
| `wait-interval`| Time to wait between polling (in seconds)    | No      | 300     |
| `count`       | Number of times to poll before timing out    | No      | 12      |


## outputs

| Output | Description |
|--------|-------------|
| result | `failure`, `success` or `not found` result of the status |

## Example Usage

```yaml
name: Wait for Status Check
on: push

jobs:
  wait_for_status:
    runs-on: ubuntu-latest
    steps:
      - name: Wait for status check
        id: outcome
        uses: omkarkhatavkar/wait-for-status-checks@main
        with:
          ref: ${{ github.head_ref }}
          context: 'continuous-integration/travis-ci/push'
          wait-interval: 60
          count: 10
      - name: Check status
        run: |
          if [ ${{ steps.outcome.outputs.result }} == 'success' ]; then
            echo "Status check passed!"
          else
            echo "Status check failed!"
          fi
```
