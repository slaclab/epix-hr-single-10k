//////////////////////////////////////////////////////////////////////////////
// This file is part of 'Vivado HLS Example'.
// It is subject to the license terms in the LICENSE.txt file found in the
// top-level directory of this distribution and at:
//    https://confluence.slac.stanford.edu/display/ppareg/LICENSE.html.
// No part of 'Vivado HLS Example', including this file,
// may be copied, modified, propagated, or distributed except according to
// the terms contained in the LICENSE.txt file.
//////////////////////////////////////////////////////////////////////////////

#ifndef _AXI_STREAM_EPIXHR10K_DESCRAMPLE_H_
#define _AXI_STREAM_EPIXHR10K_DESCRAMPLE_H_

#include <stdio.h>

#include "ap_axi_sdata.h"
#include "hls_stream.h"

#define SIZE 32
#define NUM_ASICS 2
#define ASIC_NUM_OF_STREAMS 6
#define ASIC_DATA_WIDTH 16
#define ASIC_COLUMNS_PER_STREAM 32
#define IO_STREAM_WIDTH NUM_ASICS * ASIC_NUM_OF_STREAMS * ASIC_DATA_WIDTH
// hls::axis<ap_int<WData>, WUser, WId, WDest>
typedef ap_axis<IO_STREAM_WIDTH,2,1,1> data_t;

typedef hls::stream<data_t> mystream;

extern void AxiStreamePixHR10kDescramble(mystream &ibStream, mystream &obStream);

#endif