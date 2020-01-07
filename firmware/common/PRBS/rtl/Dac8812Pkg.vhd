-------------------------------------------------------------------------------
-- File       : Dac8812Pkg.vhd
-- Company    : SLAC National Accelerator Laboratory
-------------------------------------------------------------------------------
-- Description: Types for DAC 8812 DAC
-------------------------------------------------------------------------------
-- This file is part of 'EPIX HR Development Firmware'.
-- It is subject to the license terms in the LICENSE.txt file found in the 
-- top-level directory of this distribution and at: 
--    https://confluence.slac.stanford.edu/display/ppareg/LICENSE.html. 
-- No part of 'EPIX HR Development Firmware', including this file, 
-- may be copied, modified, propagated, or distributed except according to 
-- the terms contained in the LICENSE.txt file.
-------------------------------------------------------------------------------

LIBRARY ieee;
USE ieee.std_logic_1164.ALL;

package Dac8812Pkg is

   --------------------------------------------
   -- Configuration Type
   --------------------------------------------

    -- Record
    type Dac8812ConfigType is record
        dacData         : std_logic_vector(15 downto 0);
        dacCh           : std_logic_vector( 1 downto 0); -- 00: none, 01: DAC A, 10:DAC B, 11: DAC A and DAC B
   end record;

   -- Initialize
   constant DAC8812_CONFIG_INIT_C : Dac8812ConfigType := ( 
      dacData => (others => '0'), 
      dacCh   => (others => '1') 
   );

   -- Record
    type DacWaveformConfigType is record
        enabled         : std_logic;
        run             : std_logic;
        externalUpdateEn: std_logic;
        samplingCounter : std_logic_vector(11 downto 0); -- number of clock cycles it waits to update the dac value (needs to be bigger than the refresh rate of the DAC itself).      
   end record;

   -- Initialize
   constant DACWAVEFORM_CONFIG_INIT_C : DacWaveformConfigType := ( 
      enabled          => '0', 
      run              => '0', 
      externalUpdateEn => '0', 
      samplingCounter  => x"220" 
   ); 
   
end Dac8812Pkg;

