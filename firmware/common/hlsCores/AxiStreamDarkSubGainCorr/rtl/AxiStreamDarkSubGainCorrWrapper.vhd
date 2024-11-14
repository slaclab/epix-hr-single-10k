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
use surf.AxiLitePkg.all;

entity AxiStreamDarkSubGainCorrWrapper is
   generic (
      TPD_G : time := 1 ns;
      G_S_AXI_CRTL_ADDR_WIDTH : positive := 5);
   port (
      axisClk     : in  sl;
      axisRst     : in  sl;
      -- Slave Port
      sAxisMaster : in  AxiStreamMasterArray(1 downto 0);
      sAxisSlave  : out AxiStreamSlaveArray(1 downto 0);
      -- Master Port
      mAxisMaster : out AxiStreamMasterType;
      mAxisSlave  : in  AxiStreamSlaveType;
       -- Axilite Port
      axiReadMaster  : in  AxiLiteReadMasterType;
      axiReadSlave   : out AxiLiteReadSlaveType;
      axiWriteMaster : in  AxiLiteWriteMasterType;
      axiWriteSlave  : out AxiLiteWriteSlaveType);
end AxiStreamDarkSubGainCorrWrapper;

architecture rtl of AxiStreamDarkSubGainCorrWrapper is

   constant C_S_AXI_CRTL_ADDR_WIDTH : positive := G_S_AXI_CRTL_ADDR_WIDTH;

   component AxiStreamDarkSubGainCorr_0
      port (
         ap_clk          : in  std_logic;
         ap_rst_n        : in  std_logic;
         ap_start        : in  std_logic;
         ibStream_TVALID : in  std_logic;
         ibStream_TREADY : out std_logic;
         ibStream_TDEST  : in  std_logic_vector(0 downto 0);
         ibStream_TDATA  : in  std_logic_vector(191 downto 0);
         ibStream_TKEEP  : in  std_logic_vector(23 downto 0);
         ibStream_TSTRB  : in  std_logic_vector(23 downto 0);
         ibStream_TUSER  : in  std_logic_vector(1 downto 0);
         ibStream_TLAST  : in  std_logic_vector(0 downto 0);
         ibStream_TID    : in  std_logic_vector(0 downto 0);
         --
         clbStream_TVALID : in  std_logic;
         clbStream_TREADY : out std_logic;
         clbStream_TDEST  : in  std_logic_vector(0 downto 0);
         clbStream_TDATA  : in  std_logic_vector(63 downto 0);
         clbStream_TKEEP  : in  std_logic_vector(7 downto 0);
         clbStream_TSTRB  : in  std_logic_vector(7 downto 0);
         clbStream_TUSER  : in  std_logic_vector(1 downto 0);
         clbStream_TLAST  : in  std_logic_vector(0 downto 0);
         clbStream_TID    : in  std_logic_vector(0 downto 0);
         --
         obStream_TVALID : out std_logic;
         obStream_TREADY : in  std_logic;
         obStream_TDEST  : out std_logic_vector(0 downto 0);
         obStream_TDATA  : out std_logic_vector(191 downto 0);
         obStream_TKEEP  : out std_logic_vector(23 downto 0);
         obStream_TSTRB  : out std_logic_vector(23 downto 0);
         obStream_TUSER  : out std_logic_vector(1 downto 0);
         obStream_TLAST  : out std_logic_vector(0 downto 0);
         obStream_TID    : out std_logic_vector(0 downto 0);
         --
         s_axi_crtl_AWVALID : in  std_logic;
         s_axi_crtl_AWREADY : out std_logic;
         s_axi_crtl_AWADDR  : in  std_logic_vector(C_S_AXI_CRTL_ADDR_WIDTH-1 downto 0);
         s_axi_crtl_WVALID  : in  std_logic;
         s_axi_crtl_WREADY  : out std_logic;
         s_axi_crtl_WDATA   : in  std_logic_vector(31 downto 0);
         s_axi_crtl_WSTRB   : in  std_logic_vector(3 downto 0); 
         s_axi_crtl_ARVALID : in  std_logic;
         s_axi_crtl_ARREADY : out std_logic;
         s_axi_crtl_ARADDR  : in  std_logic_vector(C_S_AXI_CRTL_ADDR_WIDTH-1 downto 0);
         s_axi_crtl_RVALID  : out std_logic;
         s_axi_crtl_RREADY  : in  std_logic;
         s_axi_crtl_RDATA   : out std_logic_vector(31 downto 0);
         s_axi_crtl_RRESP   : out std_logic_vector(1 downto 0);
         s_axi_crtl_BVALID  : out std_logic;
         s_axi_crtl_BREADY  : in  std_logic;
         s_axi_crtl_BRESP   : out std_logic_vector(1 downto 0)

         );
   end component;
   
   

   signal axisRstL   : sl;
   --signal axisMaster : AxiStreamMasterType := AXI_STREAM_MASTER_INIT_C;

begin

   axisRstL    <= not(axisRst);
   --mAxisMaster <= axisMaster;

   U_HLS : AxiStreamDarkSubGainCorr_0
      port map (
         ap_clk            => axisClk,
         ap_rst_n          => axisRstL,
         ap_start          => '1',
         -- Inbound Interface
         ibStream_TVALID   => sAxisMaster(0).tValid,
         ibStream_TDATA    => sAxisMaster(0).tData(191 downto 0),
         ibStream_TKEEP    => sAxisMaster(0).tKeep(23 downto 0),
         ibStream_TSTRB    => sAxisMaster(0).tStrb(23 downto 0),
         ibStream_TUSER    => sAxisMaster(0).tUser(1 downto 0),
         ibStream_TLAST(0) => sAxisMaster(0).tLast,
         ibStream_TID      => sAxisMaster(0).tId(0 downto 0),
         ibStream_TDEST    => sAxisMaster(0).tDest(0 downto 0),
         ibStream_TREADY   => sAxisSlave(0).tReady,
         -- Inbound Interface
         clbStream_TVALID   => sAxisMaster(1).tValid,
         clbStream_TDATA    => sAxisMaster(1).tData(63 downto 0),
         clbStream_TKEEP    => sAxisMaster(1).tKeep(7 downto 0),
         clbStream_TSTRB    => sAxisMaster(1).tStrb(7 downto 0),
         clbStream_TUSER    => sAxisMaster(1).tUser(1 downto 0),
         clbStream_TLAST(0) => sAxisMaster(1).tLast,
         clbStream_TID      => sAxisMaster(1).tId(0 downto 0),
         clbStream_TDEST    => sAxisMaster(1).tDest(0 downto 0),
         clbStream_TREADY   => sAxisSlave(1).tReady,
         -- Outbound Interface
         obStream_TVALID   => mAxisMaster.tValid,
         obStream_TDATA    => mAxisMaster.tData(191 downto 0),
         obStream_TKEEP    => mAxisMaster.tKeep(23 downto 0),
         obStream_TSTRB    => mAxisMaster.tStrb(23 downto 0),
         obStream_TUSER    => mAxisMaster.tUser(1 downto 0),
         obStream_TLAST(0) => mAxisMaster.tLast,
         obStream_TID      => mAxisMaster.tId(0 downto 0),
         obStream_TDEST    => mAxisMaster.tDest(0 downto 0),
         obStream_TREADY   => mAxisSlave.tReady,
         -- AxiLite
         s_axi_crtl_AWVALID => axiWriteMaster.awvalid,
         s_axi_crtl_AWREADY => axiWriteSlave.awready,
         s_axi_crtl_AWADDR  => axiWriteMaster.awaddr(C_S_AXI_CRTL_ADDR_WIDTH-1 downto 0),
         s_axi_crtl_WVALID  => axiWriteMaster.wvalid,
         s_axi_crtl_WREADY  => axiWriteSlave.wready,
         s_axi_crtl_WDATA   => axiWriteMaster.wdata,
         s_axi_crtl_WSTRB   => axiWriteMaster.wstrb,
         s_axi_crtl_ARVALID => axiReadMaster.arvalid,
         s_axi_crtl_ARREADY => axiReadSlave.arready,
         s_axi_crtl_ARADDR  => axiReadMaster.araddr(C_S_AXI_CRTL_ADDR_WIDTH-1 downto 0),
         s_axi_crtl_RVALID  => axiReadSlave.rvalid,
         s_axi_crtl_RREADY  => axiReadMaster.rready,
         s_axi_crtl_RDATA   => axiReadSlave.rdata,
         s_axi_crtl_RRESP   => axiReadSlave.rresp,
         s_axi_crtl_BVALID  => axiWriteSlave.bvalid,
         s_axi_crtl_BREADY  => axiWriteMaster.bready,
         s_axi_crtl_BRESP   => axiWriteSlave.bresp);

end rtl;
