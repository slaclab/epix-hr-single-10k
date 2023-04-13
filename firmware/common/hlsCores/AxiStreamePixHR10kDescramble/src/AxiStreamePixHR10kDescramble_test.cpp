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
using namespace std;

#include "AxiStreamePixHR10kDescramble.h"

int main() {
   int i;
   ap_uint<IO_STREAM_WIDTH> inputData;
   ap_uint<ASIC_DATA_WIDTH> inputPix;

   mystream A, B, C;

   cout << "AxiStreamePixHR10kDescramble_test" << endl;

  // Put data into A Stream
  for(i=0; i < SIZE; i++){
      data_t tmp;
      inputPix = i;
      cout << "pix value " << hex << inputPix << ",";
      inputData =  (inputPix,inputPix,inputPix,inputPix,inputPix,inputPix,inputPix,inputPix,inputPix,inputPix,inputPix,inputPix);
      cout << "pix value " << hex << inputData(63,0) << endl;
      tmp.data = inputData;
      tmp.last = (i == (SIZE - 1)) ? 1 : 0;
      A.write(tmp);
  }

  cout << "Start HW process" << endl;
  // Call the hardware function
  AxiStreamePixHR10kDescramble(A, B);



  // Run a software version of the hardware function to validate results
  ap_uint<ASIC_DATA_WIDTH> linebuf[NUM_ASICS * ASIC_COLUMNS_PER_STREAM * ASIC_NUM_OF_STREAMS];
  for(i=0; i < NUM_ASICS * ASIC_COLUMNS_PER_STREAM * ASIC_NUM_OF_STREAMS; i++){
	  linebuf[i]=i%32;
  }
  for(i=0; i < ASIC_COLUMNS_PER_STREAM; i++){
      data_t tmp_c;
      inputPix=0;
      tmp_c.data = (linebuf[11+i*12],linebuf[10+i*12],linebuf[9+i*12],linebuf[8+i*12],linebuf[7+i*12],linebuf[6+i*12],linebuf[5+i*12],linebuf[4+i*12],linebuf[3+i*12],linebuf[2+i*12],linebuf[1+i*12],linebuf[i*12]);
      cout << "i="          << i          << ", ";
      cout << "tmp_c.data=" << tmp_c.data << endl;
      C.write(tmp_c);
  }

  cout << "Start HW/SW comparison" << endl;
   // Compare the results
   for(i=0; i < SIZE; i++){
      data_t tmp_b = B.read();
      data_t tmp_c = C.read();
      if (tmp_b.data != tmp_c.data){
         cout << "i="          << i          << ", ";
         cout << "hw data -> tmp_b.data=" << tmp_b.data << ", ";
         cout << "sw data -> tmp_c.data=" << tmp_c.data << endl;
         cout << "ERROR HW and SW results mismatch" << endl;
         return 1;
      }
   }
   cout << "Success HW and SW results match" << endl;
   return 0;
}
