from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from typing import Sequence
import numpy as np
import hdbscan

from commons import User

class TopExtractor:

    EMBEDDING_MODEL: SentenceTransformer = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
    TOP_N: int = 5

    @staticmethod
    def embed(texts):
        return TopExtractor.EMBEDDING_MODEL.encode(texts, show_progress_bar=False)

    @staticmethod
    def cluster_headlines(embeddings, min_cluster_size=4):
        clusterer = hdbscan.HDBSCAN(min_cluster_size=min_cluster_size)
        labels = clusterer.fit_predict(embeddings)
        return labels

    @staticmethod
    def cluster_medoids(headlines, embeddings, labels):
        medoids = []
        unique_labels = [label for label in set(labels) if label != -1] # Ignore noise (-1)
        for label in unique_labels:
            idx = np.where(labels == label)[0]
            cluster_emb = embeddings[idx]
            # Compute pairwise similarity within cluster
            sim_matrix = cosine_similarity(cluster_emb)
            # Medoid = headline with highest total similarity
            total_sim = sim_matrix.sum(axis=1)
            medoid_idx = idx[np.argmax(total_sim)]

            medoids.append(headlines[medoid_idx])
        return medoids

    @staticmethod
    def mmr_select(candidates, embeddings, top_n=TOP_N, lambda_param=0.6):
        if len(candidates) <= top_n:
            return candidates
        
        sim_matrix = cosine_similarity(embeddings)
        selected = []

        # Relevance vector = similarity to average embedding
        centroid = embeddings.mean(axis=0)
        relevance = cosine_similarity(embeddings, centroid.reshape(1,-1)).flatten()

        # 1st selected is most relevant
        selected_idx = [np.argmax(relevance)]

        while len(selected_idx) < top_n:
            remaining = [i for i in range(len(candidates)) if i not in selected_idx]

            scores = []
            for i in remaining:
                redundancy = max(sim_matrix[i][selected_idx])
                score = lambda_param * relevance[i] - (1 - lambda_param) * redundancy
                scores.append((score, i))
            
            # Pick Best
            best_idx = max(scores)[1]
            selected_idx.append(best_idx)

        return [candidates[i] for i in selected_idx]
    
    @staticmethod
    def pick_top_articles(users: Sequence[User]):
        for user in users:
            headlines = [article.title for feed in user.selected_feeds for article in feed.article]

            embeddings = TopExtractor.embed(headlines)
            labels = TopExtractor.cluster_headlines(embeddings)
            # Extract Medoids
            medoid_headlines = TopExtractor.cluster_medoids(headlines, embeddings, labels)
            medoid_embeddings = TopExtractor.embed(medoid_headlines)
        
            selected_headlines = TopExtractor.mmr_select(medoid_headlines, medoid_embeddings, top_n=TopExtractor.TOP_N)
            
            visited = set()
            top_articles = []
            for feed in user.selected_feeds:
                for article in feed.article:
                    if article.title not in visited and article.title in selected_headlines:
                        visited.add(article.title)
                        top_articles.append(article)
            user.top_articles = top_articles