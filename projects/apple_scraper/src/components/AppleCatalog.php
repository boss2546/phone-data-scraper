<?php
/**
 * AppleCatalog.php - โมดูล PHP สำหรับดึงข้อมูลและแสดงผลสินค้า Apple ในเว็บไซต์ PHP / WordPress / Laravel
 * 
 * ใช้งานได้ 2 รูปแบบ:
 * 1. ดึงจาก SQLite Database (apple_catalog.db) — รวดเร็วมาก เหมาะกับ PHP/PDO
 * 2. ดึงจาก JSON Tree (apple_catalog_tree.json) — ไม่ต้องติดตั้ง PDO SQLite
 */

class AppleCatalogService {
    private $dbPath;
    private $treePath;
    private $pdo = null;

    public function __construct(
        $dbPath = __DIR__ . '/../../data/exports/apple_catalog.db',
        $treePath = __DIR__ . '/../../data/exports/apple_catalog_tree.json'
    ) {
        $this->dbPath = $dbPath;
        $this->treePath = $treePath;
    }

    /**
     * เชื่อมต่อ SQLite Database
     */
    private function getPdo() {
        if ($this->pdo === null && file_exists($this->dbPath)) {
            $this->pdo = new PDO('sqlite:' . $this->dbPath);
            $this->pdo->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
            $this->pdo->setAttribute(PDO::ATTR_DEFAULT_FETCH_MODE, PDO::FETCH_ASSOC);
        }
        return $this->pdo;
    }

    /**
     * ดึงหมวดหมู่ทั้งหมด
     */
    public function getCategories() {
        $pdo = $this->getPdo();
        if ($pdo) {
            $stmt = $pdo->query("SELECT * FROM categories ORDER BY sort_order ASC");
            return $stmt->fetchAll();
        }
        return [];
    }

    /**
     * ดึงสินค้าและสเปกตามตระกูลสินค้า (Product Summary)
     */
    public function getProducts($categoryId = null) {
        $pdo = $this->getPdo();
        if ($pdo) {
            $sql = "SELECT * FROM v_product_summary";
            if ($categoryId) {
                $sql = "SELECT p.* FROM v_product_summary p 
                        JOIN products pr ON p.product_id = pr.id 
                        WHERE pr.category_id = :catId";
                $stmt = $pdo->prepare($sql);
                $stmt->execute([':catId' => $categoryId]);
                return $stmt->fetchAll();
            }
            return $pdo->query($sql)->fetchAll();
        }
        return [];
    }

    /**
     * ดึง Color Showcase (63 รายการรูปไม่ซ้ำ พร้อมภาพความละเอียดสูง)
     */
    public function getColorShowcase($categoryId = null) {
        if (file_exists($this->treePath)) {
            $tree = json_decode(file_get_contents($this->treePath), true);
            $items = [];
            foreach ($tree as $catId => $catData) {
                if ($categoryId && $catId !== $categoryId) continue;
                foreach ($catData['products'] as $pId => $pData) {
                    $info = $pData['product_info'];
                    foreach ($pData['colors'] as $color) {
                        $items[] = [
                            'product_id' => $pId,
                            'category_id' => $catId,
                            'product_name' => $info['name'],
                            'chip' => $info['chip'],
                            'screen_size' => $info['screen_size'],
                            'color_id' => $color['color_id'],
                            'color_th' => $color['name_th'],
                            'color_en' => $color['name_en'],
                            'color_hex' => $color['color_hex'],
                            'image_url' => $color['image_url'],
                            'local_image_path' => $color['local_image_path'] ?? "data/images/{$catId}/{$pId}/{$color['color_id']}.jpg",
                            'options' => $color['options']
                        ];
                    }
                }
            }
            return $items;
        }
        return [];
    }

    /**
     * ค้นหาสินค้าตามคำค้นหา
     */
    public function searchVariants($query, $limit = 50) {
        $pdo = $this->getPdo();
        if ($pdo) {
            $stmt = $pdo->prepare("
                SELECT * FROM v_catalog 
                WHERE model_name LIKE :q 
                   OR specs_chip LIKE :q 
                   OR color_th LIKE :q 
                   OR color_en LIKE :q
                LIMIT :lim
            ");
            $qLike = "%{$query}%";
            $stmt->bindValue(':q', $qLike, PDO::PARAM_STR);
            $stmt->bindValue(':lim', $limit, PDO::PARAM_INT);
            $stmt->execute();
            return $stmt->fetchAll();
        }
        return [];
    }

    /**
     * เรนเดอร์ HTML Card สำหรับแทรกลงในหน้าเว็บ PHP ทันที
     */
    public function renderCatalogHtml($useLocalImages = false) {
        $items = $this->getColorShowcase();
        ob_start();
        ?>
        <div class="apple-php-catalog" style="display:grid; grid-template-columns:repeat(auto-fill, minmax(280px, 1fr)); gap:20px; font-family:sans-serif;">
            <?php foreach ($items as $item): ?>
                <?php 
                    $firstOpt = $item['options'][0] ?? [];
                    $img = $useLocalImages ? $item['local_image_path'] : $item['image_url'];
                ?>
                <div style="border:1px solid #e5e5e7; border-radius:16px; overflow:hidden; background:#fff; box-shadow:0 4px 12px rgba(0,0,0,0.03);">
                    <div style="background:#fbfbfd; height:220px; display:flex; align-items:center; justify-content:center; padding:16px; position:relative;">
                        <img src="<?= htmlspecialchars($img) ?>" alt="<?= htmlspecialchars($item['product_name']) ?>" style="max-height:100%; max-width:100%; object-fit:contain;">
                        <div style="position:absolute; bottom:10px; right:10px; background:rgba(255,255,255,0.9); padding:4px 8px; border-radius:12px; font-size:12px; display:flex; align-items:center; gap:6px;">
                            <span style="width:12px; height:12px; border-radius:50%; background:<?= htmlspecialchars($item['color_hex']) ?>; display:inline-block; border:1px solid #ccc;"></span>
                            <?= htmlspecialchars($item['color_th']) ?>
                        </div>
                    </div>
                    <div style="padding:16px;">
                        <span style="font-size:11px; padding:3px 6px; background:#f5f5f7; border-radius:4px; font-weight:600;">⚡ <?= htmlspecialchars($item['chip']) ?></span>
                        <h3 style="margin:8px 0 4px 0; font-size:17px;"><?= htmlspecialchars($item['product_name']) ?></h3>
                        <p style="margin:0 0 12px 0; font-size:13px; color:#86868b;">สี<?= htmlspecialchars($item['color_th']) ?> (<?= htmlspecialchars($item['color_en']) ?>)</p>
                        <div style="display:flex; justify-content:space-between; align-items:center; border-top:1px solid #eee; padding-top:10px;">
                            <div style="font-size:18px; font-weight:bold; color:#1d1d1f;"><?= htmlspecialchars($firstOpt['formatted_price'] ?? '฿0') ?></div>
                            <button style="background:#0071e3; color:#fff; border:none; padding:6px 14px; border-radius:14px; font-size:13px; font-weight:600; cursor:pointer;">เลือกซื้อ</button>
                        </div>
                    </div>
                </div>
            <?php endforeach; ?>
        </div>
        <?php
        return ob_get_clean();
    }
}
?>
