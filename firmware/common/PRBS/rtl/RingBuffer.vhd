-------------------------------------------------------------------------------
-- Title      : Ring Buffer
-- Project    : EPIX Readout
-------------------------------------------------------------------------------
-- File       : RingBuffer.vhd
-- Company    : SLAC National Accelerator Laboratory
-------------------------------------------------------------------------------
-- Description:
-- Ring buffer, originally made for use with the pseudo oscilloscope for ePix.
-------------------------------------------------------------------------------
-- This file is part of 'EPIX Development Firmware'.
-- It is subject to the license terms in the LICENSE.txt file found in the 
-- top-level directory of this distribution and at: 
--    https://confluence.slac.stanford.edu/display/ppareg/LICENSE.html. 
-- No part of 'EPIX Development Firmware', including this file, 
-- may be copied, modified, propagated, or distributed except according to 
-- the terms contained in the LICENSE.txt file.
-------------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

library surf;
use surf.StdRtlPkg.all;

entity RingBuffer is
   generic (
      MEMORY_TYPE_G: string := "block";
      DATA_WIDTH_G : integer := 16;
      ADDR_WIDTH_G : integer := 12);
   port (
      -- Clocks and reset
      sysClk      : in  sl; 
      sysClkRst   : in  sl; 
      -- Input data
      wrData      : in  slv(DATA_WIDTH_G-1 downto 0); 
      wrValid     : in  sl; 
      -- Interfaces
      arm         : in  sl; 
      trigger     : in  sl; 
      rdEn        : in  sl; 
      rdData      : out slv(DATA_WIDTH_G-1 downto 0); 
      rdReady     : out sl; 
      rdDone      : out sl; 
      -- Sampling configuration
      holdoff     : in  slv(ADDR_WIDTH_G-1 downto 0); 
      offset      : in  slv(ADDR_WIDTH_G-1 downto 0); 
      skipSamples : in  slv(ADDR_WIDTH_G-1 downto 0); 
      depth       : in  slv(ADDR_WIDTH_G-1 downto 0));
end RingBuffer;

-- Define architecture
architecture rtl of RingBuffer is

   type StateType is (
      IDLE_S,
      ARMED_S,
      TRIGGERED_S,
      READING_S,
      DONE_S);
   signal curState : StateType := IDLE_S;
   signal nxtState : StateType := IDLE_S;

   signal sampEn    : sl := '0';
   signal wrAddr    : unsigned(ADDR_WIDTH_G-1 downto 0) := (others => '0');
   signal wrDataReg : std_logic_vector(DATA_WIDTH_G-1 downto 0) := (others => '0');
   signal rdCnt     : unsigned(ADDR_WIDTH_G downto 0) := (others => '0');
   signal rdAddr    : unsigned(ADDR_WIDTH_G-1 downto 0) := (others => '0');
   signal rdAddrRst : sl := '0';
   signal rdAddrInc : sl := '0';
   signal iRdDone   : sl := '0';

   signal sampAccept : sl := '0';

   signal holdoffCnt    : unsigned(ADDR_WIDTH_G-1 downto 0) := (others => '0');
   signal holdoffCntEn  : sl := '0';
   signal holdoffCntRst : sl := '0';
   signal sampleCnt     : unsigned(ADDR_WIDTH_G downto 0) := (others => '0');
   signal sampleCntRst  : sl := '0';
   signal sampleCntEn   : sl := '0';
   signal skipCnt       : unsigned(ADDR_WIDTH_G-1 downto 0) := (others => '0');
   
begin

   SimpleDualPortRam_Inst : entity surf.SimpleDualPortRam
      generic map(
         MEMORY_TYPE_G=> "block",
         DATA_WIDTH_G => 16,
         ADDR_WIDTH_G => ADDR_WIDTH_G)
      port map (
         -- Port A
         clka  => sysClk,
         wea   => sampAccept,
         addra => slv(wrAddr),
         dina  => wrDataReg,
         -- Port B
         clkb  => sysClk,
         addrb => slv(rdAddr),
         doutb => rdData);

   -- Synchronous next state
   process (sysClk) begin
      if rising_edge(sysClk) then
         if sysClkRst = '1' then
            curState <= IDLE_S;
         else
            curState <= nxtState;
         end if;
      end if;
   end process;

   -- Asynchronous state output and next state
   process (curState,arm,holdoffCnt,trigger,sampleCnt,depth,wrAddr,rdCnt,rdEn)
   begin
      sampEn        <= '0';
      holdoffCntRst <= '0';
      holdoffCntEn  <= '0';
      sampleCntRst  <= '0';
      sampleCntEn   <= '1';
      rdReady       <= '0';
      iRdDone       <= '0';
      rdAddrRst     <= '0';
      rdAddrInc     <= '0';
      nxtState      <= curState;
      case (curState) is
         --------------------------------------------------------------------
         when IDLE_S =>
            holdoffCntRst <= '1';
            sampleCntRst  <= '1';
            if arm = '1' then
               nxtState <= ARMED_S;
            end if;
         --------------------------------------------------------------------
         when ARMED_S =>
            sampEn       <= '1';
            sampleCntRst <= '1';
            if holdoffCnt > 0 then
               holdoffCntEn <= '1';
            else
               holdoffCntEn <= '0';
               if trigger = '1' then
                  nxtState <= TRIGGERED_S;
                  rdAddrRst <= '1';
               end if;
            end if;
         --------------------------------------------------------------------
         when TRIGGERED_S =>
            sampEn      <= '1';
            if sampleCnt >  0 then
               sampleCntEn <= '1';
            else
               sampleCntEn <= '0';
               nxtState  <= READING_S;
            end if;
         --------------------------------------------------------------------
         when READING_S =>
            rdReady     <= '1';
            sampleCntEn <= '0';
            if (rdEn = '1') then
               rdAddrInc <= '1';
               if (rdCnt = 0) then
                  nxtState <= DONE_S;
               end if;
            end if;
         --------------------------------------------------------------------
         when DONE_S =>
            rdReady  <= '1';
            iRdDone  <= '1';
            nxtState <= IDLE_S;
         --------------------------------------------------------------------
         when others =>
            --Use defaults
      end case;
   end process;

   -- Determine which samples to accept
   process (sysClk) begin
      if rising_edge(sysClk) then
         sampAccept <= '0';
         if sampEn = '1' and wrValid = '1' then
            if skipCnt = 0 then
               sampAccept <= '1';
               wrDataReg  <= wrData;
               skipCnt    <= unsigned(skipSamples);
            else
               skipCnt    <= skipCnt - 1;
            end if;
         end if;
      end if;
   end process;
   -- Holdoff counter
   process (sysClk) begin
      if rising_edge(sysClk) then
         if holdoffCntRst = '1' then
            holdoffCnt <= unsigned(holdoff);
         elsif sampAccept = '1' and holdoffCntEn = '1' then
            holdoffCnt <= holdoffCnt - 1;
         end if;
      end if;
   end process;
   -- Number of samples counter
   process (sysClk) begin
      if rising_edge(sysClk) then
         if sampleCntRst = '1' then
--            sampleCnt <= resize(unsigned(depth), ADDR_WIDTH_G+1) - resize(unsigned(offset),ADDR_WIDTH_G+1) + 1;
            sampleCnt <= resize(unsigned(depth), ADDR_WIDTH_G+1) - resize(unsigned(offset),ADDR_WIDTH_G+1);
         elsif sampAccept = '1' and sampleCntEn = '1' then
            sampleCnt <= sampleCnt - 1;
         end if;
         --Write address should always be incrementing if we
         --are accepting samples
         if sampAccept = '1' and sampleCntEn = '1' then
            wrAddr    <= wrAddr    + 1;
         end if;
      end if;
   end process;
   -- Readout counter
   process (sysClk) begin
      if rising_edge(sysClk) then
         if rdAddrRst = '1' then
            rdAddr <= wrAddr - unsigned(offset);
--            rdCnt  <= resize(unsigned(depth),ADDR_WIDTH_G+1) + 1;
            rdCnt  <= resize(unsigned(depth),ADDR_WIDTH_G+1);
         elsif rdAddrInc = '1' then
            rdAddr <= rdAddr + 1;
            rdCnt  <= rdCnt - 1;
         end if;
      end if;
   end process;
   --Register for the output read done signal
   process(sysClk) begin
      if rising_edge(sysClk) then
         rdDone <= iRdDone;
      end if;
   end process;

end rtl;

