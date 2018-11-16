-------------------------------------------------------------------------------
-- File       : Ad9249ReadoutGroup.vhd
-- Company    : SLAC National Accelerator Laboratory
-- Created    : 2016-05-26
-- Last update: 2018-11-16
-------------------------------------------------------------------------------
-- Description:
-- ADC Readout Controller
-- Receives ADC Data from an AD9592 chip.
-- Designed specifically for Xilinx Ultrascale series FPGAs
-------------------------------------------------------------------------------
-- This file is part of 'SLAC Firmware Standard Library'.
-- It is subject to the license terms in the LICENSE.txt file found in the 
-- top-level directory of this distribution and at: 
--    https://confluence.slac.stanford.edu/display/ppareg/LICENSE.html. 
-- No part of 'SLAC Firmware Standard Library', including this file, 
-- may be copied, modified, propagated, or distributed except according to 
-- the terms contained in the LICENSE.txt file.
-------------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;
use ieee.std_logic_arith.all;
use ieee.std_logic_unsigned.all;

library UNISIM;
use UNISIM.vcomponents.all;

use work.StdRtlPkg.all;
use work.AxiLitePkg.all;
use work.AxiStreamPkg.all;
use work.HrAdcPkg.all;


entity Hr16bAdcReadoutGroupUS is
   generic (
      TPD_G               : time                 := 1 ns;
      NUM_CHANNELS_G      : natural range 1 to 8 := 8;
      IODELAY_GROUP_G     : string               := "DEFAULT_GROUP";
      IDELAYCTRL_FREQ_G   : real                 := 200.0;
      DELAY_VALUE_G       : natural              := 1250;
      DEFAULT_DELAY_G     : slv(8 downto 0)      := (others => '0');
      ADC_INVERT_CH_G     : slv(7 downto 0)      := "00000000");
   port (
      -- axilite system clock, 100Mhz
      axilClk : in sl;
      axilRst : in sl;

      -- Axi Interface
      axilWriteMaster   : in  AxiLiteWriteMasterType;
      axilWriteSlave    : out AxiLiteWriteSlaveType;
      axilReadMaster    : in  AxiLiteReadMasterType;
      axilReadSlave     : out AxiLiteReadSlaveType;

      -- common clocks to all deserializers
      bitClk            : in sl;
      byteClk           : in sl;          -- bit clk divided by 5
      deserClk          : in sl;          -- deserializer clk DDR, 8 bits => bit
                                        -- clk divided by 4    
      -- Reset for adc deserializer
      adcClkRst         : in sl;
      --
      idelayCtrlRdy     : in sl := '1'; 

      -- Serial Data from ADC
      adcSerial         : in HrAdcSerialGroupType;

      -- Deserialized ADC Data
      adcStreamClk      : in  sl;
      adcStreams        : out AxiStreamMasterArray(NUM_CHANNELS_G-1 downto 0) :=
      (others => axiStreamMasterInit((false, 2, 8, 0, TKEEP_NORMAL_C, 0, TUSER_NORMAL_C)));
      adcStreamsEn_n    : out slv(NUM_CHANNELS_G-1 downto 0));
end Hr16bAdcReadoutGroupUS;

-- Define architecture
architecture rtl of Hr16bAdcReadoutGroupUS is

  attribute keep : string;

  constant NUM_BITS_C       : natural          := 20;
  constant IDLE_PATTERN_1_C : slv((NUM_BITS_C-1) downto 0) := "1010101010" & "0101111100";
  constant IDLE_PATTERN_2_C : slv((NUM_BITS_C-1) downto 0) := "1010101010" & "1010000011";
  constant FRAME_PATTERN_C  : slv((NUM_BITS_C-1) downto 0) := "1111111111" & "0000000000";
  constant LOCKED_COUNTER_VALUE_C : slv(15 downto 0) := x"0100";
  constant VECTOR_OF_ZEROS_C : slv(15 downto 0) := (others => '0');
  
   -------------------------------------------------------------------------------------------------
   -- AXIL Registers
   -------------------------------------------------------------------------------------------------
   type AxilRegType is record
      resync         : sl;
      axilWriteSlave : AxiLiteWriteSlaveType;
      axilReadSlave  : AxiLiteReadSlaveType;
      delay          : slv9Array(NUM_CHANNELS_G-1 downto 0);
      dataDelaySet   : slv(NUM_CHANNELS_G-1 downto 0);
      idelayCtrlRdy  : sl;     
      freezeDebug    : sl;
      readoutDebug0  : slv20Array(NUM_CHANNELS_G-1 downto 0);
      readoutDebug1  : slv20Array(NUM_CHANNELS_G-1 downto 0);
      adcStreamsEn_n : slv(NUM_CHANNELS_G-1 downto 0);
      lockedCountRst : sl;
   end record;

   constant AXIL_REG_INIT_C : AxilRegType := (
      resync         => '0',
      axilWriteSlave => AXI_LITE_WRITE_SLAVE_INIT_C,
      axilReadSlave  => AXI_LITE_READ_SLAVE_INIT_C,
      delay          => (others => DEFAULT_DELAY_G),
      dataDelaySet   => (others => '1'),
      idelayCtrlRdy  => '0',
      freezeDebug    => '0',
      readoutDebug0  => (others => (others => '0')),
      readoutDebug1  => (others => (others => '0')),
      adcStreamsEn_n => (others => '0'),
      lockedCountRst => '0');

   signal lockedSync      : slv(NUM_CHANNELS_G-1 downto 0);
   signal lockedFallCount : slv16Array(NUM_CHANNELS_G-1 downto 0);

   signal axilR   : AxilRegType := AXIL_REG_INIT_C;
   signal axilRin : AxilRegType;

   -------------------------------------------------------------------------------------------------
   -- ADC Readout Clocked Registers
   -------------------------------------------------------------------------------------------------
   type AdcRegType is record
      slip           : Slv3Array(NUM_CHANNELS_G-1 downto 0); 
      count          : Slv6Array(NUM_CHANNELS_G-1 downto 0);
      lockedCounter  : Slv16Array(NUM_CHANNELS_G-1 downto 0);
      gearBoxOffset  : Slv2Array(NUM_CHANNELS_G-1 downto 0); 
      idleWord       : slv(NUM_CHANNELS_G-1 downto 0);
      locked         : slv(NUM_CHANNELS_G-1 downto 0);
      dataValidAll   : sl;
      fifoWrData     : Slv20Array(NUM_CHANNELS_G-1 downto 0);
   end record;

   constant ADC_REG_INIT_C : AdcRegType := (
      slip           => (others => (others => '0')),
      count          => (others => (others => '0')),
      lockedCounter  => (others => (others => '0')),
      gearBoxOffset  => (others => (others => '0')),
      idleWord       => (others => '0'),
      locked         => (others => '0'),
      dataValidAll   => '0',
      fifoWrData     => (others => (others => '0')));

   signal adcR   : AdcRegType := ADC_REG_INIT_C;
   signal adcRin : AdcRegType;


   -- Local Signals
   signal adcBitRst      : sl;
   signal adcDataPadOut  : slv(NUM_CHANNELS_G-1 downto 0);
   signal adcDataPad     : slv(NUM_CHANNELS_G-1 downto 0);
   signal adcData        : Slv20Array(NUM_CHANNELS_G-1 downto 0);
   signal dataValid      : slv(NUM_CHANNELS_G-1 downto 0);
   signal curDelayData   : slv9Array(NUM_CHANNELS_G-1 downto 0);
   signal resync         : sl;
   signal adcSEnSync     : slv(NUM_CHANNELS_G-1 downto 0);

   type Slv10bData is array (natural range<>) of slv10Array(63 downto 0);
   signal tenbData       : Slv10bData(NUM_CHANNELS_G-1 downto 0);

   signal fifoDataValid  : sl;
   signal fifoDataOut    : slv(NUM_CHANNELS_G*NUM_BITS_C-1 downto 0);
   signal fifoDataIn     : slv(NUM_CHANNELS_G*NUM_BITS_C-1 downto 0);
   signal fifoDataTmp    : slv20Array(NUM_CHANNELS_G-1 downto 0);

   signal debugDataValid : sl;
   signal debugDataOut   : slv(NUM_CHANNELS_G*NUM_BITS_C-1 downto 0);
   signal debugDataTmp   : slv20Array(NUM_CHANNELS_G-1 downto 0);

  attribute keep of bitClk        : signal is "true";
  attribute keep of byteClk       : signal is "true";  
  attribute keep of adcData       : signal is "true";
  attribute keep of dataValid     : signal is "true";
  attribute keep of adcR          : signal is "true";
  attribute keep of tenbData      : signal is "true";
  

begin

   -- Regional clock reset
   ADC_BITCLK_RST_SYNC : entity work.RstSync
      generic map (
         TPD_G           => TPD_G,
         RELEASE_DELAY_G => 5)
      port map (
         clk      => byteClk,
         asyncRst => adcClkRst,
         syncRst  => adcBitRst);

   -------------------------------------------------------------------------------------------------
   -- Synchronize adcR.locked across to axil clock domain and count falling edges on it
   -------------------------------------------------------------------------------------------------
   GenLockCounters : for i in NUM_CHANNELS_G-1 downto 0 generate
     SynchronizerOneShotCnt_1 : entity work.SynchronizerOneShotCnt
       generic map (
         TPD_G          => TPD_G,
         IN_POLARITY_G  => '0',
         OUT_POLARITY_G => '0',
         CNT_RST_EDGE_G => true,
         CNT_WIDTH_G    => 16)
       port map (
         dataIn     => adcR.locked(i),
         rollOverEn => '0',
         cntRst     => axilR.lockedCountRst,
         dataOut    => open,
         cntOut     => lockedFallCount(i),
         wrClk      => byteClk,
         wrRst      => '0',
         rdClk      => axilClk,
         rdRst      => axilRst);

     Synchronizer_1 : entity work.Synchronizer
       generic map (
         TPD_G    => TPD_G,
         STAGES_G => 2)
       port map (
         clk     => axilClk,
         rst     => axilRst,
         dataIn  => adcR.locked(i),
         dataOut => lockedSync(i));

     SynchronizerStrmEn : entity work.Synchronizer
       generic map (
         TPD_G    => TPD_G,
         STAGES_G => 2)
       port map (
         clk     => byteClk,
         rst     => adcBitRst,
         dataIn  => axilR.adcStreamsEn_n(i),
         dataOut => adcSEnSync(i));
   end generate;

   Synchronizer_Resync : entity work.Synchronizer
       generic map (
         TPD_G    => TPD_G,
         STAGES_G => 2)
       port map (
         clk     => byteClk,
         rst     => adcBitRst,
         dataIn  => axilR.resync,
         dataOut => resync);
   -------------------------------------------------------------------------------------------------
   -- AXIL Interface
   -------------------------------------------------------------------------------------------------
   axilComb : process (axilR, axilReadMaster, axilRst, axilWriteMaster, curDelayData,
                       debugDataTmp, debugDataValid, lockedFallCount, lockedSync, idelayCtrlRdy, tenbData) is
      variable v        : AxilRegType;
      variable axilEp   : AxiLiteEndpointType;
      variable local10b : slv10Array(63 downto 0);
   begin
      v := axilR;

      v.dataDelaySet        := (others => '0');
      v.axilReadSlave.rdata := (others => '0');

      --updates ctrl signal status
      v.idelayCtrlRdy := idelayCtrlRdy;

      -- Store last two samples read from ADC
      if (debugDataValid = '1' and axilR.freezeDebug = '0') then
         v.readoutDebug0 := debugDataTmp;
         v.readoutDebug1 := axilR.readoutDebug0;
      end if;

      axiSlaveWaitTxn(axilEp, axilWriteMaster, axilReadMaster, v.axilWriteSlave, v.axilReadSlave);

      axiSlaveRegister (axilEp, X"00", 0, v.adcStreamsEn_n);
      axiSlaveRegister (axilEp, X"04", 0, v.resync);
      
      -- Up to 8 delay registers
      -- Write delay values to IDELAY primatives
      -- All writes go to same r.delay register,
      for i in 0 to NUM_CHANNELS_G-1 loop
         axiSlaveRegister(axilEp, X"10"+toSlv((i*4), 8), 0, v.delay(i));
         axiSlaveRegister(axilEp, X"10"+toSlv((i*4), 8), 9, v.dataDelaySet(i), '1');
      end loop;

      -- Override read from r.delay and use curDealy output from delay primative instead
      for i in 0 to NUM_CHANNELS_G-1 loop
         axiSlaveRegisterR(axilEp, X"10"+toSlv((i*4), 8), 0, curDelayData(i));
      end loop;


      -- Debug output to see how many times the shift has needed a relock
      for i in 0 to NUM_CHANNELS_G-1 loop
        axiSlaveRegisterR(axilEp, X"30"+toSlv((i*4), 8), 0, lockedFallCount(i));
        axiSlaveRegisterR(axilEp, X"30"+toSlv((i*4), 8), 16, lockedSync(i));     
      end loop;
      axiSlaveRegister(axilEp, X"50", 0, v.lockedCountRst);

      -- Debug registers. Output the last 2 words received
      for i in 0 to NUM_CHANNELS_G-1 loop
         axiSlaveRegisterR(axilEp, X"80"+toSlv((i*4), 8), 0, axilR.readoutDebug0(i));
         axiSlaveRegisterR(axilEp, X"80"+toSlv((i*4), 8), 16, axilR.readoutDebug1(i));
      end loop;

      axiSlaveRegister(axilEp, X"A0", 0, v.freezeDebug);

      for i in 0 to NUM_CHANNELS_G-1 loop
        local10b := tenbData(i);
        for j in 0 to 63 loop
          axiSlaveRegisterR(axilEp, X"100"+toSlv((i*64*4+j*4),12), 0,  local10b(j));
        end loop;  -- j
      end loop;
      

      axiSlaveDefault(axilEp, v.axilWriteSlave, v.axilReadSlave, AXI_RESP_DECERR_C);

      if (axilRst = '1') then
         v := AXIL_REG_INIT_C;
      end if;

      axilRin        <= v;
      axilWriteSlave <= axilR.axilWriteSlave;
      axilReadSlave  <= axilR.axilReadSlave;
      adcStreamsEn_n <= axilR.adcStreamsEn_n;

   end process;

   axilSeq : process (axilClk) is
   begin
      if (rising_edge(axilClk)) then
         axilR <= axilRin after TPD_G;
      end if;
   end process axilSeq;

   --------------------------------
   -- Data Input, 8 channels
   --------------------------------
   GenData : for i in NUM_CHANNELS_G-1 downto 0 generate
     

      U_DATA_DESERIALIZER : entity work.Hr16bAdcDeserializer
      generic map (
        TPD_G             => TPD_G,
        NUM_CHANNELS_G    => NUM_CHANNELS_G,
        IODELAY_GROUP_G   => "DEFAULT_GROUP",
        IDELAYCTRL_FREQ_G => 300.0,
        DEFAULT_DELAY_G   => (others => '0'),
        FRAME_PATTERN_G   => "00000000001111111111",
        ADC_INVERT_CH_G   => ADC_INVERT_CH_G(i),
        BIT_REV_G         => '0',
        MSB_LSB_G         => '0')
      port map (
        adcClkRst     => adcBitRst,
        dClk          => bitClk,                         -- Data clock
        dClkDiv4      => deserClk,
        dClkDiv5      => byteClk,
        sDataP        => adcSerial.chP(i),                       
        sDataN        => adcSerial.chN(i),
        loadDelay     => axilR.dataDelaySet(i),
        delay         => axilR.delay(i),
        delayValueOut => curDelayData(i),
        bitSlip       => adcR.slip(i),
        gearboxOffset => adcR.gearboxOffset(i),
        dataValid     => dataValid(i),
        tenbData      => tenbData(i),
        pixData       => adcData(i)
        );
   end generate;

   -------------------------------------------------------------------------------------------------
   -- ADC Bit Clocked Logic
   -------------------------------------------------------------------------------------------------
   adcComb : process (adcData, dataValid, adcR, resync, adcSEnSync) is
      variable v : AdcRegType;
   begin
      v := adcR;

      -------------------------------------------------------------------------
      -- define data aligned logic
      -------------------------------------------------------------------------
      for i in NUM_CHANNELS_G-1 downto 0 loop
        if dataValid(i) = '1' then
          if adcData(i) = IDLE_PATTERN_1_C or adcData(i) = IDLE_PATTERN_2_C or adcData(i) = FRAME_PATTERN_C then
            v.idleWord(i) := '1';
          else
            v.idleWord(i) := '0';
          end if;
        end if;
      end loop;

      ----------------------------------------------------------------------------------------------
      -- Slip bits until correct alignment seen
      ----------------------------------------------------------------------------------------------
      for i in NUM_CHANNELS_G-1 downto 0 loop
        if (adcR.count(i) = 0) then
          if (adcR.idleWord(i) = '1') then
            v.lockedCounter(i) := adcR.lockedCounter(i) + 1;           
          else
            v.lockedCounter(i) := (others => '0');
            v.slip(i)   := adcR.slip(i) + 1;       
            -- increments the gearbox
            if adcR.slip(i) = 0 then
              v.gearBoxOffset(i) := adcR.gearBoxOffset(i) + 1;
            end if;
          end if;
        end if;
        -- checks for lock, once locked keeps states until reset is requested
        if adcR.lockedCounter(i) >= LOCKED_COUNTER_VALUE_C then
          v.locked(i) := '1';
        end if;

        -- Implements the counter while lock is  not found
        if adcR.locked(i) = '1' then
          v.count(i) := (others => '1');
        else
          v.count(i) := adcR.count(i) + 1;  
        end if;
      end loop;
      
      ----------------------------------------------------------------------------------------------
      -- Write data to fifos
      ----------------------------------------------------------------------------------------------
      for i in NUM_CHANNELS_G-1 downto 0 loop
         if (adcR.locked(i) = '1' and adcSEnSync(i) = '0') then
            -- Locked, output adc data
            v.fifoWrData(i) := adcData(i);
         else
            -- Not locked
            v.fifoWrData(i) := (others => '1');  
         end if;
      end loop;

      -------------------------------------------------------------------------
      -- data valid flag
      -------------------------------------------------------------------------
      if dataValid = VECTOR_OF_ZEROS_C(NUM_CHANNELS_G-1 downto 0) then
        v.dataValidAll := '0';
      else
        v.dataValidAll := '1';
      end if;

      -------------------------------------------------------------------------
      -- reset state variables whenever resync requested
      -------------------------------------------------------------------------
      if resync = '1' then
         v.locked := (others=>'0');       
      end if;

      adcRin <= v;

   end process adcComb;

   adcSeq : process (byteClk, adcBitRst) is
   begin
      if (adcBitRst = '1') then
         adcR <= ADC_REG_INIT_C after TPD_G;
      elsif (rising_edge(byteClk)) then
         adcR <= adcRin after TPD_G;
      end if;
   end process adcSeq;

   -- Flatten fifoWrData onto fifoDataIn for FIFO
   -- Regroup fifoDataOut by channel into fifoDataTmp
   -- Format fifoDataTmp into AxiStream channels
   glue : for i in NUM_CHANNELS_G-1 downto 0 generate
      fifoDataIn(i*NUM_BITS_C+(NUM_BITS_C-1) downto i*NUM_BITS_C)  <= adcR.fifoWrData(i);
      fifoDataTmp(i)                   <= fifoDataOut(i*NUM_BITS_C+(NUM_BITS_C-1) downto i*NUM_BITS_C);
      debugDataTmp(i)                  <= debugDataOut(i*NUM_BITS_C+(NUM_BITS_C-1) downto i*NUM_BITS_C);
      adcStreams(i).tdata((NUM_BITS_C-1) downto 0) <= fifoDataTmp(i);
      adcStreams(i).tDest              <= toSlv(i, 8);
      adcStreams(i).tValid             <= fifoDataValid;
   end generate;

   -- Single fifo to synchronize adc data to the Stream clock
   U_DataFifo : entity work.SynchronizerFifo
      generic map (
         TPD_G        => TPD_G,
         BRAM_EN_G    => false,
         DATA_WIDTH_G => NUM_CHANNELS_G*NUM_BITS_C,
         ADDR_WIDTH_G => 4,
         INIT_G       => "0")
      port map (
         rst    => adcBitRst,
         wr_clk => byteClk,
         wr_en  => adcR.dataValidAll,
         din    => fifoDataIn,
         rd_clk => adcStreamClk,
         rd_en  => fifoDataValid,
         valid  => fifoDataValid,
         dout   => fifoDataOut);

   U_DataFifoDebug : entity work.SynchronizerFifo
      generic map (
         TPD_G        => TPD_G,
         BRAM_EN_G    => false,
         DATA_WIDTH_G => NUM_CHANNELS_G*NUM_BITS_C,
         ADDR_WIDTH_G => 4,
         INIT_G       => "0")
      port map (
         rst    => adcBitRst,
         wr_clk => byteClk,
         wr_en  => fifoDataValid,  
         din    => fifoDataIn,
         rd_clk => axilClk,
         rd_en  => debugDataValid,
         valid  => debugDataValid,
         dout   => debugDataOut);
end rtl;

