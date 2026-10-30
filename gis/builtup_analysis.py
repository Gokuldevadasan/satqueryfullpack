from .spectral_indices import ndbi
def analyze_builtup(data, threshold=0.0, bands=None):
    index,stats=ndbi(data,bands,threshold); return {"built_up_percentage":float((index>threshold).mean()*100),"mean_ndbi":stats["mean"],"ndbi":stats}
