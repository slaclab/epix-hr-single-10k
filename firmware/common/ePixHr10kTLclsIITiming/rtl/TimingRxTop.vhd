-------------------------------------------------------------------------------
-- File       : TimingRxTop.vhd
-- Company    : SLAC National Accelerator Laboratory
-- Created    : 2017-02-04
-- Last update: 2022-09-08
-------------------------------------------------------------------------------
-- Description: Wave8 System Core
-------------------------------------------------------------------------------
-- This file is part of 'Wave8 Firmware'.
-- It is subject to the license terms in the LICENSE.txt file found in the
-- top-level directory of this distribution and at:
--    https://confluence.slac.stanford.edu/display/ppareg/LICENSE.html.
-- No part of 'Wave8 Firmware', including this file,
-- may be copied, modified, propagated, or distributed except according to
-- the terms contained in the LICENSE.txt file.
-------------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;
use ieee.std_logic_unsigned.all;
use ieee.std_logic_arith.all;

library unisim;
use unisim.vcomponents.all;

library surf;
use surf.StdRtlPkg.all;
use surf.AxiLitePkg.all;
use surf.AxiStreamPkg.all;
use surf.SsiPkg.all;

library lcls_timing_core;
use lcls_timing_core.TimingPkg.all;

library l2si_core;
use l2si_core.L2SiPkg.all;

entity TimingRxTop is
   generic (
      TPD_G             : time             := 1 ns;
      SIMULATION_G      : boolean          := false;
      AXI_BASE_ADDR_G   : slv(31 downto 0) := (others => '0');
      DMA_AXIS_CONFIG_G : AxiStreamConfigType;
      NUM_DETECTORS_G   : integer range 1 to 4);
   port (
      gtRefClkP           : in  sl;     -- 371 MHz ref
      gtRefClkN           : in  sl;
      gtRxP               : in  sl;
      gtRxN               : in  sl;
      gtTxP               : out sl;
      gtTxN               : out sl;
      -- timing control signals
      rxUserRst           : in  sl;
      txUserRst           : in  sl;
      useMiniTpg          : in  sl;
      -- timing status
      v1LinkUp            : out sl;
      v2LinkUp            : out sl;
      -- AXI-Lite Register Interface
      axilClk             : in  sl;
      axilRst             : in  sl;
      mAxilReadMaster     : in  AxiLiteReadMasterType;
      mAxilReadSlave      : out AxiLiteReadSlaveType;
      mAxilWriteMaster    : in  AxiLiteWriteMasterType;
      mAxilWriteSlave     : out AxiLiteWriteSlaveType;
      -- Trigger Interface
      triggerClk          : in  sl;
      triggerRst          : in  sl;
      triggerData         : out TriggerEventDataArray(NUM_DETECTORS_G-1 downto 0);
      -- L1 trigger feedback (optional)
      l1Clk               : in  sl                                                 := '0';
      l1Rst               : in  sl                                                 := '0';
      l1Feedbacks         : in  TriggerL1FeedbackArray(NUM_DETECTORS_G-1 downto 0) := (others => TRIGGER_L1_FEEDBACK_INIT_C);
      l1Acks              : out slv(NUM_DETECTORS_G-1 downto 0);
      -- Event streams
      eventClk            : in  sl;
      eventRst            : in  sl;
      eventTimingMessages : out TimingMessageArray(NUM_DETECTORS_G-1 downto 0);
      eventAxisMasters    : out AxiStreamMasterArray(NUM_DETECTORS_G-1 downto 0);
      eventAxisSlaves     : in  AxiStreamSlaveArray(NUM_DETECTORS_G-1 downto 0);
      eventAxisCtrl       : in  AxiStreamCtrlArray(NUM_DETECTORS_G-1 downto 0));
end TimingRxTop;

architecture top_level of TimingRxTop is

   constant NUM_AXI_MASTERS_C : natural := 4;

   constant RX_PHY0_INDEX_C  : natural := 0;
   constant TIMING_INDEX_C   : natural := 1;
   constant XPM_MINI_INDEX_C : natural := 2;
   constant TEM_INDEX_C      : natural := 3;

   constant AXI_CONFIG_C : AxiLiteCrossbarMasterConfigArray(NUM_AXI_MASTERS_C-1 downto 0) := genAxiLiteConfig(NUM_AXI_MASTERS_C, AXI_BASE_ADDR_G, 24, 20);

   signal axilWriteMasters : AxiLiteWriteMasterArray(NUM_AXI_MASTERS_C-1 downto 0);
   signal axilWriteSlaves  : AxiLiteWriteSlaveArray(NUM_AXI_MASTERS_C-1 downto 0);
   signal axilReadMasters  : AxiLiteReadMasterArray(NUM_AXI_MASTERS_C-1 downto 0);
   signal axilReadSlaves   : AxiLiteReadSlaveArray(NUM_AXI_MASTERS_C-1 downto 0);

   ------------------
   signal timingClkSel   : sl;
   signal gtRxOutClk     : sl;
   signal gtRxClk        : sl;
   signal timingRxClk    : sl;
   signal timingRxRst    : sl;
   signal timingRxRstTmp : sl;
   signal gtRxData       : slv(15 downto 0);
   signal rxData         : slv(15 downto 0);
   signal gtRxDataK      : slv(1 downto 0);
   signal rxDataK        : slv(1 downto 0);
   signal gtRxDispErr    : slv(1 downto 0);
   signal rxDispErr      : slv(1 downto 0);
   signal gtRxDecErr     : slv(1 downto 0);
   signal rxDecErr       : slv(1 downto 0);
   signal gtRxStatus     : TimingPhyStatusType;
   signal rxStatus       : TimingPhyStatusType;
   signal rxCtrl         : TimingPhyControlType;
   signal rxControl      : TimingPhyControlType;

   signal gtRefClkIn   : sl;
   signal gtRefClkDiv2 : sl;
   signal refClkDiv2   : sl;

   signal gtTxOutClk  : sl;
   signal gtTxClk     : sl;
   signal timingTxClk : sl;
   signal timingTxRst : sl;

   signal xpmMiniTimingPhy : TimingPhyType;
   signal appTimingBus     : TimingBusType;
   signal appTimingMode    : sl;

   -----------------------------------------------
   -- Event Header Cache signals
   -----------------------------------------------
   signal temTimingTxPhy : TimingPhyType;
   signal txControl      : TimingPhyControlType;

begin

   v1LinkUp <= appTimingBus.v1.linkUp;
   v2LinkUp <= appTimingBus.v2.linkUp;

   timingTxRst    <= txUserRst;
   timingRxRstTmp <= rxUserRst or not rxStatus.resetDone;

   U_RstSync_1 : entity surf.RstSync
      generic map (
         TPD_G => TPD_G)
      port map (
         clk      => timingRxClk,       -- [in]
         asyncRst => timingRxRstTmp,    -- [in]
         syncRst  => timingRxRst);      -- [out]

   txControl.pllReset    <= timingTxRst;
   txControl.reset       <= timingTxRst;
   txControl.inhibit     <= '0';
   txControl.polarity    <= '0';
   txControl.bufferByRst <= '0';

   ---------------------
   -- AXI-Lite: Crossbar
   ---------------------
   U_XBAR0 : entity surf.AxiLiteCrossbar
      generic map (
         TPD_G              => TPD_G,
         NUM_SLAVE_SLOTS_G  => 1,
         NUM_MASTER_SLOTS_G => NUM_AXI_MASTERS_C,
         MASTERS_CONFIG_G   => AXI_CONFIG_C)
      port map (
         axiClk              => axilClk,
         axiClkRst           => axilRst,
         sAxiWriteMasters(0) => mAxilWriteMaster,
         sAxiWriteSlaves(0)  => mAxilWriteSlave,
         sAxiReadMasters(0)  => mAxilReadMaster,
         sAxiReadSlaves(0)   => mAxilReadSlave,

         mAxiWriteMasters => axilWriteMasters,
         mAxiWriteSlaves  => axilWriteSlaves,
         mAxiReadMasters  => axilReadMasters,
         mAxiReadSlaves   => axilReadSlaves);

   ---------------------------------
   -- Timing Reference clock buffers
   ---------------------------------
   U_IBUFDS_GTE3 : IBUFDS_GTE3
      generic map (
         REFCLK_EN_TX_PATH  => '0',
         REFCLK_HROW_CK_SEL => "01",  -- 2'b01: ODIV2 = Divide-by-2 version of O
         REFCLK_ICNTL_RX    => "00")
      port map (
         I     => gtRefClkP,
         IB    => gtRefClkN,
         CEB   => '0',
         ODIV2 => gtRefClkDiv2,         -- 371 MHz
         O     => gtRefClkIn);          -- 187 MHz

   U_BUFG_GT : BUFG_GT
      port map (
         I       => gtRefClkDiv2,       -- 187 MHz
         CE      => '1',
         CEMASK  => '1',
         CLR     => '0',
         CLRMASK => '1',
         DIV     => "000",              -- Divide by 1
         O       => refClkDiv2);        -- 187 MHz

   U_RXCLK : BUFGMUX
      generic map (
         CLK_SEL_TYPE => "ASYNC")       -- ASYNC, SYNC
      port map (
         O  => gtRxClk,                 -- 1-bit output: Clock output
         I0 => gtRxOutClk,              -- 1-bit input: Clock input (S=0)
         I1 => refClkDiv2,              -- 1-bit input: Clock input (S=1)
         S  => useMiniTpg);             -- 1-bit input: Clock select

   U_TXCLK : BUFGMUX
      generic map (
         CLK_SEL_TYPE => "ASYNC")       -- ASYNC, SYNC
      port map (
         O  => gtTxClk,                 -- 1-bit output: Clock output
         I0 => gtTxOutClk,              -- 1-bit input: Clock input (S=0)
         I1 => refClkDiv2,              -- 1-bit input: Clock input (S=1)
         S  => useMiniTpg);             -- 1-bit input: Clock select

   -------------
   -- GTH Module
   -------------
   REAL_PCIE : if (not SIMULATION_G) generate

      U_LCLS2_GT : entity lcls_timing_core.TimingGtCoreWrapper
         generic map (
            TPD_G            => TPD_G,
            AXIL_BASE_ADDR_G => AXI_CONFIG_C(RX_PHY0_INDEX_C).baseAddr,
            ADDR_BITS_G      => 12,
            GTH_DRP_OFFSET_G => x"00001000")
         port map (
            -- AXI-Lite Port
            axilClk         => axilClk,
            axilRst         => axilRst,
            axilReadMaster  => axilReadMasters(RX_PHY0_INDEX_C),
            axilReadSlave   => axilReadSlaves(RX_PHY0_INDEX_C),
            axilWriteMaster => axilWriteMasters(RX_PHY0_INDEX_C),
            axilWriteSlave  => axilWriteSlaves(RX_PHY0_INDEX_C),
            stableClk       => axilClk,
            stableRst       => axilRst,
            -- GTH Ports
            gtRefClk        => gtRefClkIn,
            gtRefClkDiv2    => refClkDiv2,
            gtRxP           => gtRxP,
            gtRxN           => gtRxN,
            gtTxP           => gtTxP,
            gtTxN           => gtTxN,
            -- Rx ports
            rxControl       => rxControl,
            rxStatus        => gtRxStatus,
            rxUsrClkActive  => '1',
            rxUsrClk        => timingRxClk,
            rxData          => gtRxData,
            rxDataK         => gtRxDataK,
            rxDispErr       => gtRxDispErr,
            rxDecErr        => gtRxDecErr,
            rxOutClk        => gtRxOutClk,
            -- Tx Ports
            txControl       => txControl,
            txUsrClk        => gtTxOutClk,
            txUsrClkActive  => '1',
            txData          => temTimingTxPhy.data,
            txDataK         => temTimingTxPhy.dataK,
            txOutClk        => gtTxOutClk,
            -- Misc.
            loopback        => "000");

   end generate;

   SIM_PCIE : if (SIMULATION_G) generate

      axilReadSlaves(RX_PHY0_INDEX_C)  <= AXI_LITE_READ_SLAVE_EMPTY_OK_C;
      axilWriteSlaves(RX_PHY0_INDEX_C) <= AXI_LITE_WRITE_SLAVE_EMPTY_OK_C;

      gtRxOutClk  <= axilClk;
      gtTxOutClk  <= axilClk;
      gtRxStatus  <= TIMING_PHY_STATUS_FORCE_C;
      gtRxData    <= (others => '0');   --temTimingTxPhy.data;
      gtRxDataK   <= (others => '0');   --temTimingTxPhy.dataK;
      gtRxDispErr <= "00";
      gtRxDecErr  <= "00";

   end generate;

   process(timingRxClk)
   begin
      -- Register to help meet timing
      if rising_edge(timingRxClk) then
         if (useMiniTpg = '1') then
            rxStatus  <= TIMING_PHY_STATUS_FORCE_C after TPD_G;
            rxData    <= xpmMiniTimingPhy.data     after TPD_G;
            rxDataK   <= xpmMiniTimingPhy.dataK    after TPD_G;
            rxDispErr <= "00"                      after TPD_G;
            rxDecErr  <= "00"                      after TPD_G;
         else
            rxStatus  <= gtRxStatus  after TPD_G;
            rxData    <= gtRxData    after TPD_G;
            rxDataK   <= gtRxDataK   after TPD_G;
            rxDispErr <= gtRxDispErr after TPD_G;
            rxDecErr  <= gtRxDecErr  after TPD_G;
         end if;
      end if;
   end process;

   timingRxClk <= gtRxClk;
   timingTxClk <= gtTxClk;

   -----------------------
   -- Insert user RX reset
   -----------------------
   rxControl.reset       <= rxCtrl.reset or rxUserRst;
   rxControl.inhibit     <= rxCtrl.inhibit;
   rxControl.polarity    <= rxCtrl.polarity;
   rxControl.bufferByRst <= rxCtrl.bufferByRst;
   rxControl.pllReset    <= rxCtrl.pllReset or rxUserRst;

   --------------
   -- Timing Core
   --------------
   U_TimingCore : entity lcls_timing_core.TimingCore
      generic map (
         TPD_G             => TPD_G,
         DEFAULT_CLK_SEL_G => '1',      -- '1': default LCLS-II
         TPGEN_G           => false,
         AXIL_RINGB_G      => false,
         ASYNC_G           => true,
         AXIL_BASE_ADDR_G  => AXI_CONFIG_C(TIMING_INDEX_C).baseAddr)
      port map (
         -- GT Interface
         gtTxUsrClk      => timingTxClk,
         gtTxUsrRst      => timingTxRst,
         gtRxRecClk      => timingRxClk,
         gtRxData        => rxData,
         gtRxDataK       => rxDataK,
         gtRxDispErr     => rxDispErr,
         gtRxDecErr      => rxDecErr,
         gtRxControl     => rxCtrl,
         gtRxStatus      => rxStatus,
         timingClkSel    => timingClkSel,
         -- Decoded timing message interface
         appTimingClk    => timingRxClk,
         appTimingRst    => timingRxRst,
         appTimingMode   => appTimingMode,
         appTimingBus    => appTimingBus,
         -- AXI Lite interface
         axilClk         => axilClk,
         axilRst         => axilRst,
         axilReadMaster  => axilReadMasters(TIMING_INDEX_C),
         axilReadSlave   => axilReadSlaves(TIMING_INDEX_C),
         axilWriteMaster => axilWriteMasters(TIMING_INDEX_C),
         axilWriteSlave  => axilWriteSlaves(TIMING_INDEX_C));

   ---------------------
   -- XPM Mini Wrapper
   -- Simulates a timing/xpm stream
   ---------------------
   U_XpmMiniWrapper_1 : entity l2si_core.XpmMiniWrapper
      generic map (
         TPD_G           => TPD_G,
         NUM_DS_LINKS_G  => 1,
         AXIL_BASEADDR_G => AXI_CONFIG_C(XPM_MINI_INDEX_C).baseAddr)
      port map (
         timingClk => timingRxClk,       -- [in]
         timingRst => timingRxRst,       -- [in]
         dsTx(0)   => xpmMiniTimingPhy,  -- [out]

         dsRxClk(0)     => timingTxClk,           -- [in]
         dsRxRst(0)     => timingTxRst,           -- [in]
         dsRx(0).data   => temTimingTxPhy.data,   -- [in]
         dsRx(0).dataK  => temTimingTxPhy.dataK,  -- [in]
         dsRx(0).decErr => (others => '0'),       -- [in]
         dsRx(0).dspErr => (others => '0'),       -- [in]

         axilClk         => axilClk,                             -- [in]
         axilRst         => axilRst,                             -- [in]
         axilReadMaster  => axilReadMasters(XPM_MINI_INDEX_C),   -- [in]
         axilReadSlave   => axilReadSlaves(XPM_MINI_INDEX_C),    -- [out]
         axilWriteMaster => axilWriteMasters(XPM_MINI_INDEX_C),  -- [in]
         axilWriteSlave  => axilWriteSlaves(XPM_MINI_INDEX_C));  -- [out]

   ---------------------------------------------------------------
   -- Decode events and buffer them for the application
   ---------------------------------------------------------------
   U_TriggerEventManager_1 : entity l2si_core.TriggerEventManager
      generic map (
         TPD_G                          => TPD_G,
         EN_LCLS_I_TIMING_G             => false,
         EN_LCLS_II_TIMING_G            => true,
         NUM_DETECTORS_G                => NUM_DETECTORS_G,
         AXIL_BASE_ADDR_G               => AXI_CONFIG_C(TEM_INDEX_C).baseAddr,
         EVENT_AXIS_CONFIG_G            => DMA_AXIS_CONFIG_G,
         L1_CLK_IS_TIMING_TX_CLK_G      => false,
         TRIGGER_CLK_IS_TIMING_RX_CLK_G => false,
         EVENT_CLK_IS_TIMING_RX_CLK_G   => false)
      port map (
         timingRxClk         => timingRxClk,                    -- [in]
         timingRxRst         => timingRxRst,                    -- [in]
         timingBus           => appTimingBus,                   -- [in]
         timingMode          => appTimingMode,                  -- [in]
         timingTxClk         => timingTxClk,                    -- [in]
         timingTxRst         => timingTxRst,                    -- [in]
         timingTxPhy         => temTimingTxPhy,                 -- [out]
         triggerClk          => triggerClk,                     -- [in]
         triggerRst          => triggerRst,                     -- [in]
         triggerData         => triggerData,                    -- [out]
         l1Clk               => l1Clk,                          -- [in]
         l1Rst               => l1Rst,                          -- [in]
         l1Feedbacks         => l1Feedbacks,                    -- [in]
         l1Acks              => l1Acks,                         -- [out]
         eventClk            => eventClk,                       -- [in]
         eventRst            => eventRst,                       -- [in]
         eventTimingMessages => eventTimingMessages,            -- [out]
         eventAxisMasters    => eventAxisMasters,               -- [out]
         eventAxisSlaves     => eventAxisSlaves,                -- [in]
         eventAxisCtrl       => eventAxisCtrl,                  -- [in]
         axilClk             => axilClk,                        -- [in]
         axilRst             => axilRst,                        -- [in]
         axilReadMaster      => axilReadMasters(TEM_INDEX_C),   -- [in]
         axilReadSlave       => axilReadSlaves(TEM_INDEX_C),    -- [out]
         axilWriteMaster     => axilWriteMasters(TEM_INDEX_C),  -- [in]
         axilWriteSlave      => axilWriteSlaves(TEM_INDEX_C));  -- [out]

end top_level;
