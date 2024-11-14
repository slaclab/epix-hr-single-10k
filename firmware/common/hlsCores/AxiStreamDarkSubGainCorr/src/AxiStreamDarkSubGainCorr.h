//////////////////////////////////////////////////////////////////////////////
// This file is part of 'Vivado HLS Example'.
// It is subject to the license terms in the LICENSE.txt file found in the
// top-level directory of this distribution and at:
//    https://confluence.slac.stanford.edu/display/ppareg/LICENSE.html.
// No part of 'Vivado HLS Example', including this file,
// may be copied, modified, propagated, or distributed except according to
// the terms contained in the LICENSE.txt file.
//////////////////////////////////////////////////////////////////////////////

#ifndef _AXI_STREAM_DARKSUBGAINCORR_H_
#define _AXI_STREAM_DARKSUBGAINCORR_H_


#include "ap_axi_sdata.h"
#include "hls_stream.h"

#include <stdio.h>
#include <cstdint>


/* --------------------------------------------------------------------- *//*!
 *
 *   \brief Template to describe an ASIC
 *
 *   \par
 *    Since the ASIC is an actual piece of hardware, it is really not
 *    parameterizable, it is what it is.  This templateis provided for
 *    development and testing purposes, but primarily as just a place
 *    to gather the relevant parameters in one place.
 *
 *  \tparam NSTREAMS_PER_ASIC  The number of output streams per ASIC
 *  \tparam             NROWS  The number of output rows
 *  \tparam  NCOLS_PER_STREAM  The number of columns per stream
 *  \tparam        DATA_WIDTH  The width, in bits of ASIC data word
 *  \tparam      START_COLUMN  The starting column
 *
 *  \par \e START_COLUMN explanation
 *   Because of the way the ASIC is readout, the readout cannot start
 *   on COL = 0, but rather \e START_COLUMN.  This means, the initial
 *   \e START_COLUMNs are garbage data and need to be ignored.
 *
 *   Further it (if START_COLUMN=30, means the data order is
 *       (Discard first 30),           (ROW0, COL30), (ROW0, COL31)
 *       (ROW0,COL0), (ROW0, COL1) ... (ROW1, COL30), (ROW1, COL31)
 *       .
 *
 *   The firmware's job is to reassemble (descramble) these scrambled eggs
 *                                                                       */
/* --------------------------------------------------------------------- */
template<size_t   NSTREAMS_PER_ASIC,   // Number of streams/ASIC
         size_t               NROWS,   // Number of ASIC Rows
         size_t NCOLUMNS_PER_STREAM,   // Number of ASIC Columns/stream
         size_t          DATA_WIDTH,   // Number of bits in the ASIC data
         size_t        START_COLUMN>   // Start column of data from previous row
class AsicCfg
{
public:
   static constexpr auto NStreamsPerAsic = NSTREAMS_PER_ASIC;
   static constexpr auto NRows           = NROWS;
   static constexpr auto NColsPerStream  = NCOLUMNS_PER_STREAM;
   static constexpr auto DataWidth       = DATA_WIDTH;
   static constexpr auto StartColumn     = START_COLUMN;

   static constexpr auto NColsPerAsic    = NColsPerStream  * NStreamsPerAsic;
   static constexpr auto NPixelsPerAsic  = NColsPerAsic    * NRows;

   // -------------------------
   // Define the ASIC data word
   // -------------------------
   class Data
   {
   public:
      Data () = delete;

      // -----------------------------------------------------
      // Layout the beginning (lo) and ending (hi) bit numbers
      // of each field in a 16-bit unsigned integer
      // -----------------------------------------------------
      static constexpr auto   AdcBitLo =  0;
      static constexpr auto   AdcBitHi = 13;

      static constexpr auto GainBitLo  = 14;
      static constexpr auto GainBitHi  = 14;

      static constexpr auto  MbzBitLo  = 15;
      static constexpr auto  MbzBitHi  = 15;

      static constexpr auto    AdcNBits =   AdcBitHi -  AdcBitLo + 1;
      static constexpr auto  GainNBits =  GainBitHi -  GainBitLo + 1;
      static constexpr auto   MbzNBits =   MbzBitHi -   MbzBitLo + 1;

      static_assert (AdcNBits + GainNBits + MbzNBits == 16,
                    "\n"
                    "ERROR: AsicCfg::Data the number of bits in the word must be 16\n\n");

      using   Adc_t = ap_uint< AdcNBits>;
      using  Gain_t = ap_uint<GainNBits>;
      using   Mbz_t = ap_uint< MbzNBits>;
      using    Type = ap_uint<16>;

      // Retrieve the ADC value
      static Adc_t getAdc (Type data)
      {
         #pragma HLS INLINE
         return data (AdcBitHi, AdcBitLo);
      }

      // Retrieve the ADC gain
      static Gain_t getGain  (Type data)
      {
         #pragma HLS INLINE
         return data (GainBitHi, GainBitLo);
      }

      // Retrieve the MBZ (must be zero)
      static Mbz_t getMbz   (Type data)
      {
         #pragma HLS INLINE
         return data (MbzBitHi, MbzBitLo);
      }
   };

   using Data_t = typename Data::Type;
};
/* --------------------------------------------------------------------- */



/* --------------------------------------------------------------------- *//*!
 *
 *   \brief Template to describe a \e Tile
 *
 *   \par
 *    A tile is made up of a number of ASICs.  Tiles may further
 *    assembled into an \e Image
 *
 *   \warning
 *    Currently only linear configurations of the ASICs are supported.
 *    Eventually will need to add richness when, for example, 4 ASICs
 *    are assembled in a square. Because the readout must be on the
 *    outer edge, 2 of the ASICs will have their tiles (rows) inverted.
 *                                                                       */
/* --------------------------------------------------------------------- */
template<size_t     NASICS,
         typename ASIC_CFG>
class TileCfg
{
   TileCfg () = delete;

public:
   using                 AsicCfg  = ASIC_CFG;
   static constexpr auto NAsics   = NASICS;
   static constexpr auto NStreams = NAsics * AsicCfg::NStreamsPerAsic;
   static constexpr auto NRows    = AsicCfg::NRows;
   static constexpr auto NCols    = AsicCfg::NColsPerAsic    * NAsics;
   static constexpr auto NPixels  = AsicCfg::NPixelsPerAsic  * NAsics;
};
/* --------------------------------------------------------------------- */


/* --------------------------------------------------------------------- *//*!
 *
 *   \brief  Template to describe the inbound data stream, effectively
 *           the data as it comes from the ASIC(s)
 *
 *   \tparam TILE_CFG  The tile configuration which includes the number
 *                     of ASICs in the tile and the configuration
 *                     of the ASICs.
 *                                                                       */
/* --------------------------------------------------------------------- */
template<typename TILE_CFG>
class IbCfg
{
public:
   IbCfg () = delete;

   using  TileCfg = TILE_CFG;
   using  AsicCfg = typename TileCfg::AsicCfg;

private:
   // Internal use only
   static constexpr auto IoStreamWidth  = TileCfg::NStreams * TileCfg::AsicCfg::Data_t::width;

public:
   // --------------------------------------------------------------------
   // StreaBus_t   = The full (nominally 192 bits) streaming word
   // StreamData   = The streamed data complete with the sideband data
   // Stream       = The HLS stream
   // --------------------------------------------------------------------
   using StreamBus_t  = ap_uint<IoStreamWidth>;
   using StreamData_t = hls::axis<StreamBus_t, 2, 1, 1>;
   using Stream       = hls::stream<StreamData_t>;


   // ----------------------------------------------------
   // Extract the ASIC data value for the specified stream
   // ----------------------------------------------------
   static typename AsicCfg::Data::Type extract (StreamBus_t streamBus, int streamIdx)
   {
      auto   high_range = (AsicCfg::DataWidth  * (streamIdx + 1) - 1); // High bit number
      auto   low_range  = (AsicCfg::DataWidth  * (streamIdx)        ); // Low  bit number
      auto   data       = streamBus.range (high_range, low_range);     // Extract the data
      return data;
   }

   using Data_t = typename AsicCfg::Data::Type;
};
/* --------------------------------------------------------------------- */


/* --------------------------------------------------------------------- *//*!
 *
 *   \brief  Template to describe the outbound data stream from the HLS
 *           firmware
 *
 *   \tparam TILE_CFG  The tile configuration which includes the number
 *                     of ASICs in the tile and the  configuration
 *                     of the ASICs
 *
 *  \par Notable Differences from the inbound tile data
 *   The differences are
 *      -# The data has been descrambled into a traditional rows, cols
 *      -# The data words may, depending on the firmware configuration
 *         register settings be dark (pedestal) subtracted and gain corrected
 *      -# The first \e dummy row may have been eliminated
 *      -# The gain bit (which is in bit 14 of the input word) will have
 *        been moved to the low bit
 *
 *   The gain bit is moved because, if the dark/pedestal have been
 *   subtracted, it awkward to have the gain bit in the upper bits where
 *   the sign bits will naturally occupy.  By moving it to the lower bit,
 *   the output data word can be treated as a simple signed 16-bit
 *   integer.  Since the absolute values has not been set, only the
 *   relative gains, the user has the option of shifting the gain bit
 *   off or leaving it as is.  While it is recommended to shift it off,
 *   because it is a 1 for the high gain, it changes the value be only
 *   a very small amount, certain applications may find it okay to just
 *   leave it
 *                                                                       */
/* --------------------------------------------------------------------- */
template<typename TILE_CFG>
class ObCfg
{
public:
   ObCfg () = delete;

   using TileCfg                   = TILE_CFG;


   // -------------------------
   // Define the ASIC data word
   // -------------------------
   class Data
   {
   public:
      Data () = delete;

      // -----------------------------------------------------
      // Layout the beginning (lo) and ending (hi) bit numbers
      // of each field in a 16-bit unsigned integer
      // -----------------------------------------------------
      static constexpr auto GainBitLo  =  0;
      static constexpr auto GainBitHi  =  0;

      static constexpr auto   AdcBitLo =  1;
      static constexpr auto   AdcBitHi = 15;

     static constexpr auto   AdcNBits =   AdcBitHi -  AdcBitLo + 1;
      static constexpr auto  GainNBits =  GainBitHi -  GainBitLo + 1;

      static_assert (AdcNBits + GainNBits == 16,
                    "\n"
                    "ERROR: AsicCfg::Data the number of bits in the word must be 16\n\n");

      using   Adc_t = ap_uint< AdcNBits>;
      using  Gain_t = ap_uint<GainNBits>;
      using    Type = ap_uint<16>;

      // Retrieve the ADC value
      static Type compose (Adc_t adc, Gain_t gain)
      {
         #pragma HLS INLINE
         Type data;
         data = (adc, gain);
         return data;
      }

      // Retrieve the ADC gain
      static Gain_t getGain  (Type data)
      {
         #pragma HLS INLINE
         return data (GainBitHi, GainBitLo);
      }
   };

   static constexpr auto IoStreamWidth  = TileCfg::NStreams * Data::Type::width;

   using StreamBus_t  = ap_uint<IoStreamWidth>;
   using StreamData_t = hls::axis<StreamBus_t, 2, 1, 1>;
   using Stream       = hls::stream<StreamData_t>;

   using Data_t       = typename Data::Type;
};
/* --------------------------------------------------------------------- */


/* --------------------------------------------------------------------- *//*!
 *
 *  \brief Defines the configuration registers
 *                                                                       */
/* --------------------------------------------------------------------- */
class ConfigRegs
{
public:
   ConfigRegs () :  m_reg (0) { return; }

   // ---------------------------------------
   // Map out the configuration register bits
   // ---------------------------------------
   static constexpr uint8_t LoadCalib      = 0; /*!< Load calibration  bit # */
   static constexpr uint8_t DarkTileSub    = 1; /*!< Dark subtraction  bit # */
   static constexpr uint8_t GainEqualize   = 2; /*!< Gain equalization bit # */

   static constexpr uint32_t LoadCalib_m    = (1 << LoadCalib   );
   static constexpr uint32_t DarkTileSub_m  = (1 << DarkTileSub );
   static constexpr uint32_t GainEqualize_m = (1 << GainEqualize);

   /* ------------------------------------------------------------------ *//*!
    *
    *  \brief Construct the configuration register
    *
    *  \param[in] darkTileSub  Boolean flag, if true do dark tile subtraction
    *  \param[in] gainEqualize Boolean flag, if true do gain equalization
    *
    *  \warning
    *   While permitted (perhaps for testing purposes) enabling the gain
    *   equalization without the dark subtraction is dubious.  Since the
    *   audience of this code is believed to be knowledgeable, this option
    *    is not forbidden. (If it was the unwashed, it would be forbidden.)
    *                                                                    */
   /* ------------------------------------------------------------------ */
   ConfigRegs (bool loadCalib, bool darkTileSub, bool gainEqualize) :
      m_reg ( (   loadCalib ?    LoadCalib_m : 0)
            | ( darkTileSub ?  DarkTileSub_m : 0)
            | (gainEqualize ? GainEqualize_m : 0))
   {
      return;
   }
   /* ------------------------------------------------------------------ */

public:
   // Enable
   bool isEnabledLoadCalib    () const { return (m_reg &    LoadCalib_m); };
   bool isEnabledDarkTileSub  () const { return (m_reg &  DarkTileSub_m); };
   bool isEnabledGainEqualize () const { return (m_reg & GainEqualize_m); };

   void setLoadCalib ()
   {
      m_reg |= LoadCalib_m;
   }

   void clearLoadCalib ()
   {
      m_reg &= ~LoadCalib_m;
   }

   // Set flag to load the calibration dark/gain values
   void setLoadCalib   (bool flag)
   {
      if (flag) m_reg |=  LoadCalib_m;
      else      m_reg &= ~LoadCalib_m;
      return;
   }

   // Enable or disable the dark subtraction
   void setDarkTileSub (bool flag)
   {
      if (flag) m_reg |=  DarkTileSub_m;
      else      m_reg &= ~DarkTileSub_m;
      return;
   }

   // Enable or disable the gain equalization
   void setGainEqualize (bool flag)
   {
      if (flag) m_reg |=  GainEqualize_m;
      else      m_reg &= ~GainEqualize_m;
      return;
   }

   // Enable or disable the dark subtraction and gain equalization
   void setDarkGain (bool darkTileSub, bool gainEqualize)
   {
      setDarkTileSub  ( darkTileSub);
      setGainEqualize (gainEqualize);
      return;
   }

private:
   uint32_t m_reg;
};
/* --------------------------------------------------------------------- */


/* --------------------------------------------------------------------- *//*!
 *
 *  \brief Defines the calibration constants, \ei.e. the dark tile
 *         subtraction and the gain equalizations as read on the
 *         input/host side.
 *                                                                       */
/* --------------------------------------------------------------------- */
template<typename TILE_CFG>
class CalibInCfg
{
public:
   CalibInCfg () { return; }

   using                 TileCfg = TILE_CFG;
   static constexpr auto NPixels = TileCfg::NPixels;

   using Dark_t = uint16_t;
   using Gain_t = uint16_t;

   ///Dark_t m_darks[NPixels];
   ///Gain_t m_gains[NPixels];

   struct Constants
   {
      Dark_t m_dark;
      Gain_t m_gain;
   };

   struct Pixel
   {
      Pixel () { return; }

      Pixel (Dark_t loDark, Gain_t loGain,
             Dark_t hiDark, Gain_t hiGain)
      {
         m_constants[0].m_dark = loDark;
         m_constants[0].m_gain = loGain;
         m_constants[1].m_dark = hiDark;
         m_constants[1].m_gain = hiGain;
         return;
      }

      Constants m_constants[2];
   };

   static Pixel compose (Dark_t loDark, Gain_t loGain,
                         Dark_t hiDark, Gain_t hiGain)
   {
      Pixel pixel;
      pixel.m_constants[0].m_dark = loDark;
      pixel.m_constants[0].m_gain = loGain;
      pixel.m_constants[1].m_dark = hiDark;
      pixel.m_constants[1].m_gain = hiGain;
      return pixel;
   }

   using StreamBus_t  = Pixel;
   using StreamData_t = hls::axis<StreamBus_t, 2, 1, 1>;
   using Stream       = hls::stream<StreamData_t>;


   static StreamData_t compose (StreamBus_t &pixel, int last)
   {
      // Create the strobe and keep masks
      static constexpr auto NBytes = sizeof (StreamBus_t);
      static constexpr auto Strobe = (1 << NBytes) - 1;
      static constexpr auto Keep   = (1 << NBytes) - 1;

      StreamData_t dst;
      dst.data   = pixel;
      dst.strb   = Strobe;
      dst.keep   = Keep;
      dst.user   = 0;
      dst.last   = last;
      dst.id     = 0;

      return dst;
   }

//public:
//  Stream m_stream;
};
/* --------------------------------------------------------------------- */


/* --------------------------------------------------------------------- *//*!
 *
 *  \brief Defines the calibration constants, \ei.e. the dark tile
 *         subtraction and the gain equalizations as used in the HLS
 *         code.
 *
 *  \tparam   TILE_CFG  The configuration of a tile
 *  \tparam DARK_NBITS  Number of bits in the dark tile subtraction word
 *  \tparam GAIN_NBITS  Number of bits in the gain word
 *  \tparam      SHIFT  Number of bits to shift the gain corrected value
 *                                                                       */
/* --------------------------------------------------------------------- */
template<typename       TILE_CFG,
         std::size_t  DARK_NBITS,
         std::size_t  GAIN_NBITS,
         std::size_t       SHIFT>
class CalibHlsCfg
{
public:
   CalibHlsCfg ()
   {
     #pragma HLS INLINE
      return;
   }

   using                     TileCfg = TILE_CFG;
   static constexpr auto   DarkNBits = DARK_NBITS;
   static constexpr auto   GainNBits = GAIN_NBITS;
   static constexpr auto       Shift = SHIFT;
   static constexpr auto     NPixels = TileCfg::NPixels;

   // --------------------------------------------------
   // Define the data types of the calibration constants
   // --------------------------------------------------
   using                    Dark_t = ap_uint<DarkNBits>;
   using                    Gain_t = ap_uint<GainNBits>;

   // ------------------------------------------------
   // The calibration parameters for 1 gain of 1 pixel
   struct Prms
   {
      Dark_t m_dark;
      Gain_t m_gain;
   };
   // ------------------------------------------------


   // -----------------------------------------------------------------------
   // Transfer the calibration constants from their
   // external to their internal representations
   // ----------------------------------------------
   template    <typename STREAM>
   void constructStream (STREAM &stream)
   {
      #pragma HLS INLINE off

      calib_construct_loop: for (int ipixel = 0; ipixel < NPixels; ++ipixel)
      {
         // -------------------------------------------------------
         // No reason for high performance in loading the constants
         // -------------------------------------------------------
         #pragma HLS UNROLL factor=1

         auto pixel = stream.read().data;

         // Lo gain
         m_prms[ipixel][0].m_dark = pixel.m_constants[0].m_dark;
         m_prms[ipixel][0].m_gain = pixel.m_constants[0].m_gain;

         // Hi gain
         m_prms[ipixel][1].m_dark = pixel.m_constants[1].m_dark;
         m_prms[ipixel][1].m_gain = pixel.m_constants[1].m_gain;
      }

      return;
   }
   // ------------------------------------------------------------------

public:
   Prms   m_prms[NPixels][2];  /*!< Storage for lo/Hi dark & gains       */
};
/* --------------------------------------------------------------------- */


// ------------------------------------------------
/// Set the number of rows to decode
/// --------------------------------
#ifdef __SYNTHESIS__

// --------------------------------------------
// Use realistic number of rows for synthesis
// to produce realistic latency/II numbers
//
// NOTE: This includes the bogus 1rst row
// --------------------------------------------
static constexpr auto NROWS = 145;

#else

// --------------------------------------------
// Use number of rows defined in the test bed
// to allow debugging and developing not to
// be swamped by tons of output.
// --------------------------------------------
static constexpr auto NROWS = 145;

#endif
/// ------------------------------------------------


using Asic = AsicCfg<6,        // Number of streams/ASIC
                     NROWS,    // Number of rows in an ASIC
                     32,       // Number of columns/stream
                     16,       // Number of bits in ASIC data
                     30>;      // Start column of data from previous row

using Tile     =  TileCfg<2, Asic>;
using Ib       =       IbCfg<Tile>;
using Ob       =       ObCfg<Tile>;
using Clb      =  CalibInCfg<Tile>;
using CalibHls = CalibHlsCfg<Tile,    // Tile configuration
                               14,    // Dark pixel bit width
                               14,    // Gain       bit widht
                                7>;   // Normalization shift

extern void AxiStreamDarkSubGainCorr  (Ib ::Stream                          &ibStream,
                                       Ob ::Stream                          &obStream,
                                       Clb::Stream                         &clbStream,
                                       ConfigRegs                         &configRegs);


#endif
