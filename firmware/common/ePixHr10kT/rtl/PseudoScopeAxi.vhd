-------------------------------------------------------------------------------
-- Title      : Pseudo Oscilloscope Interface
-- Project    : EPIX 
-------------------------------------------------------------------------------
-- File       : PseudoScopeAxi.vhd
-- Company    : SLAC National Accelerator Laboratory
-------------------------------------------------------------------------------
-- Description:
-- Pseudo-oscilloscope interface for ADC channels, similar to chipscope.
-------------------------------------------------------------------------------
-- This file is part of 'EPIX Development Firmware'.
-- It is subject to the license terms in the LICENSE.txt file found in the 
-- top-level directory of this distribution and at: 
--    https://confluence.slac.stanford.edu/display/ppareg/LICENSE.html. 
-- No part of 'EPIX Development Firmware', including this file, 
-- may be copied, modified, propagated, or distributed except according to 
-- the terms contained in the LICENSE.txt file.
-------------------------------------------------------------------------------

LIBRARY ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

library surf;
use surf.StdRtlPkg.all;
use surf.AxiStreamPkg.all;
use surf.AxiLitePkg.all;
use surf.SsiPkg.all;

use work.ScopeTypes.all;

entity PseudoScopeAxi is
   generic (
      TPD_G                      : time                  := 1 ns;
      MASTER_AXI_STREAM_CONFIG_G : AxiStreamConfigType   := ssiAxiStreamConfig(4, TKEEP_COMP_C);
      AXIL_ERR_RESP_G            : slv(1 downto 0)       := AXI_RESP_OK_C
   );
   port ( 

      -- Master system clock
      sysClk          : in  sl;
      sysClkRst       : in  sl;

      -- ADC data
      adcData         : in  Slv16Array(3 downto 0);
      adcValid        : in  slv(3 downto 0);

      -- Signal for auto-rearm of trigger
      arm             : in  sl;
      
      -- Potential triggers in
      triggerIn       : in  slv(11 downto 0);
      
      -- Data out interface
      mAxisMaster     : out  AxiStreamMasterType;
      mAxisSlave      : in   AxiStreamSlaveType;
      
      -- AXI lite slave port for register access
      axilClk           : in  sl;
      axilRst           : in  sl;
      sAxilWriteMaster  : in  AxiLiteWriteMasterType;
      sAxilWriteSlave   : out AxiLiteWriteSlaveType;
      sAxilReadMaster   : in  AxiLiteReadMasterType;
      sAxilReadSlave    : out AxiLiteReadSlaveType

   );
end PseudoScopeAxi;


-- Define architecture
architecture rtl of PseudoScopeAxi is
   signal overThresholdA   : sl := '0';
   signal overThresholdB   : sl := '0';
   signal autoTrigger      : sl := '0';
   signal trigger_sel      : sl := '0';
   signal trigger          : sl := '0';
   signal triggerRising    : sl := '0';
   signal triggerFalling   : sl := '0';
   signal triggerToUse     : sl := '0';
   signal triggerEdgeSel   : sl := '0';
   signal armed            : sl := '0';
   signal triggerDelayed   : sl := '0';
   signal triggerDelayEdge : sl := '0';
   signal trigDelCnt       : integer;
   signal triggerChannel   : integer range 0 to 15 := 0;
   signal triggerMode      : integer range 0 to 3  := 0;
   signal adcChA           : slv(15 downto 0);
   signal adcChB           : slv(15 downto 0);
   signal adcChAValid      : sl;
   signal adcChBValid      : sl;
   signal bufferReadyA     : sl;
   signal bufferReadyB     : sl;
   signal bufferDataA      : slv(15 downto 0);
   signal bufferDataB      : slv(15 downto 0);
   signal bufferRdEnA      : sl;
   signal bufferRdEnB      : sl;
   signal bufferDoneA      : sl;
   signal bufferDoneB      : sl;
   signal wordCntRst       : sl;
   signal wordCntEn        : sl;
   signal wordCnt          : unsigned(3 downto 0);
   signal oddEven          : sl := '0';
   signal oddEvenToggle    : sl;
   signal oddEvenRst       : sl;
   signal armSelect        : sl;
   signal triggerAdcThresh : unsigned(15 downto 0);
   signal iAxisMaster      : AxiStreamMasterType;
   signal adcWordPackedA   : slv(31 downto 0) := (others => '0');
   signal adcWordPackedB   : slv(31 downto 0) := (others => '0');

   type StateType is (
      IDLE_S,
      START_HDR_S,
      WAIT_SCOPE_S,
      FIRST_WORD_A_S,
      SCOPE_DATA_A_S,
      FIRST_WORD_B_S,
      SCOPE_DATA_B_S,
      STOP_S);
   signal curState : StateType := IDLE_S;
   signal nxtState : StateType := IDLE_S;

   -- Hard coded words in the data stream
   -- Some may be updated later.
   constant cLane     : slv( 1 downto 0) := "00";
   constant cVC       : slv( 1 downto 0) := "10";
   constant cQuad     : slv( 1 downto 0) := "00";
   constant cOpCode   : slv( 7 downto 0) := x"00";
   constant cZeroWord : slv(31 downto 0) := x"00000000";
   
   signal scopeSync    : ScopeConfigType;
   
   type RegType is record
      scope             : ScopeConfigType;
      sAxilWriteSlave   : AxiLiteWriteSlaveType;
      sAxilReadSlave    : AxiLiteReadSlaveType;
   end record RegType;

   constant REG_INIT_C : RegType := (
      scope             => SCOPE_CONFIG_INIT_C,
      sAxilWriteSlave   => AXI_LITE_WRITE_SLAVE_INIT_C,
      sAxilReadSlave    => AXI_LITE_READ_SLAVE_INIT_C
   );
   
   signal r   : RegType := REG_INIT_C;
   signal rin : RegType;

begin

   -- Output
   mAxisMaster <= iAxisMaster;
   
   -- Type conversions
   triggerChannel   <= to_integer(unsigned(scopeSync.triggerChannel));
   triggerAdcThresh <= unsigned(scopeSync.triggerAdcThresh);
   triggerMode      <= to_integer(unsigned(scopeSync.triggerMode));

   -- Arming mode
   armSelect <= '0'             when triggerMode = 0 else
                scopeSync.arm when triggerMode = 1 else
                arm             when triggerMode = 2 else
                '1';

   -- Trigger multiplexing
   trigger_sel <= 
      scopeSync.trig   when triggerChannel =  0 else
      overThresholdA   when triggerChannel =  1 else
      overThresholdB   when triggerChannel =  2 else
      triggerIn(0)     when triggerChannel =  3 else
      triggerIn(1)     when triggerChannel =  4 else
      triggerIn(2)     when triggerChannel =  5 else
      triggerIn(3)     when triggerChannel =  6 else
      triggerIn(4)     when triggerChannel =  7 else
      triggerIn(5)     when triggerChannel =  8 else
      triggerIn(6)     when triggerChannel =  9 else
      triggerIn(7)     when triggerChannel = 10 else
      triggerIn(8)     when triggerChannel = 11 else
      triggerIn(9)     when triggerChannel = 12 else
      triggerIn(10)    when triggerChannel = 13 else
      triggerIn(11)    when triggerChannel = 14 else
      '0'              when triggerChannel = 15 else
      'X';
   
   -- Trigger enable
   trigger <= trigger_sel and scopeSync.scopeEnable;

   -- Generate edges of the possible trigger signals
   U_RunEdge : entity surf.SynchronizerEdge 
      port map (
         clk         => sysClk,
         rst         => sysClkRst,
         dataIn      => trigger,
         risingEdge  => triggerRising,
         fallingEdge => triggerFalling
      ); 

   -- And make the final trigger output
   triggerEdgeSel <= 
      triggerRising  when scopeSync.triggerEdge = '1' else
      triggerFalling when scopeSync.triggerEdge = '0' else
      'X';
   
   -- trigger delay
   process (sysClk)
   begin
      if rising_edge(sysClk) then
         if sysClkRst = '1' or (triggerEdgeSel = '1' and armed = '0') then
            trigDelCnt <= to_integer(unsigned(scopeSync.triggerDelay));
         elsif trigDelCnt /= 0 then
            trigDelCnt <= trigDelCnt - 1;
         end if;
         
         if sysClkRst = '1' or triggerDelayed = '1' then
            armed <= '0';
         elsif triggerEdgeSel = '1' then
            armed <= '1';
         end if;
      end if;
   end process;
   
   triggerDelayed <= '1' when trigDelCnt = 0 else '0';
   
   U_DelEdge : entity surf.SynchronizerEdge 
      port map (
         clk         => sysClk,
         rst         => sysClkRst,
         dataIn      => triggerDelayed,
         risingEdge  => triggerDelayEdge,
         fallingEdge => open
      ); 
   
   triggerToUse <= triggerEdgeSel when unsigned(scopeSync.triggerDelay) = 0 else triggerDelayEdge;

   -- Logic for the levels on the ADCs
   process(sysClk) begin
      if rising_edge(sysClk) then
         if (unsigned(adcChA) > triggerAdcThresh) then
            overThresholdA  <= '1';
         else
            overThresholdA  <= '0';
         end if;
         if (unsigned(adcChB) > triggerAdcThresh) then
            overThresholdB  <= '1';
         else
            overThresholdB  <= '0';
         end if;
      end if;
   end process;

   -- Input channel multiplexing
   adcChA <= adcData(to_integer(unsigned(scopeSync.inputChannelA)));
   adcChB <= adcData(to_integer(unsigned(scopeSync.inputChannelB)));
   adcChAValid <= adcValid(to_integer(unsigned(scopeSync.inputChannelA)));
   adcChBValid <= adcValid(to_integer(unsigned(scopeSync.inputChannelB)));

   -- Instantiate ring buffers for storing the ADC data
   RingBufferA : entity work.RingBuffer
      generic map(
         MEMORY_TYPE_G=> "block",
         DATA_WIDTH_G => 16,
         ADDR_WIDTH_G => 13)
      port map (
         sysClk      => sysClk,
         sysClkRst   => sysClkRst,
         wrData      => adcChA,
         wrValid     => adcChAValid,
         arm         => armSelect,
         rdEn        => bufferRdEnA,
         rdData      => bufferDataA,
         rdReady     => bufferReadyA, 
         rdDone      => bufferDoneA,
         trigger     => triggerToUse,
         holdoff     => scopeSync.triggerHoldoff,
         offset      => scopeSync.triggerOffset,
         skipSamples => scopeSync.skipSamples,
         depth       => scopeSync.traceLength
      );
   RingBufferB : entity work.RingBuffer
      generic map(
         MEMORY_TYPE_G=> "block",
         DATA_WIDTH_G => 16,
         ADDR_WIDTH_G => 13)
      port map (
         sysClk      => sysClk,
         sysClkRst   => sysClkRst,
         wrData      => adcChB,
         wrValid     => adcChBValid,
         arm         => armSelect,
         rdEn        => bufferRdEnB,
         rdData      => bufferDataB,
         rdReady     => bufferReadyB, 
         rdDone      => bufferDoneB,
         trigger     => triggerToUse,
         holdoff     => scopeSync.triggerHoldoff,
         offset      => scopeSync.triggerOffset,
         skipSamples => scopeSync.skipSamples,
         depth       => scopeSync.traceLength
      );

   --State machine to send out the data

   --Synchronous part
   process(sysClk) begin
      if rising_edge(sysClk) then
         if (sysClkRst = '1' or scopeSync.scopeEnable = '0') then
            curState <= IDLE_S;
         else
            curState <= nxtState;
         end if;
      end if;
   end process;

   process(curState,wordCnt,bufferReadyA,bufferReadyB,bufferDataA,bufferDataB,
           oddEven,mAxisSlave,triggerToUse,bufferDoneA,bufferDoneB,
           adcWordPackedA,adcWordPackedB,bufferRdEnA,bufferRdEnB) 
      variable vAxisMaster : AxiStreamMasterType;
   begin
      vAxisMaster := AXI_STREAM_MASTER_INIT_C;
      --Defaults
      ssiResetFlags(vAxisMaster);
      vAxisMaster.tData  := (others => '0');
      bufferRdEnA        <= '0';
      bufferRdEnB        <= '0';
      wordCntRst         <= '0';
      wordCntEn          <= '0';
      oddEvenRst         <= '0';
      oddEvenToggle      <= '0';
      nxtState           <= curState;
      if (mAxisSlave.tReady = '1') then
         case curState is
            when IDLE_S =>
               if triggerToUse = '1' then
                  wordCntRst <= '1';
                  nxtState   <= WAIT_SCOPE_S;
               end if;
            when WAIT_SCOPE_S =>
               if bufferReadyA = '1' and bufferReadyB = '1' then
                  oddEvenRst  <= '1';
                  nxtState    <= START_HDR_S;
               end if;
            when START_HDR_S =>
               wordCntEn          <= '1';
               vAxisMaster.tValid := '1';
               case to_integer(wordCnt) is
                  when 0 => vAxisMaster.tData(31 downto 0) := x"000000" & "00" & cLane & "00" & cVC;
                            ssiSetUserSof(MASTER_AXI_STREAM_CONFIG_G, vAxisMaster, '1');
                  when 1 => vAxisMaster.tData(31 downto 0) := x"0" & "00" & cQuad & cOpCode & x"0000";
                  when 2 => vAxisMaster.tData(31 downto 0) := cZeroWord;
                  when 3 => vAxisMaster.tData(31 downto 0) := cZeroWord;
                  when 4 => vAxisMaster.tData(31 downto 0) := cZeroWord;
                  when 5 => vAxisMaster.tData(31 downto 0) := cZeroWord;
                  when 6 => vAxisMaster.tData(31 downto 0) := cZeroWord;
                  when 7 => vAxisMaster.tData(31 downto 0) := cZeroWord;
                            nxtState <= FIRST_WORD_A_S;
                  when others  => vAxisMaster.tData(31 downto 0) := cZeroWord;
               end case;
            when FIRST_WORD_A_S =>
               bufferRdEnA            <= '1';
               oddEvenToggle          <= '1';
               if oddEven = '1' then
                  nxtState               <= SCOPE_DATA_A_S;
               end if;
            when SCOPE_DATA_A_S =>
               bufferRdEnA            <= '1';
               oddEvenToggle          <= '1';
               vAxisMaster.tData(31 downto 0) := adcWordPackedA;
               if (bufferRdEnA = '1' and oddEven = '1') then
                  vAxisMaster.tValid := '1';
               end if;
               if bufferDoneA = '1' then
                  --iFrameTxIn.valid <= '1';  --force write if odd size
                  oddEvenRst               <= '1';
                  nxtState                 <= FIRST_WORD_B_S;
               end if;
            when FIRST_WORD_B_S =>
               bufferRdEnB            <= '1';
               oddEvenToggle          <= '1';
               if oddEven = '1' then
                  nxtState               <= SCOPE_DATA_B_S;
               end if;
            when SCOPE_DATA_B_S =>
               bufferRdEnB            <= '1';
               oddEvenToggle          <= '1';
               vAxisMaster.tData(31 downto 0) := adcWordPackedB;
               if (bufferRdEnB = '1' and oddEven = '1') then
                  vAxisMaster.tValid := '1';
               end if;
               if bufferDoneB = '1' then
                  --iFrameTxIn.valid <= '1';  --force write if odd size
                  oddEvenRst               <= '1';
                  wordCntRst               <= '1';
                  nxtState                 <= STOP_S;
               end if; 
            when STOP_S =>
               vAxisMaster.tData(31 downto 0) := cZeroWord;
               vAxisMaster.tValid             := '1';
               wordCntEn                      <= '1';
               if wordCnt = 4 then
                  vAxisMaster.tLast := '1';
                  nxtState <= IDLE_S;
               end if;
            when others =>
         end case;
      end if;
      iAxisMaster <= vAxisMaster;
   end process;

   --Odd even counter used for packing words
   process(sysClk) begin
      if rising_edge(sysClk) then
         if oddEvenRst = '1' then
            oddEven <= '0';
         elsif oddEvenToggle = '1' then
            oddEven <= not(oddEven);
         end if;
      end if;
   end process;
   --Pack 16-bit ADC values into 32 bit words
   process(sysClk) begin
      if rising_edge(sysClk) then
         if oddEven = '1' then
            --adcWordPackedA <= x"0000" & x"A" & bufferDataA(11 downto 0);
            --adcWordPackedB <= x"0000" & x"B" & bufferDataB(11 downto 0);
            adcWordPackedA <= x"0000" & bufferDataA;
            adcWordPackedB <= x"0000" & bufferDataB;
         else
            adcWordPackedA(31 downto 16) <= bufferDataA;
            adcWordPackedB(31 downto 16) <= bufferDataB;
         end if;
      end if;
   end process;

   --Counts the number of words to choose what data to send next
   process(sysClk) begin
      if rising_edge(sysClk) then
         if sysClkRst = '1' or wordCntRst = '1' then
            wordCnt <= (others => '0');
         elsif wordCntEn = '1' then
            wordCnt <= wordCnt + 1;
         end if; 
      end if; 
   end process;
   
   --------------------------------------------------
   -- AXI Lite register logic
   --------------------------------------------------

   comb : process (axilRst, sAxilReadMaster, sAxilWriteMaster, r) is
      variable v        : RegType;
      variable regCon   : AxiLiteEndPointType;
   begin
      v := r;
      
      v.scope.arm          := '0';
      v.scope.trig         := '0';
      
      axiSlaveWaitTxn(regCon, sAxilWriteMaster, sAxilReadMaster, v.sAxilWriteSlave, v.sAxilReadSlave);
      
      axiSlaveRegister (regCon, x"00",  0, v.scope.arm);
      axiSlaveRegister (regCon, x"04",  0, v.scope.trig);
      axiSlaveRegister (regCon, x"08",  0, v.scope.scopeEnable);
      axiSlaveRegister (regCon, x"08",  1, v.scope.triggerEdge);
      axiSlaveRegister (regCon, x"08",  2, v.scope.triggerChannel);
      axiSlaveRegister (regCon, x"08",  6, v.scope.triggerMode);
      axiSlaveRegister (regCon, x"08", 16, v.scope.triggerAdcThresh);
      axiSlaveRegister (regCon, x"0C",  0, v.scope.triggerHoldoff);
      axiSlaveRegister (regCon, x"0C", 13, v.scope.triggerOffset);
      axiSlaveRegister (regCon, x"10",  0, v.scope.traceLength);
      axiSlaveRegister (regCon, x"10", 13, v.scope.skipSamples);
      axiSlaveRegister (regCon, x"14",  0, v.scope.inputChannelA);
      axiSlaveRegister (regCon, x"14",  5, v.scope.inputChannelB);
      axiSlaveRegister (regCon, x"18",  0, v.scope.triggerDelay);
      
      axiSlaveDefault(regCon, v.sAxilWriteSlave, v.sAxilReadSlave, AXIL_ERR_RESP_G);
      
      if (axilRst = '1') then
         v := REG_INIT_C;
      end if;

      rin <= v;

      sAxilWriteSlave   <= r.sAxilWriteSlave;
      sAxilReadSlave    <= r.sAxilReadSlave;

   end process comb;

   seq : process (axilClk) is
   begin
      if (rising_edge(axilClk)) then
         r <= rin after TPD_G;
      end if;
   end process seq;
   
   --sync registers to sysClk clock
   process(sysClk) begin
      if rising_edge(sysClk) then
         if sysClkRst = '1' then
            scopeSync <= SCOPE_CONFIG_INIT_C after TPD_G;
         else
            scopeSync <= r.scope after TPD_G;
         end if;
      end if;
   end process;
   

end rtl;

