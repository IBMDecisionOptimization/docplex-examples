# IBM Decision Optimization CPLEX Modeling for Python (DOcplex) Samples - Technology Preview

Welcome to IBM Decision Optimization CPLEX Modeling for Python.
Licensed under the Apache License, Version 2.0.

These are the IBM Decision Optimization CPLEX for Python samples


Solving with CPLEX Optimizers locally requires that IBM ILOG CPLEX Optimization Studio V12.6.2 is installed on your machine.
Solving with the IBM Decision Optimization on Cloud service requires that you register for an account and get the API key.

## Requirements

This library requires Python  version 2.7.9 (or later), or 3.4 (or later).

* One of the following options:

  * An **IBM Decision Optimization on Cloud** Service account and API key. You can
    register for a 30-day free trial or buy a subscription
    [here](https://developer.ibm.com/docloud/try-docloud-free).

  * **IBM ILOG CPLEX Optimization Studio V12.6.2** Development or Deployment edition for solving with no engine limit or
    the Community Edition with engine limits. You can download the Community Edition
    [here](http://www-01.ibm.com/software/websphere/products/optimization/cplex-studio-community-edition).

## Install the library

```
   pip install docplex
```

## Get the source code and examples

* [Documentation](https://github.com/IBMDecisionOptimization/docplex-doc)
* [Source Code](https://github.com/IBMDecisionOptimization/docplex)

## Using the  IBM Decision Optimization on Cloud service

1. Register for a trial account.
 
    Register for the DOcloud free trial and use it free for 30 days. See 
    [Free trial](https://developer.ibm.com/docloud/try-docloud-free>).
 
2. Get your API key.
 
    With your free trial, you can generate a key to access the DOcloud API. 
    Go to the 
    [Get API key & base URL](http://developer.ibm.com/docloud/docs/api-key/) 
    page to generate the key after you register. This page also contains 
    the base URL you must use for DOcloud.
    
3. The examples rely on you specifying the api_key either in the sample
   ``.py`` file or in a resource file in your HOME directory.
   
   a. Create a ``.docplexrc`` file in your HOME directory and insert the following
      lines :
      
	      url: YOUR_DOCLOUD_URL
	      api_key: YOUR_API_KEY_HERE
            
   b. Edit each sample ``.py`` file. Look for ::
      
	    """DOcloud credentials can be specified here with url and api_key.
	    
	    Alternatively, if api_key is None, DOcloudContext.make_default_context()
	    looks for a .docplexrc file in your home directory. That file contains the
	    credential and other properties.	       
	    """
	    url = "YOUR_URL_HERE"
	    api_key = None
	    
      Edit your url and api_key.


## Using IBM ILOG CPLEX V12.6.2 on your computer

If you have IBM ILOG CPLEX Optimization Studio V12.6.2 installed, you need to add
``<cplexdir>/python/<python_version>/<platform>`` to your PYTHONPATH.

* ``<cplexdir>`` is your CPLEX installation directory.
* ``<python_version>`` is:

   * 2.7 if your python version is 2.7
   * 3.4 if your python version is 3.4

* ``<platform>`` is:

   * ``x64_win64`` if your operating system is Windows
   * ``x86-64_linux`` if your operating system is Linux

Note that if CPLEX is in the PYTHONPATH, then it overrides the DOcloud credentials and solves locally, unless you use 
``solve_cloud`` instead of standard methods.



## Dependencies

These third-party dependencies are installed with ``pip``

- [docloud](https://pypi.python.org/pypi/docloud)
- [enum34](https://pypi.python.org/pypi/enum34)
- [futures](https://pypi.python.org/pypi/futures)
- [requests](https://pypi.python.org/pypi/requests)
- [six](https://pypi.python.org/pypi/six)

## License

This library is delivered under the  Apache License Version 2.0, January 2004 (see LICENSE.txt).
