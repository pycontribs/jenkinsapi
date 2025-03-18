""" jenkinsapi.command_line.jenkinsapi_version
"""

from importlib.metadata import version
import sys


def main():
    sys.stdout.write(version("jenkinsapi"))


if __name__ == "__main__":
    main()
