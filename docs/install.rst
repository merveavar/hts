.. _install:


Installation
============


We recommend to install HTS in a `virtual environment <http://docs.python-guide.org/en/latest/dev/virtualenvs/>`_.

HTS uses `GPy <http://sheffieldml.github.io/GPy/>`_ for Gaussian process normalization. GPy itself requires numpy at setup time::

    $ pip install numpy



With pip (or pip3) configured for Python3, you can install the latest version of HTS directly from Github.::

    $ pip install git+https://github.com/elkeschaper/hts.git


GPy is under constant development, and it might be useful to deinstall the PyPi version installed by default, and instead install the `latest develop version <https://github.com/SheffieldML/GPy>`_::

     $ pip install git+https://github.com/SheffieldML/GPy.git



Now you can import hts in your Python3 project::

    import hts



For creating .html or .pdf reports with HTS, install `Pandoc (v > 1.12.3) <http://pandoc.org/installing.html>`_
and an up-to-date version of `R (v >= 3.2.4) <https://www.r-project.org/>`_.
Make sure that Rscript is accessible from the command line::

    $ which Rscript


Next, within R, install these R packages::

    install.packages("ggplot2");
    install.packages("gridExtra");
    install.packages("knitr");
    install.packages("MASS);
    install.packages("rmarkdown");



We use `Knitr <http://yihui.name/knitr/>`_ to create the reports from R snippets.










