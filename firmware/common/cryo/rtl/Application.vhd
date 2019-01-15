-------------------------------------------------------------------------------
-- File       : Application.vhd
-- Company    : SLAC National Accelerator Laboratory
-- Created    : 2017-04-21
-- Last update: 2019-01-15
-------------------------------------------------------------------------------
-- Description: Application Core's Top Level
-------------------------------------------------------------------------------
-- This file is part of 'EPIX HR Firmware'.
-- It is subject to the license terms in the LICENSE.txt file found in the 
-- top-level directory of this distribution and at: 
--    https://confluence.slac.stanford.edu/display/ppareg/LICENSE.html. 
-- No part of 'EPIX HR Firmware', including this file, 
-- may be copied, modified, propagated, or distributed except according to 
-- the terms contained in the LICENSE.txt file.
------------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;
use ieee.std_logic_unsigned.all;
use ieee.std_logic_arith.all;
use ieee.numeric_std.all;

use work.StdRtlPkg.all;
use work.AxiStreamPkg.all;
use work.EpixHrCorePkg.all;
use work.AxiLitePkg.all;
use work.AxiPkg.all;
use work.Pgp2bPkg.all;
use work.SsiPkg.all;
use work.SsiCmdMasterPkg.all;
use work.Ad9249Pkg.all;
use work.Code8b10bPkg.all;
use work.HrAdcPkg.all;

use work.AppPkg.all;

library unisim;
use unisim.vcomponents.all;

entity Application is
   generic (
      TPD_G            : time            := 1 ns;
      APP_CONFIG_G     : AppConfigType   := APP_CONFIG_INIT_C;
      SIMULATION_G     : boolean         := false;
      BUILD_INFO_G     : BuildInfoType;
      AXI_ERROR_RESP_G : slv(1 downto 0) := AXI_RESP_SLVERR_C;
      IODELAY_GROUP_G   : string          := "DEFAULT_GROUP");
   port (
      ----------------------
      -- Top Level Interface
      ----------------------
      -- System Clock and Reset
      sysClk           : in    sl;
      sysRst           : in    sl;
      -- AXI-Lite Register Interface (sysClk domain)
      -- Register Address Range = [0x80000000:0xFFFFFFFF]
      sAxilReadMaster  : in    AxiLiteReadMasterType;
      sAxilReadSlave   : out   AxiLiteReadSlaveType;
      sAxilWriteMaster : in    AxiLiteWriteMasterType;
      sAxilWriteSlave  : out   AxiLiteWriteSlaveType;
      -- AXI Stream, one per QSFP lane (sysClk domain)
      mAxisMasters     : out   AxiStreamMasterArray(3 downto 0);
      mAxisSlaves      : in    AxiStreamSlaveArray(3 downto 0);
      -- Auxiliary AXI Stream, (sysClk domain)
      -- 0 is pseudo scope, 1 is slow adc monitoring
      sAuxAxisMasters  : out   AxiStreamMasterArray(1 downto 0);
      sAuxAxisSlaves   : in    AxiStreamSlaveArray(1 downto 0);
      -- DDR's AXI Memory Interface (sysClk domain)
      -- DDR Address Range = [0x00000000:0x3FFFFFFF]
      mAxiReadMaster   : out   AxiReadMasterType;
      mAxiReadSlave    : in    AxiReadSlaveType;
      mAxiWriteMaster  : out   AxiWriteMasterType;
      mAxiWriteSlave   : in    AxiWriteSlaveType;
      -- Microblaze's Interrupt bus (sysClk domain)
      mbIrq            : out   slv(7 downto 0);
      -----------------------
      -- Application Ports --
      -----------------------
      -- System Ports
      digPwrEn         : out   sl;
      anaPwrEn         : out   sl;
      syncDigDcDc      : out   sl;
      syncAnaDcDc      : out   sl;
      syncDcDc         : out   slv(6 downto 0);
      led              : out   slv(3 downto 0);
      daqTg            : in    sl;
      connTgOut        : out   sl;
      connMps          : out   sl;
      connRun          : in    sl;
      -- Fast ADC Ports
      adcSpiClk        : out   sl;
      adcSpiData       : inout sl;
      adcSpiCsL        : out   sl;
      adcPdwn          : out   sl;
      adcClkP          : out   sl;
      adcClkM          : out   sl;
      adcDoClkP        : in    sl;
      adcDoClkM        : in    sl;
      adcFrameClkP     : in    sl;
      adcFrameClkM     : in    sl;
      adcMonDoutP      : in    slv(4 downto 0);
      adcMonDoutN      : in    slv(4 downto 0);
      -- Slow ADC
      slowAdcSclk      : out   sl;
      slowAdcDin       : out   sl;
      slowAdcCsL       : out   sl;
      slowAdcRefClk    : out   sl;
      slowAdcDout      : in    sl;
      slowAdcDrdy      : in    sl;
      slowAdcSync      : out   sl;
      -- Slow DACs Port
      sDacCsL          : out   slv(4 downto 0);
      hsDacCsL         : out   sl;
      hsDacLoad        : out   sl;
      dacClrL          : out   sl;
      dacSck           : out   sl;
      dacDin           : out   sl;
      -- ASIC Gbps Ports
      asicDataP        : inout slv(23 downto 0);
      asicDataN        : inout slv(23 downto 0);
      -- ASIC Control Ports
      asicR0           : out   sl;
      asicPpmat        : out   sl;
      asicGlblRst      : out   sl;
      asicSync         : out   sl;
      asicAcq          : out   sl;
      asicRoClkP       : out   slv(3 downto 0);
      asicRoClkN       : out   slv(3 downto 0);
      -- SACI Ports
      asicSaciCmd      : out   sl;
      asicSaciClk      : out   sl;
      asicSaciSel      : out   slv(3 downto 0);
      asicSaciRsp      : in    sl;
      -- Spare Ports
      spareHpP         : inout slv(11 downto 0);
      spareHpN         : inout slv(11 downto 0);
      spareHrP         : inout slv(5 downto 0);
      spareHrN         : inout slv(5 downto 0);
      -- GTH Ports
      gtRxP            : in    sl;
      gtRxN            : in    sl;
      gtTxP            : out   sl;
      gtTxN            : out   sl;
      gtRefP           : in    sl;
      gtRefN           : in    sl;
      smaRxP           : in    sl;
      smaRxN           : in    sl;
      smaTxP           : out   sl;
      smaTxN           : out   sl);

end Application;

architecture mapping of Application is


   attribute keep : string;

   --heart beat signal
   signal heartBeat      : sl;
   
   -- prbs signals
   signal prbsBusy       : slv(NUMBER_OF_LANES_C-1 downto 0) := (others => '0');

   -- clock signals
   signal appClk         : sl;
   signal asicClk        : sl;
   signal byteClk        : sl;
   signal asicRdClk      : sl;
   signal idelayCtrlClk  : sl;
   signal appRst         : sl;
   signal axiRst         : sl;
   signal asicRst        : sl;
   signal byteClkRst     : sl;
   signal asicRdClkRst   : sl;
   signal idelayCtrlRst  : sl;
   signal idelayCtrlRst_i: sl;
   signal clkLocked      : sl;
     

   -- AXI-Lite Signals
   signal sAxiReadMaster  : AxiLiteReadMasterArray(HR_FD_NUM_AXI_SLAVE_SLOTS_C-1 downto 0);
   signal sAxiReadSlave   : AxiLiteReadSlaveArray(HR_FD_NUM_AXI_SLAVE_SLOTS_C-1 downto 0);
   signal sAxiWriteMaster : AxiLiteWriteMasterArray(HR_FD_NUM_AXI_SLAVE_SLOTS_C-1 downto 0);
   signal sAxiWriteSlave  : AxiLiteWriteSlaveArray(HR_FD_NUM_AXI_SLAVE_SLOTS_C-1 downto 0);
   -- AXI-Lite Signals
   signal mAxiWriteMasters : AxiLiteWriteMasterArray(HR_FD_NUM_AXI_MASTER_SLOTS_C-1 downto 0); 
   signal mAxiWriteSlaves  : AxiLiteWriteSlaveArray(HR_FD_NUM_AXI_MASTER_SLOTS_C-1 downto 0); 
   signal mAxiReadMasters  : AxiLiteReadMasterArray(HR_FD_NUM_AXI_MASTER_SLOTS_C-1 downto 0); 
   signal mAxiReadSlaves   : AxiLiteReadSlaveArray(HR_FD_NUM_AXI_MASTER_SLOTS_C-1 downto 0); 

   --constant AXI_STREAM_CONFIG_O_C : AxiStreamConfigType   := ssiAxiStreamConfig(4, TKEEP_COMP_C);
   signal imAxisMasters    : AxiStreamMasterArray(3 downto 0);
   signal mAxisMastersPRBS : AxiStreamMasterArray(3 downto 0);
   signal mAxisSlavesPRBS  : AxiStreamSlaveArray(3 downto 0);
   signal mAxisMastersASIC : AxiStreamMasterArray(3 downto 0);
   signal mAxisSlavesASIC  : AxiStreamSlaveArray(3 downto 0);

   -- Triggers and associated signals
   signal iDaqTrigger        : sl := '0';
   signal iRunTrigger        : sl := '0';
   signal opCode             : slv(7 downto 0);
   signal pgpOpCodeOneShot   : sl;
   signal acqStart           : sl;
   signal dataSend           : sl;
   signal saciPrepReadoutReq : sl;
   signal saciPrepReadoutAck : sl;
   signal pgpRxOut           : Pgp2bRxOutType;

   -- ASIC signals (placeholders)
   signal iAsicEnA             : sl;
   signal iAsicEnB             : sl;
   signal iAsicVid             : sl;
   signal iAsicSR0             : sl;
   signal iAsic01DM1           : sl;
   signal iAsic01DM2           : sl;
   signal iAsicPPbe            : sl;
   signal iAsicPpmat           : sl;
   signal iAsicR0              : sl;
   signal iAsicSync            : sl;
   signal iAsicAcq             : sl;
   signal iAsicGrst            : sl;
   signal iSaciSelL            : slv(3 downto 0);
   signal iSaciClk             : sl;
   signal iSaciCmd             : sl;
   signal boardConfig          : AppConfigType;
   
   signal adcClk               : sl;
   signal errInhibit           : sl;


   -- HS DAC
   signal WFDacDin_i    : sl;
   signal WFDacSclk_i   : sl;
   signal WFDacCsL_i    : sl;
   signal WFDacLdacL_i  : sl;
   signal WFDacClrL_i   : sl;

   -- ADC signals
   signal adcValid         : slv(3 downto 0);
   signal adcData          : Slv16Array(3 downto 0);
   signal adcStreams       : AxiStreamMasterArray(3 downto 0) := (others=>AXI_STREAM_MASTER_INIT_C);
   signal monAdc           : Ad9249SerialGroupType;
   signal adcSpiCsL_i      : slv(1 downto 0);
   signal adcPdwn_i        : slv(0 downto 0);
   signal idelayRdy        : sl;

   -- Power up reset to SERDES block (Monitoring ADC)
   signal adcCardPowerUp     : sl;
   signal adcCardPowerUpEdge : sl;
   signal serdesReset        : sl;

   -- Power signals
   signal digPwrEn_i         : sl;
   signal anaPwrEn_i         : sl;   
   
   -- slow DACs
   signal sDacDin_i    : sl;
   signal sDacSclk_i   : sl;
   signal sDacCsL_i    : slv(4 downto 0);
   signal sDacClrb_i   : sl;


   -- Command interface
   signal ssiCmd               : SsiCmdMasterType;
   
   -- External Signals 
   signal serialIdIo           : slv(1 downto 0) := "00";

   -- DDR signals
   signal startDdrTest_n       : sl;
   -- DDR sconstants
   constant DDR_AXI_CONFIG_C : AxiConfigType := axiConfig(
      ADDR_WIDTH_C => 15,
      DATA_BYTES_C => 32,
      ID_BITS_C    => 4,
      LEN_BITS_C   => 8);

   constant START_ADDR_C : slv(DDR_AXI_CONFIG_C.ADDR_WIDTH_C-1 downto 0) := (others => '0');
   constant STOP_ADDR_C  : slv(DDR_AXI_CONFIG_C.ADDR_WIDTH_C-1 downto 0) := (others => '1');

   -- Equalizer signals
   signal EqualizerLosIn : slv(5 downto 0);
   -- Programmable power supply signals
   signal enableLDOOut        : slv(1 downto 0);
   signal dacSclkProgSupplyOut: sl;
   signal dacDinProgSupplyOut : sl;
   signal dacCsbProgSupplyOut : slv(1 downto 0);
   signal dacClrbProgSupplyOut: sl;
   -- CJC
   signal cjcRst            : slv(1 downto 0);
   signal cjcDec            : slv(1 downto 0);
   signal cjcInc            : slv(1 downto 0);
   signal cjcFrqtbl         : slv(1 downto 0);
   signal cjcRate           : slv(3 downto 0);
   signal cjcBwSel          : slv(3 downto 0);
   signal cjcFrqSel         : slv(7 downto 0);
   signal cjcSfout          : slv(3 downto 0);
   signal cjcLos            : sl;
   signal cjcLol            : sl;

   -- ASIC signals
   constant STREAMS_PER_ASIC_C : natural := 2;
   --
   signal adcSerial         : HrAdcSerialGroupArray(NUMBER_OF_ASICS_C-1 downto 0);
   signal asicStreams       : AxiStreamMasterArray(STREAMS_PER_ASIC_C-1 downto 0) := (others=>AXI_STREAM_MASTER_INIT_C);   

   attribute keep of appClk            : signal is "true";
   attribute keep of asicRdClk         : signal is "true";
   attribute keep of startDdrTest_n    : signal is "true";
   attribute keep of iAsicAcq          : signal is "true";

   attribute keep of adcStreams        : signal is "true";


begin

  -----------------------------------------------------------------------------
  -- remaps data lines into adapter board control/status lines
  -----------------------------------------------------------------------------
  -----------------------------------------------------------------------------
  -- Programmable power supply IOBUF & MAPPING
  -----------------------------------------------------------------------------
  IOBUF_DATAP_19 : IOBUF port map (O => open, I => enableLDOOut(0), IO => asicDataP(19), T => '0');
  --
  IOBUF_DATAN_19 : IOBUF port map (O => open, I => enableLDOOut(1), IO => asicDataN(19), T => '0');
  --
  IOBUF_SPARE_HPP_0 : IOBUF port map (O => open, I => dacDinProgSupplyOut,    IO => spareHpP(0), T => '0');
  IOBUF_SPARE_HPP_1 : IOBUF port map (O => open, I => dacSclkProgSupplyOut,   IO => spareHpP(1), T => '0');
  IOBUF_SPARE_HPP_2 : IOBUF port map (O => open, I => dacClrbProgSupplyOut,   IO => spareHpP(2), T => '0');
  --
  IOBUF_SPARE_HPN_0 : IOBUF port map (O => open, I => dacCsbProgSupplyOut(0), IO => spareHpN(0), T => '0');
  IOBUF_SPARE_HPN_1 : IOBUF port map (O => open, I => dacCsbProgSupplyOut(1), IO => spareHpN(1), T => '0');
  --
  -----------------------------------------------------------------------------
  -- Equalizer IOBUF & MAPPING
  -----------------------------------------------------------------------------
  -- EqualizerLosIn(5 downto 3) <= asicDataN(18 downto 16);
  -- EqualizerLosIn(2 downto 0) <= asicDataP(18 downto 16);
  --
  IOBUF_DATAP_16 : IOBUF port map (O => EqualizerLosIn(0), I => '0', IO => asicDataP(16), T => '1');
  IOBUF_DATAP_17 : IOBUF port map (O => EqualizerLosIn(1), I => '0', IO => asicDataP(17), T => '1');
  IOBUF_DATAP_18 : IOBUF port map (O => EqualizerLosIn(2), I => '0', IO => asicDataP(18), T => '1');
  --
  IOBUF_DATAN_16 : IOBUF port map (O => EqualizerLosIn(3), I => '0', IO => asicDataN(16), T => '1');
  IOBUF_DATAN_17 : IOBUF port map (O => EqualizerLosIn(4), I => '0', IO => asicDataN(17), T => '1');
  IOBUF_DATAN_18 : IOBUF port map (O => EqualizerLosIn(5), I => '0', IO => asicDataN(18), T => '1');

  -----------------------------------------------------------------------------
  -- Clock Jitter Cleaner IOBUF & MAPPING
  -----------------------------------------------------------------------------
  IOBUF_DATAP_1 : IOBUF port map (O => open,   I => cjcFrqtbl(0),    IO => asicDataP(1),  T => cjcFrqtbl(1));
  IOBUF_DATAP_7 : IOBUF port map (O => open,   I => cjcDec(0),       IO => asicDataP(7),  T => cjcDec(1));
  IOBUF_DATAP_8 : IOBUF port map (O => open,   I => cjcInc(0),       IO => asicDataP(8),  T => cjcInc(1));
  IOBUF_DATAP_9 : IOBUF port map (O => open,   I => cjcFrqSel(0), IO => asicDataP(9),  T => cjcFrqSel(4));
  IOBUF_DATAP_10: IOBUF port map (O => open,   I => cjcFrqSel(1), IO => asicDataP(10), T => cjcFrqSel(5));
  IOBUF_DATAP_11: IOBUF port map (O => open,   I => cjcFrqSel(2), IO => asicDataP(11), T => cjcFrqSel(6));
  IOBUF_DATAP_12: IOBUF port map (O => open,   I => cjcFrqSel(3), IO => asicDataP(12), T => cjcFrqSel(7));
  IOBUF_DATAP_13: IOBUF port map (O => cjcLos, I => '0',          IO => asicDataP(13), T => '1');
  --
  IOBUF_DATAN_1 : IOBUF port map (O => open,   I => cjcRst(0),       IO => asicDataN(1),  T => cjcRst(1));
  IOBUF_DATAN_7 : IOBUF port map (O => open,   I => cjcRate(0),   IO => asicDataN(7),  T => cjcRate(2));
  IOBUF_DATAN_8 : IOBUF port map (O => open,   I => cjcRate(1),   IO => asicDataN(8),  T => cjcRate(3));
  IOBUF_DATAN_9 : IOBUF port map (O => open,   I => cjcBwSel(0),  IO => asicDataN(9),  T => cjcBwSel(2));
  IOBUF_DATAN_10: IOBUF port map (O => open,   I => cjcBwSel(1),  IO => asicDataN(10), T => cjcBwSel(3));
  IOBUF_DATAN_11: IOBUF port map (O => open,   I => cjcSfout(0),  IO => asicDataN(11), T => cjcSfout(2));
  IOBUF_DATAN_12: IOBUF port map (O => open,   I => cjcSfout(1),  IO => asicDataN(12), T => cjcSfout(3));
  IOBUF_DATAN_13: IOBUF port map (O => cjcLol, I => '0',          IO => asicDataN(13), T => '1');

  OBUFDS_CLK     : OBUFDS port map (I  => asicRdClk,    O  => asicRoClkP(0),OB => asicRoClkN(0));
  
   ---------------------
   -- Heart beat LED  --
   ---------------------
   U_Heartbeat : entity work.Heartbeat
      generic map(
         PERIOD_IN_G => 10.0E-9
      )   
      port map (
         clk => sysClk,
         o   => heartBeat
      );
   
   ----------------------------------------------------------------------------
   -- Signal routing
   ----------------------------------------------------------------------------
   led(0)          <= clkLocked;
   led(1)          <= prbsBusy(0) or prbsBusy(1) or prbsBusy(2) or prbsBusy(3);
   led(2)          <= '0';
   led(3)          <= not heartBeat;
   

   ----------------------------------------------------------------------------
   -- axi stream routing
   ----------------------------------------------------------------------------
   mAxisMasters    <= imAxisMasters;
   --imAxisMasters(0) is connected to the stream mux directly

   ----------------------------------------------------------------------------
   -- power enable routing
   ----------------------------------------------------------------------------
   digPwrEn <= digPwrEn_i;
   anaPwrEn <= anaPwrEn_i;
   
   ----------------------------------------------------------------------------
   -- ADC routing
   ----------------------------------------------------------------------------
   adcSpiCsL       <= adcSpiCsL_i(0);
   adcPdwn         <= adcPdwn_i(0);
   slowAdcSync     <= '0';              -- not used, not connected to the ADC
                                        -- via no load resistor (R67)
   ----------------------------------------------------------------------------
   -- routing DAC signals to external IOs
   ----------------------------------------------------------------------------
   hsDacCsL        <= WFDacCsL_i;       -- DAC8812C chip select
   hsDacLoad       <= WFDacLdacL_i;     -- DAC8812C chip select
   sDacCsL         <= sDacCsL_i;        -- DACs to set static configuration
   -- shared DAC signal
   dacClrL         <= WFDacClrL_i when WFDacCsL_i = '0' else
                      sDacClrb_i;
   dacSck          <= WFDacSclk_i when WFDacCsL_i = '0' else
                      sDacSclk_i;
   dacDin          <= WFDacDin_i when WFDacCsL_i = '0' else
                      sDacDin_i;

   ----------------------------------------------------------------------------
   -- SACI signals
   ----------------------------------------------------------------------------
   asicSaciCmd     <= iSaciCmd;
   asicSaciClk     <= iSaciClk;
   asicSaciSel     <= iSaciSelL;
   iSaciSelL(3 downto 1) <=  (others => '1');

   ----------------------------------------------------------------------------
   -- Monitoring signals
   ----------------------------------------------------------------------------
   connTgOut <= 
      iAsic01DM1        when boardConfig.epixhrDbgSel1 = "00000" else
      iAsicSync         when boardConfig.epixhrDbgSel1 = "00001" else
      --iAsicStart        when boardConfig.epixhrDbgSel1 = "00010" else
      iAsicAcq          when boardConfig.epixhrDbgSel1 = "00011" else
      --iAsicTpulse       when boardConfig.epixhrDbgSel1 = "00100" else
      iAsicSR0          when boardConfig.epixhrDbgSel1 = "00101" else
      iSaciClk          when boardConfig.epixhrDbgSel1 = "00110" else
      iSaciCmd          when boardConfig.epixhrDbgSel1 = "00111" else
      asicSaciRsp       when boardConfig.epixhrDbgSel1 = "01000" else
      iSaciSelL(0)      when boardConfig.epixhrDbgSel1 = "01001" else
      iSaciSelL(1)      when boardConfig.epixhrDbgSel1 = "01010" else
      asicRdClk         when boardConfig.epixhrDbgSel1 = "01011" else
      --bitClk            when boardConfig.epixhrDbgSel1 = "01100" else
      byteClk           when boardConfig.epixhrDbgSel1 = "01101" else
      WFdacDin_i        when boardConfig.epixhrDbgSel1 = "01110" else
      WFdacSclk_i       when boardConfig.epixhrDbgSel1 = "01111" else
      WFdacCsL_i        when boardConfig.epixhrDbgSel1 = "10000" else
      WFdacLdacL_i      when boardConfig.epixhrDbgSel1 = "10001" else
      WFdacClrL_i       when boardConfig.epixhrDbgSel1 = "10010" else
      iAsicGrst         when boardConfig.epixhrDbgSel1 = "10011" else
      '0';   
   
   connMps <=
      iAsic01DM2        when boardConfig.epixhrDbgSel2 = "00000" else
      iAsicSync         when boardConfig.epixhrDbgSel2 = "00001" else
      --iAsicStart        when boardConfig.epixhrDbgSel2 = "00010" else
      iAsicAcq          when boardConfig.epixhrDbgSel2 = "00011" else
      --iAsicTpulse       when boardConfig.epixhrDbgSel2 = "00100" else
      iAsicSR0          when boardConfig.epixhrDbgSel2 = "00101" else
      iSaciClk          when boardConfig.epixhrDbgSel2 = "00110" else
      iSaciCmd          when boardConfig.epixhrDbgSel2 = "00111" else
      asicSaciRsp       when boardConfig.epixhrDbgSel2 = "01000" else
      iSaciSelL(0)      when boardConfig.epixhrDbgSel2 = "01001" else
      iSaciSelL(1)      when boardConfig.epixhrDbgSel2 = "01010" else
      asicRdClk         when boardConfig.epixhrDbgSel2 = "01011" else
      --bitClk            when boardConfig.epixhrDbgSel2 = "01100" else
      byteClk           when boardConfig.epixhrDbgSel2 = "01101" else
      WFdacDin_i        when boardConfig.epixhrDbgSel2 = "01110" else
      WFdacSclk_i       when boardConfig.epixhrDbgSel2 = "01111" else
      WFdacCsL_i        when boardConfig.epixhrDbgSel2 = "10000" else
      WFdacLdacL_i      when boardConfig.epixhrDbgSel2 = "10001" else
      WFdacClrL_i       when boardConfig.epixhrDbgSel2 = "10010" else
      iAsicGrst         when boardConfig.epixhrDbgSel1 = "10011" else
      '0';

   -----------------------------------------------------------------------------
   -- ASIC signal routing
   -----------------------------------------------------------------------------
   asicPpmat       <= iasicPpmat;
   asicGlblRst     <= iAsicGrst;
   asicSync        <= iasicSync;
   asicAcq         <= iasicAcq;

   -------------------------------------------------------------------------------
   -- unasigned signals
   ----------------------------------------------------------------------------
   mbIrq           <= (others => '0');  
   asicR0          <= '0';
   asicRoClkN(3 downto 1) <= (others => '0');
   asicRoClkP(3 downto 1) <= (others => '1');  
   gtTxP           <= '0';
   gtTxN           <= '1';
   smaTxP          <= '0';
   smaTxN          <= '1';
   asicDataN(4)    <= '0';
   asicDataN(6)    <= '0';
   asicDataN(15 downto 14)  <= (others => '0');
   asicDataN(23 downto 20)  <= (others => '0');
   asicDataP(4)    <= '0';
   asicDataP(6)    <= '0';
   asicDataP(15 downto 14)  <= (others => '0');
   asicDataP(23 downto 20)  <= (others => '0');

   ------------------------------------------
   -- Generate clocks from 156.25 MHz PGP  --
   ------------------------------------------
   -- clkIn     : 156.25 MHz PGP
   -- clkOut(0) : 100.00 MHz app clock
   -- clkOut(1) : 100.00 MHz asic clock
   -- clkOut(2) : 100.00 MHz asic clock
   -- clkOut(3) : 300.00 MHz idelay control clock
   -- clkOut(4) :  50.00 MHz monitoring adc
   U_CoreClockGen : entity work.ClockManagerUltraScale 
   generic map(
      TPD_G                  => 1 ns,
      TYPE_G                 => "MMCM",  -- or "PLL"
      INPUT_BUFG_G           => true,
      FB_BUFG_G              => true,
      RST_IN_POLARITY_G      => '1',     -- '0' for active low
      NUM_CLOCKS_G           => 5,
      -- MMCM attributes
      BANDWIDTH_G            => "OPTIMIZED",
      CLKIN_PERIOD_G         => 6.4,    -- Input period in ns );
      DIVCLK_DIVIDE_G        => 10,
      CLKFBOUT_MULT_F_G      => 38.4,
      CLKFBOUT_MULT_G        => 5,
      CLKOUT0_DIVIDE_F_G     => 1.0,
      CLKOUT0_DIVIDE_G       => 6,
      CLKOUT1_DIVIDE_G       => 6,
      CLKOUT2_DIVIDE_G       => 6,
      CLKOUT3_DIVIDE_G       => 2,
      CLKOUT4_DIVIDE_G       => 12,
      CLKOUT0_PHASE_G        => 0.0,
      CLKOUT1_PHASE_G        => 0.0,
      CLKOUT2_PHASE_G        => 0.0,
      CLKOUT3_PHASE_G        => 0.0,
      CLKOUT4_PHASE_G        => 0.0,
      CLKOUT0_DUTY_CYCLE_G   => 0.5,
      CLKOUT1_DUTY_CYCLE_G   => 0.5,
      CLKOUT2_DUTY_CYCLE_G   => 0.5,
      CLKOUT3_DUTY_CYCLE_G   => 0.5,
      CLKOUT4_DUTY_CYCLE_G   => 0.5,
      CLKOUT0_RST_HOLD_G     => 3,
      CLKOUT1_RST_HOLD_G     => 3,
      CLKOUT2_RST_HOLD_G     => 3,
      CLKOUT3_RST_HOLD_G     => 3,
      CLKOUT4_RST_HOLD_G     => 3,
      CLKOUT0_RST_POLARITY_G => '1',
      CLKOUT1_RST_POLARITY_G => '1',
      CLKOUT2_RST_POLARITY_G => '1',
      CLKOUT3_RST_POLARITY_G => '1',
      CLKOUT4_RST_POLARITY_G => '1')
   port map(
      clkIn           => sysClk,
      rstIn           => sysRst,
      clkOut(0)       => appClk,
      clkOut(1)       => asicClk,
      clkOut(2)       => asicRdClk,
      clkOut(3)       => idelayCtrlClk,
      clkOut(4)       => adcClk,
      rstOut(0)       => appRst,
      rstOut(1)       => asicRst,
      rstOut(2)       => asicRdClkRst,
      rstOut(3)       => open,
      rstOut(4)       => open,
      locked          => clkLocked,
      -- AXI-Lite Interface 
      axilClk         => appClk,
      axilRst         => appRst,
      axilReadMaster  => mAxiReadMasters(PLLREGS_AXI_INDEX_C),
      axilReadSlave   => mAxiReadSlaves(PLLREGS_AXI_INDEX_C),
      axilWriteMaster => mAxiWriteMasters(PLLREGS_AXI_INDEX_C),
      axilWriteSlave  => mAxiWriteSlaves(PLLREGS_AXI_INDEX_C)
   );      


   U_BUFGCE_DIV_0 : BUFGCE_DIV
   generic map (
      BUFGCE_DIVIDE => 5,     -- 1-8
      -- Programmable Inversion Attributes: Specifies built-in programmable inversion on specific pins
      IS_CE_INVERTED => '0',  -- Optional inversion for CE
      IS_CLR_INVERTED => '0', -- Optional inversion for CLR
      IS_I_INVERTED => '0'    -- Optional inversion for I
   )
   port map (
      O => byteClk,     -- 1-bit output: Buffer
      CE => '1',   -- 1-bit input: Buffer enable
      CLR => '0', -- 1-bit input: Asynchronous clear
      I => asicClk      -- 1-bit input: Buffer
   );

   U_RdPwrUpRst : entity work.PwrUpRst
   generic map (
      DURATION_G => 20000000
   )
   port map (
      clk      => byteClk,
      rstOut   => byteClkRst
   );

   idelayCtrlRst_i <= idelayCtrlRst;    --cmt_locked or
   U_IDELAYCTRL_0 : IDELAYCTRL
   generic map (
      SIM_DEVICE => "ULTRASCALE"  -- Must be set to "ULTRASCALE" 
   )
   port map (
      RDY => idelayRdy,        -- 1-bit output: Ready output
      REFCLK => idelayCtrlClk, -- 1-bit input: Reference clock input
      RST => idelayCtrlRst_i   -- 1-bit input: Active high reset input. Asynchronous assert, synchronous deassert to
                               -- REFCLK.
   );
   
   ---------------------------------------------
   -- AXI Lite Async - cross clock domain     --
   ---------------------------------------------
   U_AxiLiteAsync : entity work.AxiLiteAsync 
   generic map(
      TPD_G            => 1 ns,
      AXI_ERROR_RESP_G => AXI_RESP_SLVERR_C,
      COMMON_CLK_G     => false,
      NUM_ADDR_BITS_G  => 31,
      PIPE_STAGES_G    => 0)
   port map(
      -- Slave Port
      sAxiClk         => sysClk,
      sAxiClkRst      => sysRst,
      sAxiReadMaster  => sAxilReadMaster,
      sAxiReadSlave   => sAxilReadSlave,
      sAxiWriteMaster => sAxilWriteMaster,
      sAxiWriteSlave  => sAxilWriteSlave,
      -- Master Port
      mAxiClk         => appClk,
      mAxiClkRst      => appRst,
      mAxiReadMaster  => sAxiReadMaster(0),
      mAxiReadSlave   => sAxiReadSlave(0),
      mAxiWriteMaster => sAxiWriteMaster(0),
      mAxiWriteSlave  => sAxiWriteSlave(0)
    );


   ---------------------------------------------
   -- AXI Lite Crossbar for register control  --
   -- Check AppPkg.vhd for addresses          --
   ---------------------------------------------
   U_AxiLiteCrossbar : entity work.AxiLiteCrossbar
   generic map (
      NUM_SLAVE_SLOTS_G  => HR_FD_NUM_AXI_SLAVE_SLOTS_C,
      NUM_MASTER_SLOTS_G => HR_FD_NUM_AXI_MASTER_SLOTS_C, 
      MASTERS_CONFIG_G   => HR_FD_AXI_CROSSBAR_MASTERS_CONFIG_C
   )
   port map (                
      sAxiWriteMasters    => sAxiWriteMaster,
      sAxiWriteSlaves     => sAxiWriteSlave,
      sAxiReadMasters     => sAxiReadMaster,
      sAxiReadSlaves      => sAxiReadSlave,
      mAxiWriteMasters    => mAxiWriteMasters,
      mAxiWriteSlaves     => mAxiWriteSlaves,
      mAxiReadMasters     => mAxiReadMasters,
      mAxiReadSlaves      => mAxiReadSlaves,
      axiClk              => appClk,
      axiClkRst           => appRst
   );

  -----------------------------------------------------------------------------
  -- Regiester control
  -----------------------------------------------------------------------------
  U_RegControl : entity work.RegisterControl
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
      axiReadMaster  => mAxiReadMasters(APP_REG_AXI_INDEX_C),
      axiReadSlave   => mAxiReadSlaves(APP_REG_AXI_INDEX_C),
      axiWriteMaster => mAxiWriteMasters(APP_REG_AXI_INDEX_C),
      axiWriteSlave  => mAxiWriteSlaves(APP_REG_AXI_INDEX_C),
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
      errInhibit     => errInhibit
   );

   ---------------------
   -- Trig control    --
   --------------------- 
   U_TrigControl : entity work.TrigControlAxi
   port map (
      -- Trigger outputs
      sysClk         => appClk,
      sysRst         => appRst,
      acqStart       => acqStart,
      dataSend       => dataSend,
      
      -- External trigger inputs
      runTrigger     => iRunTrigger,
      daqTrigger     => iDaqTrigger,
      
      -- PGP clocks and reset
      pgpClk         => sysClk,
      pgpClkRst      => sysRst,
      -- SW trigger in (from VC)
      ssiCmd         => ssiCmd,
      -- PGP RxOutType (to trigger from sideband)
      pgpRxOut       => pgpRxOut,
      -- Opcode associated with this trigger
      opCodeOut      => opCode,
      
      -- AXI lite slave port for register access
      axilClk           => appClk,
      axilRst           => appRst,
      sAxilWriteMaster  => mAxiWriteMasters(TRIG_REG_AXI_INDEX_C),
      sAxilWriteSlave   => mAxiWriteSlaves(TRIG_REG_AXI_INDEX_C),
      sAxilReadMaster   => mAxiReadMasters(TRIG_REG_AXI_INDEX_C),
      sAxilReadSlave    => mAxiReadSlaves(TRIG_REG_AXI_INDEX_C)
   );

   --------------------------------------------
   -- SACI interface controller              --
   -------------------------------------------- 
   U_AxiLiteSaciMaster : entity work.AxiLiteSaciMaster
   generic map (
      AXIL_CLK_PERIOD_G  => 10.0E-9, -- In units of seconds
      AXIL_TIMEOUT_G     => 1.0E-3,  -- In units of seconds
      SACI_CLK_PERIOD_G  => 0.25E-6, -- In units of seconds
      SACI_CLK_FREERUN_G => false,
      SACI_RSP_BUSSED_G  => true,
      SACI_NUM_CHIPS_G   => NUMBER_OF_ASICS_C)
   port map (
      -- SACI interface
      saciClk           => iSaciClk,
      saciCmd           => iSaciCmd,
      saciSelL          => iSaciSelL(0 downto 0),
      saciRsp(0)        => asicSaciRsp,
      -- AXI-Lite Register Interface
      axilClk           => appClk,
      axilRst           => appRst,
      axilReadMaster    => mAxiReadMasters(SACIREGS_AXI_INDEX_C),
      axilReadSlave     => mAxiReadSlaves(SACIREGS_AXI_INDEX_C),
      axilWriteMaster   => mAxiWriteMasters(SACIREGS_AXI_INDEX_C),
      axilWriteSlave    => mAxiWriteSlaves(SACIREGS_AXI_INDEX_C)
   );

   --------------------------------------------
   -- Virtual oscilloscope                   --
   --------------------------------------------
   U_PseudoScope : entity work.PseudoScopeAxi
   generic map (
     TPD_G                      => TPD_G,
     MASTER_AXI_STREAM_CONFIG_G => ssiAxiStreamConfig(4, TKEEP_COMP_C)      
   )
   port map ( 
      
      sysClk         => sysClk,
      sysClkRst      => sysRst,
      adcData        => adcData,
      adcValid       => adcValid,
      arm            => acqStart,
      triggerIn(0)   => acqStart,
      triggerIn(1)   => iAsicAcq,
      triggerIn(2)   => iAsicSR0,
      triggerIn(3)   => iAsicPpmat,
      triggerIn(4)   => iAsicPpbe,
      triggerIn(5)   => iAsicSync,
      triggerIn(6)   => iAsicGrst,
      triggerIn(7)   => asicRdClk,
      triggerIn(11 downto 8)  => iSaciSelL,
      mAxisMaster    => sAuxAxisMasters(0),
      mAxisSlave     => sAuxAxisSlaves(0),
      -- AXI lite slave port for register access
      axilClk           => appClk,
      axilRst           => appRst,
      sAxilWriteMaster  => mAxiWriteMasters(SCOPE_REG_AXI_INDEX_C),
      sAxilWriteSlave   => mAxiWriteSlaves(SCOPE_REG_AXI_INDEX_C),
      sAxilReadMaster   => mAxiReadMasters(SCOPE_REG_AXI_INDEX_C),
      sAxilReadSlave    => mAxiReadSlaves(SCOPE_REG_AXI_INDEX_C)

   );

   --------------------------------------------
   -- Fast ADC for Virtual oscilloscope      --
   --------------------------------------------
   -- ADC Clock outputs
   U_AdcClk2 : OBUFDS port map ( I => adcClk, O => adcClkP, OB => adcClkM );
   
   GenAdcStr : for i in 0 to 3 generate 
      adcData(i)  <= adcStreams(i).tData(15 downto 0);
      adcValid(i) <= adcStreams(i).tValid;
   end generate;

   monAdc.fClkP <= adcFrameClkP;
   monAdc.fClkN <= adcFrameClkM;
   monAdc.dClkP <= adcDoClkP;
   monAdc.dClkN <= adcDoClkM;
   monAdc.chP(3 downto 0)   <= adcMonDoutP(3 downto 0);
   monAdc.chN(3 downto 0)   <= adcMonDoutN(3 downto 0);
      
   U_MonAdcReadout : entity work.Ad9249ReadoutGroup
   generic map (
      TPD_G             => TPD_G,
      NUM_CHANNELS_G    => 4,
      IODELAY_GROUP_G   => IODELAY_GROUP_G,
      IDELAYCTRL_FREQ_G => 200.0,
      DEFAULT_DELAY_G   => (others => '0'),
      ADC_INVERT_CH_G   => "00000010"
   )
   port map (
      -- Master system clock, 100Mhz
      axilClk           => appClk,
      axilRst           => appRst,
      
      -- Axi Interface
      axilReadMaster    => mAxiReadMasters(ADC_RD_AXI_INDEX_C),
      axilReadSlave     => mAxiReadSlaves(ADC_RD_AXI_INDEX_C),
      axilWriteMaster   => mAxiWriteMasters(ADC_RD_AXI_INDEX_C),
      axilWriteSlave    => mAxiWriteSlaves(ADC_RD_AXI_INDEX_C),

      -- Reset for adc deserializer
      adcClkRst         => serdesReset,

      -- Serial Data from ADC
      adcSerial         => monAdc,

      -- Deserialized ADC Data
      adcStreamClk      => sysClk,
      adcStreams        => adcStreams
   );

   -- Give a special reset to the SERDES blocks when power
   -- is turned on to ADC card.
   adcCardPowerUp <= anaPwrEn_i and digPwrEn_i;
   U_AdcCardPowerUpRisingEdge : entity work.SynchronizerEdge
   generic map (
      TPD_G       => TPD_G)
   port map (
      clk         => appClk,
      dataIn      => adcCardPowerUp,
      risingEdge  => adcCardPowerUpEdge
   );
   U_AdcCardPowerUpReset : entity work.RstSync
   generic map (
      TPD_G           => TPD_G,
      RELEASE_DELAY_G => 50
   )
   port map (
      clk      => appClk,
      asyncRst => adcCardPowerUpEdge,
      syncRst  => serdesReset
   );

   U_IdelayCtrlReset : entity work.RstSync
   generic map (
      TPD_G           => TPD_G,
      RELEASE_DELAY_G => 250
   )
   port map (
      clk      => idelayCtrlClk,
      asyncRst => serdesReset,
      syncRst  => idelayCtrlRst
   );
   
   --------------------------------------------
   --     Fast ADC Config                    --
   --------------------------------------------
   U_AdcConf : entity work.Ad9249Config
   generic map (
      TPD_G             => TPD_G,
      AXIL_CLK_PERIOD_G => 10.0e-9,
      NUM_CHIPS_G       => 1
   )
   port map (
      axilClk           => appClk,
      axilRst           => appRst,
      
      axilReadMaster    => mAxiReadMasters(ADC_CFG_AXI_INDEX_C),
      axilReadSlave     => mAxiReadSlaves(ADC_CFG_AXI_INDEX_C),
      axilWriteMaster   => mAxiWriteMasters(ADC_CFG_AXI_INDEX_C),
      axilWriteSlave    => mAxiWriteSlaves(ADC_CFG_AXI_INDEX_C),

      adcPdwn           => adcPdwn_i,
      adcSclk           => adcSpiClk,
      adcSdio           => adcSpiData,
      adcCsb            => adcSpiCsL_i

      );
   
   --------------------------------------------
   --  Slow ADC Readout  (env. variables)    --
   -------------------------------------------- 
   U_AdcCntrl: entity work.SlowAdcCntrlAxi
   generic map (
      SYS_CLK_PERIOD_G  => 6.4E-9,	-- 100MHz
      ADC_CLK_PERIOD_G  => 200.0E-9,	-- 5MHz
      SPI_SCLK_PERIOD_G => 2.0E-6  	-- 500kHz
   )
   port map ( 
      -- Master system clock
      sysClk            => sysClk,
      sysClkRst         => sysRst,
      
      -- Trigger Control
      adcStart          => acqStart,
      
      -- AXI lite slave port for register access
      axilClk           => appClk,
      axilRst           => appRst,
      sAxilWriteMaster  => mAxiWriteMasters(MONADC_REG_AXI_INDEX_C),
      sAxilWriteSlave   => mAxiWriteSlaves(MONADC_REG_AXI_INDEX_C),
      sAxilReadMaster   => mAxiReadMasters(MONADC_REG_AXI_INDEX_C),
      sAxilReadSlave    => mAxiReadSlaves(MONADC_REG_AXI_INDEX_C),
      
      -- AXI stream output
      axisClk           => sysClk,
      axisRst           => sysRst,
      mAxisMaster       => sAuxAxisMasters(1),
      mAxisSlave        => sAuxAxisSlaves(1),

      -- ADC Control Signals
      adcRefClk         => slowAdcRefClk,
      adcDrdy           => slowAdcDrdy,
      adcSclk           => slowAdcSclk,
      adcDout           => slowAdcDout,
      adcCsL            => slowAdcCsL,
      adcDin            => slowAdcDin
   );
   

   ----------------------------------------------------------------------------
   -- Power control module instance
   ----------------------------------------------------------------------------
   U_PowerControlModule : entity work.PowerControlModule 
      generic map (
      TPD_G              => TPD_G
   )
   port map (
      -- Trigger outputs
      sysClk         => appClk,
      sysRst         => appRst,
      -- power control
      digPwrEn         => digPwrEn,
      anaPwrEn         => anaPwrEn,
      syncDigDcDc      => syncDigDcDc,
      syncAnaDcDc      => syncAnaDcDc,
      syncDcDc         => syncDcDc,
      
      -- AXI lite slave port for register access
      axilClk         => appClk,  
      axilRst         => appRst,   
      sAxilWriteMaster=> mAxiWriteMasters(POWER_MODULE_INDEX_C),
      sAxilWriteSlave => mAxiWriteSlaves(POWER_MODULE_INDEX_C),
      sAxilReadMaster => mAxiReadMasters(POWER_MODULE_INDEX_C),
      sAxilReadSlave  => mAxiReadSlaves(POWER_MODULE_INDEX_C)
   );


  --------------------------------------------
  -- High speed DAC (DAC8812)               --
  --------------------------------------------
  U_HSDAC: entity work.DacWaveformGenAxi
    generic map (
      TPD_G => TPD_G,
      NUM_SLAVE_SLOTS_G  => HR_FD_NUM_AXI_SLAVE_SLOTS_C,
      NUM_MASTER_SLOTS_G => HR_FD_NUM_AXI_MASTER_SLOTS_C,
      MASTERS_CONFIG_G   => ssiAxiStreamConfig(4, TKEEP_COMP_C)
   )
    port map (
      sysClk            => appClk,
      sysClkRst         => appRst,
      dacDin            => WFDacDin_i,
      dacSclk           => WFDacSclk_i,
      dacCsL            => WFDacCsL_i,
      dacLdacL          => WFDacLdacL_i,
      dacClrL           => WFDacClrL_i,
      externalTrigger   => acqStart,
      axilClk           => appClk,
      axilRst           => appRst,
      sAxilWriteMaster  => mAxiWriteMasters,
      sAxilWriteSlave   => mAxiWriteSlaves,
      sAxilReadMaster   => mAxiReadMasters,
      sAxilReadSlave    => mAxiReadSlaves);

  --------------------------------------------
  -- ePix HR analog board SPI DACs          --
  --------------------------------------------
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
      axiReadMaster  => mAxiReadMasters(DAC_MODULE_INDEX_C), 
      axiReadSlave   => mAxiReadSlaves(DAC_MODULE_INDEX_C),
      axiWriteMaster => mAxiWriteMasters(DAC_MODULE_INDEX_C),
      axiWriteSlave  => mAxiWriteSlaves(DAC_MODULE_INDEX_C),
      -- Guard ring DAC interfaces
      dacSclk        => sDacSclk_i,
      dacDin         => sDacDin_i,      
      dacCsb         => sDacCsL_i,
      dacClrb        => sDacClrb_i
   );


   --------------------------------------------
   --     PRBS LOOP                          --
   --------------------------------------------   
   G_PRBS : for i in 0 to NUMBER_OF_LANES_C-1 generate 
      -------------------------------------------------------
      -- ASIC AXI stream framers
      -------------------------------------------------------
      U_AXI_PRBS : entity work.SsiPrbsTx 
      generic map(         
         TPD_G                      => TPD_G,
         MASTER_AXI_PIPE_STAGES_G   => 1,
         PRBS_SEED_SIZE_G           => 128,
         MASTER_AXI_STREAM_CONFIG_G => COMM_AXIS_CONFIG_C)
      port map(
         -- Master Port (mAxisClk)
         mAxisClk        => sysClk,
         mAxisRst        => sysRst,
         mAxisMaster     => mAxisMastersPRBS(i),
         mAxisSlave      => mAxisSlavesPRBS(i),
         -- Trigger Signal (locClk domain)
         locClk          => appClk,
         locRst          => appRst,
         trig            => acqStart,
         packetLength    => X"FFFFFFFF",
         forceEofe       => '0',
         busy            => prbsBusy(i),
         tDest           => X"00",
         tId             => X"00",
         -- Optional: Axi-Lite Register Interface (locClk domain)
         axilReadMaster  => mAxiReadMasters(PRBS0_AXI_INDEX_C+i),
         axilReadSlave   => mAxiReadSlaves(PRBS0_AXI_INDEX_C+i),
         axilWriteMaster => mAxiWriteMasters(PRBS0_AXI_INDEX_C+i),
         axilWriteSlave  => mAxiWriteSlaves(PRBS0_AXI_INDEX_C+i));
      
      U_STREAM_MUX : entity work.AxiStreamMux 
        generic map(
          TPD_G                => TPD_G,
          NUM_SLAVES_G         => 2,
          PIPE_STAGES_G        => 0,
          TDEST_LOW_G          => 0,      -- LSB of updated tdest for INDEX
          ILEAVE_EN_G          => false,  -- Set to true if interleaving dests, arbitrate on gaps
          ILEAVE_ON_NOTVALID_G => false,  -- Rearbitrate when tValid drops on selected channel
          ILEAVE_REARB_G       => 0)  -- Max number of transactions between arbitrations, 0 = unlimited
        port map(
          -- Clock and reset
          axisClk      => sysClk,
          axisRst      => sysRst,
          -- Slaves
          sAxisMasters(0) => mAxisMastersPRBS(i),
          sAxisMasters(1) => mAxisMastersASIC(i),
          sAxisSlaves(0)  => mAxisSlavesPRBS(i),          
          sAxisSlaves(1)  => mAxisSlavesASIC(i),
          -- Master
          mAxisMaster  => imAxisMasters(i),
          mAxisSlave   => mAxisSlaves(i));
   end generate;


   adcSerial(0).fClkP  <= asicDataP(2);
   adcSerial(0).fClkN  <= asicDataN(2);
   adcSerial(0).dClkP  <= asicDataP(5);
   adcSerial(0).dClkN  <= asicDataN(5);
   adcSerial(0).chP(0) <= asicDataP(0);
   adcSerial(0).chN(0) <= asicDataN(0);
   adcSerial(0).chP(1) <= asicDataP(3);
   adcSerial(0).chN(1) <= asicDataN(3);
   --
   --adcSerial(1).fClkP  <= asicDataP(4);
   --adcSerial(1).fClkN  <= asicDataN(4);
   --adcSerial(1).dClkP  <= asicDataP(6);
   --adcSerial(1).dClkN  <= asicDataN(6);
   --adcSerial(1).chP(0) <= asicDataP(3);
   --adcSerial(1).chN(0) <= asicDataN(3);
   
   --------------------------------------------
   --     ASICS LOOP                         --
   --------------------------------------------   
   G_ASICS : for i in 0 to NUMBER_OF_ASICS_C-1 generate 
     -------------------------------------------------------
     -- ASIC AXI stream framers
     -------------------------------------------------------
     U_AXI_ASIC : entity work.HrAdcReadoutGroup
      generic map (
        TPD_G             => TPD_G,
        NUM_CHANNELS_G    => STREAMS_PER_ASIC_C,
        IODELAY_GROUP_G   => "DEFAULT_GROUP",
        XIL_DEVICE_G      => "ULTRASCALE",
        DEFAULT_DELAY_G   => (others => '0'),
        ADC_INVERT_CH_G   => "00000000")
      port map (
        -- Master system clock, 125Mhz
        axilClk => appClk,
        axilRst => appRst,

        -- Reset for adc deserializer
        adcClkRst => sysRst,

        -- Axi Interface
        axilWriteMaster => mAxiWriteMasters(CRYO_ASIC0_READOUT_AXI_INDEX_C+i),
        axilWriteSlave  => mAxiWriteSlaves(CRYO_ASIC0_READOUT_AXI_INDEX_C+i),
        axilReadMaster  => mAxiReadMasters(CRYO_ASIC0_READOUT_AXI_INDEX_C+i),
        axilReadSlave   => mAxiReadSlaves(CRYO_ASIC0_READOUT_AXI_INDEX_C+i),
 
        -- Serial Data from ADC
        adcSerial => adcSerial(i),

        -- Deserialized ADC Data
        adcStreamClk => byteClk,--fClkP,--sysClk,
        adcStreams   => asicStreams      
        );

     -------------------------------------------------------------------------------
     -- generate stream frames
     -------------------------------------------------------------------------------
     U_Framers : entity work.DigitalAsicStreamAxi 
       generic map(
         TPD_G               => TPD_G,
         VC_NO_G             => "0000",
         LANE_NO_G           => toSlv(i, 4),
         ASIC_NO_G           => toSlv(i, 3),
         STREAMS_PER_ASIC_G  => STREAMS_PER_ASIC_C,
         ASIC_DATA_G         => (64*16),
         ASIC_WIDTH_G        => 64,
         ASIC_DATA_PADDING_G => "LSB",
         AXIL_ERR_RESP_G     => AXI_RESP_DECERR_C
         )
       port map( 
         -- Deserialized data port
         rxClk             => byteClk, --asicRdClk, --fClkP,    --use frame clock
         rxRst             => byteClkRst,--asicRdClkRst,
         adcStreams        => asicStreams(STREAMS_PER_ASIC_C-1 downto 0),
      
         -- AXI lite slave port for register access
         axilClk           => appClk,
         axilRst           => appRst,
         sAxilWriteMaster  => mAxiWriteMasters(DIG_ASIC0_STREAM_AXI_INDEX_C+i),
         sAxilWriteSlave   => mAxiWriteSlaves(DIG_ASIC0_STREAM_AXI_INDEX_C+i),
         sAxilReadMaster   => mAxiReadMasters(DIG_ASIC0_STREAM_AXI_INDEX_C+i),
         sAxilReadSlave    => mAxiReadSlaves(DIG_ASIC0_STREAM_AXI_INDEX_C+i),
      
         -- AXI data stream output
         axisClk           => sysClk,
         axisRst           => sysRst,
         mAxisMaster       => mAxisMastersASIC(i),
         mAxisSlave        => mAxisSlavesASIC(i),
      
         -- acquisition number input to the header
         acqNo             => boardConfig.acqCnt,
      
         -- optional readout trigger for test mode
         testTrig          => acqStart,
         errInhibit        => errInhibit
         );       
   end generate;


   -------------------------------------------------------
   -- AXI stream monitoring                             --
   -------------------------------------------------------
   U_AxiSMonitor : entity work.AxiStreamMonAxiL 
   generic map(
      TPD_G           => 1 ns,
      COMMON_CLK_G    => false,  -- true if axisClk = statusClk
      AXIS_CLK_FREQ_G => 156.25E+6,  -- units of Hz
      AXIS_NUM_SLOTS_G=> 4,
      AXIS_CONFIG_G   => COMM_AXIS_CONFIG_C)
   port map(
      -- AXIS Stream Interface
      axisClk         => sysClk,
      axisRst         => sysRst,
      axisMaster      => imAxisMasters,
      axisSlave       => mAxisSlaves,
      -- AXI lite slave port for register access
      axilClk         => appClk,  
      axilRst         => appRst,   
      sAxilWriteMaster=> mAxiWriteMasters(AXI_STREAM_MON_INDEX_C),
      sAxilWriteSlave => mAxiWriteSlaves(AXI_STREAM_MON_INDEX_C),
      sAxilReadMaster => mAxiReadMasters(AXI_STREAM_MON_INDEX_C),
      sAxilReadSlave  => mAxiReadSlaves(AXI_STREAM_MON_INDEX_C)
   );


   --------------------------------------------
   -- DDR memory tester                      --
   --------------------------------------------
   -- in order to desable the mem tester, the followint two signasl need to be wired
   --   mAxiReadMaster  <= AXI_READ_MASTER_INIT_C;
   --   mAxiWriteMaster <= AXI_WRITE_MASTER_INIT_C;

   U_AxiMemTester : entity work.AxiMemTester
   generic map (
      TPD_G        => TPD_G,
      START_ADDR_G => START_ADDR_C,
      STOP_ADDR_G  => STOP_ADDR_C,
      AXI_CONFIG_G => DDR_AXI_CONFIG_C)
   port map (
      -- AXI-Lite Interface
      axilClk         => appClk,
      axilRst         => appRst,
      axilReadMaster  => mAxiReadMasters(DDR_MEM_INDEX_C),
      axilReadSlave   => mAxiReadSlaves(DDR_MEM_INDEX_C),
      axilWriteMaster => mAxiWriteMasters(DDR_MEM_INDEX_C),
      axilWriteSlave  => mAxiWriteSlaves(DDR_MEM_INDEX_C),
      memReady        => open,  -- status bits
      memError        => open, -- status bits
      -- DDR Memory Interface
      axiClk          => sysClk,
      axiRst          => sysRst,
      start           => not startDdrTest_n, -- input signal that starts the test 
      axiWriteMaster  => mAxiWriteMaster,
      axiWriteSlave   => mAxiWriteSlave,
      axiReadMaster   => mAxiReadMaster,
      axiReadSlave    => mAxiReadSlave
   );

   U_StartDdrTest : entity work.PwrUpRst
   generic map (
      DURATION_G => 10000000
   )
   port map (
      clk      => appClk,
      rstOut   => startDdrTest_n
   );

   --------------------------------------------
   -- Equalizer monitoring                   --
   --------------------------------------------
   U_EqualizerStatus : entity work.EqualizerModules
     generic map(
      TPD_G               => TPD_G,
      NUN_OF_EQUALIZER_IC => 6)
   port map(
      sysClk            => appClk,
      sysRst            => appRst,
      -- IO signals
      EqualizerLOS      => EqualizerLosIn,
      EqualizerLOSSynced=> open,
      -- AXI lite slave port for register access
      axilClk           => appClk,
      axilRst           => appRst,
      sAxilWriteMaster  => mAxiWriteMasters(EQUALIZER_REG_AXI_INDEX_C),
      sAxilWriteSlave   => mAxiWriteSlaves(EQUALIZER_REG_AXI_INDEX_C),
      sAxilReadMaster   => mAxiReadMasters(EQUALIZER_REG_AXI_INDEX_C),
      sAxilReadSlave    => mAxiReadSlaves(EQUALIZER_REG_AXI_INDEX_C)
   );

   --------------------------------------------
   -- Programmable power supply              --
   --------------------------------------------
   U_ProgPowerSup : entity work.ProgrammablePowerSupply 
     generic map(
       TPD_G         => TPD_G
       )
   port map(
      axiClk         => appClk,
      axiRst         => appRst,
      -- AXI-Lite Register Interface (axiClk domain)    
      axiReadMaster  => mAxiReadMasters(PROG_SUPPLY_REG_AXI_INDEX_C),
      axiReadSlave   => mAxiReadSlaves(PROG_SUPPLY_REG_AXI_INDEX_C),
      axiWriteMaster => mAxiWriteMasters(PROG_SUPPLY_REG_AXI_INDEX_C),
      axiWriteSlave  => mAxiWriteSlaves(PROG_SUPPLY_REG_AXI_INDEX_C),
      -- Static control IO interface
      enableLDO      => enableLDOOut, 
      -- DAC interfaces
      dacSclk        => dacSclkProgSupplyOut,
      dacDin         => dacDinProgSupplyOut,
      dacCsb         => dacCsbProgSupplyOut,
      dacClrb        => dacClrbProgSupplyOut
   );
   --------------------------------------------
   -- Clock Jitter Cleaner                   --
   --------------------------------------------
  U_CJC : entity work.ClockJitterCleaner
   generic map (
      TPD_G              => TPD_G
   )
   port map(
      sysClk            => appClk,
      sysRst            => appRst,
      -- CJC control
      cjcRst            => cjcRst,
      cjcDec            => cjcDec,
      cjcInc            => cjcInc,
      cjcFrqtbl         => cjcFrqtbl,
      cjcRate           => cjcRate,
      cjcBwSel          => cjcBwSel,
      cjcFrqSel         => cjcFrqSel,
      cjcSfout          => cjcSfout,
      -- CJC Status
      cjcLos            => cjcLos,
      cjcLol            => cjcLol,
      -- AXI lite slave port for register access
      axilClk           => appClk,
      axilRst           => appRst,
      sAxilWriteMaster  => mAxiWriteMasters(CLK_JIT_CLR_REG_AXI_INDEX_C),
      sAxilWriteSlave   => mAxiWriteSlaves(CLK_JIT_CLR_REG_AXI_INDEX_C),
      sAxilReadMaster   => mAxiReadMasters(CLK_JIT_CLR_REG_AXI_INDEX_C),
      sAxilReadSlave    => mAxiReadSlaves(CLK_JIT_CLR_REG_AXI_INDEX_C)
   );
  
end mapping;
