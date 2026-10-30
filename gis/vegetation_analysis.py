from .spectral_indices import ndvi
def analyze_vegetation(data, threshold=.2, healthy_threshold=.45, bands=None):
    index,stats=ndvi(data,bands,threshold); return {"vegetation_percentage":float((index>threshold).mean()*100),"mean_ndvi":stats["mean"],"healthy_vegetation_percentage":float((index>healthy_threshold).mean()*100),"low_vegetation_percentage":float((index<=threshold).mean()*100),"ndvi":stats}
