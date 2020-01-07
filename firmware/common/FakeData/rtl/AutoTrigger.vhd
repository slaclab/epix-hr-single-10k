-------------------------------------------------------------------------------
-- File       : AutoTrigger.vhd
-- Company    : SLAC National Accelerator Laboratory
-------------------------------------------------------------------------------
-- Description: Generates automatic triggers
-------------------------------------------------------------------------------
-- This file is part of 'EPIX Development Firmware'.
-- It is subject to the license terms in the LICENSE.txt file found in the 
-- top-level directory of this distribution and at: 
--    https://confluence.slac.stanford.edu/display/ppareg/LICENSE.html. 
-- No part of 'EPIX Development Firmware', including this file, 
-- may be copied, modified, propagated, or distributed except according to 
-- the terms contained in the LICENSE.txt file.
-------------------------------------------------------------------------------

LIBRARY ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

library surf;
use surf.StdRtlPkg.all;

library UNISIM;
use UNISIM.vcomponents.all;

entity AutoTrigger is
   port (

      -- Master system clock, 125Mhz
      sysClk        : in  sl;
      sysClkRst     : in  sl;

      -- Inputs 
      runTrigIn     : in  sl := '0';
      daqTrigIn     : in  sl := '0';

      -- Number of clock cycles between triggers
      trigPeriod    : in  slv(31 downto 0);

      --Enable run and daq triggers
      runEn         : in  sl;
      daqEn         : in  sl;

      -- Outputs
      runTrigOut    : out sl;
      daqTrigOut    : out sl
   );
end AutoTrigger;

-- Define architecture
architecture AutoTrigger of AutoTrigger is

   -- Local Signals
   signal timeoutTarget : unsigned(31 downto 0);
   signal trigTarget    : unsigned(31 downto 0);
   signal timeoutCnt    : unsigned(31 downto 0) := (others => '0');
   signal iRunTrigOut   : sl := '0';
   signal iDaqTrigOut   : sl := '0';
   -- MUX select types
   type MuxSelType is (EXTERNAL_T, INTERNAL_T);
   signal trigSel       : MuxSelType := EXTERNAL_T;

   -- Register delay for simulation
   constant tpd:time := 0.5 ns;

begin

   -- Convert count target to unsigned
   timeoutTarget <= unsigned(trigPeriod(30 downto 0) & '0');
   trigTarget    <= unsigned(trigPeriod);

   -- Send triggers if you haven't seen one in timeout 
   process(sysClk) begin
      if rising_edge(sysClk) then
         -- On reset, reset the counter to 0
         if (sysClkRst = '1') then
            iRunTrigOut <= '0'             after tpd;
            timeoutCnt  <= (others => '0') after tpd;
         else
            -- Default output
            iRunTrigOut <= '0' after tpd;
            -- Logic to generate triggers
            if runEn = '1' then
               -- If we see a trigger, reset counter and make sure we're in external mode
               if runTrigIn = '1' then
                  timeoutCnt <= (others => '0') after tpd;
                  trigSel    <= EXTERNAL_T      after tpd;
               -- Otherwise, what we do depends on which mode we're running in
               else
                  --Default is to increment the timeout count
                  timeoutCnt <= timeoutCnt + 1 after tpd;
                  case trigSel is
                     -- In external mode, if we see double the timeout, 
                     -- reset the counter and switch to internal
                     when EXTERNAL_T =>
                        if (timeoutCnt >= timeoutTarget) then
                           timeoutCnt <= (others => '0') after tpd;
                           trigSel    <= INTERNAL_T      after tpd;
                        end if;
                     -- In internal mode, fire off a trigger if we 
                     -- get to the target count and reset the count
                     when INTERNAL_T =>
                        if (timeoutCnt >= trigTarget) then
                           timeoutCnt  <= (others => '0') after tpd;
                           iRunTrigOut <= '1'             after tpd;
                        end if;
                  end case;
               end if;
            else
               --If autotriggers are off, select external triggers
               trigSel <= EXTERNAL_T;
            end if;
         end if;
      end if;
   end process;


   -- If daq trigger is enabled, send it one cycle behind run trigger
   process (sysClk) begin
      if rising_edge(sysClk) then
         if (daqEn = '1') then
            iDaqTrigOut <= iRunTrigOut;
         else
            iDaqTrigOut <= '0';
         end if;
      end if;
   end process;

   -- Mux the outputs to get a run and daq trigger out
   process(sysClk) begin
      if rising_edge(sysClk) then
         case trigSel is
            when EXTERNAL_T =>
               runTrigOut <= runTrigIn;
               daqTrigOut <= daqTrigIn;
            when INTERNAL_T =>
               runTrigOut <= iRunTrigOut;
               daqTrigOut <= iDaqTrigOut;
         end case;
      end if;
   end process;

end AutoTrigger;
