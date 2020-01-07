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

entity AD9249GroupUS_tb is

end AD9249GroupUS_tb;

-------------------------------------------------------------------------------

architecture AD9249GroupUS_arch of AD9249GroupUS_tb is

  -- component generics
  constant TPD_G : time := 1 ns;
  constant NUM_CHANNELS_G : integer := 8;

  -- component ports
  signal sysClkRst : std_logic := '1';
  signal idelayCtrlRdy : std_logic := '0';
  signal dClkP : sl := '1';                       -- Data clock
  signal dClkN : sl := '0';
  signal fClkP : sl := '0';                       -- Frame clock
  signal fClkN : sl := '1';
  signal sDataP : sl;                       -- Frame clock
  signal sDataN : sl;
--  signal cmt_locked : sl;
  signal gearboxOffset : slv(2 downto 0) := "000";
  signal bitSlip       : slv(3 downto 0) := "0101";
--  signal pixData       : slv14Array(NUM_CHANNELS_G downto 0);  -- in channels
                                                               -- is the frame
                                                               -- signal

  -- axilite
  signal axilWriteMaster : AxiLiteWriteMasterType;
  signal axilWriteSlave  : AxiLiteWriteSlaveType;
  signal axilReadMaster  : AxiLiteReadMasterType;
  signal axilReadSlave   : AxiLiteReadSlaveType;
  signal registerValue   : slv(31 downto 0);    
  signal adcSerial       : Ad9249SerialGroupType;
  signal adcStreams      : AxiStreamMasterArray(NUM_CHANNELS_G-1 downto 0);


  -- clock
  signal sysClk    : std_logic := '1';

  constant GROUP_TYPE : string := "TOP";     -- "US"

begin  -- Dac8812Cntrl_arch

  -- component instantiation
  GEN_US : if GROUP_TYPE = "US" generate
    DUT0: entity surf.Ad9249ReadoutGroupUS
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

        -- Axi Interface
        axilWriteMaster => axilWriteMaster,
        axilWriteSlave  => axilWriteSlave,
        axilReadMaster  => axilReadMaster,
        axilReadSlave   => axilReadSlave,
 
        -- Serial Data from ADC
        adcSerial => adcSerial,

        -- Deserialized ADC Data
        adcStreamClk => sysClk,
        adcStreams   => adcStreams      
        );
  end generate GEN_US;


  GEN_TOP : if GROUP_TYPE = "TOP" generate
    DUT0: entity surf.Ad9249ReadoutGroup
      generic map (
        TPD_G             => TPD_G,
        NUM_CHANNELS_G    => 8,
        IODELAY_GROUP_G   => "DEFAULT_GROUP",
        XIL_DEVICE_G      => "ULTRASCALE",
        DEFAULT_DELAY_G   => (others => '0'),
        ADC_INVERT_CH_G   => "00000000")
      port map (
        -- Master system clock, 125Mhz
        axilClk => sysClk,
        axilRst => sysClkRst,

        -- Reset for adc deserializer
        adcClkRst => sysClkRst,

        -- Axi Interface
        axilWriteMaster => axilWriteMaster,
        axilWriteSlave  => axilWriteSlave,
        axilReadMaster  => axilReadMaster,
        axilReadSlave   => axilReadSlave,

        -- Signals to/from idelayCtrl
--        idelayCtrlRdy => idelayCtrlRdy,
--        cmt_locked    => cmt_locked,
   
        -- Serial Data from ADC
        adcSerial => adcSerial,

        -- Deserialized ADC Data
        adcStreamClk => sysClk,
        adcStreams   => adcStreams      
        );
  end generate GEN_TOP;
  
  

  
 
  
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

  adcSerial.fClkP <= fClkP;
  adcSerial.fClkN <= fClkN;
  adcSerial.dClkP <= dClkP;
  adcSerial.dClkN <= dClkN;

  adcSerial.chP(0) <= sDataP;
  adcSerial.chN(0) <= sDataN;
  adcSerial.chP(1) <= sDataP;
  adcSerial.chN(1) <= sDataN;
  adcSerial.chP(2) <= sDataP;
  adcSerial.chN(2) <= sDataN;
  adcSerial.chP(3) <= sDataP;
  adcSerial.chN(3) <= sDataN;
  adcSerial.chP(4) <= sDataP;
  adcSerial.chN(4) <= sDataN;
  adcSerial.chP(5) <= sDataP;
  adcSerial.chN(5) <= sDataN;
  adcSerial.chP(6) <= sDataP;
  adcSerial.chN(6) <= sDataN;
  adcSerial.chP(7) <= sDataP;
  adcSerial.chN(7) <= sDataN;
 
  
  -- waveform generation
  WaveGen_Proc: process
    variable registerData    : slv(31 downto 0);
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
    --delayValueIn  <= "111101010";
    wait until sysClk = '1';
    --loadDelay <= '1';
    -- change to axil register command
     wait until sysClk = '0';
    --loadDelay <= '0';
    axiLiteBusSimRead (sysClk, axilReadMaster, axilReadSlave, x"00000020", registerData, true);
    registerValue <= registerData;
    wait for 1 us;
    
    axiLiteBusSimWrite (sysClk, axilWriteMaster, axilWriteSlave, x"00000020", x"00000F55", true);
    wait for 10 us;    
    
    axiLiteBusSimRead (sysClk, axilReadMaster, axilReadSlave, x"00000020", registerData, true);
    registerValue <= registerData;
    wait for 1 us;

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

  

end AD9249GroupUS_arch;

