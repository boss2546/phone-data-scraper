// Apple Catalog Frontend Helper SDK
// วิธีใช้: นำเข้า apple_catalog.js แล้วตามด้วยไฟล์นี้
const AppleCatalog = {
  // ดึงสินค้าทั้งหมด
  getAll: () => window.APPLE_VARIANTS || [],

  // ดึงหมวดหมู่ทั้งหมด
  getCategories: () => window.APPLE_CATEGORIES || [],

  // ดึงตระกูลสินค้าตามหมวดหมู่ ('iphone', 'ipad', 'mac', 'watch')
  getProductsByCategory: (catId) => {
    return (window.APPLE_PRODUCTS || []).filter(p => p.category_id === catId);
  },

  // ดึงตัวเลือกสินค้าทั้งหมดของรุ่นนั้นๆ (เช่น 'iphone-16')
  getVariantsByProduct: (productId) => {
    return (window.APPLE_VARIANTS || []).filter(v => v.product_id === productId);
  },

  // กรองสินค้าตามเงื่อนไข (หมวดหมู่, งบประมาณสูงสุด, สี, ขนาดความจุ)
  filter: ({ category, maxPrice, color, storage, query }) => {
    return (window.APPLE_VARIANTS || []).filter(item => {
      if (category && category !== 'all' && item.category !== category) return false;
      if (maxPrice && item.price_thb > maxPrice) return false;
      if (color && item.color_en.toLowerCase() !== color.toLowerCase() && item.color_th !== color) return false;
      if (storage && item.storage !== storage) return false;
      if (query) {
        const q = query.toLowerCase();
        const text = `${item.model_name} ${item.family} ${item.color_th} ${item.color_en} ${item.part_number}`.toLowerCase();
        if (!text.includes(q)) return false;
      }
      return true;
    });
  },

  // ค้นหาตาม Part Number หรือ SKU
  findByPartNumber: (partNo) => {
    return (window.APPLE_VARIANTS || []).find(v => v.part_number === partNo || v.id === partNo);
  }
};
window.AppleCatalog = AppleCatalog;
