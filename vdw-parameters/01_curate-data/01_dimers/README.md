# Data curation

Data is from DES370k. The filtering process was as follows:

- run-filter-dimer-energies.sh (filter for molecules that can be assigned Sage 2.1 parameters)
- run-add-mapped-smiles.sh (add mapped SMILES for further use)
- run-filter-attractive.sh (filtered for neutral compounds)
- run-split-dataset.sh (split the dataset into training/validation based on functional group)

Then datasets were converted either into:

- smee (run-convert-to-smee.sh)
- or ForceBalance targets (run-convert-to-targets.sh)

