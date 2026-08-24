/**
 * Advice Product Scraper (Node.js Module)
 */
import fs from 'fs';
import path from 'path';

export async function fetchAdviceProduct(url) {
  const response = await fetch(url, {
    headers: {
      "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
      "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
      "Accept-Language": "th,en;q=0.9"
    }
  });

  const html = await response.text();

  // 1. Schema.org JSON-LD
  let schemaData = {};
  const schemaMatch = html.match(/<script[^>]*type=["']application\/ld\+json["'][^>]*>(.*?)<\/script>/s);
  if (schemaMatch) {
    try {
      schemaData = JSON.parse(schemaMatch[1]);
    } catch (e) {}
  }

  const sku = schemaData.sku || "";

  // 2. High-res images
  let images = [];
  if (sku) {
    const imgRegex = new RegExp(`https?://img\\.advice\\.co\\.th/cdn-cgi/image/format=auto,width=700,quality=82,fit=contain/images_nas/pic_product4/${sku}/[^\\s"'<>]+\\.jpg`, 'g');
    const found = html.match(imgRegex);
    if (found) {
      images = [...new Set(found)];
    }
  }
  if (images.length === 0 && schemaData.image) {
    images = [schemaData.image];
  }

  // 3. Summary specs
  let keySpecs = null;
  const specMatch = html.match(/([A-Z0-9]+\s*\/\s*\d+GB\s*\/[^\n"<>]+)/);
  if (specMatch) {
    keySpecs = specMatch[1].trim();
  }

  const offers = schemaData.offers || {};

  return {
    status: "success",
    data: {
      name: schemaData.name || null,
      sku: sku,
      brand: typeof schemaData.brand === "object" ? schemaData.brand?.name : schemaData.brand,
      price: offers.price || null,
      currency: offers.priceCurrency || "THB",
      inStock: String(offers.availability || "").includes("InStock"),
      availability: offers.availability || null,
      keySpecs: keySpecs,
      images: images,
      url: url
    }
  };
}
