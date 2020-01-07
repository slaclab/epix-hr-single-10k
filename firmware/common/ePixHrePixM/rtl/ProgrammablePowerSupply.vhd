-------------------------------------------------------------------------------
-- File       : ProgrammablePowerSupply.vhd
-- Company    : SLAC National Accelerator Laboratory
-------------------------------------------------------------------------------
-- Description: cryo ASIC adapter board registers for the Programmable Power
-- Supply.
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

entity ProgrammablePowerSupply is
   generic (
      TPD_G             : time := 1 ns;
      CLK_PERIOD_G      : real := 10.0e-9;
      NUM_DAC_G         : integer := 5
   );
   port (
      -- Global Signals
      axiClk         : in  sl;
      axiRst         : in  sl;
      -- AXI-Lite Register Interface (axiClk domain)
      axiReadMaster  : in  AxiLiteReadMasterType;
      axiReadSlave   : out AxiLiteReadSlaveType;
      axiWriteMaster : in  AxiLiteWriteMasterType;
      axiWriteSlave  : out AxiLiteWriteSlaveType;
      -- DAC interfaces
      dacSclk        : out sl;
      dacDin         : out sl;
      dacCsb         : out slv(NUM_DAC_G-1 downto 0);
      dacClrb        : out sl
   );
end ProgrammablePowerSupply;

architecture rtl of ProgrammablePowerSupply is
   
   type RegType is record
      vDacSetting       : Slv16Array(NUM_DAC_G-1 downto 0);
      axiReadSlave      : AxiLiteReadSlaveType;
      axiWriteSlave     : AxiLiteWriteSlaveType;
   end record RegType;
   
   constant REG_INIT_C : RegType := (
      vDacSetting       => (others => (others=>'0')),
      axiReadSlave      => AXI_LITE_READ_SLAVE_INIT_C,
      axiWriteSlave     => AXI_LITE_WRITE_SLAVE_INIT_C
   );

   signal r   : RegType := REG_INIT_C;
   signal rin : RegType;
    
   signal axiReset : sl;
   
   signal dacDinSig  : slv(NUM_DAC_G-1 downto 0);  -- common signals
   signal dacSclkSig : slv(NUM_DAC_G-1 downto 0);  -- common signals
   signal dacClrbSig : slv(NUM_DAC_G-1 downto 0);  -- common signals
   
begin

   axiReset <= axiRst;
   --dacDin   <= uOr(dacDinSig);
   dacDin   <= (dacDinSig(4) or dacDinSig(3) or dacDinSig(2) or dacDinSig(1) or dacDinSig(0));
   --dacSclk  <= uOr(dacSclkSig);
   dacSclk  <= (dacSclkSig(4) or dacSclkSig(3) or dacSclkSig(2) or dacSclkSig(1) or dacSclkSig(0));
   --dacClrb  <= uOr(dacClrbSig);
   dacClrb <= (dacClrbSig(4) or dacClrbSig(3) or dacClrbSig(2) or dacClrbSig(1) or dacClrbSig(0));
   -------------------------------
   -- Configuration Register
   -------------------------------  
   comb : process (axiReadMaster, axiReset, axiWriteMaster, r) is
      variable v           : RegType;
      variable regCon      : AxiLiteEndPointType;
      
   begin
      -- Latch the current value
      v := r;
      
      -- Reset data and strobes
      v.axiReadSlave.rdata       := (others => '0');
            
      -- Determine the transaction type
      axiSlaveWaitTxn(regCon, axiWriteMaster, axiReadMaster, v.axiWriteSlave, v.axiReadSlave);
      
      -- Map out standard registers
      --axiSlaveRegister(regCon,  x"000000",  0, v.enableLDO); -- Guard ring dac
      for i in 0 to NUM_DAC_G-1 loop
        axiSlaveRegister(regCon,  x"000004"+toSlv((i*4), 24),  0, v.vDacSetting(i));
      end loop;      
      
      axiSlaveDefault(regCon, v.axiWriteSlave, v.axiReadSlave, AXI_RESP_OK_C);
      
      -- Synchronous Reset
      if axiReset = '1' then
         v := REG_INIT_C;
      end if;

      -- Register the variable for next clock cycle
      rin <= v;

      axiWriteSlave   <= r.axiWriteSlave;
      axiReadSlave    <= r.axiReadSlave;

      -- outputs
      
      
   end process comb;

   seq : process (axiClk) is
   begin
      if rising_edge(axiClk) then
         r <= rin after TPD_G;
      end if;
   end process seq;
   
   -----------------------------------------------
   -- DAC Controller
   -----------------------------------------------
   G_MAX5443 : for i in 0 to (NUM_DAC_G-1) generate
       U_DacCntrl : entity work.DacCntrl 
       generic map (
          TPD_G => TPD_G
       )
       port map ( 
          sysClk      => axiClk,
          sysClkRst   => axiReset,
          dacData     => r.vDacSetting(i),
          dacDin      => dacDinSig(i),
          dacSclk     => dacSclkSig(i),
          dacCsL      => dacCsb(i),
          dacClrL     => dacClrbSig(i)
       );
   end generate;      
   
end rtl;
