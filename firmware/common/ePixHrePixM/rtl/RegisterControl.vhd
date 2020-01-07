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

entity RegisterControl is
   generic (
      TPD_G             : time               := 1 ns;
      EN_DEVICE_DNA_G   : boolean            := true;
      CLK_PERIOD_G      : real            := 10.0e-9;
      BUILD_INFO_G      : BuildInfoType
   );
   port (
      -- Global Signals
      axiClk         : in  sl;
      axiRst         : out sl;
      sysRst         : in  sl;
      -- AXI-Lite Register Interface (axiClk domain)
      axiReadMaster  : in  AxiLiteReadMasterType;
      axiReadSlave   : out AxiLiteReadSlaveType;
      axiWriteMaster : in  AxiLiteWriteMasterType;
      axiWriteSlave  : out AxiLiteWriteSlaveType;
      -- Register Inputs/Outputs (axiClk domain)
      boardConfig     : out AppConfigType;
      -- 1-wire board ID interfaces
      serialIdIo     : inout slv(1 downto 0);
      -- fast ADC clock
      adcClk         : out sl;
      -- ASICs acquisition signals
      acqStart       : in  sl;
      saciReadoutReq : out sl;
      saciReadoutAck : in  sl;
      asicPPbe       : out sl;
      asicPpmat      : out sl;
      asicTpulse     : out sl;
      asicStart      : out sl;
      asicSR0        : out sl;
      asicGlblRst    : out sl;
      asicSync       : out sl;
      asicAcq        : out sl;
      asicVid        : out sl;
      asicSsrRst     : out sl;
      asicSsrSerClrb : out sl;
      asicSsrStoClrb : out sl;
      asicSsrData    : out sl;
      asicSsrClk     : out sl;
      errInhibit     : out sl
   );
end RegisterControl;

architecture rtl of RegisterControl is

   constant SSR_PARALLEL_OUT : integer := 40;
   
   type AsicAcqType is record
      SR0               : sl;
      SR0Polarity       : sl;
      SR0Delay          : slv(31 downto 0);
      SR0Width          : slv(31 downto 0);
      GlblRst           : sl;
      GlblRstPolarity   : sl;
      GlblRstDelay      : slv(31 downto 0);
      GlblRstWidth      : slv(31 downto 0);
      Acq               : sl;
      AcqPolarity       : sl;
      AcqDelay1         : slv(31 downto 0);
      AcqDelay2         : slv(31 downto 0);
      AcqWidth1         : slv(31 downto 0);
      AcqWidth2         : slv(31 downto 0);
      Vid               : sl;
      Tpulse            : sl;
      TpulsePolarity    : sl;
      TpulseDelay       : slv(31 downto 0);
      TpulseWidth       : slv(31 downto 0);
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
      Sync              : sl;
      SyncPolarity      : sl;
      SyncDelay         : slv(31 downto 0);
      SyncWidth         : slv(31 downto 0);
      saciSync          : sl;
      saciSyncPolarity  : sl;
      saciSyncDelay     : slv(31 downto 0);
      saciSyncWidth     : slv(31 downto 0);
      ssrRst            : sl;
      ssrRstPolarity    : sl;
      ssrRstDelay       : slv(31 downto 0);
      ssrRstWidth       : slv(31 downto 0);
      ssrSerialClrb     : sl;
      ssrStorageClrb    : sl;
      ssrClk            : sl;
      ssrClkEn          : sl;
      ssrCnt            : slv(31 downto 0);
      ssrClkHalfT       : slv(31 downto 0);
      ssrClkDelay       : slv(31 downto 0);
      ssrClkNumPeriods  : slv(15 downto 0);
      ssrClkCounter     : integer;
      ssrDatab          : sl;
      ssrData           : slv(SSR_PARALLEL_OUT-1 downto 0);
      ssrDataSel        : integer;
      
   end record AsicAcqType;
   
   constant ASICACQ_TYPE_INIT_C : AsicAcqType := (
      SR0               => '0',
      SR0Polarity       => '0',
      SR0Delay          => (others=>'0'),
      SR0Width          => (others=>'0'),
      GlblRst           => '1',
      GlblRstPolarity   => '1',
      GlblRstDelay      => (others=>'0'),
      GlblRstWidth      => (others=>'0'),
      Acq               => '0',
      AcqPolarity       => '0',
      AcqDelay1         => (others=>'0'),
      AcqDelay2         => (others=>'0'),
      AcqWidth1         => (others=>'0'),
      AcqWidth2         => (others=>'0'),
      Vid               => '0',
      Tpulse            => '0',
      TpulsePolarity    => '0',
      TpulseDelay       => (others=>'0'),
      TpulseWidth       => (others=>'0'),
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
      Sync              => '0',
      SyncPolarity      => '0',
      SyncDelay         => (others=>'0'),
      SyncWidth         => (others=>'0'),
      saciSync          => '0',
      saciSyncPolarity  => '0',
      saciSyncDelay     => (others=>'0'),
      saciSyncWidth     => (others=>'0'),
      ssrRst            => '0',
      ssrRstPolarity    => '0',
      ssrRstDelay       => X"0000_0010",
      ssrRstWidth       => X"0000_1410",
      ssrSerialClrb     => '1',
      ssrStorageClrb    => '1',
      ssrClk            => '0',
      ssrClkEn          => '0',
      ssrCnt            => (others=>'0'),
      ssrClkHalfT       => X"0000_0040",
      ssrClkDelay       => X"0000_0002",
      ssrClkNumPeriods  => X"0028",
      ssrClkCounter     => 0,
      ssrDatab          => '1',
      ssrData           => x"FFFF_FFFF_FE",
      ssrDataSel        => 0
   );
   
   type RegType is record
      usrRst            : sl;
      resetCounters     : sl;
      adcClk            : sl;
      adcCnt            : slv(31 downto 0);
      adcClkHalfT       : slv(31 downto 0);
      
      saciPrepRdoutCnt  : slv(31 downto 0);
      boardRegOut       : appConfigType;
      asicAcqReg        : AsicAcqType;
      asicAcqTimeCnt    : slv(31 downto 0);
      errInhibitCnt     : slv(31 downto 0);
      axiReadSlave      : AxiLiteReadSlaveType;
      axiWriteSlave     : AxiLiteWriteSlaveType;
   end record RegType;
   
   constant REG_INIT_C : RegType := (
      usrRst            => '0',
      resetCounters     => '0',
      adcClk            => '0',
      adcCnt            => (others=>'0'),
      adcClkHalfT       => x"00000001",
      saciPrepRdoutCnt  => (others=>'0'),
      boardRegOut       => APP_CONFIG_INIT_C,
      asicAcqReg        => ASICACQ_TYPE_INIT_C,
      asicAcqTimeCnt    => (others=>'0'),
      errInhibitCnt     => (others=>'0'),
      axiReadSlave      => AXI_LITE_READ_SLAVE_INIT_C,
      axiWriteSlave     => AXI_LITE_WRITE_SLAVE_INIT_C
   );

   signal r   : RegType := REG_INIT_C;
   signal rin : RegType;
   
   signal idValues : Slv64Array(2 downto 0);
   signal idValids : slv(2 downto 0);
   
   signal adcCardStartUp     : sl;
   signal adcCardStartUpEdge : sl;
   
   signal chipIdRst          : sl;
   
   signal axiReset : sl;
   
   constant BUILD_INFO_C       : BuildInfoRetType    := toBuildInfo(BUILD_INFO_G);
   
   
begin

   axiReset <= sysRst or r.usrRst;
   axiRst   <= axiReset;

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
      v.axiReadSlave.rdata       := (others => '0');
      v.resetCounters            := '0';
      
      
      -- Determine the transaction type
      axiSlaveWaitTxn(regCon, axiWriteMaster, axiReadMaster, v.axiWriteSlave, v.axiReadSlave);
      
      -- Map out standard registers
      axiSlaveRegister (regCon, x"000000",  0, v.usrRst );
      axiSlaveRegisterR(regCon, x"000000",  0, BUILD_INFO_C.fwVersion );
      axiSlaveRegisterR(regCon, x"000004",  0, ite(idValids(0) = '1',idValues(0)(31 downto  0), x"00000000")); --Digital card ID low
      axiSlaveRegisterR(regCon, x"000008",  0, ite(idValids(0) = '1',idValues(0)(63 downto 32), x"00000000")); --Digital card ID high
      axiSlaveRegisterR(regCon, x"00000C",  0, ite(idValids(1) = '1',idValues(1)(31 downto  0), x"00000000")); --Analog card ID low
      axiSlaveRegisterR(regCon, x"000010",  0, ite(idValids(1) = '1',idValues(1)(63 downto 32), x"00000000")); --Analog card ID high
      axiSlaveRegisterR(regCon, x"000014",  0, ite(idValids(2) = '1',idValues(2)(31 downto  0), x"00000000")); --Carrier card ID low
      axiSlaveRegisterR(regCon, x"000018",  0, ite(idValids(2) = '1',idValues(2)(63 downto 32), x"00000000")); --Carrier card ID high
      
      axiSlaveRegister(regCon,  x"00010C",  0, v.asicAcqReg.GlblRstPolarity);
      axiSlaveRegister(regCon,  x"000110",  0, v.asicAcqReg.GlblRstDelay);
      axiSlaveRegister(regCon,  x"000114",  0, v.asicAcqReg.GlblRstWidth);
      axiSlaveRegister(regCon,  x"000118",  0, v.asicAcqReg.AcqPolarity);
      axiSlaveRegister(regCon,  x"00011C",  0, v.asicAcqReg.AcqDelay1);
      axiSlaveRegister(regCon,  x"000120",  0, v.asicAcqReg.AcqWidth1);
      axiSlaveRegister(regCon,  x"000124",  0, v.asicAcqReg.AcqDelay2);
      axiSlaveRegister(regCon,  x"000128",  0, v.asicAcqReg.AcqWidth2);
      axiSlaveRegister(regCon,  x"00012C",  0, v.asicAcqReg.TpulsePolarity);
      axiSlaveRegister(regCon,  x"000130",  0, v.asicAcqReg.TpulseDelay);
      axiSlaveRegister(regCon,  x"000134",  0, v.asicAcqReg.TpulseWidth);
      axiSlaveRegister(regCon,  x"000138",  0, v.asicAcqReg.StartPolarity);
      axiSlaveRegister(regCon,  x"00013C",  0, v.asicAcqReg.StartDelay);
      axiSlaveRegister(regCon,  x"000140",  0, v.asicAcqReg.StartWidth);
      axiSlaveRegister(regCon,  x"000144",  0, v.asicAcqReg.PPbePolarity);
      axiSlaveRegister(regCon,  x"000148",  0, v.asicAcqReg.PPbeDelay);
      axiSlaveRegister(regCon,  x"00014C",  0, v.asicAcqReg.PPbeWidth);
      axiSlaveRegister(regCon,  x"000150",  0, v.asicAcqReg.PpmatPolarity);
      axiSlaveRegister(regCon,  x"000154",  0, v.asicAcqReg.PpmatDelay);
      axiSlaveRegister(regCon,  x"000158",  0, v.asicAcqReg.PpmatWidth);
      axiSlaveRegister(regCon,  x"00015C",  0, v.asicAcqReg.SyncPolarity);
      axiSlaveRegister(regCon,  x"000160",  0, v.asicAcqReg.SyncDelay);
      axiSlaveRegister(regCon,  x"000164",  0, v.asicAcqReg.SyncWidth);
      axiSlaveRegister(regCon,  x"000168",  0, v.asicAcqReg.saciSyncPolarity);
      axiSlaveRegister(regCon,  x"00016C",  0, v.asicAcqReg.saciSyncDelay);
      axiSlaveRegister(regCon,  x"000170",  0, v.asicAcqReg.saciSyncWidth);
      axiSlaveRegister(regCon,  x"000174",  0, v.asicAcqReg.SR0Polarity);
      axiSlaveRegister(regCon,  x"000178",  0, v.asicAcqReg.SR0Delay);
      axiSlaveRegister(regCon,  x"00017C",  0, v.asicAcqReg.SR0Width);
      axiSlaveRegister(regCon,  x"000180",  0, v.asicAcqReg.Vid);
      axiSlaveRegister(regCon,  x"000184",  0, v.asicAcqReg.ssrRstPolarity);
      axiSlaveRegister(regCon,  x"000188",  0, v.asicAcqReg.ssrRstDelay);
      axiSlaveRegister(regCon,  x"00018C",  0, v.asicAcqReg.ssrRstWidth);
      axiSlaveRegister(regCon,  x"000190",  0, v.asicAcqReg.ssrSerialClrb);
      axiSlaveRegister(regCon,  x"000190",  1, v.asicAcqReg.ssrStorageClrb);
      axiSlaveRegister(regCon,  x"000194",  0, v.asicAcqReg.ssrClkHalfT);
      axiSlaveRegister(regCon,  x"000198",  0, v.asicAcqReg.ssrClkDelay);
      axiSlaveRegister(regCon,  x"00019C",  0, v.asicAcqReg.ssrClkNumPeriods);
      axiSlaveRegister(regCon,  x"0001A0",  0, v.asicAcqReg.ssrData);
     
      axiSlaveRegisterR(regCon, x"000200",  0, r.boardRegOut.acqCnt);
      axiSlaveRegisterR(regCon, x"000204",  0, r.saciPrepRdoutCnt);
      axiSlaveRegister(regCon,  x"000208",  0, v.resetCounters);
      axiSlaveRegister(regCon,  x"00020C",  0, v.boardRegOut.powerEnable);
      axiSlaveRegister(regCon,  x"000210",  0, v.boardRegOut.asicMask);
      axiSlaveRegister(regCon,  x"000228",  0, v.boardRegOut.epixhrDbgSel1);
      axiSlaveRegister(regCon,  x"00022C",  0, v.boardRegOut.epixhrDbgSel2);
      
      axiSlaveRegister(regCon,  x"000300",  0, v.adcClkHalfT);
      axiSlaveRegister(regCon,  x"000304",  0, v.boardRegOut.requestStartupCal);
      axiSlaveRegister(regCon,  x"000304",  1, v.boardRegOut.startupAck);          -- set by Microblaze
      axiSlaveRegister(regCon,  x"000304",  2, v.boardRegOut.startupFail);         -- set by Microblaze

      
      -- Special reset for write to address 00
      --if regCon.axiStatus.writeEnable = '1' and axiWriteMaster.awaddr = 0 then
      --   v.usrRst := '1';
      --end if;
      
      axiSlaveDefault(regCon, v.axiWriteSlave, v.axiReadSlave, AXI_RESP_OK_C);
      
      -- ADC clock counter
      if r.adcCnt >= r.adcClkHalfT - 1 then
         v.adcClk := not r.adcClk;
         v.adcCnt := (others => '0');
      else
         v.adcCnt := r.adcCnt + 1;
      end if;

      -- Serial Shift Register clock counter
      if r.asicAcqReg.ssrClkEn = '1' then
        if r.asicAcqReg.ssrCnt >= r.asicAcqReg.ssrClkHalfT - 1 then
          v.asicAcqReg.ssrClk := not r.asicAcqReg.ssrClk;
          v.asicAcqReg.ssrCnt := (others => '0');
          --counts the periods
          if r.asicAcqReg.ssrClk = '1' then
            v.asicAcqReg.ssrClkCounter := r.asicAcqReg.ssrClkCounter + 1;
            -- Mux selection is bound by the number of parallel outputs
            if r.asicAcqReg.ssrDataSel < SSR_PARALLEL_OUT-1   then
              v.asicAcqReg.ssrDataSel    := r.asicAcqReg.ssrDataSel  + 1;
            else
              v.asicAcqReg.ssrDataSel    := 0;
            end if;
          end if;
        else
          v.asicAcqReg.ssrCnt := r.asicAcqReg.ssrCnt + 1;
        end if;
      else
          v.asicAcqReg.ssrClk := '0';
          v.asicAcqReg.ssrCnt := (others => '0');
      end if;

      -- serial shift register data mux
      if (r.asicAcqReg.ssrClkEn = '1') then --
        -- 40 parallel outputs
        v.asicAcqReg.ssrDatab := r.asicAcqReg.ssrData((r.asicAcqReg.ssrDataSel)); 
      else
        v.asicAcqReg.ssrDatab := '1';
      end if;
      
      -- programmable ASIC acquisition waveform
      if acqStart = '1' then
         v.boardRegOut.acqCnt       := r.boardRegOut.acqCnt + 1;
         v.asicAcqTimeCnt           := (others=>'0');
         v.asicAcqReg.SR0           := r.asicAcqReg.SR0Polarity;
         v.asicAcqReg.GlblRst       := r.asicAcqReg.GlblRstPolarity;
         v.asicAcqReg.Acq           := r.asicAcqReg.AcqPolarity;
         v.asicAcqReg.Tpulse        := r.asicAcqReg.TpulsePolarity;
         v.asicAcqReg.Start         := r.asicAcqReg.StartPolarity;
         v.asicAcqReg.PPbe          := r.asicAcqReg.PPbePolarity;
         v.asicAcqReg.Ppmat         := r.asicAcqReg.PpmatPolarity;
         v.asicAcqReg.Sync          := r.asicAcqReg.SyncPolarity;
         v.asicAcqReg.saciSync      := r.asicAcqReg.saciSyncPolarity;
         v.asicAcqReg.ssrClkEn      := '0';
         v.asicAcqReg.ssrClkCounter := 0;
         v.asicAcqReg.ssrDataSel    := 0;
      else
         if r.asicAcqTimeCnt /= x"FFFFFFFF" then
            v.asicAcqTimeCnt := r.asicAcqTimeCnt + 1;
         end if;
         
         -- single pulse. zero value corresponds to infinite delay/width
         if r.asicAcqReg.SR0Delay /= 0 and r.asicAcqReg.SR0Delay <= r.asicAcqTimeCnt then
            v.asicAcqReg.SR0 := not r.asicAcqReg.SR0Polarity;
            if r.asicAcqReg.SR0Width /= 0 and (r.asicAcqReg.SR0Width + r.asicAcqReg.SR0Delay) <= r.asicAcqTimeCnt then
               v.asicAcqReg.SR0 := r.asicAcqReg.SR0Polarity;
            end if;
         end if;

         -- single pulse. zero value corresponds to infinite delay/width
         if r.asicAcqReg.ssrRstDelay /= 0 and r.asicAcqReg.ssrRstDelay <= r.asicAcqTimeCnt then
            v.asicAcqReg.ssrRst := not r.asicAcqReg.ssrRstPolarity;
            if r.asicAcqReg.ssrRstWidth /= 0 and (r.asicAcqReg.ssrRstWidth + r.asicAcqReg.ssrRstDelay) <= r.asicAcqTimeCnt then
               v.asicAcqReg.ssrRst := r.asicAcqReg.ssrRstPolarity;
            end if;
         end if;
    
         -- single pulse. zero value corresponds to infinite delay
         if r.asicAcqReg.ssrClkDelay /= 0 and r.asicAcqReg.ssrClkDelay <= r.asicAcqTimeCnt then
            v.asicAcqReg.ssrClkEn := '1';
            if r.asicAcqReg.ssrClkNumPeriods-1 < r.asicAcqReg.ssrClkCounter then
               v.asicAcqReg.ssrClkEn := '0';
            end if;
         end if;
         
         -- single pulse. zero value corresponds to infinite delay/width
         --if r.asicAcqReg.GlblRstDelay /= 0 and r.asicAcqReg.GlblRstDelay <= r.asicAcqTimeCnt then
         --   v.asicAcqReg.GlblRst := not r.asicAcqReg.GlblRstPolarity;
         --   if r.asicAcqReg.GlblRstWidth /= 0 and (r.asicAcqReg.GlblRstWidth + r.asicAcqReg.GlblRstDelay) <= r.asicAcqTimeCnt then
               v.asicAcqReg.GlblRst := r.asicAcqReg.GlblRstPolarity;
         --   end if;
         --end if;
         
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
         
         -- single pulse. zero value corresponds to infinite delay/width
         if r.asicAcqReg.TpulseDelay /= 0 and r.asicAcqReg.TpulseDelay <= r.asicAcqTimeCnt then
            v.asicAcqReg.Tpulse := not r.asicAcqReg.TpulsePolarity;
            if r.asicAcqReg.TpulseWidth /= 0 and (r.asicAcqReg.TpulseWidth + r.asicAcqReg.TpulseDelay) <= r.asicAcqTimeCnt then
               v.asicAcqReg.Tpulse := r.asicAcqReg.TpulsePolarity;
            end if;
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
         if r.asicAcqReg.SyncDelay /= 0 and r.asicAcqReg.SyncDelay <= r.asicAcqTimeCnt then
            v.asicAcqReg.Sync := not r.asicAcqReg.SyncPolarity;
            if r.asicAcqReg.SyncWidth /= 0 and (r.asicAcqReg.SyncWidth + r.asicAcqReg.SyncDelay) <= r.asicAcqTimeCnt then
               v.asicAcqReg.Sync := r.asicAcqReg.SyncPolarity;
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
      
      -- epixhr bug workaround
      -- for a number of clock cycles
      -- data link is dropped after R0 
      if r.asicAcqReg.SR0 = not r.asicAcqReg.SR0Polarity then
         v.errInhibitCnt := (others=>'0');
         errInhibit <= '1';
      elsif r.errInhibitCnt <= 5000 then    -- inhibit for 50 us
         v.errInhibitCnt := r.errInhibitCnt + 1;
         errInhibit <= '1';
      else
         errInhibit <= '0';
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
      adcClk         <= r.adcClk;
      saciReadoutReq <= r.asicAcqReg.saciSync;
      asicPPbe       <= r.asicAcqReg.PPbe;
      asicPpmat      <= r.asicAcqReg.Ppmat;
      asicTpulse     <= r.asicAcqReg.Tpulse;
      asicStart      <= r.asicAcqReg.Start;
      asicSR0        <= r.asicAcqReg.SR0;
      asicGlblRst    <= r.asicAcqReg.GlblRst;
      asicSync       <= r.asicAcqReg.Sync;
      asicAcq        <= r.asicAcqReg.Acq;
      asicVid        <= r.asicAcqReg.Vid;
      asicSsrRst     <= r.asicAcqReg.ssrRst;
      asicSsrSerClrb <= r.asicAcqReg.ssrSerialClrb;
      asicSsrStoClrb <= r.asicAcqReg.ssrStorageClrb;
      asicSsrData    <= r.asicAcqReg.ssrDatab;
      asicSsrClk     <= r.asicAcqReg.ssrClk;
      
   end process comb;

   seq : process (axiClk) is
   begin
      if rising_edge(axiClk) then
         r <= rin after TPD_G;
      end if;
   end process seq;
   -----------------------------------------------
   -- Serial IDs: FPGA Device DNA + DS2411's
   -----------------------------------------------  
   GEN_DEVICE_DNA : if (EN_DEVICE_DNA_G = true) generate
      G_DEVICE_DNA : entity surf.DeviceDna
         generic map (
            TPD_G        => TPD_G,
            XIL_DEVICE_G => "ULTRASCALE")
         port map (
            clk      => axiClk,
            rst      => axiReset,
            dnaValue(127 downto 64) => open,
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
            clk       => axiClk,
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
      clk         => axiClk,
      dataIn      => adcCardStartUp,
      risingEdge  => adcCardStartUpEdge
   );
   
end rtl;
