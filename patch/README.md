## Synthetize White-Rabbit for the Litex Acorn Baseboard Mini

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

### 3. Synthetize
Make sure ``hdlmake`` is installed (``pip install hdlmake``) and that Vivado is in the ``PATH`` 
(e.g. ``source /opt/Xilinx/Vivado/2022.2/settings64.sh``)

```sh
cd syn/acorn_ref_design
hdlmake
make -i
```

### 4. Flash the bitstream
```sh
openFPGALoader -c ft4232 -b litex-acorn-baseboard-mini -f ./acorn_wr_ref.runs/impl_1/acorn_wr_ref_top.bit
```

### 5. Connect to White-Rabbit UART
```sh
minicom -D /dev/ttyUSB2
```
