-------------------------------------------------------------------------------
-- File       : AppPkg.vhd
-- Company    : SLAC National Accelerator Laboratory
-------------------------------------------------------------------------------
-- Description: Application's Package File
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

library surf;
use surf.StdRtlPkg.all;
use surf.AxiLitePkg.all;

package AppPkg is


   constant NUMBER_OF_ASICS_C : natural := 0;   
   constant NUMBER_OF_LANES_C : natural := 4;   
   
   constant HR_FD_NUM_AXI_MASTER_SLOTS_C  : natural := 16;
   constant HR_FD_NUM_AXI_SLAVE_SLOTS_C   : natural := 1;
   
   constant PLLREGS_AXI_INDEX_C           : natural := 0;
   constant TRIG_REG_AXI_INDEX_C          : natural := 1;
   constant PRBS0_AXI_INDEX_C             : natural := 2;
   constant PRBS1_AXI_INDEX_C             : natural := 3;
   constant PRBS2_AXI_INDEX_C             : natural := 4;
   constant PRBS3_AXI_INDEX_C             : natural := 5;
   constant AXI_STREAM_MON_INDEX_C        : natural := 6;
   constant DDR_MEM_INDEX_C               : natural := 7;
   constant POWER_MODULE_INDEX_C          : natural := 8;
   constant DAC8812_REG_AXI_INDEX_C       : natural := 9;
   constant DACWFMEM_REG_AXI_INDEX_C      : natural := 10;
   constant DAC_MODULE_INDEX_C            : natural := 11;
   constant SCOPE_REG_AXI_INDEX_C         : natural := 12;
   constant ADC_RD_AXI_INDEX_C            : natural := 13;   
   constant ADC_CFG_AXI_INDEX_C           : natural := 14;   
   constant MONADC_REG_AXI_INDEX_C        : natural := 15;
   
   
   constant PLLREGS_AXI_BASE_ADDR_C         : slv(31 downto 0) := X"00000000";
   constant TRIG_REG_AXI_BASE_ADDR_C        : slv(31 downto 0) := X"01000000";
   constant PRBS0_AXI_BASE_ADDR_C           : slv(31 downto 0) := X"02000000";
   constant PRBS1_AXI_BASE_ADDR_C           : slv(31 downto 0) := X"03000000";
   constant PRBS2_AXI_BASE_ADDR_C           : slv(31 downto 0) := X"04000000";
   constant PRBS3_AXI_BASE_ADDR_C           : slv(31 downto 0) := X"05000000";
   constant AXI_STREAM_MON_BASE_ADDR_C      : slv(31 downto 0) := X"06000000";
   constant DDR_MEM_BASE_ADDR_C             : slv(31 downto 0) := X"07000000";
   constant POWER_MODULE_BASE_ADDR_C        : slv(31 downto 0) := X"08000000";
   constant DAC8812_AXI_BASE_ADDR_C         : slv(31 downto 0) := X"09000000";
   constant DACWFMEM_AXI_BASE_ADDR_C        : slv(31 downto 0) := X"0A000000";
   constant DAC_MODULE_ADDR_C               : slv(31 downto 0) := X"0B000000";
   constant SCOPE_REG_AXI_ADDR_C            : slv(31 downto 0) := X"0C000000";
   constant ADC_RD_AXI_ADDR_C               : slv(31 downto 0) := X"0D000000";
   constant ADC_CFG_AXI_ADDR_C              : slv(31 downto 0) := X"0E000000";
   constant MONADC_REG_AXI_ADDR_C           : slv(31 downto 0) := X"0F000000";
   
   constant HR_FD_AXI_CROSSBAR_MASTERS_CONFIG_C : AxiLiteCrossbarMasterConfigArray(HR_FD_NUM_AXI_MASTER_SLOTS_C-1 downto 0) := (
      PLLREGS_AXI_INDEX_C       => (
         baseAddr             => PLLREGS_AXI_BASE_ADDR_C,
         addrBits             => 24,
         connectivity         => x"FFFF"),
      TRIG_REG_AXI_INDEX_C      => ( 
         baseAddr             => TRIG_REG_AXI_BASE_ADDR_C,
         addrBits             => 24,
         connectivity         => x"FFFF"),
      PRBS0_AXI_INDEX_C        => ( 
         baseAddr             => PRBS0_AXI_BASE_ADDR_C,
         addrBits             => 24,
         connectivity         => x"FFFF"),
      PRBS1_AXI_INDEX_C        => ( 
         baseAddr             => PRBS1_AXI_BASE_ADDR_C,
         addrBits             => 24,
         connectivity         => x"FFFF"),
      PRBS2_AXI_INDEX_C        => ( 
         baseAddr             => PRBS2_AXI_BASE_ADDR_C,
         addrBits             => 24,
         connectivity         => x"FFFF"),
      PRBS3_AXI_INDEX_C        => ( 
         baseAddr             => PRBS3_AXI_BASE_ADDR_C,
         addrBits             => 24,
         connectivity         => x"FFFF"),
      AXI_STREAM_MON_INDEX_C   => ( 
         baseAddr             => AXI_STREAM_MON_BASE_ADDR_C,
         addrBits             => 24,
         connectivity         => x"FFFF"),
      DDR_MEM_INDEX_C          => ( 
         baseAddr             => DDR_MEM_BASE_ADDR_C,
         addrBits             => 24,
         connectivity         => x"FFFF"),
      POWER_MODULE_INDEX_C    => ( 
         baseAddr             => POWER_MODULE_BASE_ADDR_C,
         addrBits             => 24,
         connectivity         => x"FFFF"),
      DAC8812_REG_AXI_INDEX_C      => ( 
         baseAddr             => DAC8812_AXI_BASE_ADDR_C,
         addrBits             => 24,
         connectivity         => x"FFFF"),
      DACWFMEM_REG_AXI_INDEX_C      => ( 
         baseAddr             => DACWFMEM_AXI_BASE_ADDR_C,
         addrBits             => 24,
         connectivity         => x"FFFF"),
      DAC_MODULE_INDEX_C            => ( 
         baseAddr             => DAC_MODULE_ADDR_C,
         addrBits             => 24,
         connectivity         => x"FFFF"),
      SCOPE_REG_AXI_INDEX_C         => ( 
         baseAddr             => SCOPE_REG_AXI_ADDR_C,
         addrBits             => 24,
         connectivity         => x"FFFF"),
     ADC_RD_AXI_INDEX_C         => ( 
         baseAddr             => ADC_RD_AXI_ADDR_C,
         addrBits             => 24,
         connectivity         => x"FFFF"),
      ADC_CFG_AXI_INDEX_C         => ( 
         baseAddr             => ADC_CFG_AXI_ADDR_C,
         addrBits             => 24,
         connectivity         => x"FFFF"),
      MONADC_REG_AXI_INDEX_C        => ( 
         baseAddr             => MONADC_REG_AXI_ADDR_C,
         addrBits             => 24,
         connectivity         => x"FFFF")
   );


   type AppConfigType is record
      AppVersion           : slv(31 downto 0);
   end record;


   constant APP_CONFIG_INIT_C : AppConfigType := (
      AppVersion           => (others => '0')
   );
   
   type HR_FDConfigType is record
      pwrEnableReq         : sl;
   end record;

   constant HR_FD_CONFIG_INIT_C : HR_FDConfigType := (
      pwrEnableReq         => '0'
   );
   

end package AppPkg;

package body AppPkg is

end package body AppPkg;
