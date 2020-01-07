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
use surf.Ad9249Pkg.all;
use surf.Code8b10bPkg.all;

library epix_hr_core;
use epix_hr_core.EpixHrCorePkg.all;

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
      hsDacEn          : out   sl := '0';
      hsDacLoad        : out   sl;
      hsDacClrL        : out   sl := '0';
      dacClrL          : out   sl;
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


   attribute keep : string;

   --heart beat signal
   signal heartBeat   : sl;
   
   -- prbs signals
   signal prbsBusy            : slv(NUMBER_OF_LANES_C-1 downto 0) := (others => '0');

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

   constant AXI_STREAM_CONFIG_O_C : AxiStreamConfigType   := ssiAxiStreamConfig(4, TKEEP_COMP_C);
   signal imAxisMasters           : AxiStreamMasterArray(3 downto 0);

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
   signal iSaciSelL            : slv(3 downto 0);
   
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
   signal startDdrTest         : sl;
   -- DDR sconstants
   constant DDR_AXI_CONFIG_C : AxiConfigType := axiConfig(
      ADDR_WIDTH_C => 15,
      DATA_BYTES_C => 32,
      ID_BITS_C    => 4,
      LEN_BITS_C   => 8);

   constant START_ADDR_C : slv(DDR_AXI_CONFIG_C.ADDR_WIDTH_C-1 downto 0) := (others => '0');
   constant STOP_ADDR_C  : slv(DDR_AXI_CONFIG_C.ADDR_WIDTH_C-1 downto 0) := (others => '1');

   attribute keep of appClk            : signal is "true";
   attribute keep of startDdrTest_n    : signal is "true";
   attribute keep of iAsicAcq          : signal is "true";

   attribute keep of adcStreams        : signal is "true";


begin


   led(0)          <= clkLocked;
   led(1)          <= prbsBusy(0) or prbsBusy(1) or prbsBusy(2) or prbsBusy(3);
   led(2)          <= '0';
   led(3)          <= not heartBeat;

   axiRst <= appRst;
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
   ----------------------------------------------------------------------------
   -- axi stream routing
   ----------------------------------------------------------------------------
   mAxisMasters    <= imAxisMasters;
   --imAxisMasters(0) is connected to the stream mux directly


   ----------------------------------------------------------------------------
   -- 
   ----------------------------------------------------------------------------
   digPwrEn <= digPwrEn_i;
   anaPwrEn <= anaPwrEn_i;
   
   mbIrq           <= (others => '0');
   --led             <= (others => '0');
   connTgOut       <= '0';
   connMps         <= '0';
   --adcSpiClk       <= '1';
   adcSpiCsL       <= adcSpiCsL_i(0);
   adcPdwn         <= adcPdwn_i(0);
   --adcClkP         <= '0';
   --adcClkM         <= '1';
   --slowAdcSclk     <= '1';
   --slowAdcDin      <= '1';
   --slowAdcCsL      <= '1';
   --slowAdcRefClk   <= '1';
   
   slowAdcSync     <= '0';              -- not used, not connected to the ADC
                                        -- via no load resistor (R67)
   -- routing DAC signals to external IOs
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
   
   asicR0          <= '0';
   asicPpmat       <= '0';
   asicGlblRst     <= '1';
   asicSync        <= '0';
   asicAcq         <= '0';
   asicRoClkP      <= (others => '0');
   asicRoClkN      <= (others => '1');
   asicSaciCmd     <= '1';
   asicSaciClk     <= '1';
   asicSaciSel     <= iSaciSelL;
   iSaciSelL       <=  (others => '1');
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
   -- clkOut(2) : 100.00 MHz asic clock
   -- clkOut(3) : 300.00 MHz idelay control clock
   -- clkOut(4) :  50.00 MHz monitoring adc
   U_CoreClockGen : entity surf.ClockManagerUltraScale 
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
      axilClk         => sysClk,
      axilRst         => axiRst,
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

   U_RdPwrUpRst : entity surf.PwrUpRst
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

   -- ADC Clock outputs
   U_AdcClk2 : OBUFDS port map ( I => adcClk, O => adcClkP, OB => adcClkM );


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




   ---------------------------------------------
   -- AXI Lite Crossbar for register control  --
   -- Master 00 : Clock                       --
   -- Master 01 : Trigger Resiters            --
   -- Master 02 : PRBS                        --
   -- Master 03 : PRBS                        --
   -- Master 04 : PRBS                        --
   -- Master 05 : PRBS                        --
   -- Master 06 : Axi Stream Mon.             --
   -- Master 07 : DDR tester                  --
   -- Master 08 : Power                       --
   -- Master 09 : HSDAC control               --
   -- Master 10 : HSDAC waveform              --
   -- Master 11 : Slow DACs                   --
   -- Master 12 : PseudoScope                 --
   -- Master 13 : Fast  ADC readout           --
   -- Master 14 : Fast. ADC config.           --
   -- Master 15 : Monit. ADC                  --
   -- Master  ? : App Registers (waveform)    --
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
         mAxisRst        => axiRst,
         mAxisMaster     => imAxisMasters(i),
         mAxisSlave      => mAxisSlaves(i),
         -- Trigger Signal (locClk domain)
         locClk          => appClk,
         locRst          => axiRst,
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
   end generate;


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

   --------------------------------------------
   -- Virtual oscilloscope                   --
   --------------------------------------------
   U_PseudoScope : entity work.PseudoScopeAxi
   generic map (
     TPD_G                      => TPD_G,
     MASTER_AXI_STREAM_CONFIG_G => ssiAxiStreamConfig(4, TKEEP_COMP_C)      
   )
   port map ( 
      
      sysClk         => appClk,
      sysClkRst      => axiRst,
      adcData        => adcData,
      adcValid       => adcValid,
      arm            => acqStart,
      acqStart       => acqStart,
      asicAcq        => iAsicAcq,
      asicR0         => iAsicSR0,
      asicPpmat      => iAsicPpmat(0),
      asicPpbe       => iAsicPpbe(0),
      asicSync       => iAsicSync,
      asicGr         => iAsicGrst,
      asicRoClk      => asicRdClk,
      asicSaciSel    => iSaciSelL,
      mAxisMaster    => sAuxAxisMasters(0),
      mAxisSlave     => sAuxAxisSlaves(0),
      -- AXI lite slave port for register access
      axilClk           => appClk,
      axilRst           => axiRst,
      sAxilWriteMaster  => mAxiWriteMasters(SCOPE_REG_AXI_INDEX_C),
      sAxilWriteSlave   => mAxiWriteSlaves(SCOPE_REG_AXI_INDEX_C),
      sAxilReadMaster   => mAxiReadMasters(SCOPE_REG_AXI_INDEX_C),
      sAxilReadSlave    => mAxiReadSlaves(SCOPE_REG_AXI_INDEX_C)

   );

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
      IDELAYCTRL_FREQ_G => 200.0,
      DEFAULT_DELAY_G   => (others => '0'),
      ADC_INVERT_CH_G   => "00000010"
   )
   port map (
      -- Master system clock, 100Mhz
      axilClk           => appClk,
      axilRst           => axiRst,
      
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
      adcStreamClk      => appClk,
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

   U_IdelayCtrlReset : entity surf.RstSync
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
   
   U_AdcConf : entity surf.Ad9249Config
   generic map (
      TPD_G             => TPD_G,
      AXIL_CLK_PERIOD_G => 10.0e-9,
      NUM_CHIPS_G       => 1
--      AXIL_ERR_RESP_G   => AXI_RESP_OK_C
   )
   port map (
      axilClk           => appClk,
      axilRst           => axiRst,
      
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
   --     Slow ADC Readout  (env. variables) --
   -------------------------------------------- 
   U_AdcCntrl: entity work.SlowAdcCntrlAxi
   generic map (
      SYS_CLK_PERIOD_G  => 10.0E-9,	-- 100MHz
      ADC_CLK_PERIOD_G  => 200.0E-9,	-- 5MHz
      SPI_SCLK_PERIOD_G => 2.0E-6  	-- 500kHz
   )
   port map ( 
      -- Master system clock
      sysClk            => appClk,
      sysClkRst         => axiRst,
      
      -- Trigger Control
      adcStart          => acqStart,
      
      -- AXI lite slave port for register access
      axilClk           => appClk,
      axilRst           => axiRst,
      sAxilWriteMaster  => mAxiWriteMasters(MONADC_REG_AXI_INDEX_C),
      sAxilWriteSlave   => mAxiWriteSlaves(MONADC_REG_AXI_INDEX_C),
      sAxilReadMaster   => mAxiReadMasters(MONADC_REG_AXI_INDEX_C),
      sAxilReadSlave    => mAxiReadSlaves(MONADC_REG_AXI_INDEX_C),
      
      -- AXI stream output
      axisClk           => appClk,
      axisRst           => axiRst,
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
   

   --------------------
   -- DDR memory tester
   --------------------
   -- in order to desable the mem tester, the followint two signasl need to be wired
   --   mAxiReadMaster  <= AXI_READ_MASTER_INIT_C;
   --   mAxiWriteMaster <= AXI_WRITE_MASTER_INIT_C;

   U_AxiMemTester : entity surf.AxiMemTester
   generic map (
      TPD_G        => TPD_G,
      START_ADDR_G => START_ADDR_C,
      STOP_ADDR_G  => STOP_ADDR_C,
      AXI_CONFIG_G => DDR_AXI_CONFIG_C)
   port map (
      -- AXI-Lite Interface
      axilClk         => appClk,
      axilRst         => axiRst,
      axilReadMaster  => mAxiReadMasters(DDR_MEM_INDEX_C),
      axilReadSlave   => mAxiReadSlaves(DDR_MEM_INDEX_C),
      axilWriteMaster => mAxiWriteMasters(DDR_MEM_INDEX_C),
      axilWriteSlave  => mAxiWriteSlaves(DDR_MEM_INDEX_C),
      memReady        => open,  -- status bits
      memError        => open, -- status bits
      -- DDR Memory Interface
      axiClk          => sysClk,
      axiRst          => axiRst,
      start           => startDdrTest, -- input signal that starts the test (not possible to use axil at the current version)
      axiWriteMaster  => mAxiWriteMaster,
      axiWriteSlave   => mAxiWriteSlave,
      axiReadMaster   => mAxiReadMaster,
      axiReadSlave    => mAxiReadSlave
   );

   startDdrTest <= not startDdrTest_n;

   U_StartDdrTest : entity surf.PwrUpRst
   generic map (
      DURATION_G => 10000000
   )
   port map (
      clk      => appClk,
      rstOut   => startDdrTest_n
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
      axilRst         => axiRst,   
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
      sysClkRst         => axiRst,
      dacDin            => WFDacDin_i,
      dacSclk           => WFDacSclk_i,
      dacCsL            => WFDacCsL_i,
      dacLdacL          => WFDacLdacL_i,
      dacClrL           => WFDacClrL_i,
      externalTrigger   => acqStart,
      axilClk           => appClk,
      axilRst           => axiRst,
      sAxilWriteMaster  => mAxiWriteMasters,
      sAxilWriteSlave   => mAxiWriteSlaves,
      sAxilReadMaster   => mAxiReadMasters,
      sAxilReadSlave    => mAxiReadSlaves);

  -------------------------------------------------------------------------
  -- SPI DACs
  -------------------------------------------------------------------------
  U_DACs : entity work.slowDacs 
   generic map (
      TPD_G             => TPD_G,
      CLK_PERIOD_G      => 10.0E-9
   )
   port map (
      -- Global Signals
      axiClk => appClk,
      axiRst => axiRst,
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
      
end mapping;
