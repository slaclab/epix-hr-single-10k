//////////////////////////////////////////////////////////////////////////////
// This file is part of 'Vivado HLS Example'.
// It is subject to the license terms in the LICENSE.txt file found in the
// top-level directory of this distribution and at:
//    https://confluence.slac.stanford.edu/display/ppareg/LICENSE.html.
// No part of 'Vivado HLS Example', including this file,
// may be copied, modified, propagated, or distributed except according to
// the terms contained in the LICENSE.txt file.
//////////////////////////////////////////////////////////////////////////////

#include <stdio.h>
#include <stdint.h>

#include <iostream>
#include "AxiStreamDarkSubGainCorr.h"

template<typename DATA_TYPE>
static int readTile (char const            *fileName,
                     char const         *description,
                     DATA_TYPE   tile[Tile::NPixels]);

template         <typename STREAM_TYPE,
                  typename DATA_TYPE>
static int initStream     (STREAM_TYPE                 &stream,
                           DATA_TYPE const tile[Tile::NPixels],
                           bool                       verbose);

static int initRawTile    (char const                          *fileName,
                           Ib::Data_t               tile[Tile::NPixels]);

static int initCalib      (Clb::Stream                          &calibIn,
                           char const                          *darkName,
                           char const                          *gainName,
                           Clb::Pixel              pixels[Tile::NPixels]);

static int initGoldenTile (char const                          *fileName,
                           Ob::Data_t                tile[Tile::NPixels]);

static int          check (Ob::Stream &b, Ob::Stream &c);


/* --------------------------------------------------------------------- *//*!
 *
 *  \brief  Reads an tile, applies the calibration constants (pedestals
 *          and gains) and compares the HLS results to a \e golden
 *          standard.
 *
 *  \param[in] argc:  The number of command line arguments
 *  \param[in] argv:  The vector of command lint arguments
 *                                                                       */
/* --------------------------------------------------------------------- */
int main(int argc, char *argv[]) {


#define TEST_PATTERN        0

#if TEST_PATTERN
	   //test parameter set 1
	   static const char    RawTile[] = "/u1/ddoering/localGit/epix-hr-single-10k/firmware/common/hlsCores/AxiStreamDarkSubGainCorr/tb_data/raw145by384.csv";
	   static const char   DarkTile[] = "/u1/ddoering/localGit/epix-hr-single-10k/firmware/common/hlsCores/AxiStreamDarkSubGainCorr/tb_data/dark145by384.csv";
	   static const char      Gains[] = "/u1/ddoering/localGit/epix-hr-single-10k/firmware/common/hlsCores/AxiStreamDarkSubGainCorr/tb_data/gains145by384.csv";
	   static const char GoldenTile[] = "/u1/ddoering/localGit/epix-hr-single-10k/firmware/common/hlsCores/AxiStreamDarkSubGainCorr/tb_data/goldenImage145by384.csv";
#else
	   //test parameter set 2
      static const char    RawTile[] = "/u1/ddoering/localGit/epix-hr-single-10k/firmware/common/hlsCores/AxiStreamDarkSubGainCorr/tb_data/raw145by384.csv";
      static const char   DarkTile[] = "/u1/ddoering/localGit/epix-hr-single-10k/firmware/common/hlsCores/AxiStreamDarkSubGainCorr/tb_data/raw145by384.csv";
      static const char      Gains[] = "/u1/ddoering/localGit/epix-hr-single-10k/firmware/common/hlsCores/AxiStreamDarkSubGainCorr/tb_data/gains145by384.csv";
      static const char GoldenTile[] = "/u1/ddoering/localGit/epix-hr-single-10k/firmware/common/hlsCores/AxiStreamDarkSubGainCorr/tb_data/zeros145by384.csv";
#endif



   // -------------------------------------------------
   // Made these static so as to avoid potential issues
   // with too much stack usage
   // -------------------------------------------------
   static Ib::Data_t    raw_tile[Tile::NPixels];
   static Ob::Data_t golden_tile[Tile::NPixels];
   static Clb::Pixel   clbPixels[Tile::NPixels];

   Ib ::Stream  ibStream;
   Ob ::Stream  obStream;
   Ob ::Stream chkStream;
   Clb::Stream clbStream;
   Clb::Stream clbStreamRtrn;


   bool verbose = false;

   std::cout << "AxiStreamDarkSubGainCorr_test" << std::endl;

   //------------------------------------------
   // Builds tile and creates scrambled stream
   //------------------------------------------
   initCalib      (clbStream,  DarkTile, Gains, clbPixels);

   // ----------------------------------
   // Set up the configuration registers
   // ----------------------------------
   static constexpr bool   DarkTileSub = true;
   static constexpr bool  GainEqualize = true;
   static constexpr bool     LoadCalib = true;
   ConfigRegs configRegs (LoadCalib, DarkTileSub, GainEqualize);

   //-------------------------------------------------
   // Call the hardware function
   // First call just loads the calibration constants
   //------------------------------------------------
   std::cout << "Start HW process" << std::endl;
   AxiStreamDarkSubGainCorr (ibStream, obStream, clbStream, clbStreamRtrn, configRegs);
   configRegs.clearLoadCalib ();

   //------------------------------------------
   // Builds tile and creates scrambled stream
   //------------------------------------------
   initRawTile    (RawTile,    raw_tile);
   initStream     (ibStream,   raw_tile, verbose);

   initGoldenTile (GoldenTile, golden_tile);
   initStream     (chkStream,  golden_tile, verbose);

   AxiStreamDarkSubGainCorr (ibStream, obStream, clbStream, clbStreamRtrn, configRegs);

   //--------------------
   // Compare the results
   //--------------------
   auto   status = check (obStream, chkStream);
   return status;
}
/* --------------------------------------------------------------------- */


/* --------------------------------------------------------------------- *//*!
 *
 *  \brief Transfers the tile's pixels to a HLS stream
 *  \retval 0  Currently this is always returns 0
 *
 *  \tparam STREAM_TYPE  The HLS stream type
 *  \tparam   DATA_TYPE  The data type of the tile
 *
 *  \param[out]  stream  The target HLS stream
 *  \param[ in]     tile The tile to transfer
 *                                                                       */
/* --------------------------------------------------------------------- */
template <typename STREAM_TYPE, typename DATA_TYPE>
static int initStream (STREAM_TYPE                 &stream,
                       DATA_TYPE const tile[Tile::NPixels],
                       bool                         report)
{
   // --------------------------------------------------------------------
   // Current implementation demands the number of asic streams must be 12
   // --------------------------------------------------------------------
   static_assert (Tile::NStreams == 12,
                 "\n"
                 "--------------------------------------------\n"
                 "ERROR, The number of asic streams must be 12\n"
                 "--------------------------------------------\n\n");

   for(int irow=0; irow < Tile::NRows; irow++)
   {
      int rowOffset = irow*Tile::NCols;

	  for(int icol = 0; icol < Tile::NCols; icol += Tile::NStreams)
      {
         Ib::StreamData_t         tmp;
         Ib::StreamBus_t    inputData;

         //Stream is scrambled due to parallel readout
         inputData =  (tile[rowOffset + icol + 11],
                       tile[rowOffset + icol + 10],
                       tile[rowOffset + icol +  9],
                       tile[rowOffset + icol +  8],
                       tile[rowOffset + icol +  7],
                       tile[rowOffset + icol +  6],
                       tile[rowOffset + icol +  5],
                       tile[rowOffset + icol +  4],
                       tile[rowOffset + icol +  3],
                       tile[rowOffset + icol +  2],
                       tile[rowOffset + icol +  1],
                       tile[rowOffset + icol +  0]);

         if (report) std::cout << "pix value " << std::hex << inputData(63,0) << std::endl;

         tmp.data = inputData;
         tmp.last = (icol == (Asic::NColsPerStream - 1)
                  & (irow == (Asic::NRows          - 1))) ? 1 : 0;

         stream.write(tmp);
      }
   }

   return 0;
}
/* --------------------------------------------------------------------- */


/* --------------------------------------------------------------------- *//*!
 *
 *   \brief Read the tile's data from the specified file
 *
 *   \param[ in] fileName     The tile's file name
 *   \param[ in] description  A short description, \ee.g. "raw tile" of
 *                            the file being read
 *   \param[out] tile         The read tile
 *                                                                       */
/* --------------------------------------------------------------------- */
template<typename DATA_TYPE>
static int readTile (char const                   *fileName,
                     char const              *description,
                     DATA_TYPE        tile[Tile::NPixels])
{
   // Load raw data from files
   FILE *fp = fopen (fileName,"r");

   // Check if successfully opened
   if (fp == NULL)
   {
      std::cout << "ERROR: Unable to open " << description << " file: " << fileName << std::endl;
      return -1;
   }

   // Read the tile data file
   for (int i=0; i< Tile::NPixels; i++){
      uint16_t tmp_value;
      fscanf(fp, "%hu ,", &tmp_value);
      tile[i] = tmp_value;
   }

   fclose(fp);

   return 0;
}
/* --------------------------------------------------------------------- */


/* --------------------------------------------------------------------- *//*!
 *
 *   \brief Reads the raw test tiles's from the designated file
 *
 *   \param[ in] fileName  The file name of the raw tile data
 *   \param[out]     tile  The read raw tile data
 */
/* --------------------------------------------------------------------- */
static int initRawTile (char const            *fileName,
                        Ib::Data_t   tile[Tile::NPixels])
{
   auto   status = readTile (fileName, "raw tile", tile);
   return status;
}
/* --------------------------------------------------------------------- */


/* --------------------------------------------------------------------- *//*!
 *
 *  \brief Fills the stream with the calibration constants
 *
 *  \param[out]  clbStream The calibration stream to fill
 *  \param[ in]   darkName The name of the file containing the dark
 *                         tile values (essentially the pedestals)
 *  \param[ in]   gainName The name of the file containing the gains
 *  \param[out]     pixels The calibration constants as an array
 *                         rather than a stream
 *
 *  \note
 *   The \a pixels array is provided mainly for convenience and debugging.
 *                                                                       */
/* --------------------------------------------------------------------- */
static int initCalib      (Clb::Stream           &clbStream,
                           char const             *darkName,
                           char const             *gainName,
                           Clb::Pixel pixels[Tile::NPixels])
{
   // -----------------------------
   // Load dark tile data from file
   // -----------------------------
   FILE *darkFp = fopen(darkName, "r");

   // Check if successfully opened
   if (darkFp == NULL)
   {
      std::cout << "ERROR: Unable to open dark file: " << darkName << std::endl;
      return -1;
   }

   // -----------------------------
   // Load dark tile data from file
   // -----------------------------
   FILE *gainFp = fopen(gainName, "r");

   // Check if successfully opened
   if (gainFp == NULL)
   {
      std::cout << "ERROR: Unable to open gain file: " << gainName << std::endl;
      fclose (darkFp);
      return -1;
   }


   //---------------------------------------
   // Read both dark tile and gain constants
   // --------------------------------------
   for (int ipixel = 0; ipixel < Tile::NPixels; ipixel++)
   {
      uint16_t darkVal;
      uint16_t gainVal;

      fscanf (darkFp, "%hu ,", &darkVal);
      fscanf (gainFp, "%hu ,", &gainVal);

      // -----------------------------------------------------
      // !!! KLUDGE !!! Duplicate lo and hi ranges for now
      // --------------
      //
      // Construct the pixel from the lo and hi dark and gains
      // -----------------------------------------------------
      Clb::Pixel pixel (darkVal, gainVal, darkVal, gainVal);
      pixels[ipixel] = pixel;

      // -----------------------------------------
      // Write the pixel to the calibration stream
      // -----------------------------------------
      int last       = (ipixel == (Tile::NPixels - 1));
      auto dst       = Clb::compose (pixel, last);
      clbStream.write (dst);
   }

   fclose (darkFp);
   fclose (gainFp);

   return 0;
}
/* --------------------------------------------------------------------- */


/* --------------------------------------------------------------------- *//*!
 *
 *   \brief Reads the golden tile data from the designated file
 *
 *   \param[ in] fileName  The file name of the golden tile data
 *   \param[out]     tile  The read golden time data
 *                                                                       */
/* --------------------------------------------------------------------- */
static int initGoldenTile (char const           *fileName,
                           Ob::Data_t tile[Tile::NPixels])
{
   auto   status = readTile (fileName, "golden tile", tile);

   // ----------------------------
   // !!! KLUDGE !!!
   // Need to fix the golden file
   // Change sw format to hw format
   // -----------------------------
   for (int ipixel = 0; ipixel < Tile::NPixels; ipixel++)
   {
      auto      tmp = tile[ipixel];
      auto      adc = Ib::AsicCfg::Data::getAdc  (tmp);
      auto     gain = Ib::AsicCfg::Data::getGain (tmp);
      auto      val = Ob::Data::compose (adc, gain);
      tile[ipixel]  = val;
   }

   return status;
}
/* --------------------------------------------------------------------- */


/* --------------------------------------------------------------------- *//*!
 *
 *   \brief Checks the HLS HW generated tile after descrambling and
 *          applying the dark subtraction and gain correction with the
 *          golden tile (softwware) generated results.
 *   \retval  0 If successful
 *   \retval -1 If unsuccessful
 *
 *   \param[ in:out] hw  The hardware tile stream
 *   \param[    out] sw  The software tile stream
 *                                                                       */
/* --------------------------------------------------------------------- */
static int check (Ob::Stream &hw, Ob::Stream &sw)
{
   int maxErrors = 10;
   int   nErrors =  0;

   std::cout << "Start HW/SW comparison" << std::endl;

   for(int irow = 0; irow < Asic::NRows; irow++)
   {
      if (nErrors < maxErrors) std::cout << "Checking Row:" << std::setw(3) << irow << " Stream:";
      for(int icol = 0; icol < Asic::NColsPerStream; icol++)
      {
         if (nErrors < maxErrors) std::cout << std::setw(3) << icol << std::flush;

         auto tmp_hw = hw.read();
         auto tmp_sw = sw.read();

         Ob::StreamBus_t chk;

         if (irow > 0){

            if (tmp_hw.data != tmp_sw.data)
            {
               if (nErrors++ < maxErrors)
               {
                  // !!! Error !!!
                  std::cout << '\n'
                            << "hw data -> tmp_hw.data=" << std::hex << tmp_hw.data << '\n'
                            << "sw data -> tmp_sw.data=" << std::hex << tmp_sw.data << '\n'
                            << "ERROR HW and SW results mismatch"       << std::endl;
               }
            }
         }
      }
      std::cout << std::endl;
   }

   if (nErrors == 0) std::cout << "Success HW and SW results match" << std::endl;
   return nErrors;
}
/* --------------------------------------------------------------------- */
