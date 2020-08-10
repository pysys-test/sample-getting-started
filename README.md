# PySys Sample - Getting Started
[![PySys tests](../workflows/PySys%20tests/badge.svg)])(../actions)

This project shows how to use the PySys system test framework to test a sample application consisting of a REST/HTTP server. 

Explore the tests in this project to get an idea for what is possible with PySys, or fork this repo to get started wit your own project.

# Running the tests

To use this project all you need is Python 3, and the latest version of PySys. You can run all the tests like this::

	cd test
	pysys.py run

Or to run just test MyServer_001::

	pysys.py run 001

If you want to re-run just the validation part of a test (which is a big time-saver during test development)::

	pysys.py run --validateOnly 001

PySys makes it easy to reproduce race conditions in your application (or test) by cycling a test many times, and for  
speeding up test execution by running multiple test jobs/threads concurrently::

	pysys.py run --cycle 20 -j5 001

PySys includes support for GitHub actions, and you can see the results of executing this test project in the 
[Actions](../actions) tab for this repo. 

# Exploring what the tests do

Now it's time to start exploring the run.py files in each of the tests. 

The best way to find out what each test does is to print out the test titles like this::

	pysys.py print

Start with 001 test in the correctness/ directory which is a simple example to show the basics, then move on to the 
higher numbered tests to explore in more detail how to execute processes, validate results and more. 

See also the [PySys documentation](https://pysys-test.github.io/pysys-test).
