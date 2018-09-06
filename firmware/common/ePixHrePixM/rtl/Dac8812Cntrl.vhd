------------------------------------------------------------------------------
-- Title         : DAC Controller
-- Project       : ePix HR Detector
-------------------------------------------------------------------------------
-- File          : Dac8812Cntrl.vhd
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


entity Dac8812Cntrl is
   generic (
      TPD_G : time := 1 ns
   ); 
   port ( 

      -- Master system clock
      sysClk          : in  std_logic;
      sysClkRst       : in  std_logic;

      -- DAC Data
      dacData         : in  std_logic_vector(15 downto 0);
      dacCh           : in  std_logic_vector( 1 downto 0); -- 00: none, 01: DAC A, 10:DAC B, 11: DAC A and DAC B

      -- DAC Control Signals
      dacDin          : out std_logic;
      dacSclk         : out std_logic;
      dacCsL          : out std_logic;
      dacLdacL        : out std_logic;
      dacClrL         : out std_logic
   );
end Dac8812Cntrl;


-- Define architecture
architecture Dac8812Cntrl of Dac8812Cntrl is


   attribute keep : string;

   -- Local Signals
   signal intData     : std_logic_vector(17 downto 0); -- appends the dacData and dacCh
   signal intCnt      : std_logic_vector(2  downto 0);
   signal intClk      : std_logic;
   signal intClkEn    : std_logic;
   signal intBitRst   : std_logic;
   signal intBitEn    : std_logic;
   signal intBit      : std_logic_vector(4 downto 0);
   signal nxtDin      : std_logic;
   signal nxtCsL      : std_logic;
   signal dacStrobe   : std_logic;
   signal intdacLdacL : std_logic;

   -- State Machine
   constant ST_IDLE      : std_logic_vector(2 downto 0) := "001";
   constant ST_WAIT      : std_logic_vector(2 downto 0) := "010";
   constant ST_SHIFT     : std_logic_vector(2 downto 0) := "011";
   constant ST_WAIT_LD   : std_logic_vector(2 downto 0) := "100";
   constant ST_LOAD      : std_logic_vector(2 downto 0) := "101";
   signal   curState     : std_logic_vector(2 downto 0);
   signal   nxtState     : std_logic_vector(2 downto 0);

   attribute keep of curState : signal is "true";
   attribute keep of dacStrobe : signal is "true";

begin

   -- Clear
   dacClrL <= '0' when sysClkRst = '1' else '1'; 

   -- Modified so that strobe is internally generated when input data changes.
   process ( sysClk ) begin
      if rising_edge(sysClk) then
         if (sysClkRst = '1') then
            intData   <= (dacCh & dacData) after TPD_G;
            dacStrobe <= '0' after TPD_G;
         elsif (intData /= (dacCh & dacData)) then
            dacStrobe <= '1' after TPD_G;
            intData   <= dacCh & dacData after TPD_G;
         else
            dacStrobe <= '0' after TPD_G;
         end if;
      end if;
   end process;

   -- Generate clock and enable signal
   process ( sysClk, sysClkRst ) begin
      if sysClkRst = '1' then
         intClk   <= '0'           after TPD_G;
         intCnt   <= (others=>'0') after TPD_G;
         intClkEn <= '0'           after TPD_G;
      elsif rising_edge(sysClk) then
         if intCnt = 1 then             -- should generate a 50MHz clock, 7 was
                                        -- the original parameter.
            intCnt   <= (others=>'0') after TPD_G;
            intClk   <= not intClk    after TPD_G;
            intClkEn <= intClk        after TPD_G;
         else
            intCnt   <= intCnt + 1    after TPD_G;
            intClkEn <= '0'           after TPD_G;
         end if;
      end if;
   end process;

   -- Output clock
   dacSclk <= '0' when curState = ST_IDLE else intClk;
   
   -- async load dac value
   process ( sysClk, sysClkRst ) begin
      if sysClkRst = '1' then
         dacLdacL <= '1';
      elsif rising_edge(sysClk) then
         dacLdacL <= intdacLdacL after TPD_G;  
      end if;
   end process;

   -- State machine
   process ( sysClk, sysClkRst ) begin
      if sysClkRst = '1' then
         intBit   <= "10010" after TPD_G; -- init counter with 18 to point to the MSB
         curState <= ST_IDLE       after TPD_G;
      elsif rising_edge(sysClk) then

         -- Bit counter
         if intBitRst = '1' then
            intBit <= "10001" after TPD_G;
         elsif intBitEn = '1' then
            intBit <= intBit - 1 after TPD_G;
         end if;

         -- DAC controls
         dacDin <= nxtDin after TPD_G;
         dacCsL <= nxtCsL after TPD_G;

         -- State
         curState <= nxtState after TPD_G;
      end if;
   end process;

   -- State machine
   process ( curState, intBit, dacStrobe, intClkEn, intData ) begin
      case ( curState ) is

         -- IDLE
         when ST_IDLE =>
            intBitRst   <= '1';
            intBitEn    <= '0';
            nxtDin      <= '0';
            nxtCsL      <= '1';
            intdacLdacL <= '1';

            if dacStrobe = '1' then
               nxtState <= ST_WAIT;
            else 
               nxtState <= curState;
            end if;

         -- Wait for neg edge
         when ST_WAIT =>
            intBitRst   <= '1';
            intBitEn    <= '0';
            nxtDin      <= '0';
            nxtCsL      <= '1';
            intdacLdacL <= '1';

            if intClkEn = '1' then
               nxtState <= ST_SHIFT;
            else 
               nxtState <= curState;
            end if;

         -- Shift data
         when ST_SHIFT =>
            intBitRst   <= '0';
            intBitEn    <= intClkEn;
            nxtDin      <= intData(conv_integer(intBit));
            nxtCsL      <= '0';
            intdacLdacL <= '1';

            if intClkEn = '1' and intBit = 0 then
               nxtState <= ST_WAIT_LD;
            else 
               nxtState <= curState;
            end if;
            
         -- Async load data
         when ST_WAIT_LD =>
               intBitRst   <= '1';
               intBitEn    <= '0';
               nxtDin      <= '0';
               nxtCsL      <= '1';
               intdacLdacL <= '1';
   
               nxtState <= ST_LOAD;
                        
         -- Async load data
         when ST_LOAD =>
            intBitRst   <= '1';
            intBitEn    <= '0';
            nxtDin      <= '0';
            nxtCsL      <= '1';
            intdacLdacL <= '0';

            nxtState <= ST_IDLE;
            
         when others =>
            intBitRst   <= '0';
            intBitEn    <= '0';
            nxtDin      <= '0';
            nxtCsL      <= '0';
            intdacLdacL <= '1';
            nxtState  <= ST_IDLE;
      end case;
   end process;

end Dac8812Cntrl;

