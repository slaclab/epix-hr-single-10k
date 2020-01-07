-------------------------------------------------------------------------------
-- File       : Ad9249ReadoutGroup.vhd
-- Company    : SLAC National Accelerator Laboratory
-------------------------------------------------------------------------------
-- Description:
-- ADC Readout Controller
-- Receives ADC Data from an AD9592 chip.
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
      adcSerialOutP     : out sl;
      adcSerialOutN     : out sl;
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
  constant IDLE_PATTERN_3_C : slv((NUM_BITS_C-1) downto 0) := "0101010101" & "1010000011";
  constant IDLE_PATTERN_4_C : slv((NUM_BITS_C-1) downto 0) := "0101010101" & "0101111100";
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
      idelayRst      : slv(NUM_CHANNELS_G-1 downto 0);  
      iserdesRst     : slv(NUM_CHANNELS_G-1 downto 0);
      sDataOutControl: slv(2 downto 0);
      curDelayData   : slv9Array(NUM_CHANNELS_G-1 downto 0);
      restartBERT    : sl;
      counterBERT    : Slv44Array(NUM_CHANNELS_G-1 downto 0);
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
      lockedCountRst => '0',
      idelayRst      => (others => '1'),
      iserdesRst     => (others => '1'),
      sDataOutControl=> (others => '0'),
      curDelayData   => (others => (others => '0')),
      restartBERT    => '0',
      counterBERT    => (others => (others => '0')));

   signal lockedSync      : slv(NUM_CHANNELS_G-1 downto 0);
   signal lockedFallCount : slv16Array(NUM_CHANNELS_G-1 downto 0);

   signal axilR   : AxilRegType := AXIL_REG_INIT_C;
   signal axilRin : AxilRegType;

   -------------------------------------------------------------------------------------------------
   -- ADC Readout Clocked Registers
   -------------------------------------------------------------------------------------------------
   type AdcRegType is record
      slip           : Slv5Array(NUM_CHANNELS_G-1 downto 0); 
      count          : Slv6Array(NUM_CHANNELS_G-1 downto 0);
      lockedCounter  : Slv16Array(NUM_CHANNELS_G-1 downto 0);
      gearBoxOffset  : Slv2Array(NUM_CHANNELS_G-1 downto 0); 
      idleWord       : slv(NUM_CHANNELS_G-1 downto 0);
      locked         : slv(NUM_CHANNELS_G-1 downto 0);
      dataValidAll   : sl;
      fifoWrData     : Slv20Array(NUM_CHANNELS_G-1 downto 0);
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
      counterBERT    => (others => (others => '0')));

   signal adcR   : AdcRegType := ADC_REG_INIT_C;
   signal adcRin : AdcRegType;


   -- Local Signals
   signal adcBitRst        : sl;
   signal idelayRst        : slv(NUM_CHANNELS_G-1 downto 0);  
   signal iserdesRst       : slv(NUM_CHANNELS_G-1 downto 0); 
   signal adcDataPadOut    : slv(NUM_CHANNELS_G-1 downto 0);
   signal adcDataPad       : slv(NUM_CHANNELS_G-1 downto 0);
   signal adcData          : Slv20Array(NUM_CHANNELS_G-1 downto 0);
   signal dataValid        : slv(NUM_CHANNELS_G-1 downto 0);
   signal curDelayData     : slv10Array(NUM_CHANNELS_G-1 downto 0);
   signal curDelayDatasync : slv9Array(NUM_CHANNELS_G-1 downto 0);
   signal resync           : sl;
   signal adcSEnSync       : slv(NUM_CHANNELS_G-1 downto 0);
   signal restartBERTsync  : sl;
   signal counterBERTsync  : Slv44Array(NUM_CHANNELS_G-1 downto 0);
   signal sDataOutP        : slv(NUM_CHANNELS_G-1 downto 0);
   signal sDataOutN        : slv(NUM_CHANNELS_G-1 downto 0);
   type Slv10bData is array (natural range<>) of slv10Array(7 downto 0);
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

   process(axilR,sDataOutP,sDataOutN)
      variable index : natural;
   begin
      index := conv_integer(axilR.sDataOutControl);
      if (index >= NUM_CHANNELS_G) or (index > 5) then
         adcSerialOutP <= '0';
         adcSerialOutN <= '0';
      else
         adcSerialOutP <= sDataOutP(index);
         adcSerialOutN <= sDataOutN(index);         
      end if;
   end process;

--  adcSerialOutN <=
--    sDataOutN(0) when axilR.sDataOutControl ="000" else
--    sDataOutN(1) when axilR.sDataOutControl ="001" else
--    sDataOutN(2) when axilR.sDataOutControl ="010" else
--    sDataOutN(3) when axilR.sDataOutControl ="011" else
--    sDataOutN(4) when axilR.sDataOutControl ="100" else
--    sDataOutN(5) when axilR.sDataOutControl ="101" else
--    '0';

--  adcSerialOutP <=
--    sDataOutP(0) when axilR.sDataOutControl ="000" else
--    sDataOutP(1) when axilR.sDataOutControl ="001" else
--    sDataOutP(2) when axilR.sDataOutControl ="010" else
--    sDataOutP(3) when axilR.sDataOutControl ="011" else
--    sDataOutP(4) when axilR.sDataOutControl ="100" else
--    sDataOutP(5) when axilR.sDataOutControl ="101" else
--    '0';
  
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

     SynchronizerCurDelayData : entity surf.SynchronizerVector 
       generic map(
         TPD_G          => TPD_G,
         STAGES_G       => 2,
         WIDTH_G        => 9)
       port map(
         clk     => axilClk,
         rst     => axilRst,
         dataIn  => curDelayData(i)(9 downto 1),
         dataOut => curDelayDatasync(i)); 

     Synchronizer_idelay_i : entity surf.Synchronizer
       generic map (
         TPD_G    => TPD_G,
         STAGES_G => 2)
       port map (
         clk     => bitClk,
         rst     => adcBitRst,
         dataIn  => axilR.idelayRst(i),
         dataOut => idelayRst(i));

     Synchronizer_iserdes_i : entity surf.Synchronizer
       generic map (
         TPD_G    => TPD_G,
         STAGES_G => 2)
       port map (
         clk     => bitClk,
         rst     => adcBitRst,
         dataIn  => axilR.iserdesRst(i),
         dataOut => iserdesRst(i));     
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
   axilComb : process (axilR, axilReadMaster, axilRst, axilWriteMaster, curDelayDatasync,
                       debugDataTmp, debugDataValid, lockedFallCount, lockedSync, idelayCtrlRdy, tenbData,
                       counterBERTsync) is
      variable v        : AxilRegType;
      variable axilEp   : AxiLiteEndpointType;
      variable local10b : slv10Array(7 downto 0);
   begin
      v := axilR;

      v.dataDelaySet        := (others => '0');
      --v.axilReadSlave.rdata := (others => '0');

      --updates ctrl signal status
      v.idelayCtrlRdy   := idelayCtrlRdy;
      v.counterBERT     := counterBERTsync;
      v.curDelayData    := curDelayDatasync;

      -- Store last two samples read from ADC
      for i in 0 to NUM_CHANNELS_G-1 loop
        if (debugDataValid = '1' and axilR.freezeDebug = '0') then
          v.readoutDebug0(i) := debugDataTmp(i);
        end if;
      end loop;
      v.readoutDebug1 := axilR.readoutDebug0;

      axiSlaveWaitTxn(axilEp, axilWriteMaster, axilReadMaster, v.axilWriteSlave, v.axilReadSlave);

      axiSlaveRegister (axilEp, X"000", 0, v.adcStreamsEn_n);
      axiSlaveRegister (axilEp, X"004", 0, v.resync);
      axiSlaveRegister (axilEp, X"004", 1, v.sDataOutControl);
      axiSlaveRegister (axilEp, X"008", 0, v.idelayRst);
      axiSlaveRegister (axilEp, X"00C", 0, v.iserdesRst);
      
      -- Up to 8 delay registers
      -- Write delay values to IDELAY primatives
      -- All writes go to same r.delay register,
      for i in 0 to NUM_CHANNELS_G-1 loop
         axiSlaveRegister(axilEp, X"010"+toSlv((i*4), 8), 0, v.delay(i));
         axiSlaveRegister(axilEp, X"010"+toSlv((i*4), 8), 9, v.dataDelaySet(i), '1');
      end loop;

      -- Override read from r.delay and use curDealy output from delay primative instead
      for i in 0 to NUM_CHANNELS_G-1 loop
         axiSlaveRegisterR(axilEp, X"010"+toSlv((i*4), 8), 0, axilR.curDelayData(i));
      end loop;


      -- Debug output to see how many times the shift has needed a relock
      for i in 0 to NUM_CHANNELS_G-1 loop
        axiSlaveRegisterR(axilEp, X"030"+toSlv((i*4), 8), 0, lockedFallCount(i));
        axiSlaveRegisterR(axilEp, X"030"+toSlv((i*4), 8), 16, lockedSync(i));     
      end loop;
      axiSlaveRegister(axilEp, X"050", 0, v.lockedCountRst);

      -- Debug registers. Output the last 2 words received
      for i in 0 to NUM_CHANNELS_G-1 loop
        axiSlaveRegisterR(axilEp, X"080"+toSlv((2*i*4), 8),   0, axilR.readoutDebug0(i));
        axiSlaveRegisterR(axilEp, X"080"+toSlv((2*i*4)+4, 8), 0, axilR.readoutDebug1(i));
      end loop;
      

      axiSlaveRegister(axilEp, X"100", 0, v.freezeDebug);
      axiSlaveRegister(axilEp, X"100", 1, v.restartBERT);
      for i in 0 to NUM_CHANNELS_G-1 loop
        axiSlaveRegisterR(axilEp, X"104"+toSlv((i*8),8), 0,  axilR.counterBERT(i));
      end loop;
      
      for i in 0 to NUM_CHANNELS_G-1 loop
        local10b := tenbData(i);
        for j in 0 to 1 loop
          axiSlaveRegisterR(axilEp, X"200"+toSlv((i*64*4+j*4),12), 0,  local10b(j));
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
      signal dataDelaySet : slv(NUM_CHANNELS_G-1 downto 0);
      signal dataDelay    : slv9Array(NUM_CHANNELS_G-1 downto 0);     
   begin
      U_DATA_DESERIALIZER : entity work.Hr16bAdcDeserializer
      generic map (
        TPD_G             => TPD_G,
        NUM_CHANNELS_G    => NUM_CHANNELS_G,
        IODELAY_GROUP_G   => "DEFAULT_GROUP",
        IDELAYCTRL_FREQ_G => 200.0,
        DEFAULT_DELAY_G   => (others => '0'),
        FRAME_PATTERN_G   => "00000000001111111111",
        ADC_INVERT_CH_G   => ADC_INVERT_CH_G(i),
        BIT_REV_G         => '0',
        MSB_LSB_G         => '0')
      port map (
        adcClkRst     => adcBitRst,
        idelayRst     => idelayRst(i),
        iserdesRst    => iserdesRst(i),
        dClk          => bitClk,                         -- Data clock
        dClkDiv4      => deserClk,
        dClkDiv5      => byteClk,
        sDataP        => adcSerial.chP(i),                       
        sDataN        => adcSerial.chN(i),
        sDataOutP     => sDataOutP(i),
        sDataOutN     => sDataOutN(i),
        loadDelay     => dataDelaySet(i),
        delay         => dataDelay(i),
        delayValueOut => curDelayData(i),
        bitSlip       => adcR.slip(i),
        gearboxOffset => adcR.gearboxOffset(i),
        dataValid     => dataValid(i),
        tenbData      => tenbData(i),
        pixData       => adcData(i)
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
   -- ADC Bit Clocked Logic
   -------------------------------------------------------------------------------------------------
   adcComb : process (adcData, dataValid, adcR, resync, adcSEnSync, restartBERTsync) is
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
      -- PSEUDO BERT counter based on idleWord
      -------------------------------------------------------------------------
      for i in NUM_CHANNELS_G-1 downto 0 loop
        if restartBERTsync = '1' then
          --v.countBertEn(i) := '1';
          v.counterBERT(i) := (others => '0');
        else
          if adcR.idleWord(i) = '0' then -- and adcR.countBertEn(i) = '1' then
            v.counterBERT(i) := adcR.counterBERT(i) + 1;            
          else
            --v.countBertEn(i) := '0';
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
   U_DataFifo : entity surf.SynchronizerFifo
      generic map (
         TPD_G        => TPD_G,
         MEMORY_TYPE_G=> "distributed",
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

   U_DataFifoDebug : entity surf.SynchronizerFifo
      generic map (
         TPD_G        => TPD_G,
         MEMORY_TYPE_G=> "distributed",
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

