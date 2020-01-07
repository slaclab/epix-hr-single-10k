-------------------------------------------------------------------------------
-- File       : Ad9249Pkg.vhd
-- Company    : SLAC National Accelerator Laboratory
-------------------------------------------------------------------------------
-- Description: AD9249 Package File
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
use surf.AxiStreamPkg.all;

package HrAdcPkg is

   -- Interface to HrAdcSerialGroupType chip
   -- Chip has two SerialGroup outputs
   type HrAdcSerialGroupType is record
      fClkP : sl;                       -- Frame clock
      fClkN : sl;
      dClkP : sl;                       -- Data clock
      dClkN : sl;
      chP   : slv(7 downto 0);          -- Serial Data channels
      chN   : slv(7 downto 0);
   end record;

   type HrAdcSerialGroupArray is array (natural range <>) of HrAdcSerialGroupType;

   constant HrAdc_AXIS_CFG_G : AxiStreamConfigType := (
      TSTRB_EN_C    => false,
      TDATA_BYTES_C => 2,
      TDEST_BITS_C  => 0,
      TID_BITS_C    => 0,
      TKEEP_MODE_C  => TKEEP_FIXED_C,
      TUSER_BITS_C  => 0,
      TUSER_MODE_C  => TUSER_NONE_C);

end package HrAdcPkg;
