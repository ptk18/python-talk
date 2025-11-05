import os
import tempfile
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.models.models import Conversation
from app.nlp_v2.extract_catalog_from_source_code.ast_extractor import extract_from_file
from app.nlp_v2.main import process_complex_command

from app.models.schemas import AnalyzeCommandRequest

router = APIRouter(tags=["Analyze Command"])

@router.post("/analyze_command")
def analyze_command(payload: AnalyzeCommandRequest, db: Session = Depends(get_db)):
    conversation_id = payload.conversation_id
    command = payload.command

    convo = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not convo:
        raise HTTPException(status_code=404, detail="Conversation not found")

    if not convo.code:
        raise HTTPException(status_code=400, detail="This conversation has no uploaded code")

    import tempfile, os
    with tempfile.NamedTemporaryFile(delete=False, suffix=".py") as temp_file:
        temp_file.write(convo.code.encode("utf-8"))
        temp_path = temp_file.name

    try:
        catalog = extract_from_file(temp_path)
        if not catalog.classes:
            raise HTTPException(status_code=400, detail="No class found in uploaded file")

        class_name = list(catalog.classes.keys())[0]
        result = process_complex_command(command, catalog, class_name, verbose=False)

        return {
            "class_name": class_name,
            "file_name": convo.file_name,
            "result": result
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing command: {str(e)}")

    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)
