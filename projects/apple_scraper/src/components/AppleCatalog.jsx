import React, { useState, useEffect, useMemo } from 'react';

/**
 * AppleCatalog - คอมโพเนนต์ React / Next.js สำเร็จรูปสำหรับแสดงรายการสินค้า Apple ทางการ
 * 
 * คุณสมบัติ:
 * - สลับดูสีสินค้าสด พร้อมเปลี่ยนรูปตามสีทันที
 * - เลือกความจุ/สเปก พร้อมคำนวณราคาแบบ Realtime
 * - รองรับทั้งรูปจาก Apple Official CDN หรือ Local Storage (data/images/)
 * - ค้นหาและกรองตามหมวดหมู่ (iPhone, iPad, Mac, Apple Watch)
 * - รองรับ Callback onSelectVariant เมื่อผู้ใช้เลือกสินค้าไปลงตะกร้า (Cart)
 * 
 * ตัวอย่างการใช้งาน:
 * import AppleCatalog from './components/AppleCatalog';
 * <AppleCatalog onSelectVariant={(v) => console.log('Selected:', v)} />
 */
export default function AppleCatalog({
  initialTreeData = null,
  treeApiUrl = '/data/exports/apple_catalog_tree.json',
  useLocalImages = false,
  imageBaseUrl = '',
  onSelectVariant = null,
}) {
  const [catalogTree, setCatalogTree] = useState(initialTreeData);
  const [loading, setLoading] = useState(!initialTreeData);
  const [error, setError] = useState(null);

  // States
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [viewMode, setViewMode] = useState('color'); // 'color' (Color Showcase) or 'product' (Family)
  const [selectedColors, setSelectedColors] = useState({}); // { [productId]: colorIndex }
  const [selectedStorages, setSelectedStorages] = useState({}); // { [productId]: optionIndex }

  // โหลดข้อมูลหากไม่ได้ส่ง initialTreeData เข้ามา
  useEffect(() => {
    if (initialTreeData) {
      setCatalogTree(initialTreeData);
      return;
    }
    
    // ตรวจสอบว่ามี window.APPLE_TREE ในหน้าเว็บอยู่แล้วหรือไม่
    if (typeof window !== 'undefined' && window.APPLE_TREE) {
      setCatalogTree(window.APPLE_TREE);
      setLoading(false);
      return;
    }

    fetch(treeApiUrl)
      .then((res) => {
        if (!res.ok) throw new Error(`HTTP ${res.status}: ไม่สามารถดึงข้อมูล Apple Tree ได้`);
        return res.json();
      })
      .then((data) => {
        setCatalogTree(data);
        setLoading(false);
      })
      .catch((err) => {
        setError(err.message);
        setLoading(false);
      });
  }, [initialTreeData, treeApiUrl]);

  // ดึงหมวดหมู่ทั้งหมด
  const categories = useMemo(() => {
    if (!catalogTree) return [];
    return [
      { id: 'all', name_th: 'ทั้งหมด', icon: '✨' },
      ...Object.keys(catalogTree).map((k) => ({
        id: k,
        name_th: catalogTree[k]?.info?.name_th || catalogTree[k]?.category_info?.name_th || k,
        icon: catalogTree[k]?.info?.icon || catalogTree[k]?.category_info?.icon || '📱',
      })),
    ];
  }, [catalogTree]);

  // ประมวลผลรายการสินค้าทั้งหมด
  const items = useMemo(() => {
    if (!catalogTree) return [];
    const list = [];

    Object.entries(catalogTree).forEach(([catId, catObj]) => {
      const products = catObj.products || {};
      Object.entries(products).forEach(([pId, pData]) => {
        const info = pData.product_info || {};
        const colors = pData.colors || [];

        if (viewMode === 'color') {
          // โหมด Color Showcase: 1 การ์ด = 1 สี (รูปไม่ซ้ำ 100%)
          colors.forEach((c) => {
            list.push({
              key: `${pId}-${c.color_id}`,
              productId: pId,
              categoryId: catId,
              productName: info.name,
              chip: info.chip,
              screenSize: info.screen_size,
              colorId: c.color_id,
              colorTh: c.name_th,
              colorEn: c.name_en,
              colorHex: c.color_hex,
              imageUrl: useLocalImages ? `${imageBaseUrl}${c.local_image_path}` : c.image_url,
              options: c.options || [],
              minPrice: Math.min(...(c.options || []).map((o) => o.price_thb || 0)),
              maxPrice: Math.max(...(c.options || []).map((o) => o.price_thb || 0)),
              productUrl: info.product_url,
            });
          });
        } else {
          // โหมด Product Family: 1 การ์ด = 1 รุ่นสินค้า (สลับสีในตัว)
          list.push({
            key: pId,
            productId: pId,
            categoryId: catId,
            productName: info.name,
            chip: info.chip,
            screenSize: info.screen_size,
            colors: colors,
            productUrl: info.product_url,
          });
        }
      });
    });

    return list;
  }, [catalogTree, viewMode, useLocalImages, imageBaseUrl]);

  // กรองตามหมวดหมู่และค้นหา
  const filteredItems = useMemo(() => {
    return items.filter((item) => {
      const matchesCat = selectedCategory === 'all' || item.categoryId === selectedCategory;
      const query = searchQuery.trim().toLowerCase();
      if (!query) return matchesCat;

      const matchesSearch =
        item.productName.toLowerCase().includes(query) ||
        (item.colorTh && item.colorTh.toLowerCase().includes(query)) ||
        (item.colorEn && item.colorEn.toLowerCase().includes(query)) ||
        (item.chip && item.chip.toLowerCase().includes(query));

      return matchesCat && matchesSearch;
    });
  }, [items, selectedCategory, searchQuery]);

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: '60px 20px', fontFamily: 'system-ui, sans-serif' }}>
        <div style={{ fontSize: '36px', marginBottom: '16px' }}>🍎</div>
        <div style={{ fontSize: '18px', fontWeight: 600, color: '#1d1d1f' }}>กำลังโหลดข้อมูลสินค้า Apple ทางการ...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div style={{ padding: '30px', textAlign: 'center', backgroundColor: '#fee2e2', borderRadius: '12px', color: '#b91c1c' }}>
        <strong>⚠️ เกิดข้อผิดพลาด:</strong> {error}
      </div>
    );
  }

  return (
    <div style={{ maxWidth: '1280px', margin: '0 auto', padding: '24px 16px', fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif', color: '#1d1d1f' }}>
      {/* Header & Controls */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '20px', marginBottom: '32px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '16px' }}>
          <div>
            <h2 style={{ fontSize: '28px', fontWeight: 700, margin: '0 0 6px 0', letterSpacing: '-0.5px' }}>
              Apple Store Official Catalog
            </h2>
            <p style={{ margin: 0, fontSize: '14px', color: '#86868b' }}>
              ข้อมูลสินค้า สเปก ชิป ราคา และรูปภาพทางการส่งตรงจาก Apple Store Thailand
            </p>
          </div>

          {/* View Mode Toggle */}
          <div style={{ display: 'flex', backgroundColor: '#f5f5f7', padding: '4px', borderRadius: '12px', border: '1px solid #d2d2d7' }}>
            <button
              onClick={() => setViewMode('color')}
              style={{
                padding: '8px 16px',
                borderRadius: '8px',
                border: 'none',
                cursor: 'pointer',
                fontWeight: 600,
                fontSize: '13px',
                backgroundColor: viewMode === 'color' ? '#ffffff' : 'transparent',
                color: viewMode === 'color' ? '#0071e3' : '#6e6e73',
                boxShadow: viewMode === 'color' ? '0 2px 6px rgba(0,0,0,0.08)' : 'none',
                transition: 'all 0.2s',
              }}
            >
              🎨 แยกตามสีสินค้า ({viewMode === 'color' ? filteredItems.length : '63'})
            </button>
            <button
              onClick={() => setViewMode('product')}
              style={{
                padding: '8px 16px',
                borderRadius: '8px',
                border: 'none',
                cursor: 'pointer',
                fontWeight: 600,
                fontSize: '13px',
                backgroundColor: viewMode === 'product' ? '#ffffff' : 'transparent',
                color: viewMode === 'product' ? '#0071e3' : '#6e6e73',
                boxShadow: viewMode === 'product' ? '0 2px 6px rgba(0,0,0,0.08)' : 'none',
                transition: 'all 0.2s',
              }}
            >
              🛍️ รวมรุ่นสินค้า (18 รุ่น)
            </button>
          </div>
        </div>

        {/* Filter Pills & Search */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '16px' }}>
          {/* Category Tabs */}
          <div style={{ display: 'flex', gap: '8px', overflowX: 'auto', paddingBottom: '4px' }}>
            {categories.map((c) => {
              const active = selectedCategory === c.id;
              return (
                <button
                  key={c.id}
                  onClick={() => setSelectedCategory(c.id)}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '6px',
                    padding: '8px 18px',
                    borderRadius: '20px',
                    border: '1px solid',
                    borderColor: active ? '#0071e3' : '#d2d2d7',
                    backgroundColor: active ? '#0071e3' : '#ffffff',
                    color: active ? '#ffffff' : '#1d1d1f',
                    cursor: 'pointer',
                    fontSize: '14px',
                    fontWeight: active ? 600 : 500,
                    whiteSpace: 'nowrap',
                    transition: 'all 0.15s ease',
                  }}
                >
                  <span>{c.icon}</span>
                  <span>{c.name_th}</span>
                </button>
              );
            })}
          </div>

          {/* Search Input */}
          <div style={{ position: 'relative', width: '280px' }}>
            <input
              type="text"
              placeholder="ค้นหารุ่น ชิป หรือสี..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              style={{
                width: '100%',
                padding: '10px 16px 10px 38px',
                borderRadius: '20px',
                border: '1px solid #d2d2d7',
                fontSize: '14px',
                outline: 'none',
                boxSizing: 'border-box',
                backgroundColor: '#ffffff',
              }}
            />
            <span style={{ position: 'absolute', left: '14px', top: '10px', color: '#86868b' }}>🔍</span>
          </div>
        </div>
      </div>

      {/* Grid of Cards */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))',
          gap: '24px',
        }}
      >
        {filteredItems.map((item) => {
          if (viewMode === 'color') {
            // Card: Color Showcase (1 unique image per card)
            const activeOptIdx = selectedStorages[item.key] || 0;
            const currentOption = item.options[activeOptIdx] || item.options[0] || {};
            const displayPrice = currentOption.formatted_price || `฿${item.minPrice.toLocaleString()}`;

            return (
              <div
                key={item.key}
                style={{
                  backgroundColor: '#ffffff',
                  borderRadius: '18px',
                  border: '1px solid #e5e5e7',
                  overflow: 'hidden',
                  display: 'flex',
                  flexDirection: 'column',
                  boxShadow: '0 4px 12px rgba(0,0,0,0.04)',
                }}
              >
                {/* Image Section */}
                <div
                  style={{
                    backgroundColor: '#fbfbfd',
                    padding: '24px',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    height: '240px',
                    position: 'relative',
                  }}
                >
                  <img
                    src={item.imageUrl}
                    alt={`${item.productName} ${item.colorTh}`}
                    loading="lazy"
                    style={{
                      maxHeight: '100%',
                      maxWidth: '100%',
                      objectFit: 'contain',
                    }}
                  />
                  {/* Color Swatch Dot */}
                  <div
                    style={{
                      position: 'absolute',
                      bottom: '12px',
                      right: '14px',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '6px',
                      backgroundColor: 'rgba(255,255,255,0.9)',
                      padding: '4px 8px',
                      borderRadius: '12px',
                      fontSize: '12px',
                      fontWeight: 500,
                      backdropFilter: 'blur(4px)',
                      border: '1px solid rgba(0,0,0,0.06)',
                    }}
                  >
                    <span
                      style={{
                        width: '12px',
                        height: '12px',
                        borderRadius: '50%',
                        backgroundColor: item.colorHex,
                        border: '1px solid rgba(0,0,0,0.2)',
                      }}
                    />
                    <span>{item.colorTh}</span>
                  </div>
                </div>

                {/* Content Section */}
                <div style={{ padding: '20px', display: 'flex', flexDirection: 'column', flexGrow: 1 }}>
                  <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap', marginBottom: '8px' }}>
                    <span style={{ fontSize: '11px', padding: '3px 8px', borderRadius: '6px', backgroundColor: '#f5f5f7', color: '#1d1d1f', fontWeight: 600 }}>
                      ⚡ {item.chip}
                    </span>
                    {item.screenSize && item.screenSize !== '-' && (
                      <span style={{ fontSize: '11px', padding: '3px 8px', borderRadius: '6px', backgroundColor: '#f5f5f7', color: '#6e6e73' }}>
                        📐 {item.screenSize}
                      </span>
                    )}
                  </div>

                  <h3 style={{ fontSize: '18px', fontWeight: 700, margin: '0 0 4px 0' }}>{item.productName}</h3>
                  <div style={{ fontSize: '13px', color: '#86868b', marginBottom: '16px' }}>
                    สี{item.colorTh} ({item.colorEn})
                  </div>

                  {/* Storage Chips */}
                  {item.options.length > 1 && (
                    <div style={{ marginBottom: '16px' }}>
                      <div style={{ fontSize: '12px', fontWeight: 600, color: '#6e6e73', marginBottom: '6px' }}>
                        ความจุ / สเปก:
                      </div>
                      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                        {item.options.map((opt, idx) => {
                          const active = idx === activeOptIdx;
                          return (
                            <button
                              key={opt.id || idx}
                              onClick={() => setSelectedStorages({ ...selectedStorages, [item.key]: idx })}
                              style={{
                                padding: '4px 10px',
                                borderRadius: '6px',
                                fontSize: '12px',
                                border: '1px solid',
                                borderColor: active ? '#0071e3' : '#d2d2d7',
                                backgroundColor: active ? '#e8f2ff' : '#ffffff',
                                color: active ? '#0071e3' : '#1d1d1f',
                                fontWeight: active ? 600 : 400,
                                cursor: 'pointer',
                              }}
                            >
                              {opt.storage}
                            </button>
                          );
                        })}
                      </div>
                    </div>
                  )}

                  <div style={{ marginTop: 'auto', paddingTop: '12px', borderTop: '1px solid #f0f0f2', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <div>
                      <div style={{ fontSize: '11px', color: '#86868b' }}>ราคาทางการ</div>
                      <div style={{ fontSize: '20px', fontWeight: 700, color: '#1d1d1f' }}>{displayPrice}</div>
                    </div>

                    <button
                      onClick={() => onSelectVariant && onSelectVariant(currentOption)}
                      style={{
                        padding: '8px 14px',
                        borderRadius: '16px',
                        backgroundColor: '#0071e3',
                        color: '#ffffff',
                        border: 'none',
                        fontSize: '13px',
                        fontWeight: 600,
                        cursor: 'pointer',
                      }}
                    >
                      เลือกซื้อ
                    </button>
                  </div>
                </div>
              </div>
            );
          } else {
            // Card: Product Family (Dynamic color swatches on card)
            const activeColorIdx = selectedColors[item.key] || 0;
            const currentColor = item.colors[activeColorIdx] || item.colors[0] || {};
            const activeOptIdx = selectedStorages[item.key] || 0;
            const currentOption = (currentColor.options || [])[activeOptIdx] || (currentColor.options || [])[0] || {};
            const imgUrl = useLocalImages ? `${imageBaseUrl}${currentColor.local_image_path}` : currentColor.image_url;

            return (
              <div
                key={item.key}
                style={{
                  backgroundColor: '#ffffff',
                  borderRadius: '18px',
                  border: '1px solid #e5e5e7',
                  overflow: 'hidden',
                  display: 'flex',
                  flexDirection: 'column',
                  boxShadow: '0 4px 12px rgba(0,0,0,0.04)',
                }}
              >
                {/* Dynamic Image */}
                <div
                  style={{
                    backgroundColor: '#fbfbfd',
                    padding: '24px',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    height: '240px',
                  }}
                >
                  <img
                    src={imgUrl}
                    alt={`${item.productName} ${currentColor.name_th}`}
                    loading="lazy"
                    style={{
                      maxHeight: '100%',
                      maxWidth: '100%',
                      objectFit: 'contain',
                    }}
                  />
                </div>

                {/* Content */}
                <div style={{ padding: '20px', display: 'flex', flexDirection: 'column', flexGrow: 1 }}>
                  <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap', marginBottom: '8px' }}>
                    <span style={{ fontSize: '11px', padding: '3px 8px', borderRadius: '6px', backgroundColor: '#f5f5f7', fontWeight: 600 }}>
                      ⚡ {item.chip}
                    </span>
                    {item.screenSize && item.screenSize !== '-' && (
                      <span style={{ fontSize: '11px', padding: '3px 8px', borderRadius: '6px', backgroundColor: '#f5f5f7', color: '#6e6e73' }}>
                        📐 {item.screenSize}
                      </span>
                    )}
                  </div>

                  <h3 style={{ fontSize: '18px', fontWeight: 700, margin: '0 0 12px 0' }}>{item.productName}</h3>

                  {/* Interactive Swatches */}
                  <div style={{ marginBottom: '14px' }}>
                    <div style={{ fontSize: '12px', fontWeight: 600, color: '#6e6e73', marginBottom: '6px' }}>
                      สี: {currentColor.name_th} ({currentColor.name_en})
                    </div>
                    <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
                      {item.colors.map((c, cIdx) => {
                        const active = cIdx === activeColorIdx;
                        return (
                          <button
                            key={c.color_id}
                            title={c.name_th}
                            onClick={() => setSelectedColors({ ...selectedColors, [item.key]: cIdx })}
                            style={{
                              width: '26px',
                              height: '26px',
                              borderRadius: '50%',
                              backgroundColor: c.color_hex,
                              border: active ? '2px solid #0071e3' : '1px solid rgba(0,0,0,0.2)',
                              outline: active ? '2px solid rgba(0,113,227,0.3)' : 'none',
                              outlineOffset: '2px',
                              cursor: 'pointer',
                              padding: 0,
                              transform: active ? 'scale(1.15)' : 'scale(1)',
                              transition: 'transform 0.15s ease',
                            }}
                          />
                        );
                      })}
                    </div>
                  </div>

                  {/* Price & CTA */}
                  <div style={{ marginTop: 'auto', paddingTop: '12px', borderTop: '1px solid #f0f0f2', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <div>
                      <div style={{ fontSize: '11px', color: '#86868b' }}>ราคาเริ่มต้น</div>
                      <div style={{ fontSize: '20px', fontWeight: 700, color: '#1d1d1f' }}>
                        {currentOption.formatted_price || 'ตรวจสอบราคา'}
                      </div>
                    </div>

                    <button
                      onClick={() => onSelectVariant && onSelectVariant(currentOption)}
                      style={{
                        padding: '8px 14px',
                        borderRadius: '16px',
                        backgroundColor: '#0071e3',
                        color: '#ffffff',
                        border: 'none',
                        fontSize: '13px',
                        fontWeight: 600,
                        cursor: 'pointer',
                      }}
                    >
                      เลือกซื้อ
                    </button>
                  </div>
                </div>
              </div>
            );
          }
        })}
      </div>
    </div>
  );
}
