from pyspark import SparkContext
import itertools

sc = SparkContext("spark://spark-master:7077", "PopularItems")

data = sc.textFile("/tmp/data/access.txt", 2)     # each worker loads a piece of the data file

pairs = data.map(lambda line: line.split("\t"))   # tell each worker to split each line of it's partition

# Group data into (user_id, <item_id>)
click_pairs = pairs.groupByKey().mapValues(list)

# Transform into (user_id, (item1, item2) where item1 and item2 are pairs of items the user clicked on
def non_dup_pairs(linput):
	comb = [(x,y) for x in linput for y in linput if x != y ]
	for e in comb:
		if (e[1], e[0]) in comb:
			if e[1] < e[0]:
				comb.remove(e)
			else:
				comb.remove((e[1], e[0]))
	return comb
click_pairs_combo = click_pairs.map(lambda x: (x[0], non_dup_pairs(x[1])))

# Transform into ((item1, item2), <user>) where users are all the ones who co-clicked (item1, item2)
def f(x): return x
click_pairs_map = click_pairs_combo.flatMapValues(f)
c = click_pairs_map.map(lambda x: reversed(x))
click_pair_to_users = c.groupByKey().mapValues(list)

# Transform into ((item1, item2), count of distinct users who co-clicked (item1, item2)
click_pair_to_count = click_pair_to_users.map(lambda x: (x[0], len(x[1])))

# Filter out any results where less than 3 users co-clicked the same pair of items
result = click_pair_to_count.filter(lambda x: x[1] > 2)
output = result.collect()                          # bring the data back to the master node so we can print it out
for item_id, count in output:
    print ("co-viewed item_id: " + str(item_id) + "\t count: " + str(count))
print ("Done")

sc.stop()