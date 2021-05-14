-------------------------------------------------------------------------------
-- File       : cryo: EqualizerModules.vhd
-- Company    : SLAC National Accelerator Laboratory
-------------------------------------------------------------------------------
-- Description: This module enables the equalizer LOS status information
-- to be accessed via axi lite and exposes it to other modules after 
-- synchronization.
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

entity EqualizerModules is
   generic (
      TPD_G               : time             := 1 ns;
      AXIL_ERR_RESP_G     : slv(1 downto 0)  := AXI_RESP_DECERR_C;
      NUN_OF_EQUALIZER_IC : natural          := 6
   );
   port (
      sysClk            : in  sl;
      sysRst            : in  sl;
      -- IO signals
      EqualizerLOS      : in   slv(NUN_OF_EQUALIZER_IC-1 downto 0);
      EqualizerLOSSynced: out  slv(NUN_OF_EQUALIZER_IC-1 downto 0);
      -- AXI lite slave port for register access
      axilClk           : in  sl;
      axilRst           : in  sl;
      sAxilWriteMaster  : in  AxiLiteWriteMasterType;
      sAxilWriteSlave   : out AxiLiteWriteSlaveType;
      sAxilReadMaster   : in  AxiLiteReadMasterType;
      sAxilReadSlave    : out AxiLiteReadSlaveType
   );

end EqualizerModules;

architecture rtl of EqualizerModules is
   
   
   type EqualizerStatusType is record
      EqLOS         : slv(NUN_OF_EQUALIZER_IC-1 downto 0);
   end record EqualizerStatusType;
   
   constant EQUALIZER_STATUS_INIT_C : EqualizerStatusType := (
      EqLOS         => (others=>'0')
   );
   
   type RegType is record
      EqStatus          : EqualizerStatusType;
      sAxilWriteSlave   : AxiLiteWriteSlaveType;
      sAxilReadSlave    : AxiLiteReadSlaveType;
   end record RegType;

   constant REG_INIT_C : RegType := (
      EqStatus          => EQUALIZER_STATUS_INIT_C,
      sAxilWriteSlave   => AXI_LITE_WRITE_SLAVE_INIT_C,
      sAxilReadSlave    => AXI_LITE_READ_SLAVE_INIT_C
   );

   signal r   : RegType := REG_INIT_C;
   signal rin : RegType;
  
   signal EqualizerSync : EqualizerStatusType;
   
begin
  
   -------------------------------------------------
   -- output wiring
   -------------------------------------------------
   EqualizerLOSSynced <= EqualizerSync.EqLOS;
   
   --------------------------------------------------
   -- AXI Lite register logic
   --------------------------------------------------

   comb : process (axilRst, sAxilReadMaster, sAxilWriteMaster, r, EqualizerLOS) is
      variable v        : RegType;
      variable regCon   : AxiLiteEndPointType;
   begin
      v := r;
      
      axiSlaveWaitTxn(regCon, sAxilWriteMaster, sAxilReadMaster, v.sAxilWriteSlave, v.sAxilReadSlave);

      -- update read only registers
      v.EqStatus.EqLOS := EqualizerLOS;

      -- all registers for the present module
      axiSlaveRegisterR(regCon, x"00", 0, r.EqStatus.EqLOS);
      
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
            EqualizerSync <= EQUALIZER_STATUS_INIT_C after TPD_G;
         else
            EqualizerSync <= r.EqStatus after TPD_G;
         end if;
      end if;
   end process;
   

end rtl;
