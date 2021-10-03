#pragma once
// uintN_t types for any N
#include "uintN_t.h"

// Function to test
float fp32sub(float x, float y)
{
  return x - y;
}

// Verilator device under test test bench setup
#include "../dut.h"

#ifdef __PIPELINEC__
// Define hardware debug hooks

// Generate top level debug ports
#include "debug_port.h"

// Debug ports, two inputs, one output
#include "clock_crossing/x_DEBUG.h"
DEBUG_INPUT_DECL(float, x)
#include "clock_crossing/y_DEBUG.h"
DEBUG_INPUT_DECL(float, y)
#include "clock_crossing/result_DEBUG.h"
DEBUG_OUTPUT_DECL(float, result)
// Mark as top level for synthesis
#pragma MAIN test_bench
void test_bench()
{
  // Drive result debug port 
  // with the output of doing 
  // an operation on the two input ports
  DEBUG_SET(result, fp32sub(DEBUG_GET(x), DEBUG_GET(y)));
}
#endif

// Define test params + logic using debug hooks

#define DUT_VARS_DECL \
float x;\
float y;\
float result;\
float c_result;

#define DUT_SET_NEXT_INPUTS \
if(test_num==(10-1))\
{\
  done = true; \
}\
/*Generate random input*/ \
x = rand_float();\
y = rand_float();

#define DUT_SET_INPUTS(top) \
DUT_SET_FLOAT_INPUT(top, x)\
DUT_SET_FLOAT_INPUT(top, y)

#define DUT_GET_OUTPUTS(top) \
DUT_GET_FLOAT_OUTPUT(top, result)\
c_result = fp32sub(x, y);

#define DUT_COMPARE_LOG(top) \
DUMP_PIPELINEC_DEBUG(top) \
if(fabs(c_result - result) > 1e-6)\
{\
  test_passed = false;\
}
