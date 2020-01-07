------------------------------------------------------------------------------
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

use work.Dac8812Pkg.all;
use work.AppPkg.all;

entity DacWaveformGenAxi is
   generic (
      TPD_G : time := 1 ns;
      NUM_SLAVE_SLOTS_G  : natural := 2; 
      NUM_MASTER_SLOTS_G : natural := 1;
      MASTERS_CONFIG_G   : AxiStreamConfigType   := ssiAxiStreamConfig(4, TKEEP_COMP_C);
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
      -- external trigger
      externalTrigger : in  std_logic;

      -- AXI lite slave port for register access
      axilClk           : in  std_logic;
      axilRst           : in  std_logic;
      sAxilWriteMaster  : in  AxiLiteWriteMasterArray(1 downto 0);
      sAxilWriteSlave   : out AxiLiteWriteSlaveArray(1 downto 0);
      sAxilReadMaster   : in  AxiLiteReadMasterArray(1 downto 0);
      sAxilReadSlave    : out AxiLiteReadSlaveArray(1 downto 0)
   );


end DacWaveformGenAxi;


-- Define architecture
architecture DacWaveformGenAxi_arch of DacWaveformGenAxi is

    attribute keep : string;

    constant ADDR_WIDTH_G : integer := 10;
    constant DATA_WIDTH_G : integer := 16;
    constant SAMPLING_COUNTER_WIDTH_G : integer := 12;

    -- Local Signals
    signal dacData            : std_logic_vector(15 downto 0);
    signal dacCh              : std_logic_vector(1 downto 0);
    signal waveform_en        : sl := '1';
    signal waveform_we        : sl := '0';
    signal waveform_weByte    : slv(wordCount(DATA_WIDTH_G, 8)-1 downto 0) := (others => '0');
    signal waveform_addr      : slv(ADDR_WIDTH_G-1 downto 0)               := (others => '0');
    signal waveform_din       : slv(DATA_WIDTH_G-1 downto 0)               := (others => '0');
    signal waveform_dout      : slv(DATA_WIDTH_G-1 downto 0);
    signal axiWrValid         : sl;
    signal axiWrStrobe        : slv(wordCount(DATA_WIDTH_G, 8)-1 downto 0);
    signal axiWrAddr          : slv(ADDR_WIDTH_G-1 downto 0);
    signal axiWrData          : slv(DATA_WIDTH_G-1 downto 0);
    signal dacSync            : Dac8812ConfigType;
    signal WaveformSync       : DacWaveformConfigType;
    signal counter, nextCounter                 : std_logic_vector(ADDR_WIDTH_G-1 downto 0);
    signal rampCounter, nextRampCounter         : std_logic_vector(DATA_WIDTH_G-1 downto 0);
    signal samplingCounter, nextSamplingCounter : std_logic_vector(SAMPLING_COUNTER_WIDTH_G-1 downto 0);

    type RegType is record
        dac               : Dac8812ConfigType;
        waveform          : DacWaveformConfigType;
        rCStartValue      : slv(DATA_WIDTH_G-1 downto 0);
        rCStopValue       : slv(DATA_WIDTH_G-1 downto 0);
        rCStep            : slv(DATA_WIDTH_G-1 downto 0);
        sAxilWriteSlave   : AxiLiteWriteSlaveType;
        sAxilReadSlave    : AxiLiteReadSlaveType;
    end record RegType;

    constant REG_INIT_C : RegType := (
        dac               => DAC8812_CONFIG_INIT_C,
        waveform          => DACWAVEFORM_CONFIG_INIT_C,
        rCStartValue      => (others=>'0'),
        rCStopValue       => (others=>'0'),
        rCStep            => (others=>'0'),
        sAxilWriteSlave   => AXI_LITE_WRITE_SLAVE_INIT_C,
        sAxilReadSlave    => AXI_LITE_READ_SLAVE_INIT_C
    );
   
    signal r   : RegType := REG_INIT_C;
    signal rin : RegType;

    attribute keep of dacDin : signal is "true";
    attribute keep of dacSclk : signal is "true";
    attribute keep of dacCsL : signal is "true";
    attribute keep of dacLdacL : signal is "true";
    attribute keep of dacClrL : signal is "true";
    attribute keep of dacData : signal is "true";
    attribute keep of dacCh : signal is "true";
    attribute keep of waveform_addr : signal is "true";
    attribute keep of waveform_dout : signal is "true";
   

begin

    --------------------------------------------------
    -- process declaration
    --------------------------------------------------
    waveform_en     <= r.waveform.enabled;    
    waveform_we     <= '0'; --only axi writes to the memory
    waveform_weByte <= (others => '0'); --only axi writes to the memory
    waveform_din    <= (others => '0'); --only axi writes to the memory
    waveform_addr   <= counter;

    comb_mux : process (dacSync, r, waveform_dout, rampCounter) is
        variable v          : RegType;
        variable axiStatus  : AxiLiteStatusType;
        variable decAddrInt : integer;
    begin
        -- dacData could be written by register or by the waveform gen
        if (r.waveform.enabled = '1') then
           if (r.waveform.source = "00") then
             dacData  <= waveform_dout;
           else
             dacData  <= rampCounter;
           end if;
        else
            dacData  <= dacSync.dacData;
        end if;

        -- dacCh is always set by an axi register
        dacCh    <= dacSync.dacCh;
    end process comb_mux;


    comb_waveformCounters : process (r, counter, samplingCounter, rampCounter) is
        variable v          : RegType;
        variable axiStatus  : AxiLiteStatusType;
        variable decAddrInt : integer;
    begin
        -- counter only run when the waveform generation run value is true        
        if (r.waveform.run = '1') then 

            -- creates the sampling rate
            if (samplingCounter = r.waveform.samplingCounter) then
                nextSamplingCounter <= (others => '0');
            else
                nextSamplingCounter <= samplingCounter + 1;
            end if;

            -- updates a pointer to output a new element from the waveform memory
            nextCounter <= counter + 1;

            -- data width counter
            if rampCounter = r.rCStopValue then
              nextRampCounter <= r.rCStartValue;
            else
              nextRampCounter <= rampCounter + r.rCStep;
            end if;
                        
        else
            nextSamplingCounter <= (others => '0');
            nextCounter <= (others => '0');
            nextRampCounter <= r.rCStartValue;
        end if;
    end process comb_waveformCounters;


    seq_waveformCounters : process(sysClk, sysClkRst) begin
      if rising_edge(sysClk) then
         --sampliing
         if sysClkRst = '1' then
            samplingCounter <= (others => '0') after TPD_G;
         else
            samplingCounter <= nextSamplingCounter after TPD_G;
         end if;
         -- counter used for memory address
         if sysClkRst = '1' then
            counter <= (others => '0') after TPD_G;
            rampCounter <= (others => '0') after TPD_G;
         else
            if (r.waveform.externalUpdateEn = '0') then
               if (samplingCounter = x"000") then
                   counter <= nextCounter after TPD_G;
                   rampCounter <= nextRampCounter after TPD_G;
               end if;
            else
                if (externalTrigger = '1') then
                   counter <= nextCounter after TPD_G;
                   rampCounter <= nextRampCounter after TPD_G;
               end if;
            end if;
         end if;
      end if;
   end process;



    --------------------------------------------------
    -- component instantiation
    --------------------------------------------------

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


    WAVEFORM_MEM_0: entity surf.AxiDualPortRam 
        generic map(
            TPD_G            => 1 ns,
            AXI_WR_EN_G      => true,
            SYS_WR_EN_G      => false,
            SYS_BYTE_WR_EN_G => false,
            COMMON_CLK_G     => false,
            ADDR_WIDTH_G     => ADDR_WIDTH_G,
            DATA_WIDTH_G     => DATA_WIDTH_G,
            INIT_G           => "0")
        port map (
            -- Axi Port
            axiClk         => sysClk,
            axiRst         => sysClkRst,
            axiReadMaster  => sAxilReadMaster(1),
            axiReadSlave   => sAxilReadSlave(1),
            axiWriteMaster => sAxilWriteMaster(1),
            axiWriteSlave  => sAxilWriteSlave(1),
            -- Standard Port
            clk           => sysClk,
            en            => waveform_en,
            we            => waveform_we,
            weByte        => waveform_weByte,
            rst           => sysClkRst,
            addr          => waveform_addr,
            din           => waveform_din,
            dout          => waveform_dout,
            axiWrValid    => axiWrValid,
            axiWrStrobe   => axiWrStrobe,
            axiWrAddr     => axiWrAddr,
            axiWrData     => axiWrData);


   --------------------------------------------------
   -- AXI Lite register logic
   --------------------------------------------------

   comb : process (axilRst, sAxilReadMaster, sAxilWriteMaster, r) is
      variable v        : RegType;
      variable regCon   : AxiLiteEndPointType;
   begin
      v := r;
            
      v.sAxilReadSlave.rdata := (others => '0');
      axiSlaveWaitTxn(regCon, sAxilWriteMaster(0), sAxilReadMaster(0), v.sAxilWriteSlave, v.sAxilReadSlave);
      
      axiSlaveRegister (regCon, x"0000",  0, v.waveform.enabled);
      axiSlaveRegister (regCon, x"0000",  1, v.waveform.run);
      axiSlaveRegister (regCon, x"0000",  2, v.waveform.externalUpdateEn);
      axiSlaveRegister (regCon, x"0000",  3, v.waveform.source);
      axiSlaveRegister (regCon, x"0004",  0, v.waveform.samplingCounter);
      axiSlaveRegister (regCon, x"0008",  0, v.dac.dacData);
      axiSlaveRegister (regCon, x"0008", 16, v.dac.dacCh);
      axiSlaveRegister (regCon, x"0010",  0, v.rCStartValue);
      axiSlaveRegister (regCon, x"0014",  0, v.rCStopValue);
      axiSlaveRegister (regCon, x"0018",  0, v.rCStep);
      
      axiSlaveDefault(regCon, v.sAxilWriteSlave, v.sAxilReadSlave, AXIL_ERR_RESP_G);
      
      if (axilRst = '1') then
         v := REG_INIT_C;
      end if;

      rin <= v;

      sAxilWriteSlave(0)   <= r.sAxilWriteSlave;
      sAxilReadSlave(0)    <= r.sAxilReadSlave;

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

end DacWaveformGenAxi_arch;

