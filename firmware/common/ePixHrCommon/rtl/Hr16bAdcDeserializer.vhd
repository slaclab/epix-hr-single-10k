-------------------------------------------------------------------------------
-- File       : Hr16bAdcDeserializerUS.vhd
-- Company    : SLAC National Accelerator Laboratory
-------------------------------------------------------------------------------
-- Description:
-- ADC data deserializer
-- Receives serial ADC Data from an Hr12bAdc SLAC ASIC.
-- Designed specifically for Xilinx Ultrascale series FPGAs
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
use ieee.std_logic_arith.all;
use ieee.std_logic_unsigned.all;
use ieee.std_logic_arith.all;
use ieee.numeric_std.all;

library surf;
use surf.StdRtlPkg.all;
use surf.AxiLitePkg.all;
use surf.AxiStreamPkg.all;

use work.HrAdcPkg.all;

library UNISIM;
use UNISIM.vcomponents.all;

entity Hr16bAdcDeserializer is
   generic (
      TPD_G             : time                 := 1 ns;
      NUM_CHANNELS_G    : natural range 1 to 8 := 8;
      IODELAY_GROUP_G   : string               := "DEFAULT_GROUP";
      IDELAYCTRL_FREQ_G : real                 := 350.0;
      DEFAULT_DELAY_G   : slv(8  downto 0)     := (others => '0');
      FRAME_PATTERN_G   : slv(19 downto 0)     := "11111111110000000000";
      ADC_INVERT_CH_G   : sl                   := '0';
      BIT_REV_G         : sl                   := '0';
      MSB_LSB_G         : sl                   := '1' -- '0' for "MSB_FIRST"
                                                      -- and '1' for "LSB_FIRST"
                                                      );
   port (
      -- Reset for adc deserializer
      adcClkRst : in  sl;                -- global reset
      idelayRst : in  sl;                -- register based reset  
      iserdesRst: in  sl;                -- register based reset 
      -- Serial Data from ADC
      dClk      : in  sl;                       -- Data clock
      dClkDiv4  : in  sl;
      dClkDiv5  : in  sl;
      sDataP    : in  sl;                       -- Frame clock
      sDataN    : in  sl;
      sDataOutP : out sl;                       -- copy of the data
      sDataOutN : out sl;     
      -- Signal to control data gearboxes
      loadDelay       : in sl;
      delay           : in slv(8 downto 0) := "000000000";
      delayValueOut   : out slv(9 downto 0);
      bitSlip         : in slv(4 downto 0) := "00000";
      tenbOrder       : in sl := '1';
      gearboxOffset   : in slv(1 downto 0) := "00";
      dataValid       : out sl;
      tenbData        : out Slv10Array(7 downto 0);            
      pixData         : out slv(19 downto 0)     
      );
end Hr16bAdcDeserializer;

-- Define architecture
architecture rtl of Hr16bAdcDeserializer is

  attribute keep : string;
  -------------------------------------------------------------------------------------------------
  -- ADC Readout Clocked Registers
  -------------------------------------------------------------------------------------------------
  type AdcClkDiv4RegType is record
    masterData         : slv(7  downto 0);
    masterData_1       : slv(7  downto 0);
    masterData_2       : slv(7  downto 0);
    masterData_3       : slv(7  downto 0);
    masterData_4       : slv(7  downto 0);
    longDataCounter    : slv(2  downto 0);
    longData           : slv(39 downto 0);
    longData_1         : slv(39 downto 0);
    bitSlip            : slv(4  downto 0);
    masterDataBS       : slv(7  downto 0);
    masterDataBS_1     : slv(7  downto 0);
    longDataStable     : sl;
  end record;

  constant ADC_CLK_DV4_REG_INIT_C : AdcClkDiv4RegType := (
    masterData         => (others => '0'),
    masterData_1       => (others => '0'),
    masterData_2       => (others => '0'),
    masterData_3       => (others => '0'),
    masterData_4       => (others => '0'),
    longDataCounter    => (others => '0'),
    longData           => (others => '0'),
    longData_1         => (others => '0'),
    bitSlip            => (others => '0'),
    masterDataBS       => (others => '0'),
    masterDataBS_1     => (others => '0'),
    longDataStable     => '0'
    );

  type AdcClkDiv5RegType is record
    gearboxCounter      : slv(1 downto 0);
    gearboxSeq          : slv(1 downto 0);
    tenbData            : Slv10Array(7 downto 0);
    masterPixData       : slv(19 downto 0);
    tenbOrder           : sl;
    dataAligned         : sl;
    valid               : sl;
    pixDataGearboxIn    : slv(7 downto 0);
    pixDataGearboxIn_1  : slv(7 downto 0);
    
  end record;

  constant ADC_CLK_DV5_REG_INIT_C : AdcClkDiv5RegType := (
    gearboxCounter      => (others => '0'),
    gearboxSeq          => (others => '0'),
    tenbData            => (others=>(others=>'0')),
    masterPixData       => (others => '0'),
    tenbOrder           => '0',
    dataAligned         => '0',
    valid               => '0',
    pixDataGearboxIn    => (others => '0'),
    pixDataGearboxIn_1  => (others => '0')
    );

  
  
  signal adcDV4R   : AdcClkDiv4RegType := ADC_CLK_DV4_REG_INIT_C;
  signal adcDv4Rin : AdcClkDiv4RegType;

  signal adcDV5R   : AdcClkDiv5RegType := ADC_CLK_DV5_REG_INIT_C;
  signal adcDv5Rin : AdcClkDiv5RegType;
  

   -- Local signals
  signal sDataPadP  : sl;
  signal sDataPadN  : sl;
  signal sData_i    : sl;
  signal sData_d    : sl;
  signal cascOut    : sl;
  signal cascRet    : sl;
  signal delayValueOut1   : slv(8 downto 0);
  signal delayValueOut2   : slv(8 downto 0);

  -- iserdes signal
  signal masterData      : slv(7 downto 0);

  attribute keep of adcDV4R          : signal is "true";
  attribute keep of adcDV5R          : signal is "true";
  attribute keep of sData_i          : signal is "true";

begin

  PixData <= adcDv5R.masterPixData(10)&adcDv5R.masterPixData(11)&adcDv5R.masterPixData(12)&adcDv5R.masterPixData(13)&adcDv5R.masterPixData(14)&adcDv5R.masterPixData(15)&adcDv5R.masterPixData(16)&adcDv5R.masterPixData(17)&adcDv5R.masterPixData(18)&adcDv5R.masterPixData(19)&adcDv5R.masterPixData(0)&adcDv5R.masterPixData(1)&adcDv5R.masterPixData(2)&adcDv5R.masterPixData(3)&adcDv5R.masterPixData(4)&adcDv5R.masterPixData(5)&adcDv5R.masterPixData(6)&adcDv5R.masterPixData(7)&adcDv5R.masterPixData(8)&adcDv5R.masterPixData(9)                       when BIT_REV_G = '1'
             else adcDv5R.masterPixData;

  sDataOutP <= '1';--sData_d;-- sending sData_d is not routable
  sDataOutN <= '0';
  -------------------------------------------------------------------------------------------------
  -- Create Clocks
  -------------------------------------------------------------------------------------------------
  
  -- input sData buffer
  --
  U_IBUFDS_sData : IBUFDS_DIFF_OUT
    generic map (
      DQS_BIAS => "FALSE"  -- (FALSE, TRUE)
      )
    port map (
      O  => sDataPadP,   -- 1-bit output: Buffer output
      OB => sDataPadN,
      I  => sDataP,   -- 1-bit input: Diff_p buffer input (connect directly to top-level port)
      IB => sDataN  -- 1-bit input: Diff_n buffer input (connect directly to top-level port)
      );
  -- Optionally invert the pad input
  sData_i <= sDataPadP when ADC_INVERT_CH_G = '0' else sDataPadN;
  ----------------------------------------------------------------------------
  -- idelay3 
  ----------------------------------------------------------------------------
  U_IDELAYE3_0 : entity surf.Idelaye3Wrapper 
    generic map (
      CASCADE => "NONE",          -- Cascade setting (MASTER, NONE, SLAVE_END, SLAVE_MIDDLE)
      DELAY_FORMAT => "COUNT",     -- Units of the DELAY_VALUE (COUNT, TIME)
      DELAY_SRC => "IDATAIN",     -- Delay input (DATAIN, IDATAIN)
      DELAY_TYPE => "VAR_LOAD",   -- Set the type of tap delay line (FIXED, VARIABLE, VAR_LOAD)
      DELAY_VALUE => conv_integer(DEFAULT_DELAY_G), -- Input delay value setting
      IS_CLK_INVERTED => '0',     -- Optional inversion for CLK
      IS_RST_INVERTED => '0',     -- Optional inversion for RST
      REFCLK_FREQUENCY => IDELAYCTRL_FREQ_G,  -- IDELAYCTRL clock input frequency in MHz (200.0-2667.0)
      SIM_DEVICE => "ULTRASCALE", -- Set the device version (ULTRASCALE, ULTRASCALE_PLUS, ULTRASCALE_PLUS_ES1,
                                  -- ULTRASCALE_PLUS_ES2)
      UPDATE_MODE => "ASYNC"      -- Determines when updates to the delay will take effect (ASYNC, MANUAL,
                                  -- SYNC)
      )
    port map (
      CASC_OUT => cascOut,           -- 1-bit output: Cascade delay output to ODELAY input cascade
      CNTVALUEOUT => delayValueOut1, -- 9-bit output: Counter value output
      DATAOUT => sData_d,            -- 1-bit output: Delayed data output
      CASC_IN => '0',                -- 1-bit input: Cascade delay input from slave ODELAY CASCADE_OUT
      CASC_RETURN => cascRet,        -- 1-bit input: Cascade delay returning from slave ODELAY DATAOUT
      CE => '0',                     -- 1-bit input: Active high enable increment/decrement input
      CLK => dClkDiv4,               -- 1-bit input: Clock input
      CNTVALUEIN => delay,           -- 9-bit input: Counter value input
      DATAIN => '1',                 -- 1-bit input: Data input from the logic
      EN_VTC => '0',                 -- 1-bit input: Keep delay constant over VT
      IDATAIN => sData_i,            -- 1-bit input: Data input from the IOBUF
      INC => '0',                    -- 1-bit input: Increment / Decrement tap delay input
      LOAD => loadDelay,             -- 1-bit input: Load DELAY_VALUE input
      RST => idelayRst               -- 1-bit input: Asynchronous Reset to the DELAY_VALUE
      );    

  ODELAYE3_inst : entity surf.Odelaye3Wrapper 
    generic map (
      CASCADE => "SLAVE_END",    -- Cascade setting (MASTER, NONE, SLAVE_END, SLAVE_MIDDLE)
      DELAY_FORMAT => "COUNT",   -- Units of the DELAY_VALUE (COUNT, TIME)
      DELAY_TYPE => "VAR_LOAD",  -- Set the type of tap delay line (FIXED, VARIABLE, VAR_LOAD)
      DELAY_VALUE => conv_integer(DEFAULT_DELAY_G), -- Input delay value setting
      IS_CLK_INVERTED => '0',    -- Optional inversion for CLK
      IS_RST_INVERTED => '0',    -- Optional inversion for RST
      REFCLK_FREQUENCY => 300.0, -- IDELAYCTRL clock input frequency in MHz (200.0-2400.0)
      UPDATE_MODE => "ASYNC")    -- Determines when updates to the delay will take effect (ASYNC, MANUAL, SYNC)
    port map (
      CASC_IN     => cascOut,          -- 1-bit input: Cascade delay input from slave IDELAY CASCADE_OUT
      CASC_OUT    => open,             -- 1-bit output: Cascade delay output to IDELAY input cascade 
      CASC_RETURN => '0',              -- 1-bit input: Cascade delay returning from slave IDELAY DATAOUT 
      ODATAIN     => '0',              -- 1-bit input: Data input
      DATAOUT     => cascRet,          -- 1-bit output: Delayed data from ODATAIN input port 
      CLK         => dClkDiv4,         -- 1-bit input: Clock input 
      EN_VTC      => '0',              -- 1-bit input: Keep delay constant over VT 
      INC         => '0',              -- 1-bit input: Increment / Decrement tap delay input
      CE          => '0',              -- 1-bit input: Active high enable increment/decrement input 
      LOAD        => loadDelay,        -- 1-bit input: Load DELAY_VALUE input 
      RST         => idelayRst,        -- 1-bit input: Asynchronous Reset to the DELAY_VALUE 
      CNTVALUEIN  => delay,            -- 9-bit input: Counter value input
      CNTVALUEOUT => delayValueOut2);  -- 9-bit output: Counter value output

  delayValueOut <= resize(delayValueOut1, 10, '0') + delayValueOut2;-- 
  ----------------------------------------------------------------------------
  -- iserdes3
  ----------------------------------------------------------------------------
  U_ISERDESE3_master : ISERDESE3
    generic map (
      DATA_WIDTH => 8,            -- Parallel data width (4,8)
      FIFO_ENABLE => "FALSE",     -- Enables the use of the FIFO
      FIFO_SYNC_MODE => "FALSE",  -- Enables the use of internal 2-stage synchronizers on the FIFO
      IS_CLK_B_INVERTED => '1',   -- Optional inversion for CLK_B
      IS_CLK_INVERTED => '0',     -- Optional inversion for CLK
      IS_RST_INVERTED => '0',     -- Optional inversion for RST
      SIM_DEVICE => "ULTRASCALE"  -- Set the device version (ULTRASCALE, ULTRASCALE_PLUS, ULTRASCALE_PLUS_ES1,
                                  -- ULTRASCALE_PLUS_ES2)
      )
    port map (
      FIFO_EMPTY => OPEN,         -- 1-bit output: FIFO empty flag
      INTERNAL_DIVCLK => open,    -- 1-bit output: Internally divided down clock used when FIFO is
                                  -- disabled (do not connect)

      Q => masterData,            -- bit registered output
      CLK => dClk,            -- 1-bit input: High-speed clock
      CLKDIV => dClkDiv4,         -- 1-bit input: Divided Clock
      CLK_B => dClk,        -- 1-bit input: Inversion of High-speed clock CLK
      D => sData_d,               -- 1-bit input: Serial Data Input
      FIFO_RD_CLK => '1',         -- 1-bit input: FIFO read clock
      FIFO_RD_EN => '1',          -- 1-bit input: Enables reading the FIFO when asserted
      RST => iserdesRst           -- 1-bit input: Asynchronous Reset
      );

  -----------------------------------------------------------------------------
  -- custom logic 
  -----------------------------------------------------------------------------

  -----------------------------------------------------------------------------
  -- 8 to 16, 56 gearbox and bitSlip control logic
  -- Part or all 56 bits can be used for idelay3 adjustment
  -----------------------------------------------------------------------------
  adc8to56GearboxComb : process (adcDv4R, masterData, bitSlip) is
    variable v : AdcClkDiv4RegType;
  begin

     v := adcDv4R;

     -- update register with signal values
     v.masterData   := masterData;
     v.bitSlip      := bitSlip;

     -- creates pipeline
     v.masterData_1 := adcDv4R.masterData;
     v.masterData_2 := adcDv4R.masterData_1;
     v.masterData_3 := adcDv4R.masterData_2;
     v.masterData_4 := adcDv4R.masterData_3;
     v.longData_1   := adcDv4R.longData;
     v.masterDataBS_1 := adcDv4R.masterDataBS;
     
     -- data checks on this logic.
     -- 56 bit assembly logic
     case (adcDv4R.longDataCounter) is
       when "000" =>
         v.longData(7 downto 0) := adcDv4R.masterData_1;
         v.longDataCounter := adcDv4R.longDataCounter + 1;
       when "001" =>
         v.longData(15 downto 8) := adcDv4R.masterData_1;
         v.longDataCounter := adcDv4R.longDataCounter + 1;
       when "010" =>
         v.longData(23 downto 16) := adcDv4R.masterData_1;
         v.longDataCounter := adcDv4R.longDataCounter + 1;
       when "011" =>
         v.longData(31 downto 24) := adcDv4R.masterData_1;
         v.longDataCounter := adcDv4R.longDataCounter + 1;            
       when "100" =>
         v.longData(39 downto 32) := adcDv4R.masterData_1;
         v.longDataCounter := (others => '0');
       when others =>
         v.longData  := (others => '0');
         v.longDataCounter := (others => '0');
     end case;

     if adcDv4R.longDataCounter = "000" then
       if adcDv4r.longData = adcDv4r.longData_1 then
         v.longDataStable := '1';
       else
         v.longDataStable := '0';
       end if;
     end if;
   
     --bit slip logic
     case (adcDv4R.bitSlip) is
       when "00000" =>
         v.masterDataBS := adcDv4R.masterData(7 downto 0);
       when "00001" =>
         v.masterDataBS := adcDv4R.masterData(6 downto 0) & adcDv4R.masterData_1(7);
       when "00010" =>
         v.masterDataBS := adcDv4R.masterData(5 downto 0) & adcDv4R.masterData_1(7 downto 6);
       when "00011" =>
         v.masterDataBS := adcDv4R.masterData(4 downto 0) & adcDv4R.masterData_1(7 downto 5);
       when "00100" =>
         v.masterDataBS := adcDv4R.masterData(3 downto 0) & adcDv4R.masterData_1(7 downto 4);
       when "00101" =>
         v.masterDataBS := adcDv4R.masterData(2 downto 0) & adcDv4R.masterData_1(7 downto 3);
       when "00110" =>
         v.masterDataBS := adcDv4R.masterData(1 downto 0) & adcDv4R.masterData_1(7 downto 2);
       when "00111" =>
         v.masterDataBS := adcDv4R.masterData(0)          & adcDv4R.masterData_1(7 downto 1);
       when "01000" =>
         v.masterDataBS := adcDv4R.masterData_1(7 downto 0);
       when "01001" =>
         v.masterDataBS := adcDv4R.masterData_1(6 downto 0) & adcDv4R.masterData_2(7);
       when "01010" =>
         v.masterDataBS := adcDv4R.masterData_1(5 downto 0) & adcDv4R.masterData_2(7 downto 6);
       when "01011" =>
         v.masterDataBS := adcDv4R.masterData_1(4 downto 0) & adcDv4R.masterData_2(7 downto 5);
       when "01100" =>
         v.masterDataBS := adcDv4R.masterData_1(3 downto 0) & adcDv4R.masterData_2(7 downto 4);
       when "01101" =>
         v.masterDataBS := adcDv4R.masterData_1(2 downto 0) & adcDv4R.masterData_2(7 downto 3);
       when "01110" =>
         v.masterDataBS := adcDv4R.masterData_1(1 downto 0) & adcDv4R.masterData_2(7 downto 2);
       when "01111" =>
         v.masterDataBS := adcDv4R.masterData_1(0)          & adcDv4R.masterData_2(7 downto 1);
       when "10000" =>
         v.masterDataBS := adcDv4R.masterData_2(7 downto 0);
       when "10001" =>
         v.masterDataBS := adcDv4R.masterData_2(6 downto 0) & adcDv4R.masterData_3(7);
       when "10010" =>
         v.masterDataBS := adcDv4R.masterData_2(5 downto 0) & adcDv4R.masterData_3(7 downto 6);
       when "10011" =>
         v.masterDataBS := adcDv4R.masterData_2(4 downto 0) & adcDv4R.masterData_3(7 downto 5);
       when "10100" =>
         v.masterDataBS := adcDv4R.masterData_2(3 downto 0) & adcDv4R.masterData_3(7 downto 4);
       when "10101" =>
         v.masterDataBS := adcDv4R.masterData_2(2 downto 0) & adcDv4R.masterData_3(7 downto 3);
       when "10110" =>
         v.masterDataBS := adcDv4R.masterData_2(1 downto 0) & adcDv4R.masterData_3(7 downto 2);
       when "10111" =>
         v.masterDataBS := adcDv4R.masterData_2(0)          & adcDv4R.masterData_3(7 downto 1);
       when "11000" =>
         v.masterDataBS := adcDv4R.masterData_3(7 downto 0);
       when "11001" =>
         v.masterDataBS := adcDv4R.masterData_3(6 downto 0) & adcDv4R.masterData_4(7);
       when "11010" =>
         v.masterDataBS := adcDv4R.masterData_3(5 downto 0) & adcDv4R.masterData_4(7 downto 6);
       when "11011" =>
         v.masterDataBS := adcDv4R.masterData_3(4 downto 0) & adcDv4R.masterData_4(7 downto 5);
       when "11100" =>
         v.masterDataBS := adcDv4R.masterData_3(3 downto 0) & adcDv4R.masterData_4(7 downto 4);
       when "11101" =>
         v.masterDataBS := adcDv4R.masterData_3(2 downto 0) & adcDv4R.masterData_4(7 downto 3);
       when "11110" =>
         v.masterDataBS := adcDv4R.masterData_3(1 downto 0) & adcDv4R.masterData_4(7 downto 2);
       when "11111" =>
         v.masterDataBS := adcDv4R.masterData_3(0)          & adcDv4R.masterData_4(7 downto 1);
       when others =>
         v.masterDataBS := (others => '0');
     end case;

     adcDv4Rin <= v;
         
     --outputs
     
   end process;

  adclongSeq : process (adcClkRst, dClkDiv4, adcDv4Rin) is 
  begin
    if (adcClkRst = '1') then           
      adcDv4R <= ADC_CLK_DV4_REG_INIT_C;
    elsif (rising_edge(dClkDiv4)) then
      -- latch deserializer data
      adcDv4R <= adcDv4Rin  after TPD_G;
    end if;      
  end process;
   
          
  adc8To7GearboxComb : process (adcDv4R, adcDv5R, gearboxOffset, tenbOrder) is
    variable v : AdcClkDiv5RegType;
  begin

    v := adcDv5R;

    v.tenbOrder           := tenbOrder;
    v.gearboxSeq          := adcDv5R.gearboxCounter + gearboxOffset;
    v.pixDataGearboxIn    := adcDv4R.masterDataBS;
    v.pixDataGearboxIn_1  := adcDv4R.masterDataBS_1;
    
    -- flag that indicates data, or frame signal matches the expected pattern
    if adcDv5R.masterPixData = FRAME_PATTERN_G then
      v.dataAligned := '1';
    else
      v.dataAligned := '0';
    end if;

    if MSB_LSB_G = '1' then             -- LSB
      case (adcDv5R.gearboxSeq) is
        when "00" =>
          v.tenbData(0)   := adcDv5R.pixDataGearboxIn( 1 downto 0) & adcDv5R.pixDataGearboxIn_1( 7 downto 0);
          v.gearboxCounter  := adcDv5R.gearboxCounter + 1;
        when "01" =>
          v.tenbData(0)   := adcDv5R.pixDataGearboxIn( 3 downto 0) & adcDv5R.pixDataGearboxIn_1( 7 downto 2);
          v.gearboxCounter  := adcDv5R.gearboxCounter + 1;
        when "10" =>
          v.tenbData(0)   := adcDv5R.pixDataGearboxIn( 5 downto 0) & adcDv5R.pixDataGearboxIn_1( 7 downto 4);
          v.gearboxCounter  := adcDv5R.gearboxCounter + 1;
        when "11" =>
          v.tenbData(0)   := adcDv5R.pixDataGearboxIn( 7 downto 0) & adcDv5R.pixDataGearboxIn_1( 7 downto 6);
          v.gearboxCounter  := adcDv5R.gearboxCounter + 1;
        when others =>
          v.tenbData(0)   := (others => '0');
          v.gearboxCounter  := (others => '0');
      end case;
    else
      case (adcDv5R.gearboxSeq) is
        when "11" =>
          v.tenbData(0)   := adcDv5R.pixDataGearboxIn( 1 downto 0) & adcDv5R.pixDataGearboxIn_1( 7 downto 0);
          v.gearboxCounter  := adcDv5R.gearboxCounter + 1;
        when "00" =>
          v.tenbData(0)   := adcDv5R.pixDataGearboxIn( 3 downto 0) & adcDv5R.pixDataGearboxIn_1( 7 downto 2);
          v.gearboxCounter  := adcDv5R.gearboxCounter + 1;
        when "01" =>
          v.tenbData(0)   := adcDv5R.pixDataGearboxIn( 5 downto 0) & adcDv5R.pixDataGearboxIn_1( 7 downto 4);
          v.gearboxCounter  := adcDv5R.gearboxCounter + 1;
        when "10" =>
          v.tenbData(0)   := adcDv5R.pixDataGearboxIn( 7 downto 0) & adcDv5R.pixDataGearboxIn_1( 7 downto 6);
          v.gearboxCounter  := adcDv5R.gearboxCounter + 1;
        when others =>
          v.tenbData(0)   := (others => '0');
          v.gearboxCounter  := (others => '0');
      end case;
    end if;

    -- latch whole double word
    v.valid := not adcDv5R.valid;
    if adcDv5R.valid = '1' then
      if adcDv5R.tenbOrder = '0' then
        v.masterPixData  := adcDv5R.tenbData(3) & adcDv5R.tenbData(2);
      else
        v.masterPixData  := adcDv5R.tenbData(2) & adcDv5R.tenbData(3);
      end if;
    end if;
    
    -- 10 bit words pipeline
    for i in 1 to 7 loop
         v.tenbData(i) := adcDv5R.tenbData(i-1);
    end loop;

    adcDv5Rin <= v;
         
    --outputs
    dataValid <= adcDv5R.valid;
    tenbData  <= adcDv5R.tenbData;
    
  end process;
   
   
  adc8To7GearboxSeq : process (adcClkRst, dClkDiv5, adcDv5Rin) is 
  begin
    if (adcClkRst = '1') then
      adcDv5R <= ADC_CLK_DV5_REG_INIT_C;
    elsif (rising_edge(dClkDiv5)) then
      -- latch deserializer data
      adcDv5R <= adcDv5Rin after TPD_G;
    end if;  
  end process;
end rtl;

