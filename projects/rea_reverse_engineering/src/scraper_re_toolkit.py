#!/usr/bin/env python3
"""
Scraper Reverse Engineering Toolkit (REA for Web Scraping & Interception)
Demonstrates how REA superpowers the Monorepo's scraping and interception workflows.
"""

import json
from pathlib import Path
from typing import Dict, Any, List

MODULE_DIR = Path(__file__).resolve().parent.parent
SAMPLES_DIR = MODULE_DIR / "data" / "samples"
RESULTS_DIR = MODULE_DIR / "data" / "results"


class ScraperReverseToolkit:
    """Toolkit translating REA analysis evidence into actionable web scraping artifacts."""

    @staticmethod
    def har_to_scraper_recipe(har_analysis_json: Dict[str, Any]) -> Dict[str, Any]:
        """Convert REA inspect_web_network_capture output into ready-to-use Python scraping code."""
        norm = har_analysis_json.get("normalized_result", {})
        records = norm.get("records", [])
        
        recipes = []
        for rec in records:
            reported = rec.get("reported", {})
            req = reported.get("request", {})
            resp = reported.get("response", {})
            
            url = req.get("url", "")
            method = req.get("method", "GET")
            headers = {h.get("name"): h.get("value") for h in req.get("headers", []) if h.get("name")}
            params = {q.get("name"): q.get("value") for q in req.get("queryString", []) if q.get("name")}
            
            # Generate python code snippet
            code_snippet = f"""# 🤖 Auto-generated Scraper from REA Network Capture
import requests

url = "{url.split('?')[0]}"
params = {json.dumps(params, indent=2)}
headers = {json.dumps({k: v for k, v in headers.items() if k.lower() in ['user-agent', 'accept', 'authorization', 'x-client-signature']}, indent=2)}

response = requests.{method.lower()}(url, params=params, headers=headers)
print("Status Code:", response.status_code)
data = response.json()
print("Scraped Payload:", data)
"""
            recipes.append({
                "url": url,
                "method": method,
                "status": resp.get("status"),
                "content_type": resp.get("headers", {}),
                "generated_code": code_snippet.strip()
            })
            
        return {
            "total_endpoints": len(recipes),
            "recipes": recipes
        }

    @staticmethod
    def app_to_scraping_intel(plist_analysis_json: Dict[str, Any]) -> Dict[str, Any]:
        """Extract deep link schemes, bundle identities, and metadata for app scraping."""
        norm = plist_analysis_json.get("normalized_result", {})
        val = norm.get("value", {})
        bundle = norm.get("bundle", {})
        
        schemes = val.get("PrivateURLSchemes") or val.get("CFBundleURLTypes", [])
        return {
            "app_name": bundle.get("name"),
            "bundle_id": bundle.get("identifier"),
            "version": bundle.get("version"),
            "short_version": bundle.get("short_version"),
            "executable": bundle.get("executable"),
            "min_os_version": val.get("LSMinimumSystemVersion", "Unknown"),
            "url_schemes": schemes,
            "scraping_application": f"สามารถใช้ URL Scheme {schemes} เพื่อเปิด App หรือจำลอง Deeplink Interception ได้"
        }
