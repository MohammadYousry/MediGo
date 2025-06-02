from fastapi import APIRouter, HTTPException
from firebase_config import db
from datetime import datetime
import pytz

from routers.doctor_assignments import auto_assign_reviewer

egypt_tz = pytz.timezone("Africa/Cairo")
router = APIRouter(prefix="/pending", tags=["Pending Approvals"])

# 🔎 Resolve Firestore doc ID from reviewer ID
def resolve_reviewer_doc_id(assigned_to_id: str) -> str:
    facilities = db.collection("Facilities").where("facility_id", "==", assigned_to_id).stream()
    for doc in facilities:
        return doc.id

    doctor_doc = db.collection("Doctors").document(assigned_to_id).get()
    if doctor_doc.exists:
        return assigned_to_id

    if assigned_to_id == "admin":
        return "admin"

    raise HTTPException(status_code=404, detail=f"Reviewer with ID '{assigned_to_id}' not found")


@router.get("/reviewer/{assigned_to}")
def get_pending_approvals_for_reviewer(assigned_to: str):
    doc_id = resolve_reviewer_doc_id(assigned_to)
    pending_ref = db.collection("PendingApprovals").document(doc_id)
    results = []

    for col in pending_ref.collections():
        for doc in col.stream():
            doc_data = doc.to_dict()
            doc_data["id"] = doc.id
            doc_data["collection"] = col.id
            results.append(doc_data)

    return results


# === ✅ APPROVE with reviewer_name (for deletion from PendingApprovals/<name>)
@router.post("/approve/{assigned_to}/{doc_id}")
def approve_pending(assigned_to: str, doc_id: str, reviewer_name: str = ""):
    reviewer_doc_id = resolve_reviewer_doc_id(assigned_to)
    pending_doc = db.collection("PendingApprovals").document(reviewer_doc_id)

    found_snapshot = None
    found_collection = None

    for col in pending_doc.collections():
        doc_ref = col.document(doc_id)
        snapshot = doc_ref.get()
        if snapshot.exists:
            found_snapshot = snapshot
            found_collection = col.id
            break

    if not found_snapshot:
        raise HTTPException(status_code=404, detail="Pending record not found")

    data = found_snapshot.to_dict()
    national_id = data["national_id"]
    record = data["record"]
    data_type = data.get("data_type", found_collection)

    user_ref = db.collection("Users").document(national_id)
    if not user_ref.get().exists:
        raise HTTPException(status_code=404, detail="User not found")

    timestamp = datetime.now(egypt_tz).strftime("%Y-%m-%d %H:%M:%S")
    record["date_added"] = timestamp

    # ✅ Store in ClinicalIndicators
    user_ref.collection("ClinicalIndicators") \
        .document(data_type).collection("Records") \
        .document(timestamp).set(record)

    # ✅ Archive to ApprovedApprovals
    db.collection("ApprovedApprovals").document(reviewer_doc_id) \
        .collection(found_collection).document(doc_id).set({
            "national_id": national_id,
            "record": record,
            "data_type": data_type,
            "approved_at": timestamp,
            "approved_by": assigned_to
        })

    # ✅ Remove from reviewer_name (human-readable doc) if provided
    if reviewer_name:
        doc_ref = db.collection("PendingApprovals").document(reviewer_name).collection(found_collection).document(doc_id)
        if doc_ref.get().exists:
            doc_ref.delete()
            print(f"✅ Deleted from {reviewer_name}/{found_collection}/{doc_id}")

    # ✅ Remove from all reviewers
    all_reviewers = db.collection("PendingApprovals").stream()
    for reviewer in all_reviewers:
        doc_ref = db.collection("PendingApprovals").document(reviewer.id).collection(found_collection).document(doc_id)
        if doc_ref.get().exists:
            doc_ref.delete()

    return {"message": f"✅ Approved and saved under {national_id}/{data_type} with ID {timestamp}"}


# === ✅ REJECT with reviewer_name (for deletion from PendingApprovals/<name>)
@router.delete("/reject/{assigned_to}/{doc_id}")
def reject_pending(assigned_to: str, doc_id: str, reviewer_name: str = ""):
    reviewer_doc_id = resolve_reviewer_doc_id(assigned_to)
    pending_doc = db.collection("PendingApprovals").document(reviewer_doc_id)

    for col in pending_doc.collections():
        doc_ref = col.document(doc_id)
        snapshot = doc_ref.get()
        if snapshot.exists:
            data = snapshot.to_dict()
            timestamp = datetime.now(egypt_tz).isoformat()

            db.collection("RejectedApprovals").document(reviewer_doc_id) \
                .collection(col.id).document(doc_id).set({
                    "national_id": data.get("national_id"),
                    "record": data.get("record"),
                    "data_type": data.get("data_type", col.id),
                    "rejected_at": timestamp,
                    "rejected_by": assigned_to
                })

            # ✅ Remove from reviewer_name
            if reviewer_name:
                doc_ref = db.collection("PendingApprovals").document(reviewer_name).collection(col.id).document(doc_id)
                if doc_ref.get().exists:
                    doc_ref.delete()
                    print(f"❌ Deleted from {reviewer_name}/{col.id}/{doc_id}")

            # ✅ Remove from all reviewers
            all_reviewers = db.collection("PendingApprovals").stream()
            for reviewer in all_reviewers:
                doc_ref = db.collection("PendingApprovals").document(reviewer.id).collection(col.id).document(doc_id)
                if doc_ref.get().exists:
                    doc_ref.delete()

            return {"message": f"❌ Rejected and removed {doc_id} from {col.id}"}

    raise HTTPException(status_code=404, detail="Pending record not found")


@router.get("/")
def get_all_pending():
    root = db.collection("PendingApprovals")
    all_docs = []

    for doc in root.stream():
        reviewer_id = doc.id
        for col in root.document(reviewer_id).collections():
            for entry in col.stream():
                entry_data = entry.to_dict()
                entry_data["id"] = entry.id
                entry_data["collection"] = col.id
                entry_data["assigned_to"] = reviewer_id
                all_docs.append(entry_data)

    return all_docs
