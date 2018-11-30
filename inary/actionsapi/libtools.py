# -*- coding: utf-8 -*-
#
# Main fork Pisi: Copyright (C) 2005 - 2011, Tubitak/UEKAE
#
# Copyright (C) 2016 - 2018, Suleyman POYRAZ (Zaryob)
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation; either version 3 of the License, or (at your option)
# any later version.
#
# Please read the COPYING file.

# Standard Python Modules
import os

import gettext
__trans = gettext.translation('inary', fallback=True)
_ = __trans.gettext

# Inary-Core Modules
import inary.context as ctx
from inary.util import join_path

# ActionsAPI Modules
import inary.actionsapi
from inary.actionsapi.shelltools import *
import inary.actionsapi.get as get

class RunTimeError(inary.actionsapi.Error):
    def __init__(self, value=''):
        inary.actionsapi.Error.__init__(self, value)
        self.value = value
        ctx.ui.error(value)

def preplib(sourceDirectory = '/usr/lib'):
    sourceDirectory = join_path(get.installDIR(), sourceDirectory)
    if can_access_directory(sourceDirectory):
        if system('/sbin/ldconfig -n -N {}'.format(sourceDirectory)):
            raise RunTimeError(_('Running ldconfig failed.'))

def gnuconfig_update():
    """ copy newest config.* onto source\'s """
    for root, dirs, files in os.walk(os.getcwd()):
        for fileName in files:
            if fileName in ['config.sub', 'config.guess']:
                targetFile = os.path.join(root, fileName)
                if os.path.islink(targetFile):
                    unlink(targetFile)

                try:
                    copy('/usr/share/gnuconfig/{}'.format(fileName), join_path(root, fileName))
                except:
                    ctx.ui.info(_('Can not make GNU Config Update... Passing...'))
                else:
                    ctx.ui.info(_('GNU Config Update Finished.'))

def libtoolize(parameters = ''):
    if system('/usr/bin/libtoolize {}'.format(parameters)):
        raise RunTimeError(_('Running libtoolize failed.'))

def gen_usr_ldscript(dynamicLib):

    makedirs('{}/usr/lib'.format(get.installDIR()))

    destinationFile = open('{0}/usr/lib/{1}'.format(get.installDIR(), dynamicLib), 'w')
    content = '''
/* GNU ld script
    Since Pardus has critical dynamic libraries
    in /lib, and the static versions in /usr/lib,
    we need to have a "fake" dynamic lib in /usr/lib,
    otherwise we run into linking problems.
*/
GROUP ( /lib/{} )
'''.format(dynamicLib)

    destinationFile.write(content)
    destinationFile.close()
    chmod('{0}/usr/lib/{1}'.format(get.installDIR(), dynamicLib))
