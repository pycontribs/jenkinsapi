"""
Module for jenkinsapi Plugin
"""

from __future__ import annotations

from typing import Union


class Plugin(object):
    """
    Plugin class
    """

    def __init__(self, plugin_dict: Union[dict, str]) -> None:
        if isinstance(plugin_dict, dict):
            self.__dict__ = plugin_dict
        else:
            self.__dict__ = self.to_plugin(plugin_dict)
        self.shortName: str = self.__dict__["shortName"]
        self.version: str = self.__dict__.get("version", "Unknown")

    def to_plugin(self, plugin_string: str) -> dict:
        plugin_string = str(plugin_string)
        if "@" not in plugin_string or len(plugin_string.split("@")) != 2:
            usage_err: str = (
                "plugin specification must be a string like "
                '"plugin-name@version", not "{0}"'
            )
            usage_err = usage_err.format(plugin_string)
            raise ValueError(usage_err)

        shortName, version = plugin_string.split("@")
        return {"shortName": shortName, "version": version}

    def __eq__(self, other) -> bool:
        return self.__dict__ == other.__dict__

    def __str__(self) -> str:
        return self.shortName

    def __repr__(self) -> str:
        return "<%s.%s %s>" % (
            self.__class__.__module__,
            self.__class__.__name__,
            str(self),
        )

    def get_attributes(self) -> str:
        """
        Used by Plugins object to install plugins in Jenkins
        """
        return '<jenkins> <install plugin="%s@%s" /> </jenkins>' % (
            self.shortName,
            self.version,
        )

    def is_latest(self, update_center_dict: dict) -> bool:
        """
        Used by Plugins object to determine if plugin can be
        installed through the update center (when plugin version is
        latest version), or must be installed by uploading
        the plugin hpi file.
        """
        if self.version == "latest":
            return True
        center_plugin = update_center_dict["plugins"][self.shortName]
        return center_plugin["version"] == self.version

    def get_download_link(self, update_center_dict) -> str:
        latest_version = update_center_dict["plugins"][self.shortName][
            "version"
        ]
        latest_url = update_center_dict["plugins"][self.shortName]["url"]
        return latest_url.replace(
            "/".join((self.shortName, latest_version)),
            "/".join((self.shortName, self.version)),
        )
