-------------------------------------------------------------------------------
-- File       : EpixHr10kT.vhd
-- Company    : SLAC National Accelerator Laboratory
-------------------------------------------------------------------------------
-- Description: Firmware Target's Top Level
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

library surf;
use surf.StdRtlPkg.all;
use surf.AxiPkg.all;
use surf.AxiLitePkg.all;
use surf.AxiStreamPkg.all;
use surf.SsiCmdMasterPkg.all;

library epix_hr_core;
use epix_hr_core.EpixHrCorePkg.all;

use work.AppPkg.all;

entity EpixHr10kTLclsIITiming is
   generic (
      TPD_G                : time := 1 ns;
      BUILD_INFO_G         : BuildInfoType;
      ROGUE_SIM_EN_G       : boolean                     := false;
      ROGUE_SIM_PORT_NUM_G : natural range 1024 to 49151 := 11000);
   port (
      -----------------------
      -- Application Ports --
      -----------------------
      -- System Ports
      digPwrEn      : out   sl;
      anaPwrEn      : out   sl;
      syncDigDcDc   : out   sl;
      syncAnaDcDc   : out   sl;
      syncDcDc      : out   slv(6 downto 0);
      daqTg         : in    sl;
      connTgOut     : out   sl;
      connMps       : out   sl;
      connRun       : in    sl;
      -- Fast ADC Ports
      adcSpiClk     : out   sl;
      adcSpiData    : inout sl;
      adcSpiCsL     : out   sl;
      adcPdwn       : out   sl;
      adcClkP       : out   sl;
      adcClkM       : out   sl;
      adcDoClkP     : in    sl;
      adcDoClkM     : in    sl;
      adcFrameClkP  : in    sl;
      adcFrameClkM  : in    sl;
      adcMonDoutP   : in    slv(4 downto 0);
      adcMonDoutN   : in    slv(4 downto 0);
      -- Slow ADC
      slowAdcSclk   : out   sl;
      slowAdcDin    : out   sl;
      slowAdcCsL    : out   sl;
      slowAdcRefClk : out   sl;
      slowAdcDout   : in    sl;
      slowAdcDrdy   : in    sl;
      slowAdcSync   : out   sl;
      -- Slow DACs Port
      sDacCsL       : out   slv(4 downto 0);
      hsDacCsL      : out   sl;
      hsDacLoad     : out   sl;
      dacClrL       : out   sl;
      dacSck        : out   sl;
      dacDin        : out   sl;
      -- ASIC Gbps Ports
      asicDataP     : inout slv(23 downto 0);
      asicDataN     : inout slv(23 downto 0);
      -- ASIC Control Ports
      asicR0        : out   sl;
      asicPpmat     : out   sl;
      asicGlblRst   : out   sl;
      asicSync      : out   sl;
      asicAcq       : out   sl;
      asicRoClkP    : out   slv(3 downto 0);
      asicRoClkN    : out   slv(3 downto 0);
      -- SACI Ports
      asicSaciCmd   : out   sl;
      asicSaciClk   : out   sl;
      asicSaciSel   : out   slv(3 downto 0);
      asicSaciRsp   : in    sl;
      -- Spare Ports
      spareHpP      : inout slv(11 downto 0);
      spareHpN      : inout slv(11 downto 0);
      spareHrP      : inout slv(5 downto 0);
      spareHrN      : inout slv(5 downto 0);
      -- GTH Ports
      gtRxP         : in    sl;
      gtRxN         : in    sl;
      gtTxP         : out   sl;
      gtTxN         : out   sl;
      gtRefP        : in    sl;
      gtRefN        : in    sl;
      smaRxP        : in    sl;
      smaRxN        : in    sl;
      smaTxP        : out   sl;
      smaTxN        : out   sl;
      ----------------
      -- Core Ports --
      ----------------   
      -- Board IDs Ports
      snIoAdcCard   : inout sl;
      snIoCarrier   : inout sl;
      -- QSFP Ports
      qsfpRxP       : in    slv(3 downto 0);
      qsfpRxN       : in    slv(3 downto 0);
      qsfpTxP       : out   slv(3 downto 0);
      qsfpTxN       : out   slv(3 downto 0);
      qsfpClkP      : in    sl;
      qsfpClkN      : in    sl;
      qsfpTimingClkP: in    sl;
      qsfpTimingClkN: in    sl;
      qsfpLpMode    : inout sl;
      qsfpModSel    : inout sl;
      qsfpInitL     : inout sl;
      qsfpRstL      : inout sl;
      qsfpPrstL     : inout sl;
      qsfpScl       : inout sl;
      qsfpSda       : inout sl;
      -- DDR Ports
      ddrClkP       : in    sl;
      ddrClkN       : in    sl;
      ddrBg         : out   sl;
      ddrCkP        : out   sl;
      ddrCkN        : out   sl;
      ddrCke        : out   sl;
      ddrCsL        : out   sl;
      ddrOdt        : out   sl;
      ddrAct        : out   sl;
      ddrRstL       : out   sl;
      ddrA          : out   slv(16 downto 0);
      ddrBa         : out   slv(1 downto 0);
      ddrDm         : inout slv(3 downto 0);
      ddrDq         : inout slv(31 downto 0);
      ddrDqsP       : inout slv(3 downto 0);
      ddrDqsN       : inout slv(3 downto 0);
      ddrPg         : in    sl;
      ddrPwrEn      : out   sl;
      -- SYSMON Ports
      vPIn          : in    sl;
      vNIn          : in    sl);
end EpixHr10kTLclsIITiming;

architecture top_level of EpixHr10kTLclsIITiming is

   constant PGP_NUM_LANE_C : integer := 3;

   -- System Clock and Reset
   signal sysClk          : sl;
   signal sysRst          : sl;
   -- AXI-Lite Register Interface (sysClk domain)
   signal axilReadMaster  : AxiLiteReadMasterType;
   signal axilReadSlave   : AxiLiteReadSlaveType;
   signal axilWriteMaster : AxiLiteWriteMasterType;
   signal axilWriteSlave  : AxiLiteWriteSlaveType;
   -- AXI Stream, one per QSFP lane (sysClk domain)
   signal axisMasters     : AxiStreamMasterArray(PGP_NUM_LANE_C-1 downto 0);
   signal axisSlaves      : AxiStreamSlaveArray(PGP_NUM_LANE_C-1 downto 0);
   -- Auxiliary AXI Stream, (sysClk domain)
   signal sAuxAxisMasters : AxiStreamMasterArray(1 downto 0);
   signal sAuxAxisSlaves  : AxiStreamSlaveArray(1 downto 0);
   -- ssi commands (Lane and Vc 0)
   signal ssiCmd          : SsiCmdMasterType;
   -- Trigger (axilClk domain)
   signal pgpTrigger      : sl;
   -- DDR's AXI Memory Interface (sysClk domain)
   signal axiReadMaster   : AxiReadMasterType;
   signal axiReadSlave    : AxiReadSlaveType;
   signal axiWriteMaster  : AxiWriteMasterType;
   signal axiWriteSlave   : AxiWriteSlaveType;
   -- Microblaze's Interrupt bus (sysClk domain)
   signal mbIrq           : slv(7 downto 0);
   -- snIO and Dig monitoring share signals
   signal asicDM          : sl;

begin

   U_App : entity work.Application
      generic map (
         TPD_G        => TPD_G,
         SIMULATION_G => ROGUE_SIM_EN_G,
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
         -- ssi commands (Lane 0 and Vc 1)
         ssiCmd           => ssiCmd,
         -- Trigger (sysClk domain)
         pgpTrigger       => pgpTrigger,
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
         asicDMSN         => asicDM,
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
         --timing GTH ports
         gtTimingRefClkP  => qsfpTimingClkP,
         gtTimingRefClkN  => qsfpTimingClkN,
         gtTimingRxP      => qsfpRxP(3),
         gtTimingRxN      => qsfpRxN(3),
         gtTimingTxP      => qsfpTxP(3),
         gtTimingTxN      => qsfpTxN(3),
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
         NUM_LANE_G           => PGP_NUM_LANE_C,
         RATE_G               => "6.25Gbps",
         BUILD_INFO_G         => BUILD_INFO_G,
         ROGUE_SIM_EN_G       => ROGUE_SIM_EN_G,
         ROGUE_SIM_PORT_NUM_G => ROGUE_SIM_PORT_NUM_G)
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
         -- ssi commands (Lane 0 and Vc 1)
         ssiCmd           => ssiCmd,
         -- Trigger (axilClk domain)
         pgpTrigger       => pgpTrigger,
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
         snIoCarrier      => snIoCarrier,
         snCarrierOut     => asicDM,
         -- QSFP Ports
         qsfpRxP          => qsfpRxP(PGP_NUM_LANE_C-1 downto 0),
         qsfpRxN          => qsfpRxN(PGP_NUM_LANE_C-1 downto 0),
         qsfpTxP          => qsfpTxP(PGP_NUM_LANE_C-1 downto 0),
         qsfpTxN          => qsfpTxN(PGP_NUM_LANE_C-1 downto 0),
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

end top_level;
