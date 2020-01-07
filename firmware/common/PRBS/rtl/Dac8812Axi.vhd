-------------------------------------------------------------------------------
-- File       : Dac8812Axi.vhd
-- Company    : SLAC National Accelerator Laboratory
-------------------------------------------------------------------------------
-- Description: DAC Controller
-------------------------------------------------------------------------------
-- This file is part of 'EPIX HR Development Firmware'.
-- It is subject to the license terms in the LICENSE.txt file found in the 
-- top-level directory of this distribution and at: 
--    https://confluence.slac.stanford.edu/display/ppareg/LICENSE.html. 
-- No part of 'EPIX HR Development Firmware', including this file, 
-- may be copied, modified, propagated, or distributed except according to 
-- the terms contained in the LICENSE.txt file.
-------------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;
use ieee.std_logic_unsigned.all;
use ieee.numeric_std.all;

library surf;
use surf.StdRtlPkg.all;
use surf.AxiStreamPkg.all;
use surf.AxiLitePkg.all;
use surf.SsiPkg.all;

library epix_hr_core;
use epix_hr_core.EpixHrCorePkg.all;

use work.Dac8812Pkg.all;

entity Dac8812Axi is
   generic (
      TPD_G : time := 1 ns;
      MASTER_AXI_STREAM_CONFIG_G : AxiStreamConfigType   := ssiAxiStreamConfig(4, TKEEP_COMP_C);
      AXIL_ERR_RESP_G            : slv(1 downto 0)       := AXI_RESP_DECERR_C
   ); 
   port ( 

      -- Master system clock
      sysClk          : in  std_logic;
      sysClkRst       : in  std_logic;

      -- DAC Control Signals
      dacDin          : out std_logic;
      dacSclk         : out std_logic;
      dacCsL          : out std_logic;
      dacLdacL        : out std_logic;
      dacClrL         : out std_logic;

      -- AXI lite slave port for register access
      axilClk           : in  std_logic;
      axilRst           : in  std_logic;
      sAxilWriteMaster  : in  AxiLiteWriteMasterType;
      sAxilWriteSlave   : out AxiLiteWriteSlaveType;
      sAxilReadMaster   : in  AxiLiteReadMasterType;
      sAxilReadSlave    : out AxiLiteReadSlaveType

   );
end Dac8812Axi;


-- Define architecture
architecture Dac8812Axi_arch of Dac8812Axi is

    attribute keep : string;

    -- Local Signals
    signal dacData   : std_logic_vector(15 downto 0);
    signal dacCh     : std_logic_vector(1 downto 0);

    signal dacSync    : Dac8812ConfigType;

    type RegType is record
        dac               : Dac8812ConfigType;
        sAxilWriteSlave   : AxiLiteWriteSlaveType;
        sAxilReadSlave    : AxiLiteReadSlaveType;
    end record RegType;

    constant REG_INIT_C : RegType := (
        dac               => DAC8812_CONFIG_INIT_C,
        sAxilWriteSlave   => AXI_LITE_WRITE_SLAVE_INIT_C,
        sAxilReadSlave    => AXI_LITE_READ_SLAVE_INIT_C
    );
   
    signal r   : RegType := REG_INIT_C;
    signal rin : RegType;

    attribute keep of dacData : signal is "true";
    attribute keep of dacCh : signal is "true";
   

begin
    --------------------------------------------------
    -- component instantiation
    --------------------------------------------------

    dacData  <= dacSync.dacData;
    dacCh    <= dacSync.dacCh;

    DAC8812_0: entity work.Dac8812Cntrl
        generic map (
            TPD_G => TPD_G)
        port map (
            sysClk    => sysClk,
            sysClkRst => sysClkRst,
            dacData   => dacData,
            dacCh     => dacCh,
            dacDin    => dacDin,
            dacSclk   => dacSclk,
            dacCsL    => dacCsL,
            dacLdacL  => dacLdacL,
            dacClrL   => dacClrL);

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
      
      axiSlaveRegister (regCon, x"00",  0, v.dac.dacData);
      axiSlaveRegister (regCon, x"00", 16, v.dac.dacCh);

      
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
            dacSync <= DAC8812_CONFIG_INIT_C after TPD_G;
         else
            dacSync <= r.dac after TPD_G;
         end if;
      end if;
   end process;


end Dac8812Axi_arch;

