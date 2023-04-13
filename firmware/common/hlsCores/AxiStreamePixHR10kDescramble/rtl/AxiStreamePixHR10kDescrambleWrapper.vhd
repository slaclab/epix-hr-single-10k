-------------------------------------------------------------------------------
-- Company    : SLAC National Accelerator Laboratory
-------------------------------------------------------------------------------
-- Description: Wrapper on the Vivado HLS AXI Stream Buffer Mirror
-------------------------------------------------------------------------------
-- This file is part of 'Example Project Firmware'.
-- It is subject to the license terms in the LICENSE.txt file found in the
-- top-level directory of this distribution and at:
--    https://confluence.slac.stanford.edu/display/ppareg/LICENSE.html.
-- No part of 'Example Project Firmware', including this file,
-- may be copied, modified, propagated, or distributed except according to
-- the terms contained in the LICENSE.txt file.
-------------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;

library surf;
use surf.StdRtlPkg.all;
use surf.AxiStreamPkg.all;

entity AxiStreamePixHR10kDescrambleWrapper is
   generic (
      TPD_G : time := 1 ns);
   port (
      axisClk     : in  sl;
      axisRst     : in  sl;
      -- Slave Port
      sAxisMaster : in  AxiStreamMasterType;
      sAxisSlave  : out AxiStreamSlaveType;
      -- Master Port
      mAxisMaster : out AxiStreamMasterType;
      mAxisSlave  : in  AxiStreamSlaveType);
end AxiStreamePixHR10kDescrambleWrapper;

architecture rtl of AxiStreamePixHR10kDescrambleWrapper is

   component AxiStreamePixHR10kDescramble_0
      port (
         ap_clk          : in  std_logic;
         ap_rst_n        : in  std_logic;
         ibStream_TVALID : in  std_logic;
         ibStream_TREADY : out std_logic;
         ibStream_TDEST  : in  std_logic_vector(0 downto 0);
         ibStream_TDATA  : in  std_logic_vector(31 downto 0);
         ibStream_TKEEP  : in  std_logic_vector(3 downto 0);
         ibStream_TSTRB  : in  std_logic_vector(3 downto 0);
         ibStream_TUSER  : in  std_logic_vector(1 downto 0);
         ibStream_TLAST  : in  std_logic_vector(0 downto 0);
         ibStream_TID    : in  std_logic_vector(0 downto 0);
         obStream_TVALID : out std_logic;
         obStream_TREADY : in  std_logic;
         obStream_TDEST  : out std_logic_vector(0 downto 0);
         obStream_TDATA  : out std_logic_vector(31 downto 0);
         obStream_TKEEP  : out std_logic_vector(3 downto 0);
         obStream_TSTRB  : out std_logic_vector(3 downto 0);
         obStream_TUSER  : out std_logic_vector(1 downto 0);
         obStream_TLAST  : out std_logic_vector(0 downto 0);
         obStream_TID    : out std_logic_vector(0 downto 0)
         );
   end component;

   signal axisRstL   : sl;
   signal axisMaster : AxiStreamMasterType := AXI_STREAM_MASTER_INIT_C;

begin

   axisRstL    <= not(axisRst);
   mAxisMaster <= axisMaster;

   U_HLS : AxiStreamePixHR10kDescramble_0
      port map (
         ap_clk            => axisClk,
         ap_rst_n          => axisRstL,
         -- Inbound Interface
         ibStream_TVALID   => sAxisMaster.tValid,
         ibStream_TDATA    => sAxisMaster.tData(31 downto 0),
         ibStream_TKEEP    => sAxisMaster.tKeep(3 downto 0),
         ibStream_TSTRB    => sAxisMaster.tStrb(3 downto 0),
         ibStream_TUSER    => sAxisMaster.tUser(1 downto 0),
         ibStream_TLAST(0) => sAxisMaster.tLast,
         ibStream_TID      => sAxisMaster.tId(0 downto 0),
         ibStream_TDEST    => sAxisMaster.tDest(0 downto 0),
         ibStream_TREADY   => sAxisSlave.tReady,
         -- Outbound Interface
         obStream_TVALID   => axisMaster.tValid,
         obStream_TDATA    => axisMaster.tData(31 downto 0),
         obStream_TKEEP    => axisMaster.tKeep(3 downto 0),
         obStream_TSTRB    => axisMaster.tStrb(3 downto 0),
         obStream_TUSER    => axisMaster.tUser(1 downto 0),
         obStream_TLAST(0) => axisMaster.tLast,
         obStream_TID      => axisMaster.tId(0 downto 0),
         obStream_TDEST    => axisMaster.tDest(0 downto 0),
         obStream_TREADY   => mAxisSlave.tReady);

end rtl;
