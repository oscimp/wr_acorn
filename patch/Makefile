RISCV_TOOLCHAIN=riscv-11.2-small
RISCV_TOOLCHAIN_BASE_URL=https://gitlab.com/ohwr/project/wrpc-sw/-/wikis/uploads/9f9224d2249848ed3e854636de9c08dc/

all: acorn

riscv_get:
	wget -nc $(RISCV_TOOLCHAIN_BASE_URL)$(RISCV_TOOLCHAIN).tgz
	tar xvf $(RISCV_TOOLCHAIN).tgz

wrpc-sw_litex: riscv_get clean_wrpc-sw
	git clone --recursive https://gitlab.com/ohwr/project/wrpc-sw.git
	cd wrpc-sw && git checkout fc6a0f95ac2069d0ed73a6af4021876194f2dc54
	cd wrpc-sw && git apply ../wrpc-sw_litex.patch
	cp wrpc-sw_litex.config wrpc-sw/.config
	export PATH=$$PWD/$(RISCV_TOOLCHAIN)/bin:$$PATH && echo $$PATH && cd wrpc-sw && make

wr-cores_acorn: wrpc-sw_litex clean_wr-cores
	git clone --recursive https://gitlab.com/ohwr/project/wr-cores.git
	cd wr-cores && git checkout mle/upstream/zc706
	cd wr-cores && git checkout 1de3f69cdffaad0003f8e6dfd2fb4d8919574964
	cd wr-cores && git submodule update --init --force
	cd wr-cores && git apply ../wr_acorn.patch
	cp wrpc-sw/wrc.bram wr-cores/bin/wrpc/wrc_phy16_direct_dmtd.bram
	cd wr-cores/syn/acorn_ref_design/ && hdlmake
	cd wr-cores/syn/acorn_ref_design/ && make -i

acorn: wr-cores_acorn
	cp -f ./wr-cores/syn/acorn_ref_design/acorn_wr_ref.runs/impl_1/acorn_wr_ref_top.bit .

wr-cores_m2sdr: wrpc-sw_litex clean_wr-cores
	git clone --recursive https://gitlab.com/ohwr/project/wr-cores.git
	cd wr-cores && git checkout mle/upstream/zc706
	cd wr-cores && git checkout 1de3f69cdffaad0003f8e6dfd2fb4d8919574964
	cd wr-cores && git submodule update --init --force
	cd wr-cores && git apply ../wr_m2sdr.patch
	cp wrpc-sw/wrc.bram wr-cores/bin/wrpc/wrc_phy16_direct_dmtd.bram
	cd wr-cores/syn/m2sdr_ref_design/ && hdlmake
	cd wr-cores/syn/m2sdr_ref_design/ && make -i

m2sdr: wr-cores_m2sdr
	cp -f ./wr-cores/syn/m2sdr_ref_design/m2sdr_wr_ref.runs/impl_1/m2sdr_wr_ref_top.bit .

clean_riscv:
	rm -rf $(RISCV_TOOLCHAIN) $(RISCV_TOOLCHAIN).tgz

clean_wrpc-sw:
	rm -rf wrpc-sw/

clean_wr-cores:
	rm -rf wr-cores/

clean: clean_riscv clean_wrpc-sw clean_wr-cores
