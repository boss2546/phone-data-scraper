// Apple Catalog Frontend Helper SDK (Ultra HD 4K, Sub-Models, Full Specs)
const AppleCatalog = {
  getAll: () => window.APPLE_VARIANTS || [],
  getCategories: () => window.APPLE_CATEGORIES || [],
  getFamilies: () => window.APPLE_PRODUCTS || [],
  getSubModels: (familyId) => {
    const list = window.APPLE_SUB_MODELS || [];
    return familyId ? list.filter(sm => sm.family_id === familyId) : list;
  },
  getVariantsBySubModel: (subModelId) => {
    return (window.APPLE_VARIANTS || []).filter(v => v.sub_model_id === subModelId);
  },
  getProductGallery: (productId, colorId) => {
    if (!window.APPLE_IMAGES) return [];
    return window.APPLE_IMAGES.filter(img => 
      img.product_id === productId && (!colorId || img.color_id === colorId)
    ).sort((a, b) => (a.sort_order || 0) - (b.sort_order || 0));
  },
  filter: ({ category, maxPrice, color, storage, query }) => {
    return (window.APPLE_VARIANTS || []).filter(item => {
      if (category && category !== 'all' && item.category_id !== category && item.category !== category) return false;
      if (maxPrice && item.price_thb > maxPrice) return false;
      if (color && item.color_en.toLowerCase() !== color.toLowerCase() && item.color_th !== color) return false;
      if (storage && item.storage !== storage) return false;
      if (query) {
        const q = query.toLowerCase();
        const text = `${item.model_name} ${item.family} ${item.sub_model_name} ${item.color_th} ${item.part_number}`.toLowerCase();
        if (!text.includes(q)) return false;
      }
      return true;
    });
  },
  findByPartNumber: (partNo) => {
    return (window.APPLE_VARIANTS || []).find(v => v.part_number === partNo || v.id === partNo);
  }
};
window.AppleCatalog = AppleCatalog;
