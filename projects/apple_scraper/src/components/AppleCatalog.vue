<template>
  <div class="apple-catalog-container">
    <!-- Header & Controls -->
    <header class="catalog-header">
      <div class="header-main">
        <div class="title-group">
          <h2 class="catalog-title">Apple Store Official Catalog</h2>
          <p class="catalog-subtitle">
            ฐานข้อมูลสเปก ราคา และรูปภาพทางการส่งตรงจาก Apple Store Thailand
          </p>
        </div>

        <!-- View Switcher -->
        <div class="view-switcher">
          <button
            :class="{ active: viewMode === 'color' }"
            @click="viewMode = 'color'"
            class="switch-btn"
          >
            🎨 สีสินค้า (Showcase 63 รุ่น)
          </button>
          <button
            :class="{ active: viewMode === 'product' }"
            @click="viewMode = 'product'"
            class="switch-btn"
          >
            🛍️ รวมรุ่นสินค้า (18 รุ่น)
          </button>
        </div>
      </div>

      <!-- Filters & Search -->
      <div class="filters-bar">
        <div class="category-pills">
          <button
            v-for="cat in categories"
            :key="cat.id"
            :class="['pill-btn', { active: selectedCategory === cat.id }]"
            @click="selectedCategory = cat.id"
          >
            <span class="cat-icon">{{ cat.icon }}</span>
            <span>{{ cat.name_th }}</span>
          </button>
        </div>

        <div class="search-box">
          <span class="search-icon">🔍</span>
          <input
            v-model="searchQuery"
            type="text"
            placeholder="ค้นหารุ่น ชิป หรือสี..."
            class="search-input"
          />
        </div>
      </div>
    </header>

    <!-- Loading & Error States -->
    <div v-if="loading" class="state-container">
      <div class="loading-icon">🍎</div>
      <p class="loading-text">กำลังโหลดข้อมูลสินค้าทางการ...</p>
    </div>

    <div v-else-if="error" class="error-container">
      <strong>⚠️ เกิดข้อผิดพลาด:</strong> {{ error }}
    </div>

    <!-- Product Grid -->
    <div v-else class="catalog-grid">
      <!-- Mode 1: Color Showcase (Zero duplicate images) -->
      <template v-if="viewMode === 'color'">
        <article
          v-for="item in filteredColorItems"
          :key="item.key"
          class="catalog-card"
        >
          <!-- Image -->
          <div class="card-media">
            <span class="res-badge">⚡ 2560px 4K</span>
            <img
              :src="getImageUrl(item)"
              :alt="`${item.productName} สี${item.colorTh}`"
              loading="lazy"
              class="product-image"
            />
            <div class="color-badge">
              <span
                class="swatch-dot"
                :style="{ backgroundColor: item.colorHex }"
              ></span>
              <span>{{ item.colorTh }}</span>
            </div>
          </div>

          <!-- Multi-angle Gallery Row -->
          <div v-if="item.gallery && item.gallery.length > 1" class="gallery-angles-bar">
            <button
              v-for="(g, gIdx) in item.gallery"
              :key="g.angle_type || gIdx"
              :class="['gallery-angle-btn', { active: (selectedAngles[item.key] || 0) === gIdx }]"
              @click="selectAngle(item.key, gIdx)"
            >
              {{ g.angle_type === 'hero' ? '📱 หน้า' : (g.angle_type === 'back' ? '📸 หลัง' : (g.angle_type === 'side' ? '📏 ข้าง' : (g.angle_type === 'box' ? '📦 กล่อง' : (g.label_th || g.angle_type)))) }}
            </button>
          </div>

          <!-- Info -->
          <div class="card-content">
            <div class="badges-row">
              <span class="chip-badge">⚡ {{ item.chip }}</span>
              <span v-if="item.screenSize && item.screenSize !== '-'" class="spec-badge">
                📐 {{ item.screenSize }}
              </span>
            </div>

            <h3 class="product-name">{{ item.productName }}</h3>
            <div class="product-color-name">
              สี{{ item.colorTh }} ({{ item.colorEn }})
            </div>

            <!-- Storage Options -->
            <div v-if="item.options.length > 1" class="options-group">
              <span class="options-label">ความจุ:</span>
              <div class="options-chips">
                <button
                  v-for="(opt, idx) in item.options"
                  :key="opt.id || idx"
                  :class="['chip-btn', { active: (selectedOptions[item.key] || 0) === idx }]"
                  @click="selectOption(item.key, idx)"
                >
                  {{ opt.storage }}
                </button>
              </div>
            </div>

            <!-- Footer Price & CTA -->
            <div class="card-footer">
              <div class="price-group">
                <span class="price-label">ราคาทางการ</span>
                <span class="price-value">{{ getCurrentPrice(item) }}</span>
              </div>
              <button
                class="buy-btn"
                @click="onSelect(getActiveOption(item))"
              >
                เลือกซื้อ
              </button>
            </div>
          </div>
        </article>
      </template>

      <!-- Mode 2: Product Family (Interactive swatches on card) -->
      <template v-else>
        <article
          v-for="item in filteredProductItems"
          :key="item.key"
          class="catalog-card"
        >
          <div class="card-media">
            <span class="res-badge">⚡ 2560px 4K</span>
            <img
              :src="getFamilyImageUrl(item)"
              :alt="item.productName"
              loading="lazy"
              class="product-image"
            />
          </div>

          <!-- Multi-angle Gallery Row -->
          <div v-if="getActiveFamilyColor(item).gallery && getActiveFamilyColor(item).gallery.length > 1" class="gallery-angles-bar">
            <button
              v-for="(g, gIdx) in getActiveFamilyColor(item).gallery"
              :key="g.angle_type || gIdx"
              :class="['gallery-angle-btn', { active: (selectedAngles[item.key] || 0) === gIdx }]"
              @click="selectAngle(item.key, gIdx)"
            >
              {{ g.angle_type === 'hero' ? '📱 หน้า' : (g.angle_type === 'back' ? '📸 หลัง' : (g.angle_type === 'side' ? '📏 ข้าง' : (g.angle_type === 'box' ? '📦 กล่อง' : (g.label_th || g.angle_type)))) }}
            </button>
          </div>

          <div class="card-content">
            <div class="badges-row">
              <span class="chip-badge">⚡ {{ item.chip }}</span>
              <span v-if="item.screenSize && item.screenSize !== '-'" class="spec-badge">
                📐 {{ item.screenSize }}
              </span>
            </div>

            <h3 class="product-name">{{ item.productName }}</h3>

            <!-- Color Swatches -->
            <div class="swatches-section">
              <div class="swatch-label">
                สี: {{ getActiveFamilyColor(item).name_th }}
              </div>
              <div class="swatches-list">
                <button
                  v-for="(c, cIdx) in item.colors"
                  :key="c.color_id"
                  :class="['swatch-circle', { active: (selectedColors[item.key] || 0) === cIdx }]"
                  :style="{ backgroundColor: c.color_hex }"
                  :title="c.name_th"
                  @click="selectColor(item.key, cIdx)"
                ></button>
              </div>
            </div>

            <div class="card-footer">
              <div class="price-group">
                <span class="price-label">ราคาเริ่มต้น</span>
                <span class="price-value">{{ getFamilyStartingPrice(item) }}</span>
              </div>
              <button
                class="buy-btn"
                @click="onSelect(getActiveFamilyOption(item))"
              >
                เลือกซื้อ
              </button>
            </div>
          </div>
        </article>
      </template>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';

const props = defineProps({
  initialTree: { type: Object, default: null },
  apiUrl: { type: String, default: '/data/exports/apple_catalog_tree.json' },
  useLocalImages: { type: Boolean, default: false },
  imageBaseUrl: { type: String, default: '' },
});

const emit = defineEmits(['select-variant']);

const catalogTree = ref(props.initialTree);
const loading = ref(!props.initialTree);
const error = ref(null);

const viewMode = ref('color'); // 'color' or 'product'
const selectedCategory = ref('all');
const searchQuery = ref('');
const selectedOptions = ref({});
const selectedColors = ref({});
const selectedAngles = ref({});

onMounted(async () => {
  if (props.initialTree) return;

  if (typeof window !== 'undefined' && window.APPLE_TREE) {
    catalogTree.value = window.APPLE_TREE;
    loading.value = false;
    return;
  }

  try {
    const res = await fetch(props.apiUrl);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    catalogTree.value = await res.json();
  } catch (err) {
    error.value = err.message;
  } finally {
    loading.value = false;
  }
});

const categories = computed(() => {
  if (!catalogTree.value) return [];
  const cats = [{ id: 'all', name_th: 'ทั้งหมด', icon: '✨' }];
  Object.entries(catalogTree.value).forEach(([k, v]) => {
    cats.push({
      id: k,
      name_th: v.info?.name_th || v.category_info?.name_th || k,
      icon: v.info?.icon || v.category_info?.icon || '📱',
    });
  });
  return cats;
});

// Build Color Showcase list (63 unique items, zero duplicate images)
const colorItems = computed(() => {
  if (!catalogTree.value) return [];
  const list = [];
  Object.entries(catalogTree.value).forEach(([catId, catObj]) => {
    const prods = catObj.products || {};
    Object.entries(prods).forEach(([pId, pData]) => {
      const info = pData.product_info || {};
      (pData.colors || []).forEach((c) => {
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
          imageUrl: c.image_url,
          localImagePath: c.local_image_path,
          gallery: c.gallery || [],
          options: c.options || [],
        });
      });
    });
  });
  return list;
});

// Build Product Family list (18 products)
const productItems = computed(() => {
  if (!catalogTree.value) return [];
  const list = [];
  Object.entries(catalogTree.value).forEach(([catId, catObj]) => {
    const prods = catObj.products || {};
    Object.entries(prods).forEach(([pId, pData]) => {
      const info = pData.product_info || {};
      list.push({
        key: pId,
        productId: pId,
        categoryId: catId,
        productName: info.name,
        chip: info.chip,
        screenSize: info.screen_size,
        colors: pData.colors || [],
        productUrl: info.product_url,
      });
    });
  });
  return list;
});

const filteredColorItems = computed(() => {
  return colorItems.value.filter((item) => {
    const matchesCat = selectedCategory.value === 'all' || item.categoryId === selectedCategory.value;
    const q = searchQuery.value.trim().toLowerCase();
    if (!q) return matchesCat;
    return (
      matchesCat &&
      (item.productName.toLowerCase().includes(q) ||
        item.colorTh.toLowerCase().includes(q) ||
        item.colorEn.toLowerCase().includes(q) ||
        item.chip.toLowerCase().includes(q))
    );
  });
});

const filteredProductItems = computed(() => {
  return productItems.value.filter((item) => {
    const matchesCat = selectedCategory.value === 'all' || item.categoryId === selectedCategory.value;
    const q = searchQuery.value.trim().toLowerCase();
    if (!q) return matchesCat;
    return (
      matchesCat &&
      (item.productName.toLowerCase().includes(q) ||
        item.chip.toLowerCase().includes(q))
    );
  });
});

function getImageUrl(item) {
  const gall = item.gallery || [];
  const aIdx = selectedAngles.value[item.key] || 0;
  const activeG = gall[aIdx] || gall[0];
  if (props.useLocalImages) {
    const p = activeG?.local_image_path || item.localImagePath;
    if (p) return `${props.imageBaseUrl}${p}`;
  }
  return activeG?.image_url || item.imageUrl;
}

function selectOption(key, idx) {
  selectedOptions.value[key] = idx;
}

function selectColor(key, idx) {
  selectedColors.value[key] = idx;
  selectedAngles.value[key] = 0;
}

function selectAngle(key, idx) {
  selectedAngles.value[key] = idx;
}

function getActiveOption(item) {
  const idx = selectedOptions.value[item.key] || 0;
  return item.options[idx] || item.options[0] || {};
}

function getCurrentPrice(item) {
  const opt = getActiveOption(item);
  return opt.formatted_price || 'ตรวจสอบราคา';
}

function getActiveFamilyColor(item) {
  const idx = selectedColors.value[item.key] || 0;
  return item.colors[idx] || item.colors[0] || {};
}

function getActiveFamilyOption(item) {
  const col = getActiveFamilyColor(item);
  return (col.options || [])[0] || {};
}

function getFamilyImageUrl(item) {
  const col = getActiveFamilyColor(item);
  const gall = col.gallery || [];
  const aIdx = selectedAngles.value[item.key] || 0;
  const activeG = gall[aIdx] || gall[0];
  if (props.useLocalImages) {
    const p = activeG?.local_image_path || col.local_image_path;
    if (p) return `${props.imageBaseUrl}${p}`;
  }
  return activeG?.image_url || col.image_url;
}

function getFamilyStartingPrice(item) {
  const col = getActiveFamilyColor(item);
  const firstOpt = (col.options || [])[0];
  return firstOpt ? firstOpt.formatted_price : 'ตรวจสอบราคา';
}

function onSelect(variant) {
  emit('select-variant', variant);
}
</script>

<style scoped>
.apple-catalog-container {
  max-width: 1280px;
  margin: 0 auto;
  padding: 24px 16px;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  color: #1d1d1f;
}

.catalog-header {
  margin-bottom: 32px;
}

.header-main {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 16px;
  margin-bottom: 24px;
}

.catalog-title {
  font-size: 28px;
  font-weight: 700;
  margin: 0 0 6px 0;
  letter-spacing: -0.5px;
}

.catalog-subtitle {
  margin: 0;
  font-size: 14px;
  color: #86868b;
}

.view-switcher {
  display: flex;
  background-color: #f5f5f7;
  padding: 4px;
  border-radius: 12px;
  border: 1px solid #d2d2d7;
}

.switch-btn {
  padding: 8px 16px;
  border-radius: 8px;
  border: none;
  cursor: pointer;
  font-weight: 600;
  font-size: 13px;
  background-color: transparent;
  color: #6e6e73;
  transition: all 0.2s;
}

.switch-btn.active {
  background-color: #ffffff;
  color: #0071e3;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.08);
}

.filters-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 16px;
}

.category-pills {
  display: flex;
  gap: 8px;
  overflow-x: auto;
}

.pill-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 18px;
  border-radius: 20px;
  border: 1px solid #d2d2d7;
  background-color: #ffffff;
  color: #1d1d1f;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  white-space: nowrap;
  transition: all 0.15s ease;
}

.pill-btn.active {
  background-color: #0071e3;
  border-color: #0071e3;
  color: #ffffff;
  font-weight: 600;
}

.search-box {
  position: relative;
  width: 280px;
}

.search-icon {
  position: absolute;
  left: 14px;
  top: 10px;
  color: #86868b;
}

.search-input {
  width: 100%;
  padding: 10px 16px 10px 38px;
  border-radius: 20px;
  border: 1px solid #d2d2d7;
  font-size: 14px;
  outline: none;
  box-sizing: border-box;
}

.catalog-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 24px;
}

.catalog-card {
  background-color: #ffffff;
  border-radius: 18px;
  border: 1px solid #e5e5e7;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.04);
  transition: transform 0.2s, box-shadow 0.2s;
}

.catalog-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.08);
}

.card-media {
  background-color: #fbfbfd;
  padding: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  height: 240px;
  position: relative;
}

.product-image {
  max-height: 100%;
  max-width: 100%;
  object-fit: contain;
}

.color-badge {
  position: absolute;
  bottom: 12px;
  right: 14px;
  display: flex;
  align-items: center;
  gap: 6px;
  background-color: rgba(255, 255, 255, 0.9);
  padding: 4px 8px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
  backdrop-filter: blur(4px);
  border: 1px solid rgba(0, 0, 0, 0.06);
}

.swatch-dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  border: 1px solid rgba(0, 0, 0, 0.2);
}

.card-content {
  padding: 20px;
  display: flex;
  flex-direction: column;
  flex-grow: 1;
}

.badges-row {
  display: flex;
  gap: 6px;
  margin-bottom: 8px;
}

.chip-badge {
  font-size: 11px;
  padding: 3px 8px;
  border-radius: 6px;
  background-color: #f5f5f7;
  font-weight: 600;
}

.spec-badge {
  font-size: 11px;
  padding: 3px 8px;
  border-radius: 6px;
  background-color: #f5f5f7;
  color: #6e6e73;
}

.product-name {
  font-size: 18px;
  font-weight: 700;
  margin: 0 0 4px 0;
}

.product-color-name {
  font-size: 13px;
  color: #86868b;
  margin-bottom: 16px;
}

.options-group {
  margin-bottom: 16px;
}

.options-label {
  font-size: 12px;
  font-weight: 600;
  color: #6e6e73;
  display: block;
  margin-bottom: 6px;
}

.options-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.chip-btn {
  padding: 4px 10px;
  border-radius: 6px;
  font-size: 12px;
  border: 1px solid #d2d2d7;
  background-color: #ffffff;
  color: #1d1d1f;
  cursor: pointer;
}

.chip-btn.active {
  border-color: #0071e3;
  background-color: #e8f2ff;
  color: #0071e3;
  font-weight: 600;
}

.swatches-section {
  margin-bottom: 14px;
}

.swatch-label {
  font-size: 12px;
  font-weight: 600;
  color: #6e6e73;
  margin-bottom: 6px;
}

.swatches-list {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.swatch-circle {
  width: 26px;
  height: 26px;
  border-radius: 50%;
  border: 1px solid rgba(0, 0, 0, 0.2);
  cursor: pointer;
  padding: 0;
  transition: transform 0.15s ease;
}

.swatch-circle.active {
  border: 2px solid #0071e3;
  outline: 2px solid rgba(0, 113, 227, 0.3);
  outline-offset: 2px;
  transform: scale(1.15);
}

.card-footer {
  margin-top: auto;
  padding-top: 12px;
  border-top: 1px solid #f0f0f2;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.price-label {
  display: block;
  font-size: 11px;
  color: #86868b;
}

.price-value {
  font-size: 20px;
  font-weight: 700;
  color: #1d1d1f;
}

.buy-btn {
  padding: 8px 14px;
  border-radius: 16px;
  background-color: #0071e3;
  color: #ffffff;
  border: none;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: background-color 0.15s;
}

.buy-btn:hover {
  background-color: #0077ed;
}

.state-container {
  text-align: center;
  padding: 60px 20px;
}

.loading-icon {
  font-size: 36px;
  margin-bottom: 16px;
}

.loading-text {
  font-size: 18px;
  font-weight: 600;
}

.error-container {
  padding: 30px;
  text-align: center;
  background-color: #fee2e2;
  border-radius: 12px;
  color: #b91c1c;
}
</style>
