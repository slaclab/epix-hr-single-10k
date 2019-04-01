-------------------------------------------------------------------------------
-- Title      : 14b to 12b filestream decoder
-------------------------------------------------------------------------------
-- File       : decodefile.vhd
-- Author     : Faisal Abu-Nimeh
-- Created    : 20171106
-- Platform   : Generic
-- Standard   : VHDL'93/02
-------------------------------------------------------------------------------
-- Description:
-- Reads a bit stream from a text file then 14b12bdecodes it.
--
-------------------------------------------------------------------------------
-- License:
-- Copyright (c) 2017 SLAC
-- See LICENSE or
-- https://confluence.slac.stanford.edu/display/ppareg/LICENSE.html
-------------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;
use ieee.math_real.all;
-- file io
use std.textio.all;

entity decodefile is
    generic(g_file         : string := "in.txt"; -- waveform ascii file
            g_banks        : positive := 2; -- number of banks
            g_subbanks     : positive := 8; -- number of subbanks
            g_subbanks_chn : positive := 4; -- number of channels in subbank
            g_enc_width    : positive := 14; -- Encoded data width
            g_adc_width    : positive := 12); -- adc data width

end entity;

architecture arch of decodefile is
    constant c_enc_cnt_width : positive := integer(ceil(log2(real(g_enc_width))));

    -- IDLE pattern
    -- "00_1011_1111_1000"
    constant c_idle1 : std_logic_vector(g_enc_width - 1 downto 0) := "00" & x"BF8";

    constant c_clk_period : time := 15.625 ns; -- 64MHz
    constant c_clk_serprd : time := c_clk_period/g_enc_width; -- deserializer clk period

    -- constants to interface with SLAC's modules
    constant c_tpd       : time    := 1 ps; -- SLAC's timing
    constant c_rst_async : boolean := true; -- synchronize reset

    -- Type: array of vectors to store ADC data
    type t_ADC_DATA is array (0 to g_subbanks - 1) of std_logic_vector(g_adc_width - 1 downto 0);
    signal s_adc_data : t_ADC_DATA; -- single bank data

    -- signals
    signal s_ser_clk : std_logic;

    signal s_clk   : std_logic;
    signal s_rst   : std_logic;
    signal s_rst_n : std_logic;

    -- sync reset across two domains
    signal s_rst_sync   : std_logic;
    signal s_rst_sync_d : std_logic;

    -- cnt samples from file
    signal s_cnt_samples : unsigned(c_enc_cnt_width - 1 downto 0); -- samples counter
    signal s_cnt_test    : unsigned(2 downto 0); -- samples counter

    signal s_dec_data_i : std_logic_vector(g_enc_width - 1 downto 0); -- decoder input
    signal s_dec_data_o : std_logic_vector(g_adc_width - 1 downto 0); -- decoder ouput
    signal s_pdata      : std_logic_vector(g_enc_width - 1 downto 0); -- deserialized parallel data

    -- decoder signals
    signal s_dec_valid   : std_logic;
    signal s_dec_sof     : std_logic;
    signal s_dec_eof     : std_logic;
    signal s_dec_eofe    : std_logic;
    signal s_dec_coderr  : std_logic;
    signal s_dec_disperr : std_logic;

    signal s_deser_valid : std_logic;   -- visual beacon for simulation
    signal s_aligned     : std_logic;   -- deserializer completed

    -- file io signals
    signal s_file_value : std_logic;
    signal s_file_clk   : std_logic;
    signal s_file_read  : std_logic := '0'; -- flag

    signal s_test_started  : std_logic; -- flag

    -- SSP 12b14b Decoder
    -- uses SLAC's naming convention
    component SspDecoder12b14b is
        generic(
            TPD_G          : time;
            RST_POLARITY_G : std_logic;
            RST_ASYNC_G    : boolean
        );
        port(
            clk       : in  std_logic;
            rst       : in  std_logic;
            validIn   : in  std_logic;
            dataIn    : in  std_logic_vector(13 downto 0);
            validOut  : out std_logic;
            dataOut   : out std_logic_vector(11 downto 0);
            valid     : out std_logic;
            sof       : out std_logic;
            eof       : out std_logic;
            eofe      : out std_logic;
            codeError : out std_logic;
            dispError : out std_logic
        );
    end component;

    -- start here
begin
    U_SspDecoder12b14b_1 : SspDecoder12b14b
        generic map(
            TPD_G          => c_tpd,
            RST_POLARITY_G => '0',      -- active-low reset
            RST_ASYNC_G    => c_rst_async)
        port map(
            clk       => s_clk,
            rst       => s_rst_n,
            validIn   => '1',
            dataIn    => s_dec_data_i,
            dataOut   => s_dec_data_o,
            validOut  => s_dec_valid,
            sof       => s_dec_sof,
            eof       => s_dec_eof,
            eofe      => s_dec_eofe,
            codeError => s_dec_coderr,
            dispError => s_dec_disperr);

    -- generate clock for testbench
    p_clk_gen : process is
    begin
        s_clk <= '0';
        wait for c_clk_period / 2;
        s_clk <= '1';
        wait for c_clk_period / 2;
    end process p_clk_gen;

    -- generate clock for testbench
    p_serclk_gen : process is
    begin
        s_ser_clk <= '0';
        wait for c_clk_serprd / 2;
        s_ser_clk <= '1';
        wait for c_clk_serprd / 2;
    end process p_serclk_gen;

    -- generate reset for testbench
    p_rst_gen : process is
    begin
        s_rst   <= '1';
        s_rst_n <= '0';
        wait for 40 * c_clk_period;     -- hold rest for 40 clock periods
        wait until s_clk = '1';
        s_rst   <= '0';
        s_rst_n <= '1';
        wait;
    end process p_rst_gen;

    -- clk xdomain reset sync
    sync_reset : process(s_ser_clk)
    begin
        if rising_edge(s_ser_clk) then
            s_rst_sync   <= s_rst;
            s_rst_sync_d <= s_rst_sync; -- two stage DFF sync
        end if;
    end process;

    -- deserializer and aligner process
    deserialize : process(s_ser_clk)
    begin
        if rising_edge(s_ser_clk) then
            if s_rst_sync_d = '1' then
                s_pdata       <= (others => '0');
                s_cnt_samples <= (others => '0');
                s_deser_valid <= '0';
                s_dec_data_i  <= (others => '0');
                s_aligned     <= '0';
            else
                if s_file_read = '1' then
                    -- right shift i.e. LSB 1st
                    s_pdata       <= s_file_value & s_pdata(g_enc_width - 1 downto 1);
                    s_deser_valid <= '0';

                    if s_aligned = '1' then
                        -- incr counter
                        s_cnt_samples <= s_cnt_samples + 1;
                        if s_cnt_samples >= (g_enc_width - 1) then
                            s_cnt_samples <= (others => '0');
                            s_deser_valid <= '1'; -- deserialization completed
                            --s_dec_data_i <= s_file_value & s_pdata(g_enc_width - 1 downto 1);
                            s_dec_data_i  <= s_pdata; -- feed decoder good data
                        end if;
                    else
                        -- look for idle pattern
                        if s_pdata = c_idle1 or s_pdata = not c_idle1 then
                            s_aligned     <= '1';
                            s_cnt_samples <= (others => '0'); -- now we can count properly
                            s_dec_data_i  <= s_pdata; -- feed decoder good data
                        end if;
                    end if;
                end if;
            end if;
        end if;
    end process;

    -- read stimulus from txt file
    readfile : process
        file infile     : text open read_mode is g_file;
        variable inline : line;
        variable v, c   : bit;    -- value and clock
    begin
        wait until s_ser_clk = '1' and s_ser_clk'event and s_rst_sync_d = '0';
        -- read data bit from file
        if (not endfile(infile)) then
            readline(infile, inline);   -- read entire line
            read(inline, v);            -- data value
            read(inline, c);            -- read clock
            s_file_value <= to_stdulogic(v); -- will read values at both clock edges
            s_file_clk   <= to_stdulogic(c);
            s_file_read  <= '1';
        else
            wait for 40 * c_clk_period;
            report "Simulation finished. No Data?" severity failure;
        end if;
    end process;

    decode_test : process(s_clk)
    begin
        -- FIXME: on real implementation e.g. FPGA
        -- this should be rising edge or whatever edge the design uses
        -- using falling edge here is a quick and dirty way to sync data
        if falling_edge(s_clk) then
            if s_rst = '1' then
                s_cnt_test <= (others => '0');
                s_test_started <= '0';
            else
                if s_dec_valid = '1' then
                    s_test_started <= '1';
                    --s_adc_data(to_integer(s_cnt_test)) <= s_dec_data_o;
                    -- ADC data comes in MSB first
                    s_adc_data(to_integer(s_cnt_test)) <= s_dec_data_o(0) & s_dec_data_o(1)
                    & s_dec_data_o(2) & s_dec_data_o(3) & s_dec_data_o(4) & s_dec_data_o(5)
                    & s_dec_data_o(6) & s_dec_data_o(7) & s_dec_data_o(8) & s_dec_data_o(9)
                    & s_dec_data_o(10) & s_dec_data_o(11);
                    -- assert (unsigned(s_dec_data_o) = s_cnt_test) report "Bad decode" severity failure;
                    s_cnt_test <= s_cnt_test + 1; -- counter will wrap around
                    --if s_cnt_test = to_unsigned(8, s_cnt_test'length) then
                    --    s_cnt_test <= to_unsigned(1, s_cnt_test'length);
                    --end if;
                else
                    if s_test_started = '1' then
                        null;
                        -- report "Simulation finished successfully" severity failure;
                    end if;
                end if;
            end if;
        end if;
    end process;
end;
