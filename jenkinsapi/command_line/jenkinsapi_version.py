""" jenkinsapi.command_line.jenkinsapi_version
"""

from jenkinsapi import __version__ as version
import sys


def main():
    sys.stdout.write(version)


if __name__ == "__main__":
    main()
