-------------------------------------------------------------------------------
-- File       : cryo_tb.vhd
-- Company    : SLAC National Accelerator Laboratory
-------------------------------------------------------------------------------
-- Description: 
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
use ieee.std_logic_unsigned.all;
use ieee.std_logic_textio.all;
use ieee.std_logic_arith.all;
use ieee.numeric_std.all;

library STD;
use STD.textio.all;      

library surf;
use surf.StdRtlPkg.all;
use surf.AxiStreamPkg.all;
use surf.AxiLitePkg.all;
use surf.AxiPkg.all;
use surf.Pgp2bPkg.all;
use surf.SsiPkg.all;
use surf.SsiCmdMasterPkg.all;
use surf.Code8b10bPkg.all;

library epix_hr_core;
use epix_hr_core.EpixHrCorePkg.all;

use work.HrAdcPkg.all;
use work.AppPkg.all;

library unisim;
use unisim.vcomponents.all;

-------------------------------------------------------------------------------

entity cryo_tb is

end cryo_tb;

-------------------------------------------------------------------------------

architecture cryo_tb_arch of cryo_tb is

  -- component generics
  constant TPD_G : time := 1 ns;
  constant NUM_CHANNELS_G : integer := 8;
  constant IDLE_PATTERN_C : slv(11 downto 0) := x"03F";
  constant STREAMS_PER_ASIC_C : natural := 2;
  -- Axilite constants
  constant READOUT_GROUP_ID   : integer := 0;
  constant AXISTREAM_GROUP_ID : integer := 1;

  --file definitions
  constant DATA_BITS   : natural := 12;
  constant DEPTH_C     : natural := 1024;
  constant FILENAME_C  : string  := "/afs/slac.stanford.edu/u/re/ddoering/localGit/epix-hr-dev/firmware/simulations/CryoEncDec/sin.csv";
  subtype word_t  is slv(DATA_BITS - 1 downto 0);
  type    ram_t   is array(0 to DEPTH_C - 1) of word_t;

  impure function readWaveFile(FileName : STRING) return ram_t is
    file     FileHandle   : TEXT open READ_MODE is FileName;
    variable CurrentLine  : LINE;
    variable TempWord     : integer; --slv(DATA_BITS - 1 downto 0);
    variable TempWordSlv  : slv(16 - 1 downto 0);
    variable Result       : ram_t    := (others => (others => '0'));
  begin
    for i in 0 to DEPTH_C - 1 loop
      exit when endfile(FileHandle);
      readline(FileHandle, CurrentLine);
      read(CurrentLine, TempWord);
      TempWordSlv  := toSlv(TempWord, 16);
      Result(i)    := TempWordSlv(15 downto 16 - DATA_BITS);
    end loop;
    return Result;
  end function;

  -- waveform signal
  signal ramWaveform      : ram_t    := readWaveFile(FILENAME_C);
  signal ramTestWaveform  : ram_t    := readWaveFile(FILENAME_C);
  
  -- component ports
  signal sysClkRst : std_logic := '1';
  signal sysClkRst_n : sl := '0';
  signal idelayCtrlRdy : std_logic := '0';
  signal dClkP : sl := '1'; -- Data clock
  signal dClkN : sl := '0';
  signal fClkP : sl := '0'; -- Frame clock
  signal fClkN : sl := '1';
  signal sDataP : sl;                       
  signal sDataN : sl;
  signal gearboxOffset : slv(2 downto 0) := "000";
  signal bitSlip       : slv(3 downto 0) := "0101";
  -- encoder
  signal EncValidIn  : sl              := '1';
  signal EncReadyIn  : sl;
  signal EncDataIn   : slv(11 downto 0);
  signal EncDispIn   : slv(1 downto 0) := "00";
  signal EncDataKIn  : sl;
  signal EncValidOut : sl;
  signal EncReadyOut : sl              := '1';
  signal EncDataOut  : slv(13 downto 0);
  signal EncDispOut  : slv(1 downto 0);
  signal EncSof      : sl := '0';
  signal EncEof      : sl := '0';
  signal DecValidOut : sl;
  signal DecDataOut  : slv(11 downto 0);
  signal DecDataKOut : sl;
  signal DecDispOut  : slv(1 downto 0);
  signal DecCodeError: sl;
  signal DecDispError: sl;
  signal DecSof      : sl;
  signal DecEof      : sl;
  signal DecEofe     : sl;
  signal DecValid    : sl;

  signal serialDataOut : sl;


  -- axilite
  -- 0 deserializer
  -- 1 framers
  signal sAxilReadMaster  : AxiLiteReadMasterArray(1 downto 0);
  signal sAxilReadSlave   : AxiLiteReadSlaveArray(1 downto 0);
  signal sAxilWriteMaster : AxiLiteWriteMasterArray(1 downto 0);
  signal sAxilWriteSlave  : AxiLiteWriteSlaveArray(1 downto 0);
  
  --
  signal registerValue   : slv(31 downto 0);    
  signal adcSerial       : HrAdcSerialGroupType;
  signal adcStreams      : AxiStreamMasterArray(NUM_CHANNELS_G-1 downto 0);


  -- clock
  signal sysClk    : std_logic := '1';

  -- automatic test
  signal testOk : sl := '0';

  -- test trigger
  signal testTrig          : sl := '0';

  -- framer test
  signal acqNo             : slv(31 downto 0) := (others=>'0');

  -- axistream
  -- AXI Stream, one per QSFP lane (sysClk domain)
  signal mAxisMasters     : AxiStreamMasterArray(0 downto 0);
  signal mAxisSlaves      : AxiStreamSlaveArray(0 downto 0) := (others=>AXI_STREAM_SLAVE_FORCE_C); --
                                                                      --AXI_STREAM_SLAVE_INIT_C


begin  --

  sysClkRst_n <= not sysClkRst;

  U_encoder : entity work.SspEncoder12b14b 
   generic map (
     TPD_G          => TPD_G,
     RST_POLARITY_G => '1',
     RST_ASYNC_G    => false,
     AUTO_FRAME_G   => true,
     FLOW_CTRL_EN_G => false)
   port map(
      clk      => fClkP,
      rst      => sysClkRst,
      validIn  => EncValidIn,
      readyIn  => EncReadyIn,
      sof      => EncSof,
      eof      => EncEof,
      dataIn   => EncDataIn,
      validOut => EncValidOut,
      readyOut => EncReadyOut,
      dataOut  => EncDataOut);

  U_serializer :  entity work.serializerSim 
    generic map(
        g_dwidth => 14 
    )
    port map(
        clk_i     => dClkP,
        reset_n_i => sysClkRst_n,
        data_i    => EncDataOut,        -- "00"&EncDataIn, --
        data_o    => serialDataOut
    );

  -- DUT is the deserializer using iserdes3 for ultrascale devices
  -- DUT enables data synchronization based on a channel data pattern or on frame clock.

  sDataP <=     serialDataOut;
  sDataN <= not serialDataOut;

  adcSerial.fClkP <= fClkP;
  adcSerial.fClkN <= fClkN;
  adcSerial.dClkP <= dClkP;
  adcSerial.dClkN <= dClkN;

  adcSerial.chP(0) <= sDataP;
  adcSerial.chN(0) <= sDataN;
  adcSerial.chP(1) <= sDataP;
  adcSerial.chN(1) <= sDataN;
  adcSerial.chP(2) <= sDataP;
  adcSerial.chN(2) <= sDataN;
  adcSerial.chP(3) <= sDataP;
  adcSerial.chN(3) <= sDataN;
  adcSerial.chP(4) <= sDataP;
  adcSerial.chN(4) <= sDataN;
  adcSerial.chP(5) <= sDataP;
  adcSerial.chN(5) <= sDataN;
  adcSerial.chP(6) <= sDataP;
  adcSerial.chN(6) <= sDataN;
  adcSerial.chP(7) <= sDataP;
  adcSerial.chN(7) <= sDataN;

  DUT0: entity work.HrAdcReadoutGroup
      generic map (
        TPD_G             => TPD_G,
        NUM_CHANNELS_G    => 8,
        IODELAY_GROUP_G   => "DEFAULT_GROUP",
        XIL_DEVICE_G      => "ULTRASCALE",
        DEFAULT_DELAY_G   => (others => '0'),
        ADC_INVERT_CH_G   => "00000000")
      port map (
        -- Master system clock, 125Mhz
        axilClk => sysClk,
        axilRst => sysClkRst,

        -- Reset for adc deserializer
        adcClkRst => sysClkRst,

        -- Axi Interface
        axilWriteMaster => sAxilWriteMaster(READOUT_GROUP_ID),
        axilWriteSlave  => sAxilWriteSlave(READOUT_GROUP_ID),
        axilReadMaster  => sAxilReadMaster(READOUT_GROUP_ID),
        axilReadSlave   => sAxilReadSlave(READOUT_GROUP_ID),
 
        -- Serial Data from ADC
        adcSerial => adcSerial,

        -- Deserialized ADC Data
        adcStreamClk => fClkP,--sysClk,
        adcStreams   => adcStreams      
        );
-------------------------------------------------------------------------------
-- decodes a single stream
-------------------------------------------------------------------------------  
  U_decoder_deserdata : entity work.SspDecoder12b14b 
    generic map(
      TPD_G          => TPD_G,
      RST_POLARITY_G => '1',
      RST_ASYNC_G    => false)
   port map(
      clk       => fClkP,
      rst       => sysClkRst,
      validIn   => adcStreams(0).tValid,
      dataIn    => adcStreams(0).tData(13 downto 0),
      validOut  => DecValidOut,
      dataOut   => DecDataOut,
      valid     => DecValid,
      sof       => DecSof,
      eof       => DecEof,
      eofe      => DecEofe,
      codeError => DecCodeError,
      dispError => DecDispError);
-------------------------------------------------------------------------------
-- use the code below to bypass serializer/deserializer
-------------------------------------------------------------------------------
--  U_decoder : entity work.SspDecoder12b14b 
--    generic map(
--      TPD_G          => TPD_G,
--      RST_POLARITY_G => '1',
--      RST_ASYNC_G    => false)
--   port map(
--      clk       => fClkP,
--      rst       => sysClkRst,
--      validIn   => EncValidOut,
--      dataIn    => EncDataOut,
--      validOut  => DecValidOut,
--      dataOut   => DecDataOut,
--      valid     => DecValid,
--      sof       => DecSof,
--      eof       => DecEof,
--      eofe      => DecEofe,
--      codeError => DecCodeError,
--      dispError => DecDispError);
  
-------------------------------------------------------------------------------
-- generate stream frames
-------------------------------------------------------------------------------
-------------------------------------------------------------------------------
  U_Framers : entity work.DigitalAsicStreamAxi 
   generic map(
      TPD_G           	  => TPD_G,
      VC_NO_G             => "0000",
      LANE_NO_G           => "0000",
      ASIC_NO_G           => "000",
      STREAMS_PER_ASIC_G  => STREAMS_PER_ASIC_C,
      ASIC_DATA_G         => (32*32)-1,
      ASIC_WIDTH_G        => 32,
      ASIC_DATA_PADDING_G => "LSB",
      AXIL_ERR_RESP_G     => AXI_RESP_DECERR_C
   )
   port map( 
      -- Deserialized data port
      rxClk             => fClkP,
      rxRst             => sysClkRst,
      adcStreams        => adcStreams(1 downto 0),
      
      -- AXI lite slave port for register access
      axilClk           => sysClk,
      axilRst           => sysClkRst,
      sAxilWriteMaster  => sAxilWriteMaster(AXISTREAM_GROUP_ID),
      sAxilWriteSlave   => sAxilWriteSlave(AXISTREAM_GROUP_ID),
      sAxilReadMaster   => sAxilReadMaster(AXISTREAM_GROUP_ID),
      sAxilReadSlave    => sAxilReadSlave(AXISTREAM_GROUP_ID),
      
      -- AXI data stream output
      axisClk           => sysClk,
      axisRst           => sysClkRst,
      mAxisMaster       => mAxisMasters(0),
      mAxisSlave        => mAxisSlaves(0),
      
      -- acquisition number input to the header
      acqNo             => acqNo,
      
      -- optional readout trigger for test mode
      testTrig          => testTrig,
      errInhibit        => '0'      
   );
  
  -- clock generation
  sysClk <= not sysClk after 4 ns;
  --
  fClkP <= not fClkP after 7 * 4 ns;
  fClkN <= not fClkP;
  dClkP <= not dClkP after 4 ns; 
  dClkN <= not dClkP;
  --

  EncDataIn_Proc: process
    variable dataIndex : integer := 0;
  begin
    wait until fClkP = '1';
    if EncValidIn = '1' then
      EncDataIn <= ramWaveform(dataIndex);
      dataIndex := dataIndex + 1;
      if dataIndex = DEPTH_C then
        dataIndex := 0;
      end if;
    else
      EncDataIn <= IDLE_PATTERN_C;
    end if;
  end process;

  AutomaticTestCheck_Proc: process
    variable dataIndex : integer := 0;
  begin
    wait until fClkP = '1';
    if DecValidOut = '1' then
      if DecDataOut = ramTestWaveform(dataIndex) then
        testOk <= '1';
        dataIndex := dataIndex + 1;
        if dataIndex = DEPTH_C then
          dataIndex := 0;
        end if;
      else
        testOk <= '0';
      end if;
    end if;
  end process;

  
  -- waveform generation
  WaveGen_Proc: process
    variable registerData    : slv(31 downto 0);  
  begin

    ---------------------------------------------------------------------------
    -- reset
    ---------------------------------------------------------------------------
    wait until sysClk = '1';
    sysClkRst  <= '1';
    EncValidIn <= '0';
    testTrig <= '0';

    wait for 1 us;
    sysClkRst <= '0';
    idelayCtrlRdy <= '1';               -- simulates control ready signal
            
    wait for 10 us;
    EncValidIn <= '1';                  -- starts sending realData

    wait for 100 us;
    EncValidIn <= '0';                  -- starts sending realData

    wait for 10 us;
    EncValidIn <= '1';                  -- starts sending realData

    wait for 200 us;
    EncValidIn <= '0';                  -- starts sending realData

    wait for 10 us;
    EncValidIn <= '1';                  -- starts sending realData

    wait for 100 us;

    ---------------------------------------------------------------------------
    -- load axilite registers
    ---------------------------------------------------------------------------
    --
    wait until sysClk = '1';
    -- change to axil register command
    wait until sysClk = '0';

    axiLiteBusSimRead (sysClk, sAxilReadMaster(READOUT_GROUP_ID), sAxilReadSlave(READOUT_GROUP_ID), x"00000020", registerData, true);
    registerValue <= registerData;
    wait for 1 us;
    
    axiLiteBusSimWrite (sysClk, sAxilWriteMaster(READOUT_GROUP_ID), sAxilWriteSlave(READOUT_GROUP_ID), x"00000020", x"00000000", true);
    wait for 10 us;    
    
    axiLiteBusSimRead (sysClk, sAxilReadMaster(READOUT_GROUP_ID), sAxilReadSlave(READOUT_GROUP_ID), x"00000020", registerData, true);
    registerValue <= registerData;
    wait for 1 us;

    wait for 100 us;
    ---------------------------------------------------------------------------
    -- change to stream mode
    ---------------------------------------------------------------------------
    wait until sysClk = '1';
    -- change to axil register command
    wait until sysClk = '0';
    
    axiLiteBusSimRead (sysClk, sAxilReadMaster(AXISTREAM_GROUP_ID), sAxilReadSlave(AXISTREAM_GROUP_ID), x"00000020", registerData, true);
    registerValue <= registerData;
    wait for 1 us;
    
    axiLiteBusSimWrite (sysClk, sAxilWriteMaster(AXISTREAM_GROUP_ID), sAxilWriteSlave(AXISTREAM_GROUP_ID), x"00000020", x"00000001", true);
    wait for 10 us;    
    
    axiLiteBusSimRead (sysClk, sAxilReadMaster(AXISTREAM_GROUP_ID), sAxilReadSlave(AXISTREAM_GROUP_ID), x"00000020", registerData, true);
    registerValue <= registerData;
    wait for 1 us;

    -- run tests
    wait for 200 us;
    wait until sysClk = '1';
    -- change to axil register command
    wait until sysClk = '0';
     
    axiLiteBusSimWrite (sysClk, sAxilWriteMaster(AXISTREAM_GROUP_ID), sAxilWriteSlave(AXISTREAM_GROUP_ID), x"00000020", x"00000000", true);
    wait for 100 us;    

    ---------------------------------------------------------------------------
    -- change to test mode
    ---------------------------------------------------------------------------
    wait until sysClk = '1';
    -- change to axil register command
    wait until sysClk = '0';
    
    axiLiteBusSimRead (sysClk, sAxilReadMaster(AXISTREAM_GROUP_ID), sAxilReadSlave(AXISTREAM_GROUP_ID), x"0000001C", registerData, true);
    registerValue <= registerData;
    wait for 1 us;
    
    axiLiteBusSimWrite (sysClk, sAxilWriteMaster(AXISTREAM_GROUP_ID), sAxilWriteSlave(AXISTREAM_GROUP_ID), x"0000001C", x"00000003", true);
    wait for 10 us;    
    
    axiLiteBusSimRead (sysClk, sAxilReadMaster(AXISTREAM_GROUP_ID), sAxilReadSlave(AXISTREAM_GROUP_ID), x"0000001C", registerData, true);
    registerValue <= registerData;
    wait for 1 us;

    ---------------------------------------------------------------------------
    -- triggers in test mode
    ---------------------------------------------------------------------------
    wait for 100 us;
    wait until sysClk = '1';
    testTrig <= '1';
    wait until sysClk = '1';
    testTrig <= '0';

    ---------------------------------------------------------------------------
    -- start gearbox offset search
    ---------------------------------------------------------------------------
    gearboxOffset <= "000";
    bitSlip <= "0000";


    wait for 10 us;
    

    
    wait;
  end process WaveGen_Proc;

  

end cryo_tb_arch;

