# PRETSA BINARY: Privacy-Preserving Event Log Sanitization Improvement

## Overview

### Introduction

PRETSA BINARY (Privacy-Enforcing Transformation for Secure Anonymization) is an optimized version of the original PRETSA framework [1]. The motivation behind the original method is that event logs contain sensitive timestamps and case durations, which can lead to re-identification risks even when no employee data is left in the data.

The original PRETSA framework builds a tree based on an event log, where each node corresponds to an activity. Each node contains key node-specific data structures:

- **self.cases**: A set containing all caseIds associated with that node.
- **self.annotation**: A dictionary mapping each caseId in the node to its corresponding activity duration.
- **self.sequences**: A set containing all possible sequences at the node level.

Additionally, the following attributes exist at the tree level (global scope across all nodes):

- **self.__annotationDataOverAll**: A mapping of all activities to their durations for all caseIds in the tree.
- **self._caseToSequenceDict**: A mapping that tracks a caseId’s sequence up to the activity represented by a node.

This distinction is important because node-level attributes store localized information about specific activities in the tree, while tree-level attributes provide a global view of activity durations and sequence mappings across all nodes.

### Problems: Original PRETSA Implementation

The original PRETSA method makes the check for the **k-anonymity** and **t-closeness** violations for a node in the same `if` statement within the `_treePrunning(self, k,t)` function. As a result, both violations are fixed using the same method, which is removing the violating node and then transferring these caseIds along with the original activity duration into another treePath sequence that closely matches its sequence.

The closeness between two paths is assessed using a **Levenshtein distance** calculation between the sequence strings stored at the node level. The sequence with the minimal distance is selected, and the cut-out caseIDs with the original activity duration are merged into the nodes for the activities in the selected sequence. 

The problem with this approach is that while it is an efficient way to deal with **k-anonymity**, the **t-closeness** is not really ensured since the decision is solely made on similarity of the strings, but distribution changes are not taken into account.

The original repository [2] was outdated, relying on deprecated Python functions. Additionally, the organization of logs and files was not optimal, as all newly generated durations and method logs were stored in the same directory as the code, making file management inefficient. Furthermore, the repository did not provide a secure method for users to directly load their own dataset or configure key parameters such as **k** or **t** values. While the repository included some error logging and statistics generation modules, the resulting logs did not correctly assess the difference in durations from the non-sanitized vs sanitized events. Additionally, code to generate appropriate graphs was not provided.

### Solutions: PRETSA BINARY

The PRETSA BINARY implementation attempts to ensure compliance with **t-closeness threshold** [3] and maximize data utility by reassigning activity durations statistically close to the original distribution by performing a **binary search** in a preordering of the tree built by PRETSA.

The new sanitization approach operates in two stages:

1. **K-Anonymity Enforcement**: Removing traces that do not meet the **k-anonymity** threshold and re-adding them to maximize data utility using the original approach.
2. **T-Closeness Correction**: Adjusting sensitive attributes (activity durations) while minimizing distortion.

This implementation introduces two new security-related features that significantly improve the privacy-preserving process:

1. **A Binary Search-Based Approach for T-Closeness Correction after K-Anonymity enforcement.**
2. **A complete pipeline from raw dataset to visualization.** Enabling the user to input their own dataset and parameters, resulting in a **Heatmap-Based Visualization** for optimal **k** and **t** parameter selection for both models.

## Installation

To run this implementation, install the required dependencies:

```sh
pip install -r requirements.txt
```

### Requirements:

```txt
anytree==2.4.3
numpy>=1.18.1
scipy>=1.4.1
pandas>=0.23.4
matplotlib>=3.1.0
seaborn>=0.10.0
pm4py
```

## Security Features: Details

### 1. T-Closeness Fix Using Binary Search

**Modules:**
- `startExperimentsForJournalExtension_PRETSA_BINARY.py`
- `runExperimentForJournalExtension_pretsa_BINARY.py`
- `runPretsa_BINARY.py`
- `pretsa_binary.py`

**Workflow:**

When `runPretsa_BINARY(k, t, normalTCloseness=True)` is executed, it follows this sequence of function calls:

1. **Fixing k-Anonymity**
   - Calls `_treePrunning(k, t)` to remove nodes with fewer than **k** cases.
   - If nodes are removed, calls `_cutCasesOutOfTreeStartingFromNode(node, cutOutTraces)` to ensure affected nodes are fully removed.
   - Reassigns removed cases to the closest valid sequence using `__combineTracesAndTree(cutOutCases).`
   - Repeats pruning and reassignment until all nodes satisfy **k-anonymity**.

2. **Fixing t-Closeness**
   - Iterates over the tree and calls `_violatesTCloseness(activity, annotations, t, cases)` for each node.
   - If a node violates **t-closeness**, calls `_binary_search_adjust(node, t_threshold=t)` to modify durations while minimizing changes.
   - Logs adjustments and saves them using `_save_tcloseness_logs_json()`, storing logs in `/content/PRETSA/t-closeness/`.

3. **Generating the Final Event Log**
   - Calls `getPrivatisedEventLog()` to reconstruct the modified event log from the adjusted tree.

### 2. User-Optimal Framework

**Modules:**
- `dataset_collection.py`
- `calculateDurationDifferences.py`
- `mapDurationDifferences.py`

This implementation enables direct download of data files with `dataset_collection.py`, allowing users to use any available dataset online or their own datasets. Users can pass a list of **k** and **t** values to each sanitization method to assess security-related design choices to sanitize their own event logs.

It also introduces **heatmaps** to visualize the impact of different **k** and **t** values, helping users find an optimal balance between privacy and data utility.

## Results

- Identifies an optimal **k-value**, ensuring sufficient privacy without excessive data loss.
- Helps select a suitable **t-value** that keeps durations close to their original distribution.
- Securely stores logs and final sanitized event logs in their respective directories:
  - `/content/PRETSA/pretsa_binarylog` for **PRETSA BINARY**.
  - `/content/PRETSA/pretsalog` for **Original PRETSA**.

## Conclusion

Full workflow to use **PRETSA BINARY** can be found in `notebook.ipynb`. The graphs and tests were generated using online datasets **Sepsis** [4] and **CoSeLoG** [5] as in the original paper.

This implementation enhances PRETSA by introducing:

1. **A Binary Search-Based Fix for T-Closeness** – Ensuring activity durations are optimally adjusted without excessive modifications.
2. **Heatmap-Based Visualization** – Allowing users to choose the best privacy parameters before running the anonymization process.

## References

[1]. S. A. Fahrenkrog-Petersen, H. van der Aa and M. Weidlich, "PRETSA: Event Log Sanitization for Privacy-aware Process Discovery," 2019 International Conference on Process Mining (ICPM), Aachen, Germany, 2019, pp. 1-8, doi: 10.1109/ICPM.2019.00012.
keywords: {Privacy;Information systems;Differential privacy;Business;Analytical models;Process Discovery;Privacy;Privacy-aware Process Mining}

[2]. [Original Github](https://github.com/samadeusfp/PRETSA)

[3]. N. Li, T. Li and S. Venkatasubramanian, "t-Closeness: Privacy Beyond k-Anonymity and l-Diversity," 2007 IEEE 23rd International Conference on Data Engineering, Istanbul, Turkey, 2007, pp. 106-115, doi: 10.1109/ICDE.2007.367856.
keywords: {Privacy;Earth;Computer science;Publishing;Motion measurement;Databases;Data security;Diseases;Remuneration;Protection}

[4]. M. De Leoni and F. Mannhardt, “Road traffic fine
management process,” 2015. https://data.4tu.nl/repository/uuid:
270fd440-1057-4fb9-89a9-b699b47990f5

[5]. J. Buijs, “Environmental permit application process
(‘wabo’), coselog project,” 2014. https://data.4tu.nl/repository/uuid:
26aba40d-8b2d-435b-b5af-6d4bfbd7a270
