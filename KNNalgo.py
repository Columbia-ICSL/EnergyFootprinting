class KNearestNeighbors:
	def __init__(self, samplePairs):#pairs of (sample, label)
		self.samplePairs = samplePairs

	def get_nearest_pairs(self, sample, K=7):
		distances=[]
		for i in xrange(len(self.samplePairs)):
			dist = self.EUDist(self.samplePairs[i][0], sample)
			distances.append((dist, self.samplePairs[i][1]))
		sortedDistances = sorted(distances, key=lambda dist:dist[0])
		return [(pair[1],1) for pair in sortedDistances[0:K]]
		#majority = self.majority_vote(sortedDistances[0:self.K])
		#return majority[0]
		
	def EUDist(self, Xmeas, Ymeas):
		sum = 0
		for i in xrange(len(Xmeas)):
			sum += (Ymeas[i]-Xmeas[i])*(Ymeas[i]-Xmeas[i])
		return sum

	def majority_vote(self, vote_pairs):#pair(roomID, #votes)
		def merge_same_votes(pairs):
			vote_map={}
			for pair in pairs:
				if pair[0] not in vote_map:
					vote_map[pair[0]]=0
				vote_map[pair[0]]+=pair[1]
			merged_votes=[]
			for roomID in vote_map:
				merged_votes+=(roomID,vote_map[roomID])
			return merged_votes

		vote_pairs=merge_same_votes(vote_pairs)
		maximum_pair = (None, 0)
		for vote in vote_pairs:
			if vote[1]>maximum_pair[1]:
				maximum_pair=vote
		return maximum_pair

