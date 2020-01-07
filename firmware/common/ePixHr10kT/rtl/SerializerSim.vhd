-------------------------------------------------------------------------------
-- Title      : g_dwidth-to-1 double data rate serializer
-------------------------------------------------------------------------------
-- File       : serializer.vhd
-- Company    : SLAC National Accelerator Laboratory
-------------------------------------------------------------------------------
-- Description:
-- Serializer which outputs on rising and falling edges, i.e., DDR.
-- LSB first on rising edge
-------------------------------------------------------------------------------
-- This file is part of 'EPIX HR Firmware'.
-- It is subject to the license terms in the LICENSE.txt file found in the 
-- top-level directory of this distribution and at: 
--    https://confluence.slac.stanford.edu/display/ppareg/LICENSE.html. 
-- No part of 'EPIX HR Firmware', including this file, 
-- may be copied, modified, propagated, or distributed except according to 
-- the terms contained in the LICENSE.txt file.
-------------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;
use ieee.math_real.all;

-- DDR serializer
entity serializerSim is
    generic(
      TPD_G    : time := 1 ns;
      g_dwidth : positive := 14 -- must be an even number
    );
    port(
        clk_i     : in  std_logic;
        reset_n_i : in  std_logic;

        data_i  : in  std_logic_vector(g_dwidth - 1 downto 0);
        data_o  : out std_logic
    );
end entity;

architecture rtl of serializerSim is
    -- generic bus width
    constant c_cnt_width : positive := integer(ceil(log2(real(g_dwidth))));
    -- high and low counters
    signal s_cnt_h, s_cnt_l : unsigned(c_cnt_width - 1 downto 0);
    -- high and low data out
    signal s_data_o_h, s_data_o_l : std_logic;
    -- force low process to wait for high
    signal s_start : std_logic;
    signal s_data : std_logic_vector(g_dwidth - 1 downto 0);
begin
    -- when clk is high output data_h, otherwise output data_l
    -- first conversion contains junk
--    s_data_o_h <= s_data(to_integer(s_cnt_h));
--    s_data_o_l <= s_data(to_integer(s_cnt_l));
   
    s_data_o_h <= s_data(to_integer(g_dwidth - 1 - s_cnt_h));
    s_data_o_l <= s_data(to_integer(g_dwidth - 1 - s_cnt_l));

    data_o <= s_data_o_h after TPD_G when clk_i = '1' else s_data_o_l after TPD_G;

    -- even bits on rising edge
    process(clk_i)
    begin
        if rising_edge(clk_i) then
            if reset_n_i = '0' then
                s_cnt_h <= (others => '0'); -- start from 0
                s_data  <= (others => '0');
                s_start <= '0';
            else
                -- force falling edge process
                if s_start = '0' then
                    s_start <= '1';
                end if;

                s_cnt_h    <= s_cnt_h + 2;
                if s_cnt_h >= g_dwidth - 2 then
                    s_cnt_h <= (others => '0');
                    -- register incoming data
                    s_data  <= data_i;
                end if;
            end if;
        end if;
    end process;

    -- odd bits on falling edge
    process(clk_i)
    begin
        if falling_edge(clk_i) then
            if reset_n_i = '0' then
                s_cnt_l <= to_unsigned(1, s_cnt_l'length); -- start from 1
            else
                if s_start = '1' then
                    s_cnt_l    <= s_cnt_l + 2;
                    if s_cnt_l >= g_dwidth - 1 then
                        s_cnt_l <= to_unsigned(1, s_cnt_l'length);
                    end if;
                end if;
            end if;
        end if;
    end process;
end rtl;
