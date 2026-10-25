def test_knowledge_search_and_crud(client):
    kb_payload = {
        "doc_code": "KB-TEST-001",
        "title": "车门双唇密封防高压水冲洗设计准则",
        "subsystem": "Primary Body Seal",
        "category": "Design-Guideline",
        "tags": "water-leak,car-wash,EPDM",
        "content": "在A柱区域采用双唇阻水槽结构，可承受100 bar高压水洗冲击而不发生微量渗透。",
        "keywords": "车门 密封 漏水 高压清洗 双唇",
        "source_reference": "ES-QA-SEAL-01",
        "author": "Dr. Wei Chen"
    }
    create_res = client.post("/api/v1/knowledge", json=kb_payload)
    assert create_res.status_code == 201
    kb_id = create_res.json()["id"]

    # Search by keyword
    search_res = client.get("/api/v1/knowledge?search=双唇")
    assert search_res.status_code == 200
    items = search_res.json()["items"]
    assert len(items) == 1
    assert items[0]["doc_code"] == "KB-TEST-001"

    # Filter by category
    cat_res = client.get("/api/v1/knowledge?category=Design-Guideline")
    assert cat_res.status_code == 200
    assert cat_res.json()["total"] == 1
