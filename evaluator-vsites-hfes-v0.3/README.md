# VSite HFEs with Yank (Evaluator v0.3)

Experimenting with running HFEs with evaluator and yank.

- a test of a molecule with OPC and OPC3 executes successfully in 8 hours or so

Note -- to run evaluator with 4-site water, you'll need the `add-vsite-sfes` branch of [my fork](https://github.com/lilyminium/openff-evaluator).

You'll also need to install my branch of [mdtraj](https://github.com/lilyminium/mdtraj/tree/v1.9.8-fix-integer).

Note that you'll need "cython <3" to install mdtraj, and moreover for some reason `pip install` will fail. Instead, cloning the repo and running `python setup.py install` will install mdtraj.

Prior to installing the special mdtraj and openff-evaluator versions, ensure they are not currently installed with:

```
pip uninstall openff-evaluator
pip uninstall openff-evaluator-base
pip uninstall mdtraj
```


## Manifest

- `evaluate-property.py` evaluates a single property
- `filtered_dataset_sfe_np1.json` is a test dataset taken from https://github.com/barmoral/evaluator-SFEs/tree/main
- `force-field.json` are Evaluator force field sources also taken from https://github.com/barmoral/evaluator-SFEs/tree/main
- `run-evaluate-property.sh` shows how I executed `evaluate-property.py` on a cluster
- `*.out` are output files

