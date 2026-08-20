#!/usr/bin/env python3

import argparse
import os
import importlib
import subprocess
import sys

from boards.cmoda7 import Cmoda7DemoDDMTD


# update SPI flash (cmod A7 only)
def flashBistream(build_dir="build"):
    tool = os.environ.get("OPENFPGALOADER", "openFPGALoader")
    bit_name = os.path.join(build_dir, "top.bit")
    subprocess.check_call([tool, "-b", "cmoda7_35t", '-f', '--freq', '30e6', '-m', bit_name])

def platform_get(platform_name):
    plt_name_l = platform_name.lower()
    if plt_name_l.startswith("cmoda7"):
        target = "amaranth_boards.cmod_a7:CmodA7_35Platform"
    else:
        return None

    tgt = target.split(':')
    if len(tgt) != 2:
        print("wrong platform name must be zedboard, cmoda7, pynqz2")
        return None
    (module, name) = tgt
    platform_module = importlib.import_module(module)

    # Once we have the relevant module, extract our class from it.
    platform_class = getattr(platform_module, name)
    return platform_class

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--platform",     default="cmoda7", help="Target Platform (cmoda7 only for now)", type=str)
    parser.add_argument("-v","--verbose", help="prints all the parameters used for this instance of the program", action="store_true")
    parser.add_argument("--no-build",     help="sources generate only", action="store_true")
    parser.add_argument("--no-load",      help="don't load bitstream", action="store_true")
    parser.add_argument("--flash",        help="write bitstream into SPI flash (cmoda7 only)", action="store_true")
    parser.add_argument("--build-dir",    default="build", help="build directory")
    parser.add_argument("--toolchain",    default="Vivado", help="toolchain to use (Vivado or Symbiflow) (cmoda7 only) (default: Vivado)")
    args = parser.parse_args()

    flash_bitstream = True if args.platform == "cmoda7" and args.flash else False

    platform = platform_get(args.platform)
    if platform is None:
        print("error: undifined/unknown platform")
        sys.exit(1)

    gateware = platform(toolchain=args.toolchain).build(
        Cmoda7DemoDDMTD(),
        do_program=not (args.no_load or flash_bitstream),
        do_build=not args.no_build,
        build_dir=args.build_dir)
    if flash_bitstream:
        flashBistream(args.build_dir)

    # if no build nothing produces -> force
    if args.no_build:
        gateware.execute_local(args.build_dir, run_script=False)
