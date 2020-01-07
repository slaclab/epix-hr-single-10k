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
use surf.Code8b10bPkg.all;

use work.AppPkg.all;

library unisim;
use unisim.vcomponents.all;

-------------------------------------------------------------------------------

entity HR16bClkUs_tb is

end HR16bClkUs_tb;

-------------------------------------------------------------------------------

architecture arch of HR16bClkUs_tb is

  -- component generics
  constant TPD_G : time := 1 ns;

  -- component ports
  signal sysClkRst : std_logic := '1';
  signal idelayCtrlRdy : std_logic := '0';
  signal dClkP : sl := '1';                       -- Data clock
  signal dClkN : sl := '0';
  signal dClkP_i : sl;
  signal dClkN_i : sl;
  signal dClkDiv4_i : sl := '0';
  signal dClkDiv5_i : sl := '0';
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
  signal gearboxOffset : slv(1 downto 0) := "00";
  signal bitSlip       : slv(2 downto 0) := "101";
  signal dataValid     : sl;
  signal pixData       : slv20Array(2-1 downto 0);

  -- clock
  signal sysClk    : std_logic := '1';

begin  -- Dac8812Cntrl_arch

  -- component instantiation
  DUT0: entity work.Hr16bAdcDeserializer
    generic map (
      TPD_G             => TPD_G,
      NUM_CHANNELS_G    => 8,
      IODELAY_GROUP_G   => "DEFAULT_GROUP",
      IDELAYCTRL_FREQ_G => 350.0,
      DEFAULT_DELAY_G   => (others => '0'),
      FRAME_PATTERN_G   => "00000000001111111111",
      ADC_INVERT_CH_G   => '0',
      BIT_REV_G         => '1',
      MSB_LSB_G         => '1')
    port map (
      -- Reset for adc deserializer
      adcClkRst => sysClkRst,

      -- Signals to/from idelayCtrl
      idelayCtrlRdy => idelayCtrlRdy,
      
      -- Serial Data from ADC
      dClk      => dClkP_i,                         -- Data clock
      dClkDiv4  => dClkDiv4_i,
      dClkDiv5  => dClkDiv5_i,
      sDataP    => sDataP,                       -- Frame clock
      sDataN    => sDataN,
            
      -- Signal to control data gearboxes
      loadDelay     => loadDelay,
      delay         => delayValueIn,
      delayValueOut => dataDelayValue,
      bitSlip       => bitSlip,
      gearboxOffset => gearboxOffset,
      dataValid     => dataValid,
      pixData       => pixData(1)

      -- axilite
      
      );

  
  -- clock generation
  sysClk <= not sysClk after 6.4 ns;
  --
  fClkP <= not fClkP after 3 * 10 ns;-- 20.0 ns;
  fClkN <= not fClkP;
  dClkP <= not dClkP after 3 ns; --2.857148571485714 ns;--1.428571428571428571428571428571 ns;
  dClkN <= not dClkP;
  dClkDiv4_i <= not dClkDiv4_i after 3 * 4 ns;
  --
  sDataP <= not fClkP;
  sDataN <=     fClkP;

  dClkP_i    <= dClkP;
  dClkDiv5_i <=  not dClkDiv5_i after 3 * 5 ns;

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
    gearboxOffset <= "00";
    bitSlip <= "000";

    for i in 0 to 15 loop
      
       wait for 10 us;
       gearboxOffset <= gearboxOffset + 1;
       
    end loop;  -- i

    wait for 10 us;
    
    ---------------------------------------------------------------------------
    -- start gearbox offset search
    ---------------------------------------------------------------------------
    gearboxOffset <= "10";
    bitSlip <= "000";

    for i in 0 to 15 loop

      wait for 10 us;
      bitSlip <= bitSlip + 1;

    end loop;

    wait for 10 us;
    
    ---------------------------------------------------------------------------
    -- start gearbox offset search
    ---------------------------------------------------------------------------
    gearboxOffset <= "10";
    bitSlip <= "010";

    for i in 0 to 15 loop

      wait for 10 us;
      bitSlip <= bitSlip + 1;

    end loop;

    bitSlip <= "010";


    
    wait;
  end process WaveGen_Proc;

  

end arch;

