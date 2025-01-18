"""
Module for jenkinsapi Result
"""


class Result(object):
    """
    Result class
    """

    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

    def __str__(self):
        return f"{self.className} {self.name} {self.status}"

    def __repr__(self) -> str:
        module_name = self.__class__.__module__
        class_name = self.__class__.__name__
        self_str = str(self)
        return "<%s.%s %s>" % (module_name, class_name, self_str)

    def identifier(self) -> str:
        """
        Calculate an ID for this object.
        """
        return f"{self.className}.{self.name}"
