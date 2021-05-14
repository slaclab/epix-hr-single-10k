-------------------------------------------------------------------------------
-- File       : ePixHr10kT_full_tb.vhd
-- Company    : SLAC National Accelerator Laboratory
-------------------------------------------------------------------------------
-- Description: Testbench for design "ePixHr10kT"
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
use surf.SsiPkg.all;
use surf.SsiCmdMasterPkg.all;
use surf.Code8b10bPkg.all;

library epix_hr_core;
use epix_hr_core.EpixHrCorePkg.all;

library ruckus;
use ruckus.BuildInfoPkg.all;

use work.HrAdcPkg.all;
use work.AppPkg.all;

library unisim;
use unisim.vcomponents.all;

-------------------------------------------------------------------------------

entity ePixHr10kT_full_tb is
     generic (
      TPD_G        : time := 1 ns;
      BUILD_INFO_G : BuildInfoType := BUILD_INFO_C;
      IDLE_PATTERN_C : slv(15 downto 0) := x"00FF"  -- "11 0100 0000 0111"
      );
end ePixHr10kT_full_tb;

-------------------------------------------------------------------------------

architecture arch of ePixHr10kT_full_tb is

  --file definitions
  constant DATA_BITS   : natural := 16;
  constant DEPTH_C     : natural := 1024;
  constant FILENAME_C  : string  := "/afs/slac.stanford.edu/u/re/ddoering/localGit/epix-hr-dev/firmware/targets/EpixHr10kT/tb/sin.csv";
  --simulation constants to select data type
  constant CH_ID       : natural := 0;
  constant CH_WF       : natural := 1;
  constant DATA_TYPE_C : natural := CH_ID;
  
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


  -----------------------------------------------------------------------------
  -- Signals to mimic top module io
  -----------------------------------------------------------------------------
      -----------------------
      -- Application Ports --
      -----------------------
      -- System Ports
      signal digPwrEn      : sl;
      signal anaPwrEn      : sl;
      signal syncDigDcDc   : sl;
      signal syncAnaDcDc   : sl;
      signal syncDcDc      : slv(6 downto 0);
      signal daqTg         : sl;
      signal connTgOut     : sl;
      signal connMps       : sl;
      signal connRun       : sl;
      -- Fast ADC Ports
      signal adcSpiClk     : sl;
      signal adcSpiData    : sl;
      signal adcSpiCsL     : sl;
      signal adcPdwn       : sl;
      signal adcClkP       : sl;
      signal adcClkM       : sl;
      signal adcDoClkP     : sl;
      signal adcDoClkM     : sl;
      signal adcFrameClkP  : sl;
      signal adcFrameClkM  : sl;
      signal adcMonDoutP   : slv(4 downto 0);
      signal adcMonDoutN   : slv(4 downto 0);
      -- Slow ADC
      signal slowAdcSclk   : sl;
      signal slowAdcDin    : sl;
      signal slowAdcCsL    : sl;
      signal slowAdcRefClk : sl;
      signal slowAdcDout   : sl;
      signal slowAdcDrdy   : sl;
      signal slowAdcSync   : sl;
      -- Slow DACs Port
      signal sDacCsL       : slv(4 downto 0);
      signal hsDacCsL      : sl;
      signal hsDacLoad     : sl;
      signal dacClrL       : sl;
      signal dacSck        : sl;
      signal dacDin        : sl;
      -- ASIC Gbps Ports
      signal asicDataP     : slv(23 downto 0);
      signal asicDataN     : slv(23 downto 0);
      -- ASIC Control Ports
      signal asicR0        : sl;
      signal asicSR0       : sl;
      signal asicPpmat     : sl;
      signal asicGlblRst   : sl;
      signal asicSync      : sl;
      signal asicAcq       : sl;
      signal asicRoClkP    : slv(3 downto 0);
      signal asicRoClkN    : slv(3 downto 0);
      -- SACI Ports
      signal asicSaciCmd   : sl;
      signal asicSaciClk   : sl;
      signal asicSaciSel   : slv(3 downto 0);
      signal asicSaciRsp   : sl;
      -- Spare Ports
      signal spareHpP      : slv(11 downto 0);
      signal spareHpN      : slv(11 downto 0);
      signal spareHrP      : slv(5 downto 0);
      signal spareHrN      : slv(5 downto 0);
      -- GTH Ports
      signal gtRxP         : sl;
      signal gtRxN         : sl;
      signal gtTxP         : sl;
      signal gtTxN         : sl;
      signal gtRefP        : sl;
      signal gtRefN        : sl;
      signal smaRxP        : sl;
      signal smaRxN        : sl;
      signal smaTxP        : sl;
      signal smaTxN        : sl;
      ----------------
      -- Core Ports --
      ----------------   
      -- Board IDs Ports
      signal snIoAdcCard   : sl;
      signal snIoCarrier   : sl;
      -- QSFP Ports
      signal qsfpRxP       : slv(3 downto 0);
      signal qsfpRxN       : slv(3 downto 0);
      signal qsfpTxP       : slv(3 downto 0);
      signal qsfpTxN       : slv(3 downto 0);
      signal qsfpClkP      : sl := '1';
      signal qsfpClkN      : sl;
      signal qsfpLpMode    : sl;
      signal qsfpModSel    : sl;
      signal qsfpInitL     : sl;
      signal qsfpRstL      : sl;
      signal qsfpPrstL     : sl;
      signal qsfpScl       : sl;
      signal qsfpSda       : sl;
      -- DDR Ports
      signal ddrClkP       : sl := '1';
      signal ddrClkN       : sl;
      signal ddrBg         : sl;
      signal ddrCkP        : sl;
      signal ddrCkN        : sl;
      signal ddrCke        : sl;
      signal ddrCsL        : sl;
      signal ddrOdt        : sl;
      signal ddrAct        : sl;
      signal ddrRstL       : sl;
      signal ddrA          : slv(16 downto 0);
      signal ddrBa         : slv(1 downto 0);
      signal ddrDm         : slv(3 downto 0);
      signal ddrDq         : slv(31 downto 0);
      signal ddrDqsP       : slv(3 downto 0);
      signal ddrDqsN       : slv(3 downto 0);
      signal ddrPg         : sl;
      signal ddrPwrEn      : sl;
      -- SYSMON Ports
      signal vPIn          : sl;
      signal vNIn          : sl;

  
  
  -----------------------------------------------------------------------------
  -- Signals to communicate among app and core
  -----------------------------------------------------------------------------
  -- System Clock and Reset
  signal sysClk          : sl;
  signal sysRst          : sl;
  signal sysRst_n        : sl;
  -- AXI-Lite Register Interface (sysClk domain)
  signal axilReadMaster  : AxiLiteReadMasterType;
  signal axilReadSlave   : AxiLiteReadSlaveType;
  signal axilWriteMaster : AxiLiteWriteMasterType;
  signal axilWriteSlave  : AxiLiteWriteSlaveType;
  -- AXI Stream, one per QSFP lane (sysClk domain)
  signal axisMasters     : AxiStreamMasterArray(3 downto 0);
  signal axisSlaves      : AxiStreamSlaveArray(3 downto 0);
  -- Auxiliary AXI Stream, (sysClk domain)
  signal sAuxAxisMasters : AxiStreamMasterArray(1 downto 0);
  signal sAuxAxisSlaves  : AxiStreamSlaveArray(1 downto 0);
  -- ssi commands (Lane and Vc 0)
  signal ssiCmd          : SsiCmdMasterType;
  -- DDR's AXI Memory Interface (sysClk domain)
  signal axiReadMaster   : AxiReadMasterType;
  signal axiReadSlave    : AxiReadSlaveType;
  signal axiWriteMaster  : AxiWriteMasterType;
  signal axiWriteSlave   : AxiWriteSlaveType;
  -- Microblaze's Interrupt bus (sysClk domain)
  signal mbIrq           : slv(7 downto 0);

  -- encoder
  signal EncValidIn  : sl              := '1';
  signal EncReadyIn  : sl;
  signal EncDataIn   : slv(15 downto 0);
  signal EncDispIn   : slv(1 downto 0) := "00";
  signal EncDataKIn  : sl;
  signal EncValidOut : sl;
  signal EncReadyOut : sl              := '1';
  signal EncDataOut  : slv(19 downto 0);
  signal EncDataOutRev  : slv(19 downto 0);
  signal EncDataOut_d: Slv20Array(7 downto 0) := (others => (others => '0'));
  signal EncDispOut  : slv(1 downto 0);
  signal EncSof      : sl := '0';
  signal EncEof      : sl := '0';

  signal asicSimClk : sl;
  signal asicSimRst : sl;
  signal dClkP      : sl := '1'; -- Data clock
  signal dClkN      : sl := '0';
  signal fClkP      : sl := '0'; -- Frame clock
  signal fClkN      : sl := '1';
  signal dClkP2x    : sl := '1'; -- Data clock
  signal serData1_20b : slv(19 downto 0);
  signal serData1_10b : slv( 9 downto 0);
  signal serData2_20b : slv(19 downto 0);
  signal serData2_10b : slv( 9 downto 0);
  signal serialDataOut1  : sl;
  signal serialDataOut2  : sl;
  signal serialDataOut1d : slv(39 downto 0) := (others => '0');
  signal serialDataOut2d : slv(39 downto 0) := (others => '0');
  signal chId           : slv(15 downto 0);
  signal dummy : slv(2 downto 0);

begin  --
  sysRst_n   <= not sysRst;
  asicSR0 <= spareHrP(0);
  EncDataOutRev <= bitReverse(EncDataOut);
  asicSimRst <= not asicGlblRst;
  asicSimClk <= asicRoClkP(0);
  
  -- clock generation
  qsfpClkP  <= not qsfpClkP after 3.2 ns;
  qsfpClkN  <= not qsfpClkP;
  ddrClkP  <= not ddrCkP after 3.2 ns;
  ddrClkN  <= not ddrCkP;
  fClkN <= not fClkP;
  dClkN <= not dClkP;

  ----------------------------------------------
  -- Generate clocks for ASIC emulation model --
  ----------------------------------------------
  -- clkIn     : 320 MHz 
  -- clkOut(0) : 320 MHz 
  -- clkOut(1) :  32 MHz 
  -- clkOut(2) : 640 MHz 


  U_TB_ClockGen : entity surf.ClockManagerUltraScale 
    generic map(
      TPD_G                  => 1 ns,
      TYPE_G                 => "MMCM",  -- or "PLL"
      INPUT_BUFG_G           => true,
      FB_BUFG_G              => true,
      RST_IN_POLARITY_G      => '1',     -- '0' for active low
      NUM_CLOCKS_G           => 3,
      -- MMCM attributes
      BANDWIDTH_G            => "OPTIMIZED",
      CLKIN_PERIOD_G         => 3.125,    -- Input period in ns );
      DIVCLK_DIVIDE_G        => 4,
      CLKFBOUT_MULT_F_G      => 16.0,
      CLKFBOUT_MULT_G        => 16,
      CLKOUT0_DIVIDE_F_G     => 1.0,
      CLKOUT0_DIVIDE_G       => 4,
      CLKOUT0_PHASE_G        => 0.0,
      CLKOUT0_DUTY_CYCLE_G   => 0.5,
      CLKOUT0_RST_HOLD_G     => 3,
      CLKOUT0_RST_POLARITY_G => '1',
      CLKOUT1_DIVIDE_G       => 40,
      CLKOUT1_PHASE_G        => 0.0,
      CLKOUT1_DUTY_CYCLE_G   => 0.5,
      CLKOUT1_RST_HOLD_G     => 3,
      CLKOUT1_RST_POLARITY_G => '1',
      CLKOUT2_DIVIDE_G       => 2,
      CLKOUT2_PHASE_G        => 0.0,
      CLKOUT2_DUTY_CYCLE_G   => 0.5,
      CLKOUT2_RST_HOLD_G     => 3,
      CLKOUT2_RST_POLARITY_G => '1')
   port map(
      clkIn           => asicSimClk, --56MHz
      rstIn           => asicSimRst,
      clkOut(0)       => dClkP,       --bit clk
      clkOut(1)       => fClkP,
      clkOut(2)       => dClkP2x,
      rstOut(0)       => dummy(0),
      rstOut(1)       => dummy(1),
      rstOut(2)       => dummy(2),
      locked          => open
   );
  
  -- waveform generation
  WaveGen_Proc: process
    variable registerData    : slv(31 downto 0);  
  begin

    ---------------------------------------------------------------------------
    -- reset
    ---------------------------------------------------------------------------
    wait until sysClk = '1';
   
    wait;
  end process WaveGen_Proc;




-------------------------------------------------------------------------------
--  Starts transmitting data in the righ clock transition
-------------------------------------------------------------------------------  
  EncValid_Proc: process  
  begin
    wait until fClkP = '1';
    EncValidIn <= asicSR0;
  end process;  
  
-------------------------------------------------------------------------------
--  simulation process for channel ID. Counter from 0 to 31
-------------------------------------------------------------------------------  
  chId_Proc: process
    variable chIdCounter : integer := 0;
  begin
    wait until fClkP = '1';
    if asicSR0 = '1' then
      chIdCounter := ChIdCounter + 1;
      if chIdCounter = 32 then
        chIdCounter := 0;
      end if;
    else
      chIdCounter := 0;
    end if;
    chId <= toSlv(chIdCounter, 16);
  end process;  
-------------------------------------------------------------------------------
--  
-------------------------------------------------------------------------------
-------------------------------------------------------------------------------
  EncDataIn_Proc: process
    variable dataIndex : integer := 0;
  begin
    wait until fClkP = '1';
    if asicSR0 = '1' then
      if DATA_TYPE_C = CH_ID then
        EncDataIn <= chId;
      else
        EncDataIn <= ramWaveform(dataIndex);
      end if;
      dataIndex := dataIndex + 1;
      if dataIndex = DEPTH_C then
        dataIndex := 0;
      end if;
    else
      EncDataIn <= IDLE_PATTERN_C;
    end if;
    EncDataOut_d(0) <= EncDataOutRev;
    for i in 1 to 7 loop
      EncDataOut_d(i) <= EncDataOut_d(i-1);
    end loop;
  end process;

  U_encoder : entity surf.SspEncoder8b10b 
   generic map (
     TPD_G          => TPD_G,
     RST_POLARITY_G => '1',
     RST_ASYNC_G    => false,
     AUTO_FRAME_G   => true,
     FLOW_CTRL_EN_G => false)
   port map(
      clk      => fClkP,
      rst      => sysRst,
      validIn  => EncValidIn,
      readyIn  => EncReadyIn,
      sof      => EncSof,
      eof      => EncEof,
      dataIn   => EncDataIn,
      validOut => EncValidOut,
      readyOut => EncReadyOut,
      dataOut  => EncDataOut);

  serData1_20b <= EncDataOut_d(0);
  serData1_10b <= serData1_20b(19 downto 10) when fClkP = '1' else serData1_20b(9 downto 0);
  serData2_20b <= EncDataOut_d(7);
  serData2_10b <= serData2_20b(19 downto 10) when fClkP = '1' else serData2_20b(9 downto 0);
  
  U_serializer :  entity work.serializerSim 
    generic map(
      TPD_G    => 0ns,
      g_dwidth => 10 
    )
    port map(
        clk_i     => dClkP,
        reset_n_i => sysRst_n,
        data_i    => serData1_10b,        -- "00"&EncDataIn, --
        data_o    => serialDataOut1
    );


  U_serializer2 :  entity work.serializerSim 
    generic map(
      TPD_G    => 0ns,
      g_dwidth => 10 
    )
    port map(
        clk_i     => dClkP,
        reset_n_i => sysRst_n,
        data_i    => serData2_10b,        -- "00"&EncDataIn, --
        data_o    => serialDataOut2
    );

  DelaySerialData_Proc: process 
  begin
    wait until dClkP2x = '1';
    serialDataOut1d(0) <= serialDataOut1;
    for i in 1 to 39 loop
      serialDataOut1d(i) <= serialDataOut1d(i-1);
    end loop;

    serialDataOut2d(0) <= serialDataOut2;
    for i in 1 to 39 loop
      serialDataOut2d(i) <= serialDataOut2d(i-1);
    end loop;
  end process;

  asicDataWiring:  process(serialDataOut1, serialDataOut1d)
      variable i       : natural;
      variable retVarP : std_logic_vector(24-1 downto 0);
      variable retVarN : std_logic_vector(24-1 downto 0);
   begin
      for i in 0 to 24-1 loop
        retVarP(i) := serialDataOut2d(i);
        retVarN(i) := not serialDataOut2d(i);
      end loop;
      asicDataP <= retVarP;
      asicDataN <= retVarN;
   end process;    
  
 
  U_App : entity work.Application
      generic map (
         TPD_G => TPD_G,
         SIMULATION_G => true,
         BUILD_INFO_G => BUILD_INFO_G)
      port map (
         ----------------------
         -- Top Level Interface
         ----------------------
         -- System Clock and Reset
         sysClk           => sysClk,
         sysRst           => sysRst,
         -- AXI-Lite Register Interface (sysClk domain)
         -- Register Address Range = [0x80000000:0xFFFFFFFF]
         sAxilReadMaster  => axilReadMaster,
         sAxilReadSlave   => axilReadSlave,
         sAxilWriteMaster => axilWriteMaster,
         sAxilWriteSlave  => axilWriteSlave,
         -- AXI Stream, one per QSFP lane (sysClk domain)
         mAxisMasters     => axisMasters,
         mAxisSlaves      => axisSlaves,
         -- Auxiliary AXI Stream, (sysClk domain)
         sAuxAxisMasters  => sAuxAxisMasters,
         sAuxAxisSlaves   => sAuxAxisSlaves,
         ssiCmd           => ssiCmd,
         -- DDR's AXI Memory Interface (sysClk domain)
         -- DDR Address Range = [0x00000000:0x3FFFFFFF]
         mAxiReadMaster   => axiReadMaster,
         mAxiReadSlave    => axiReadSlave,
         mAxiWriteMaster  => axiWriteMaster,
         mAxiWriteSlave   => axiWriteSlave,
         -- Microblaze's Interrupt bus (sysClk domain)
         mbIrq            => mbIrq,
         -----------------------
         -- Application Ports --
         -----------------------
         -- System Ports
         digPwrEn         => digPwrEn,
         anaPwrEn         => anaPwrEn,
         syncDigDcDc      => syncDigDcDc,
         syncAnaDcDc      => syncAnaDcDc,
         syncDcDc         => syncDcDc,
         led              => open,
         daqTg            => daqTg,
         connTgOut        => connTgOut,
         connMps          => connMps,
         connRun          => connRun,
         -- Fast ADC Ports
         adcSpiClk        => adcSpiClk,
         adcSpiData       => adcSpiData,
         adcSpiCsL        => adcSpiCsL,
         adcPdwn          => adcPdwn,
         adcClkP          => adcClkP,
         adcClkM          => adcClkM,
         adcDoClkP        => adcDoClkP,
         adcDoClkM        => adcDoClkM,
         adcFrameClkP     => adcFrameClkP,
         adcFrameClkM     => adcFrameClkM,
         adcMonDoutP      => adcMonDoutP,
         adcMonDoutN      => adcMonDoutN,
         -- Slow ADC
         slowAdcSclk      => slowAdcSclk,
         slowAdcDin       => slowAdcDin,
         slowAdcCsL       => slowAdcCsL,
         slowAdcRefClk    => slowAdcRefClk,
         slowAdcDout      => slowAdcDout,
         slowAdcDrdy      => slowAdcDrdy,
         slowAdcSync      => slowAdcSync,
         -- Slow DACs Port         
         sDacCsL          => sDacCsL,
         hsDacCsL         => hsDacCsL,
         hsDacLoad        => hsDacLoad,
         dacClrL          => dacClrL,
         dacSck           => dacSck,
         dacDin           => dacDin,
         -- ASIC Gbps Ports
         asicDataP        => asicDataP,
         asicDataN        => asicDataN,
         -- ASIC Control Ports
         asicR0           => asicR0,
         asicPpmat        => asicPpmat,
         asicGlblRst      => asicGlblRst,
         asicSync         => asicSync,
         asicAcq          => asicAcq,
         asicRoClkP       => asicRoClkP,
         asicRoClkN       => asicRoClkN,
         -- SACI Ports
         asicSaciCmd      => asicSaciCmd,
         asicSaciClk      => asicSaciClk,
         asicSaciSel      => asicSaciSel,
         asicSaciRsp      => asicSaciRsp,
         -- Spare Ports
         spareHpP         => spareHpP,
         spareHpN         => spareHpN,
         spareHrP         => spareHrP,
         spareHrN         => spareHrN,
         -- GTH Ports
         gtRxP            => gtRxP,
         gtRxN            => gtRxN,
         gtTxP            => gtTxP,
         gtTxN            => gtTxN,
         gtRefP           => gtRefP,
         gtRefN           => gtRefN,
         smaRxP           => smaRxP,
         smaRxN           => smaRxN,
         smaTxP           => smaTxP,
         smaTxN           => smaTxN);

  U_Core : entity epix_hr_core.EpixHrCore
      generic map (
         TPD_G                => TPD_G,
         BUILD_INFO_G         => BUILD_INFO_G,
         ROGUE_SIM_EN_G       => true,
         ROGUE_SIM_PORT_NUM_G => 13000
      )
      port map (
         ----------------------
         -- Top Level Interface
         ----------------------
         -- System Clock and Reset
         sysClk           => sysClk,
         sysRst           => sysRst,
         -- AXI-Lite Register Interface (sysClk domain)
         -- Register Address Range = [0x80000000:0xFFFFFFFF]
         mAxilReadMaster  => axilReadMaster,
         mAxilReadSlave   => axilReadSlave,
         mAxilWriteMaster => axilWriteMaster,
         mAxilWriteSlave  => axilWriteSlave,
         -- AXI Stream, one per QSFP lane (sysClk domain)
         sAxisMasters     => axisMasters,
         sAxisSlaves      => axisSlaves,
         -- Auxiliary AXI Stream, (sysClk domain)
         sAuxAxisMasters  => sAuxAxisMasters,
         sAuxAxisSlaves   => sAuxAxisSlaves,
         ssiCmd           => ssiCmd,
         -- DDR's AXI Memory Interface (sysClk domain)
         -- DDR Address Range = [0x00000000:0x3FFFFFFF]
         sAxiReadMaster   => axiReadMaster,
         sAxiReadSlave    => axiReadSlave,
         sAxiWriteMaster  => axiWriteMaster,
         sAxiWriteSlave   => axiWriteSlave,
         -- Microblaze's Interrupt bus (sysClk domain)
         mbIrq            => mbIrq,
         ----------------
         -- Core Ports --
         ----------------   
         -- Board IDs Ports
         snIoAdcCard      => snIoAdcCard,
         -- QSFP Ports
         qsfpRxP          => qsfpRxP,
         qsfpRxN          => qsfpRxN,
         qsfpTxP          => qsfpTxP,
         qsfpTxN          => qsfpTxN,
         qsfpClkP         => qsfpClkP,
         qsfpClkN         => qsfpClkN,
         qsfpLpMode       => qsfpLpMode,
         qsfpModSel       => qsfpModSel,
         qsfpInitL        => qsfpInitL,
         qsfpRstL         => qsfpRstL,
         qsfpPrstL        => qsfpPrstL,
         qsfpScl          => qsfpScl,
         qsfpSda          => qsfpSda,
         -- DDR Ports
         ddrClkP          => ddrClkP,
         ddrClkN          => ddrClkN,
         ddrBg            => ddrBg,
         ddrCkP           => ddrCkP,
         ddrCkN           => ddrCkN,
         ddrCke           => ddrCke,
         ddrCsL           => ddrCsL,
         ddrOdt           => ddrOdt,
         ddrAct           => ddrAct,
         ddrRstL          => ddrRstL,
         ddrA             => ddrA,
         ddrBa            => ddrBa,
         ddrDm            => ddrDm,
         ddrDq            => ddrDq,
         ddrDqsP          => ddrDqsP,
         ddrDqsN          => ddrDqsN,
         ddrPg            => ddrPg,
         ddrPwrEn         => ddrPwrEn,
         -- SYSMON Ports
         vPIn             => vPIn,
         vNIn             => vNIn);  

end arch;

