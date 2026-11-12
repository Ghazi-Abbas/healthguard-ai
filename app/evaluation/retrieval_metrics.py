TOP_K = 5

METRICS = [
    f"recall@{TOP_K}",
    f"precision@{TOP_K}",
    f"mrr@{TOP_K}",
    f"ndcg@{TOP_K}",
]

TARGETS = {
    f"recall@{TOP_K}": 0.90,
    f"mrr@{TOP_K}": 0.80,
}


"""
Metric	Meaning
Recall@5	How many relevant chunks were retrieved in the top 5
Precision@5	How many of the top 5 retrieved chunks were relevant
MRR@5	How early the first relevant chunk appeared
NDCG@5	How good the overall ranking was

"""
