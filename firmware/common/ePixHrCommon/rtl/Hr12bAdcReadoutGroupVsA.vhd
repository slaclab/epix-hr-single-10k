-------------------------------------------------------------------------------
-- File       : Ad9249ReadoutGroup.vhd
-- Company    : SLAC National Accelerator Laboratory
-------------------------------------------------------------------------------
-- Description:
-- ADC Readout Controller
-- Receives ADC Data from an SLAC 12b14b data stream.
-- Designed specifically for Xilinx Ultrascale series FPGAs
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
use ieee.std_logic_arith.all;
use ieee.std_logic_unsigned.all;

library surf;
use surf.StdRtlPkg.all;
use surf.AxiLitePkg.all;
use surf.AxiStreamPkg.all;

use work.HrAdcPkg.all;

library UNISIM;
use UNISIM.vcomponents.all;

entity Hr12bAdcReadoutGroupVsA is
   generic (
      TPD_G             : time                 := 1 ns;
      SIMULATION_G      : boolean              := false;
      NUM_CHANNELS_G    : natural range 1 to 8 := 2;
      IODELAY_GROUP_G   : string               := "DEFAULT_GROUP";
      IDELAYCTRL_FREQ_G : real                 := 200.0;
      DELAY_VALUE_G     : natural              := 1250;
      DEFAULT_DELAY_G   : slv(8 downto 0)      := (others => '0');
      ADC_INVERT_CH_G   : slv(7 downto 0)      := "00000000");
   port (
      -- Master system clock, 125Mhz
      axilClk           : in sl;
      axilRst           : in sl;

      -- Axi Interface
      axilWriteMaster   : in  AxiLiteWriteMasterType;
      axilWriteSlave    : out AxiLiteWriteSlaveType;
      axilReadMaster    : in  AxiLiteReadMasterType;
      axilReadSlave     : out AxiLiteReadSlaveType;

      -- common clocks to all deserializers
      bitClk            : in sl;
      byteClk           : in sl;          -- bit clk divided by 7
      deserClk          : in sl;          -- deserializer clk DDR, 8 bits => bit
                                          -- clk divided by 4    

      -- Reset for adc deserializer
      adcClkRst         : in sl;      

      -- Serial Data from ADC
      adcSerial         : in HrAdcSerialGroupType;

      -- Deserialized ADC Data
      adcStreamClk      : in  sl;
      adcStreams        : out AxiStreamMasterArray(NUM_CHANNELS_G-1 downto 0) := (others => axiStreamMasterInit((false, 2, 8, 0, TKEEP_NORMAL_C, 0, TUSER_NORMAL_C)));
      adcStreamsEn_n    : out slv(NUM_CHANNELS_G-1 downto 0);
      monitoringSig     : out slv(NUM_CHANNELS_G-1 downto 0)
      );
end Hr12bAdcReadoutGroupVsA;

-- Define architecture
architecture rtl of Hr12bAdcReadoutGroupVsA is

  attribute keep : string;
  
  constant NUM_BITS_C       : natural          := 14;
  constant FRAME_PATTERN_C : slv(13 downto 0) := "00000001111111";
  constant IDLE_PATTERN_1_C : slv((NUM_BITS_C-1) downto 0) := "00101111111000"; --x0bf8
  constant IDLE_PATTERN_2_C : slv((NUM_BITS_C-1) downto 0) := "11010000000111"; --x3407
  constant IDLE_PATTERN_3_C : slv((NUM_BITS_C-1) downto 0) := "00011111110100"; --x0bf8
  constant IDLE_PATTERN_4_C : slv((NUM_BITS_C-1) downto 0) := "11100000001011"; --x3407
  constant LOCKED_COUNTER_VALUE_C : slv(15 downto 0) := ite(SIMULATION_G, x"0100", x"1000");
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
      frameDelaySet  : sl;
      freezeDebug    : sl;
      readoutDebug0  : slv16Array(9 downto 0);
      readoutDebug1  : slv16Array(9 downto 0);
      adcStreamsEn_n : slv(NUM_CHANNELS_G-1 downto 0);
      lockedCountRst : sl;
      restartBERT    : sl;
   end record;

   constant AXIL_REG_INIT_C : AxilRegType := (
      resync          => '0',
      axilWriteSlave  => AXI_LITE_WRITE_SLAVE_INIT_C,
      axilReadSlave   => AXI_LITE_READ_SLAVE_INIT_C,
      delay           => (others => DEFAULT_DELAY_G),
      dataDelaySet    => (others => '1'),
      frameDelaySet   => '1',
      freezeDebug     => '0',
      readoutDebug0   => (others => (others => '0')),
      readoutDebug1   => (others => (others => '0')),
      adcStreamsEn_n  => (others => '0'),
      lockedCountRst  => '0',
      restartBERT     => '0'
      );

   signal lockedSync      : slv(NUM_CHANNELS_G-1 downto 0);
   signal lockedFallCount : slv16Array(NUM_CHANNELS_G-1 downto 0);

   signal axilR   : AxilRegType := AXIL_REG_INIT_C;
   signal axilRin : AxilRegType;

   -------------------------------------------------------------------------------------------------
   -- ADC Readout Clocked Registers
   -------------------------------------------------------------------------------------------------
   type AdcRegType is record
      slip           : Slv4Array(NUM_CHANNELS_G-1 downto 0); 
      count          : Slv5Array(NUM_CHANNELS_G-1 downto 0);
      lockedCounter  : Slv16Array(NUM_CHANNELS_G-1 downto 0);
      gearBoxOffset  : Slv3Array(NUM_CHANNELS_G-1 downto 0); 
      idleWord       : slv(NUM_CHANNELS_G-1 downto 0);
      locked         : slv(NUM_CHANNELS_G-1 downto 0);
      dataValidAll   : sl;
      fifoWrData     : Slv16Array(NUM_CHANNELS_G-1 downto 0);
      countBertEn    : slv(NUM_CHANNELS_G-1 downto 0);
      counterBERT    : Slv44Array(NUM_CHANNELS_G-1 downto 0);
   end record;

   constant ADC_REG_INIT_C : AdcRegType := (
      slip           => (others => (others => '0')),
      count          => (others => (others => '0')),
      lockedCounter  => (others => (others => '0')),
      gearBoxOffset  => (others => (others => '0')),
      idleWord       => (others => '0'),
      locked         => (others => '0'),
      dataValidAll   => '0',
      fifoWrData     => (others => (others => '0')),
      countBertEn    => (others => '0'),
      counterBERT    => (others => (others => '0'))
      );

   signal adcR   : AdcRegType := ADC_REG_INIT_C;
   signal adcRin : AdcRegType;


   -- Local Signals
   signal dataValid       : slv(NUM_CHANNELS_G-1 downto 0);
   signal resync          : sl;
   signal adcSEnSync      : slv(NUM_CHANNELS_G-1 downto 0);
   signal restartBERTsync : sl;
   signal counterBERTsync : Slv44Array(NUM_CHANNELS_G-1 downto 0);

   type Slv14bData is array (natural range<>) of slv14Array(7 downto 0);
   signal debugData       : Slv14bData(NUM_CHANNELS_G-1 downto 0);

   signal adcFramePad   : sl;
   signal adcFrame      : slv(13 downto 0);
   signal adcFrameSync  : slv(13 downto 0);
   signal adcDataPadOut : slv(NUM_CHANNELS_G-1 downto 0);
   signal adcDataPad    : slv(NUM_CHANNELS_G-1 downto 0);
   signal adcData       : Slv14Array(NUM_CHANNELS_G-1 downto 0);
   signal adcBitRst     : sl;

   signal curDelayFrame : slv(8 downto 0);
   signal curDelayData  : slv9Array(NUM_CHANNELS_G-1 downto 0);

   signal fifoDataValid : sl;
   signal fifoDataOut   : slv(NUM_CHANNELS_G*16-1 downto 0);
   signal fifoDataIn    : slv(NUM_CHANNELS_G*16-1 downto 0);
   signal fifoDataTmp   : slv16Array(NUM_CHANNELS_G-1 downto 0);

   signal debugDataValid : sl;
   signal debugDataOut   : slv(NUM_CHANNELS_G*16-1 downto 0);
   signal debugDataTmp   : slv16Array(NUM_CHANNELS_G-1 downto 0);

begin

  monitoringSig <= adcR.idleWord;
  
   -- Regional clock reset
   ADC_BITCLK_RST_SYNC : entity surf.RstSync
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
     SynchronizerOneShotCnt_1 : entity surf.SynchronizerOneShotCnt
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

     Synchronizer_1 : entity surf.Synchronizer
       generic map (
         TPD_G    => TPD_G,
         STAGES_G => 2)
       port map (
         clk     => axilClk,
         rst     => axilRst,
         dataIn  => adcR.locked(i),
         dataOut => lockedSync(i));

     SynchronizerStrmEn : entity surf.Synchronizer
       generic map (
         TPD_G    => TPD_G,
         STAGES_G => 2)
       port map (
         clk     => byteClk,
         rst     => adcBitRst,
         dataIn  => axilR.adcStreamsEn_n(i),
         dataOut => adcSEnSync(i));

     SynchronizerCounterBERT : entity surf.SynchronizerVector 
       generic map(
         TPD_G          => TPD_G,
         STAGES_G       => 2,
         WIDTH_G        => 44)
       port map(
         clk     => axilClk,
         rst     => axilRst,
         dataIn  => adcR.counterBERT(i),
         dataOut => counterBERTsync(i)); 
     
   end generate;

   Synchronizer_Resync : entity surf.Synchronizer
     generic map (
       TPD_G    => TPD_G,
       STAGES_G => 2)
     port map (
       clk     => byteClk,
       rst     => adcBitRst,
       dataIn  => axilR.resync,
       dataOut => resync);

  Synchronizer_restartBertSync : entity surf.Synchronizer
     generic map (
       TPD_G    => TPD_G,
       STAGES_G => 2)
     port map (
       clk     => byteClk,
       rst     => adcBitRst,
       dataIn  => axilR.restartBERT,
       dataOut => restartBERTsync);
   
   -------------------------------------------------------------------------------------------------
   -- AXIL Interface
   -------------------------------------------------------------------------------------------------
   axilComb : process (axilR, axilReadMaster, axilRst, axilWriteMaster, curDelayData,
                       curDelayFrame, debugDataTmp, debugDataValid, lockedFallCount, lockedSync, debugData,
                       counterBERTsync) is
      variable v      : AxilRegType;
      variable axilEp : AxiLiteEndpointType;
      variable localDebugData : slv14Array(7 downto 0);
   begin
      v := axilR;

      v.dataDelaySet        := (others => '0');
      v.axilReadSlave.rdata := (others => '0');

      -- Store last two samples read from ADC
      if (debugDataValid = '1' and axilR.freezeDebug = '0') then
         v.readoutDebug0(0) := debugDataTmp(0);
         v.readoutDebug1(0) := debugDataTmp(1);
         for i in 1 to 9 loop
           v.readoutDebug0(i) := axilR.readoutDebug0(i-1);
           v.readoutDebug1(i) := axilR.readoutDebug1(i-1);
         end loop;
      end if;

      axiSlaveWaitTxn(axilEp, axilWriteMaster, axilReadMaster, v.axilWriteSlave, v.axilReadSlave);

      axiSlaveRegister (axilEp, X"00", 0, v.adcStreamsEn_n);
      axiSlaveRegister (axilEp, X"04", 0, v.resync);

      -- Up to 8 delay registers
      -- Write delay values to IDELAY primatives
      -- All writes go to same r.delay register,
      -- dataDelaySet(i) or frameDelaySet enables the primative write
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
        axiSlaveRegisterR(axilEp, X"30"+toSlv((i*4), 8), 0,  lockedFallCount(i));
        axiSlaveRegisterR(axilEp, X"30"+toSlv((i*4), 8), 16, lockedSync(i));
      end loop;        
      axiSlaveRegister (axilEp, X"50", 0, v.lockedCountRst);

      -- Debug registers. Output the last 2 words received
      --for i in 0 to NUM_CHANNELS_G-1 loop     i
         axiSlaveRegisterR(axilEp, X"80"+toSlv((0*4), 8), 0, axilR.readoutDebug0(0));
         axiSlaveRegisterR(axilEp, X"80"+toSlv((0*4), 8), 16, axilR.readoutDebug0(1));
         axiSlaveRegisterR(axilEp, X"80"+toSlv((1*4), 8), 0, axilR.readoutDebug1(0));
         axiSlaveRegisterR(axilEp, X"80"+toSlv((1*4), 8), 16, axilR.readoutDebug1(1));
      --end loop;

      axiSlaveRegister(axilEp, X"A0", 0, v.freezeDebug);
      axiSlaveRegister(axilEp, X"A0", 1, v.restartBERT);
      for i in 0 to NUM_CHANNELS_G-1 loop
        axiSlaveRegisterR(axilEp, X"A4"+toSlv((i*8),8), 0,  counterBERTsync(i));
      end loop;

      --for i in 0 to NUM_CHANNELS_G-1 loop
      --  localDebugData := debugData(i);
      --  for j in 0 to 7 loop
      --    axiSlaveRegisterR(axilEp, X"100"+toSlv((i*64*4+j*4),12), 0,  localDebugData(j));
      --  end loop;  -- j
      --end loop;
      for j in 2 to 9 loop
          axiSlaveRegisterR(axilEp, X"100"+toSlv((0*64*4+(j-2)*4),12), 0,  axilR.readoutDebug0(j));
          axiSlaveRegisterR(axilEp, X"100"+toSlv((1*64*4+(j-2)*4),12), 0,  axilR.readoutDebug1(j));
      end loop;  -- j

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
   -- Data Input, upto 8 channels
   --------------------------------
   GenData : for i in NUM_CHANNELS_G-1 downto 0 generate
      signal dataDelaySet : slv(NUM_CHANNELS_G-1 downto 0);
      signal dataDelay    : slv9Array(NUM_CHANNELS_G-1 downto 0);
   begin  
      U_DATA_DESERIALIZER : entity work.Hr12bAdcDeserializerUSVsA
      generic map (
        TPD_G             => TPD_G,
        NUM_CHANNELS_G    => NUM_CHANNELS_G,
        IODELAY_GROUP_G   => "DEFAULT_GROUP",
        IDELAYCTRL_FREQ_G => 350.0,
        DEFAULT_DELAY_G   => (others => '0'),
        FRAME_PATTERN_G   => FRAME_PATTERN_C,
        ADC_INVERT_CH_G   => ADC_INVERT_CH_G(i),
        BIT_REV_G         => '0',
        MSB_LSB_G         => '0')
      port map (
        adcClkRst     => adcBitRst,
        dClk          => bitClk,                         -- Data clock
        dClkDiv4      => deserClk,
        dClkDiv7      => byteClk,
        sDataP        => adcSerial.chP(i),                       -- Frame clock
        sDataN        => adcSerial.chN(i),
        loadDelay     => dataDelaySet(i),
        delay         => dataDelay(i),
        delayValueOut => curDelayData(i),
        bitSlip       => adcR.slip(i),
        gearboxOffset => adcR.gearboxOffset(i),
        dataValid     => dataValid(i),
        debugData     => debugData(i),
        adcData       => adcData(i)
        );

      U_DataDlyFifo : entity surf.SynchronizerFifo
         generic map (
            TPD_G        => TPD_G,
            MEMORY_TYPE_G=> "distributed",
            DATA_WIDTH_G => 9,
            ADDR_WIDTH_G => 4,
            INIT_G       => "0")
         port map (
            rst    => axilRst,
            wr_clk => axilClk,
            wr_en  => axilR.dataDelaySet(i),
            din    => axilR.delay(i),
            rd_clk => deserClk,
            rd_en  => '1',
            valid  => dataDelaySet(i),
            dout   => dataDelay(i)
         );         
   end generate;

   -------------------------------------------------------------------------------------------------
   -- ADC Byte Clocked Logic
   -------------------------------------------------------------------------------------------------
   adcComb : process (adcData, adcFrame, adcR, dataValid, adcSEnSync, resync, restartBERTsync) is
      variable v : AdcRegType;
   begin
      v := adcR;      

      -------------------------------------------------------------------------
      -- define data aligned logic
      -------------------------------------------------------------------------
      for i in NUM_CHANNELS_G-1 downto 0 loop
        if dataValid(i) = '1' then
          if adcData(i) = IDLE_PATTERN_1_C or adcData(i) = IDLE_PATTERN_2_C or adcData(i) = IDLE_PATTERN_3_C or adcData(i) = IDLE_PATTERN_4_C or adcData(i) = FRAME_PATTERN_C then
            v.idleWord(i) := '1';
          else
            v.idleWord(i) := '0';
          end if;
        end if;
      end loop;

      -------------------------------------------------------------------------
      -- BERT counter based on idleWord
      -------------------------------------------------------------------------
      for i in NUM_CHANNELS_G-1 downto 0 loop
        if restartBERTsync = '1' then
          v.countBertEn(i) := '1';
          v.counterBERT(i) := (others => '0');
        else
          if adcR.idleWord(i) = '1' and adcR.countBertEn(i) = '1' then
            v.counterBERT(i) := adcR.counterBERT(i) + 1;            
          else
            v.countBertEn(i) := '0';
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
          if (adcR.count(i) = 29) then
            v.count(i) := (others => '0');
          else
            v.count(i) := adcR.count(i) + 1;
          end if;
        end if;
      end loop;
      
      ----------------------------------------------------------------------------------------------
      -- Write data to fifos
      ----------------------------------------------------------------------------------------------
      for i in NUM_CHANNELS_G-1 downto 0 loop
         if (adcR.locked(i) = '1' and adcSEnSync(i) = '0') then
            -- Locked, output adc data
            v.fifoWrData(i) := "00" & adcData(i);
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
      fifoDataIn(i*16+15 downto i*16)  <= adcR.fifoWrData(i);
      fifoDataTmp(i)                   <= fifoDataOut(i*16+15 downto i*16);
      debugDataTmp(i)                  <= debugDataOut(i*16+15 downto i*16);
      adcStreams(i).tdata(15 downto 0) <= fifoDataTmp(i);
      adcStreams(i).tDest              <= toSlv(i, 8);
      adcStreams(i).tValid             <= fifoDataValid;
   end generate;

   -- Single fifo to synchronize adc data to the Stream clock
   U_DataFifo : entity surf.SynchronizerFifo
      generic map (
         TPD_G        => TPD_G,
         MEMORY_TYPE_G=> "distributed",
         DATA_WIDTH_G => NUM_CHANNELS_G*16,
         ADDR_WIDTH_G => 4,
         INIT_G       => "0")
      port map (
         rst    => adcBitRst,
         wr_clk => byteClk,
         wr_en  => adcR.dataValidAll,                 --Always write data
         din    => fifoDataIn,
         rd_clk => adcStreamClk,
         rd_en  => fifoDataValid,
         valid  => fifoDataValid,
         dout   => fifoDataOut);

   U_DataFifoDebug : entity surf.SynchronizerFifo
      generic map (
         TPD_G        => TPD_G,
         MEMORY_TYPE_G=> "distributed",
         DATA_WIDTH_G => NUM_CHANNELS_G*16,
         ADDR_WIDTH_G => 4,
         INIT_G       => "0")
      port map (
         rst    => adcBitRst,
         wr_clk => byteClk,
         wr_en  => '1',                 --Always write data
         din    => fifoDataIn,
         rd_clk => axilClk,
         rd_en  => debugDataValid,
         valid  => debugDataValid,
         dout   => debugDataOut);
   
end rtl;

