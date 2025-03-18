# PRETSA BINARY: Privacy-Preserving Event Log Sanitization improvement

## Overview

Introduction

PRETSA BINARY (Privacy-Enforcing Transformation for Secure Anonymization) is an optimized version of the original PRETSA framework [1]. The motivation behind the original method is that Event logs contain sensitive timestamps and case durations, which can lead to re-identification risks even when no employee data is left in the data.

The original PRETSA framework builds a tree based on an event log, where each node corresponds to an activity. Each node contains key node-specific data structures:
	•	self.cases: A set containing all caseIds associated with that node.
	•	self.annotation: A dictionary mapping each caseId in the node to its corresponding activity duration.
	•	self.sequences: A set containing all possible sequences at the node level.

Additionally, the following attributes exist at the tree level (global scope across all nodes):
	•	self.__annotationDataOverAll: A mapping of all activities to their durations for all caseIds in the tree.
	•	self._caseToSequenceDict: A mapping that tracks a caseId’s sequence up to the activity represented by a node.

This distinction is important because node-level attributes store localized information about specific activities in the tree, while tree-level attributes provide a global view of activity durations and sequence mappings across all nodes.



Problems: Original PRETSA Implementation

The original PRETSA method makes the check for the k-anonimity and t-closeness violations for a node in the same if statement within the _treePrunning(self, k,t) function. As a result both violations are fixed using the same method which is removing the violating node and then transferring these caseIds along with the original activity duration into another treePath sequence that closely matches it's sequence. The closeness between two paths is assesed using a levenheistein distance calculation between the sequence strings stored at the node level. The sequence with the minimal distance and attempts to merge the cutout caseIDs with the original activity duration into the nodes for the activities in the selected sequence. The problem with this approach is that while it is a efficient way to deal wth k anonimity the t-closeness is not really ensured since the decision is solely made on similarity of the strings but distribution changes are not taken into account.

The original repository [2] was outdated, relying on deprecated Python functions. Additionally, the organization of logs and files was not optimal, as all newly generated durations and method logs were stored in the same directory as the code, making file management inefficient. Furthermore, the repository did not provide a secure method for users to directly load their own dataset or configure key parameters such as k or t values. While the repository included some error logging and statistics generation modules the resulting logs did not correctly asses the diffference in durationsfrom the non-sanitized vs sanitized events. Additinally code to generate appropriate graphs was not provided.

Solutions: PRETSA BINARY

The PRETSA BINARY implementation attempts to ensure compliance with t-closeness treshold [3] and to maximize data utility by reassigning activity durations statistically close to the original distribution by doing a binary search in a preordering of the tree built by PRETSA. 

The new sanitization approach operates in two stages:
	1.	K-Anonymity Enforcement: Removing traces that do not meet the k-anonymity threshold and re-adding them to maximize data utility using the original approach.
	2.	T-Closeness Correction: Adjusting sensitive attributes (activity durations) while minimizing distortion.

This implementation introduces two new security related features that significantly improve the privacy-preserving process:
	1.	A Binary Search-Based Approach for T-Closeness Correction after K-Anonimity enforcement.
	2.	Complete pipeline from raw dataset to visualization. Enabling user to input their own dataset and parameters which results in a Heatmap-Based Visualization for Optimal k and t Parameter Selection for both models.

## Installation

To run this implementation, install the required dependencies:

pip install -r requirements.txt

Requirements:

anytree==2.4.3
numpy>=1.18.1
scipy>=1.4.1
pandas>=0.23.4
matplotlib>=3.1.0 
seaborn>=0.10.0  
pm4py

## Security Features: Details

### 1. T-Closeness Fix Using Binary Search

Modules: startExperimentsForJournalExtension_PRETSA_BINARY.py, runExperimentForJournalExtension_pretsa_BINARY.py
and runPretsa_BINARY.py, pretsa_binary.py.

User calls startExperimentsForJournalExtension_PRETSA_BINARY.py <k-values> <t-values>. This will trigger the runExperimentForJournalExtension_pretsa_BINARY.py calls for each value in k and t values lists which in turn fires the pretsa tree construction as well as the runPretsa method with the two steps:

PRETSA_BINAY Workflow from runPretsa_BINARY.py

When runPretsa_BINARY(k, t, normalTCloseness=True) is executed, it follows this sequence of function calls:
	1.	Fixing k-Anonymity
	•	Calls _treePrunning(k, t) to remove nodes with fewer than k cases.
	•	If nodes are removed, calls _cutCasesOutOfTreeStartingFromNode(node, cutOutTraces) to ensure affected nodes are fully removed.
	•	Reassigns removed cases to the closest valid sequence using __combineTracesAndTree(cutOutCases).
	•	Repeats pruning and reassignment until all nodes satisfy k-anonymity.
	2.	Fixing t-Closeness
	•	Iterates over the tree and calls _violatesTCloseness(activity, annotations, t, cases) for each node.
	•	If a node violates t-closeness, calls _binary_search_adjust(node, t_threshold=t) to modify durations while minimizing changes.
	•	Logs adjustments and saves them using _save_tcloseness_logs_json(), which stores the logs in the /content/PRETSA/t-closeness/ directory.
	3.	Generating the Final Event Log
	•	Calls getPrivatisedEventLog() to reconstruct the modified event log from the adjusted tree.

Summary of Key Function Calls
	1.	_treePrunning, _cutCasesOutOfTreeStartingFromNode, __combineTracesAndTree (Fix k-anonymity)
	2.	_violatesTCloseness, _binary_search_adjust, _save_tcloseness_logs_json (Fix t-closeness, logs stored in /content/PRETSA/t-closeness/)
	3.	getPrivatisedEventLog (Export the final anonymized dataset)

_binary_search_adjust Details:
	•	Binary Search 
	•	A low and high range is set for possible duration values.
	•	The method uses binary search to determine the minimal change required to satisfy t-closeness.
	•	The best replacement is selected based on minimal Wasserstein Distance shift.
	•	Logging Adjustments:
	•	Every modification is logged for transparency.
	•	The implementation ensures that no unnecessary distortions are introduced.


### 2. User-optimal framework

Modules: dataset_collection.py, calculateDurationDifferences.py & mapDurationDifferences.py

This implementation introduces direct download of data files with the dataset_collection.py module. Enables user to use any available dataset online or their own datasets. This implementation also enables the user to pass a list of k and t values to each sanitization method to asses security related design choices for sanitization of their own logs

This implementation introduces heatmaps that visualize the impact of different k and t values, allowing users to find an optimal balance between privacy and data utility. This implementation securely generates the final sanitized event_log for both methods and stores them in their respective directories: "/content/PRETSA/pretsa_binarylog" for PRETSA Binary and "/content/PRETSA/pretsalog" for Original PRETSA.

Results
	•	Helps identify an optimal k-value, ensuring sufficient privacy without excessive data loss.
	•	Assists in selecting a suitable t-value that keeps durations close to their original distribution.
    •	Organized in their respective directory, secure process logs and secure final sanitized event logs.
      
# Analyze duration differences
Defined in calculateDurationDifferences.py
User can call error_data = calculate_duration_differences("CoSeLoG", "default") with an option parameter to select which model to get the logs from.
This could be "default" for PRETSA or "binary" for PRETSA BINARY.

# Generate heatmap visualization
Defined in mapDurationDifferences.py

User can call generate_heatmap("CoSeLoG", "default") with an option parameter to select which model to get the logs from.
This could be "default" for PRETSA or "binary" for PRETSA BINARY.

This will produce a heatmap illustrating the accuracy of durations for various k and t values and for a selected method that allows the user to select the best sanitization method for their specific database. 

Additional notes: Accuracy of durations seem to vary a lot even for the same t-value and k-value in both methods and it's because there are never any real checks for t-closeness in the original method. The PRETSA BINARY will modify the durations even for a k-anonimous compliant log which will further modify the utility while the original PRETSA will stop at the k-anonimity constrain being satisfied. Please look at google colab output for SEPSIS dataset for a clear view of my discovery.

## Conclusion

Full workflow to use the PRETSA BINARY can be found in the notebook.ipynb. The graphs and test were generated using online datasets Sepsis[4] and Coselogs [5] as in the original paper.

This implementation enhances PRETSA by introducing:
	1.	A Binary Search-Based Fix for T-Closeness - Ensuring activity durations are optimally adjusted without excessive modifications.
	2.	Heatmap-Based Visualization - Allowing users to choose the best privacy parameters before running the anonymization process.

## References

[1]. S. A. Fahrenkrog-Petersen, H. van der Aa and M. Weidlich, "PRETSA: Event Log Sanitization for Privacy-aware Process Discovery," 2019 International Conference on Process Mining (ICPM), Aachen, Germany, 2019, pp. 1-8, doi: 10.1109/ICPM.2019.00012.
keywords: {Privacy;Information systems;Differential privacy;Business;Analytical models;Process Discovery;Privacy;Privacy-aware Process Mining},
[2]. [Original Github](https://github.com/samadeusfp/PRETSA)
[3]. N. Li, T. Li and S. Venkatasubramanian, "t-Closeness: Privacy Beyond k-Anonymity and l-Diversity," 2007 IEEE 23rd International Conference on Data Engineering, Istanbul, Turkey, 2007, pp. 106-115, doi: 10.1109/ICDE.2007.367856.
keywords: {Privacy;Earth;Computer science;Publishing;Motion measurement;Databases;Data security;Diseases;Remuneration;Protection},
[4]. M. De Leoni and F. Mannhardt, “Road traffic fine
management process,” 2015. https://data.4tu.nl/repository/uuid:
270fd440-1057-4fb9-89a9-b699b47990f5
[5]. J. Buijs, “Environmental permit application process
(‘wabo’), coselog project,” 2014. https://data.4tu.nl/repository/uuid:
26aba40d-8b2d-435b-b5af-6d4bfbd7a270