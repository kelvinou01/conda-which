# conda-which

Which package does this file belong to?

```bash
➜ conda activate my-env
(my-env) ➜ cd /path/to/my-env/bin
(my-env) ➜ conda which ./zstd
File '/path/to/my-env/bin/zstd' belongs to
  📦 Package: zstd-1.5.6-hb46c0d2_0
  🌏 Environment: /path/to/my-env
```

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

```bash
# Full path
conda which /path/to/my-env/bin/zstd

cd /path/to/my-env
# Relative path
conda which bin/zstd
# Multiple files
conda which bin/zstd bin/ahost lib/cmake/OpenSSL/OpenSSLConfig.cmake
```

# Local development

### Test changes

```bash
conda activate dev-env
pip install -e .
conda which /path/to/file  # Changes to conda-which will immediately show up
```

### Run tests with a conda environment

```bash
conda env create -f tests/environment.yml
conda activate test
pytest tests/test.py
```

### Run actions in a docker container with [act](https://github.com/nektos/act)

```bash
act -j 'test' --container-architecture linux/amd64 -vv
```
