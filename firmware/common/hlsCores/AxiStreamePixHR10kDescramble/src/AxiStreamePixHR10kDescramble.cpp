//////////////////////////////////////////////////////////////////////////////
// This file is part of 'Vivado HLS Example'.
// It is subject to the license terms in the LICENSE.txt file found in the
// top-level directory of this distribution and at:
//    https://confluence.slac.stanford.edu/display/ppareg/LICENSE.html.
// No part of 'Vivado HLS Example', including this file,
// may be copied, modified, propagated, or distributed except according to
// the terms contained in the LICENSE.txt file.
//////////////////////////////////////////////////////////////////////////////

#include "AxiStreamePixHR10kDescramble.h"

#include <iostream>
using namespace std;

void AxiStreamePixHR10kDescramble(mystream &ibStream, mystream &obStream) {
   // Set the input and output ports as AXI4-Stream
   #pragma HLS INTERFACE axis port=ibStream
   #pragma HLS INTERFACE axis port=obStream

   // Don't generate ap_ctrl ports in RTL
   #pragma HLS INTERFACE ap_ctrl_none port=return



   // Exemple for 2 ePixHR10k ASICs => 2 * 32 * 6 = 384
   ap_uint<ASIC_DATA_WIDTH> input_line_buffer[NUM_ASICS * ASIC_COLUMNS_PER_STREAM * ASIC_NUM_OF_STREAMS];
   #pragma HLS ARRAY_PARTITION variable=input_line_buffer dim=1 complete
   ap_uint<ASIC_DATA_WIDTH> output_line_buffer[NUM_ASICS * ASIC_COLUMNS_PER_STREAM * ASIC_NUM_OF_STREAMS];
   #pragma HLS ARRAY_PARTITION variable=output_line_buffer dim=1 complete

   ap_uint<32> lastDataFlag=0;

   ap_uint<1> last;


   rows_loop:
   do{
       #pragma HLS DATAFLOW
	   read_frame(ibStream, input_line_buffer, lastDataFlag);

	   //#pragma HLS DATAFLOW
	   //process_line(input_line_buffer, output_line_buffer, lastDataFlag);

       #pragma HLS DATAFLOW
	   last = send_frame(input_line_buffer, lastDataFlag, obStream);


   }while(last==0);
}

void read_frame(mystream &ibStream, ap_uint<ASIC_DATA_WIDTH> linebuf[NUM_ASICS * ASIC_COLUMNS_PER_STREAM * ASIC_NUM_OF_STREAMS], ap_uint<32> &lastDataFlag){
	ap_uint<8> idx = 0, idx2 = 0;
	int high_range, low_range;
	data_t ibVar;
	ap_uint<IO_STREAM_WIDTH> temp_data;
	ap_uint<ASIC_DATA_WIDTH> temp_pix;

   input_to_buf_loop:
   	   for (idx = 0; idx < ASIC_COLUMNS_PER_STREAM; ++idx){
           auto ibVar = ibStream.read();
           temp_data = ibVar.data;
           cout << "hw lane ibVar.data=" << ibVar.data << " hw lane ibVar.strb=" << ibVar.strb << " hw lane ibVar.keep=" << ibVar.keep << ", linebuf " << linebuf[idx] <<", last " << lastDataFlag[idx] << ", " << endl;
	       //loops over the single input data and buffer it on a line buffer
	       for (idx2 = 0; idx2 < ASIC_NUM_OF_STREAMS*NUM_ASICS; ++idx2){
	    	   high_range = ((ASIC_DATA_WIDTH)*(idx2+1)-1);
		       low_range = (ASIC_DATA_WIDTH*idx2);
	    	   temp_pix = temp_data.range(high_range,low_range);
	    	   cout << "tmp data " << temp_pix << ", ";
		       linebuf[idx+(idx2*ASIC_COLUMNS_PER_STREAM)] = temp_pix;
	       }
	       cout << endl;
	       cout << "idx " << idx << "linebuff values " << linebuf[idx] << ", " << linebuf[32+idx] << ", " << linebuf[64+idx] << ", " << endl;
   	       lastDataFlag[idx]=ibVar.last;

   	   }
}

void process_line(ap_uint<ASIC_DATA_WIDTH> input_line_buffer[NUM_ASICS * ASIC_COLUMNS_PER_STREAM * ASIC_NUM_OF_STREAMS], ap_uint<ASIC_DATA_WIDTH> output_line_buffer[NUM_ASICS * ASIC_COLUMNS_PER_STREAM * ASIC_NUM_OF_STREAMS]){
	ap_uint<8> idx = 0, idx2 = 0;
	ap_uint<IO_STREAM_WIDTH> temp_data;

	buf_in_to_buf_out_loop:
	   	  for (idx = 0; idx < ASIC_COLUMNS_PER_STREAM  ; ++idx){
		      for (idx2 = 0; idx2 < ASIC_NUM_OF_STREAMS*NUM_ASICS; ++idx2){
		    	  temp_data.range(((ASIC_DATA_WIDTH)*(idx2+1)-1),ASIC_DATA_WIDTH*idx2) =  input_line_buffer[((idx*ASIC_NUM_OF_STREAMS*NUM_ASICS)+idx2)];
		       }
	   	  }
}

ap_uint<1> send_frame(ap_uint<ASIC_DATA_WIDTH> output_line_buffer[NUM_ASICS * ASIC_COLUMNS_PER_STREAM * ASIC_NUM_OF_STREAMS], ap_uint<32> &lastDataFlag, mystream &obStream){
   ap_uint<8> idx = 0, idx2 = 0;
   data_t obVar;
   ap_uint<IO_STREAM_WIDTH> temp_data;

   output_to_buf_loop:
   	  for (idx = 0; idx < ASIC_COLUMNS_PER_STREAM  ; ++idx){
	      for (idx2 = 0; idx2 < ASIC_NUM_OF_STREAMS*NUM_ASICS; ++idx2){
		temp_data.range(((ASIC_DATA_WIDTH)*(idx2+1)-1),ASIC_DATA_WIDTH*idx2) = output_line_buffer[((idx*ASIC_NUM_OF_STREAMS*NUM_ASICS)+idx2)];
	       }
           obVar.data = temp_data;
           //create error flag check and set
           //last should coincide with idx = 31
           obVar.last = lastDataFlag[idx];//flag is kept in order since only data should be mirrored
           obVar.strb = 0xFFFFFF;//ibVar.strb; //for 192 bits bus this value should always be xFFFFFF
           obVar.keep = 0xFFFFFF;//ibVar.keep;

           cout << "idx="        << idx        << ", ";
           cout << "linebuffer=" << output_line_buffer[idx] << ", ";
           cout << "obVar.data=" << obVar.data << " hw lane obVar.strb=" << obVar.strb << " hw lane obVar.keep=" << obVar.keep <<endl;

           obStream.write(obVar);
      }
   	  return obVar.last;
}
