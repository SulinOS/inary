# -*- coding:utf-8 -*-
#
# Copyright (C) 2016  -  2017,  Suleyman POYRAZ (Zaryob)
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation; either version 2 of the License, or (at your option)
# any later version.
#
# Please read the COPYING file.
#

import optparse

import gettext
__trans = gettext.translation('inary', fallback=True)
_ = __trans.gettext

import inary
import inary.cli.command as command
import inary.cli.build as build
import inary.context as ctx
import inary.reactor as Reactor

class EmergeUp(build.Build, metaclass=command.autocommand):
    __doc__ = _("""Build and install INARY source packages from repository

Usage: emergeup ...

You should give the name of a source package to be
downloaded from a repository containing sources.

You can also give the name of a component.
""")

    def __init__(self, args):
        super(EmergeUp, self).__init__(args)
        self.scom = True

    name = ("emergeup", "emup")

    def options(self):

        group = optparse.OptionGroup(self.parser, _("emergeup options"))
        super(EmergeUp, self).add_options(group)
        group.add_option("-c", "--component", action="store",
                               default=None, help=_("Emerge available packages under given component"))
        group.add_option("--ignore-file-conflicts", action="store_true",
                     default=False, help=_("Ignore file conflicts"))
        group.add_option("--ignore-package-conflicts", action="store_true",
                     default=False, help=_("Ignore package conflicts"))
        group.add_option("--ignore-scom", action="store_true",
                               default=False, help=_("Bypass scom configuration agent"))
        self.parser.add_option_group(group)

    def run(self):
        self.init(database = True)

        source = inary.db.sourcedb.SourceDB()

        imdb = inary.db.installdb.InstallDB()

        installed_emerge_packages = imdb.list_installed_with_build_host("localhost")

        emerge_up_list = []

        for package in installed_emerge_packages:
            if source.has_spec(package):
                spec = source.get_spec(package)
                if spec.getSourceRelease() > imdb.get_version(package)[1]:
                    emerge_up_list.append(package)

        if ctx.get_option('output_dir'):
            ctx.ui.info(_('Output directory: {}').format(ctx.config.options.output_dir))
        else:
            ctx.ui.info(_('Outputting binary packages in the package cache.'))
            ctx.config.options.output_dir = ctx.config.cached_packages_dir()

        repos = Reactor.list_repos()
        Reactor.update_repos(repos, ctx.get_option('force'))
	
        Reactor.emerge(emerge_up_list)