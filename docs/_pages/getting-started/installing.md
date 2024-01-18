# Installing Wavelink

**Wavelink currently supports the following [Python](https://www.python.org/downloads/) versions:**


| Version            | Status                                                                                       | Notes                                                          |
| -----------        | -------------------------------------------------------------------------------------------- | -------------------------------------------------------------- |
| **`<= 3.9`**       | :fontawesome-solid-triangle-exclamation:{ .icon-warning .pythonista-tag title="Unsupported"} | Unsupported                                                    |
| **`3.10, 3.11`**   | :fontawesome-solid-check:{ .icon-check .pythonista-tag title="Supported" }                   | Supported                                                      |
| **`3.12`**         | :fontawesome-solid-check:{ .icon-unknown .pythonista-tag title="See Notes" }                 | May require a [Custom Index](#custom-index) or build-tools     |
| **`3.13`**         | :fontawesome-solid-question:{ .icon-unknown .pythonista-tag title="Unknown" }                | Unknown                                                        |


## Virtual Environments

Wavelink recommends the use of Virtual Environments (venvs).

You can read more about [Virtual Environments here.](https://realpython.com/python-virtual-environments-a-primer/)
Below are some simple commands to help you get started with a **venv** and wavelink.

=== "Windows"

    ``` shell
    # Change into your projects root directory or open a terminal there...
    cd path/to/project

    # Create the virtual environment...
    # Replace 3.10 with the Python version you want to use...
    # You can check what Python versions you have installed with:
    # py -0
    py -3.10 -m venv venv

    # Activate your venv...
    # Everytime you want to use your venv in a new terminal you should run this command...
    # You will know your venv is activated if you see the (venv) prefix in your terminal...
    venv/Scripts/Activate

    # Install your packages...
    pip install -U wavelink

    # You can use your venv python while it's activated simply by running py
    # E.g. py main.py
    # E.g. py --version
    py main.py

    # You can deactivate your venv in this terminal with
    deactivate

    # REMEMBER!
    # You have to re-activate your venv whenever it is deactivated to use for it for you project...
    # You will know your venv is activated by looking for the (venv) prefix in your terminal
    ```


=== "Linux & MacOS"

    ``` shell
    # Change into your projects root directory or open a terminal there...
    cd path/to/project

    # Create the virtual environment...
    # Replace 3.10 with the Python version you want to use...
    python3.10 -m venv venv

    # Activate your venv...
    # Everytime you want to use your venv in a new terminal you should run this command...
    # You will know your venv is activated if you see the (venv) prefix in your terminal...
    source venv/bin/activate

    # Install your packages...
    pip install -U wavelink

    # You can use your venv python while it's activated simply by running python
    # E.g. python main.py
    # E.g. python --version
    python main.py

    # You can deactivate your venv in this terminal with
    deactivate

    # REMEMBER!
    # You have to re-activate your venv whenever it is deactivated to use for it for you project...
    # You will know your venv is activated by looking for the (venv) prefix in your terminal
    ```


## Custom Index

Using wavelink with `Python >= 3.12` may require the use of a custom pip index.

The index allows pip to fetch pre-built wheels for some dependencies that may require build-tools for C/C++ due to not having released their own wheels for recent versions of Python.

Usually with time, dependencies will eventually release wheels for new Python releases.

**To install with prebuilt wheels:**
``` shell
pip install -U wavelink --extra-index-url https://pip.pythonista.gg

```

## Installation Issues
Make sure you have the latest version of Python installed, or if you prefer, a Python version of 3.10 or greater.

If you have any other issues feel free to search for duplicates and then create a new issue on [GitHub](https://github.com/PythonistaGuild/Wavelink) with as much detail as possible. Including providing the output of pip, your OS details and Python version.

