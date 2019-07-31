# -*- coding: utf-8 -*-
#
#Copyright (C) 2019, Ali Rıza KESKİN (sulincix)
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation; either version 3 of the License, or (at your option)
# any later version.
#

import gettext
__trans = gettext.translation('inary', fallback=True)
_ = __trans.gettext

import inary.context as ctx
import inary.db
import inary.util as util
import os
import sys
pkg_path=None

def pre_install(package_name, provided_scripts,
             scriptpath, metapath, filepath,
             fromVersion, fromRelease, toVersion, toRelease):
    """Do package's pre install operations"""
    installdb = inary.db.installdb.InstallDB()
    pkg_path = installdb.package_path(package_name)
    if(os.path.isfile(pkg_path+"/"+ctx.const.scom_dir+"/package.py")):
        sys.path.insert(0,pkg_path+"/"+ctx.const.scom_dir)
    elif(os.path.isfile(pkg_path+"/"+ctx.const.comar_dir+"/package.py")):
        sys.path.insert(0,pkg_path+"/"+ctx.const.comar_dir)
    else:
        ctx.ui.debug(_("SKIP: "+package_name))
        return 0
    import package as package_py
    if "preInstall" in dir(package_py):
        package_py.preInstall(fromVersion, fromRelease, toVersion, toRelease)
    del package_py
    sys.path.pop(0)

def post_install(package_name, provided_scripts,
             scriptpath, metapath, filepath,
             fromVersion, fromRelease, toVersion, toRelease):
    """Do package's post install operations"""
    installdb = inary.db.installdb.InstallDB()
    pkg_path = installdb.package_path(package_name)
    if(os.path.isfile(pkg_path+"/"+ctx.const.scom_dir+"/package.py")):
        sys.path.insert(0,pkg_path+"/"+ctx.const.scom_dir)
    elif(os.path.isfile(pkg_path+"/"+ctx.const.comar_dir+"/package.py")):
        sys.path.insert(0,pkg_path+"/"+ctx.const.comar_dir)
    else:
        ctx.ui.debug(_("SKIP: "+package_name))
        return 0
    import package as package_py
    if "postInstall" in dir(package_py):
        package_py.postInstall(fromVersion, fromRelease, toVersion, toRelease)
    del package_py
    sys.path.pop(0)

def post_remove(package_name, metapath, filepath, provided_scripts=None):
    """Do package's post removal operations"""
    installdb = inary.db.installdb.InstallDB()
    pkg_path = installdb.package_path(package_name)
    if(os.path.isfile(pkg_path+"/"+ctx.const.scom_dir+"/package.py")):
        sys.path.insert(0,pkg_path+"/"+ctx.const.scom_dir)
    elif(os.path.isfile(pkg_path+"/"+ctx.const.comar_dir+"/package.py")):
        sys.path.insert(0,pkg_path+"/"+ctx.const.comar_dir)
    else:
        ctx.ui.debug(_("SKIP: "+package_name))
        return 0
    import package as package_py
    if "postRemove" in dir(package_py):
        package_py.postRemove(timeout=ctx.dbus_timeout)
    del package_py
    sys.path.pop(0)

def pre_remove(package_name, metapath, filepath):
    """Do package's post removal operations"""
    installdb = inary.db.installdb.InstallDB()
    pkg_path = installdb.package_path(package_name)
    if(os.path.isfile(pkg_path+"/"+ctx.const.scom_dir+"/package.py")):
        sys.path.insert(0,pkg_path+"/"+ctx.const.scom_dir)
    elif(os.path.isfile(pkg_path+"/"+ctx.const.comar_dir+"/package.py")):
        sys.path.insert(0,pkg_path+"/"+ctx.const.comar_dir)
    else:
        ctx.ui.debug(_("SKIP: "+package_name))
        return 0
    import package as package_py
    if "preRemove" in dir(package_py):
        package_py.preRemove(timeout=ctx.dbus_timeout)
    del package_py
    sys.path.pop(0)
