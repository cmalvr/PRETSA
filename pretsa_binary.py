from anytree import AnyNode, PreOrderIter
from levenshtein import levenshtein
import sys
from scipy.stats import wasserstein_distance
from scipy.stats import normaltest
import pandas as pd
import numpy as np
import time
import json
from pathlib import Path

class Pretsa_binary:
    def __init__(self,eventLog, dataset):
        root = AnyNode(id='Root', name="Root", cases=set(), sequence="", annotation=dict(),sequences=set())
        current = root
        currentCase = ""
        caseToSequenceDict = dict() 
        sequence = None
        self.__dataset = dataset
        self.__caseIDColName = "Case ID"
        self.__activityColName = "Activity"
        self.__annotationColName = "Duration"
        self.__constantEventNr = "Event_Nr"
        self.__annotationDataOverAll = dict() # Activity mapped to list of durations
        self.__normaltest_alpha = 0.05
        self.__normaltest_result_storage = dict()
        self.__normalTCloseness = True

        # Iterates through the event log and creates a tree structure
        for index, row in eventLog.iterrows():
            
            activity = row[self.__activityColName] # Activity
            annotation = row[self.__annotationColName] #Duration
            
            if row[self.__caseIDColName] != currentCase: #First iteration currentCase = "" so it will be unequal
                current = root
                if not sequence is None:
                    caseToSequenceDict[currentCase] = sequence  #For first iteration currentCase  = "" gets mapped to None squence in caseToSequenceDict dict !!
                    current.sequences.add(sequence) # For first iteration sequence is None . It gets added to sequences set!
                currentCase = row[self.__caseIDColName] # Get Case ID
                current.cases.add(currentCase) # Add Case ID to current node cases. For first iteration currentCase is "". It gets added to cases set!
                sequence = "" # Initialize empty sequence since its first one or a new subtree
            
            #FOR ALL ROWS
            childAlreadyExists = False
            sequence = sequence + "@" + activity # Generate sequence@activity string
           
           #Iterate through children of current node DFS
            for child in current.children:
                if child.name == activity: # If Child equals activity
                    childAlreadyExists = True
                    current = child # Set current to child. Last iterated child will become current
            
            #If this node has no children, create a new one
            if not childAlreadyExists:
                node = AnyNode(id=index, name=activity, parent=current, cases=set(), sequence=sequence, annotations=dict()) #First child will be a index = 0, second will be 1 ...
                current = node
            
            current.cases.add(currentCase) # Add Case ID to cases set !!!
            current.annotations[currentCase] = annotation #CaseID mapped to activity duration in annotations dict !!!
            self.__addAnnotation(annotation, activity)
        
        #Handle last case
        caseToSequenceDict[currentCase] = sequence #Maps CaseID to sequence which is many activities concatenated with @ !!!!
        root.sequences.add(sequence) #Add last sequence to sequences set
        self._tree = root
        self._caseToSequenceDict = caseToSequenceDict
        self.__numberOfTracesOriginal = len(self._tree.cases)
        self._sequentialPrunning = True
        self.__setMaxDifferences()
        self.__haveAllValuesInActivitityDistributionTheSameValue = dict()
        self._distanceMatrix = self.__generateDistanceMatrixSequences(self._getAllPotentialSequencesTree(self._tree))

    def __addAnnotation(self, annotation, activity):
        dataForActivity = self.__annotationDataOverAll.get(activity, None)
        if dataForActivity is None:
            self.__annotationDataOverAll[activity] = []
            dataForActivity = self.__annotationDataOverAll[activity]
        dataForActivity.append(annotation)

    def __setMaxDifferences(self):
        self.annotationMaxDifferences = dict()
        for key in self.__annotationDataOverAll.keys():
            maxVal = max(self.__annotationDataOverAll[key])
            minVal = min(self.__annotationDataOverAll[key])
            self.annotationMaxDifferences[key] = abs(maxVal - minVal)

    def _violatesTCloseness(self, activity, annotations, t, cases):
        distributionActivity = self.__annotationDataOverAll[activity]
        maxDifference = self.annotationMaxDifferences[activity]
        #Consider only data from cases still in node
        distributionEquivalenceClass = []
        casesInClass = cases.intersection(set(annotations.keys()))
        for caseInClass in casesInClass:
            distributionEquivalenceClass.append(annotations[caseInClass])
        if len(distributionEquivalenceClass) == 0: #No original annotation is left in the node
            return False
        if maxDifference == 0.0: #All annotations have the same value(most likely= 0.0)
            return
        if self.__normalTCloseness == True:
            return ((wasserstein_distance(distributionActivity,distributionEquivalenceClass)/maxDifference) >= t)
        else:
            return self._violatesStochasticTCloseness(distributionActivity,distributionEquivalenceClass,t,activity)


    def _treePrunning(self, k,t):
        cutOutTraces = set()
        for node in PreOrderIter(self._tree):
            if node != self._tree:
                node.cases = node.cases.difference(cutOutTraces)
                # If the node has less than k cases or violates t-closeness, we cut out the cases and the subtree
                # To enfoce l-DIVERSITY WE NEED THE DURAION NUMBERS BECAUSE THAT IS THE SENSITIVE VALUE
                if len(node.cases) < k:
                    cutOutTraces = cutOutTraces.union(node.cases)
                    self._cutCasesOutOfTreeStartingFromNode(node,cutOutTraces)
                    if self._sequentialPrunning:
                        return cutOutTraces
        return cutOutTraces

    def _cutCasesOutOfTreeStartingFromNode(self,node,cutOutTraces,tree=None):
        if tree == None:
            tree = self._tree
        current = node
        try:
            tree.sequences.remove(node.sequence)
        except KeyError:
            pass
        while current != tree:
            current.cases = current.cases.difference(cutOutTraces)
            if len(current.cases) == 0:
                node = current
                current = current.parent
                node.parent = None
            else:
                current = current.parent

    def _getAllPotentialSequencesTree(self, tree):
        return tree.sequences

    def _addCaseToTree(self, trace, sequence,tree=None):
        if tree == None:
            tree = self._tree
        if trace != "":
            activities = sequence.split("@")
            currentNode = tree
            tree.cases.add(trace)
            for activity in activities:
                for child in currentNode.children:
                    if child.name == activity:
                        child.cases.add(trace)
                        currentNode = child
                        break

    def __combineTracesAndTree(self, traces):
        #We transform the set of sequences into a list and sort it, to discretize the behaviour of the algorithm
        sequencesTree = list(self._getAllPotentialSequencesTree(self._tree))
        sequencesTree.sort()
        for trace in traces:
            bestSequence = ""
            #initial value as high as possible
            lowestDistance = sys.maxsize
            traceSequence = self._caseToSequenceDict[trace]
            for treeSequence in sequencesTree:
                currentDistance = self._getDistanceSequences(traceSequence, treeSequence)
                if currentDistance < lowestDistance:
                    bestSequence = treeSequence
                    lowestDistance = currentDistance
            self._overallLogDistance += lowestDistance
            self._addCaseToTree(trace, bestSequence)
            
    def _binary_search_adjust(self, node, t_threshold):
        """
        Adjusts a node's annotations using binary search over possible activity durations
        while minimizing modifications and ensuring T-Closeness.

        Args:
            node: The tree node containing the annotations (CaseID -> duration).
            t_threshold: Maximum allowed Wasserstein Distance fraction.
        """
        activity = node.name
        case_ids = list(node.annotations.keys())
        original_durations = np.array(list(node.annotations.values()))  # Node's current durations
        possible_values = sorted(self.__annotationDataOverAll[activity])  # All known durations for this activity

        if not possible_values or len(original_durations) == 0:
            return  # Nothing to adjust

        maxDifference = self.annotationMaxDifferences[activity]  # Normalized threshold

        # Compute initial Wasserstein Distance (before adjustment)
        wasserstein_before = wasserstein_distance(self.__annotationDataOverAll[activity], original_durations)

        low, high = 0, len(possible_values) - 1
        candidate_replacements = []  # Store valid replacements

        # **Binary search to find the best valid replacement**
        for _ in range(20):  # Limit to 20 iterations for efficiency
            mid = (low + high) // 2  # Midpoint in sorted possible values
            candidate_durations = np.random.choice(possible_values[:mid+1], size=len(case_ids), replace=True)

            # Compute Wasserstein Distance after modification
            wasserstein_after = wasserstein_distance(self.__annotationDataOverAll[activity], candidate_durations)
            t_value = wasserstein_after / maxDifference

            if t_value < t_threshold:
                # Store valid replacement with its Wasserstein Distance
                candidate_replacements.append((candidate_durations.copy(), wasserstein_after))
                low = mid + 1  # Try using more values
            else:
                high = mid - 1  # Try using fewer values

        # **Find the best candidate that minimizes Wasserstein Distance change**
        if candidate_replacements:
            best_replacement, best_wasserstein_diff = min(
                candidate_replacements,
                key=lambda x: x[1]  # Select the one with the lowest Wasserstein Distance
            )
        else:
            best_replacement = original_durations.copy()  # Default: no changes
            best_wasserstein_diff = wasserstein_before  # No change in Wasserstein Distance

        # **Log the changes per node**
        self.t_closeness_adjustments.append({
            "Activity": activity,
            "Wasserstein Distance Before": wasserstein_before,
            "Wasserstein Distance After": best_wasserstein_diff,
            "Original Durations": original_durations.tolist(),
            "Modified Durations": best_replacement.tolist(),
            "Cases Affected": len(case_ids)
        })

        # **Apply the best found durations to the node**
        node.annotations = {case: new_duration for case, new_duration in zip(case_ids, best_replacement)}
        
    def _save_tcloseness_logs_json(self):
        """ Saves the T-Closeness adjustment logs to a JSON file. """
        log_path = Path(f"/content/PRETSA/t-closeness/{self.__dataset}_t_closeness_logs.json")
        log_path.parent.mkdir(parents=True, exist_ok=True)  # Ensure directory exists

        with open(log_path, "w") as file:
            json.dump(self.t_closeness_adjustments, file, indent=4)


    def runPretsa(self,k,t,normalTCloseness=True):
        self.__normalTCloseness = normalTCloseness
        if not self.__normalTCloseness:
            self.__haveAllValuesInActivitityDistributionTheSameValue = dict()
        self._overallLogDistance = 0.0
        if self._sequentialPrunning:
            cutOutCases = set()
            print(" Fixing K-Anonymity...")
            cutOutCase = self._treePrunning(k,t)
            while len(cutOutCase) > 0:
                self.__combineTracesAndTree(cutOutCase)
                cutOutCases = cutOutCases.union(cutOutCase)
                cutOutCase = self._treePrunning(k,t)
        else:
            cutOutCases = self._treePrunning(k,t)
            self.__combineTracesAndTree(cutOutCases)

        print(" Fixing T-closeness...")

        for node in PreOrderIter(self._tree):
            if node != self._tree:  # Avoid processing root node
                if self._violatesTCloseness(node.name, node.annotations, t, node.cases):
                    self._binary_search_adjust(node, t_threshold= t)
        return cutOutCases, self._overallLogDistance

    def __generateNewAnnotation(self, activity):
        #normaltest works only with more than 8 samples
        if(len(self.__annotationDataOverAll[activity])) >=8 and activity not in self.__normaltest_result_storage.keys():
            stat, p = normaltest(self.__annotationDataOverAll[activity])
        else:
            p = 1.0
        self.__normaltest_result_storage[activity] = p
        if self.__normaltest_result_storage[activity] <= self.__normaltest_alpha:
            mean = np.mean(self.__annotationDataOverAll[activity])
            std = np.std(self.__annotationDataOverAll[activity])
            randomValue = np.random.normal(mean, std)
        else:
            randomValue = np.random.choice(self.__annotationDataOverAll[activity])
        if randomValue < 0:
            randomValue = 0
        return randomValue

    def getEvent(self,case,node):
        event = {
            self.__activityColName: node.name,
            self.__caseIDColName: case,
            self.__annotationColName: node.annotations.get(case, self.__generateNewAnnotation(node.name)),
            self.__constantEventNr: node.depth
        }
        return event

    def getEventsOfNode(self, node):
        events = []
        if node != self._tree:
            events = events + [self.getEvent(case, node) for case in node.cases]
        return events

    def getPrivatisedEventLog(self):
        events = []
        self.__normaltest_result_storage = dict()
        nodeEvents = [self.getEventsOfNode(node) for node in PreOrderIter(self._tree)]
        for node in nodeEvents:
            events.extend(node)
        eventLog = pd.DataFrame(events)
        if not eventLog.empty:
            eventLog = eventLog.sort_values(by=[self.__caseIDColName, self.__constantEventNr])
        return eventLog


    def __generateDistanceMatrixSequences(self,sequences):
        distanceMatrix = dict()
        for sequence1 in sequences:
            distanceMatrix[sequence1] = dict()
            for sequence2 in sequences:
                if sequence1 != sequence2:
                    distanceMatrix[sequence1][sequence2] = levenshtein(sequence1,sequence2)
        print("Generated Distance Matrix")
        return distanceMatrix

    def _getDistanceSequences(self, sequence1, sequence2):
        if sequence1 == "" or sequence2 == "" or sequence1 == sequence2:
            return sys.maxsize
        try:
            distance = self._distanceMatrix[sequence1][sequence2]
        except KeyError:
            print("A Sequence is not in the distance matrix")
            print(sequence1)
            print(sequence2)
            raise
        return distance

    def __areAllValuesInDistributionAreTheSame(self, distribution):
        if max(distribution) == min(distribution):
            return True
        else:
            return False

    def _violatesStochasticTCloseness(self,distributionEquivalenceClass,overallDistribution,t,activity):
        if activity not in self.__haveAllValuesInActivitityDistributionTheSameValue.keys():
            self.__haveAllValuesInActivitityDistributionTheSameValue[activity] = self.__areAllValuesInDistributionAreTheSame(overallDistribution)
        if not self.__haveAllValuesInActivitityDistributionTheSameValue[activity]:
            upperLimitsBuckets = self._getBucketLimits(t,overallDistribution)
            return (self._calculateStochasticTCloseness(overallDistribution, distributionEquivalenceClass, upperLimitsBuckets) > t)
        else:
            return False

    def _calculateStochasticTCloseness(self, overallDistribution, equivalenceClassDistribution, upperLimitBuckets):
        overallDistribution.sort()
        equivalenceClassDistribution.sort()
        counterOverallDistribution = 0
        counterEquivalenceClass = 0
        distances = list()
        for bucket in upperLimitBuckets:
            lastCounterOverallDistribution = counterOverallDistribution
            lastCounterEquivalenceClass = counterEquivalenceClass
            while counterOverallDistribution<len(overallDistribution) and overallDistribution[counterOverallDistribution
            ] < bucket:
                counterOverallDistribution = counterOverallDistribution + 1
            while counterEquivalenceClass<len(equivalenceClassDistribution) and equivalenceClassDistribution[counterEquivalenceClass
            ] < bucket:
                counterEquivalenceClass = counterEquivalenceClass + 1
            probabilityOfBucketInEQ = (counterEquivalenceClass-lastCounterEquivalenceClass)/len(equivalenceClassDistribution)
            probabilityOfBucketInOverallDistribution = (counterOverallDistribution-lastCounterOverallDistribution)/len(overallDistribution)
            if probabilityOfBucketInEQ == 0 and probabilityOfBucketInOverallDistribution == 0:
                distances.append(0)
            elif probabilityOfBucketInOverallDistribution == 0 or probabilityOfBucketInEQ == 0:
                distances.append(sys.maxsize)
            else:
                distances.append(max(probabilityOfBucketInEQ/probabilityOfBucketInOverallDistribution,probabilityOfBucketInOverallDistribution/probabilityOfBucketInEQ))
        return max(distances)



    def _getBucketLimits(self,t,overallDistribution):
        numberOfBuckets = round(t+1)
        overallDistribution.sort()
        divider = round(len(overallDistribution)/numberOfBuckets)
        upperLimitsBuckets = list()
        for i in range(1,numberOfBuckets):
            upperLimitsBuckets.append(overallDistribution[min(round(i*divider),len(overallDistribution)-1)])
        return upperLimitsBuckets