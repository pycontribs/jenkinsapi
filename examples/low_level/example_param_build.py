import json
import requests


def foo():
    """
    A low level example of how JenkinsAPI runs a parameterized build
    """
    toJson = {"parameter": [{"name": "B", "value": "xyz"}]}
    url = "http://localhost:8080/job/ddd/build"
    # url = 'http://localhost:8000'
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    form = {"json": json.dumps(toJson)}
    response = requests.post(url, data=form, headers=headers)
    print(response.text.encode("UTF-8"))


if __name__ == "__main__":
    foo()
