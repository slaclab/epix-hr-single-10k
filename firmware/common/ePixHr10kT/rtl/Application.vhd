-------------------------------------------------------------------------------
-- File       : Application.vhd
-- Company    : SLAC National Accelerator Laboratory
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

library surf;
use surf.StdRtlPkg.all;
use surf.AxiStreamPkg.all;
use surf.AxiLitePkg.all;
use surf.AxiPkg.all;
use surf.SsiPkg.all;
use surf.SsiCmdMasterPkg.all;
use surf.Ad9249Pkg.all;
use surf.Code8b10bPkg.all;

library epix_hr_core;
use epix_hr_core.EpixHrCorePkg.all;

--use work.HrAdcPkg.all;
use work.AppPkg.all;

library unisim;
use unisim.vcomponents.all;

entity Application is
   generic (
      TPD_G            : time            := 1 ns;
      APP_CONFIG_G     : AppConfigType   := APP_CONFIG_INIT_C;
      SIMULATION_G     : boolean         := false;
      PRBS_GEN_G       : boolean         := false;
      DDR_GEN_G        : boolean         := false;
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
      -- ssi commands (Lane 0 and Vc 1)
      ssiCmd           : in    SsiCmdMasterType;
      -- Trigger (sysClk domain)
      pgpTrigger       : in sl;
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
      asicDataP        : in slv(23 downto 0);
      asicDataN        : in slv(23 downto 0);
      -- ASIC Control Ports
      asicR0           : out   sl;
      asicPpmat        : out   sl;
      asicGlblRst      : out   sl;
      asicSync         : out   sl;
      asicAcq          : out   sl;
      asicRoClkP       : out   slv(3 downto 0);
      asicRoClkN       : out   slv(3 downto 0);
      asicDMSN         : inout sl;
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

   constant AXIL_ASIC_CONFIG_C : AxiLiteCrossbarMasterConfigArray(1 downto 0) := genAxiLiteConfig(2, (HR_FD_AXI_CROSSBAR_MASTERS_CONFIG_C(ASIC_READOUT_AXI_INDEX_C).baseAddr), 20, 16);
 
   -- prbs signals
   signal prbsBusy       : slv(NUMBER_OF_LANES_C-1 downto 0) := (others => '0');

   -- clock signals
   signal appClk         : sl;
   signal refClk         : sl;
   signal asicRdClk      : sl;

   signal appRst         : sl;
   signal refRst         : sl;
   signal asicRdClkRst   : sl;
   signal clkLocked      : sl;
   signal dummyRst       : slv(1 downto 0);
     

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
   -- AXI-Lite Signals (Asic xbar)
   signal axilAsicWriteMasters : AxiLiteWriteMasterArray(1 downto 0);
   signal axilAsicWriteSlaves  : AxiLiteWriteSlaveArray(1 downto 0);
   signal axilAsicReadMasters  : AxiLiteReadMasterArray(1 downto 0);
   signal axilAsicReadSlaves   : AxiLiteReadSlaveArray(1 downto 0);

   --constant AXI_STREAM_CONFIG_O_C : AxiStreamConfigType   := ssiAxiStreamConfig(4, TKEEP_COMP_C);
   signal imAxisMasters    : AxiStreamMasterArray(3 downto 0);
   signal mAxisMastersPRBS : AxiStreamMasterArray(3 downto 0);
   signal mAxisSlavesPRBS  : AxiStreamSlaveArray(3 downto 0);
   signal mAxisMastersASIC : AxiStreamMasterArray(3 downto 0);
   signal mAxisSlavesASIC  : AxiStreamSlaveArray(3 downto 0);

   -- Triggers and associated signals
   signal iDaqTrigger        : sl := '0';
   signal iRunTrigger        : sl := '0';
   signal connTgMux          : sl;
   signal connMpsMux         : sl;
   signal acqStart           : sl;
   signal dataSend           : sl;
   signal saciPrepReadoutReq : sl;
   signal saciPrepReadoutAck : sl;

   -- ASIC signals (placeholders)
   signal iAsicEnA             : sl;
   signal iAsicEnB             : sl;
   signal iAsicVid             : sl;
   signal iAsicSR0, oAsicSR0   : sl;
   signal iAsicClkSyncEn       : sl;
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

   signal slowAdcDin_i         : sl;  
   signal slowAdcRefClk_i      : sl;
   signal slowAdcCsL_i         : sl;
   signal slowAdcSclk_i        : sl;


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
   signal idelayRdy        : sl := '1';
   signal adcSerialOutP    : slv(NUMBER_OF_ASICS_C-1 downto 0);
   signal adcSerialOutN    : slv(NUMBER_OF_ASICS_C-1 downto 0);

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
   signal ssiCmd_i               : SsiCmdMasterType;
   
   -- External Signals 
   signal serialIdIo           : slv(1 downto 0) := "00";

   -- DDR signals
   signal startDdrTest_n       : sl;
   signal startDdrTest         : sl;
   -- DDR sconstants
   constant DDR_AXI_CONFIG_C : AxiConfigType := axiConfig(
      ADDR_WIDTH_C => 15,
      DATA_BYTES_C => 32,
      ID_BITS_C    => 4,
      LEN_BITS_C   => 8);

   constant START_ADDR_C : slv(DDR_AXI_CONFIG_C.ADDR_WIDTH_C-1 downto 0) := (others => '0');
   constant STOP_ADDR_C  : slv(DDR_AXI_CONFIG_C.ADDR_WIDTH_C-1 downto 0) := (others => '1');



   -- ASIC signals
   constant STREAMS_PER_ASIC_C : natural := 6;
   --
   --signal adcSerial         : HrAdcSerialGroupArray(NUMBER_OF_ASICS_C-1 downto 0);

   signal deserClk        : sl;
   signal deserRst        : sl;
   signal deserData       : Slv8Array(23 downto 0);
   signal dlyLoad         : slv(23 downto 0);
   signal dlyCfg          : Slv9Array(23 downto 0);
   
   signal rxLinkUp        : slv(23 downto 0);
   signal rxValid         : slv(23 downto 0);
   signal rxData          : Slv16Array(23 downto 0);
   signal rxSof           : slv(23 downto 0);
   signal rxEof           : slv(23 downto 0);
   signal rxEofe          : slv(23 downto 0);

   attribute keep of appClk            : signal is "true";
   attribute keep of asicRdClk         : signal is "true";
   attribute keep of iAsicAcq          : signal is "true";
   attribute keep of ssiCmd_i          : signal is "true";
   attribute keep of iDaqTrigger       : signal is "true";
   attribute keep of iRunTrigger       : signal is "true";
   attribute keep of connMpsMux        : signal is "true";
   attribute keep of connTgMux         : signal is "true";
   attribute keep of deserData         : signal is "true";
   attribute keep of rxLinkUp          : signal is "true";
   attribute keep of rxValid           : signal is "true";
   attribute keep of rxData            : signal is "true";
   attribute keep of rxSof             : signal is "true";
   attribute keep of rxEofe            : signal is "true";


begin

  -----------------------------------------------------------------------------
  -- remaps data lines into adapter board control/status lines
  -----------------------------------------------------------------------------
  --IOBUF_DM1      : IOBUF  port map (O  => iAsic01DM1,   I => '0',           IO => asicDMSN,    T => '1');
  iAsic01DM1 <= asicDMSN; -- this signal is shared with the SN form core, so it comes buffered already.
  IOBUF_DM2      : IOBUF  port map (O  => iAsic01DM2,   I => '0',           IO => spareHrN(0), T => '1');
  -----------------------------------------------------------------------------
  -- Differential asic signals IOBUF & MAPPING
  -----------------------------------------------------------------------------
  OBUFDS_CLK0 : entity surf.ClkOutBufDiff
  generic map(
    TPD_G         => TPD_G,
    XIL_DEVICE_G  => "ULTRASCALE"
    )
  port map(
    clkIn   => asicRdClk,
    clkOutP => asicRoClkP(0),
    clkOutN => asicRoClkN(0));

  OBUFDS_CLK1 : entity surf.ClkOutBufDiff
  generic map(
    TPD_G         => TPD_G,
    XIL_DEVICE_G  => "ULTRASCALE"
    )
  port map(
    clkIn   => asicRdClk,
    clkOutP => asicRoClkP(1),
    clkOutN => asicRoClkN(1));

  OBUFDS_CLK2 : entity surf.ClkOutBufDiff
  generic map(
    TPD_G         => TPD_G,
    XIL_DEVICE_G  => "ULTRASCALE"
    )
  port map(
    clkIn   => asicRdClk,
    clkOutP => asicRoClkP(2),
    clkOutN => asicRoClkN(2));

  OBUFDS_CLK3 : entity surf.ClkOutBufDiff
  generic map(
    TPD_G         => TPD_G,
    XIL_DEVICE_G  => "ULTRASCALE"
    )
  port map(
    clkIn   => asicRdClk,
    clkOutP => asicRoClkP(3),
    clkOutN => asicRoClkN(3)); 
  
   ----------------------------------------------------------------------------
   -- Signal routing
   ----------------------------------------------------------------------------  

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

  ----------------------------------------------------------------------------
   -- Trigger signals
   ----------------------------------------------------------------------------
   iDaqTrigger <= daqTg;
   iRunTrigger <= connRun;
   ssiCmd_i    <= ssiCmd;

   slowAdcDin    <= slowAdcDin_i;
   slowAdcRefClk <= slowAdcRefClk_i;
   slowAdcCsL    <= slowAdcCsL_i;
   slowAdcSclk   <= slowAdcSclk_i;
  
   ----------------------------------------------------------------------------
   -- Monitoring signals
   ----------------------------------------------------------------------------
   connTgOut <= not connTgMux;          -- required because the board has a
                                        -- inverter driver
   connTgMux <= 
      iAsic01DM1        when boardConfig.epixhrDbgSel1 = "00000" else
      iAsicSync         when boardConfig.epixhrDbgSel1 = "00001" else
      iAsicAcq          when boardConfig.epixhrDbgSel1 = "00010" else
      oAsicSR0          when boardConfig.epixhrDbgSel1 = "00011" else
      iSaciClk          when boardConfig.epixhrDbgSel1 = "00100" else
      iSaciCmd          when boardConfig.epixhrDbgSel1 = "00101" else
      asicSaciRsp       when boardConfig.epixhrDbgSel1 = "00110" else
      iSaciSelL(0)      when boardConfig.epixhrDbgSel1 = "00111" else
      iSaciSelL(1)      when boardConfig.epixhrDbgSel1 = "01000" else
      asicRdClk         when boardConfig.epixhrDbgSel1 = "01001" else
      deserClk          when boardConfig.epixhrDbgSel1 = "01010" else
      WFdacDin_i        when boardConfig.epixhrDbgSel1 = "01011" else
      WFdacSclk_i       when boardConfig.epixhrDbgSel1 = "01100" else
      WFdacCsL_i        when boardConfig.epixhrDbgSel1 = "01101" else
      WFdacLdacL_i      when boardConfig.epixhrDbgSel1 = "01110" else
      WFdacClrL_i       when boardConfig.epixhrDbgSel1 = "01111" else
      iAsicGrst         when boardConfig.epixhrDbgSel1 = "10000" else
      iAsicR0           when boardConfig.epixhrDbgSel1 = "10001" else   
      slowAdcDin_i      when boardConfig.epixhrDbgSel1 = "10010" else
      slowAdcDrdy       when boardConfig.epixhrDbgSel1 = "10011" else
      slowAdcDout       when boardConfig.epixhrDbgSel1 = "10100" else
      slowAdcRefClk_i   when boardConfig.epixhrDbgSel1 = "10101" else
      pgpTrigger        when boardConfig.epixhrDbgSel1 = "10110" else
      acqStart          when boardConfig.epixhrDbgSel1 = "10111" else
      '0';   

   connMps    <= not connMpsMux;        -- required because the board has a
                                        -- inverter driver
   connMpsMux <=
      iAsic01DM2        when boardConfig.epixhrDbgSel2 = "00000" else
      iAsicSync         when boardConfig.epixhrDbgSel2 = "00001" else
      iAsicAcq          when boardConfig.epixhrDbgSel2 = "00010" else
      oAsicSR0          when boardConfig.epixhrDbgSel2 = "00011" else
      iSaciClk          when boardConfig.epixhrDbgSel2 = "00100" else
      iSaciCmd          when boardConfig.epixhrDbgSel2 = "00101" else
      asicSaciRsp       when boardConfig.epixhrDbgSel2 = "00110" else
      iSaciSelL(0)      when boardConfig.epixhrDbgSel2 = "00111" else
      iSaciSelL(1)      when boardConfig.epixhrDbgSel2 = "01000" else
      asicRdClk         when boardConfig.epixhrDbgSel2 = "01001" else
      deserClk          when boardConfig.epixhrDbgSel2 = "01010" else
      WFdacDin_i        when boardConfig.epixhrDbgSel2 = "01011" else
      WFdacSclk_i       when boardConfig.epixhrDbgSel2 = "01100" else
      WFdacCsL_i        when boardConfig.epixhrDbgSel2 = "01101" else
      WFdacLdacL_i      when boardConfig.epixhrDbgSel2 = "01110" else
      WFdacClrL_i       when boardConfig.epixhrDbgSel2 = "01111" else
      iAsicGrst         when boardConfig.epixhrDbgSel2 = "10000" else
      iAsicR0           when boardConfig.epixhrDbgSel2 = "10001" else   
      slowAdcDin_i      when boardConfig.epixhrDbgSel2 = "10010" else
      slowAdcDrdy       when boardConfig.epixhrDbgSel2 = "10011" else
      slowAdcDout       when boardConfig.epixhrDbgSel2 = "10100" else
      slowAdcRefClk_i   when boardConfig.epixhrDbgSel2 = "10101" else
      pgpTrigger        when boardConfig.epixhrDbgSel1 = "10110" else
      acqStart          when boardConfig.epixhrDbgSel1 = "10111" else
      '0';

  smaTxP          <= '0';
  smaTxN          <= '0';

   -----------------------------------------------------------------------------
   -- ASIC signal routing
  -----------------------------------------------------------------------------
  AsicPpmatBuf: entity surf.OutputBufferReg
    generic map(
      TPD_G          => TPD_G,
      DIFF_PAIR_G    => false)
    port map(
      I  => iAsicPpmat,
      C  => asicRdClk,
      O  => asicPpmat);

  AsicGlblRstBuf: entity surf.OutputBufferReg
    generic map(
      TPD_G          => TPD_G,
      DIFF_PAIR_G    => false)
   port map(
      I  => iAsicGrst,
      C  => asicRdClk,
      O  => asicGlblRst);

  AsicSyncBuf: entity surf.OutputBufferReg
    generic map(
      TPD_G          => TPD_G,
      DIFF_PAIR_G    => false)
    port map(
      I  => iAsicSync,
      C  => asicRdClk,
      O  => asicSync);

  AsicAcqBuf: entity surf.OutputBufferReg
    generic map(
      TPD_G          => TPD_G,
      DIFF_PAIR_G    => false)
   port map(
      I  => iAsicAcq,
      C  => asicRdClk,
      O  => asicAcq);

  AsicR0Buf: entity surf.OutputBufferReg 
    generic map(
      TPD_G          => TPD_G,
      DIFF_PAIR_G    => false)
    port map(
      I  => iAsicR0,
      C  => asicRdClk,
      O  => asicR0);
   
  AsicSR0Buf: entity surf.OutputBufferReg
    generic map(
      TPD_G          => TPD_G,
      DIFF_PAIR_G    => false)
    port map(
      I  => oAsicSR0,
      C  => asicRdClk,
      O  => spareHrP(0));

  AsicClksyncEnaBuf: entity surf.OutputBufferReg
    generic map(
      TPD_G          => TPD_G,
      DIFF_PAIR_G    => false)
    port map(
      I  => iAsicClkSyncEn,
      C  => asicRdClk,
      O  => spareHrP(1));
   -------------------------------------------------------------------------------
   -- unasigned signals
   ----------------------------------------------------------------------------
   mbIrq           <= (others => '0');  
   gtTxP           <= '0';
   gtTxN           <= '1';

   Synchronizer_SR0 : entity surf.Synchronizer
     generic map (
       TPD_G    => TPD_G,
       STAGES_G => 2)
     port map (
       clk     => asicRdClk,
       rst     => asicRdClkRst,
       dataIn  => iAsicSR0,
       dataOut => oAsicSR0);


   ------------------------------------------
   -- Generate clocks from 156.25 MHz PGP  --
   ------------------------------------------
   -- clkIn     : 156.25 MHz PGP
   -- base clk is 1000 MHz
   -- clkOut(0) : 160.00 MHz ASIC ref clock
   -- clkOut(1) : 50.00  MHz adc clock
   -- clkOut(2) : 100.00 MHz app clock
   U_CoreClockGen : entity surf.ClockManagerUltraScale 
   generic map(
      TPD_G                  => 1 ns,
      TYPE_G                 => "MMCM",  -- or "PLL"
      INPUT_BUFG_G           => true,
      FB_BUFG_G              => true,
      RST_IN_POLARITY_G      => '1',     -- '0' for active low
      NUM_CLOCKS_G           => 3,
      SIMULATION_G           => SIMULATION_G,
      -- MMCM attributes
      BANDWIDTH_G            => "OPTIMIZED",
      CLKIN_PERIOD_G         => 6.4,    -- Input period in ns );
      DIVCLK_DIVIDE_G        => 5,        -- 1000 Base clk
      CLKFBOUT_MULT_F_G      => 32.0,     -- 1000 Base clk
      CLKFBOUT_MULT_G        => 5,
      CLKOUT0_DIVIDE_F_G     => 6.25,     -- 1000 Base clk
      CLKOUT0_DIVIDE_G       => 1,
      CLKOUT1_DIVIDE_G       => 20,       -- 1000 Base clk
      CLKOUT2_DIVIDE_G       => 10,       -- 1000 Base clk
      CLKOUT0_PHASE_G        => 0.0,
      CLKOUT1_PHASE_G        => 0.0,
      CLKOUT2_PHASE_G        => 0.0,
      CLKOUT0_DUTY_CYCLE_G   => 0.5,
      CLKOUT1_DUTY_CYCLE_G   => 0.5,
      CLKOUT2_DUTY_CYCLE_G   => 0.5,
      CLKOUT0_RST_HOLD_G     => 3,
      CLKOUT1_RST_HOLD_G     => 3,
      CLKOUT2_RST_HOLD_G     => 3,
      CLKOUT0_RST_POLARITY_G => '1',
      CLKOUT1_RST_POLARITY_G => '1',
      CLKOUT2_RST_POLARITY_G => '1')
   port map(
      clkIn           => sysClk,
      rstIn           => sysRst,
      clkOut(0)       => refClk,
      clkOut(1)       => adcClk,
      clkOut(2)       => appClk,
      rstOut(0)       => refRst,
      rstOut(1)       => dummyRst(0),
      rstOut(2)       => appRst,
      locked          => clkLocked,
      -- AXI-Lite Interface 
      axilClk         => appClk,
      axilRst         => appRst,
      axilReadMaster  => mAxiReadMasters(PLLREGS_AXI_INDEX_C),
      axilReadSlave   => mAxiReadSlaves(PLLREGS_AXI_INDEX_C),
      axilWriteMaster => mAxiWriteMasters(PLLREGS_AXI_INDEX_C),
      axilWriteSlave  => mAxiWriteSlaves(PLLREGS_AXI_INDEX_C)
   );      
  
   ---------------------------------------------
   -- AXI Lite Async - cross clock domain     --
   ---------------------------------------------
   U_AxiLiteAsync : entity surf.AxiLiteAsync 
   generic map(
      TPD_G            => 1 ns,
      AXI_ERROR_RESP_G => AXI_RESP_SLVERR_C,
      COMMON_CLK_G     => false,
      NUM_ADDR_BITS_G  => 32,
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
   U_AxiLiteCrossbar : entity surf.AxiLiteCrossbar
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

  U_ASIC_XBAR : entity surf.AxiLiteCrossbar
      generic map (
         TPD_G              => TPD_G,
         NUM_SLAVE_SLOTS_G  => 1,
         NUM_MASTER_SLOTS_G => 2,
         MASTERS_CONFIG_G   => AXIL_ASIC_CONFIG_C)
      port map (
         axiClk              => appClk,
         axiClkRst           => appRst,
         sAxiWriteMasters(0) => mAxiWriteMasters(ASIC_READOUT_AXI_INDEX_C),
         sAxiWriteSlaves(0)  => mAxiWriteSlaves(ASIC_READOUT_AXI_INDEX_C),
         sAxiReadMasters(0)  => mAxiReadMasters(ASIC_READOUT_AXI_INDEX_C),
         sAxiReadSlaves(0)   => mAxiReadSlaves(ASIC_READOUT_AXI_INDEX_C),
         mAxiWriteMasters    => axilAsicWriteMasters,
         mAxiWriteSlaves     => axilAsicWriteSlaves,
         mAxiReadMasters     => axilAsicReadMasters,
         mAxiReadSlaves      => axilAsicReadSlaves);

  -----------------------------------------------------------------------------
  -- Regiester control
  -----------------------------------------------------------------------------
  U_RegControl : entity work.RegisterControlDualClock
   generic map (
      TPD_G            => TPD_G,
      EN_DEVICE_DNA_G  => false,        -- this is causing placement errors,
                                        -- needs fixing.
      BUILD_INFO_G     => BUILD_INFO_G
   )
   port map (
      axilClk        => appClk,
      axilRst        => appRst,
      -- AXI-Lite Register Interface (axiClk domain)
      axiReadMaster  => mAxiReadMasters(APP_REG_AXI_INDEX_C),
      axiReadSlave   => mAxiReadSlaves(APP_REG_AXI_INDEX_C),
      axiWriteMaster => mAxiWriteMasters(APP_REG_AXI_INDEX_C),
      axiWriteSlave  => mAxiWriteSlaves(APP_REG_AXI_INDEX_C),
      -- Register Inputs/Outputs (axiClk domain)
      boardConfig    => boardConfig,
      -- 1-wire board ID interfaces
      serialIdIo     => serialIdIo,
      -- ASICs acquisition signals
      acqStart       => acqStart,
      asicR0         => iAsicR0,
      asicAcq        => iAsicAcq,
      asicPPbe       => iAsicPpbe,
      asicPpmat      => iAsicPpmat,
      saciReadoutReq => saciPrepReadoutReq,
      saciReadoutAck => saciPrepReadoutAck,
      errInhibit     => errInhibit,
      -- sys clock based signals
      sysRst         => refRst,
      sysClk         => refClk,
      asicSR0        => iAsicSR0,
      asicClkSyncEn  => iAsicClkSyncEn,
      asicGlblRst    => iAsicGrst,
      asicSync       => iAsicSync
   );

   ---------------------
   -- Trig control    --
   --------------------- 
   U_TrigControl : entity work.TrigControlAxi
   port map (
      -- Trigger outputs
      appClk         => appClk,
      appRst         => appRst,
      acqStart       => acqStart,
      dataSend       => dataSend,
      
      -- External trigger inputs
      runTrigger     => iRunTrigger,
      daqTrigger     => iDaqTrigger,
      
      -- PGP clocks and reset
      sysClk         => sysClk,
      sysRst         => sysRst,
      -- SW trigger in (from VC)
      ssiCmd         => ssiCmd_i,
      -- Fiber optic trigger (axilClk domain)
      pgpTrigger     => pgpTrigger,
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
   U_AxiLiteSaciMaster : entity surf.AxiLiteSaciMaster
   generic map (
      AXIL_CLK_PERIOD_G  => 10.0E-9, -- In units of seconds
      AXIL_TIMEOUT_G     => 1.0E-3,  -- In units of seconds
      SACI_CLK_PERIOD_G  => 1.00E-6, -- In units of seconds
      SACI_CLK_FREERUN_G => false,
      SACI_RSP_BUSSED_G  => true,
      SACI_NUM_CHIPS_G   => NUMBER_OF_ASICS_C)
   port map (
      -- SACI interface
      saciClk           => iSaciClk,
      saciCmd           => iSaciCmd,
      saciSelL          => iSaciSelL,
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
      triggerIn(4)   => pgpTrigger,
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
      
   U_MonAdcReadout : entity surf.Ad9249ReadoutGroup
   generic map (
      TPD_G             => TPD_G,
      NUM_CHANNELS_G    => 4,
      IODELAY_GROUP_G   => IODELAY_GROUP_G,
      IDELAYCTRL_FREQ_G => 250.0,
      DEFAULT_DELAY_G   => (others => '0'),
      ADC_INVERT_CH_G   => "00000010",
      USE_MMCME_G       => true
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
      adcClkRst         => '0',
      adcBitClkIn       => '0',
      adcBitClkDiv4In   => '0',
      adcBitRstIn       => '0',
      adcBitRstDiv4In   => '0',

      -- Serial Data from ADC
      adcSerial         => monAdc,

      -- Deserialized ADC Data
      adcStreamClk      => sysClk,
      adcStreams        => adcStreams
   );

   -- Give a special reset to the SERDES blocks when power
   -- is turned on to ADC card.
   adcCardPowerUp <= anaPwrEn_i and digPwrEn_i;
   U_AdcCardPowerUpRisingEdge : entity surf.SynchronizerEdge
   generic map (
      TPD_G       => TPD_G)
   port map (
      clk         => appClk,
      dataIn      => adcCardPowerUp,
      risingEdge  => adcCardPowerUpEdge
   );
   U_AdcCardPowerUpReset : entity surf.RstSync
   generic map (
      TPD_G           => TPD_G,
      RELEASE_DELAY_G => 50
   )
   port map (
      clk      => appClk,
      asyncRst => adcCardPowerUpEdge,
      syncRst  => serdesReset
   );
   
   --------------------------------------------
   --     Fast ADC Config                    --
   --------------------------------------------
   U_AdcConf : entity surf.Ad9249Config
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
      SYS_CLK_PERIOD_G  => 6.4E-9,	-- 156.25MHz
      ADC_CLK_PERIOD_G  => 200.0E-9,	-- 5MHz
      SPI_SCLK_PERIOD_G => 2.0E-6  	-- 500kHz
   )
   port map ( 
      -- Master system clock
      sysClk            => appClk,
      sysClkRst         => appRst,
      
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
      adcRefClk         => slowAdcRefClk_i,
      adcDrdy           => slowAdcDrdy,
      adcSclk           => slowAdcSclk_i,
      adcDout           => slowAdcDout,
      adcCsL            => slowAdcCsL_i,
      adcDin            => slowAdcDin_i
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
      sAxilWriteMaster  => mAxiWriteMasters(DACWFMEM_REG_AXI_INDEX_C downto DAC8812_REG_AXI_INDEX_C),
      sAxilWriteSlave   => mAxiWriteSlaves(DACWFMEM_REG_AXI_INDEX_C downto DAC8812_REG_AXI_INDEX_C),
      sAxilReadMaster   => mAxiReadMasters(DACWFMEM_REG_AXI_INDEX_C downto DAC8812_REG_AXI_INDEX_C),
      sAxilReadSlave    => mAxiReadSlaves(DACWFMEM_REG_AXI_INDEX_C downto DAC8812_REG_AXI_INDEX_C));

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
   --------------------------------------------
   PRBS_GEN : if (PRBS_GEN_G) generate
    G_PRBS : for i in 0 to NUMBER_OF_LANES_C-1 generate 
      -------------------------------------------------------
      -- ASIC AXI stream framers
      -------------------------------------------------------
      U_AXI_PRBS : entity surf.SsiPrbsTx 
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
      
      U_STREAM_MUX : entity surf.AxiStreamMux 
        generic map(
          TPD_G                => TPD_G,
          NUM_SLAVES_G         => 2,
          PIPE_STAGES_G        => 0,
          MODE_G               =>"ROUTED",
          TDEST_ROUTES_G       => (0=>x"01", 1=>x"00"),
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
    end generate;
    
    PRBS_NOT_GEN : if (not PRBS_GEN_G) generate
          -- route streams
          imAxisMasters   <= mAxisMastersASIC;
          mAxisSlavesASIC <= mAxisSlaves;
          -- init unused axiLite
          mAxiWriteSlaves(PRBS0_AXI_INDEX_C) <= axiLiteWriteSlaveEmptyInit(AXI_RESP_OK_C);
          mAxiWriteSlaves(PRBS1_AXI_INDEX_C) <= axiLiteWriteSlaveEmptyInit(AXI_RESP_OK_C);
          mAxiWriteSlaves(PRBS2_AXI_INDEX_C) <= axiLiteWriteSlaveEmptyInit(AXI_RESP_OK_C);
          mAxiWriteSlaves(PRBS3_AXI_INDEX_C) <= axiLiteWriteSlaveEmptyInit(AXI_RESP_OK_C);
          mAxiReadSlaves(PRBS0_AXI_INDEX_C)  <= axiLiteReadSlaveEmptyInit(AXI_RESP_OK_C);
          mAxiReadSlaves(PRBS1_AXI_INDEX_C)  <= axiLiteReadSlaveEmptyInit(AXI_RESP_OK_C);
          mAxiReadSlaves(PRBS2_AXI_INDEX_C)  <= axiLiteReadSlaveEmptyInit(AXI_RESP_OK_C);
          mAxiReadSlaves(PRBS3_AXI_INDEX_C)  <= axiLiteReadSlaveEmptyInit(AXI_RESP_OK_C);
    end generate;
  
   --

   -------------------------------------------------------
   -- ASIC Deserializers
   -------------------------------------------------------
   U_Deser : entity surf.SelectioDeserUltraScale
     generic map(
       TPD_G            => TPD_G,
       SIMULATION_G     => SIMULATION_G,
       NUM_LANE_G       => 24,
       CLKIN_PERIOD_G   => 6.25,  -- 160 MHz
       DIVCLK_DIVIDE_G  => 1,
       CLKFBOUT_MULT_G  => 4,     -- 640 MHz = 160 MHz x 4 / 1
       CLKOUT0_DIVIDE_G => 2      -- 320 MHz = 640 MHz/2
     )
     port map (
       -- SELECTIO Ports
       rxP             => asicDataP,
       rxN             => asicDataN,
       pllClk          => asicRdClk,
       -- Reference Clock and Reset
       refClk          => refClk,
       refRst          => refRst,
       -- Deserialization Interface (deserClk domain)
       deserClk        => deserClk ,
       deserRst        => deserRst ,
       deserData       => deserData,
       dlyLoad         => dlyLoad  ,
       dlyCfg          => dlyCfg   ,
       -- AXI-Lite Interface (axilClk domain)
       axilClk         => appClk,
       axilRst         => appRst,
       axilReadMaster  => axilAsicReadMasters(0),
       axilReadSlave   => axilAsicReadSlaves(0),
       axilWriteMaster => axilAsicWriteMasters(0),
       axilWriteSlave  => axilAsicWriteSlaves(0)
     );
   
   -------------------------------------------------------
   -- ASIC Gearboxes and SSP decoders
   -------------------------------------------------------
   U_SspDecoder : entity surf.SspLowSpeedDecoder8b10bWrapper
     generic map (
       TPD_G        => TPD_G,
       SIMULATION_G => SIMULATION_G,
       NUM_LANE_G   => 24
     )
     port map (
       -- Deserialization Interface (deserClk domain)
       deserClk        => deserClk ,
       deserRst        => deserRst ,
       deserData       => deserData,
       dlyLoad         => dlyLoad  ,
       dlyCfg          => dlyCfg   ,
       -- SSP Frame Output
       rxLinkUp        => rxLinkUp,
       rxValid         => rxValid ,
       rxData          => rxData  ,
       rxSof           => rxSof   ,
       rxEof           => rxEof   ,
       rxEofe          => rxEofe  ,
       -- AXI-Lite Interface (axilClk domain)
       axilClk         => appClk,
       axilRst         => appRst,
       axilReadMaster  => axilAsicReadMasters(1),
       axilReadSlave   => axilAsicReadSlaves(1),
       axilWriteMaster => axilAsicWriteMasters(1),
       axilWriteSlave  => axilAsicWriteSlaves(1)
     );
      
    
   --------------------------------------------
   --     ASICS LOOP                         --
   --------------------------------------------   
   G_ASICS : for i in 0 to NUMBER_OF_ASICS_C-1 generate

     -------------------------------------------------------------------------------
     -- generate stream frames
     -------------------------------------------------------------------------------
     U_Framers : entity work.DigitalAsicStreamAxi 
       generic map(
         TPD_G               => TPD_G,
         VC_NO_G             => "0000",
         LANE_NO_G           => toSlv(i, 4),
         ASIC_NO_G           => toSlv(i, 3),
         LANES_NO_G          => STREAMS_PER_ASIC_C,
         AXIL_ERR_RESP_G     => AXI_RESP_DECERR_C
         )
       port map( 
         -- Deserialized data port
         deserClk          => deserClk,
         deserRst          => deserRst,
         rxValid           => rxValid(i*STREAMS_PER_ASIC_C+STREAMS_PER_ASIC_C-1 downto i*STREAMS_PER_ASIC_C),
         rxData            => rxData(i*STREAMS_PER_ASIC_C+STREAMS_PER_ASIC_C-1 downto i*STREAMS_PER_ASIC_C),
         rxSof             => rxSof(i*STREAMS_PER_ASIC_C+STREAMS_PER_ASIC_C-1 downto i*STREAMS_PER_ASIC_C),
         rxEof             => rxEof(i*STREAMS_PER_ASIC_C+STREAMS_PER_ASIC_C-1 downto i*STREAMS_PER_ASIC_C),
         rxEofe            => rxEofe(i*STREAMS_PER_ASIC_C+STREAMS_PER_ASIC_C-1 downto i*STREAMS_PER_ASIC_C),
    
      
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
      
         -- start of readout strobe
         startRdout        => iAsicSR0
         );       
   end generate;


   -------------------------------------------------------
   -- AXI stream monitoring                             --
   -------------------------------------------------------
   U_AxiSMonitor : entity surf.AxiStreamMonAxiL 
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
      axisMasters     => imAxisMasters,
      axisSlaves      => mAxisSlaves,
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
   DDR_NOT_GEN : if (not DDR_GEN_G) generate
     -- in order to desable the mem tester, the followint two signasl need to be wired
     mAxiReadMaster  <= AXI_READ_MASTER_INIT_C;
     mAxiWriteMaster <= AXI_WRITE_MASTER_INIT_C;
     -- init unused axiLite
     mAxiWriteSlaves(DDR_MEM_INDEX_C) <= axiLiteWriteSlaveEmptyInit(AXI_RESP_OK_C);
     mAxiReadSlaves(DDR_MEM_INDEX_C)  <= axiLiteReadSlaveEmptyInit(AXI_RESP_OK_C);
   end generate;

   DDR_GEN : if (DDR_GEN_G) generate
     U_AxiMemTester : entity surf.AxiMemTester
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
         start           => startDdrTest, -- input signal that starts the test 
         axiWriteMaster  => mAxiWriteMaster,
         axiWriteSlave   => mAxiWriteSlave,
         axiReadMaster   => mAxiReadMaster,
         axiReadSlave    => mAxiReadSlave
         );

     U_StartDdrTest : entity surf.PwrUpRst
       generic map (
         DURATION_G => 10000000
         )
       port map (
         clk      => appClk,
         rstOut   => startDdrTest_n
         );
     startDdrTest <= not startDdrTest_n;
   end generate;

  
end mapping;
