Testing tools for CoLoRe

# Installation
Create virtual environment (optional):
```shell
conda create -n <env_name> python=3.8.5
```

Install general requirements:
```shell
pip install -r requirements.txt
```

Install pymaster:
```shell
conda install -c conda-forge namaster
```

Install pyccl:
```shell
conda install -c conda-forge pyccl
```

Install package (in editable mode):
```shell
pip install -e .
```

Run full set of tests:
```shell
RUN_CCL_TESTS=Y RUN_SHEAR_TESTS=Y python -m unittest discover CoLoRe_analysis/tests/
```