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
import re
import shutil

import gettext

__trans = gettext.translation('inary', fallback=True)
_ = __trans.gettext

# Inary Modules
import inary.context as ctx

# ActionsAPI Modules
import inary.actionsapi
import inary.actionsapi.get          as get
import inary.actionsapi.autotools    as autotools
import inary.actionsapi.inarytools   as inarytools
import inary.actionsapi.shelltools   as shelltools


class ConfigureError(inary.actionsapi.Error):
    def __init__(self, value=''):
        inary.actionsapi.Error.__init__(self, value)
        self.value = value
        ctx.ui.error("[KernelTools]" + value)


# Internal helpers

def __getAllSupportedFlavours():
    if os.path.exists("/etc/kernel"):
        return os.listdir("/etc/kernel")


#################
# Other helpers #
#################

def __getFlavour():
    try:
        flavour = get.srcNAME().split("kernel-")[1]
    except IndexError:
        return ""
    else:
        return flavour


def __getModuleFlavour():
    for fl in [_f for _f in __getAllSupportedFlavours() if "-" in _f]:
        try:
            if fl.split("-")[1] == get.srcNAME().split("-")[1]:
                return fl
        except IndexError:
            # the package is not a module, may be a userspace application
            # needing the kernel sources/headers for only reference.
            pass

    return "kernel"


def __getKernelARCH():
    """i386 is relevant for our i686 architecture."""
    return get.ARCH()


def __getSuffix():
    """Read and return the value read from .suffix file."""
    suffix = get.srcVERSION()
    if __getFlavour():
        suffix += "-{}".format(__getFlavour())
    return suffix


def __getExtraVersion():
    extraversion = ""
    try:
        # if successful, this is something like:
        # .1 for 2.6.30.1
        # _rc8 for 2.6.30_rc8
        extraversion = re.split("5.[0-9].[0-9]{2}([._].*)", get.srcVERSION())[1]
    except IndexError:
        # e.g. if version == 2.6.30
        pass

    # Append pae, default, rt, etc. to the extraversion if available
    if __getFlavour():
        extraversion += "-{}".format(__getFlavour())

    return extraversion


#######################
# Configuration stuff #
#######################

def getKernelVersion(flavour=None):
    # Returns the KVER information to use with external module compilation
    # This is something like 2.6.30_rc7-119 which will be appended to /lib/modules.
    # if flavour==None, it will return the KVER in the /etc/kernel/kernel file else,
    # /etc/kernel/<flavour>.
    # If it fails, it will return the running kernel version.

    # Try to detect module flavour
    if not flavour:
        flavour = __getModuleFlavour()

    kverfile = os.path.join("/etc/kernel", flavour)

    if os.path.exists(kverfile):
        return open(kverfile).read().strip()
    else:
        # Fail
        raise ConfigureError(_("Can't find kernel version information file \"{}\".").format(kverfile))


def configure():
    # Copy the relevant configuration file

    # Set EXTRAVERSION
    inarytools.dosed("Makefile", "EXTRAVERSION =.*", "EXTRAVERSION = {}".format(__getExtraVersion()))

    # Configure the kernel interactively if
    # configuration contains new options
    autotools.make("ARCH={} oldconfig".format(__getKernelARCH()))

    # Check configuration with listnewconfig
    try:
        autotools.make("ARCH={} listnewconfig".format(__getKernelARCH()))
    except:
        pass


###################################
# Building and installation stuff #
###################################

def dumpVersion():
    # Writes the specific kernel version into /etc/kernel
    destination = os.path.join(get.installDIR(), "etc/kernel/")
    if not os.path.exists(destination):
        os.makedirs(destination)

    open(os.path.join(destination, get.srcNAME()), "w").write(__getSuffix())


def build(debugSymbols=False):
    extra_config = []
    if debugSymbols:
        # Enable debugging symbols (-g -gdwarf2)
        extra_config.append("CONFIG_DEBUG_INFO=y")

    autotools.make("ARCH={0} {1}".format(__getKernelARCH(), " ".join(extra_config)))


def install():
    suffix = __getSuffix()

    # Dump kernel version under /etc/kernel
    dumpVersion()

    # Install kernel image
    inarytools.insinto("/boot/", "arch/x86/boot/bzImage", "kernel-{}".format(suffix))

    # Install the modules
    # mod-fw= avoids firmwares from installing
    # Override DEPMOD= to not call depmod as it will be called
    # during module-init-tools' package handler
    autotools.rawInstall("INSTALL_MOD_PATH={}/".format(get.installDIR()),
                         "DEPMOD=/bin/true modules_install mod-fw=")

    # Remove symlinks first
    inarytools.remove("/lib/modules/{}-sulinos/source".format(suffix))
    inarytools.remove("/lib/modules/{}-sulinos/build".format(suffix))

    # Install Module.symvers and System.map here too
    shutil.copy("Module.symvers", "{0}/lib/modules/{1}-sulinos/".format(get.installDIR(), suffix))
    shutil.copy("System.map", "{0}/lib/modules/{1}-sulinos/".format(get.installDIR(), suffix))

    # Create extra/ and updates/ subdirectories
    for _dir in ("extra", "updates"):
        inarytools.dodir("/lib/modules/{0}-sulinos/{1}".format(suffix, _dir))


def installHeaders(extraHeaders=None):
    """ Install the files needed to build out-of-tree kernel modules. """

    extras = [
              "drivers/media/dvb-frontends",
              "drivers/media/tuners",
              "drivers/media/platform"]

    if extraHeaders:
        extras.extend(extraHeaders)

    pruned = ["include", "scripts", "Documentation"]
    wanted = ["Makefile*", "Kconfig*", "Kbuild*", "*.sh", "*.pl", "*.lds"]

    suffix = __getSuffix()
    headersDirectoryName = "usr/src/linux-headers-{}-sulinos".format(suffix)

    # Get the destination directory for header installation
    destination = os.path.join(get.installDIR(), headersDirectoryName)
    shelltools.makedirs(destination)

    # First create the skel
    find_cmd = "find . -path {0} -prune -o -type f \( -name {1} \) -print".format(
        " -prune -o -path ".join(["'./{}/*'".format(l for l in pruned)]),
        " -o -name ".join(["'{}'".format(k for k in wanted)])
    ) + " | cpio -pVd --preserve-modification-time {}".format(destination)

    shelltools.system(find_cmd)

    # Install additional headers
    for headers in extras:
        if not os.path.exists("{0}/{1}".format(destination, headers)):
            shelltools.system("mkdir -p {0}/{1}".format(destination, headers))
        shelltools.system("cp -a {0}/*.h {1}/{2}".format(headers, destination, headers))

    # Install remaining headers
    shelltools.system("cp -a {0} {1}".format(" ".join(pruned), destination))

    # Cleanup directories
    shelltools.system("rm -rf {}/scripts/*.o".format(destination))
    shelltools.system("rm -rf {}/scripts/*/*.o".format(destination))
    shelltools.system("rm -rf {}/Documentation/DocBook".format(destination))

    # Finally copy the include directories found in arch/
    shelltools.system("(find arch -name include -type d -print | \
                        xargs -n1 -i: find : -type f) | \
                        cpio -pd --preserve-modification-time {}".format(destination))

    # Copy Modules.symvers and System.map
    shutil.copy("Module.symvers", "{}/".format(destination))
    shutil.copy("System.map", "{}/".format(destination))

    # Copy .config file which will be needed by some external modules
    shutil.copy(".config", "{}/".format(destination))

    # Settle the correct build symlink to this headers
    inarytools.dosym("/{}".format(headersDirectoryName), "/lib/modules/{}-sulinos/build".format(suffix))
    inarytools.dosym("build", "/lib/modules/{}-sulinos/source".format(suffix))


def installLibcHeaders(excludes=None):
    headers_tmp = os.path.join(get.installDIR(), 'tmp-headers')
    headers_dir = os.path.join(get.installDIR(), 'usr/include')

    make_cmd = "O={0} INSTALL_HDR_PATH={0}/install".format(headers_tmp)

    # Cleanup temporary header directory
    shelltools.system("rm -rf {}".format(headers_tmp))

    # Create directories
    shelltools.makedirs(headers_tmp)
    shelltools.makedirs(headers_dir)

    ###################Workaround begins here ...
    # Workaround information -- http://patches.openembedded.org/patch/33433/
    cpy_src = "{}/linux-*/arch/x86/include/generated".format(get.workDIR())
    cpy_tgt = "{}/arch/x86/include".format(headers_tmp)
    shelltools.makedirs(cpy_tgt)

    copy_cmd = "cp -Rv {0} {1} ".format(cpy_src, cpy_tgt)

    shelltools.system(copy_cmd)
    #######################Workaround ends here ...

    # make defconfig and install the headers
    autotools.make("{} defconfig".format(make_cmd))
    autotools.rawInstall(make_cmd, "headers_install")

    oldwd = os.getcwd()

    shelltools.cd(os.path.join(headers_tmp, "install", "include"))
    shelltools.system("find . -name '.' -o -name '.*' -prune -o -print | \
                       cpio -pVd --preserve-modification-time {}".format(headers_dir))

    # Remove sound/ directory which is installed by alsa-headers
    shelltools.system("rm -rf {}/sound".format(headers_dir))

    # Remove possible excludes given by actions.py
    if excludes:
        shelltools.system(
            "rm -rf {}".format(" ".join(["{0}/{1}".format(headers_dir, exc.strip("/")) for exc in excludes])))

    shelltools.cd(oldwd)

    # Remove tmp directory
    shelltools.system("rm -rf {}".format(headers_tmp))
