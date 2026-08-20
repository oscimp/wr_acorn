-------------------------------------------------------------------------------
-- Title      : Digital DMTD Edge Tagger
-- Project    : White Rabbit
-------------------------------------------------------------------------------
-- File       : dmtd_with_deglitcher.vhd
-- Author     : Tomasz Wlostowski
-- Company    : CERN BE-Co-HT
-- Created    : 2010-02-25
-- Platform   : FPGA-generic
-- Standard   : VHDL '93
-------------------------------------------------------------------------------
-- Description: Single-channel DDMTD phase tagger with integrated bit-median
-- deglitcher. Contains a DDMTD detector, which output signal is deglitched and
-- tagged with a counter running in DMTD offset clock domain. Phase tags are
-- generated for each rising edge in DDMTD output with an internal counter
-------------------------------------------------------------------------------
--
-- Copyright (c) 2009 - 2011 CERN
--
-- This source file is free software; you can redistribute it
-- and/or modify it under the terms of the GNU Lesser General
-- Public License as published by the Free Software Foundation;
-- either version 2.1 of the License, or (at your option) any
-- later version.
--
-- This source is distributed in the hope that it will be
-- useful, but WITHOUT ANY WARRANTY; without even the implied
-- warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR
-- PURPOSE.  See the GNU Lesser General Public License for more
-- details.
--
-- You should have received a copy of the GNU Lesser General
-- Public License along with this source; if not, download it
-- from http://www.gnu.org/licenses/lgpl-2.1.html
--
-------------------------------------------------------------------------------
-- Revisions  :
-- Date        Version  Author          Description
-- 2009-01-24  1.0      twlostow        Created
-- 2011-18-04  1.1      twlostow        Bit-median type deglitcher, comments
-------------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;
use ieee.NUMERIC_STD.all;

library work;
use work.gencores_pkg.all;

entity dmtd_with_deglitcher is
  generic (
    -- Size of the phase tag counter. Must be big enough to cover at least one
    -- full period of the DDMTD detector output. Given the frequencies of clk_in_i
    -- and clk_dmtd_i are respectively f_in an f_dmtd, it can be calculated with
    -- the following formula:
    -- g_counter_bits = log2(f_in / abs(f_in - f_dmtd)) + 1
    g_counter_bits : natural := 17;

    -- Divides the inputs by 2 (effectively passing the clock through a flip flop)
    -- before it gets to the DMTD, effectively removing Place&Route warnings
    -- (at the cost of detector bandwidth)
    g_divide_input_by_2 : boolean := false;

    -- enables oversampling mode. In this case, the oversampling divider must
    -- be provided through r_oversample_div_i port.
    g_with_oversampling : boolean := false;

    -- enables jitter measurement statistic registers (r_low_o, r_high_o,
    -- r_samples_o, r_minmax_sel_i, r_reset_i ). They take some resources, so use with care.
    g_with_jitter_stats_regs : boolean := false;

    -- reversed mode: samples clk_dmtd_i with clk_in_i.
    g_reverse : boolean := false;

    -- uses an external DDMTD sampler and just deglitches and generates tags
    -- for an externally generated DDMTD output (clk_sampled_a_i).
    g_use_sampled_clock : boolean := false
    );
  port (
    -- resets for different clock domains
    rst_n_dmtdclk_i : in std_logic;
    rst_n_sysclk_i  : in std_logic;

    -- input clock
    clk_in_i : in std_logic;

    -- DMTD sampling clock
    clk_dmtd_i : in std_logic;
    clk_dmtd_over_i : in std_logic := '0';

    -- system clock
    clk_sys_i : in std_logic;

    -- externally sampled clock.
    clk_sampled_a_i : in std_logic := '0';

    -- async counter resync input: resets only the DDMTD state machine and free
    -- running counter, synchronized to clk_dmtd_i
    resync_p_a_i : in std_logic := '0';

    -- [clk_dmtd_i] counter resync output, pulses when free_cntr == 0
    resync_p_o : out std_logic;

    -- [clk_dmtd_over_i] counter resync input (oversampled mode)
    resync_p_over_i : in std_logic := '0';
    -- CONTROL REGISTERS (wired from SoftPLL)

    -- [clk_dmtd_i] deglitcher threshold
    r_deglitch_threshold_i : in std_logic_vector(15 downto 0);

    -- fractional mode input clock divider
    r_oversample_in_div_i : in std_logic_vector(5 downto 0) := (others => '0');
    -- fractional mode PPS alignment clock divider
    r_oversample_pps_div_i : in std_logic_vector(5 downto 0) := (others => '0');

    -- min/max stable 0 duration (selectable with r_minmax_sel_i)
    r_low_o : out std_logic_vector(15 downto 0);
    -- min/max stable 1 duration (selectable with r_minmax_sel_i)
    r_high_o : out std_logic_vector(15 downto 0);
    -- min/max sample count
    r_samples_i : in std_logic_vector(15 downto 0) := (others => '0');
    -- 1: calculate max low/high period, 0: calculate min low/high period.
    r_minmax_sel_i : in std_logic := '0';
    -- 1: resets r_low_o/r_high_o/r_samples_o
    r_stat_reset_i : in std_logic := '0';

    r_stat_ready_o : out std_logic;

    -- [clk_dmtd_i] raw DDMTD output (for debugging purposes)
    dbg_dmtdout_o : out std_logic;

    -- [clk_in_i] 1 PPS input for fractional clock-to-PPS alignment.
    pps_p1_i : in std_logic := '0';

    -- [clk_sys_i] deglitched edge tag value
    tag_o : out std_logic_vector(g_counter_bits-1 downto 0);

    -- [clk_sys_i] pulse indicates new phase tag on tag_o
    tag_stb_p1_o : out std_logic;
    dbg_clk_d3_o : out std_logic
    );
end dmtd_with_deglitcher;

architecture rtl of dmtd_with_deglitcher is
  type t_state is (WAIT_STABLE_0, WAIT_EDGE, GOT_EDGE);

  signal state : t_state;

  signal stab_cntr : unsigned(15 downto 0);
  signal free_cntr : unsigned(g_counter_bits-1 downto 0);

  signal clk_sampled : std_logic;

  signal new_edge_p_dmtdclk    : std_logic;
  signal new_edge_p_sysclk    : std_logic;

  signal tag_int       : unsigned(g_counter_bits-1 downto 0);
  signal resync_p_dmtd : std_logic;

  signal stat_sample_cnt : unsigned(15 downto 0);
  signal stat_length_low, stat_length_high : unsigned(15 downto 0);
  signal stat_length_low_minmax, stat_length_high_minmax : unsigned(15 downto 0);
  signal stat_discard_cnt : unsigned(1 downto 0);
  signal stat_discard_p : std_logic;
  signal stat_ready_dmtd, r_minmax_reset_dmtd : std_logic;

  attribute mark_debug : string;
  attribute mark_debug of free_cntr : signal is "true";
  attribute mark_debug of state : signal is "true";
  attribute mark_debug of tag_o : signal is "true";
  attribute mark_debug of tag_stb_p1_o : signal is "true";

  signal tag_latched_dmtdclk : std_logic_vector(g_counter_bits-1 downto 0);
  signal tag_latched_sysclk : std_logic_vector(g_counter_bits-1 downto 0);
  signal new_edge_p_sysclk_d0 : std_logic;
  
begin  -- rtl

  U_Sync_Resync_Pulse : gc_sync
    generic map (
      g_sync_edge => "positive")
    port map (
      clk_i     => clk_dmtd_i,
      rst_n_a_i => rst_n_dmtdclk_i,
      d_i       => resync_p_a_i,
      q_o       => resync_p_dmtd);

  gen_builtin : if( g_use_sampled_clock = false )generate

   U_Sampler: entity work.dmtd_sampler
      generic map (
        g_divide_input_by_2 => g_divide_input_by_2,
        g_reverse           => g_reverse,
        g_with_oversampling => g_with_oversampling)
      port map (
        clk_in_i        => clk_in_i,
        en_i            => '1',
        sync_p1_i       => resync_p_over_i,
        clk_dmtd_over_i => clk_dmtd_over_i,
        clk_dmtd_i      => clk_dmtd_i,
        clk_sampled_o   => clk_sampled,
        r_oversample_div_i => r_oversample_in_div_i );

  end generate gen_builtin;

  gen_externally_sampled : if g_use_sampled_clock generate
    clk_sampled <= clk_sampled_a_i;
  end generate gen_externally_sampled;


  p_free_counter : process(clk_dmtd_i)
  begin
    if rising_edge(clk_dmtd_i) then
      if (rst_n_dmtdclk_i = '0' or resync_p_dmtd = '1') then  -- synchronous reset (active low)
        free_cntr <= (others => '0');
      else
        free_cntr <= free_cntr + 1;
      end if;
    end if;
  end process;


-- glitchproof DMTD output edge detection
  p_deglitch : process (clk_dmtd_i)
  begin  -- process deglitch

    if rising_edge(clk_dmtd_i) then     -- rising clock edge

      if rst_n_dmtdclk_i = '0' then  -- synchronous reset (active low)
        stab_cntr     <= (others => '0');
        state         <= WAIT_STABLE_0;
        stat_discard_p <= '0';
        new_edge_p_dmtdclk <= '0';
      else

        case state is
          when WAIT_STABLE_0 =>         -- out-of-sync
            stat_discard_p <= '0';
            new_edge_p_dmtdclk <= '0';

            if clk_sampled /= '0' then
              stab_cntr <= (others => '0');
            else
              stab_cntr <= stab_cntr + 1;
            end if;

            -- DMTD output stable counter hit the LOW level threshold?
            if stab_cntr = unsigned(r_deglitch_threshold_i) then
              state <= WAIT_EDGE;
            end if;

          when WAIT_EDGE =>
            new_edge_p_dmtdclk <= '0';
            if (clk_sampled /= '0') then   -- got a glitch?
              state     <= GOT_EDGE;
              tag_int   <= free_cntr;
              stab_cntr <= (others => '0');
            end if;

          when GOT_EDGE =>
            if (clk_sampled = '0') then
              tag_int <= tag_int + 1;
            end if;

            if stab_cntr = unsigned(r_deglitch_threshold_i) then
              state         <= WAIT_STABLE_0;
              new_edge_p_dmtdclk <= '1';
              tag_latched_dmtdclk <= std_logic_vector(tag_int);
              stab_cntr     <= (others => '0');
              stat_discard_p <= '1';
            elsif (clk_sampled = '0') then
              stab_cntr <= (others => '0');
            else
              stab_cntr <= stab_cntr + 1;
            end if;
        end case;
      end if;
    end if;
  end process p_deglitch;


  gen_with_jitter_stats : if g_with_jitter_stats_regs generate

    inst_sync_stat_ready : gc_sync
      generic map (
        g_sync_edge => "positive")
      port map (
        clk_i     => clk_sys_i,
        rst_n_a_i => rst_n_sysclk_i,
        d_i       => stat_ready_dmtd,
        q_o       => r_stat_ready_o);

    inst_sync_stat_reset : gc_sync
      generic map (
        g_sync_edge => "positive")
      port map (
        clk_i     => clk_dmtd_i,
        rst_n_a_i => rst_n_dmtdclk_i,
        d_i       => r_stat_reset_i,
        q_o       => r_minmax_reset_dmtd);

    p_stats : process(clk_dmtd_i)
    begin
      if rising_edge(clk_dmtd_i) then
        if r_minmax_reset_dmtd = '1' or rst_n_dmtdclk_i = '0' then
          if r_minmax_sel_i = '1' then
            -- max
            stat_length_high_minmax <= (others => '0');
            stat_length_low_minmax <= (others => '0');
          else
            -- min
            stat_length_high_minmax <= (others => '1');
            stat_length_low_minmax <= (others => '1');
          end if;

          stat_sample_cnt <= (others => '0');
          stat_length_low <= (others => '0');
          stat_length_high <= (others => '0');
          stat_discard_cnt <= (others => '0');
          stat_ready_dmtd <= '0';
        else
          if stat_sample_cnt = unsigned(r_samples_i) then
            r_low_o <= std_logic_vector( stat_length_low_minmax );
            r_high_o <= std_logic_vector( stat_length_high_minmax );
            stat_ready_dmtd <= '1';
          end if;

          if stat_discard_p = '1' and stat_discard_cnt /= 3 then
            stat_discard_cnt <= stat_discard_cnt + 1;
          end if;

          if stat_discard_cnt = 3 then
            if clk_sampled = '1' then
              stat_length_high <= stat_length_high + 1;
              stat_length_low <= (others => '0');
              if stat_length_low > unsigned(r_deglitch_threshold_i) then
                stat_sample_cnt <= stat_sample_cnt + 1;
                if r_minmax_sel_i = '0' and stat_length_low < stat_length_low_minmax then
                  stat_length_low_minmax <= stat_length_low;
                elsif r_minmax_sel_i = '1' and stat_length_low > stat_length_low_minmax then
                  stat_length_low_minmax <= stat_length_low;
                end if;
              end if;
            else
              stat_length_low <= stat_length_low + 1;
              stat_length_high <= (others => '0');

              if stat_length_high > unsigned(r_deglitch_threshold_i) then
                stat_sample_cnt <= stat_sample_cnt + 1;

                if r_minmax_sel_i = '0' and stat_length_high < stat_length_high_minmax then
                  stat_length_high_minmax <= stat_length_high;
                elsif r_minmax_sel_i = '1' and stat_length_high > stat_length_low_minmax then
                  stat_length_high_minmax <= stat_length_low;
                end if;
              end if;
            end if;
          end if;
        end if;
      end if;
    end process;
  end generate gen_with_jitter_stats;

  p_resync_pulse_output : process(clk_dmtd_i)
  begin
    if rising_edge(clk_dmtd_i) then
      if(unsigned(free_cntr(free_cntr'length-1 downto 3)) = 0) then
        resync_p_o <= '1';
      else
        resync_p_o <= '0';
      end if;
    end if;
  end process;


  U_sync_tag : entity work.gc_sync_register
      generic map (
        g_width => g_counter_bits)
      port map (
        clk_i     => clk_sys_i,
        rst_n_a_i => rst_n_sysclk_i,
        d_i       => tag_latched_dmtdclk,
        q_o       => tag_latched_sysclk);
  

  U_sync_tag_strobe : entity work.gc_pulse_synchronizer2
      port map (
        clk_in_i    => clk_dmtd_i,
        rst_in_n_i  => rst_n_dmtdclk_i,
        clk_out_i   => clk_sys_i,
        rst_out_n_i => rst_n_sysclk_i,
        d_p_i       => new_edge_p_dmtdclk,
        q_p_o       => new_edge_p_sysclk);

  p_tag_output : process(clk_sys_i)
  begin
    if rising_edge(clk_sys_i) then
      if rst_n_sysclk_i = '0' then
        tag_stb_p1_o <= '0';
      else
        new_edge_p_sysclk_d0 <= new_edge_p_sysclk;
        
        if new_edge_p_sysclk_d0 = '1' then
          tag_o <= tag_latched_sysclk;
          tag_stb_p1_o <= '1';
        else
          tag_stb_p1_o <= '0';
        end if;
      end if;
    end if;
  end process;
  
  
  
  U_Extend_Debug_Pulses : gc_extend_pulse
    generic map (
      g_width => 3000)
    port map (
      clk_i      => clk_sys_i,
      rst_n_i    => rst_n_sysclk_i,
      pulse_i    => new_edge_p_sysclk,
      extended_o => dbg_dmtdout_o);

  dbg_clk_d3_o <= clk_sampled;

end rtl;
