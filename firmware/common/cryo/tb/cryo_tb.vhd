-------------------------------------------------------------------------------
-- Title      : Testbench for design "AD9249ClkUS"
-- Project    : 
-------------------------------------------------------------------------------
-- File       : cryo_tb.vhd
-- Author     : Dionisio Doering  <ddoering@tid-pc94280.slac.stanford.edu>
-- Company    : 
-- Created    : 2017-05-22
-- Last update: 2018-07-09
-- Platform   : 
-- Standard   : VHDL'87
-------------------------------------------------------------------------------
-- Description: 
-------------------------------------------------------------------------------
-- Copyright (c) 2017 
-------------------------------------------------------------------------------
-- Revisions  :
-- Date        Version  Author  Description
-------------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;
use ieee.std_logic_unsigned.all;
use ieee.std_logic_textio.all;

library STD;
use STD.textio.all;      

use work.all;
use work.StdRtlPkg.all;

use ieee.std_logic_arith.all;
use ieee.numeric_std.all;

use work.StdRtlPkg.all;
use work.AxiStreamPkg.all;
use work.EpixHrCorePkg.all;
use work.AxiLitePkg.all;
use work.AxiPkg.all;
use work.Pgp2bPkg.all;
use work.SsiPkg.all;
use work.SsiCmdMasterPkg.all;
use work.HrAdcPkg.all;
use work.Code8b10bPkg.all;

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
  signal ramWaveform    : ram_t    := readWaveFile(FILENAME_C);
  
  -- component ports
  signal sysClkRst : std_logic := '1';
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
  signal axilWriteMaster : AxiLiteWriteMasterType;
  signal axilWriteSlave  : AxiLiteWriteSlaveType;
  signal axilReadMaster  : AxiLiteReadMasterType;
  signal axilReadSlave   : AxiLiteReadSlaveType;
  signal registerValue   : slv(31 downto 0);    
  signal adcSerial       : HrAdcSerialGroupType;
  signal adcStreams      : AxiStreamMasterArray(NUM_CHANNELS_G-1 downto 0);


  -- clock
  signal sysClk    : std_logic := '1';


begin  --

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
        reset_n_i => not sysClkRst,
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
        axilWriteMaster => axilWriteMaster,
        axilWriteSlave  => axilWriteSlave,
        axilReadMaster  => axilReadMaster,
        axilReadSlave   => axilReadSlave,
 
        -- Serial Data from ADC
        adcSerial => adcSerial,

        -- Deserialized ADC Data
        adcStreamClk => sysClk,
        adcStreams   => adcStreams      
        );
  
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

-- use the code below to bypass serializer/deserializer
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

    wait for 1 us;
    sysClkRst <= '0';
    idelayCtrlRdy <= '1';               -- simulates control ready signal
            
    wait for 10 us;
    EncValidIn <= '1';                  -- starts sending realData

    wait for 100 us;
    EncValidIn <= '0';                  -- starts sending realData

    wait for 10 us;
    EncValidIn <= '1';                  -- starts sending realData

    ---------------------------------------------------------------------------
    -- load axilite registers
    ---------------------------------------------------------------------------
    --
    wait until sysClk = '1';
    -- change to axil register command
    wait until sysClk = '0';
    --loadDelay <= '0';
    axiLiteBusSimRead (sysClk, axilReadMaster, axilReadSlave, x"00000020", registerData, true);
    registerValue <= registerData;
    wait for 1 us;
    
    axiLiteBusSimWrite (sysClk, axilWriteMaster, axilWriteSlave, x"00000020", x"00000000", true);
    wait for 10 us;    
    
    axiLiteBusSimRead (sysClk, axilReadMaster, axilReadSlave, x"00000020", registerData, true);
    registerValue <= registerData;
    wait for 1 us;

    ---------------------------------------------------------------------------
    -- start gearbox offset search
    ---------------------------------------------------------------------------
    gearboxOffset <= "000";
    bitSlip <= "0000";


    wait for 10 us;
    

    
    wait;
  end process WaveGen_Proc;

  

end cryo_tb_arch;

