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

library surf;
use surf.StdRtlPkg.all;
use surf.AxiStreamPkg.all;
use surf.AxiLitePkg.all;
use surf.AxiPkg.all;

library unisim;
use unisim.vcomponents.all;

entity Application is
   generic (
      TPD_G            : time            := 1 ns;
      SIMULATION_G     : boolean         := false;
      AXI_ERROR_RESP_G : slv(1 downto 0) := AXI_RESP_SLVERR_C);
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
      sAxilReadSlave   : out   AxiLiteReadSlaveType  := AXI_LITE_READ_SLAVE_EMPTY_OK_C;
      sAxilWriteMaster : in    AxiLiteWriteMasterType;
      sAxilWriteSlave  : out   AxiLiteWriteSlaveType := AXI_LITE_WRITE_SLAVE_EMPTY_OK_C;
      -- AXI Stream, one per QSFP lane (sysClk domain)
      mAxisMasters     : out   AxiStreamMasterArray(3 downto 0);
      mAxisSlaves      : in    AxiStreamSlaveArray(3 downto 0);
      -- Auxiliary AXI Stream, (sysClk domain)
      -- 0 is pseudo scope, 1 is slow adc monitoring
      sAuxAxisMasters  : out   AxiStreamMasterArray(1 downto 0) := (others=>AXI_STREAM_MASTER_INIT_C);
      sAuxAxisSlaves   : in    AxiStreamSlaveArray(1 downto 0)  := (others=>AXI_STREAM_SLAVE_FORCE_C);
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
      sDacCsL          : out   slv(3 downto 0);
      hsDacCsL         : out   sl;
      hsDacEn          : out   sl;
      hsDacLoad        : out   sl;
      hsDacClrL        : out   sl;
      dacSck           : out   sl;
      dacDin           : out   sl;
      -- ASIC Gbps Ports
      asicDataP        : in    slv(23 downto 0);
      asicDataN        : in    slv(23 downto 0);
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

   --heart beat signal
   signal heartBeat   : sl;

begin


   led(0)          <= heartBeat;
   led(2 downto 1) <= (others => '1');
   led(3)          <= not heartBeat;
   ---------------------
   -- Heart beat LED  --
   ---------------------
   U_Heartbeat : entity surf.Heartbeat
      generic map(
         PERIOD_IN_G => 10.0E-9)   
      port map (
         clk => sysClk,
         o   => heartBeat);

   mAxisMasters    <= (others => AXI_STREAM_MASTER_INIT_C);
   mAxiReadMaster  <= AXI_READ_MASTER_INIT_C;
   mAxiWriteMaster <= AXI_WRITE_MASTER_INIT_C;
   mbIrq           <= (others => '0');
   digPwrEn        <= '0';
   anaPwrEn        <= '0';
   syncDigDcDc     <= '0';
   syncAnaDcDc     <= '0';
   syncDcDc        <= (others => '0');
   --led             <= (others => '0');
   connTgOut       <= '0';
   connMps         <= '0';
   adcSpiClk       <= '1';
   adcSpiCsL       <= '1';
   adcPdwn         <= '1';
   U_adcClk : OBUFDS
      port map (
         I  => '0',
         O  => adcClkP,
         OB => adcClkM);   
   slowAdcSclk     <= '1';
   slowAdcDin      <= '1';
   slowAdcCsL      <= '1';
   slowAdcRefClk   <= '1';
   slowAdcSync     <= '0';
   sDacCsL         <= (others => '1');
   hsDacCsL        <= '1';
   hsDacEn         <= '0';
   hsDacLoad       <= '0';
   hsDacClrL       <= '1';
   dacSck          <= '1';
   dacDin          <= '1';
   asicR0          <= '0';
   asicPpmat       <= '0';
   asicGlblRst     <= '1';
   asicSync        <= '0';
   asicAcq         <= '0';
   asicRoClkP      <= (others => '0');
   asicRoClkN      <= (others => '1');
   asicSaciCmd     <= '1';
   asicSaciClk     <= '1';
   asicSaciSel     <= (others => '1');
   gtTxP           <= '0';
   gtTxN           <= '1';
   smaTxP          <= '0';
   smaTxN          <= '1';

end mapping;
