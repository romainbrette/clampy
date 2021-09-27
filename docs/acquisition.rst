Signal acquisition
==================

Basic acquisition
-----------------

.. code:: Python

    import numpy as np

    x = np.zeros(1000)*nA
    x[300:400] = 1*nA
    V = board.acquire('V', Ic=x)

In this example, we measure the signal `V` while sending the command signal `x` on the analog output `Ic`.
Outputs are passed as keyword arguments, as Numpy arrays, while inputs to measured are passed as a list.
Thus, to record `V1` and `V2` while sending a current and a trigger signal, write:

.. code:: Python

    V1, V2 = board.acquire('V1', 'V2', Ic=x, trigger=my_digital_signal)

The method returns when acquisition is finished.
It is important to note that the board sets size limits to acquisitions.

Optionally, the signals can be written fo file at the end of acquisition:

.. code:: Python

    V1, V2 = board.acquire('V1', 'V2', Ic=x, trigger=my_digital_signal, save='data.txt.gz')

The format can be Numpy `npz`, or compressed/uncompressed text file (`.txt` or `.txt.gz`).
For text files, data signals are saved as columns and the first row is a header listing all variable names
separated by spaces. In the `npz` format, the acquisition time relative to the initialization time of the board object
is also saved as the variable `acquisition_time`, in seconds. The initialization time can be reset with
`board.reset_clock()`.

Building signals
----------------
