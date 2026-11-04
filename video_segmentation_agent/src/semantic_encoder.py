def adjacent_similarities(chunks):
    if len(chunks)<2:return []
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    texts=[c.get('transcript','') for c in chunks]; v=TfidfVectorizer(analyzer='char_wb',ngram_range=(3,5),min_df=1); x=v.fit_transform(texts)
    return [float(cosine_similarity(x[i],x[i+1])[0,0]) for i in range(len(chunks)-1)]
