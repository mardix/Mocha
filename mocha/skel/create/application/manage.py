# -*- coding: utf-8 -*-
"""
Manage.py is a command line utility to perform admin task

"""

import mocha.cli


class Manage(mocha.cli.Manager):
    def __init__(self, command, click):
        """
        Initiate the command line
        Place all your command functions in this method
        And they can be called with

            > mocha $fn_name

        ie:

            @command
            def hello():
                click.echo("Hello World!")

        In your terminal:
            > mocha hello


        :param command: copy of the cli.command
        :param click: click
        """

        from mocha import models

        @command()
        def setup():
            """ The setup """
            click.echo("This is a setup!")
