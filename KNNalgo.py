class KNearestNeighbors:
	def __init__(self, K, dataset, labels):
		self.K = K
		self.dataset = dataset
		self.labels = labels
		deletedIndices = [345, 344, 341, 335, 336]
		for i in xrange(len(deletedIndices)):
			self.dataset.pop(deletedIndices[i])
			self.labels.pop(deletedIndices[i])
		self.beacons = len(dataset[0])
		self.samples = len(dataset)
		self.distances = [0] * self.samples


	def classifier(self, measurement):
		for i in xrange(len(self.dataset)):
			sum = self.EUDist(self.dataset[i], measurement)
			self.distances[i] = (sum, self.labels[i])
		sortedDistances = sorted(self.distances, key=lambda dist:dist[0])
		majority = self.majority_vote(sortedDistances[0:self.K])
		return majority[0]


	def EUDist(self, Xmeas, Ymeas):
		sum = 0
		for i in xrange(self.beacons):
			sum += (Ymeas[i]-Xmeas[i])*(Ymeas[i]-Xmeas[i])
		return sum

	def majority_vote(self, votes):
		voteMap = {}
		maximum = (0, 0)
		for vote in votes:
			if (vote[1] in voteMap): voteMap[vote[1]] += 1
			else: voteMap[vote[1]] = 1
			if voteMap[vote[1]] > maximum[1]: maximum = (vote[1], voteMap[vote[1]])
		return maximum

