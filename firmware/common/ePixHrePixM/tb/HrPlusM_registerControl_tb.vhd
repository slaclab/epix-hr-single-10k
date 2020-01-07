-------------------------------------------------------------------------------
-- File       : cryo_tb.vhd
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
use ieee.std_logic_textio.all;
use ieee.std_logic_arith.all;
use ieee.numeric_std.all;

library STD;
use STD.textio.all;      

library surf;
use surf.StdRtlPkg.all;
use surf.AxiStreamPkg.all;
use surf.AxiLitePkg.all;
use surf.AxiPkg.all;
use surf.Pgp2bPkg.all;
use surf.SsiPkg.all;
use surf.SsiCmdMasterPkg.all;
use surf.Code8b10bPkg.all;

library ruckus;
use ruckus.BuildInfoPkg.all;

library epix_hr_core;
use epix_hr_core.EpixHrCorePkg.all;

use work.HrAdcPkg.all;
use work.AppPkg.all;

library unisim;
use unisim.vcomponents.all;

-------------------------------------------------------------------------------

entity HrPlusM_registerControl_tb is
     generic (
      TPD_G        : time := 1 ns;
      BUILD_INFO_G : BuildInfoType := BUILD_INFO_C);
end HrPlusM_registerControl_tb;

-------------------------------------------------------------------------------

architecture arch of HrPlusM_registerControl_tb is

  -- component generics
  constant NUM_CHANNELS_G : integer := 8;
  constant IDLE_PATTERN_C : slv(15 downto 0) := x"00FF";
  constant STREAMS_PER_ASIC_C : natural := 2;
  -- Axilite constants
  constant APP_REG_AXI_INDEX_C : integer := 0;
  constant DAC_MODULE_INDEX_C  : integer := 1;

  --file definitions
  constant DATA_BITS   : natural := 16;
  constant DEPTH_C     : natural := 1024;
  constant FILENAME_C  : string  := "/afs/slac.stanford.edu/u/re/ddoering/localGit/epix-hr-dev/firmware/simulations/CryoEncDec/sin.csv";
  subtype word_t  is slv(DATA_BITS - 1 downto 0);
  type    ram_t   is array(0 to DEPTH_C - 1) of word_t;

  impure function readWaveFile(FileName : STRING) return ram_t is
    file     FileHandle   : TEXT open READ_MODE is FileName;
    variable CurrentLine  : LINE;
    variable TempWord     : integer; --slv(DATA_BITS - 1 downto 0);
    variable TempWordSlv  : slv(16 - 1 downto 0);
    variable Result       : ram_t    := (others => (others => '0'));
  begin
    for i in 0 to DEPTH_C - 1 loop
      exit when endfile(FileHandle);
      readline(FileHandle, CurrentLine);
      read(CurrentLine, TempWord);
      TempWordSlv  := toSlv(TempWord, 16);
      Result(i)    := TempWordSlv(15 downto 16 - DATA_BITS);
    end loop;
    return Result;
  end function;

  -- waveform signal
  signal ramWaveform      : ram_t    := readWaveFile(FILENAME_C);
  signal ramTestWaveform  : ram_t    := readWaveFile(FILENAME_C);
  
  -- component ports
  signal sysClkRst   : std_logic := '1';
  signal sysClkRst_n : sl := '0';
  signal appRst      : std_logic;
  signal axilRst     : std_logic;
  signal axiRst      : sl;
  

  -- axilite
  -- 0 register control
  -- 1 TBD
  signal sAxilReadMaster  : AxiLiteReadMasterArray(1 downto 0):= (others=>AXI_LITE_READ_MASTER_INIT_C);
  signal sAxilReadSlave   : AxiLiteReadSlaveArray(1 downto 0);
  signal sAxilWriteMaster : AxiLiteWriteMasterArray(1 downto 0):= (others=>AXI_LITE_WRITE_MASTER_INIT_C);
  signal sAxilWriteSlave  : AxiLiteWriteSlaveArray(1 downto 0);
  
  --
  signal registerValue   : slv(31 downto 0);    

  -- clock
  signal sysClk    : std_logic := '1';
  signal appClk    : std_logic := '1';


  -- test trigger
  signal testTrig          : sl := '0';

  -- framer test
  signal acqNo             : slv(31 downto 0) := (others=>'0');
  signal boardConfig       : AppConfigType;
  signal serialIdIo        : slv(1 downto 0);
  signal adcClk            : sl;
  signal acqStart          : sl := '0';
  signal saciPrepReadoutReq    : sl;
  signal saciPrepReadoutAck    : sl;
  signal iAsicPPbe          : sl;
  signal iAsicPpmat         : sl;
  signal iAsicTpulse        : sl;
  signal iAsicStart         : sl;
  signal iAsicSR0           : sl;
  signal iAsicGrst          : sl;
  signal iAsicSync          : sl;
  signal iAsicAcq           : sl;
  signal iAsicVid           : sl;
  signal iAsicSsrRst        : sl;
  signal iAsicSsrSerClrb    : sl;
  signal iAsicSsrStoClrb    : sl;
  signal iAsicSsrData       : sl;
  signal iAsicSsrClk        : sl;
  signal errInhibit         : sl;
  -- slow DACs
  signal sDacSclk_i         : sl;
  signal sDacDin_i          : sl;
  signal sDacCsL_i          : slv(4 downto 0);
  signal sDacClrb_i         : sl;


begin  --

  sysClkRst_n <= not sysClkRst;
  appRst <= sysClkRst;


  DUT0: entity work.RegisterControl
   generic map (
      TPD_G            => TPD_G,
      EN_DEVICE_DNA_G  => false,        -- this is causing placement errors,
                                        -- needs fixing.
      BUILD_INFO_G     => BUILD_INFO_G
   )
   port map (
      axiClk         => appClk,
      axiRst         => axiRst,
      sysRst         => appRst,
      -- AXI-Lite Register Interface (axiClk domain)
      axiReadMaster  => sAxilReadMaster(APP_REG_AXI_INDEX_C),
      axiReadSlave   => sAxilReadSlave(APP_REG_AXI_INDEX_C),
      axiWriteMaster => sAxilWriteMaster(APP_REG_AXI_INDEX_C),
      axiWriteSlave  => sAxilWriteSlave(APP_REG_AXI_INDEX_C),
      -- Register Inputs/Outputs (axiClk domain)
      boardConfig    => boardConfig,
      -- 1-wire board ID interfaces
      serialIdIo     => serialIdIo,
      -- fast ADC clock
      adcClk         => open,
      -- ASICs acquisition signals
      acqStart       => acqStart,
      saciReadoutReq => saciPrepReadoutReq,
      saciReadoutAck => saciPrepReadoutAck,
      asicPPbe       => iAsicPpbe,
      asicPpmat      => iAsicPpmat,
      asicTpulse     => open,
      asicStart      => open,
      asicSR0        => iAsicSR0,
      asicGlblRst    => iAsicGrst,
      asicSync       => iAsicSync,
      asicAcq        => iAsicAcq,
      asicVid        => open,
      asicSsrRst     => iAsicSsrRst,
      asicSsrSerClrb => iAsicSsrSerClrb,
      asicSsrStoClrb => iAsicSsrStoClrb,
      asicSsrData    => iAsicSsrData,
      asicSsrClk     => iAsicSsrClk,
      errInhibit     => errInhibit
   );

  U_DACs : entity work.slowDacs 
   generic map (
      TPD_G             => TPD_G,
      CLK_PERIOD_G      => 10.0E-9
   )
   port map (
      -- Global Signals
      axiClk => appClk,
      axiRst => appRst,
      -- AXI-Lite Register Interface (axiClk domain)
      axiReadMaster  => sAxilReadMaster(DAC_MODULE_INDEX_C), 
      axiReadSlave   => sAxilReadSlave(DAC_MODULE_INDEX_C),
      axiWriteMaster => sAxilWriteMaster(DAC_MODULE_INDEX_C),
      axiWriteSlave  => sAxilWriteSlave(DAC_MODULE_INDEX_C),
      -- Guard ring DAC interfaces
      dacSclk        => sDacSclk_i,
      dacDin         => sDacDin_i,      
      dacCsb         => sDacCsL_i,
      dacClrb        => sDacClrb_i
   );
  
  -- clock generation
  sysClk    <= not sysClk after 3.2 ns;
  appClk    <= not appClk after 5 ns;

  
  -- waveform generation
  WaveGen_Proc: process
    variable registerData    : slv(31 downto 0);  
  begin

    ---------------------------------------------------------------------------
    -- reset
    ---------------------------------------------------------------------------
    wait until sysClk = '1';
    sysClkRst  <= '1';

    wait for 1 us;
    sysClkRst <= '0';

    ---------------------------------------------------------------------------
    -- load axilite registers
    ---------------------------------------------------------------------------
    --
    wait until sysClk = '1';
    -- change to axil register command
    wait until sysClk = '0';

    axiLiteBusSimRead (sysClk, sAxilReadMaster(APP_REG_AXI_INDEX_C), sAxilReadSlave(APP_REG_AXI_INDEX_C), x"00000000", registerData, true);
    registerValue <= registerData;
    
    wait for 1 us;
    axiLiteBusSimWrite (sysClk, sAxilWriteMaster(APP_REG_AXI_INDEX_C), sAxilWriteSlave(APP_REG_AXI_INDEX_C), x"00000000", registerData, true);

    --slow DACs
    registerData := x"0000_0010";
    wait until sysClk = '1';
    axiLiteBusSimWrite (sysClk, sAxilWriteMaster(DAC_MODULE_INDEX_C), sAxilWriteSlave(DAC_MODULE_INDEX_C), x"0000000C", registerData, true);
    wait for 5 us;
    wait until sysClk = '1';
    axiLiteBusSimWrite (sysClk, sAxilWriteMaster(DAC_MODULE_INDEX_C), sAxilWriteSlave(DAC_MODULE_INDEX_C), x"00000010", registerData, true);
    wait for 5 us;
    wait until sysClk = '1';
    axiLiteBusSimWrite (sysClk, sAxilWriteMaster(DAC_MODULE_INDEX_C), sAxilWriteSlave(DAC_MODULE_INDEX_C), x"00000000", registerData, true);
    wait for 5 us;
    wait until sysClk = '1';
    axiLiteBusSimWrite (sysClk, sAxilWriteMaster(DAC_MODULE_INDEX_C), sAxilWriteSlave(DAC_MODULE_INDEX_C), x"00000004", registerData, true);
    wait for 5 us;
    wait until sysClk = '1';
    axiLiteBusSimWrite (sysClk, sAxilWriteMaster(DAC_MODULE_INDEX_C), sAxilWriteSlave(DAC_MODULE_INDEX_C), x"00000008", registerData, true);
    
    --SR0
    wait for 1 us;wait until sysClk = '0';
    registerData := x"0000_0010";
    axiLiteBusSimWrite (sysClk, sAxilWriteMaster(APP_REG_AXI_INDEX_C), sAxilWriteSlave(APP_REG_AXI_INDEX_C), x"00000178", registerData, true);
    registerData := x"0000_1410";
    axiLiteBusSimWrite (sysClk, sAxilWriteMaster(APP_REG_AXI_INDEX_C), sAxilWriteSlave(APP_REG_AXI_INDEX_C), x"0000017C", registerData, true);

    --ssrRst
    registerData := x"0000_0001";
    axiLiteBusSimWrite (sysClk, sAxilWriteMaster(APP_REG_AXI_INDEX_C), sAxilWriteSlave(APP_REG_AXI_INDEX_C), x"00000188", registerData, true);
    registerData := x"0000_1410";
    axiLiteBusSimWrite (sysClk, sAxilWriteMaster(APP_REG_AXI_INDEX_C), sAxilWriteSlave(APP_REG_AXI_INDEX_C), x"0000018C", registerData, true);
    
    

    wait for 80 us;
    wait until appClk = '1';
    acqStart <= '1';
    wait until appClk = '1';
    acqStart <= '0';

    wait for 80 us;
    axiLiteBusSimRead (sysClk, sAxilReadMaster(APP_REG_AXI_INDEX_C), sAxilReadSlave(APP_REG_AXI_INDEX_C), x"000001A0", registerData, true);
    wait for 1 us;
    axiLiteBusSimWrite (sysClk, sAxilWriteMaster(APP_REG_AXI_INDEX_C), sAxilWriteSlave(APP_REG_AXI_INDEX_C), x"000001A0", x"AA75_55FE", true);
    wait for 1 us;
    axiLiteBusSimWrite (sysClk, sAxilWriteMaster(APP_REG_AXI_INDEX_C), sAxilWriteSlave(APP_REG_AXI_INDEX_C), x"000001A4", x"73", true);
    wait for 1 us;
    axiLiteBusSimRead (sysClk, sAxilReadMaster(APP_REG_AXI_INDEX_C), sAxilReadSlave(APP_REG_AXI_INDEX_C), x"000001A0", registerData, true);
    wait for 1 us;
    wait until appClk = '1';
    acqStart <= '1';
    

    wait until appClk = '1';
    acqStart <= '0';
    
    wait for 100 us;
    

    wait for 10 us;
    
    wait;
  end process WaveGen_Proc;

  

end arch;

