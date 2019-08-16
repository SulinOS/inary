# -*- coding: utf-8 -*-
#
# Main fork Pisi: Copyright (C) 2005 - 2011, Tubitak/UEKAE (Licensed with GPLv2)
# More details about GPLv2, please read the COPYING.OLD file.
#
# Copyright (C) 2016 - 2019, Suleyman POYRAZ (Zaryob)
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU Affero General Public License as published by the Free
# Software Foundation; either version 3 of the License, or (at your option)
# any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# Please read the COPYING file.
#

import os
import time

import gettext

__trans = gettext.translation('inary', fallback=True)
_ = __trans.gettext

import inary.api
import inary.context as ctx
import inary.errors
import inary.util as util


class Error(inary.errors.Error):
    pass


try:
    import scom
    import dbus

except ImportError:
    raise Error(_("scom package is not fully installed."))


def is_char_valid(char):
    """Test if char is valid object path character."""
    return char in util.ascii_letters + util.digits + "_"


def is_method_missing(exception):
    """Tells if exception is about missing method in SCOM script"""
    if exception._dbus_error_name in ("tr.org.sulin.scom.python.missing",
                                      "tr.org.sulin.scom.Missing"):
        return True
    return False


def safe_script_name(package):
    """Generates DBus-safe object name for package script names."""
    object = package
    for char in package:
        if not is_char_valid(char):
            object = object.replace(char, '_')
    if object[0].isdigit():
        object = '_{}'.format(object)
    return object


def get_link():
    """Connect to the SCOM daemon and return the link."""

    sockname = "/var/run/dbus/system_bus_socket"
    if ctx.dbus_sockname:
        sockname = ctx.dbus_sockname

    alternate = False
    # If SCOM package is updated, all new configuration requests should be
    # made through new SCOM service. Passing alternate=True to Link() class
    # will ensure this.
    if ctx.scom_updated:
        alternate = True

    # This function is sometimes called when scom has recently started
    # or restarting after an update. So we give scom a chance to become
    # active in a reasonable time.
    timeout = 7
    exceptions = []
    while timeout > 0:
        try:
            link = scom.Link(socket=sockname, alternate=alternate)
            link.setLocale()
            return link
        except dbus.exceptions.DBusException as e:
            if str(e) in exceptions:
                pass
            else:
                exceptions.append(str(e))
        except Exception as e:
            if str(e) in exceptions:
                pass
            else:
                exceptions.append(str(e))
        time.sleep(0.2)
        timeout -= 0.2
    raise Error(_("Cannot connect to SCOM: \n  \"{}\"\n").format("\n  ".join(exceptions)))


def post_install(package_name, provided_scripts,
                 scriptpath, metapath, filepath,
                 fromVersion, fromRelease, toVersion, toRelease):
    """Do package's post install operations"""

    ctx.ui.info(_("Configuring \"{}\" package.").format(package_name))
    self_post = False

    package_name = safe_script_name(package_name)

    if package_name == 'scom':
        ctx.ui.debug(_("SCOM package updated. From now on,"
                       " using new SCOM daemon."))
        inary.api.set_scom_updated(True)

    link = get_link()

    for script in provided_scripts:
        ctx.ui.debug(_("Registering \"{0}\" named scom script for \"{1}\".").format(script.om, package_name))
        script_name = safe_script_name(script.name) \
            if script.name else package_name
        if script.om == "System.Package":
            self_post = True
        try:
            link.register(script_name, script.om,
                          os.path.join(scriptpath, script.script))
        except dbus.exceptions.DBusException as exception:
            raise Error(_("Script error: {}").format(exception))
        if script.om == "System.Service":
            try:
                link.System.Service[script_name].registerState()
            except dbus.exceptions.DBusException as exception:
                raise Error(_("Script error: {}").format(exception))

    ctx.ui.debug(_("Calling post install handlers for \"{}\" package.").format(package_name))
    for handler in link.System.PackageHandler:
        try:
            link.System.PackageHandler[handler].setupPackage(
                metapath,
                filepath,
                timeout=ctx.dbus_timeout)
        except dbus.exceptions.DBusException as exception:
            # Do nothing if setupPackage method is not defined
            # in package script
            if not is_method_missing(exception):
                raise Error(_("Script error for \"{0}\" package: {1}.").format(package_name, exception))

    if self_post:
        if not fromVersion:
            fromVersion = ""
        if not fromRelease:
            fromRelease = ""

        ctx.ui.debug(_("Running package's post install script for \"{0}\" package.").format(package_name))
        try:
            link.System.Package[package_name].postInstall(
                fromVersion, fromRelease, toVersion, toRelease,
                timeout=ctx.dbus_timeout)
        except dbus.exceptions.DBusException as exception:
            # Do nothing if postInstall method is not defined in package script
            if not is_method_missing(exception):
                raise Error(_("Script error for \"{0}\" package: {1}").format(package_name, exception))


def pre_remove(package_name, metapath, filepath):
    """Do package's pre removal operations"""

    ctx.ui.info(_("Running pre removal operations for \"{}\" package.").format(package_name))
    link = get_link()

    package_name = safe_script_name(package_name)

    if package_name in list(link.System.Package):
        ctx.ui.debug(_("Running package's pre remove script for \"{}\" package.").format(package_name))
        try:
            link.System.Package[package_name].preRemove(
                timeout=ctx.dbus_timeout)
        except dbus.exceptions.DBusException as exception:
            # Do nothing if preRemove method is not defined in package script
            if not is_method_missing(exception):
                raise Error(_("Script error: {}").format(exception))

    ctx.ui.debug(_("Calling pre remove handlers for \"{}\" package.").format(package_name))
    for handler in list(link.System.PackageHandler):
        try:
            link.System.PackageHandler[handler].cleanupPackage(
                metapath, filepath, timeout=ctx.dbus_timeout)
        except dbus.exceptions.DBusException as exception:
            # Do nothing if cleanupPackage method is not defined
            # in package script
            if not is_method_missing(exception):
                raise Error(_("Script error: {}").format(exception))


def post_remove(package_name, metapath, filepath, provided_scripts=None):
    """Do package's post removal operations"""

    if provided_scripts is None:
        provided_scripts = []
    ctx.ui.info(_("Running post removal operations for \"{}\" package.").format(package_name))
    link = get_link()

    package_name = safe_script_name(package_name)
    scripts = set([safe_script_name(s.name) for s \
                   in provided_scripts if s.name])
    scripts.add(package_name)

    if package_name in list(link.System.Package):
        ctx.ui.debug(_("Running package's postremove script for \"{}\" package.").format(package_name))
        try:
            link.System.Package[package_name].postRemove(
                timeout=ctx.dbus_timeout)
        except dbus.exceptions.DBusException as exception:
            # Do nothing if postRemove method is not defined in package script
            if not is_method_missing(exception):
                raise Error(_("Script error: {}").format(exception))

    ctx.ui.debug(_("Calling post remove handlers for \"{}\" package.").format(package_name))
    for handler in list(link.System.PackageHandler):
        try:
            link.System.PackageHandler[handler].postCleanupPackage(
                metapath, filepath, timeout=ctx.dbus_timeout)
        except dbus.exceptions.DBusException as exception:
            # Do nothing if postCleanupPackage method is not defined
            # in package script
            if not is_method_missing(exception):
                raise Error(_("Script error: {}").format(exception))

    ctx.ui.debug(_("Unregistering scom scripts of \"{}\" package.").format(package_name))
    for scr in scripts:
        try:
            ctx.ui.debug(_("Unregistering {} script.").format(scr))
            link.remove(scr, timeout=ctx.dbus_timeout)
        except dbus.exceptions.DBusException as exception:
            raise Error(_("Script error: {}").format(exception))
