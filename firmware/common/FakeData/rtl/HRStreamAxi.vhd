-------------------------------------------------------------------------------
-- File       : AsicStreamAxi.vhd
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

LIBRARY ieee;
use ieee.std_logic_1164.all;
use ieee.std_logic_arith.all;
use ieee.std_logic_unsigned.all;

library surf;
use surf.StdRtlPkg.all;
use surf.AxiLitePkg.all;
use surf.AxiStreamPkg.all;
use surf.SsiPkg.all;

entity HRStreamAxi is 
   generic (
      TPD_G           	: time := 1 ns;
      VC_NO_G           : slv(3 downto 0)  := "0000";
      LANE_NO_G         : slv(3 downto 0)  := "0000";
      ASIC_NO_G         : slv(2 downto 0)  := "000";
      ASIC_DATA_G       : natural := 230400-1;
      AXIL_ERR_RESP_G   : slv(1 downto 0)  := AXI_RESP_DECERR_C
   );
   port ( 
      -- Deserialized data port
      rxClk             : in  sl;
      rxRst             : in  sl;
      rxData            : in  slv(19 downto 0);
      rxValid           : in  sl;
      
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

      -- waveform signal in
      asicSR0           : in  sl; -- waveform
      asicSync          : in  sl; -- waveform
      -- optional inhibit counting errors 
      -- workaround to tixel bug dropping link after R0
      -- affects only SOF error counter
      errInhibit        : in  sl := '0'
      
   );
end HRStreamAxi;


-- Define architecture
architecture RTL of HRStreamAxi is

   constant AXI_STREAM_CONFIG_I_C : AxiStreamConfigType   := ssiAxiStreamConfig(2, TKEEP_COMP_C);
   constant AXI_STREAM_CONFIG_O_C : AxiStreamConfigType   := ssiAxiStreamConfig(4, TKEEP_COMP_C);

   
   type StateType is (IDLE_S, HDR_S, DATA_S);
   
   type StrType is record
      state          : StateType;
      stCnt          : natural;
      testColCnt     : natural;
      testRowCnt     : natural;
      testTrig       : slv(2 downto 0);
      testMode       : sl;
      testBitFlip    : sl;
      frmSize        : slv(31 downto 0);
      frmMax         : slv(31 downto 0);
      frmMin         : slv(31 downto 0);
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
      testMode       => '0',
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
      testMode          : sl;
      frmSize           : slv(31 downto 0);
      frmMax            : slv(31 downto 0);
      frmMin            : slv(31 downto 0);
      frmCnt            : slv(31 downto 0);
      sofError          : slv(15 downto 0);
      eofError          : slv(15 downto 0);
      ovError           : slv(15 downto 0);
      rstCnt            : slv(2 downto 0);
      sAxilWriteSlave   : AxiLiteWriteSlaveType;
      sAxilReadSlave    : AxiLiteReadSlaveType;
      frameRate         : slv(31 downto 0);
      frameRateMax      : slv(31 downto 0);
      frameRateMin      : slv(31 downto 0);
      bandwidth         : slv(63 downto 0);
      bandwidthMax      : slv(63 downto 0);
      bandwidthMin      : slv(63 downto 0);
      numRowFD          : slv(31 downto 0);
   end record RegType;

   constant REG_INIT_C : RegType := (
      testMode          => '0',
      frmSize           => (others=>'0'),
      frmMax            => (others=>'0'),
      frmMin            => (others=>'0'),
      frmCnt            => (others=>'0'),
      sofError          => (others=>'0'),
      eofError          => (others=>'0'),
      ovError           => (others=>'0'),
      rstCnt            => (others=>'0'),
      sAxilWriteSlave   => AXI_LITE_WRITE_SLAVE_INIT_C,
      sAxilReadSlave    => AXI_LITE_READ_SLAVE_INIT_C,
      frameRate         => (others=>'0'),
      frameRateMax      => (others=>'0'),
      frameRateMin      => (others=>'0'),
      bandwidth         => (others=>'0'),
      bandwidthMax      => (others=>'0'),
      bandwidthMin      => (others=>'0'),
      numRowFD          => x"00000017"
   );
   
   signal r   : RegType := REG_INIT_C;
   signal rin : RegType;
   signal s   : StrType := STR_INIT_C;
   signal sin : StrType;
   
   signal decDataOut    : slv(15 downto 0);
   signal decValid      : sl;
   signal decSof        : sl;
   signal decEof        : sl;
   signal decEofe       : sl;
   signal lutDataOut    : slv(19 downto 0);
   
   signal dFifoRd       : sl;
   signal dFifoEofe     : sl;
   signal dFifoEof      : sl;
   signal dFifoSof      : sl;
   signal dFifoValid    : sl;
   signal dFifoOut      : slv(15 downto 0);
   
   signal sAxisMaster   : AxiStreamMasterType;
   signal imAxisMaster  : AxiStreamMasterType;
   signal sAxisSlave    : AxiStreamSlaveType;
   
   signal testModeSync  : sl;
   signal iRxValid      : sl;

  
   signal rxDataCs   : slv(19 downto 0);                 -- for chipscope
   signal rxValidCs  : sl;                               -- for chipscope
   attribute keep : string;                              -- for chipscope
   attribute keep of s : signal is "true";               -- for chipscope
   attribute keep of dFifoOut : signal is "true";        -- for chipscope
   attribute keep of dFifoSof : signal is "true";        -- for chipscope
   attribute keep of dFifoEof : signal is "true";        -- for chipscope
   attribute keep of dFifoEofe : signal is "true";       -- for chipscope
   attribute keep of dFifoValid : signal is "true";      -- for chipscope
   attribute keep of rxDataCs : signal is "true";        -- for chipscope
   attribute keep of rxValidCs : signal is "true";       -- for chipscope

   signal frameRate         : slv(31 downto 0);
   signal frameRateMax      : slv(31 downto 0);
   signal frameRateMin      : slv(31 downto 0);
   signal bandwidth         : slv(63 downto 0);
   signal bandwidthMax      : slv(63 downto 0);
   signal bandwidthMin      : slv(63 downto 0);

begin
   
   rxDataCs <= rxData;     -- for chipscope
   rxValidCs <= rxValid;   -- for chipscope

   U_rateMonitor : entity surf.AxiStreamMon
   generic map(
      TPD_G           => 1 ns,
      COMMON_CLK_G    => false,  -- true if axisClk = statusClk
      AXIS_CLK_FREQ_G => 156.25E+6,  -- units of Hz
      AXIS_CONFIG_G   => AXI_STREAM_CONFIG_O_C)
   port map(
      -- AXIS Stream Interface
      axisClk      => axisClk,
      axisRst      => axisRst,
      axisMaster   => imAxisMaster, 
      axisSlave    => mAxisSlave,
      -- Status Interface
      statusClk    => axilClk,
      statusRst    => axilRst,
      frameRate    => frameRate,
      frameRateMax => frameRateMax,
      frameRateMin => frameRateMin,
      bandwidth    => bandwidth,
      bandwidthMax => bandwidthMax,
      bandwidthMin => bandwidthMin
   );

   mAxisMaster <= imAxisMaster;

   
   -- synchronizers
   Sync1_U : entity surf.Synchronizer
   port map (
      clk     => rxClk,
      rst     => rxRst,
      dataIn  => s.testMode,
      dataOut => testModeSync
   );
   
   -- 8b10b decoder with SSP output
   Dec8b10b_U : entity surf.SspDecoder8b10b
   generic map (
      RST_POLARITY_G => '1'
   )
   port map (
      clk         => rxClk,
      rst         => rxRst,
      dataIn      => rxData,
      validIn     => iRxValid,
      dataOut     => decDataOut,
      validOut    => decValid,
      sof         => decSof,
      eof         => decEof,
      eofe        => decEofe
   );
   
   -- disable decoder in test mode (fake ASIC data)
   iRxValid <= rxValid and not testModeSync;
   
   -- async fifo for data
   -- for synchronization and small data pipeline
   -- not to store the whole frame
   DataFifo_U : entity surf.FifoCascade
   generic map (
      GEN_SYNC_FIFO_G   => false,
      FWFT_EN_G         => true,
      ADDR_WIDTH_G      => 4,
      DATA_WIDTH_G      => 19
   )
   port map (
      -- Resets
      rst               => rxRst,
      wr_clk            => rxClk,
      wr_en             => decValid,
      din(18)           => decSof,   
      din(17)           => decEof,   
      din(16)           => decEofe,   
      din(15 downto 0)  => decDataOut,
      --Read Ports (rd_clk domain)
      rd_clk            => axisClk,
      rd_en             => dFifoRd,
      dout(15 downto 0) => dFifoOut,
      dout(16)          => dFifoEofe,
      dout(17)          => dFifoEof,
      dout(18)          => dFifoSof,
      valid             => dFifoValid
   );
   
   -- axi stream fifo
   -- must be able to store whole frame if AXIS is muxed
   AxisFifo_U: entity surf.AxiStreamFifoV2
   generic map(
      GEN_SYNC_FIFO_G      => false,
      FIFO_ADDR_WIDTH_G    => 13,
      SLAVE_AXI_CONFIG_G   => AXI_STREAM_CONFIG_I_C,
      MASTER_AXI_CONFIG_G  => AXI_STREAM_CONFIG_O_C
   )
   port map(
      sAxisClk    => axisClk,
      sAxisRst    => axisRst,
      sAxisMaster => sAxisMaster,
      sAxisSlave  => sAxisSlave,
      mAxisClk    => axisClk,
      mAxisRst    => r.rstCnt(0),
      mAxisMaster => imAxisMaster,
      mAxisSlave  => mAxisSlave
   );

 
   
   comb : process (axilRst, axisRst, sAxilReadMaster, sAxilWriteMaster, sAxisSlave, r, s, 
      acqNo, dFifoOut, dFifoValid, dFifoSof, dFifoEof, dFifoEofe, testTrig, errInhibit,
      frameRate, frameRateMax, frameRateMin, bandwidth, bandwidthMax, bandwidthMin) is
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
      sv.errInhibit  := errInhibit;
      
      -- cross clock sync
      
      rv.frmSize      := s.frmSize;
      rv.frmMax       := s.frmMax;
      rv.frmMin       := s.frmMin;
      rv.frmCnt       := s.frmCnt;
      rv.sofError     := s.sofError;
      rv.eofError     := s.eofError;
      rv.ovError      := s.ovError;
      rv.frameRate    := frameRate;
      rv.frameRateMax := frameRateMax;
      rv.frameRateMin := frameRateMin;
      rv.bandwidth    := bandwidth;
      rv.bandwidthMax := bandwidthMax;
      rv.bandwidthMin := bandwidthMin;
      sv.testMode := r.testMode;

      if r.rstCnt /= "000" then
         sv.rstCnt := '1';
      else
         sv.rstCnt := '0';
      end if;
      
      -- axi lite logic 
      rv.rstCnt := r.rstCnt(1 downto 0) & '0';
      rv.sAxilReadSlave.rdata := (others => '0');
      axiSlaveWaitTxn(regCon, sAxilWriteMaster, sAxilReadMaster, rv.sAxilWriteSlave, rv.sAxilReadSlave);
      
      axiSlaveRegisterR(regCon, x"00", 0, r.frmCnt);
      axiSlaveRegisterR(regCon, x"04", 0, r.frmSize);
      axiSlaveRegisterR(regCon, x"08", 0, r.frmMax);
      axiSlaveRegisterR(regCon, x"0C", 0, r.frmMin);
      axiSlaveRegisterR(regCon, x"10", 0, r.sofError);
      axiSlaveRegisterR(regCon, x"14", 0, r.eofError);
      axiSlaveRegisterR(regCon, x"18", 0, r.ovError);
      axiSlaveRegister (regCon, x"1C", 0, rv.testMode);
      axiSlaveRegister (regCon, x"20", 0, rv.rstCnt);

      axiSlaveRegisterR(regCon, x"24", 0, r.frameRate);   
      axiSlaveRegisterR(regCon, x"28", 0, r.frameRateMax);   
      axiSlaveRegisterR(regCon, x"2C", 0, r.frameRateMin);   
      axiSlaveRegisterR(regCon, x"30", 0, r.bandwidth(31 downto 0));   
      axiSlaveRegisterR(regCon, x"34", 0, r.bandwidth(63 downto 32));   
      axiSlaveRegisterR(regCon, x"38", 0, r.bandwidthMax(31 downto 0));   
      axiSlaveRegisterR(regCon, x"3C", 0, r.bandwidthMax(63 downto 32));   
      axiSlaveRegisterR(regCon, x"40", 0, r.bandwidthMin(31 downto 0));   
      axiSlaveRegisterR(regCon, x"44", 0, r.bandwidthMin(63 downto 32));  
      axiSlaveRegister (regCon, x"48", 0, rv.numRowFD);  
      
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
            if (dFifoValid = '1' and dFifoSof = '1') or (s.testMode = '1' and s.testTrig(1) = '1' and s.testTrig(2) = '0') then
               -- start sending the header
               -- do not read the fifo yet
               sv.acqNo(1) := s.acqNo(0);
               sv.state := HDR_S;
               sv.testBitFlip := '0';
               sv.testColCnt := 0;
               sv.testRowCnt := 0;
            elsif dFifoValid = '1' then
               -- should not happen
               -- dump data and report an error
               if s.errInhibit = '0' then
                  sv.sofError := s.sofError + 1;
               end if;
               sv.dFifoRd := '1';
            end if;
         
         -- header is 6 x 16 bit words
         when HDR_S =>
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
               if s.testMode = '0' then
                  sv.axisMaster.tData(15 downto 0) := x"00" & "000" & "00" & ASIC_NO_G; -- Put the flag counter A or B here
               else
                  sv.axisMaster.tData(15 downto 0) := x"000" & s.testBitFlip & ASIC_NO_G;
               end if;
            else
               sv.axisMaster.tData(15 downto 0) := x"0000";
            end if;
         
         when DATA_S =>
            if dFifoValid = '1' or s.testMode = '1' then
               
               -- test mode row and col counters
               if s.testColCnt < 47 then
                  sv.testColCnt := s.testColCnt + 1;
               else
                  sv.testColCnt := 0;
                  sv.testRowCnt := s.testRowCnt + 1;
               end if;
               
               -- test or real data readout
               sv.axisMaster.tValid := '1';
               if s.testMode = '0' then
                  sv.axisMaster.tData(15 downto 0) := dFifoOut;
               else
                  if s.testColCnt = 23 then
                     sv.axisMaster.tData(15 downto 0) := ASIC_NO_G(1 downto 0) & s.testBitFlip & s.acqNo(1)(4 downto 0) & "00" & toSlv(s.testRowCnt, 6);
                  elsif s.testRowCnt = r.numRowFD then
                     sv.axisMaster.tData(15 downto 0) := ASIC_NO_G(1 downto 0) & s.testBitFlip & s.acqNo(1)(4 downto 0) & "00" & toSlv(s.testColCnt, 6);
                  else
                     sv.axisMaster.tData(15 downto 0) := ASIC_NO_G(1 downto 0) & s.testBitFlip & "00000" & x"ff";
                  end if;
               end if;
               sv.dFifoRd := '1';
               sv.stCnt := s.stCnt + 1;
               if ((dFifoEof = '1' or dFifoEofe = '1') and s.testMode = '0') or s.stCnt = ASIC_DATA_G then 
                  sv.frmSize := toSlv(s.stCnt, 32);
                  sv.stCnt := 0;
                  if s.frmMax <= sv.frmSize then
                     sv.frmMax := sv.frmSize;
                  end if;
                  if s.frmMin >= sv.frmSize then
                     sv.frmMin := sv.frmSize;
                  end if;
                  
                  if dFifoEofe = '1' or sv.frmSize /= ASIC_DATA_G then
                     ssiSetUserEofe(AXI_STREAM_CONFIG_I_C, sv.axisMaster, '1');
                     sv.eofError := s.eofError + 1;
                  else
                     sv.frmCnt := s.frmCnt + 1;
                  end if;
                  sv.axisMaster.tLast := '1';
                  if s.testMode = '0' then
                     sv.state := IDLE_S;
                  else
                     -- if test mode is enabled 
                     -- emulate second data set (toa and tot)
                     if s.testBitFlip = '0' then
                        sv.testBitFlip := '1';
                        sv.testColCnt := 0;
                        sv.testRowCnt := 0;
                        sv.state := HDR_S;
                     else
                        sv.state := IDLE_S;
                     end if;
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

