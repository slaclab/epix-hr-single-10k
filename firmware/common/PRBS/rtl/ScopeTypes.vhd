-------------------------------------------------------------------------------
-- Title      : Virtual Oscilloscope Types
-- Project    : EPIX Readout
-------------------------------------------------------------------------------
-- File       : ScopeTypes.vhd
-- Company    : SLAC National Accelerator Laboratory
-------------------------------------------------------------------------------
-- Description:
-- Types for EPIX virtual oscilloscope
-------------------------------------------------------------------------------
-- This file is part of 'EPIX Development Firmware'.
-- It is subject to the license terms in the LICENSE.txt file found in the 
-- top-level directory of this distribution and at: 
--    https://confluence.slac.stanford.edu/display/ppareg/LICENSE.html. 
-- No part of 'EPIX Development Firmware', including this file, 
-- may be copied, modified, propagated, or distributed except according to 
-- the terms contained in the LICENSE.txt file.
-------------------------------------------------------------------------------

LIBRARY ieee;
USE ieee.std_logic_1164.ALL;

package ScopeTypes is

   --------------------------------------------
   -- Configuration Type
   --------------------------------------------

   -- Record
   type ScopeConfigType is record
      scopeEnable       : std_logic;
      triggerEnable     : std_logic;
      triggerEdge       : std_logic;
      triggerChannel    : std_logic_vector(3 downto 0);
      triggerMode       : std_logic_vector(1 downto 0);
      triggerAdcThresh  : std_logic_vector(15 downto 0);
      triggerHoldoff    : std_logic_vector(12 downto 0);
      triggerOffset     : std_logic_vector(12 downto 0);
      triggerDelay      : std_logic_vector(12 downto 0);
      traceLength       : std_logic_vector(12 downto 0);
      skipSamples       : std_logic_vector(12 downto 0);
      inputChannelA     : std_logic_vector(1 downto 0);
      inputChannelB     : std_logic_vector(1 downto 0);
      arm               : std_logic;
      trig              : std_logic;
   end record;

   -- Initialize
   constant SCOPE_CONFIG_INIT_C : ScopeConfigType := ( 
      scopeEnable      => '0',
      triggerEnable    => '0',
      triggerEdge      => '0',
      triggerChannel   => (others => '0'), 
      triggerMode      => (others => '0'), 
      triggerAdcThresh => (others => '0'),
      triggerHoldoff   => (others => '0'),
      triggerOffset    => (others => '0'),
      triggerDelay     => (others => '0'),
      traceLength      => (others => '0'),
      skipSamples      => (others => '0'),
      inputChannelA    => (others => '0'),
      inputChannelB    => (others => '0'),
      arm              => '0',
      trig             => '0'
   ); 
   
end ScopeTypes;

