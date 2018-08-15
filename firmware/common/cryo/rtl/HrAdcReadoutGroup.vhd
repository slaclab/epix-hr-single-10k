-------------------------------------------------------------------------------
-- File       : HrAdcReadoutGroup.vhd
-- Company    : SLAC National Accelerator Laboratory
-- Created    : 2016-05-26
-- Last update: 2018-07-06
-------------------------------------------------------------------------------
-- Description:
-- ADC Readout Controller
-- Receives ADC Data from a custom high rate adc asic.
-- Designed specifically for Ultrascale series FPGAs
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

library UNISIM;
use UNISIM.vcomponents.all;

use work.StdRtlPkg.all;
use work.AxiLitePkg.all;
use work.AxiStreamPkg.all;
use work.HrAdcPkg.all;

entity HrAdcReadoutGroup is
   generic (
      TPD_G             : time                 := 1 ns;
      NUM_CHANNELS_G    : natural range 1 to 8 := 8;
      DATA_TYPE_G       : string               := "12b14b";
      IODELAY_GROUP_G   : string               := "DEFAULT_GROUP";
      XIL_DEVICE_G      : string               := "ULTRASCALE";  -- place
                                                                 -- holder for
                                                                 -- an option  "7SERIES"
      IDELAYCTRL_FREQ_G : real                 := 200.0;
      DEFAULT_DELAY_G   : slv(8 downto 0)      := (others => '0');
      ADC_INVERT_CH_G   : slv(7 downto 0)      := "00000000");
   port (
      -- Master system clock, 125Mhz
      axilClk : in sl;
      axilRst : in sl;

      -- Axi Interface
      axilWriteMaster : in  AxiLiteWriteMasterType;
      axilWriteSlave  : out AxiLiteWriteSlaveType;
      axilReadMaster  : in  AxiLiteReadMasterType;
      axilReadSlave   : out AxiLiteReadSlaveType;

      -- Reset for adc deserializer
      adcClkRst : in sl;

      -- Serial Data from ADC
      adcSerial : in HrAdcSerialGroupType;

      -- Deserialized ADC Data
      adcStreamClk : in  sl;
      adcStreams   : out AxiStreamMasterArray(NUM_CHANNELS_G-1 downto 0) :=
      (others => axiStreamMasterInit((false, 2, 8, 0, TKEEP_NORMAL_C, 0, TUSER_NORMAL_C))));
end HrAdcReadoutGroup;

-- Define architecture
architecture rtl of HrAdcReadoutGroup is

   signal idelayCtrlRdy : sl;
   signal cmt_locked    : sl;

begin

 GEN_ULTRASCALE_HRADC : if ((XIL_DEVICE_G = "ULTRASCALE") and (DATA_TYPE_G = "12b14b")) generate
    U_HrADC_0 : entity work.Hr12bAdcReadoutGroupUS
      generic map (
        TPD_G             => TPD_G,
        NUM_CHANNELS_G    => NUM_CHANNELS_G,
        IODELAY_GROUP_G   => IODELAY_GROUP_G,
        IDELAYCTRL_FREQ_G => IDELAYCTRL_FREQ_G,
        DEFAULT_DELAY_G   => DEFAULT_DELAY_G,
        ADC_INVERT_CH_G   => ADC_INVERT_CH_G
        )
      port map (
        axilClk           => axilClk,
        axilRst           => axilRst,
        axilReadMaster    => axilReadMaster,
        axilReadSlave     => axilReadSlave,
        axilWriteMaster   => axilWriteMaster,
        axilWriteSlave    => axilWriteSlave,
        adcClkRst         => adcClkRst,
        adcSerial         => adcSerial,
        adcStreamClk      => adcStreamClk,
        adcStreams        => adcStreams
        );
  end generate GEN_ULTRASCALE_HRADC;
end rtl;

