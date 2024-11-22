//////////////////////////////////////////////////////////////////////////////
// This file is part of 'Vivado HLS Example'.
// It is subject to the license terms in the LICENSE.txt file found in the
// top-level directory of this distribution and at:
//    https://confluence.slac.stanford.edu/display/ppareg/LICENSE.html.
// No part of 'Vivado HLS Example', including this file,
// may be copied, modified, propagated, or distributed except according to
// the terms contained in the LICENSE.txt file.
//////////////////////////////////////////////////////////////////////////////

#include "AxiStreamDarkSubGainCorr.h"
#include <iostream>
#include <ap_int.h>

using namespace std;

// ----------------------------------------------------------------------------
// Set DEBUG only if not synthesisizing
// ------------------------------------
#ifndef __SYNTHESIS__
   #define DEBUG        1
#else
   #define DEBUG        0
#endif
// ----------------------------------------------------------------------------


class Debug
{
public:
   Debug () { return; }

#if DEBUG
   static void printRow (int rowIdx)
   {
      std::cout << '\n'
                <<  "row Idx " << rowIdx << '\n' << endl;
      return;
   }


   template<typename IBVAR_TYPE>
   static void print (int              colIdx,
                      IBVAR_TYPE const &ibVar)
   {
      std::cout << std::hex
                <<  "hw lane ibVar.data="  << ibVar.data
                << " hw lane ibVar.strb="  << ibVar.strb
                << " hw lane ibVar.keep="  << ibVar.keep << std::endl;
   }

   static void printTitle ()
   {
      std::cout <<
      " Stream    Adc  Hi/Lo   Dark SubAdc   Gain CorPix  Shift CorAdc\n"
      " ------ ------ ------ ------ ------ ------ ------ ------ ------" << std::endl;
   }

   static void printIn (bool     darkTileSub,
                        bool    gainEqualize,
                        int        streamIdx,
                        uint16_t         adc,
                        uint16_t    adc_gain,
                        int         dark_pix,
                        int          sub_pix,
                        int             gain,
                        int         corr_pix,
                        int            shift,
                        int          mul_pix)
   {
      std::cout << std::hex << std::setw(7) << streamIdx
                << std::hex << std::setw(7) <<       adc
                            << std::setw(7) <<  adc_gain;


      if (darkTileSub)  std::cout << std::hex          << std::setw(7) << dark_pix;
      else              std::cout << std::setfill(' ') << std::setw(7) <<      '-';


      std::cout  << std::hex << std::setw(7)<<    sub_pix;


      if (gainEqualize) std::cout << std::hex          << std::setw(7) <<     gain
                                  << std::hex          << std::setw(7) << corr_pix
                                  << std::dec          << std::setw(7) <<    shift;

      else              std::cout << std::setfill(' ') << std::setw(7) <<      '-'
                                  << std::setfill(' ') << std::setw(7) <<      '-'
                                  << std::setfill(' ') << std::setw(7) <<      '-';

      std::cout << std::hex << std::setw(7) <<   mul_pix
                << std::endl;
      return;
   }

#else
   static void printRow (int __attribute__ ((unused)) rowIdx)
   {
      return;
   }

   template<typename IBVAR_TYPE>
   static void print (int               __attribute__ ((unused)) colIdx,
                       IBVAR_TYPE const __attribute__ ((unused) )&ibVar)
   {
      return;
   }

   static void printTitle ()
   {
      return;
   }

   static void printIn (bool         __attribute__ ((unused))  darkTileSub,
                        bool         __attribute__ ((unused)) gainEqualize,
                        int          __attribute__ ((unused))    streamIdx,
                        uint16_t     __attribute__ ((unused))          adc,
                        uint16_t     __attribute__ ((unused))     adc_gain,
                        int          __attribute__ ((unused))     dark_pix,
                        int          __attribute__ ((unused))      sub_pix,
                        int          __attribute__ ((unused))         gain,
                        int          __attribute__ ((unused))     corr_pix,
                        int          __attribute__ ((unused))        shift,
                        int          __attribute__ ((unused))      mul_pix)
   {
      return;
   }
#endif

};

static Debug Dbg;

// --------------------------
// Get the data type of a - b
// --------------------------
template<typename TA, typename TB>
using Sub_t = decltype(TA(0) - TB(0));

// --------------------------
// Get the data type of a * b
// --------------------------
template<typename TA, typename TB>
using Mul_t = decltype(TA(0) * TB(0));

// -------------------------------------------------------------------------
// Local declarations
// ------------------
static void process_row (Ib::Stream            &ibStream,
                         Ob::Stream            &obStream,
                         ConfigRegs          &configRegs,
                         CalibHls        const &calibHls,
			 int                      rowIdx);
// -------------------------------------------------------------------------



/* ------------------------------------------------------------------------ *//*!
 *
 *   \brief  If requested in the \a configRegs, applies a dark pixel
 *           subtraction and a gain correction.
 *
 *   \param[ in]   ibStream  The in bound stream holding the row pixels
 *   \param[out]   obStream  The out bound stream to write the potentially
 *                           calibrated pixels to
 *   \param[ in]  clbStream  If enabled in the \a configRegs, the stream
 *                           holding the calibration constants.
 *   \param[ in] configRegs  The configuration registers. This holds
 *                           the dark subtraction and gain enable flags
 *
 *  \note
 *   Even if the application of the calibration constants is disabled, the
 *   format of the outbound data word is altered.  This is because the
 *   input word is a 14-bit ADC, which, if the dark pixel is subtracted
 *   now occupies a 15-bit signed word.  To make this easier to decode, the
 *   gain bit is placed in the LSB, with the corrected ADC value occupying
 *   the 15 MSBs.
 *                                                                          */
/* ------------------------------------------------------------------------ */
void AxiStreamDarkSubGainCorr   (Ib ::Stream   &ibStream,
                                 Ob ::Stream   &obStream,
                                 Clb::Stream  &clbStream,
                                 Clb::Stream  &clbStreamRtrn,
                                 ConfigRegs  &configRegs)
{
   // Set the input and output ports as AXI4-Stream
   #pragma HLS INTERFACE      axis port= ibStream
   #pragma HLS INTERFACE      axis port= obStream
   #pragma HLS INTERFACE      axis port=clbStream
   #pragma HLS INTERFACE      axis port=clbStreamRtrn
   #pragma HLS INTERFACE s_axilite port=configRegs  bundle=crtl

   // --------------------------------------------------------------------
   // Static storage for the calibration constants as used in this module
   // Contrast this with the calibration constants as they are streamed in
   // To get performance, these calibration constants most be partitioned
   // which one cannot do.
   //
   // NOTE: HLS Quirk
   // ---------------
   // The calibration constants are only unrolled by half as much as one
   // might expect for maximal performance.  This is because HLS will
   // implement this as simple dual port memory, giving the 'missing'
   // factor of 2. Now, here is the strange thing, if the pragma to
   // specify to use a RAM2SP is added, the result is not only different
   // but much worse.
   // --------------------------------------------------------------------
   static CalibHls                      calibHls;
   #pragma HLS ARRAY_PARTITION variable=calibHls.m_prms factor=Tile::NStreams/2 type=cyclic dim=1

   bool clbStream_empty, ibStream_empty;

   clbStream_empty = clbStream.empty();
   ibStream_empty = ibStream.empty();

   bool loadCalib = configRegs.isEnabledLoadCalib ();
   if  (loadCalib)
   {
	   if (!clbStream_empty)
	   {
		   calibHls.constructStreamfb (clbStream, clbStreamRtrn);
	   }
   }

   // ---------------------------------------------------------------------
   // Loop over the incoming rows, potentially calibrating each pixel's ADC
   // ---------------------------------------------------------------------

   if (!ibStream_empty)
   {
	   rows_loop: for (int rowIdx = 0; rowIdx < Asic::NRows; rowIdx++)
   	   {
		   Dbg.printRow (rowIdx);
		   process_row (ibStream, obStream, configRegs, calibHls, rowIdx);
   	   }
   }

   return;
}
/* ------------------------------------------------------------------------ */



/* ------------------------------------------------------------------------ *//*!
 *
 *   \brief Processes on row of pixels by applying a dark/pedestal
 *          subtraction and gain correction if enabled in the configRegs
 *
 *   \param[ in]   ibStream  The in bound stream holding the row pixels
 *   \param[out]   obStream  The out bound stream to write the potentially
 *                           calibrated pixels to
 *   \param[ in] configRegs  The configuration registers. This holds
 *                           the dark subtraction and gain enable flags
 *   \param[ in]      calib  The calibration constants, \e i.e. the dark
 *                           pixel and gain correction, one pair (for
 *                           high and low gain) for each pixel
 *
 *                                                                          */
/* ------------------------------------------------------------------------ */
void process_row (Ib::Stream      &ibStream,
                  Ob::Stream      &obStream,
                  ConfigRegs    &configRegs,
                  CalibHls const     &calib,
				  int                rowIdx)
{
   #pragma HLS INLINE

   int           temp_pix;
   Ob::StreamData_t obVar;
   int  pixIdx    = rowIdx*Tile::NCols;

   bool enableDarkTileSub  = configRegs.isEnabledDarkTileSub  ();
   bool enableGainEqualize = configRegs.isEnabledGainEqualize ();
   
   col_loop: for (int colIdx = 0; colIdx < Asic::NColsPerStream; ++colIdx)
   {
      #pragma HLS UNROLL   factor=1
      #pragma HLS PIPELINE     II=1

      auto ibVar     = ibStream.read();
      auto temp_data = ibVar.data;


      Dbg.print (colIdx, ibVar);
      Dbg.printTitle ();

      // -------------------------------------------------------
      // Loops over the streams where each the single input data
      // is the data for the current colIdx
      // -------------------------------------------------------
      //stream_loop: for (int streamIdx = (Tile::NStreams-1); streamIdx >= 0 ; --streamIdx, ++pixIdx)
      stream_loop: for (int streamIdx = 0; streamIdx < Tile::NStreams ; ++streamIdx, ++pixIdx)
      {
         // -------------------------------------------------
         // Extract the pixel from the streamed data word and
         // get the ADC value and gain.
         // -------------------------------------------------
         auto temp_pix   = Ib::extract (temp_data, streamIdx);
         auto adc        = Ib::AsicCfg::Data::getAdc  (temp_pix);
         auto adc_gain   = Ib::AsicCfg::Data::getGain (temp_pix);

         // --------------------------------------------------
         // The calibration constants are in sequential order,
         // so a simple incrementing index is sufficient.
         // --------------------------------------------------
         auto const prms = calib.m_prms[pixIdx][adc_gain];
         auto dark_pix   = prms.m_dark;
         auto gain       = prms.m_gain;

         // -------------------------------------------------------
         // Define the data types and variables for the calculation
         // -------------------------------------------------------
         Sub_t<decltype(     adc), CalibHls::Dark_t>  sub_pix;
         Mul_t<decltype( sub_pix), CalibHls::Gain_t> corr_pix;
         Ob::Data::Adc_t                              mul_pix;

         // --------------------------------------
         // If enabled, apply the dark subtraction
         // --------------------------------------
         if (enableDarkTileSub) sub_pix = adc - dark_pix;
         else                   sub_pix = adc;

         // --------------------------------------
         // If enable, apply the gain equalization
         if (enableGainEqualize){
            corr_pix =  sub_pix  * gain;
            mul_pix  = corr_pix >> calib.Shift;
         } else {
            mul_pix  = sub_pix;
         }
         // --------------------------------------

         
         Dbg.printIn (enableDarkTileSub,
                      enableGainEqualize,
                      streamIdx,            adc, adc_gain,
                      dark_pix,         sub_pix,     gain,
                      corr_pix, CalibHls::Shift, mul_pix);

         // --------------------------------------
         // Compose the outbound data word and
         // and commit to theoutbound data stream
         // --------------------------------------
         auto obData = Ob::Data::compose (mul_pix, adc_gain);
         obVar.data.range((Asic::Data_t::width * (streamIdx+1)-1),
                          (Asic::Data_t::width * (streamIdx  )  )) = obData;
      }

      obVar.last = ibVar.last;
      obVar.keep = ibVar.keep;
      obVar.strb = ibVar.strb;
      obVar.user = ibVar.user;
      obVar.id   = ibVar.id;
      obVar.dest = ibVar.dest;
      obStream.write(obVar);
   }

   return;
}
/* ------------------------------------------------------------------------ */
