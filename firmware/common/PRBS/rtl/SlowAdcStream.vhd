-------------------------------------------------------------------------------
-- File       : SlowAdcStream.vhd
-- Company    : SLAC National Accelerator Laboratory
-------------------------------------------------------------------------------
-- Description: EPIX slow ADC stream
-------------------------------------------------------------------------------
-- This file is part of 'EPIX Development Firmware'.
-- It is subject to the license terms in the LICENSE.txt file found in the 
-- top-level directory of this distribution and at: 
--    https://confluence.slac.stanford.edu/display/ppareg/LICENSE.html. 
-- No part of 'EPIX Development Firmware', including this file, 
-- may be copied, modified, propagated, or distributed except according to 
-- the terms contained in the LICENSE.txt file.
-------------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

library surf;
use surf.StdRtlPkg.all;
use surf.AxiStreamPkg.all;
use surf.SsiPkg.all;

library unisim;
use unisim.vcomponents.all;

entity SlowAdcStream is
   generic (
      TPD_G                      : time      := 1 ns;
      MASTER_AXI_STREAM_CONFIG_G : AxiStreamConfigType := ssiAxiStreamConfig(4)
   );
   port (
      -- global signals
      sysClk               : in  sl;
      sysRst               : in  sl;
      
      acqCount             : in  slv(31 downto 0);
      seqCount             : in  slv(31 downto 0);
      
      -- trigger inputs
      trig                 : in  sl;
      
      -- ADC data input signals
      dataIn               : in  Slv32Array(8 downto 0);
      
      -- Data out interface
      mAxisMaster          : out AxiStreamMasterType;
      mAxisSlave           : in  AxiStreamSlaveType
   );
end SlowAdcStream;

architecture rtl of SlowAdcStream is

   constant HEADER_SIZE_C           : natural   := 7;
   
   TYPE STATE_TYPE IS (IDLE_S, HEADER_S, DATA_S, FOOTER_S);
   SIGNAL state, next_state   : STATE_TYPE; 
   
   signal dwordCnt               : natural range 0 to HEADER_SIZE_C;
   signal dwordCntRst            : std_logic;
   signal dwordCntEn             : std_logic;
   
   -- Hard coded words in the data stream for now
   constant LANE_C     : slv( 1 downto 0) := "00";
   constant VC_C       : slv( 1 downto 0) := "11";
   constant QUAD_C     : slv( 1 downto 0) := "00";
   constant OPCODE_C   : slv( 7 downto 0) := x"00";
   constant ZEROWORD_C : slv(31 downto 0) := x"00000000";
   
   
   
begin
   
   -----------------------------------------------
   -- Readout FSM
   -----------------------------------------------
   
   fsm_seq_p: process ( sysClk ) 
   begin
      -- FSM state register
      if rising_edge(sysClk) then
         if sysRst = '1' then
            state <= IDLE_S               after TPD_G;
         else
            state <= next_state           after TPD_G;         
         end if;
      end if;
      
      -- word counter
      if rising_edge(sysClk) then
         if sysRst = '1' or dwordCntRst = '1' then
            dwordCnt <= 0                 after TPD_G;
         elsif dwordCntEn = '1' then
            dwordCnt <= dwordCnt + 1      after TPD_G;         
         end if;
      end if;
      
   end process;
   

   fsm_cmb_p: process ( state, trig, dwordCnt, mAxisSlave, dataIn, acqCount, seqCount) 
      variable mAxisMasterVar : AxiStreamMasterType := AXI_STREAM_MASTER_INIT_C;
   begin
      next_state <= state;
      dwordCntRst <= '1';
      dwordCntEn <= '0';
      mAxisMasterVar := AXI_STREAM_MASTER_INIT_C;
      
      
      case state is
      
         when IDLE_S =>
            if trig = '1' then
               next_state <= HEADER_S;
            end if;
         
         when HEADER_S =>
            dwordCntRst <= '0';
            
            if dwordCnt = 0 then
               mAxisMasterVar.tData(31 downto 0) := x"000000" & "00" & LANE_C & "00" & VC_C;
               ssiSetUserSof(MASTER_AXI_STREAM_CONFIG_G, mAxisMasterVar, '1');
            elsif dwordCnt = 1 then
               mAxisMasterVar.tData(31 downto 0) := x"0" & "00" & QUAD_C & OPCODE_C & std_logic_vector(acqCount(15 downto 0));
            elsif dwordCnt = 2 then
               mAxisMasterVar.tData(31 downto 0) := std_logic_vector(seqCount);
            elsif dwordCnt >= HEADER_SIZE_C then
               next_state <= DATA_S;
               dwordCntRst <= '1';
            end if;
            
            mAxisMasterVar.tValid := '1';
            
            if mAxisSlave.tReady = '1' then
               dwordCntEn <= '1';
            else
               dwordCntEn <= '0';
            end if;
         
         when DATA_S => 
            dwordCntRst <= '0';
            
            if dwordCnt = 0 then
               mAxisMasterVar.tData(31 downto 0) := dataIn(0);
            elsif dwordCnt = 1 then
               mAxisMasterVar.tData(31 downto 0) := dataIn(1);
            elsif dwordCnt = 2 then
               mAxisMasterVar.tData(31 downto 0) := dataIn(2);
            elsif dwordCnt = 3 then
               mAxisMasterVar.tData(31 downto 0) := dataIn(3);
            elsif dwordCnt = 4 then
               mAxisMasterVar.tData(31 downto 0) := dataIn(4);
            elsif dwordCnt = 5 then
               mAxisMasterVar.tData(31 downto 0) := dataIn(5);
            elsif dwordCnt = 6 then
               mAxisMasterVar.tData(31 downto 0) := dataIn(7);
            else
               mAxisMasterVar.tData(31 downto 0) := dataIn(8);
               next_state <= FOOTER_S;
            end if;
            
            mAxisMasterVar.tValid := '1';
            
            if mAxisSlave.tReady = '1' then
               dwordCntEn <= '1';
            else
               dwordCntEn <= '0';
            end if;
         
         when FOOTER_S =>
            ssiSetUserEofe(MASTER_AXI_STREAM_CONFIG_G, mAxisMasterVar, '0');
            mAxisMasterVar.tData(31 downto 0) := ZEROWORD_C;
            mAxisMasterVar.tValid := '1';
            mAxisMasterVar.tLast := '1';
            if mAxisSlave.tReady = '1' then
               next_state <= IDLE_S;
            end if;
         
         when others =>
            next_state <= IDLE_S;
      
      end case;
      
      mAxisMaster <= mAxisMasterVar;
      
   end process;
   
end rtl;
