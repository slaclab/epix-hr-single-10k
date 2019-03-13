------------------------------------------------------------------------------
-- Title         : SR0 resynchronizer
-- Project       : cryo adc 
-------------------------------------------------------------------------------
-- File          : SR0Synchronizer.vhd
-------------------------------------------------------------------------------
-- Description:
-- DAC Controller.
-------------------------------------------------------------------------------
-- This file is part of 'EPIX HR Development Firmware'.
-- It is subject to the license terms in the LICENSE.txt file found in the 
-- top-level directory of this distribution and at: 
--    https://confluence.slac.stanford.edu/display/ppareg/LICENSE.html. 
-- No part of 'EPIX HR Development Firmware', including this file, 
-- may be copied, modified, propagated, or distributed except according to 
-- the terms contained in the LICENSE.txt file.
-------------------------------------------------------------------------------
-- Modification history:
-- 08/09/2011: created as DacCntrl.vhd by Ryan
-- 05/19/2017: modifed to Dac8812Cntrl.vhd by Dionisio
-------------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;
use ieee.std_logic_unsigned.all;
use work.all;
use work.StdRtlPkg.all;


entity SR0Synchronizer is
   generic (
      TPD_G : time := 1 ns
   ); 
   port ( 

      -- Master system clock
      sysClk       : in  sl;
      sysClkRst    : in  sl;

      -- DAC Data
      delay        : in  slv(7 downto 0);
      period       : in  slv(7 downto 0);
      SR0          : in  sl;

      -- DAC Control Signals
      refClk       : out sl;
      SR0Out       : out sl     
   );
end SR0Synchronizer;


-- Define architecture
architecture arch of SR0Synchronizer is


   attribute keep : string;
   type AsicAcqType is record
      SR0               : sl;
      refClock          : sl;
      counter           : slv(7 downto 0);
      delay             : slv(7 downto 0);
      period            : slv(7 downto 0);     
   end record AsicAcqType;
   
   constant ASICACQ_TYPE_INIT_C : AsicAcqType := (
      SR0               => '0',
      refClock          => '0',
      counter           => (others=>'0'),
      delay             => (others=>'0'),
      period            => x"38"      -- 56 counts
   );

   
   -- Local Signals
   signal s       : AsicAcqType := ASICACQ_TYPE_INIT_C;
   signal sin     : AsicAcqType;
   signal SR0Sync : sl;

   --
   attribute keep of s : signal is "true";


begin

  -- synchronizers
   U_Sync_SR0 : entity work.Synchronizer     
   port map (
      clk     => sysClk,
      rst     => sysClkRst,
      dataIn  => SR0,
      dataOut => SR0Sync
   );   

   -------------------------------
   -- Configuration Register
   -------------------------------  
   comb : process (s, SR0Sync, delay, period) is
      variable v           : AsicAcqType;
      
   begin
      -- Latch the current value
      v := s;
      v.delay  := delay;
      v.period := period;

      if s.counter = s.period-1 then
        v.counter := (others=>'0');
      else
        v.counter := s.counter + 1;
      end if;

      -- SR0 logic
      if (SR0Sync = '0') then 
        v.SR0 := '0';
      elsif (s.counter = s.delay) and (SR0Sync = '1') then
        v.SR0 := '1';
      end if;
      
      --ref clock logic
      if (s.counter = x"00") then
        v.refClock := not s.refClock;
      end if;

      -- Synchronous Reset
      if sysClkRst = '1' then
         v := ASICACQ_TYPE_INIT_C;
      end if;

      -- Register the variable for next clock cycle
      sin <= v;

      --------------------------
      -- Outputs 
      --------------------------
      refClk         <= s.refClock;
      SR0Out         <= s.SR0;
      
   end process comb;

   seq : process (sysClk) is
   begin
      if rising_edge(sysClk) then
         s <= sin after TPD_G;
      end if;
   end process seq;
   
end arch;

