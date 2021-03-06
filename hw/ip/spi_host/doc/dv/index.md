---
title: "SPI_HOST DV Document"
---

## Goals
* **DV**
  * Verify all SPI_HOST IP features by running dynamic simulations with a SV/UVM based testbench
  * Develop and run tests that exercise all testpoints in the [testplan](#testplan) below towards closing code and functional coverage on the IP and all of its sub-modules
* **FPV**
  * Verify TileLink device protocol compliance with an SVA based testbench

## Current status
* [Design & verification stage]({{< relref "hw" >}})
  * [HW development stages]({{< relref "doc/project/development_stages" >}})
* [Simulation results](https://reports.opentitan.org/hw/ip/spi_host/dv/latest/results.html)

## Design features
For detailed information on SPI_HOST design features, please see the
[SPI_HOST HWIP technical specification]({{< relref "hw/ip/spi_host/doc" >}}).

## Testbench architecture
SPI_HOST testbench has been constructed based on the
[CIP testbench architecture]({{< relref "hw/dv/sv/cip_lib/doc" >}}).

### Block diagram
![Block diagram](tb.svg)

### Top level testbench
Top level testbench is located at `hw/ip/spi_host/dv/tb/tb.sv`. It instantiates the SPI_HOST DUT module `hw/ip/spi_host/rtl/spi_host.sv`.
In addition, it instantiates the following interfaces, connects them to the DUT and sets their handle into `uvm_config_db`:
* [Clock and reset interface]({{< relref "hw/dv/sv/common_ifs" >}})
* [TileLink host interface]({{< relref "hw/dv/sv/tl_agent/README.md" >}})
* SPI_HOST IOs
* Interrupts ([`pins_if`]({{< relref "hw/dv/sv/common_ifs" >}}))
* Alerts ([`pins_if`]({{< relref "hw/dv/sv/common_ifs" >}}))
* Devmode ([`pins_if`]({{< relref "hw/dv/sv/common_ifs" >}}))

### Common DV utility components
The following utilities provide generic helper tasks and functions to perform activities that are common across the project:
* [common_ifs]({{< relref "hw/dv/sv/common_ifs" >}})
* [dv_utils_pkg]({{< relref "hw/dv/sv/dv_utils/README.md" >}})
* [csr_utils_pkg]({{< relref "hw/dv/sv/csr_utils/README.md" >}})

### Compile-time configurations
[list compile time configurations, if any and what are they used for]
```systemverilog
TODO
```

### Global types & methods
All common types and methods defined at the package level can be found in
`spi_host_env_pkg`. Some of them in use are:
```systemverilog
TODO
```
### TL_agent
SPI_HOST testbench instantiates (already handled in CIP base env)
[tl_agent]({{< relref "hw/dv/sv/tl_agent/README.md" >}})
which provides the ability to drive and independently monitor random traffic via TL host interface into SPI_HOST device.
Transactions will be sampled by the monitor and passed on to the predictor in the scoreboard.

###  SPI Agent
SPI agent is configured to work in target mode.
The agent monitor samples the pins and stores the data in a sequence item that is forwarded to the predictor in the scoreboard.
The sequence item is then compared to a sequence item from the predictor generated on the stimulus from the TL_UL accesses.

### UVM RAL Model
The SPI_HOST RAL model is created with the [`ralgen`]({{< relref "hw/dv/tools/ralgen/README.md" >}}) FuseSoC generator script automatically when the simulation is at the build stage.

It can be created manually by invoking [`regtool`]({{< relref "util/reggen/README.md" >}}):

### Stimulus strategy
#### Test sequences
All test sequences reside in `hw/ip/spi_host/dv/env/seq_lib`.
The `spi_host_base_vseq` virtual sequence is extended from `cip_base_vseq` and serves as a starting point.
All test sequences are extended from `spi_host_base_vseq`.
It provides commonly used handles, variables, functions and tasks that the test sequences can simple use / call.
Some of the most commonly used tasks / functions are as follows:
* spi_read(int len, bit [3:0] addr)

  read ***len*** bytes from address ***addr***

* spi_write(int len, bit [3:0] addr)

  write ***len*** bytes to address ***addr***

#### Functional coverage
To ensure high quality constrained random stimulus, it is necessary to develop a functional coverage model.
the list of functional coverpoints can be found under covergroups in the [testplan](#testplan)


### Self-checking strategy
#### Scoreboard
The `spi_host_scoreboard` is primarily used for end to end checking.
It creates the following analysis ports to retrieve the data monitored by corresponding interface agents:

**TL_UL AGENT**

* tl_a_chan_fifo: tl address channel
* tl_d_chan_fifo: tl data channel

**SPI_AGENT**

* spi_channel: TBD - subject to change until env is in place

The tl_ul FIFOs provide the transaction items that will be converted to SPI transactions in the DUT.
A predictor in the DUT will collect these transactions and convert them into SPI items with an address and data.

On the SPI channel transactions are received in segments.
These segments are re-assembled into full SPI transactions and stored in SPI sequence items.

The generated item from the predictor and the re-assembled item from the SPI channel is then compared in the scoreboard to validate then transaction.

#### Assertions
* TLUL assertions: The `tb/spi_host_bind.sv` binds the `tlul_assert` [assertions]({{< relref "hw/ip/tlul/doc/TlulProtocolChecker.md" >}}) to the IP to ensure TileLink interface protocol compliance.
* Unknown checks on DUT outputs: The RTL has assertions to ensure all outputs are initialized to known values after coming out of reset.


## Building and running tests
We are using our in-house developed [regression tool]({{< relref "hw/dv/tools/README.md" >}}) for building and running our tests and regressions.
Please take a look at the link for detailed information on the usage, capabilities, features and known issues.
Here's how to run a smoke test:
```console
$ $REPO_TOP/util/dvsim/dvsim.py $REPO_TOP/hw/ip/spi_host/dv/spi_host_sim_cfg.hjson -i spi_host_smoke
```

## Testplan
{{< incGenFromIpDesc "../../data/spi_host_testplan.hjson" "testplan">}}
