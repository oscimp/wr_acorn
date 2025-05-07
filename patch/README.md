## Synthetize White-Rabbit for the Litex Acorn Baseboard Mini

### 1. Get the sources
```sh
git clone https://gitlab.com/ohwr/project/wr-cores.git
cd wr-cores
git checkout 618e08ca5180e2754748998c373fa50c76c44bd0
```

### 2. Apply the patch
```sh
git apply wr_acorn.patch
```

### 3. Synthetize
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
