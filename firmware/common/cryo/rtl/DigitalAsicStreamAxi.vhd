-------------------------------------------------------------------------------
-- Title         : DigitalAsicStreamAxi
-- Project       : Hr Detectors
-------------------------------------------------------------------------------
-- File          : DigitalAsicStreamAxi.vhd
-- Created       : 7/12/2018
-------------------------------------------------------------------------------
-- Description:
-------------------------------------------------------------------------------
-- This file is part of 'Hr ADC Development Firmware'.
-- It is subject to the license terms in the LICENSE.txt file found in the 
-- top-level directory of this distribution and at: 
--    https://confluence.slac.stanford.edu/display/ppareg/LICENSE.html. 
-- No part of 'EPIX Development Firmware', including this file, 
-- may be copied, modified, propagated, or distributed except according to 
-- the terms contained in the LICENSE.txt file.
-------------------------------------------------------------------------------
-- Modification history:
-- 4/27/2017: created.
-------------------------------------------------------------------------------

LIBRARY ieee;
use work.all;
use ieee.std_logic_1164.all;
use ieee.std_logic_arith.all;
use ieee.std_logic_unsigned.all;
use work.StdRtlPkg.all;
use work.AxiLitePkg.all;
use work.AxiStreamPkg.all;
use work.SsiPkg.all;

entity DigitalAsicStreamAxi is 
   generic (
      TPD_G           	: time := 1 ns;
      VC_NO_G           : slv(3 downto 0)  := "0000";
      LANE_NO_G         : slv(3 downto 0)  := "0000";
      ASIC_NO_G         : slv(2 downto 0)  := "000";
      STREAMS_PER_ASIC_G  : natural := 2;  -- 1, 2 or 6. Number of screams per ASIC HR
                                         -- prototype has 2 final version 6
      ASIC_DATA_G         : natural := (32*32)-1; --workds
      ASIC_WIDTH_G        : natural := 32; --workds
      ASIC_DATA_PADDING_G : string := "LSB";  -- or "MSB"      
      AXIL_ERR_RESP_G     : slv(1 downto 0)  := AXI_RESP_DECERR_C
   );
   port ( 
      -- Deserialized data port
      rxClk             : in  sl;
      rxRst             : in  sl;
      adcStreams        : in AxiStreamMasterArray(STREAMS_PER_ASIC_G-1 downto 0);
      
      -- AXI lite slave port for register access
      axilClk           : in  sl;
      axilRst           : in  sl;
      sAxilWriteMaster  : in  AxiLiteWriteMasterType;
      sAxilWriteSlave   : out AxiLiteWriteSlaveType;
      sAxilReadMaster   : in  AxiLiteReadMasterType;
      sAxilReadSlave    : out AxiLiteReadSlaveType;
      
      -- AXI data stream output
      axisClk           : in  sl;
      axisRst           : in  sl;
      mAxisMaster       : out AxiStreamMasterType;
      mAxisSlave        : in  AxiStreamSlaveType;
      
      -- acquisition number input to the header
      acqNo             : in  slv(31 downto 0);
      
      -- optional readout trigger for test mode
      testTrig          : in  sl := '0';
      -- optional inhibit counting errors 
      -- workaround to tixel bug dropping link after R0
      -- affects only SOF error counter
      errInhibit        : in  sl := '0'
      
   );
end DigitalAsicStreamAxi;


-- Define architecture
architecture RTL of DigitalAsicStreamAxi is

   -- makes the fifo input with 2B per stream
   constant AXI_STREAM_CONFIG_I_C : AxiStreamConfigType   := ssiAxiStreamConfig(2*STREAMS_PER_ASIC_G, TKEEP_COMP_C);
   constant AXI_STREAM_CONFIG_O_C : AxiStreamConfigType   := ssiAxiStreamConfig(16, TKEEP_COMP_C);--
   constant VECTOR_OF_ONES_C  : slv(15 downto 0) := (others => '1');
   constant VECTOR_OF_ZEROS_C : slv(15 downto 0) := (others => '0');
   -- PGP3 protocol is using 128bit (check for global constant for this configuration)
   
   type StateType is (IDLE_S, HDR_S, DATA_S);
   
   type StrType is record
      state          : StateType;
      stCnt          : natural;
      testColCnt     : natural;
      testRowCnt     : natural;
      testTrig       : slv(2 downto 0);
      testMode       : slv(STREAMS_PER_ASIC_G-1 downto 0);
      streamDataMode : sl;
      stopDataTx     : sl;
      testBitFlip    : sl;
      frmSize        : slv(15 downto 0);
      frmMax         : slv(15 downto 0);
      frmMin         : slv(15 downto 0);
      acqNo          : Slv32Array(1 downto 0);
      frmCnt         : slv(31 downto 0);
      sofError       : slv(15 downto 0);
      eofError       : slv(15 downto 0);
      ovError        : slv(15 downto 0);
      rstCnt         : sl;
      errInhibit     : sl;
      dFifoRd        : sl;
      tReady         : sl;
      axisMaster     : AxiStreamMasterType;
   end record;

   constant STR_INIT_C : StrType := (
      state          => IDLE_S,
      stCnt          => 0,
      testColCnt     => 0,
      testRowCnt     => 0,
      testTrig       => "000",
      testMode       => (others=>'0'),
      streamDataMode => '0',
      stopDataTx     => '0',
      testBitFlip    => '0',
      frmSize        => (others=>'0'),
      frmMax         => (others=>'0'),
      frmMin         => (others=>'1'),
      acqNo          => (others=>(others=>'0')),
      frmCnt         => (others=>'0'),
      sofError       => (others=>'0'),
      eofError       => (others=>'0'),
      ovError        => (others=>'0'),
      rstCnt         => '0',
      errInhibit     => '0',
      dFifoRd        => '0',
      tReady         => '0',
      axisMaster     => AXI_STREAM_MASTER_INIT_C
   );
   
   type RegType is record
      testMode          : slv(STREAMS_PER_ASIC_G-1 downto 0);
      streamDataMode    : sl;
      stopDataTx        : sl;
      frmSize           : slv(15 downto 0);
      frmMax            : slv(15 downto 0);
      frmMin            : slv(15 downto 0);
      frmCnt            : slv(31 downto 0);
      sofError          : slv(15 downto 0);
      eofError          : slv(15 downto 0);
      ovError           : slv(15 downto 0);
      rstCnt            : slv(2 downto 0);
      sAxilWriteSlave   : AxiLiteWriteSlaveType;
      sAxilReadSlave    : AxiLiteReadSlaveType;
   end record RegType;

   constant REG_INIT_C : RegType := (
      testMode          => (others=>'0'),
      streamDataMode    => '0',
      stopDataTx        => '0',
      frmSize           => (others=>'0'),
      frmMax            => (others=>'0'),
      frmMin            => (others=>'0'),
      frmCnt            => (others=>'0'),
      sofError          => (others=>'0'),
      eofError          => (others=>'0'),
      ovError           => (others=>'0'),
      rstCnt            => (others=>'0'),
      sAxilWriteSlave   => AXI_LITE_WRITE_SLAVE_INIT_C,
      sAxilReadSlave    => AXI_LITE_READ_SLAVE_INIT_C
   );
   
   signal r   : RegType := REG_INIT_C;
   signal rin : RegType;
   signal s   : StrType := STR_INIT_C;
   signal sin : StrType;

   signal rxValid       : slv(STREAMS_PER_ASIC_G-1 downto 0);
   
   signal decDataOut    : slv12Array(STREAMS_PER_ASIC_G-1 downto 0);
   signal decValidOut   : slv(STREAMS_PER_ASIC_G-1 downto 0);
   signal decSof        : slv(STREAMS_PER_ASIC_G-1 downto 0);
   signal decEof        : slv(STREAMS_PER_ASIC_G-1 downto 0);
   signal decEofe       : slv(STREAMS_PER_ASIC_G-1 downto 0);
   signal decCodeError  : slv(STREAMS_PER_ASIC_G-1 downto 0);
   signal decDispError  : slv(STREAMS_PER_ASIC_G-1 downto 0);
   
   signal dFifoRd       : sl;
   signal dFifoEofe     : slv(STREAMS_PER_ASIC_G-1 downto 0);
   signal dFifoEof      : slv(STREAMS_PER_ASIC_G-1 downto 0);
   signal dFifoSof      : slv(STREAMS_PER_ASIC_G-1 downto 0);
   signal dFifoValid    : slv(STREAMS_PER_ASIC_G-1 downto 0);
   signal dFifoOut      : slv12Array(STREAMS_PER_ASIC_G-1 downto 0);
   signal dFifoExtData  : slv(16*STREAMS_PER_ASIC_G-1 downto 0) := (others => '0');
   
   signal sAxisMaster  : AxiStreamMasterType;
   signal sAxisSlave   : AxiStreamSlaveType;
   signal imAxisMaster : AxiStreamMasterType;
   signal imAxisSlave  : AxiStreamSlaveType;
   
   signal testModeSync  : slv(STREAMS_PER_ASIC_G-1 downto 0);
   signal iRxValid      : slv(STREAMS_PER_ASIC_G-1 downto 0);
   
   signal rxDataCs   : slv(13 downto 0);                 -- for chipscope
   signal rxValidCs  : sl;                               -- for chipscope
   attribute keep : string;                              -- for chipscope
   attribute keep of s            : signal is "true";    -- for chipscope
   attribute keep of dFifoOut     : signal is "true";    -- for chipscope
   attribute keep of dFifoSof     : signal is "true";    -- for chipscope
   attribute keep of dFifoEof     : signal is "true";    -- for chipscope
   attribute keep of dFifoEofe    : signal is "true";    -- for chipscope
   attribute keep of dFifoValid   : signal is "true";    -- for chipscope
   attribute keep of rxDataCs     : signal is "true";    -- for chipscope
   attribute keep of rxValidCs    : signal is "true";    -- for chipscope
   attribute keep of sAxisMaster  : signal is "true";    -- for chipscope
   attribute keep of imAxisMaster : signal is "true";    -- for chipscope 
   attribute keep of imAxisSlave  : signal is "true";    -- for chipscope 


begin
   
   rxDataCs <= adcStreams(0).tData(13 downto 0);     -- for chipscope
   rxValidCs <= adcStreams(0).tValid;   -- for chipscope

   mAxisMaster <= imAxisMaster;
   mAxisSlave  <= imAxisSlave;

   fifoExtData_GEN : for i in 0 to STREAMS_PER_ASIC_G-1 generate
     dataExt : process(dFifoOut)
       begin
         if ASIC_DATA_PADDING_G = "LSB" then
           dFifoExtData(16*i+15 downto 16*i) <= dFifoOut(i)&"0000";
         else
           dFifoExtData(16*i+15 downto 16*i) <= "0000"&dFifoOut(i);
         end if;
       end process;
   end generate;
   
   -- synchronizers
   Sync1_U : entity work.SynchronizerVector
     generic map (
       WIDTH_G => 2)
   port map (
      clk     => rxClk,
      rst     => rxRst,
      dataIn  => s.testMode,
      dataOut => testModeSync
   );

   ----------------------------------------------------------------------------
   -- Instatiate one decoder per data stream.
   ----------------------------------------------------------------------------
   U_DECODERS : for i in 0 to STREAMS_PER_ASIC_G-1 generate
     --------------------------------------------------------------------------
     -- 12b14b decoder with SSP output
     --------------------------------------------------------------------------
     Dec12b14b_U : entity work.SspDecoder12b14b 
       generic map (
         TPD_G          => TPD_G,
         RST_POLARITY_G => '1',
         RST_ASYNC_G    => false)
       port map (
         clk         => rxClk,
         rst         => rxRst,
         dataIn      => adcStreams(i).tData(13 downto 0),
         validIn     => iRxValid(i),
         dataOut     => decDataOut(i),
         validOut    => decValidOut(i),
         valid       => open,
         sof         => decSof(i),
         eof         => decEof(i),
         eofe        => decEofe(i),
         codeError   => decCodeError(i),
         dispError   => decDispError(i)
         );

   
     -- disable decoder in test mode (fake ASIC data)
     iRxValid(i) <= adcStreams(i).tValid and not testModeSync(i);
   
     -- async fifo for data
     -- for synchronization and small data pipeline
     -- not to store the whole frame
     DataFifo_U : entity work.FifoCascade
       generic map (
         GEN_SYNC_FIFO_G   => false,
         FWFT_EN_G         => true,
         ADDR_WIDTH_G      => 4,
         DATA_WIDTH_G      => 15
         )
       port map (
         -- Resets
         rst               => rxRst,
         wr_clk            => rxClk,
         wr_en             => decValidOut(i),
         din(11 downto 0)  => decDataOut(i),
         din(12)           => decEofe(i),
         din(13)           => decEof(i),
         din(14)           => decSof(i),
         --Read Ports (rd_clk domain)
         rd_clk            => axisClk,
         rd_en             => dFifoRd,
         dout(11 downto 0) => dFifoOut(i),
         dout(12)          => dFifoEofe(i),
         dout(13)          => dFifoEof(i),
         dout(14)          => dFifoSof(i),
         valid             => dFifoValid(i)
         );
   end generate;

   ----------------------------------------------------------------------------
   -- axi stream fifo
   ----------------------------------------------------------------------------
   -- must be able to store whole frame if AXIS is muxed
   ----------------------------------------------------------------------------
   AxisFifo_U: entity work.AxiStreamFifo
   generic map(
      GEN_SYNC_FIFO_G      => false,
      FIFO_ADDR_WIDTH_G    => 13,
      XIL_DEVICE_G         => "ULTRASCALE",
      SLAVE_AXI_CONFIG_G   => AXI_STREAM_CONFIG_I_C,
      MASTER_AXI_CONFIG_G  => AXI_STREAM_CONFIG_O_C
   )
   port map(
      sAxisClk    => axisClk,
      sAxisRst    => axisRst,
      sAxisMaster => sAxisMaster,
      sAxisSlave  => sAxisSlave,
      mAxisClk    => axisClk,
      mAxisRst    => axisRst,
      mAxisMaster => imAxisMaster,
      mAxisSlave  => imAxisSlave
   );



   comb : process (axilRst, axisRst, sAxilReadMaster, sAxilWriteMaster, sAxisSlave, r, s, 
      acqNo, dFifoOut, dFifoExtData, dFifoValid, dFifoSof, dFifoEof, dFifoEofe, testTrig, errInhibit) is
      variable sv       : StrType;
      variable rv       : RegType;
      variable regCon   : AxiLiteEndPointType;
   begin
      rv := r;    -- r is in AXI lite clock domain
      sv := s;    -- s is in AXI stream clock domain
      sv.dFifoRd := '0';
      sv.axisMaster := AXI_STREAM_MASTER_INIT_C;
      sv.testTrig(0) := testTrig;
      sv.testTrig(1) := s.testTrig(0);
      sv.testTrig(2) := s.testTrig(1);
      sv.errInhibit := errInhibit;
      
      -- cross clock sync
      
      rv.frmSize    := s.frmSize;
      rv.frmMax     := s.frmMax;
      rv.frmMin     := s.frmMin;
      rv.frmCnt     := s.frmCnt;
      rv.sofError   := s.sofError;
      rv.eofError   := s.eofError;
      rv.ovError    := s.ovError;
      sv.testMode   := r.testMode;
      sv.stopDataTx := r.stopDataTx;
      sv.streamDataMode := r.streamDataMode;
      
      if r.rstCnt /= "000" then
         sv.rstCnt := '1';
      else
         sv.rstCnt := '0';
      end if;
      
      -- axi lite logic 
      rv.rstCnt := r.rstCnt(1 downto 0) & '0';
      rv.sAxilReadSlave.rdata := (others => '0');
      axiSlaveWaitTxn(regCon, sAxilWriteMaster, sAxilReadMaster, rv.sAxilWriteSlave, rv.sAxilReadSlave);
      
      axiSlaveRegisterR(regCon, x"00",  0, r.frmCnt);
      axiSlaveRegisterR(regCon, x"04",  0, r.frmSize);
      axiSlaveRegisterR(regCon, x"08",  0, r.frmMax);
      axiSlaveRegisterR(regCon, x"0C",  0, r.frmMin);
      axiSlaveRegisterR(regCon, x"10",  0, r.sofError);
      axiSlaveRegisterR(regCon, x"14",  0, r.eofError);
      axiSlaveRegisterR(regCon, x"18",  0, r.ovError);
      axiSlaveRegister (regCon, x"1C",  0, rv.testMode);
      axiSlaveRegister (regCon, x"20",  0, rv.streamDataMode);
      axiSlaveRegister (regCon, x"20",  1, rv.stopDataTx);   
      axiSlaveRegister (regCon, x"24",  0, rv.rstCnt);
      
      axiSlaveDefault(regCon, rv.sAxilWriteSlave, rv.sAxilReadSlave, AXIL_ERR_RESP_G);
      
      -- axi stream logic
      
      -- sync acquisition number
      sv.acqNo(0) := acqNo;
      
      -- report an error when sAxisSlave.tReady is dropped (overflow)
      sv.tReady := sAxisSlave.tReady;
      if sAxisSlave.tReady = '0' and s.tReady = '1' then
         sv.ovError := s.ovError + 1;
      end if;
      
      case s.state is
         when IDLE_S =>
           --------------------------------------------------------------------
           -- FIRST frame mode trigger option
           --------------------------------------------------------------------
           -- starts data tx when all streams have DV and SOF, different data
           -- delays should be acommodate by the fifo
           --------------------------------------------------------------------
           -- SECOND frame mode trigger option
           --------------------------------------------------------------------
           -- in test mode and rising edge of testTrig signal
           --------------------------------------------------------------------
           -- STREAM mode
           --------------------------------------------------------------------
           -- when a frame is finished, the next one starts. 
           --------------------------------------------------------------------
           -- OBS
           --------------------------------------------------------------------
           -- if module is desabled data is not set ever as indicated by
           -- stopDataTx signal
            if (
                ((dFifoValid(STREAMS_PER_ASIC_G-1 downto 0) = VECTOR_OF_ONES_C(STREAMS_PER_ASIC_G-1 downto 0) and dFifoSof(STREAMS_PER_ASIC_G-1 downto 0) = VECTOR_OF_ONES_C(STREAMS_PER_ASIC_G-1 downto 0))
                 or (s.testMode(STREAMS_PER_ASIC_G-1 downto 0) /= VECTOR_OF_ZEROS_C(STREAMS_PER_ASIC_G-1 downto 0) and s.testTrig(1) = '1' and s.testTrig(2) = '0')
                 or (s.streamDataMode='1'))
                and (s.stopDataTx='0'))  then
               -- start sending the header
               -- do not read the fifo yet
               sv.acqNo(1) := s.acqNo(0);
               sv.state := HDR_S;
               sv.testBitFlip := '0';
               sv.testColCnt := 0;
               sv.testRowCnt := 0;
            elsif dFifoValid = VECTOR_OF_ONES_C(STREAMS_PER_ASIC_G-1 downto 0) then
               -- should only happen if we are in stream mode, else in frame
               -- mode it should not happen
               -- ADD logic for stream mode
               -- In frame mode:
               -- dump data and report an error
               if s.errInhibit = '0' then
                  sv.sofError := s.sofError + 1;
               end if;
               sv.dFifoRd := '1';
            end if;
         
         -- header is 6 x 16 bit words
         when HDR_S =>
           --------------------------------------------------------------------
           -- HEADER for 1 STREAM
           --------------------------------------------------------------------
           if STREAMS_PER_ASIC_G = 1 then        
             sv.axisMaster.tValid := '1';
             if s.stCnt = 5 then
               sv.stCnt := 0;
               sv.state := DATA_S;
             else
               sv.stCnt := s.stCnt + 1;
             end if;
             if s.stCnt = 0 then
               sv.axisMaster.tData(15 downto 0) := x"00" & LANE_NO_G & VC_NO_G;
               ssiSetUserSof(AXI_STREAM_CONFIG_I_C, sv.axisMaster, '1');
             elsif s.stCnt = 1 then
               sv.axisMaster.tData(15 downto 0) := x"0000";
             elsif s.stCnt = 2 then
               sv.axisMaster.tData(15 downto 0) := s.acqNo(1)(15 downto 0);
             elsif s.stCnt = 3 then
               sv.axisMaster.tData(15 downto 0) := s.acqNo(1)(31 downto 16);
             elsif s.stCnt = 4 then
               if s.testMode /= VECTOR_OF_ONES_C(STREAMS_PER_ASIC_G-1 downto 0) then
                 sv.axisMaster.tData(15 downto 0) := x"000" & '0' & ASIC_NO_G;
               else
                 sv.axisMaster.tData(15 downto 0) := x"000" & '0' & ASIC_NO_G;
               end if;
             else
               sv.axisMaster.tData(15 downto 0) := toSlv(STREAMS_PER_ASIC_G, 16);
             end if;
           end if;
           ------------------------------------------------------------------
           -- HEADER for 2 Streams
           ------------------------------------------------------------------
           if STREAMS_PER_ASIC_G = 2 then        
             sv.axisMaster.tValid := '1';
             if s.stCnt = 2 then
               sv.stCnt := 0;
               sv.state := DATA_S;
             else
               sv.stCnt := s.stCnt + 1;
             end if;
             if s.stCnt = 0 then
               sv.axisMaster.tData(31 downto 0) := x"0000" & x"00" & LANE_NO_G & VC_NO_G;
               ssiSetUserSof(AXI_STREAM_CONFIG_I_C, sv.axisMaster, '1');
             elsif s.stCnt = 1 then
               sv.axisMaster.tData(31 downto 0) := s.acqNo(1)(31 downto 0);
             elsif s.stCnt = 2 then
               if s.testMode /= VECTOR_OF_ONES_C(STREAMS_PER_ASIC_G-1 downto 0) then
                 sv.axisMaster.tData(15 downto 0) := x"000" & '0' & ASIC_NO_G;
               else
                 sv.axisMaster.tData(15 downto 0) := x"000" & '0' & ASIC_NO_G;
               end if;
               sv.axisMaster.tData(31 downto 16) := toSlv(STREAMS_PER_ASIC_G, 16);
             else
               sv.axisMaster.tData(31 downto 0) := x"00000000";
             end if;
           end if;
           ------------------------------------------------------------------
           -- HEADER for 6 Streams
           ------------------------------------------------------------------
           if STREAMS_PER_ASIC_G = 6 then        
             sv.axisMaster.tValid := '1';
             sv.state := DATA_S;
             sv.axisMaster.tData(31 downto  0) := x"0000" & x"00" & LANE_NO_G & VC_NO_G;
             sv.axisMaster.tData(63 downto 32) := s.acqNo(1)(31 downto 0);
             if s.testMode /= VECTOR_OF_ONES_C(STREAMS_PER_ASIC_G-1 downto 0) then
               sv.axisMaster.tData(79 downto 64) := x"000" & '0' & ASIC_NO_G;
             else
               sv.axisMaster.tData(79 downto 64) := x"000" & '0' & ASIC_NO_G;
             end if;
             sv.axisMaster.tData(95 downto 80) := x"0000";
             ssiSetUserSof(AXI_STREAM_CONFIG_I_C, sv.axisMaster, '1');                    
           end if;
             
         when DATA_S =>
            if dFifoValid /= VECTOR_OF_ZEROS_C(STREAMS_PER_ASIC_G-1 downto 0) or (s.testMode /= VECTOR_OF_ZEROS_C(STREAMS_PER_ASIC_G-1 downto 0) and (sAxisSlave.tReady='1')) then
               
               -- test mode row and col counters
               if s.testColCnt < (ASIC_WIDTH_G/STREAMS_PER_ASIC_G)-1 then  -- why -1 here??
                  sv.testColCnt := s.testColCnt + 1;
               else
                  sv.testColCnt := 0;
                  sv.testRowCnt := s.testRowCnt + 1;
               end if;
               
               sv.axisMaster.tValid := '1';
               -- test or real data readout
               if s.testMode(0) = '0' then
                 sv.axisMaster.tData(16*STREAMS_PER_ASIC_G-1 downto 0) := dFifoExtData;
               else
                 sv.axisMaster.tData(16*STREAMS_PER_ASIC_G-1 downto 0) := (others => '0');
                 if s.testColCnt = ASIC_WIDTH_G/(2*STREAMS_PER_ASIC_G)-1 then
                   sv.axisMaster.tData(15 downto 0) := ASIC_NO_G(1 downto 0) & s.testBitFlip & s.acqNo(1)(4 downto 0) & "00" & toSlv(s.testRowCnt, 6);
                 elsif s.testRowCnt = 15 then
                   sv.axisMaster.tData(15 downto 0) := ASIC_NO_G(1 downto 0) & s.testBitFlip & s.acqNo(1)(4 downto 0) & "00" & toSlv(s.testColCnt, 6);
                 else
                   sv.axisMaster.tData(15 downto 0) := ASIC_NO_G(1 downto 0) & s.testBitFlip & "00000" & x"ff";
                 end if;
               end if;
               
               sv.dFifoRd := '1';
                           
               sv.stCnt := s.stCnt + 1;
               if ((dFifoEof /= VECTOR_OF_ZEROS_C(STREAMS_PER_ASIC_G-1 downto 0) or dFifoEofe /= VECTOR_OF_ZEROS_C(STREAMS_PER_ASIC_G-1 downto 0)) and s.testMode /= VECTOR_OF_ONES_C(STREAMS_PER_ASIC_G-1 downto 0)) or s.stCnt = ASIC_DATA_G then 
                  sv.frmSize := toSlv(s.stCnt, 16);
                  sv.stCnt := 0;
                  if s.frmMax <= sv.frmSize then
                     sv.frmMax := sv.frmSize;
                  end if;
                  if s.frmMin >= sv.frmSize then
                     sv.frmMin := sv.frmSize;
                  end if;
                  
                  if dFifoEofe /= VECTOR_OF_ZEROS_C(STREAMS_PER_ASIC_G-1 downto 0) or sv.frmSize /= ASIC_DATA_G then
                     ssiSetUserEofe(AXI_STREAM_CONFIG_I_C, sv.axisMaster, '1');
                     sv.eofError := s.eofError + 1;
                  else
                     sv.frmCnt := s.frmCnt + 1;
                  end if;
                  sv.axisMaster.tLast := '1';
                  if s.testMode(0) = '0' then
                     sv.state := IDLE_S;
                  else
                    sv.state := IDLE_S;
                  end if;
               end if;               
            end if;
         
         when others =>
      end case;
      
      -- reset counters
      if s.rstCnt = '1' then
         sv.frmCnt   := (others=>'0');
         sv.frmSize  := (others=>'0');
         sv.frmMax   := (others=>'0');
         sv.frmMin   := (others=>'1');
         sv.eofError := (others=>'0');
         sv.sofError := (others=>'0');
         sv.ovError  := (others=>'0');
      end if;
      
      -- reset logic
      
      if (axilRst = '1') then
         rv := REG_INIT_C;
      end if;
      if (axisRst = '1') then
         sv := STR_INIT_C;
      end if;

      -- outputs
      
      rin <= rv;
      sin <= sv;

      sAxilWriteSlave   <= r.sAxilWriteSlave;
      sAxilReadSlave    <= r.sAxilReadSlave;
      sAxisMaster       <= s.axisMaster;
      dFifoRd           <= sv.dFifoRd;

   end process comb;

   rseq : process (axilClk) is
   begin
      if (rising_edge(axilClk)) then
         r <= rin after TPD_G;
      end if;
   end process rseq;
   
   sseq : process (axisClk) is
   begin
      if (rising_edge(axisClk)) then
         s <= sin after TPD_G;
      end if;
   end process sseq;
   

end RTL;

