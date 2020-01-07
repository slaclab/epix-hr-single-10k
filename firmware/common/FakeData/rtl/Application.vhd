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
use surf.Pgp2bPkg.all;
use surf.SsiPkg.all;
use surf.SsiCmdMasterPkg.all;
use surf.Code8b10bPkg.all;

use work.AppPkg.all;

library unisim;
use unisim.vcomponents.all;

entity Application is
   generic (
      TPD_G            : time            := 1 ns;
      APP_CONFIG_G     : AppConfigType   := APP_CONFIG_INIT_C;
      SIMULATION_G     : boolean         := false;
      BUILD_INFO_G     : BuildInfoType;
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
      sAxilReadSlave   : out   AxiLiteReadSlaveType;
      sAxilWriteMaster : in    AxiLiteWriteMasterType;
      sAxilWriteSlave  : out   AxiLiteWriteSlaveType;
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

   -- clock signals
   signal appClk      : sl;
   signal asicClk     : sl;
   signal byteClk     : sl;
   signal appRst      : sl;
   signal axiRst      : sl;
   signal asicRst     : sl;
   signal byteClkRst  : sl;
   signal clkLocked   : sl;

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

   constant AXI_STREAM_CONFIG_O_C : AxiStreamConfigType   := ssiAxiStreamConfig(4, TKEEP_COMP_C);
   signal imAxisMasters    : AxiStreamMasterArray(3 downto 0);


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
   signal iAsicPPbe            : slv(1 downto 0);
   signal iAsicPpmat           : slv(1 downto 0);
   signal iAsicR0              : sl;
   signal iAsicSync            : sl;
   signal iAsicAcq             : sl;
   signal iAsicGrst            : sl;
   signal adcClk               : sl;
   signal errInhibit           : sl;

   -- Command interface
   signal ssiCmd           : SsiCmdMasterType;
   -- Guard ring DAC
   signal vGuardDacSclk       : sl;
   signal vGuardDacDin        : sl;
   signal vGuardDacCsb        : sl;
   signal vGuardDacClrb       : sl;
   
   signal hrConfig       : HR_FDConfigType;
      -- External Signals
      
   signal serialIdIo           : slv(1 downto 0) := "00";

begin


   led(0)          <= clkLocked;
   led(2 downto 1) <= (others => '0');
   led(3)          <= not heartBeat;
   ---------------------
   -- Heart beat LED  --
   ---------------------
   U_Heartbeat : entity surf.Heartbeat
      generic map(
         PERIOD_IN_G => 10.0E-9
      )   
      port map (
         clk => sysClk,
         o   => heartBeat
      );


--   U_AxiLiteEmpty : entity surf.AxiLiteEmpty
--      generic map (
--         TPD_G            => TPD_G,
--         AXI_ERROR_RESP_G => AXI_ERROR_RESP_G)
--      port map (
--         axiClk         => sysClk,
--         axiClkRst      => sysRst,
--         axiReadMaster  => sAxilReadMaster,
--         axiReadSlave   => sAxilReadSlave,
--         axiWriteMaster => sAxilWriteMaster,
--         axiWriteSlave  => sAxilWriteSlave);

  

--   mAxisMasters    <= (others => AXI_STREAM_MASTER_INIT_C);
   mAxisMasters    <= imAxisMasters;
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
   adcClkP         <= '0';
   adcClkM         <= '1';
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

   ------------------------------------------
   -- Generate clocks from 156.25 MHz PGP  --
   ------------------------------------------
   -- clkIn     : 156.25 MHz PGP
   -- clkOut(0) : 100.00 MHz app clock
   -- clkOut(1) : 100.00 MHz asic clock
   U_CoreClockGen : entity surf.ClockManagerUltraScale 
   generic map(
      TPD_G                  => 1 ns,
      TYPE_G                 => "MMCM",  -- or "PLL"
      INPUT_BUFG_G           => true,
      FB_BUFG_G              => true,
      RST_IN_POLARITY_G      => '1',     -- '0' for active low
      NUM_CLOCKS_G           => 2,
      -- MMCM attributes
      BANDWIDTH_G            => "OPTIMIZED",
      CLKIN_PERIOD_G         => 6.4,    -- Input period in ns );
      DIVCLK_DIVIDE_G        => 10,
      CLKFBOUT_MULT_F_G      => 38.4,
      CLKFBOUT_MULT_G        => 5,
      CLKOUT0_DIVIDE_F_G     => 1.0,
      CLKOUT0_DIVIDE_G       => 6,
      CLKOUT1_DIVIDE_G       => 6,
      CLKOUT0_PHASE_G        => 0.0,
      CLKOUT1_PHASE_G        => 0.0,
      CLKOUT0_DUTY_CYCLE_G   => 0.5,
      CLKOUT1_DUTY_CYCLE_G   => 0.5,
      CLKOUT0_RST_HOLD_G     => 3,
      CLKOUT1_RST_HOLD_G     => 3,
      CLKOUT0_RST_POLARITY_G => '1',
      CLKOUT1_RST_POLARITY_G => '1')
   port map(
      clkIn           => sysClk,
      rstIn           => sysRst,
      clkOut(0)       => appClk,
      clkOut(1)       => asicClk,
      rstOut(0)       => appRst,
      rstOut(1)       => asicRst,
      locked          => clkLocked,
      -- AXI-Lite Interface 
      axilClk         => sysClk,
      axilRst         => axiRst,
      axilReadMaster  => mAxiReadMasters(PLLREGS_AXI_INDEX_C),
      axilReadSlave   => mAxiReadSlaves(PLLREGS_AXI_INDEX_C),
      axilWriteMaster => mAxiWriteMasters(PLLREGS_AXI_INDEX_C),
      axilWriteSlave  => mAxiWriteSlaves(PLLREGS_AXI_INDEX_C)
   );      


   U_BUFR : BUFR
   generic map (
      SIM_DEVICE  => "7SERIES",
      BUFR_DIVIDE => "5"
   )
   port map (
      I   => asicClk,
      O   => byteClk,
      CE  => '1',
      CLR => '0'
   );

   U_RdPwrUpRst : entity surf.PwrUpRst
   generic map (
      DURATION_G => 20000000
   )
   port map (
      clk      => byteClk,
      rstOut   => byteClkRst
   );


   U_AxiLiteAsync : entity surf.AxiLiteAsync 
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




   --------------------------------------------
   -- AXI Lite Crossbar for register control --
   -- Master 0 : Clock                       --
   -- Master 1 : App Registers               --
   -- Master 2 : Trigger Resiters            --
   --------------------------------------------
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
      axilRst           => axiRst,
      sAxilWriteMaster  => mAxiWriteMasters(TRIG_REG_AXI_INDEX_C),
      sAxilWriteSlave   => mAxiWriteSlaves(TRIG_REG_AXI_INDEX_C),
      sAxilReadMaster   => mAxiReadMasters(TRIG_REG_AXI_INDEX_C),
      sAxilReadSlave    => mAxiReadSlaves(TRIG_REG_AXI_INDEX_C)
   );

   --------------------------------------------
   --     Master Register Controllers        --
   --------------------------------------------   
   U_RegControl : entity work.RegControlHR_FD
   generic map (
      TPD_G           => TPD_G,
      EN_DEVICE_DNA_G => false,
      BUILD_INFO_G    => BUILD_INFO_G
   )
   port map (
      axiClk         => appClk,
      axiRst         => axiRst,
      sysRst         => appRst,
      -- AXI-Lite Register Interface (axiClk domain)
      axiReadMaster  => mAxiReadMasters(HR_FD_REG_AXI_INDEX_C),
      axiReadSlave   => mAxiReadSlaves(HR_FD_REG_AXI_INDEX_C),
      axiWriteMaster => mAxiWriteMasters(HR_FD_REG_AXI_INDEX_C),
      axiWriteSlave  => mAxiWriteSlaves(HR_FD_REG_AXI_INDEX_C),
      -- Register Inputs/Outputs (axiClk domain)
      hrConfig       => hrConfig,
      -- Guard ring DAC interfaces
      dacSclk        => vGuardDacSclk,
      dacDin         => vGuardDacDin,
      dacCsb         => vGuardDacCsb,
      dacClrb        => vGuardDacClrb,
      -- 1-wire board ID interfaces
      serialIdIo     => serialIdIo,
      -- fast ADC clock
      adcClk         => adcClk,
      -- ASICs acquisition signals
      acqStart       => acqStart,
      saciReadoutReq => saciPrepReadoutReq,
      saciReadoutAck => saciPrepReadoutAck,
      asicEnA        => iAsicEnA,
      asicEnB        => iAsicEnB,
      asicVid        => iAsicVid,
      asicSR0        => iAsicSR0,
      asicPPbe       => iAsicPpbe,
      asicPpmat      => iAsicPpmat,
      asicR0         => iAsicR0,
      asicGlblRst    => iAsicGrst,
      asicSync       => iAsicSync,
      asicAcq        => iAsicAcq,
      errInhibit     => errInhibit
   );

   G_ASIC : for i in 0 to NUMBER_OF_ASICS_C-1 generate 
      -------------------------------------------------------
      -- ASIC AXI stream framers
      -------------------------------------------------------
      
      U_AXI_Framer : entity work.HRStreamAxi
      generic map (
         ASIC_NO_G   => std_logic_vector(to_unsigned(i, 3))
      )
      port map (
         rxClk             => byteClk,
         rxRst             => byteClkRst,
         rxData            => (others => '0'),
         rxValid           => '0',
         axilClk           => appClk,
         axilRst           => axiRst,
         sAxilWriteMaster  => mAxiWriteMasters(ASICS0_AXI_INDEX_C+i),
         sAxilWriteSlave   => mAxiWriteSlaves(ASICS0_AXI_INDEX_C+i),
         sAxilReadMaster   => mAxiReadMasters(ASICS0_AXI_INDEX_C+i),
         sAxilReadSlave    => mAxiReadSlaves(ASICS0_AXI_INDEX_C+i),
         axisClk           => sysClk,
         axisRst           => axiRst,
         mAxisMaster       => imAxisMasters(i),
         mAxisSlave        => mAxisSlaves(i),
         acqNo             => hrConfig.syncCounter,
         testTrig          => iAsicAcq,
         asicSR0           => iAsicSR0,
         asicSync          => iAsicSync,
         errInhibit        => errInhibit
      );
   end generate;


   U_AxiSMonitor : entity surf.AxiStreamMonAxiL 
   generic map(
      TPD_G             => 1 ns,
      COMMON_CLK_G      => false,  -- true if axisClk = statusClk
      AXIS_CLK_FREQ_G   => 156.25E+6,  -- units of Hz
      AXIS_NUM_SLOTS_G  => 4,
      AXIS_CONFIG_G     => AXI_STREAM_CONFIG_O_C)
   port map(
      -- AXIS Stream Interface
      axisClk         => sysClk,
      axisRst         => axiRst,
      axisMasters     => imAxisMasters,
      axisSlaves      => mAxisSlaves,
      -- AXI lite slave port for register access
      axilClk         => appClk,  
      axilRst         => axiRst,   
      sAxilWriteMaster=> mAxiWriteMasters(AXI_STREAM_MON_INDEX_C),
      sAxilWriteSlave => mAxiWriteSlaves(AXI_STREAM_MON_INDEX_C),
      sAxilReadMaster => mAxiReadMasters(AXI_STREAM_MON_INDEX_C),
      sAxilReadSlave  => mAxiReadSlaves(AXI_STREAM_MON_INDEX_C)
   );
end mapping;
