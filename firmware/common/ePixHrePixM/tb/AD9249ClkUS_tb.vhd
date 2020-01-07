-------------------------------------------------------------------------------
-- File       : AD9249ClkUS_tb.vhd
-- Company    : SLAC National Accelerator Laboratory
-------------------------------------------------------------------------------
-- Description: 
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
use ieee.std_logic_unsigned.all;
use ieee.std_logic_arith.all;
use ieee.numeric_std.all;

library surf;
use surf.StdRtlPkg.all;
use surf.AxiStreamPkg.all;
use surf.AxiLitePkg.all;
use surf.AxiPkg.all;
use surf.Pgp2bPkg.all;
use surf.SsiPkg.all;
use surf.SsiCmdMasterPkg.all;
use surf.Ad9249Pkg.all;
use surf.Code8b10bPkg.all;

library epix_hr_core;
use epix_hr_core.EpixHrCorePkg.all;

use work.AppPkg.all;

library unisim;
use unisim.vcomponents.all;

-------------------------------------------------------------------------------

entity AD9249ClkUS_tb is

end AD9249ClkUS_tb;

-------------------------------------------------------------------------------

architecture AD9249ClkUS_arch of AD9249ClkUS_tb is

  -- component generics
  constant TPD_G : time := 1 ns;

  -- component ports
  signal sysClkRst : std_logic := '1';
  signal idelayCtrlRdy : std_logic := '0';
  signal dClkP : sl := '1';                       -- Data clock
  signal dClkN : sl := '0';
  signal dClkP_i : sl;
  signal dClkN_i : sl;
  signal dClkDiv4_i : sl;
  signal dClkDiv7_i : sl;
  signal fClkP : sl := '0';                       -- Frame clock
  signal fClkN : sl := '1';
  signal sDataP : sl;                       -- Frame clock
  signal sDataN : sl;
  signal cmt_locked : sl;
  signal loadDelay        : sl := '0';
  signal delayValueIn     : slv(8 downto 0) := "000010101";
  signal masterDelayValue : slv(8 downto 0);
  signal slaveDelayValue  : slv(8 downto 0);
  signal dataDelayValue   : slv(8 downto 0);
  signal gearboxOffset : slv(2 downto 0) := "000";
  signal bitSlip       : slv(3 downto 0) := "0101";
  signal pixData       : slv14Array(2-1 downto 0);

  -- clock
  signal sysClk    : std_logic := '1';

begin  -- Dac8812Cntrl_arch

  -- component instantiation
  DUT0: entity surf.Ad9249ReadoutClkUS
     generic map (
      TPD_G             => TPD_G,
      NUM_CHANNELS_G    => 8,
      IODELAY_GROUP_G   => "DEFAULT_GROUP",
      IDELAYCTRL_FREQ_G => 350.0,
      DELAY_VALUE_G     => 1250,
      DEFAULT_DELAY_G   => (others => '0'),
      ADC_INVERT_CH_G   => "00000000")
   port map (
      -- Master system clock, 125Mhz
      axilClk => sysClk,
      axilRst => sysClkRst,

      -- Reset for adc deserializer
      adcClkRst => sysClkRst,

      -- Signals to/from idelayCtrl
      idelayCtrlRdy => idelayCtrlRdy,
      cmt_locked    => cmt_locked,
      
      -- Serial Data from ADC
      dClkP => dClkP,                         -- Data clock
      dClkN => dClkN,
      dClkPOut     => dClkP_i,
      dClkNOut     => dClkN_i,
      dClkDiv4Out  => dClkDiv4_i,
      dClkDiv7Out  => dClkDiv7_i,
      fClkP => fClkP,                       -- Frame clock
      fClkN => fClkN,
      
      
      -- Signal to control data gearboxes
      loadDelay           => loadDelay,
      delay               => delayValueIn,
      masterDelayValueOut => masterDelayValue,
      slaveDelayValueOut  => slaveDelayValue,
      bitSlip => bitSlip,
      gearboxOffset => gearboxOffset,
      pixData => pixData(0)

      -- axilite
      
      );

    DUT1: entity surf.Ad9249DeserializerUS
     generic map (
      TPD_G             => TPD_G,
      NUM_CHANNELS_G    => 8,
      IODELAY_GROUP_G   => "DEFAULT_GROUP",
      IDELAYCTRL_FREQ_G => 350.0,
      DELAY_VALUE_G     => 1250,
      DEFAULT_DELAY_G   => (others => '0'),
      ADC_INVERT_CH_G   => "00000000")
   port map (
      -- Reset for adc deserializer
      adcClkRst => sysClkRst,

      -- Signals to/from idelayCtrl
      idelayCtrlRdy => idelayCtrlRdy,
      
      -- Serial Data from ADC
      dClkP     => dClkP_i,                         -- Data clock
      dClkN     => dClkN_i,
      dClkDiv4  => dClkDiv4_i,
      dClkDiv7  => dClkDiv7_i,
      sDataP    => sDataP,                       -- Frame clock
      sDataN    => sDataN,
            
      -- Signal to control data gearboxes
      loadDelay     => loadDelay,
      delay         => delayValueIn,
      delayValueOut => dataDelayValue,
      bitSlip       => bitSlip,
      gearboxOffset => gearboxOffset,
      pixData       => pixData(1)

      -- axilite
      
      );

  
  -- clock generation
  sysClk <= not sysClk after 6.4 ns;
  --
  fClkP <= not fClkP after 3 * 7 ns;-- 20.0 ns;
  fClkN <= not fClkP;
  dClkP <= not dClkP after 3 ns; --2.857148571485714 ns;--1.428571428571428571428571428571 ns;
  dClkN <= not dClkP;
  --
  sDataP <= not fClkP;
  sDataN <=     fClkP;
  
  -- waveform generation
  WaveGen_Proc: process
  begin

    ---------------------------------------------------------------------------
    -- reset
    ---------------------------------------------------------------------------
    wait until sysClk = '1';
    sysClkRst <= '1';

    wait for 1 us;
    sysClkRst <= '0';
    idelayCtrlRdy <= '1';               -- simulates control ready signal
        
    wait for 10 us;

    ---------------------------------------------------------------------------
    -- laod idelay value
    ---------------------------------------------------------------------------
    delayValueIn  <= "111101010";
    wait until sysClk = '1';
    loadDelay <= '1';
    wait until sysClk = '0';
    loadDelay <= '0';

    ---------------------------------------------------------------------------
    -- start gearbox offset search
    ---------------------------------------------------------------------------
    gearboxOffset <= "000";
    bitSlip <= "0000";

    for i in 0 to 15 loop
      
       wait for 10 us;
       gearboxOffset <= gearboxOffset + 1;
       
    end loop;  -- i

    wait for 10 us;
    
    ---------------------------------------------------------------------------
    -- start gearbox offset search
    ---------------------------------------------------------------------------
    gearboxOffset <= "111";
    bitSlip <= "0000";

    for i in 0 to 15 loop

      wait for 10 us;
      bitSlip <= bitSlip + 1;

    end loop;

    wait for 10 us;
    
    ---------------------------------------------------------------------------
    -- start gearbox offset search
    ---------------------------------------------------------------------------
    gearboxOffset <= "000";
    bitSlip <= "0000";

    for i in 0 to 15 loop

      wait for 10 us;
      bitSlip <= bitSlip + 1;

    end loop;

    bitSlip <= "1011";


    
    wait;
  end process WaveGen_Proc;

  

end AD9249ClkUS_arch;

