""" jenkinsapi.command_line.jenkinsapi_version
"""

import jenkinsapi
import sys


def main():
    sys.stdout.write(jenkinsapi.__version__)


if __name__ == "__main__":
    main()
