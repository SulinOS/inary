# -*- coding: utf-8 -*-
#
#Copyright (C) 2019, Ali Rıza KESKİN (sulincix)
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation; either version 3 of the License, or (at your option)
# any later version.
#
import inary.context as ctx
import inary.db
import os
import sys

def post_install(package_name, provided_scripts,
             scriptpath, metapath, filepath,
             fromVersion, fromRelease, toVersion, toRelease):
    """Do package's post install operations"""
    pkg_path = installdb.package_path(package_name)
    if(os.path.isfile(pkg_path+"/"+ctx.const.scom_dir+"/package.py")):
        sys.path.insert(0,pkg_path+"/"+ctx.const.scom_dir)
        import package as package_py
        package_py.postInstall(fromVersion, fromRelease, toVersion, toRelease)
        sys.path.pop(0)

def post_install(package_name, provided_scripts,
             scriptpath, metapath, filepath,
             fromVersion, fromRelease, toVersion, toRelease):
    """Do package's post install operations"""
    installdb = inary.db.installdb.InstallDB()
    pkg_path = installdb.package_path(package_name)
    if(os.path.isfile(pkg_path+"/"+ctx.const.scom_dir+"/package.py")):
        sys.path.insert(0,pkg_path+"/"+ctx.const.scom_dir)
        import package as package_py
        if "postInstall" in dir(package_py):
            package_py.postInstall(fromVersion, fromRelease, toVersion, toRelease)
        sys.path.pop(0)

def post_remove(package_name, metapath, filepath, provided_scripts=None):
    """Do package's post removal operations"""
    if(os.path.isfile(pkg_path+"/"+ctx.const.scom_dir+"/package.py")):
        sys.path.insert(0,pkg_path+"/"+ctx.const.scom_dir)
        import package as package_py
        if "postInstall" in dir(package_py):
            package_py.postRemove(timeout=ctx.dbus_timeout)
        sys.path.pop(0)

def pre_remove(package_name, metapath, filepath):
    """Do package's post removal operations"""
    if(os.path.isfile(pkg_path+"/"+ctx.const.scom_dir+"/package.py")):
        sys.path.insert(0,pkg_path+"/"+ctx.const.scom_dir)
        import package as package_py
        if "postInstall" in dir(package_py):
            package_py.preRemove(timeout=ctx.dbus_timeout)
        sys.path.pop(0)
