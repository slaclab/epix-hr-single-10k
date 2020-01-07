-------------------------------------------------------------------------------
-- File       : EpixHr: PowerControlModule.vhd
-- Company    : SLAC National Accelerator Laboratory
-------------------------------------------------------------------------------
-- Description: This module enable the voltage regulators on the epix boards
-- based on saci register values. If needed synchronization modules should be
-- inserted in this module as well.
-------------------------------------------------------------------------------
-- This file is part of 'EPIX HR Firmware'.
-- It is subject to the license terms in the LICENSE.txt file found in the 
-- top-level directory of this distribution and at: 
--    https://confluence.slac.stanford.edu/display/ppareg/LICENSE.html. 
-- No part of 'EPIX HR Firmware', including this file, 
-- may be copied, modified, propagated, or distributed except according to 
-- the terms contained in the LICENSE.txt file.
-------------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;
use ieee.std_logic_arith.all;
use ieee.std_logic_unsigned.all;

library surf;
use surf.StdRtlPkg.all;
use surf.AxiLitePkg.all;

entity PowerControlModule is
   generic (
      TPD_G              : time             := 1 ns;
      AXIL_ERR_RESP_G    : slv(1 downto 0)  := AXI_RESP_DECERR_C
   );
   port (
      sysClk        : in  sl;
      sysRst        : in  sl;
      -- power control
      digPwrEn         : out   sl;
      anaPwrEn         : out   sl;
      syncDigDcDc      : out   sl;
      syncAnaDcDc      : out   sl;
      syncDcDc         : out   slv(6 downto 0);
      
      -- AXI lite slave port for register access
      axilClk           : in  sl;
      axilRst           : in  sl;
      sAxilWriteMaster  : in  AxiLiteWriteMasterType;
      sAxilWriteSlave   : out AxiLiteWriteSlaveType;
      sAxilReadMaster   : in  AxiLiteReadMasterType;
      sAxilReadSlave    : out AxiLiteReadSlaveType
   );

end PowerControlModule;

architecture rtl of PowerControlModule is
   
   
   type PowerControlType is record
      digPwrEn         : sl;
      anaPwrEn         : sl;
      syncDigDcDc      : sl;
      syncAnaDcDc      : sl;
      syncDcDc         : slv(6 downto 0);
   end record PowerControlType;
   
   constant POWER_CONTROL_INIT_C : PowerControlType := (
      digPwrEn         => '0',
      anaPwrEn         => '0',
      syncDigDcDc      => '0',
      syncAnaDcDc      => '0',
      syncDcDc         => (others=>'0')
   );
   
   type RegType is record
      powerReg          : PowerControlType;
      sAxilWriteSlave   : AxiLiteWriteSlaveType;
      sAxilReadSlave    : AxiLiteReadSlaveType;
   end record RegType;

   constant REG_INIT_C : RegType := (
      powerReg          => POWER_CONTROL_INIT_C,
      sAxilWriteSlave   => AXI_LITE_WRITE_SLAVE_INIT_C,
      sAxilReadSlave    => AXI_LITE_READ_SLAVE_INIT_C
   );

   signal r   : RegType := REG_INIT_C;
   signal rin : RegType;
  
   signal powerSync : PowerControlType;
   
begin

  digPwrEn         <= powerSync.digPwrEn;
  anaPwrEn         <= powerSync.anaPwrEn;
  syncDigDcDc      <= powerSync.syncDigDcDc;
  syncAnaDcDc      <= powerSync.syncAnaDcDc;
  syncDcDc         <= powerSync.syncDcDc;
   
   --------------------------------------------------
   -- AXI Lite register logic
   --------------------------------------------------

   comb : process (axilRst, sAxilReadMaster, sAxilWriteMaster, r) is
      variable v        : RegType;
      variable regCon   : AxiLiteEndPointType;
   begin
      v := r;
      
      v.sAxilReadSlave.rdata := (others => '0');
      axiSlaveWaitTxn(regCon, sAxilWriteMaster, sAxilReadMaster, v.sAxilWriteSlave, v.sAxilReadSlave);

      -- all registers for the present module
      axiSlaveRegister (regCon, x"00", 0, v.powerReg.digPwrEn);
      axiSlaveRegister (regCon, x"00", 1, v.powerReg.anaPwrEn);
      
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
            powerSync <= POWER_CONTROL_INIT_C after TPD_G;
         else
            powerSync <= r.powerReg after TPD_G;
         end if;
      end if;
   end process;
   

end rtl;
