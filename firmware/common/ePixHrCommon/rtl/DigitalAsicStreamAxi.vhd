-------------------------------------------------------------------------------
-- File       : DigitalAsicStreamAxi.vhd
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

entity DigitalAsicStreamAxi is 
   generic (
      TPD_G           	   : time := 1 ns;
      VC_NO_G              : slv(3 downto 0)  := "0000";
      LANE_NO_G            : slv(3 downto 0)  := "0000";
      ASIC_NO_G            : slv(2 downto 0)  := "000";
      LANES_NO_G           : natural := 6;
      AXIL_ERR_RESP_G      : slv(1 downto 0)  := AXI_RESP_DECERR_C
   );
   port ( 
      -- Deserialized data port
      deserClk          : in  sl;
      deserRst          : in  sl;
      rxValid           : in  slv(LANES_NO_G-1 downto 0);
      rxData            : in  Slv16Array(LANES_NO_G-1 downto 0);
      rxSof             : in  slv(LANES_NO_G-1 downto 0);
      rxEof             : in  slv(LANES_NO_G-1 downto 0);
      rxEofe            : in  slv(LANES_NO_G-1 downto 0);
      
      
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
      
      -- readout request input
      startRdout        : in  sl
      
   );
end DigitalAsicStreamAxi;


-- Define architecture
architecture RTL of DigitalAsicStreamAxi is

   -- makes the fifo input with 2B per stream
   constant AXI_STREAM_CONFIG_I_C : AxiStreamConfigType   := ssiAxiStreamConfig(2*LANES_NO_G, TKEEP_COMP_C);
   constant AXI_STREAM_CONFIG_W_C : AxiStreamConfigType   := ssiAxiStreamConfig(48, TKEEP_COMP_C);
   constant AXI_STREAM_CONFIG_O_C : AxiStreamConfigType   := ssiAxiStreamConfig(16, TKEEP_COMP_C);--
   constant VECTOR_OF_ONES_C  : slv(15 downto 0) := (others => '1');
   constant VECTOR_OF_ZEROS_C : slv(15 downto 0) := (others => '0');
   -- PGP3 protocol is using 128bit (check for global constant for this configuration)
   
   type StateType is (IDLE_S, WAIT_SOF_S, HDR_S, DATA_S, TIMEOUT_S);
   
   type RegType is record
      state          : StateType;
      stateD1        : StateType;
      disableLane    : slv(LANES_NO_G-1 downto 0);
      enumDisLane    : slv(LANES_NO_G-1 downto 0);
      gainBitRemap   : slv(LANES_NO_G-1 downto 0);
      dataReqLane    : slv(15 downto 0);
      dataCntLane    : Slv16Array(LANES_NO_G-1 downto 0);
      dataCntLaneReg : Slv16Array(LANES_NO_G-1 downto 0);
      dataCntLaneMin : Slv16Array(LANES_NO_G-1 downto 0);
      dataCntLaneMax : Slv16Array(LANES_NO_G-1 downto 0);
      dataDlyLane    : Slv16Array(LANES_NO_G-1 downto 0);
      dataDlyLaneReg : Slv16Array(LANES_NO_G-1 downto 0);
      dataOvfLane    : Slv16Array(LANES_NO_G-1 downto 0);
      stCnt          : slv(15 downto 0);
      frmSize        : slv(15 downto 0);
      frmMax         : slv(15 downto 0);
      frmMin         : slv(15 downto 0);
      timeoutCntLane : Slv16Array(LANES_NO_G-1 downto 0);
      acqNo          : Slv32Array(1 downto 0);
      frmCnt         : slv(31 downto 0); 
      rstCnt         : sl;
      startRdSync    : slv(3 downto 0);
      dFifoRd        : slv(LANES_NO_G-1 downto 0);
      txMaster       : AxiStreamMasterType;
      axilWriteSlave : AxiLiteWriteSlaveType;
      axilReadSlave  : AxiLiteReadSlaveType;
   end record;

   constant REG_INIT_C : RegType := (
      state          => IDLE_S,
      stateD1        => IDLE_S,
      disableLane    => (others=>'0'),
      enumDisLane    => (others=>'0'),
      gainBitRemap   => (others=>'1'),
      dataReqLane    => (others=>'0'),
      dataCntLane    => (others=>(others=>'0')),
      dataCntLaneReg => (others=>(others=>'0')),
      dataCntLaneMin => (others=>(others=>'1')),
      dataCntLaneMax => (others=>(others=>'0')),
      dataDlyLane    => (others=>(others=>'0')),
      dataDlyLaneReg => (others=>(others=>'0')),
      dataOvfLane    => (others=>(others=>'0')),
      stCnt          => (others=>'0'),
      frmSize        => (others=>'0'),
      frmMax         => (others=>'0'),
      frmMin         => (others=>'1'),
      timeoutCntLane => (others=>(others=>'0')),
      acqNo          => (others=>(others=>'0')),
      frmCnt         => (others=>'0'),
      rstCnt         => '0',
      startRdSync    => (others=>'0'),
      dFifoRd        => (others=>'0'),
      txMaster       => AXI_STREAM_MASTER_INIT_C,
      axilWriteSlave => AXI_LITE_WRITE_SLAVE_INIT_C,
      axilReadSlave  => AXI_LITE_READ_SLAVE_INIT_C
   );
   
   signal r   : RegType := REG_INIT_C;
   signal rin : RegType;
   
   signal dFifoRd       : slv(LANES_NO_G-1 downto 0);
   signal dFifoEofe     : slv(LANES_NO_G-1 downto 0);
   signal dFifoEof      : slv(LANES_NO_G-1 downto 0);
   signal dFifoSof      : slv(LANES_NO_G-1 downto 0);
   signal dFifoValid    : slv(LANES_NO_G-1 downto 0);
   signal dFifoOut      : slv16Array(LANES_NO_G-1 downto 0);
   signal dFifoExtData  : slv(16*LANES_NO_G-1 downto 0) := (others => '0');
   signal dFifoRst      : sl;

   signal rxDataReMap   : Slv16Array(LANES_NO_G-1 downto 0);
   signal rxFull        : slv(LANES_NO_G-1 downto 0);
   
   signal startRdSync   : sl;
   
   signal txSlave          : AxiStreamSlaveType;
   signal sAxisMasterWide  : AxiStreamMasterType;
   signal sAxisSlaveWide   : AxiStreamSlaveType;
   
   signal acqNoSync     : slv(31 downto 0);
   
   signal axilWriteMaster  : AxiLiteWriteMasterType;
   signal axilWriteSlave   : AxiLiteWriteSlaveType;
   signal axilReadMaster   : AxiLiteReadMasterType;
   signal axilReadSlave    : AxiLiteReadSlaveType;

   
   attribute keep : string;
   attribute keep of r           : signal is "true";
   attribute keep of startRdSync : signal is "true";
   attribute keep of dFifoEofe   : signal is "true";
   attribute keep of dFifoEof    : signal is "true";
   attribute keep of dFifoSof    : signal is "true";
   attribute keep of dFifoValid  : signal is "true";
   
   
   
begin
   
   ----------------------------------------------------------------------------
   -- Cross clocking synchronizers
   ----------------------------------------------------------------------------
   
   AcqNoSync_U : entity surf.SynchronizerVector
   generic map (
      WIDTH_G => 32)
   port map (
      clk     => deserClk,
      rst     => deserRst,
      dataIn  => acqNo,
      dataOut => acqNoSync
   );
   
   SroSync_U : entity surf.SynchronizerEdge
   port map (
      clk         => deserClk,
      rst         => deserRst,
      dataIn      => startRdout,
      risingEdge  => startRdSync
   );
   
   AxilSync_U : entity surf.AxiLiteAsync
   port map (
      -- Slave Port
      sAxiClk         => axilClk,
      sAxiClkRst      => axilRst,
      sAxiWriteMaster => sAxilWriteMaster,
      sAxiWriteSlave  => sAxilWriteSlave,
      sAxiReadMaster  => sAxilReadMaster,
      sAxiReadSlave   => sAxilReadSlave,
      -- Master Port
      mAxiClk         => deserClk,
      mAxiClkRst      => deserRst,
      mAxiWriteMaster => axilWriteMaster,
      mAxiWriteSlave  => axilWriteSlave,
      mAxiReadMaster  => axilReadMaster,
      mAxiReadSlave   => axilReadSlave
   );
   
   ----------------------------------------------------------------------------
   -- Instatiate one FIFO per data stream.
   ----------------------------------------------------------------------------
   G_FIFO : for i in 0 to LANES_NO_G-1 generate
     
      -- ePixHR10k has the gian bit defined as LSB and it is remapped as MSB.
      U_GainBitReMap : process (rxData, r)
      begin
        if (r.gainBitRemap(i) = '1') then
          rxDataReMap(i)(14 downto 0)   <= rxData(i)(15 downto 1);
          rxDataReMap(i)(15)            <= rxData(i)(0);
        else
          rxDataReMap(i) <= rxData(i);
        end if;
      end process;       
   
      -- async fifo for data
      DataFifo_U : entity surf.FifoCascade
      generic map (
         GEN_SYNC_FIFO_G   => true,
         FWFT_EN_G         => true,
         ADDR_WIDTH_G      => 9,
         DATA_WIDTH_G      => 19
         )
      port map (
         rst               => dFifoRst,
         wr_clk            => deserClk,
         wr_en             => rxValid(i),
         full              => rxFull(i),
         din(15 downto 0)  => rxDataReMap(i),
         din(16)           => rxEofe(i),
         din(17)           => rxEof(i),
         din(18)           => rxSof(i),
         rd_clk            => deserClk,
         rd_en             => dFifoRd(i),
         dout(15 downto 0) => dFifoOut(i),
         dout(16)          => dFifoEofe(i),
         dout(17)          => dFifoEof(i),
         dout(18)          => dFifoSof(i),
         valid             => dFifoValid(i)
      );
      
      -- in cPix seeing corrupted junk being stuck in one of the lanes 
      -- this can only be cleared by the FSM stuck waiting for data
      dFifoRst <= deserRst or startRdSync;
      
      
      dataExt : process(dFifoOut, r.disableLane, r.enumDisLane)
      begin
         if r.disableLane(i) = '1' then
            if r.enumDisLane(i) = '0' then
               dFifoExtData(16*i+15 downto 16*i) <= (others => '0');
            else
               dFifoExtData(16*i+15 downto 16*i) <= toSlv(i,16);
            end if;
         else
            dFifoExtData(16*i+15 downto 16*i) <= dFifoOut(i);
         end if;
      end process;
         
   end generate;


   comb : process (deserRst, axilReadMaster, axilWriteMaster, txSlave, r, 
      acqNoSync, dFifoExtData, dFifoValid, dFifoSof, dFifoEof, dFifoEofe, startRdSync, rxValid, rxSof, rxEof, rxEofe, rxFull) is
      variable v        : RegType;
      variable regCon   : AxiLiteEndPointType;
   begin
      v := r;
      
      v.rstCnt := '0';
      v.dFifoRd := (others=>'0');
      v.stateD1 := r.state;
      v.startRdSync(3) := startRdSync;
      v.startRdSync(2) := r.startRdSync(3);
      v.startRdSync(1) := r.startRdSync(2);
      v.startRdSync(0) := r.startRdSync(1);
      
      axiSlaveWaitTxn(regCon, axilWriteMaster, axilReadMaster, v.axilWriteSlave, v.axilReadSlave);
      
      axiSlaveRegisterR(regCon, x"000",  0, r.frmCnt);
      axiSlaveRegisterR(regCon, x"004",  0, r.frmSize);
      axiSlaveRegisterR(regCon, x"008",  0, r.frmMax);
      axiSlaveRegisterR(regCon, x"00C",  0, r.frmMin);
      axiSlaveRegister (regCon, x"024",  0, v.rstCnt);
      axiSlaveRegister (regCon, x"028",  0, v.dataReqLane);
      axiSlaveRegister (regCon, x"02C",  0, v.disableLane);
      axiSlaveRegister (regCon, x"030",  0, v.enumDisLane);
      axiSlaveRegister (regCon, x"034",  0, v.gainBitRemap);
      
      for i in 0 to (LANES_NO_G-1) loop
         axiSlaveRegisterR(regCon, x"100"+toSlv(i*4,12),  0, r.timeoutCntLane(i));
         axiSlaveRegisterR(regCon, x"200"+toSlv(i*4,12),  0, r.dataCntLane(i));
         axiSlaveRegisterR(regCon, x"300"+toSlv(i*4,12),  0, r.dataCntLaneReg(i));
         axiSlaveRegisterR(regCon, x"400"+toSlv(i*4,12),  0, r.dataCntLaneMin(i));
         axiSlaveRegisterR(regCon, x"500"+toSlv(i*4,12),  0, r.dataCntLaneMax(i));
         axiSlaveRegisterR(regCon, x"600"+toSlv(i*4,12),  0, r.dataDlyLaneReg(i));
         axiSlaveRegisterR(regCon, x"700"+toSlv(i*4,12),  0, r.dataOvfLane(i));
      end loop;
      
      axiSlaveDefault(regCon, v.axilWriteSlave, v.axilReadSlave, AXIL_ERR_RESP_G);
      
      -- axi stream logic

      -- sync acquisition number
      v.acqNo(0) := acqNoSync;
      
      
      
      -- Reset strobing Signals
      if (txSlave.tReady = '1') then
         v.txMaster.tValid := '0';
         v.txMaster.tLast  := '0';
         v.txMaster.tUser  := (others => '0');
         v.txMaster.tKeep  := (others => '1');
         v.txMaster.tStrb  := (others => '1');
      end if;
      
      case r.state is
         when IDLE_S =>
            if startRdSync = '1' then
               v.state := WAIT_SOF_S;
            end if;
            
            
         when WAIT_SOF_S =>
         
            --keeps flushing data until all SOF show up
            for i in 0 to (LANES_NO_G-1) loop
               if dFifoSof(i) = '0' and dFifoValid(i) = '1' then
                  v.dFifoRd(i) := '1';
               end if;             
            end loop;
            
            -- next SRO while waiting for previous SOF
            for i in 0 to (LANES_NO_G-1) loop
               if startRdSync = '1' and dFifoSof(i) = '0' then
                  v.timeoutCntLane(i) := r.timeoutCntLane(i) + 1;
               end if;
            end loop;
            
            if ((dFifoSof(LANES_NO_G-1 downto 0) or r.disableLane) = VECTOR_OF_ONES_C(LANES_NO_G-1 downto 0)) then
               v.acqNo(1) := r.acqNo(0);
               v.state := HDR_S;
            end if;
            v.stCnt := (others=>'0');
           
         when HDR_S =>
            ------------------------------------------------------------------
            -- HEADER
            ------------------------------------------------------------------    
            if v.txMaster.tValid = '0' then
               v.txMaster.tValid := '1';
               v.state := DATA_S;
               v.txMaster.tData(31 downto  0) := x"0000" & x"00" & LANE_NO_G & VC_NO_G;
               v.txMaster.tData(63 downto 32) := r.acqNo(1)(31 downto 0);
               v.txMaster.tData(79 downto 64) := x"000" & '0' & ASIC_NO_G;
               v.txMaster.tData(95 downto 80) := x"0000";
               ssiSetUserSof(AXI_STREAM_CONFIG_I_C, v.txMaster, '1');
            end if;
             
         when DATA_S =>
            if ((dFifoValid or r.disableLane) = VECTOR_OF_ONES_C(LANES_NO_G-1 downto 0)) and v.txMaster.tValid = '0' then
               
               v.txMaster.tValid := '1';
               v.txMaster.tData(16*LANES_NO_G-1 downto 0) := dFifoExtData;
               
               v.dFifoRd := (others=>'1');
                           
               v.stCnt := r.stCnt + 1;
               if r.stCnt = r.dataReqLane then 
                  v.frmSize := r.stCnt;
                  v.stCnt := (others=>'0');
                  
                  if r.frmMax <= v.frmSize then
                     v.frmMax := v.frmSize;
                  end if;
                  
                  if r.frmMin >= v.frmSize then
                     v.frmMin := v.frmSize;
                  end if;
                  
                  v.frmCnt := r.frmCnt + 1;
                  
                  v.txMaster.tLast := '1';
                  ssiSetUserEofe(AXI_STREAM_CONFIG_I_C, v.txMaster, '0');
                  v.state := IDLE_S;
               end if;  
            
            elsif startRdSync = '1' then
               v.state := TIMEOUT_S;
               for i in 0 to (LANES_NO_G-1) loop
                  if (dFifoValid(i) or r.disableLane(i)) = '0' then
                     v.timeoutCntLane(i) := r.timeoutCntLane(i) + 1;
                  end if;
               end loop;
            end if;
         
         when TIMEOUT_S =>
            if v.txMaster.tValid = '0' then
               v.txMaster.tLast := '1';
               v.txMaster.tValid := '1';
               ssiSetUserEofe(AXI_STREAM_CONFIG_I_C, v.txMaster, '1');
               v.state := WAIT_SOF_S;
            end if;
         
         when others =>
      end case;
      
      -- reset counters
      if r.rstCnt = '1' then
         v.frmCnt          := (others=>'0');
         v.frmSize         := (others=>'0');
         v.frmMax          := (others=>'0');
         v.frmMin          := (others=>'1');
         v.timeoutCntLane  := (others=>(others=>'0'));
      end if;
      
      -- counters on the write side of the lane's buffer FIFO
      for i in 0 to (LANES_NO_G-1) loop
         
         -- count incoming data per lane
         -- store min and max
         if r.rstCnt = '1' then
            v.dataCntLaneReg(i)  := (others=>'0');
            v.dataCntLaneMin(i)  := (others=>'1');
            v.dataCntLaneMax(i)  := (others=>'0');
            v.dataCntLane(i)     := (others=>'0');
         elsif (r.stateD1 = DATA_S and r.state /= DATA_S) then -- update actual, min, max register when leaving DATA_S (on timeout or normally)
            v.dataCntLaneReg(i) := r.dataCntLane(i);
            if r.dataCntLaneMax(i) <= r.dataCntLane(i) then
               v.dataCntLaneMax(i) := r.dataCntLane(i);
            end if;
            if r.dataCntLaneMin(i) >= r.dataCntLane(i) then
               v.dataCntLaneMin(i) := r.dataCntLane(i);
            end if;
         elsif r.startRdSync(0) = '1' then                     -- startRdSync must be delayed few cycles as the same signal is taking the FSM out from DATA_S (condition above)
            v.dataCntLane(i) := (others=>'0');                 -- reset counter before next data cycle
         elsif rxValid(i) = '1' and rxSof(i) = '0' then
            v.dataCntLane(i) := r.dataCntLane(i) + 1;
         end if;
         
         -- count delay from SRO to SOF
         if r.rstCnt = '1' then
            v.dataDlyLaneReg(i)  := (others=>'0');
            v.dataDlyLane(i)     := (others=>'0');
         elsif startRdSync = '1' then
            v.dataDlyLane(i) := (others=>'0');
         elsif (r.stateD1 = WAIT_SOF_S and r.state /= WAIT_SOF_S) then
            v.dataDlyLaneReg(i) := r.dataDlyLane(i);
         elsif dFifoSof(i) = '0' and r.dataDlyLane(i) /= x"ffff" then
            v.dataDlyLane(i) := r.dataDlyLane(i) + 1;
         end if;
         
         -- count writes to full FIFO (overflow)
         if r.rstCnt = '1' then
            v.dataOvfLane(i) := (others=>'0');
         elsif rxFull(i) = '1' and rxValid(i) = '1' and r.dataOvfLane(i) /= x"ffff" then
            v.dataOvfLane(i) := r.dataOvfLane(i) + 1;
         end if;
         
      end loop;

      -- reset logic      
      if (deserRst = '1') then
         v := REG_INIT_C;
      end if;

      -- outputs
      
      rin <= v;

      axilWriteSlave <= r.axilWriteSlave;
      axilReadSlave  <= r.axilReadSlave;
      dFifoRd        <= v.dFifoRd;

   end process comb;

   seq : process (deserClk) is
   begin
      if (rising_edge(deserClk)) then
         r <= rin after TPD_G;
      end if;
   end process seq;
   
   
   ----------------------------------------------------------------------------
   -- axi stream fifo
   -- deserializer clock to axis clock crossing
   -- gearbox 4/3 by double stream resizing 
   -- must be able to store whole frame if AXIS is muxed
   ----------------------------------------------------------------------------
   AxisResize12to48_U: entity surf.AxiStreamFifoV2
   generic map(
      GEN_SYNC_FIFO_G      => false,
      FIFO_ADDR_WIDTH_G    => 11,
      CASCADE_SIZE_G       => 1,
      INT_WIDTH_SELECT_G   => "WIDE",
      SLAVE_AXI_CONFIG_G   => AXI_STREAM_CONFIG_I_C,
      MASTER_AXI_CONFIG_G  => AXI_STREAM_CONFIG_W_C
   )
   port map(
      sAxisClk    => deserClk,
      sAxisRst    => deserRst,
      sAxisMaster => r.txMaster,
      sAxisSlave  => txSlave,
      mAxisClk    => axisClk,
      mAxisRst    => axisRst,
      mAxisMaster => sAxisMasterWide,
      mAxisSlave  => sAxisSlaveWide
   );
   
   
   AxisResize48to16_U: entity surf.AxiStreamResize
   generic map(
      -- General Configurations
      TPD_G      => TPD_G,
      READY_EN_G => true,
      -- AXI Stream Port Configurations
      SLAVE_AXI_CONFIG_G  => AXI_STREAM_CONFIG_W_C,
      MASTER_AXI_CONFIG_G => AXI_STREAM_CONFIG_O_C
      )
   port map(
      -- Clock and reset
      axisClk     => axisClk,
      axisRst     => axisRst,
      -- Slave Port
      sAxisMaster => sAxisMasterWide,
      sAxisSlave  => sAxisSlaveWide,
      -- Master Port
      mAxisMaster => mAxisMaster,
      mAxisSlave  => mAxisSlave
   );
   

end RTL;
