import os
import io
import json
from main import app
import database

def run_tests():
    print("=== STARTING DOCUMIND AUTOMATED INTEGRATION TESTS ===")
    app.config["TESTING"] = True
    client = app.test_client()

    # 1. Test GET / (Homepage)
    res = client.get("/")
    assert res.status_code == 200, f"Expected 200, got {res.status_code}"
    assert b"DocuMind" in res.data, "Expected 'DocuMind' in homepage HTML"
    print(" [PASSED] GET / (Homepage rendered successfully)")

    # 2. Test GET /documents (Initially empty)
    res = client.get("/documents")
    assert res.status_code == 200
    data = res.get_json()
    assert data["success"] is True
    print(" [PASSED] GET /documents")

    # 3. Test POST /upload with a real PDF
    test_pdf_path = os.path.join("document loaders", "GRU.pdf")
    if not os.path.exists(test_pdf_path):
        test_pdf_path = os.path.join("document loaders", "deeplearning.pdf")
    
    assert os.path.exists(test_pdf_path), f"Test PDF {test_pdf_path} not found"
    
    with open(test_pdf_path, "rb") as f:
        pdf_bytes = f.read()

    print(f"Uploading {test_pdf_path} ({len(pdf_bytes)} bytes)...")
    res = client.post("/upload",
                      data={"file": (io.BytesIO(pdf_bytes), "test_doc.pdf")},
                      content_type="multipart/form-data")
    
    assert res.status_code == 200, f"Upload failed: {res.get_json()}"
    upload_data = res.get_json()
    assert upload_data["success"] is True
    doc_info = upload_data["document"]
    print(f" [PASSED] POST /upload (Processed {doc_info['pages']} pages, {doc_info['chunks']} chunks)")

    # 4. Test POST /chat (Valid question from the PDF)
    question = "What is a GRU or recurrent neural network?"
    print(f"Testing /chat query: '{question}'...")
    res = client.post("/chat", json={"message": question, "document_id": doc_info["id"]})
    assert res.status_code == 200, f"Chat failed: {res.get_json()}"
    chat_data = res.get_json()
    assert chat_data["success"] is True
    assert "response" in chat_data and len(chat_data["response"]) > 0
    print(f" [PASSED] POST /chat (AI response: {chat_data['response'][:100]}...)")
    print(f" [PASSED] MMR Sources cited: {len(chat_data.get('sources', []))} chunks")

    # 5. Test GET /history
    conv_id = chat_data["conversation_id"]
    res = client.get(f"/history?conversation_id={conv_id}")
    assert res.status_code == 200
    hist_data = res.get_json()
    assert len(hist_data["messages"]) >= 2
    print(f" [PASSED] GET /history (Retrieved {len(hist_data['messages'])} messages)")

    # 6. Test POST /delete-document
    res = client.post("/delete-document", json={"document_id": doc_info["id"]})
    assert res.status_code == 200
    del_data = res.get_json()
    assert del_data["success"] is True
    print(" [PASSED] POST /delete-document (Document and collection deleted cleanly)")

    print("\n=== ALL INTEGRATION TESTS PASSED SUCCESSFULLY! ===")

if __name__ == "__main__":
    run_tests()
