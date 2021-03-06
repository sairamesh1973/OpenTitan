# Copyright lowRISC contributors.
# Licensed under the Apache License, Version 2.0, see LICENSE for details.
# SPDX-License-Identifier: Apache-2.0

# List of self-checking test applications, which return PASS or FAIL after
# completion.
#
# Each list entry is a dict with the following keys:
#
# name:
#   Name of the test (required)
# signing_key:
#   Name of the key used to sign the binary (required)
# verilator_extra_args:
#   A list of additional command-line arguments passed to the Verilator
#   simulation (optional).
# targets:
#   List of targets for which the test is executed. The test will be executed
#   on all targets if not given (optional).
TEST_SILICON_CREATOR_APPS_SELFCHECKING = [
    {
        "name": "uart_smoketest",
        "signing_key": "fpga_key_1",
    },
]
