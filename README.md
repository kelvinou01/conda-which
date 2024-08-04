# conda-which

Which package does this file belong to?



## Installation

### Using conda-forge (recommended)

1. Ensure you have conda-forge added as a channel:
   
   ```sh
   conda config --add channels conda-forge
   ```

2. Install the plugin using conda:
   
   ```sh
   conda install conda-which
   ```



### Using pip

1. Clone the repository:
   
   ```sh
   git clone https://github.com/kelvinou01/conda-which.git
   ```

2. Navigate to the repository directory:
   
   ```sh
   cd conda-which
   ```

3. With the target conda environment activated, install the plugin using `pip`:
   
   ```sh
   pip install -e .
   ```



## Usage

```sh
# Full path
conda which /path/to/project/my-env/bin/deactivate

cd /path/to/project/my-env
# Relative path
conda which bin/deactivate
# Multiple files
conda which bin/deactivate bin/ahost lib/cmake/OpenSSL/OpenSSLConfig.cmake
```
