-------------------------------------------------------------------------------
-- File       : Cryo ASIC: ClockJitterCleaner.vhd
-- Company    : SLAC National Accelerator Laboratory
-- Created    : 04/07/2017
-- Last update: 2018-11-02
-------------------------------------------------------------------------------
-- Description: This module enables to set all registers asssociated with the
-- clock jitter clean part at the cryo adapter board.
-- 
-------------------------------------------------------------------------------
-- This file is part of 'SLAC Firmware Standard Library'.
-- It is subject to the license terms in the LICENSE.txt file found in the 
-- top-level directory of this distribution and at: 
--    https://confluence.slac.stanford.edu/display/ppareg/LICENSE.html. 
-- No part of 'SLAC Firmware Standard Library', including this file, 
-- may be copied, modified, propagated, or distributed except according to 
-- the terms contained in the LICENSE.txt file.
-------------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;
use ieee.std_logic_arith.all;
use ieee.std_logic_unsigned.all;

use work.StdRtlPkg.all;
use work.AxiLitePkg.all;

entity ClockJitterCleaner is
   generic (
      TPD_G              : time             := 1 ns;
      AXIL_ERR_RESP_G    : slv(1 downto 0)  := AXI_RESP_DECERR_C
   );
   port (
      sysClk            : in  sl;
      sysRst            : in  sl;
      -- CJC control
      cjcRst            : out   sl(1 downto 0);
      cjcDec            : out   sl(1 downto 0);
      cjcInc            : out   sl(1 downto 0);
      cjcFrqtbl         : out   sl(1 downto 0);
      cjcRate           : out   slv(3 downto 0);
      cjcBwSel          : out   slv(3 downto 0);
      cjcFrqSel         : out   slv(7 downto 0);
      cjcSfout          : out   slv(3 downto 0);
      -- CJC Status
      cjcLos            : in    sl;
      cjcLol            : in    sl;
      
      -- AXI lite slave port for register access
      axilClk           : in  sl;
      axilRst           : in  sl;
      sAxilWriteMaster  : in  AxiLiteWriteMasterType;
      sAxilWriteSlave   : out AxiLiteWriteSlaveType;
      sAxilReadMaster   : in  AxiLiteReadMasterType;
      sAxilReadSlave    : out AxiLiteReadSlaveType
   );

end ClockJitterCleaner;

architecture rtl of ClockJitterCleaner is
   
   
   type ClockJitterCleanerType is record
      Rst            : sl(1 downto 0);
      Dec            : sl(1 downto 0);
      Inc            : sl(1 downto 0);
      Frqtbl         : sl(1 downto 0);
      Los            : sl;
      Lol            : sl;
      Rate           : slv(3 downto 0);
      BwSel          : slv(3 downto 0);
      FrqSel         : slv(7 downto 0);
      Sfout          : slv(3 downto 0);
   end record ClockJitterCleanerType;
   
   constant CLK_JITTER_CLEANER_INIT_C : ClockJitterCleanerType := (
      Rst          => (others=>'0'),
      Dec          => (others=>'0'),
      Inc          => (others=>'0'),
      Frqtbl       => (others=>'0'),
      Los          => '0',
      Lol          => '0',
      Rate         => (others=>'0'),
      BwSel        => (others=>'0'),
      FrqSel       => (others=>'0'),
      Sfout        => (others=>'0')
   );
   
   type RegType is record
      cjcReg            : ClockJitterCleanerType;
      sAxilWriteSlave   : AxiLiteWriteSlaveType;
      sAxilReadSlave    : AxiLiteReadSlaveType;
   end record RegType;

   constant REG_INIT_C : RegType := (
      cjcReg            => CLK_JITTER_CLEANER_INIT_C,
      sAxilWriteSlave   => AXI_LITE_WRITE_SLAVE_INIT_C,
      sAxilReadSlave    => AXI_LITE_READ_SLAVE_INIT_C
   );

   signal r   : RegType := REG_INIT_C;
   signal rin : RegType;
  
   signal cjcSync : ClockJitterCleanerType;
   
begin

  cjcRst           <= cjcSync.Rst;
  cjcDec           <= cjcSync.Dec;
  cjcInc           <= cjcSync.Inc;
  cjcFrqtbl        <= cjcSync.Frqtbl;
  cjcRate          <= cjcSync.Rate;
  cjcBwSel         <= cjcSync.BwSel;
  cjcFrqSel        <= cjcSync.FrqSel;
  cjcSfout         <= cjcSync.Sfout;
   
   --------------------------------------------------
   -- AXI Lite register logic
   --------------------------------------------------

   comb : process (axilRst, sAxilReadMaster, sAxilWriteMaster, r, cjcLol, cjcLos) is
      variable v        : RegType;
      variable regCon   : AxiLiteEndPointType;
   begin
      v := r;

      -- updating read only registers
      v.cjcReg.Lol := cjcLol;
      v.cjcReg.Los := cjcLos;
      
      v.sAxilReadSlave.rdata := (others => '0');
      axiSlaveWaitTxn(regCon, sAxilWriteMaster, sAxilReadMaster, v.sAxilWriteSlave, v.sAxilReadSlave);

      -- all registers for the present module
      axiSlaveRegisterR(regCon, x"00", 0, v.cjcReg.Lol);
      axiSlaveRegisterR(regCon, x"00", 1, v.cjcReg.Los);
      axiSlaveRegister (regCon, x"04", 0, v.cjcReg.Rst);
      axiSlaveRegister (regCon, x"04", 2, v.cjcReg.Dec);
      axiSlaveRegister (regCon, x"04", 4, v.cjcReg.Inc);
      axiSlaveRegister (regCon, x"04", 6, v.cjcReg.Frqtbl);
      axiSlaveRegister (regCon, x"08", 0, v.cjcReg.Rate);
      axiSlaveRegister (regCon, x"0C", 0, v.cjcReg.BwSel);
      axiSlaveRegister (regCon, x"10", 0, v.cjcReg.FrqSel);
      axiSlaveRegister (regCon, x"14", 0, v.cjcReg.Sfout);

      
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
         if sysRst = '1' then
            cjcSync <= CLK_JITTER_CLEANER_INIT_C after TPD_G;
         else
            cjcSync <= r.cjcReg after TPD_G;
         end if;
      end if;
   end process;
   

end rtl;
