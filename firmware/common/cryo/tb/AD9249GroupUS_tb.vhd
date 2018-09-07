-------------------------------------------------------------------------------
-- Title      : Testbench for design "AD9249ClkUS"
-- Project    : 
-------------------------------------------------------------------------------
-- File       : AD9249ClkUS_tb.vhd
-- Author     : Dionisio Doering  <ddoering@tid-pc94280.slac.stanford.edu>
-- Company    : 
-- Created    : 2017-05-22
-- Last update: 2018-09-07
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
use work.all;
use work.StdRtlPkg.all;

library STD;
use STD.textio.all;      


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
use work.Ad9249Pkg.all;
use work.Code8b10bPkg.all;

use work.AppPkg.all;

library unisim;
use unisim.vcomponents.all;

-------------------------------------------------------------------------------

entity AD9249GroupUS_tb is

end AD9249GroupUS_tb;

-------------------------------------------------------------------------------

architecture AD9249GroupUS_arch of AD9249GroupUS_tb is

  -- component generics
  constant TPD_G : time := 1 ns;
  constant IDLE_PATTERN_C : slv(13 downto 0) := "00000001111111";
  constant NUM_CHANNELS_G : integer := 8;
  constant DEPTH_C     : natural := 1024;
  constant DATA_BITS   : natural := 14;
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
  signal dClkP : sl := '1';                       -- Data clock
  signal dClkN : sl := '0';
  signal fClkP : sl := '0';                       -- Frame clock
  signal fClkN : sl := '1';
  signal sDataP : sl;                       -- Frame clock
  signal sDataN : sl;
--  signal cmt_locked : sl;
--  signal pixData       : slv14Array(NUM_CHANNELS_G downto 0);  -- in channels
                                                               -- is the frame
                                                               -- signal

  -- axilite
  signal axilWriteMaster : AxiLiteWriteMasterType;
  signal axilWriteSlave  : AxiLiteWriteSlaveType;
  signal axilReadMaster  : AxiLiteReadMasterType;
  signal axilReadSlave   : AxiLiteReadSlaveType;
  signal registerValue   : slv(31 downto 0);    
  signal adcSerial       : Ad9249SerialGroupType;
  signal adcStreams      : AxiStreamMasterArray(NUM_CHANNELS_G-1 downto 0);


  -- clock
  signal sysClk    : std_logic := '1';

  signal dataValidIn   : sl := '0';
  signal dataIn        : slv(13 downto 0);
  signal dataInRev        : slv(13 downto 0);
  signal serialDataOut : sl;
  signal testData      : slv(13 downto 0);
  -- automatic test
  signal testOk : sl := '0';

begin  -- Dac8812Cntrl_arch

  sysClkRst_n <= not sysClkRst;
  dataInRev <= bitReverse(dataIn(13 downto 7))&bitReverse(dataIn(6 downto 0));
   
  DataIn_Proc: process
    variable dataIndex : integer := 0;
  begin
    wait until fClkP = '1';
    if dataValidIn = '1' then
      dataIn <= (ramWaveform(dataIndex));--"10101101100111";--
      dataIndex := dataIndex + 1;
      if dataIndex = DEPTH_C then
        dataIndex := 0;
      end if;
    else
      dataIn <= IDLE_PATTERN_C;
    end if;
  end process;


  U_serializer :  entity work.serializerSim 
    generic map(
        g_dwidth => 14,
        g_lsb_first => "False"
    )
    port map(
        clk_i     => dClkP,
        reset_n_i => sysClkRst_n,
        data_i    => dataIn,        -- "00"&EncDataIn, --
        data_o    => serialDataOut
    );

  -- clock generation
  sysClk <= not sysClk after 6.4 ns;
  --
  fClkP <= not fClkP after 3 * 7 ns;-- 20.0 ns;
  fClkN <= not fClkP;
  dClkP <= not dClkP after 3 ns; --2.857148571485714 ns;--1.428571428571428571428571428571 ns;
  dClkN <= not dClkP;
  --
  --sDataP <= not fClkP;
  --sDataN <=     fClkP;

  sDataP <=     serialDataOut;
  sDataN <= not serialDataOut;

  adcSerial.fClkP <= fClkN;
  adcSerial.fClkN <= fClkP;
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

  
  DUT0: entity work.Ad9249ReadoutGroup
      generic map (
        TPD_G             => TPD_G,
        NUM_CHANNELS_G    => 8,
        IODELAY_GROUP_G   => "DEFAULT_GROUP",
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
  
  AutomaticTestCheck_Proc: process
    variable dataIndex : integer := 0;
  begin
    wait until sysClk = '1';             --check this clock
    if adcStreams(0).tValid = '1' then
      testData <= (adcStreams(0).tData(13 downto 0));
      if testData = ramTestWaveform(dataIndex) then
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
    sysClkRst <= '1';

    wait for 1 us;
    sysClkRst <= '0';
    idelayCtrlRdy <= '1';               -- simulates control ready signal
        
    wait for 10 us;

    dataValidIn <= '1';

    ---------------------------------------------------------------------------
    -- laod idelay value
    ---------------------------------------------------------------------------
    --delayValueIn  <= "111101010";
    wait until sysClk = '1';
    --loadDelay <= '1';
    -- change to axil register command
     wait until sysClk = '0';
    --loadDelay <= '0';
    axiLiteBusSimRead (sysClk, axilReadMaster, axilReadSlave, x"00000020", registerData, true);
    registerValue <= registerData;
    wait for 1 us;
    
    axiLiteBusSimWrite (sysClk, axilWriteMaster, axilWriteSlave, x"00000020", x"00000F55", true);
    wait for 10 us;    
    
    axiLiteBusSimRead (sysClk, axilReadMaster, axilReadSlave, x"00000020", registerData, true);
    registerValue <= registerData;
    wait for 1 us;

    
    wait;
  end process WaveGen_Proc;

  

end AD9249GroupUS_arch;

