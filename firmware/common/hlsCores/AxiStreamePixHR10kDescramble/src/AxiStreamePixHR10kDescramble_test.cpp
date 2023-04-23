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
   int i,row;
   ap_uint<IO_STREAM_WIDTH> inputData;
   ap_uint<ASIC_DATA_WIDTH> inputPix;

   mystream A, B, C;

   cout << "AxiStreamePixHR10kDescramble_test" << endl;

  //-----------------------------------------------
  // builds image and creates scrambled stream
  //-----------------------------------------------
  for(row=0; row < ASIC_ROWS; row++){
	  for(i=0; i < ASIC_COLUMNS_PER_STREAM; i++){
		  data_t tmp;
		  if (i < ROW_SHIFT_START_COLUMN){
			  //pixels is LSB row, MSB bank column
			  inputPix = (row*256)+i;
		  }else{
			  //pixels is LSB row, MSB bank column
			  inputPix = ((row+1)*256)+i;
		  }
		  cout << "pix value " << hex << inputPix << ",";
		  //Stream is scrambled due to parallel readout
		  inputData =  (inputPix,inputPix,inputPix,inputPix,inputPix,inputPix,inputPix,inputPix,inputPix,inputPix,inputPix,inputPix);
		  cout << "pix value " << hex << inputData(63,0) << endl;
		  tmp.data = inputData;
		  tmp.last = (i == (ASIC_COLUMNS_PER_STREAM - 1)&(row==(ASIC_ROWS-1))) ? 1 : 0;
		  A.write(tmp);
	  }
  }

  cout << "Start HW process" << endl;

  //-----------------------------------------------
  // Call the hardware function
  //-----------------------------------------------
  AxiStreamePixHR10kDescramble(A, B);



  //-----------------------------------------------
  // Run a software version of the hardware
  // function to validate results
  // Creates image with proper sequence
  //-----------------------------------------------
  ap_uint<ASIC_DATA_WIDTH> linebuf[NUM_ASICS * ASIC_COLUMNS_PER_STREAM * ASIC_NUM_OF_STREAMS * ASIC_ROWS];
  for(row=0; row < ASIC_ROWS; row++){
	  for(i=0; i < NUM_ASICS * ASIC_COLUMNS_PER_STREAM * ASIC_NUM_OF_STREAMS; i++){
		  linebuf[(row*NUM_ASICS * ASIC_COLUMNS_PER_STREAM * ASIC_NUM_OF_STREAMS)+i]=(row*256+(i%ASIC_COLUMNS_PER_STREAM));
	  }
  }

  // creates a stream that sends data out
  // stream bus is 12x16 pixels wide for this core
  for(i=0; i < ASIC_COLUMNS_PER_STREAM*ASIC_ROWS; i++){
      data_t tmp_c;
      inputPix=0;
      tmp_c.data = (linebuf[11+i*12],linebuf[10+i*12],linebuf[9+i*12],linebuf[8+i*12],linebuf[7+i*12],linebuf[6+i*12],linebuf[5+i*12],linebuf[4+i*12],linebuf[3+i*12],linebuf[2+i*12],linebuf[1+i*12],linebuf[i*12]);
      cout << "i="          << i          << ", ";
      cout << "tmp_c.data=" << tmp_c.data << endl;
      C.write(tmp_c);
  }

  //-----------------------------------------------
  // Compare the results
  //-----------------------------------------------
  cout << "Start HW/SW comparison" << endl;

  //for(i=0; i < ASIC_COLUMNS_PER_STREAM*ASIC_ROWS; i++){
  for(row=0; row < ASIC_ROWS; row++){
	  for(i=0; i < ASIC_COLUMNS_PER_STREAM; i++){
		  data_t tmp_b = B.read();
		  data_t tmp_c = C.read();
		  if (row>0){
			  if (tmp_b.data != tmp_c.data){
				 cout << "i="          << i          << ", ";
				 cout << "hw data -> tmp_b.data=" << tmp_b.data << ", ";
				 cout << "sw data -> tmp_c.data=" << tmp_c.data << endl;
				 cout << "ERROR HW and SW results mismatch" << endl;
				 return 1;
			  }
		  }
	  }
  }
  cout << "Success HW and SW results match" << endl;
  return 0;
}
