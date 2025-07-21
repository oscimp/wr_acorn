## Synthetize White-Rabbit for the Litex Acorn Baseboard Mini

We assume we are in this ``patch/`` subdirectory of the ``wr_acorn`` repository in the following command sequence.

### 0. Compile the softcore firmware
```sh
git clone --recursive https://gitlab.com/ohwr/project/wrpc-sw
cd wrpc-sw
```

edit ``scripts/kconfig/lxdialog/check-lxdialog.sh`` according to ``https://gitlab.com/ohwr/project/wrpc-sw/-/issues?show=eyJpaWQiOiI3MyIsImZ1bGxfcGF0aCI6Im9od3IvcHJvamVjdC93cnBjLXN3IiwiaWQiOjE2NjQwMjQwOH0%3D`` (removing the exit 1 statement on line 56 of 
``scripts/kconfig/lxdialog/check-lxdialog.sh``)

```
make menuconfig
```

select ``Architecture = riscV`` and ``Target Platform = Generic WR Node with 16-bit PCS/PHY``

Then

```
export PATH=$HOME/WR/riscv-11.2-small/bin:$PATH  # adapt to you directory layout
make
```

The resuting ``wrc.bram`` will be needed later to synthesize the bitstream, assuming its location
will be ``wr-cores/bin/wrpc/wrc_phy16_direct_dmtd.bram`` (see below).

### 1. Get the sources
```sh
git clone --recursive https://gitlab.com/ohwr/project/wr-cores.git
cd wr-cores
git checkout mle/upstream/zc706
git checkout 1de3f69cdffaad0003f8e6dfd2fb4d8919574964
```

### 2. Apply the patch
```sh
git apply ../wr_acorn.patch
```
or 
```sh
patch -p1 < ../wr_acorn.patch
```
or 

### 3. Synthesize
Make sure ``hdlmake`` is installed (``pip install --user hdlmake`` or execute ``python3 ./setup.py install --user`` 
from a clone of https://gitlab.com/ohwr/project/hdl-make) and that Vivado is in the ``PATH`` 
(e.g. ``source /opt/Xilinx/Vivado/2022.2/settings64.sh`` -- tested with Vivado 2022.2 and 2024.2)

```sh
cd syn/acorn_ref_design
cp ../../../wrpc-sw/wrc.bram ../../../wr-cores/bin/wrpc/wrc_phy16_direct_dmtd.bram
hdlmake
make -i
```
Do not be concerned with ``hdlmake`` stating that
```
INFO    action.py:141: build_file_set() not parseable: .../wr_acorn/patch/wr-cores/top/acorn_ref_design/acorn_wr_ref_top.bmm
INFO    action.py:141: build_file_set() not parseable: .../wr_acorn/patch/wr-cores/top/acorn_ref_design/acorn_wr_ref_top.xdc
```
but notice that the patch did create a file ``syn/acorn_ref_design/bitstream.tcl`` including the statement
```
set_property SEVERITY WARNING [get_drc_checks REQP-49]
```
Since ``make clean`` will delete all TCL scripts, the newly generated ``bitstream.tcl`` will miss this option, leading to a failure
to synthesize the bitstream. Thus, avoid ``make clean``, or at least include the ``bitstream.tcl`` manually in the ``syn/acorn_ref_design``
to avoid ``Makefile`` from overwriting and deleting the mandatory option.

### 4. Flash the bitstream
```sh
openFPGALoader -c ft4232 -b litex-acorn-baseboard-mini -f ./acorn_wr_ref.runs/impl_1/acorn_wr_ref_top.bit
```

### 5. Connect to White-Rabbit UART
```sh
minicom -D /dev/ttyUSB2
```
