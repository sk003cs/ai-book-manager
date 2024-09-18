# from langchain_core.embeddings import Embeddings
# from sentence_transformers import SentenceTransformer

# class DistilBertEmbeddings(Embeddings):
#     def __init__(self):
#         self.model = SentenceTransformer('distilbert-base-nli-mean-tokens')

#     def embed_documents(self, texts):
#         return self.model.encode(texts, convert_to_tensor=False).tolist()

#     def embed_query(self, text):
#         return self.model.encode([text], convert_to_tensor=False).tolist()[0]

# # Create an instance of your custom embeddings
# distilbert_embeddings = DistilBertEmbeddings()