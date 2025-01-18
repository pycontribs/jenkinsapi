"""
Module for MutableJenkinsThing
"""


class MutableJenkinsThing(object):
    """
    A mixin for certain mutable objects which can be renamed and deleted.
    """

    def get_delete_url(self) -> str:
        return f"{self.baseurl}/doDelete"

    def get_rename_url(self) -> str:
        return f"{self.baseurl}/doRename"
