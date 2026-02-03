"""
This module enables Manifest file parsing.
Copied from
https://chromium.googlesource.com/external/googleappengine/python/+/master
/google/appengine/tools/jarfile.py
"""

import zipfile

_MANIFEST_NAME = "META-INF/MANIFEST.MF"


class InvalidJarError(Exception):
    """
    InvalidJar exception class
    """

    pass


class Manifest:
    """
    The parsed manifest from a jar file.
    Attributes:
      main_section: a dict representing the main (first)
        section of the manifest.
        Each key is a string that is an attribute, such as
        'Manifest-Version', and the corresponding value is a string that
        is the value of the attribute, such as '1.0'.
      sections: a dict representing the other sections of the manifest.
        Each key is a string that is the value of the 'Name' attribute for
        the section, and the corresponding value is a dict like the
        main_section one, for the other attributes.
    """

    def __init__(self, main_section, sections):
        self.main_section = main_section
        self.sections = sections


def read_manifest(jar_file_name):
    """
    Read and parse the manifest out of the given jar.
    Args:
        jar_file_name: the name of the jar from which the manifest is to be read.

    Returns:
        A parsed Manifest object, or None if the jar has no manifest.

    Raises:
        IOError: if the jar does not exist or cannot be read.
    """
    with zipfile.ZipFile(jar_file_name) as jar:
        try:
            manifest_string = jar.read(_MANIFEST_NAME).decode("UTF-8")
        except KeyError:
            return None
        return _parse_manifest(manifest_string)


def _parse_manifest(manifest_string):
    """
    Parse a Manifest object out of the given string.
    Args:
      manifest_string: a str or unicode that is the manifest contents.
    Returns:
      A Manifest object parsed out of the string.
    Raises:
      InvalidJarError: if the manifest is not well-formed.
    """
    manifest_string = "\n".join(manifest_string.splitlines()).rstrip("\n")
    section_strings = manifest_string.split("\n\n")
    parsed_sections = [_parse_manifest_section(s) for s in section_strings]
    main_section = parsed_sections[0]
    sections = dict()
    try:
        for entry in parsed_sections[1:]:
            sections[entry["Name"]] = entry
    except KeyError:
        raise InvalidJarError(
            "Manifest entry has no Name attribute: %s" % entry
        )
    return Manifest(main_section, sections)


def _parse_manifest_section(section):
    """Parse a dict out of the given manifest section string.
    Args:
      section: a str or unicode that is the manifest section.
        It looks something like this (without the >):
        > Name: section-name
        > Some-Attribute: some value
        > Another-Attribute: another value
    Returns:
      A dict where the keys are the attributes (here, 'Name', 'Some-Attribute',
      'Another-Attribute'), and the values are the corresponding
      attribute values.
    Raises:
      InvalidJarError: if the manifest section is not well-formed.
    """
    section = section.replace("\n ", "")
    try:
        return dict(line.split(": ", 1) for line in section.split("\n"))
    except ValueError:
        raise InvalidJarError("Invalid manifest %r" % section)
