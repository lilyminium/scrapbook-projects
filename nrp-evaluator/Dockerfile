FROM condaforge/miniforge3

SHELL ["/bin/bash", "-c"]

RUN mamba create -n evaluator -q -c conda-forge -c openeye openff-evaluator dask-kubernetes packmol openeye-toolkits

ENV PATH /opt/conda/bin:$PATH
RUN echo "source activate evaluator" > ~/.bashrc
