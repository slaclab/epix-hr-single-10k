-------------------------------------------------------------------------------
-- File       : RegControlEpixHR.vhd
-- Company    : SLAC National Accelerator Laboratory
-------------------------------------------------------------------------------
-- Description: EpixHR register controller
-------------------------------------------------------------------------------
-- This file is part of 'EpixHR Development Firmware'.
-- It is subject to the license terms in the LICENSE.txt file found in the 
-- top-level directory of this distribution and at: 
--    https://confluence.slac.stanford.edu/display/ppareg/LICENSE.html. 
-- No part of 'EpixHR Development Firmware', including this file, 
-- may be copied, modified, propagated, or distributed except according to 
-- the terms contained in the LICENSE.txt file.
-------------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;
use ieee.std_logic_unsigned.all;
use ieee.std_logic_arith.all;

library surf;
use surf.StdRtlPkg.all;
use surf.AxiLitePkg.all;

use work.AppPkg.all;

library unisim;
use unisim.vcomponents.all;

entity RegisterControlDualClock is
   generic (
      TPD_G             : time               := 1 ns;
      EN_DEVICE_DNA_G   : boolean            := true;
      CLK_PERIOD_G      : real               := 10.0e-9;
      BUILD_INFO_G      : BuildInfoType
   );
   port (
      -- Global Signals
      axilClk        : in  sl;
      axilRst        : in  sl;
      -- AXI-Lite Register Interface (axiClk domain)
      axiReadMaster  : in  AxiLiteReadMasterType;
      axiReadSlave   : out AxiLiteReadSlaveType;
      axiWriteMaster : in  AxiLiteWriteMasterType;
      axiWriteSlave  : out AxiLiteWriteSlaveType;
      -- Register Inputs/Outputs (axiClk domain)
      boardConfig     : out AppConfigType;
      -- 1-wire board ID interfaces
      serialIdIo     : inout slv(1 downto 0);
      -- ASICs acquisition signals
      acqStart       : in  sl;
      asicR0         : out sl;
      asicAcq        : out sl;
      asicPPbe       : out sl;
      asicPpmat      : out sl;
      saciReadoutReq : out sl;
      saciReadoutAck : in  sl;
      errInhibit     : out sl;
      -- sys clock signals (ASIC RD clock domain)
      sysRst         : in  sl;
      sysClk         : in  sl;
      --
      asicSR0        : out sl;
      asicClkSyncEn  : out sl;
      asicGlblRst    : out sl;
      asicSync       : out sl
   );
end RegisterControlDualClock;

architecture rtl of RegisterControlDualClock is
  
  
   type AsicAcqType is record
      Acq               : sl;
      AcqPolarity       : sl;
      AcqDelay1         : slv(31 downto 0);
      AcqDelay2         : slv(31 downto 0);
      AcqWidth1         : slv(31 downto 0);
      AcqWidth2         : slv(31 downto 0);
      Start             : sl;
      StartPolarity     : sl;
      StartDelay        : slv(31 downto 0);
      StartWidth        : slv(31 downto 0);
      PPbe              : sl;
      PPbePolarity      : sl;
      PPbeDelay         : slv(31 downto 0);
      PPbeWidth         : slv(31 downto 0);
      Ppmat             : sl;
      PpmatPolarity     : sl;
      PpmatDelay        : slv(31 downto 0);
      PpmatWidth        : slv(31 downto 0);
      saciSync          : sl;
      saciSyncPolarity  : sl;
      saciSyncDelay     : slv(31 downto 0);
      saciSyncWidth     : slv(31 downto 0);
      startReadout      : sl;
      startRoDelay      : slv(15 downto 0);
      
   end record AsicAcqType;
   
   constant ASICACQ_TYPE_INIT_C : AsicAcqType := (
      Acq               => '0',
      AcqPolarity       => '0',
      AcqDelay1         => (others=>'0'),
      AcqDelay2         => (others=>'0'),
      AcqWidth1         => (others=>'0'),
      AcqWidth2         => (others=>'0'),
      Start             => '0',
      StartPolarity     => '0',
      StartDelay        => (others=>'0'),
      StartWidth        => (others=>'0'),
      PPbe              => '0',
      PPbePolarity      => '0',
      PPbeDelay         => (others=>'0'),
      PPbeWidth         => (others=>'0'),
      Ppmat             => '0',
      PpmatPolarity     => '0',
      PpmatDelay        => (others=>'0'),
      PpmatWidth        => (others=>'0'),
      saciSync          => '0',
      saciSyncPolarity  => '0',
      saciSyncDelay     => (others=>'0'),
      saciSyncWidth     => (others=>'0'),
      startReadout      => '0',
      startRoDelay      => X"0001"
   );

   type AsicAcqType2 is record
      SR0               : sl;
      SR0Polarity       : sl;
      SR0Delay          : slv(31 downto 0);
      SR0Width          : slv(31 downto 0);
      ClkSyncEn         : sl;
      ClkSyncEnLatched  : sl;
      GlblRst           : sl;
      GlblRstPolarity   : sl;
      Sync              : sl;
      SyncPolarity      : sl;
      SyncDelay         : slv(31 downto 0);
      SyncWidth         : slv(31 downto 0);
      ePixAdcSHT        : slv(15 downto 0);
      ePixAdcSHCnt      : slv(15 downto 0);
      ePixAdcSHSR0Phase : slv(15 downto 0);
   end record AsicAcqType2;
   
   constant ASICACQ_TYPE2_INIT_C : AsicAcqType2 := (
      SR0               => '0',
      SR0Polarity       => '0',
      SR0Delay          => (others=>'0'),
      SR0Width          => (others=>'0'),
      ClkSyncEn         => '0',
      ClkSyncEnLatched  => '0',
      GlblRst           => '1',
      GlblRstPolarity   => '1',
      Sync              => '0',
      SyncPolarity      => '0',
      SyncDelay         => (others=>'0'),
      SyncWidth         => (others=>'0'),
      ePixAdcSHT        => X"0100",
      ePixAdcSHCnt      => (others=>'0'),
      ePixAdcSHSR0Phase => (others=>'0')
   );
   
   type RegType is record
      usrRst            : sl;
      resetCounters     : sl; 
      saciPrepRdoutCnt  : slv(31 downto 0);
      boardRegOut       : appConfigType;
      asicAcqReg        : AsicAcqType;
      asicAcqReg2       : AsicAcqType2;
      asicAcqTimeCnt    : slv(31 downto 0);
      axiReadSlave      : AxiLiteReadSlaveType;
      axiWriteSlave     : AxiLiteWriteSlaveType;
   end record RegType;
   
   constant REG_INIT_C : RegType := (
      usrRst            => '0',
      resetCounters     => '0',
      saciPrepRdoutCnt  => (others=>'0'),
      boardRegOut       => APP_CONFIG_INIT_C,
      asicAcqReg        => ASICACQ_TYPE_INIT_C,
      asicAcqReg2       => ASICACQ_TYPE2_INIT_C,
      asicAcqTimeCnt    => (others=>'0'),
      axiReadSlave      => AXI_LITE_READ_SLAVE_INIT_C,
      axiWriteSlave     => AXI_LITE_WRITE_SLAVE_INIT_C
      );

   type RegType2 is record
      asicAcqReg2       : AsicAcqType2;
      asicAcqTimeCnt    : slv(31 downto 0);
      errInhibitCnt     : slv(31 downto 0);      
   end record RegType2;
   
   constant REG2_INIT_C : RegType2 := (
      asicAcqReg2       => ASICACQ_TYPE2_INIT_C,
      asicAcqTimeCnt    => (others=>'0'),
      errInhibitCnt     => (others=>'0')
   );

   signal r   : RegType := REG_INIT_C;
   signal rin : RegType;

   signal r_sys    : RegType2 := REG2_INIT_C;
   signal rin_sys  : RegType2;

   signal asicAcqReg2Synced    : AsicAcqType2;
   signal startReadoutSynced   : sl;
   
   signal idValues : Slv64Array(2 downto 0);
   signal idValids : slv(2 downto 0);
   signal dummyIdValues : slv(63 downto 0);
   
   signal adcCardStartUp     : sl;
   signal adcCardStartUpEdge : sl;
   
   signal chipIdRst          : sl;
   
   signal axiReset : sl;
   
   constant BUILD_INFO_C       : BuildInfoRetType    := toBuildInfo(BUILD_INFO_G);
   
   
begin

   axiReset <= sysRst or r.usrRst;

   -------------------------------
   -- Configuration Register
   -------------------------------  
   comb : process (axiReadMaster, axiReset, axiWriteMaster, r, idValids, idValues, acqStart, saciReadoutAck) is
      variable v           : RegType;
      variable regCon      : AxiLiteEndPointType;
      
   begin
      -- Latch the current value
      v := r;
      
      -- Reset data and strobes
      v.resetCounters            := '0';
      
      
      -- Determine the transaction type
      axiSlaveWaitTxn(regCon, axiWriteMaster, axiReadMaster, v.axiWriteSlave, v.axiReadSlave);
      
      -- Map out standard registers
      axiSlaveRegister (regCon, x"0000",  0, v.usrRst );
      axiSlaveRegisterR(regCon, x"0000",  0, BUILD_INFO_C.fwVersion );
      axiSlaveRegisterR(regCon, x"0004",  0, ite(idValids(0) = '1',idValues(0)(31 downto  0), x"00000000")); --Digital card ID low
      axiSlaveRegisterR(regCon, x"0008",  0, ite(idValids(0) = '1',idValues(0)(63 downto 32), x"00000000")); --Digital card ID high
      axiSlaveRegisterR(regCon, x"000C",  0, ite(idValids(1) = '1',idValues(1)(31 downto  0), x"00000000")); --Analog card ID low
      axiSlaveRegisterR(regCon, x"0010",  0, ite(idValids(1) = '1',idValues(1)(63 downto 32), x"00000000")); --Analog card ID high
      axiSlaveRegisterR(regCon, x"0014",  0, ite(idValids(2) = '1',idValues(2)(31 downto  0), x"00000000")); --Carrier card ID low
      axiSlaveRegisterR(regCon, x"0018",  0, ite(idValids(2) = '1',idValues(2)(63 downto 32), x"00000000")); --Carrier card ID high
      -- Register used in the sys clock domain
      axiSlaveRegister(regCon,  x"0100",  0, v.asicAcqReg2.GlblRstPolarity);
      axiSlaveRegister(regCon,  x"0100",  1, v.asicAcqReg2.ClkSyncEn);
      axiSlaveRegister(regCon,  x"0104",  0, v.asicAcqReg2.SyncPolarity);
      axiSlaveRegister(regCon,  x"0108",  0, v.asicAcqReg2.SyncDelay);
      axiSlaveRegister(regCon,  x"010C",  0, v.asicAcqReg2.SyncWidth);
      axiSlaveRegister(regCon,  x"0110",  0, v.asicAcqReg2.SR0Polarity);
      axiSlaveRegister(regCon,  x"0114",  0, v.asicAcqReg2.SR0Delay);
      axiSlaveRegister(regCon,  x"0118",  0, v.asicAcqReg2.SR0Width);
      axiSlaveRegister(regCon,  x"011C",  0, v.asicAcqReg2.ePixAdcSHT);
      axiSlaveRegister(regCon,  x"0120",  0, v.asicAcqReg2.ePixAdcSHSR0Phase);     
      -- registers used in the app clock domain
      axiSlaveRegister(regCon,  x"0200",  0, v.asicAcqReg.AcqPolarity);
      axiSlaveRegister(regCon,  x"0204",  0, v.asicAcqReg.AcqDelay1);
      axiSlaveRegister(regCon,  x"0208",  0, v.asicAcqReg.AcqWidth1);
      axiSlaveRegister(regCon,  x"020C",  0, v.asicAcqReg.AcqDelay2);
      axiSlaveRegister(regCon,  x"0210",  0, v.asicAcqReg.AcqWidth2);
      axiSlaveRegister(regCon,  x"0214",  0, v.asicAcqReg.StartPolarity);
      axiSlaveRegister(regCon,  x"0218",  0, v.asicAcqReg.StartDelay);
      axiSlaveRegister(regCon,  x"021C",  0, v.asicAcqReg.StartWidth);
      axiSlaveRegister(regCon,  x"0220",  0, v.asicAcqReg.PPbePolarity);
      axiSlaveRegister(regCon,  x"0224",  0, v.asicAcqReg.PPbeDelay);
      axiSlaveRegister(regCon,  x"0228",  0, v.asicAcqReg.PPbeWidth);
      axiSlaveRegister(regCon,  x"022C",  0, v.asicAcqReg.PpmatPolarity);
      axiSlaveRegister(regCon,  x"0230",  0, v.asicAcqReg.PpmatDelay);
      axiSlaveRegister(regCon,  x"0234",  0, v.asicAcqReg.PpmatWidth);
      axiSlaveRegister(regCon,  x"0238",  0, v.asicAcqReg.saciSyncPolarity);
      axiSlaveRegister(regCon,  x"023C",  0, v.asicAcqReg.saciSyncDelay);
      axiSlaveRegister(regCon,  x"0240",  0, v.asicAcqReg.saciSyncWidth);
      axiSlaveRegisterR(regCon, x"0244",  0, r.boardRegOut.acqCnt);
      axiSlaveRegisterR(regCon, x"0248",  0, r.saciPrepRdoutCnt);
      axiSlaveRegister(regCon,  x"024C",  0, v.resetCounters);
      axiSlaveRegister(regCon,  x"0250",  0, v.boardRegOut.powerEnable);
      axiSlaveRegister(regCon,  x"0254",  0, v.boardRegOut.asicMask);
      axiSlaveRegister(regCon,  x"0258",  0, v.boardRegOut.epixhrDbgSel1);
      axiSlaveRegister(regCon,  x"025C",  0, v.boardRegOut.epixhrDbgSel2);
      axiSlaveRegister(regCon,  x"0260",  0, v.boardRegOut.epixhrDbgSel3);
      axiSlaveRegister(regCon,  x"0264",  0, v.boardRegOut.requestStartupCal);
      axiSlaveRegister(regCon,  x"0264",  1, v.boardRegOut.startupAck);          -- set by Microblaze
      axiSlaveRegister(regCon,  x"0264",  2, v.boardRegOut.startupFail);         -- set by Microblaze

      
      axiSlaveDefault(regCon, v.axiWriteSlave, v.axiReadSlave, AXI_RESP_OK_C);
   
 
      -- programmable ASIC acquisition waveform
      if acqStart = '1' then
         v.asicAcqReg.startReadout  := '0';
         v.boardRegOut.acqCnt       := r.boardRegOut.acqCnt + 1;
         v.asicAcqTimeCnt           := (others=>'0');
         v.asicAcqReg.Acq           := r.asicAcqReg.AcqPolarity;
         v.asicAcqReg.Start         := r.asicAcqReg.StartPolarity;
         v.asicAcqReg.PPbe          := r.asicAcqReg.PPbePolarity;
         v.asicAcqReg.Ppmat         := r.asicAcqReg.PpmatPolarity;
         v.asicAcqReg.saciSync      := r.asicAcqReg.saciSyncPolarity;
      else
         if r.asicAcqTimeCnt /= x"FFFFFFFF" then
            v.asicAcqTimeCnt := r.asicAcqTimeCnt + 1;
         end if;
         
       
         -- double pulse. zero value corresponds to infinite delay/width
         if r.asicAcqReg.AcqDelay1 /= 0 and r.asicAcqReg.AcqDelay1 <= r.asicAcqTimeCnt then
            v.asicAcqReg.Acq := not r.asicAcqReg.AcqPolarity;
            if r.asicAcqReg.AcqWidth1 /= 0 and (r.asicAcqReg.AcqWidth1 + r.asicAcqReg.AcqDelay1) <= r.asicAcqTimeCnt then
               v.asicAcqReg.Acq := r.asicAcqReg.AcqPolarity;
               if r.asicAcqReg.AcqDelay2 /= 0 and (r.asicAcqReg.AcqDelay2 + r.asicAcqReg.AcqWidth1 + r.asicAcqReg.AcqDelay1) <= r.asicAcqTimeCnt then
                  v.asicAcqReg.Acq := not r.asicAcqReg.AcqPolarity;
                  if r.asicAcqReg.AcqWidth2 /= 0 and (r.asicAcqReg.AcqWidth2 + r.asicAcqReg.AcqDelay2 + r.asicAcqReg.AcqWidth1 + r.asicAcqReg.AcqDelay1) <= r.asicAcqTimeCnt then
                     v.asicAcqReg.Acq := r.asicAcqReg.AcqPolarity;
                  end if;
               end if;
            end if;
         end if;


         if (r.asicAcqReg.AcqWidth2 + r.asicAcqReg.AcqDelay2 + r.asicAcqReg.AcqWidth1 + r.asicAcqReg.AcqDelay1 + r.asicAcqReg.startRoDelay) <= r.asicAcqTimeCnt then
           v.asicAcqReg.startReadout := '1';
         end if;
         
         -- single pulse. zero value corresponds to infinite delay/width
         if r.asicAcqReg.StartDelay /= 0 and r.asicAcqReg.StartDelay <= r.asicAcqTimeCnt then
            v.asicAcqReg.Start := not r.asicAcqReg.StartPolarity;
            if r.asicAcqReg.StartWidth /= 0 and (r.asicAcqReg.StartWidth + r.asicAcqReg.StartDelay) <= r.asicAcqTimeCnt then
               v.asicAcqReg.Start := r.asicAcqReg.StartPolarity;
            end if;
         end if;
         
         -- single pulse. zero value corresponds to infinite delay/width
         if r.asicAcqReg.PPbeDelay /= 0 and r.asicAcqReg.PPbeDelay <= r.asicAcqTimeCnt then
            v.asicAcqReg.PPbe := not r.asicAcqReg.PPbePolarity;
            if r.asicAcqReg.PPbeWidth /= 0 and (r.asicAcqReg.PPbeWidth + r.asicAcqReg.PPbeDelay) <= r.asicAcqTimeCnt then
               v.asicAcqReg.PPbe := r.asicAcqReg.PPbePolarity;
            end if;
         end if;
         
         -- single pulse. zero value corresponds to infinite delay/width
         if r.asicAcqReg.PpmatDelay /= 0 and r.asicAcqReg.PpmatDelay <= r.asicAcqTimeCnt then
            v.asicAcqReg.Ppmat := not r.asicAcqReg.PpmatPolarity;
            if r.asicAcqReg.PpmatWidth /= 0 and (r.asicAcqReg.PpmatWidth + r.asicAcqReg.PpmatDelay) <= r.asicAcqTimeCnt then
               v.asicAcqReg.Ppmat := r.asicAcqReg.PpmatPolarity;
            end if;
         end if;
         
         
         -- single pulse. zero value corresponds to infinite delay/width
         if r.asicAcqReg.saciSyncDelay /= 0 and r.asicAcqReg.saciSyncDelay <= r.asicAcqTimeCnt then
            v.asicAcqReg.saciSync := not r.asicAcqReg.saciSyncPolarity;
            if r.asicAcqReg.saciSyncWidth /= 0 and (r.asicAcqReg.saciSyncWidth + r.asicAcqReg.saciSyncDelay) <= r.asicAcqTimeCnt then
               v.asicAcqReg.saciSync := r.asicAcqReg.saciSyncPolarity;
            end if;
         end if;
         
      end if;
      
      -- SACI preperare for readout ack counter
      if saciReadoutAck = '1' then
         v.saciPrepRdoutCnt := r.saciPrepRdoutCnt + 1;
      end if;
      
      -- reset counters
      if r.resetCounters = '1' then
         v.boardRegOut.acqCnt := (others=>'0');
         v.saciPrepRdoutCnt   := (others=>'0');
      end if;
  
    
      -- Synchronous Reset
      if axiReset = '1' then
         v := REG_INIT_C;
      end if;

      -- Register the variable for next clock cycle
      rin <= v;

      --------------------------
      -- Outputs 
      --------------------------
      axiReadSlave   <= r.axiReadSlave;
      axiWriteSlave  <= r.axiWriteSlave;
      boardConfig    <= r.boardRegOut;
      saciReadoutReq <= r.asicAcqReg.saciSync;
      asicPPbe       <= r.asicAcqReg.PPbe;
      asicPpmat      <= r.asicAcqReg.Ppmat;
      asicR0         <= r.asicAcqReg.Start;
      asicAcq        <= r.asicAcqReg.Acq;

      
   end process comb;

   seq : process (axilClk) is
   begin
      if rising_edge(axilClk) then
         r <= rin after TPD_G;
      end if;
   end process seq;

   -----------------------------------------------
   -- Crossing clock domains
   -----------------------------------------------
   -----------------------------------------------
   SynchronizerSR0Polarity : entity surf.Synchronizer
       generic map(
         TPD_G          => TPD_G,
         STAGES_G       => 2)
       port map(
         clk     => sysClk,
         rst     => sysRst,
         dataIn  => r.asicAcqReg2.SR0Polarity,
         dataOut => asicAcqReg2Synced.SR0Polarity);
   
   SynchronizerCounterSR0D : entity surf.SynchronizerVector 
       generic map(
         TPD_G          => TPD_G,
         STAGES_G       => 2,
         WIDTH_G        => 32)
       port map(
         clk     => sysClk,
         rst     => sysRst,
         dataIn  => r.asicAcqReg2.SR0Delay,
         dataOut => asicAcqReg2Synced.SR0Delay);

   SynchronizerCounterSR0W : entity surf.SynchronizerVector 
       generic map(
         TPD_G          => TPD_G,
         STAGES_G       => 2,
         WIDTH_G        => 32)
       port map(
         clk     => sysClk,
         rst     => sysRst,
         dataIn  => r.asicAcqReg2.SR0Width,
         dataOut => asicAcqReg2Synced.SR0Width);

    SynchronizerSyncPolarity : entity surf.Synchronizer
       generic map(
         TPD_G          => TPD_G,
         STAGES_G       => 2)
       port map(
         clk     => sysClk,
         rst     => sysRst,
         dataIn  => r.asicAcqReg2.SyncPolarity,
         dataOut => asicAcqReg2Synced.SyncPolarity);

      SynchronizerCounterSyncD : entity surf.SynchronizerVector 
       generic map(
         TPD_G          => TPD_G,
         STAGES_G       => 2,
         WIDTH_G        => 32)
       port map(
         clk     => sysClk,
         rst     => sysRst,
         dataIn  => r.asicAcqReg2.SyncDelay,
         dataOut => asicAcqReg2Synced.SyncDelay);

   SynchronizerCounterSyncW : entity surf.SynchronizerVector 
       generic map(
         TPD_G          => TPD_G,
         STAGES_G       => 2,
         WIDTH_G        => 32)
       port map(
         clk     => sysClk,
         rst     => sysRst,
         dataIn  => r.asicAcqReg2.SyncWidth,
         dataOut => asicAcqReg2Synced.SyncWidth);


   SynchronizerCounterePixAdcSHT : entity surf.SynchronizerVector 
       generic map(
         TPD_G          => TPD_G,
         STAGES_G       => 2,
         WIDTH_G        => 16)
       port map(
         clk     => sysClk,
         rst     => sysRst,
         dataIn  => r.asicAcqReg2.ePixAdcSHT,
         dataOut => asicAcqReg2Synced.ePixAdcSHT);


   SynchronizerCounterePixAdcSHSR0Phase : entity surf.SynchronizerVector 
       generic map(
         TPD_G          => TPD_G,
         STAGES_G       => 2,
         WIDTH_G        => 16)
       port map(
         clk     => sysClk,
         rst     => sysRst,
         dataIn  => r.asicAcqReg2.ePixAdcSHSR0Phase,
         dataOut => asicAcqReg2Synced.ePixAdcSHSR0Phase);

   Synchronizer_1 : entity surf.SynchronizerOneShot
       generic map (
         TPD_G    => TPD_G,
         PULSE_WIDTH_G => 1)
       port map (
         clk     => sysClk,
         rst     => sysRst,
         dataIn  => r.asicAcqReg.startReadout,
         dataOut => startReadoutSynced
         );
   
   SynchronizerGlblRst : entity surf.Synchronizer
       generic map(
         TPD_G          => TPD_G,
         STAGES_G       => 2)
       port map(
         clk     => sysClk,
         rst     => sysRst,
         dataIn  => r.asicAcqReg2.GlblRstPolarity,
         dataOut => asicAcqReg2Synced.GlblRstPolarity);
   
   SynchronizerSampClkEn : entity surf.Synchronizer
       generic map(
         TPD_G          => TPD_G,
         STAGES_G       => 2)
       port map(
         clk     => sysClk,
         rst     => sysRst,
         dataIn  => r.asicAcqReg2.ClkSyncEn,
         dataOut => asicAcqReg2Synced.ClkSyncEn);

   -----------------------------------------------
   -- System clock combinatorial logic
   -----------------------------------------------  
   comb2 : process (sysRst,r_sys, asicAcqReg2Synced, startReadoutSynced) is
      variable v           : RegType2;
      
   begin
      -- Latch the current value
      v := r_sys;
      v.asicAcqReg2.SR0Polarity := asicAcqReg2Synced.SR0Polarity;
      v.asicAcqReg2.SR0Delay := asicAcqReg2Synced.SR0Delay;
      v.asicAcqReg2.SR0Width := asicAcqReg2Synced.SR0Width;
      --
      v.asicAcqReg2.SyncPolarity := asicAcqReg2Synced.SyncPolarity;
      v.asicAcqReg2.SyncDelay := asicAcqReg2Synced.SyncDelay;
      v.asicAcqReg2.SyncWidth := asicAcqReg2Synced.SyncWidth;
      --
      v.asicAcqReg2.ePixAdcSHT := asicAcqReg2Synced.ePixAdcSHT;
      v.asicAcqReg2.ePixAdcSHSR0Phase := asicAcqReg2Synced.ePixAdcSHSR0Phase;
      
            
      -- ePixHrADC clock counter to mimic the SHClk and SDrst periods in the asic
      -- sync SR0 start to this period to avoid the background bounce per bank
      -- at 320MHz this should be 1.00us
      -- at 250MHz this should be 1.28us
      -- at 125 this should be 2.56us
      if r_sys.asicAcqReg2.ePixAdcSHCnt >= r_sys.asicAcqReg2.ePixAdcSHT - 1 then
         v.asicAcqReg2.ePixAdcSHCnt := (others => '0');
      else
         v.asicAcqReg2.ePixAdcSHCnt := r_sys.asicAcqReg2.ePixAdcSHCnt + 1;
      end if;
  
      -- programmable ASIC acquisition waveform
      if startReadoutSynced = '1' then
         v.asicAcqReg2.SR0           := r_sys.asicAcqReg2.SR0Polarity;
         v.asicAcqReg2.GlblRst       := r_sys.asicAcqReg2.GlblRstPolarity;
         v.asicAcqReg2.Sync          := r_sys.asicAcqReg2.SyncPolarity;
         v.asicAcqTimeCnt           := (others=>'0');
      else
         if r_sys.asicAcqTimeCnt /= x"FFFFFFFF" then
            v.asicAcqTimeCnt := r_sys.asicAcqTimeCnt + 1;
         end if;

         
         -- single pulse. zero value corresponds to infinite delay/width
         if r_sys.asicAcqReg2.SR0Delay /= 0 and r_sys.asicAcqReg2.SR0Delay <= r_sys.asicAcqTimeCnt and r_sys.asicAcqReg2.ePixAdcSHCnt = r_sys.asicAcqReg2.ePixAdcSHSR0Phase then
            v.asicAcqReg2.SR0 := not r_sys.asicAcqReg2.SR0Polarity;
            if r_sys.asicAcqReg2.SR0Width /= 0 and (r_sys.asicAcqReg2.SR0Width + r_sys.asicAcqReg2.SR0Delay) <= r_sys.asicAcqTimeCnt and r_sys.asicAcqReg2.ePixAdcSHCnt = r_sys.asicAcqReg2.ePixAdcSHSR0Phase then
               v.asicAcqReg2.SR0 := r_sys.asicAcqReg2.SR0Polarity;
            end if;
         end if;
        
         -- global reset changes in sync with SHCnt per ASIC designers recomendation
         if r_sys.asicAcqReg2.ePixAdcSHCnt = 0 then
           v.asicAcqReg2.GlblRst := asicAcqReg2Synced.GlblRstPolarity;
           v.asicAcqReg2.ClkSyncEnLatched := asicAcqReg2Synced.ClkSyncEn;
         end if;
         
        
         -- single pulse. zero value corresponds to infinite delay/width
         if r_sys.asicAcqReg2.SyncDelay /= 0 and r_sys.asicAcqReg2.SyncDelay <= r_sys.asicAcqTimeCnt then
            v.asicAcqReg2.Sync := not r_sys.asicAcqReg2.SyncPolarity;
            if r_sys.asicAcqReg2.SyncWidth /= 0 and (r_sys.asicAcqReg2.SyncWidth + r_sys.asicAcqReg2.SyncDelay) <= r_sys.asicAcqTimeCnt then
               v.asicAcqReg2.Sync := r_sys.asicAcqReg2.SyncPolarity;
            end if;
         end if;
         
         
      end if;
      
     
      -- epixhr bug workaround
      -- for a number of clock cycles
      -- data link is dropped after R0 
      if r_sys.asicAcqReg2.SR0 = not r_sys.asicAcqReg2.SR0Polarity then
         v.errInhibitCnt := (others=>'0');
         errInhibit <= '1';
      elsif r_sys.errInhibitCnt <= 5000 then    -- inhibit for 50 us
         v.errInhibitCnt := r_sys.errInhibitCnt + 1;
         errInhibit <= '1';
      else
         errInhibit <= '0';
      end if;
      
      -- Synchronous Reset
      if sysRst = '1' then
         v := REG2_INIT_C;
      end if;

      -- Register the variable for next clock cycle
      rin_sys <= v;

      --------------------------
      -- Outputs 
      --------------------------
      asicSR0        <= r_sys.asicAcqReg2.SR0;
      asicClkSyncEn  <= r_sys.asicAcqReg2.ClkSyncEnLatched;
      asicGlblRst    <= r_sys.asicAcqReg2.GlblRst;
      asicSync       <= r_sys.asicAcqReg2.Sync;
     
   end process comb2;

   -----------------------------------------------
   -- System clock sequencial logic
   -----------------------------------------------

   seq2 : process (sysClk) is
   begin
      if rising_edge(sysClk) then
         r_sys <= rin_sys after TPD_G;
      end if;
   end process seq2;
   
   -----------------------------------------------
   -- Serial IDs: FPGA Device DNA + DS2411's
   -----------------------------------------------  
   GEN_DEVICE_DNA : if (EN_DEVICE_DNA_G = true) generate
      G_DEVICE_DNA : entity surf.DeviceDna
         generic map (
            TPD_G        => TPD_G,
            XIL_DEVICE_G => "ULTRASCALE")
         port map (
            clk      => axilClk,
            rst      => axiReset,
            dnaValue(127 downto 64) => dummyIdValues,
            dnaValue( 63 downto  0) => idValues(0),
            dnaValid => idValids(0)
         );
      G_DS2411 : for i in 0 to 1 generate
        U_DS2411_N : entity surf.DS2411Core
          generic map (
            TPD_G        => TPD_G,
            CLK_PERIOD_G => CLK_PERIOD_G
            )
          port map (
            clk       => axilClk,
            rst       => chipIdRst,
            fdSerSdio => serialIdIo(i),
            fdValue   => idValues(i+1),
            fdValid   => idValids(i+1)
          );
      end generate;
   end generate GEN_DEVICE_DNA;
   
   BYP_DEVICE_DNA : if (EN_DEVICE_DNA_G = false) generate
      idValids(0) <= '1';
      idValues(0) <= (others=>'0');
   end generate BYP_DEVICE_DNA;   
      
   
   
   chipIdRst <= axiReset or adcCardStartUpEdge;

   -- Special reset to the DS2411 to re-read in the event of a start up request event
   -- Start up (picoblaze) is disabling the ASIC digital monitors to ensure proper carrier ID readout
   adcCardStartUp <= r.boardRegOut.startupAck or r.boardRegOut.startupFail;
   U_adcCardStartUpRisingEdge : entity surf.SynchronizerEdge
   generic map (
      TPD_G       => TPD_G)
   port map (
      clk         => axilClk,
      dataIn      => adcCardStartUp,
      risingEdge  => adcCardStartUpEdge
   );
   
end rtl;
