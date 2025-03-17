from anytree import AnyNode, PreOrderIter
from levenshtein import levenshtein
import sys
from scipy.stats import wasserstein_distance
from scipy.stats import normaltest
import pandas as pd
import numpy as np
from gan_module import train_gan, generate_synthetic_durations  # Import the GAN functions
from pathlib import Path
import json

class Pretsa_gan:
    def _trainGAN(self):
        """
        Trains GAN using all durations from the dataset and stores it in self.generator
        """
        all_durations = []
        for durations in self.__annotationDataOverAll.values():
            all_durations.extend(durations)

        if len(all_durations) >= 5:
            self.generator = train_gan(all_durations, all_durations, self.__t_threshold)
        else:
            self.generator = None

    def __init__(self,eventLog):
        root = AnyNode(id='Root', name="Root", cases=set(), sequence="", annotation=dict(),sequences=set())
        current = root
        currentCase = ""
        caseToSequenceDict = dict() 
        sequence = None
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
        self._trainGAN()
    

    def _attemptGANRepair(self, node, t):
        """
        Uses the GAN to generate synthetic durations for a node to bring it within T-Closeness threshold.
        Separates drift tracking from T-Closeness validation.
        """
        if self.generator is None or node.name not in self.__annotationDataOverAll:
            return None  # No GAN available, return failure

        original_durations = np.array([node.annotations[case] for case in node.cases])
        global_distribution = np.array(self.__annotationDataOverAll[node.name])

        # Generate synthetic durations using GAN
        repaired_durations = np.array(generate_synthetic_durations(
            self.generator,
            global_distribution,
            original_durations.tolist(),
            num_samples=len(node.cases)
        ))

        # Compute Wasserstein Drift (tracks how much GAN changed things)
        drift = wasserstein_distance(original_durations, repaired_durations)

        # Compute actual T-Closeness validation (is this distribution valid?)
        maxDifference = self.annotationMaxDifferences[node.name]
        t_closeness_violation = wasserstein_distance(global_distribution, repaired_durations) / maxDifference >= t

        if not t_closeness_violation:  # If within threshold, accept modifications
            repaired_annotations = {
                case: new_duration for case, new_duration in zip(node.cases, repaired_durations)
            }

            # Compute Mean Absolute Change for tracking GAN impact
            mean_absolute_change = np.mean(np.abs(original_durations - repaired_durations))

            # Log information separately
            self.gan_log.append({
                "Activity": node.name,
                "Wasserstein Drift": drift,  # How much was changed
                "T-Closeness Valid": not t_closeness_violation,  # Whether it passed T-Closeness
                "Mean Absolute Change": mean_absolute_change,  # Individual case changes
                "Original Mean": np.mean(original_durations),
                "Modified Mean": np.mean(repaired_durations),
                "Original Std Dev": np.std(original_durations),
                "Modified Std Dev": np.std(repaired_durations),
                "Cases Affected": len(node.cases)
            })

            return repaired_annotations  # Return modified durations

        return None  # Repair unsuccessful (T-Closeness still violated)


    def _save_gan_log_json(self):
        """
        Saves the GAN log dictionary as a JSON file in '/content/PRETSA/gan_logs.json'.
        Ensures that the directory exists before writing the file.
        """
        log_path = Path("/content/PRETSA/gan_logs.json")  # Define JSON log file path
        log_path.parent.mkdir(parents=True, exist_ok=True)  # Ensure that the directory exists

        with open(log_path, mode="w") as file:
            json.dump(self.gan_log_dict, file, indent=4)  # Save logs in JSON format

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

    #In this case always sequential prunning is used
    def _treePrunning(self, k, t):
        cutOutTraces = set()
        gan_log = []  # Track GAN modifications

        for node in PreOrderIter(self._tree):
            if node != self._tree:
                node.cases = node.cases.difference(cutOutTraces)

                violates_k = len(node.cases) < k
                violates_t = self._violatesTCloseness(node.name, node.annotations, t, node.cases)

                # Case 1: Violates K-Anonymity but NOT T-Closeness → Prune & Merge (Original Method)
                if violates_k and not violates_t:
                    cutOutTraces = cutOutTraces.union(node.cases)
                    self._cutCasesOutOfTreeStartingFromNode(node, cutOutTraces)
                    if self._sequentialPrunning:
                        return cutOutTraces

                # Case 2: Violates T-Closeness but NOT K-Anonymity → Attempt GAN Repair
                elif violates_t and not violates_k:
                    repaired_durations = self._attemptGANRepair(node, t)
                    if repaired_durations is not None:
                        node.annotations = repaired_durations  # Apply GAN-fix
                        gan_log.append((node.name, repaired_durations))
                    else:
                        # If GAN repair fails, prune as usual
                        cutOutTraces = cutOutTraces.union(node.cases)
                        self._cutCasesOutOfTreeStartingFromNode(node, cutOutTraces)
                        if self._sequentialPrunning:
                            return cutOutTraces

                # Case 3: Violates BOTH K-Anonymity and T-Closeness
                elif violates_k and violates_t:
                    repaired_durations = self._attemptGANRepair(node, t)
                    if repaired_durations is not None:
                        node.annotations = repaired_durations  # Apply GAN-fix first
                        gan_log.append((node.name, repaired_durations))
                    else:
                        # If GAN repair fails, prune like in the original
                        cutOutTraces = cutOutTraces.union(node.cases)
                        self._cutCasesOutOfTreeStartingFromNode(node, cutOutTraces)
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


    def runPretsa(self,k,t,normalTCloseness=True):
        self.__normalTCloseness = normalTCloseness
        if not self.__normalTCloseness:
            self.__haveAllValuesInActivitityDistributionTheSameValue = dict()
        self._overallLogDistance = 0.0
        if self._sequentialPrunning:
            cutOutCases = set()
            cutOutCase = self._treePrunning(k,t)
            while len(cutOutCase) > 0:
                self.__combineTracesAndTree(cutOutCase)
                cutOutCases = cutOutCases.union(cutOutCase)
                cutOutCase = self._treePrunning(k,t)
        else:
            cutOutCases = self._treePrunning(k,t)
            self.__combineTracesAndTree(cutOutCases)

            #Saving GAN log after prunning
            self._save_gan_log_json()
            
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