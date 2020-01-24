from abc import ABC, abstractclassmethod


class BaseEntryPoint(ABC):
    from asreview.__init__ import __version__
    description = "Base Entry point."
    extension_name = "asreview"
    version = __version__

    @abstractclassmethod
    def execute(self, argv):
        raise NotImplementedError

    def format(self, entry_name="?"):
        description = self.description
        version = getattr(self, "version", "?")
        extension_name = getattr(self, "extension_name", "?")

        display_name = f"{entry_name} [{extension_name}-{version}]"

        return f"{display_name}\n    {description}"
