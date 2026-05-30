import argparse

from django_extensions.management.commands.runscript import Command as BaseRunScriptCommand


class Command(BaseRunScriptCommand):
    def add_arguments(self, parser):
        super().add_arguments(parser)
        for action in parser._actions:
            if action.dest == "script_args":
                action.nargs = argparse.REMAINDER
                break
