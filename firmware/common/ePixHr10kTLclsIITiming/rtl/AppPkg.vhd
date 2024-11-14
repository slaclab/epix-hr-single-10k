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


   constant NUMBER_OF_ASICS_C : natural := 4;   
   constant NUMBER_OF_LANES_C : natural := 3;   
   
   constant HR_FD_NUM_AXI_MASTER_SLOTS_C  : natural := 25;
   constant HR_FD_NUM_AXI_SLAVE_SLOTS_C   : natural := 1;
   
   constant PLLREGS_AXI_INDEX_C            : natural := 0;
   constant TRIG_REG_AXI_INDEX_C           : natural := 1;
   constant HLS0_AXI_INDEX_C               : natural := 2;
   constant HLS1_AXI_INDEX_C               : natural := 3;
   constant PRBS2_AXI_INDEX_C              : natural := 4;
   constant AXI_STREAM_MON_INDEX_C         : natural := 5;
   constant DDR_MEM_INDEX_C                : natural := 6;
   constant SACIREGS_AXI_INDEX_C           : natural := 7;
   constant POWER_MODULE_INDEX_C           : natural := 8;
   constant DAC8812_REG_AXI_INDEX_C        : natural := 9;
   constant DACWFMEM_REG_AXI_INDEX_C       : natural := 10;
   constant DAC_MODULE_INDEX_C             : natural := 11;
   constant SCOPE_REG_AXI_INDEX_C          : natural := 12;
   constant ADC_RD_AXI_INDEX_C             : natural := 13;   
   constant ADC_CFG_AXI_INDEX_C            : natural := 14;   
   constant MONADC_REG_AXI_INDEX_C         : natural := 15;
   constant ASIC_READOUT_AXI_INDEX_C       : natural := 16;
   constant DIG_ASIC0_STREAM_AXI_INDEX_C   : natural := 17;
   constant DIG_ASIC1_STREAM_AXI_INDEX_C   : natural := 18;
   constant DIG_ASIC_PRE_PROC_AXI_INDEX_C  : natural := 19;
   constant APP_REG_AXI_INDEX_C            : natural := 20;
   constant TIMING_INDEX_C                 : natural := 21;
   constant EVENT_LANE_0_INDEX_C           : natural := 22;
   constant EVENT_LANE_1_INDEX_C           : natural := 23;
   constant EVENT_LANE_2_INDEX_C           : natural := 24;

   
   constant PLLREGS_AXI_BASE_ADDR_C         : slv(31 downto 0) := X"80000000";--0
   constant TRIG_REG_AXI_BASE_ADDR_C        : slv(31 downto 0) := X"81000000";--1
   constant HLS0_AXI_BASE_ADDR_C            : slv(31 downto 0) := X"82000000";--2
   constant HLS1_AXI_BASE_ADDR_C            : slv(31 downto 0) := X"83000000";--3
   constant PRBS2_AXI_BASE_ADDR_C           : slv(31 downto 0) := X"84000000";--4
-- constant PRBS3_AXI_BASE_ADDR_C           : slv(31 downto 0) := X"85000000";--5
   constant AXI_STREAM_MON_BASE_ADDR_C      : slv(31 downto 0) := X"86000000";--6
   constant DDR_MEM_BASE_ADDR_C             : slv(31 downto 0) := X"87000000";--7
   constant SACIREGS_BASE_ADDR_C            : slv(31 downto 0) := X"88000000";--8
   constant POWER_MODULE_BASE_ADDR_C        : slv(31 downto 0) := X"89000000";--9
   constant DAC8812_AXI_BASE_ADDR_C         : slv(31 downto 0) := X"8A000000";--10
   constant DACWFMEM_AXI_BASE_ADDR_C        : slv(31 downto 0) := X"8B000000";--11
   constant DAC_MODULE_ADDR_C               : slv(31 downto 0) := X"8C000000";--12
   constant SCOPE_REG_AXI_ADDR_C            : slv(31 downto 0) := X"8D000000";--13
   constant ADC_RD_AXI_ADDR_C               : slv(31 downto 0) := X"8E000000";--14
   constant ADC_CFG_AXI_ADDR_C              : slv(31 downto 0) := X"8F000000";--15
   constant MONADC_REG_AXI_ADDR_C           : slv(31 downto 0) := X"90000000";--16
   constant ASIC_READOUT_AXI_ADDR_C         : slv(31 downto 0) := X"94000000";--17
   constant DIG_ASIC0_STREAM_AXI_ADDR_C     : slv(31 downto 0) := X"95000000";--18
   constant DIG_ASIC1_STREAM_AXI_ADDR_C     : slv(31 downto 0) := X"95100000";--19
   constant DIG_ASIC_PRE_PROC_C             : slv(31 downto 0) := X"95200000";--20
   constant APP_REG_AXI_ADDR_C              : slv(31 downto 0) := X"96000000";--21
   constant TIMING_ADDR_C                   : slv(31 downto 0) := X"97000000";--22
   constant EVENT_LANE_0_ADDR_C             : slv(31 downto 0) := X"98000000";--23
   constant EVENT_LANE_1_ADDR_C             : slv(31 downto 0) := X"99000000";--24
   constant EVENT_LANE_2_ADDR_C             : slv(31 downto 0) := X"9A000000";--25
   
   constant HR_FD_AXI_CROSSBAR_MASTERS_CONFIG_C : AxiLiteCrossbarMasterConfigArray(HR_FD_NUM_AXI_MASTER_SLOTS_C-1 downto 0) := (
      PLLREGS_AXI_INDEX_C               => (
         baseAddr             => PLLREGS_AXI_BASE_ADDR_C,
         addrBits             => 24,
         connectivity         => x"FFFF"),
      TRIG_REG_AXI_INDEX_C              => ( 
         baseAddr             => TRIG_REG_AXI_BASE_ADDR_C,
         addrBits             => 24,
         connectivity         => x"FFFF"),
      HLS0_AXI_INDEX_C                 => ( 
         baseAddr             => HLS0_AXI_BASE_ADDR_C,
         addrBits             => 24,
         connectivity         => x"FFFF"),
      HLS1_AXI_INDEX_C                 => ( 
         baseAddr             => HLS1_AXI_BASE_ADDR_C,
         addrBits             => 24,
         connectivity         => x"FFFF"),
      PRBS2_AXI_INDEX_C                 => ( 
         baseAddr             => PRBS2_AXI_BASE_ADDR_C,
         addrBits             => 24,
         connectivity         => x"FFFF"),
      AXI_STREAM_MON_INDEX_C            => ( 
         baseAddr             => AXI_STREAM_MON_BASE_ADDR_C,
         addrBits             => 24,
         connectivity         => x"FFFF"),
      DDR_MEM_INDEX_C                   => ( 
         baseAddr             => DDR_MEM_BASE_ADDR_C,
         addrBits             => 24,
         connectivity         => x"FFFF"),      
      SACIREGS_AXI_INDEX_C              => ( 
         baseAddr             => SACIREGS_BASE_ADDR_C,
         addrBits             => 24,
         connectivity         => x"FFFF"),      
      POWER_MODULE_INDEX_C              => ( 
         baseAddr             => POWER_MODULE_BASE_ADDR_C,
         addrBits             => 24,
         connectivity         => x"FFFF"),
      DAC8812_REG_AXI_INDEX_C           => ( 
         baseAddr             => DAC8812_AXI_BASE_ADDR_C,
         addrBits             => 24,
         connectivity         => x"FFFF"),
      DACWFMEM_REG_AXI_INDEX_C           => ( 
         baseAddr             => DACWFMEM_AXI_BASE_ADDR_C,
         addrBits             => 24,
         connectivity         => x"FFFF"),
      DAC_MODULE_INDEX_C                 => ( 
         baseAddr             => DAC_MODULE_ADDR_C,
         addrBits             => 24,
         connectivity         => x"FFFF"),
      SCOPE_REG_AXI_INDEX_C              => ( 
         baseAddr             => SCOPE_REG_AXI_ADDR_C,
         addrBits             => 24,
         connectivity         => x"FFFF"),
      ADC_RD_AXI_INDEX_C                 => ( 
         baseAddr             => ADC_RD_AXI_ADDR_C,
         addrBits             => 24,
         connectivity         => x"FFFF"),
      ADC_CFG_AXI_INDEX_C                => ( 
         baseAddr             => ADC_CFG_AXI_ADDR_C,
         addrBits             => 24,
         connectivity         => x"FFFF"),
      MONADC_REG_AXI_INDEX_C             => ( 
         baseAddr             => MONADC_REG_AXI_ADDR_C,
         addrBits             => 24,
         connectivity         => x"FFFF"),
      ASIC_READOUT_AXI_INDEX_C           => ( 
         baseAddr             => ASIC_READOUT_AXI_ADDR_C,
         addrBits             => 24,
         connectivity         => x"FFFF"),
      DIG_ASIC0_STREAM_AXI_INDEX_C       => ( 
         baseAddr             => DIG_ASIC0_STREAM_AXI_ADDR_C,
         addrBits             => 20,
         connectivity         => x"FFFF"),
      DIG_ASIC1_STREAM_AXI_INDEX_C       => ( 
         baseAddr             => DIG_ASIC1_STREAM_AXI_ADDR_C,
         addrBits             => 20,
         connectivity         => x"FFFF"),
      DIG_ASIC_PRE_PROC_AXI_INDEX_C      => ( 
         baseAddr             => DIG_ASIC_PRE_PROC_C,
         addrBits             => 20,
         connectivity         => x"FFFF"),
      APP_REG_AXI_INDEX_C                => ( 
         baseAddr             => APP_REG_AXI_ADDR_C,
         addrBits             => 24,
         connectivity         => x"FFFF"),
      TIMING_INDEX_C                     => ( 
         baseAddr             => TIMING_ADDR_C,
         addrBits             => 24,
         connectivity         => x"FFFF"),
      EVENT_LANE_0_INDEX_C               => ( 
         baseAddr             => EVENT_LANE_0_ADDR_C,
         addrBits             => 24,
         connectivity         => x"FFFF"),
      EVENT_LANE_1_INDEX_C               => ( 
         baseAddr             => EVENT_LANE_1_ADDR_C,
         addrBits             => 24,
         connectivity         => x"FFFF"),
      EVENT_LANE_2_INDEX_C               => ( 
         baseAddr             => EVENT_LANE_2_ADDR_C,
         addrBits             => 24,
         connectivity         => x"FFFF")
   );


   type AppConfigType is record
      AppVersion           : slv(31 downto 0);
      powerEnable          : slv(3 downto 0);
      asicMask             : slv(NUMBER_OF_ASICS_C-1 downto 0);
      acqCnt               : slv(31 downto 0);
      requestStartupCal    : sl;
      startupAck           : sl;
      startupFail          : sl;
      epixhrDbgSel1        : slv(4 downto 0);
      epixhrDbgSel2        : slv(4 downto 0);
      epixhrDbgSel3        : slv(3 downto 0);
   end record;


   constant APP_CONFIG_INIT_C : AppConfigType := (
      AppVersion           => (others => '0'),
      powerEnable          => (others => '0'),
      asicMask             => (others => '0'),
      acqCnt               => (others => '0'),
      requestStartupCal    => '1',
      startupAck           => '0',
      startupFail          => '0',
      epixhrDbgSel1        => (others => '0'),
      epixhrDbgSel2        => (others => '0'),
      epixhrDbgSel3        => (others => '0')
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
