# -*- coding: utf-8 -*-
"""
CLI

This allows you to create command line interface

"""

import mocha.cli


class CLI(mocha.cli.CLI):
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

        @command()
        def setup():
            """ The setup """
            click.echo("This is a setup!")
