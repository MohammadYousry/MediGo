from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional, Dict, Any
from datetime import date, datetime

# --- Helper Functions (Placeholders) ---
def fetch_patient_name(patient_national_id: str, db_session) -> Optional[str]:
    print(f"[Placeholder] fetch_patient_name called for {patient_national_id}")
    return "Patient Name (Placeholder)"

def resolve_added_by_name(added_by_id: str, db_session) -> Optional[str]:
    print(f"[Placeholder] resolve_added_by_name called for {added_by_id}")
    return "Added By Name (Placeholder)"

def calculate_age(birthdate_str: Optional[str]) -> Optional[int]:
    if not birthdate_str: return None
    try:
        birthdate_dt_obj = datetime.strptime(birthdate_str, "%Y-%m-%d").date()
        today = date.today()
        return today.year - birthdate_dt_obj.year - ((today.month, today.day) < (birthdate_dt_obj.month, birthdate_dt_obj.day))
    except (ValueError, TypeError): return None

# --- Base Models ---
class BaseInput(BaseModel):
    notes: Optional[str] = None

class BaseRecord(BaseInput):
    record_id: str = Field(..., description="Unique ID for the record")
    patient_name: Optional[str] = None
    added_by_name: Optional[str] = None
    entry_date: Optional[str] = Field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    
    class Config: # Corrected Indentation
        from_attributes = True

# --- User Models ---
class UserBase(BaseModel):
    email: Optional[EmailStr] = Field(None, description="User's email address") # <-- ضفنا Optional و None
    full_name: Optional[str] = Field(None, description="User's full name")
    national_id: str = Field(..., description="National ID, must be unique")
    phone_number: Optional[str] = Field(None, description="User's phone number")
    gender: Optional[str] = Field(None, description="Gender (e.g., male, female, other)")
    date_of_birth: Optional[str] = Field(None, description="Date of birth (YYYY-MM-DD)")
    address: Optional[str] = Field(None, description="Primary address line")
    city: Optional[str] = Field(None, description="City")
    region: Optional[str] = Field(None, description="Region or governorate")
    blood_type: Optional[str] = Field(None, description="Blood type (e.g., A+, O-)")
    profile_picture_url: Optional[str] = Field(None, description="URL to profile picture")
    emergency_contacts: Optional[List[Dict[str, Any]]] = Field(default_factory=list, description="List of emergency contacts")
    allergies: Optional[List[Dict[str, Any]]] = Field(default_factory=list, description="List of allergies")
    chronic_diseases: Optional[List[str]] = Field(default_factory=list, description="List of chronic diseases")
    medications: Optional[List[Dict[str, Any]]] = Field(default_factory=list, description="List of current medications")

class UserCreate(UserBase):
    password: str = Field(..., min_length=8, description="User password")

class UserResponse(UserBase):
    user_id: str = Field(..., description="Unique user identifier (often same as national_id or a UUID)")
    is_active: Optional[bool] = Field(True, description="User account status")
    
    class Config: # Corrected Indentation
        from_attributes = True

class UserEmergencyInfo(UserBase):
    age: Optional[int] = Field(None, description="Calculated age of the user")

# --- Doctor Specific Models ---
class DoctorsBase(UserBase):
    specialization: Optional[str] = Field(None, description="Doctor's specialization")
    license_number: Optional[str] = Field(None, unique=True, description="Medical license number")
    years_of_experience: Optional[int] = Field(None, ge=0)

class DoctorsCreateRequest(DoctorsBase):
    password: str = Field(..., min_length=8, description="Doctor's account password")

class Doctors(DoctorsBase):
    doctor_id: str = Field(..., description="Unique doctor identifier")
    is_active: Optional[bool] = Field(True)
    
    class Config: # Corrected Indentation
        from_attributes = True

# --- Facility Models ---
class FacilityBase(BaseModel):
    name: str = Field(...)
    facility_type: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    region: Optional[str] = None
    phone_number: Optional[str] = None
    email: Optional[EmailStr] = None

class FacilityCreateRequest(FacilityBase):
    pass

class Facility(FacilityBase):
    facility_id: str = Field(...)
    
    class Config: # Corrected Indentation
        from_attributes = True

# --- QR Code Models ---
class QRCodeCreate(BaseModel): user_id: str; expiration_date: str
class QRCodeResponse(BaseModel): user_id: str; last_accessed: str; expiration_date: str; qr_image: str; qr_data: Optional[str] = None
class QRCodeWithUserInfoResponse(BaseModel): user_id: str; last_accessed: Optional[str] = None; expiration_date: Optional[str] = None; qr_image: Optional[str] = None; user_info: Optional[UserEmergencyInfo] = None

# --- Doctor Assignment Models ---
class DoctorAssignmentBase(BaseModel): patient_national_id: str; doctor_email: EmailStr; assignment_date: Optional[str] = Field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S")); notes: Optional[str] = None
class DoctorAssignmentCreate(DoctorAssignmentBase): pass
class DoctorAssignment(DoctorAssignmentBase):
    assignment_id: str = Field(...)
    
    class Config: # Corrected Indentation
        from_attributes = True

# --- Surgery Models ---
class SurgeryBase(BaseInput): surgery_name: str; surgery_date: str; hospital_name: Optional[str] = None; doctor_name: Optional[str] = None
class SurgeryCreate(SurgeryBase): pass
class SurgeryEntry(SurgeryBase, BaseRecord): # BaseRecord already has Config
    pass 

# --- BloodBiomarker Models ---
class TestResultItem(BaseModel): test_name: str; value: Any; unit: Optional[str] = None; reference_range: Optional[str] = None; flag: Optional[str] = None
class BloodBiomarkerInput(BaseInput): test_date: str = Field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d")); test_type: str; results: List[TestResultItem]
class BloodBioMarker(BloodBiomarkerInput, BaseRecord): # BaseRecord already has Config
    pass

# --- HeightWeight Models ---
class HeightWeightBase(BaseInput): measurement_date: str = Field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d")); height_cm: Optional[float] = Field(None, gt=0); weight_kg: Optional[float] = Field(None, gt=0); bmi: Optional[float] = None
class HeightWeightCreate(HeightWeightBase): pass
class HeightWeight(HeightWeightBase, BaseRecord): # BaseRecord already has Config
    pass

# --- Radiology Models ---
class RadiologyTestBase(BaseInput): test_name: str; test_date: str = Field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d")); body_part: Optional[str] = None; findings: Optional[str] = None; impression: Optional[str] = None
class RadiologyTestInput(RadiologyTestBase): pass
class RadiologyTest(RadiologyTestBase, BaseRecord): # BaseRecord already has Config
    pass

# --- Hypertension Models ---
class HypertensionReading(BaseModel): systolic: int = Field(..., gt=0); diastolic: int = Field(..., gt=0); pulse: Optional[int] = Field(None, gt=0)
class HypertensionBase(BaseInput): reading_date: str = Field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S")); readings: HypertensionReading; position: Optional[str] = None
class HypertensionCreate(HypertensionBase): pass
class HypertensionEntry(HypertensionBase, BaseRecord): # BaseRecord already has Config
    pass

# --- Medication Models ---
class MedicationBase(BaseInput): name: str; dosage: Optional[str] = None; frequency: Optional[str] = None; start_date: Optional[str] = None; end_date: Optional[str] = None; reason: Optional[str] = None
class MedicationCreate(MedicationBase): pass
class MedicationEntry(MedicationBase, BaseRecord): # BaseRecord already has Config
    pass

# --- Diagnosis Models ---
class DiagnosisBase(BaseInput): diagnosis_code: Optional[str] = None; diagnosis_description: str; diagnosis_date: str = Field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d")); status: Optional[str] = None
class DiagnosisCreate(DiagnosisBase): pass
class DiagnosisEntry(DiagnosisBase, BaseRecord): # BaseRecord already has Config
    pass

# --- Allergy Models ---
class AllergyBase(BaseInput): allergen: str; reaction: Optional[str] = None; severity: Optional[str] = None; onset_date: Optional[str] = None
class AllergyCreate(AllergyBase): pass
class Allergy(AllergyBase, BaseRecord): # BaseRecord already has Config
    pass

# --- FamilyHistory Models ---
class FamilyHistoryBase(BaseInput): relative_name: Optional[str] = None; relationship: str; condition: str; age_at_diagnosis: Optional[int] = Field(None, gt=0)
class FamilyHistoryCreate(FamilyHistoryBase): pass
class FamilyHistoryEntry(FamilyHistoryBase, BaseRecord): # BaseRecord already has Config
    pass

# --- EmergencyContact Models ---
class EmergencyContactBase(BaseModel): name: str; relationship: str; phone_number: str
class EmergencyContactCreate(EmergencyContactBase): pass
class EmergencyContact(EmergencyContactBase, BaseRecord): # BaseRecord already has Config
    pass

# --- PendingApproval Models ---
class PendingApprovalBase(BaseModel): item_id: str; item_type: str; requested_by_id: Optional[str] = None; request_date: Optional[str] = Field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S")); status: str = Field(default="pending"); reviewer_assigned_id: Optional[str] = None; review_notes: Optional[str] = None
class PendingApprovalCreate(PendingApprovalBase): pass
class PendingApproval(PendingApprovalBase):
    approval_id: str = Field(...)
    class Config: # Corrected Indentation
        from_attributes = True

# --- Role Models ---
class RoleBase(BaseModel): name: str = Field(..., unique=True); description: Optional[str] = None; permissions: Optional[List[str]] = Field(default_factory=list)
class RoleCreate(RoleBase): pass
class RoleResponse(RoleBase):
    role_id: str = Field(...)
    class Config: # Corrected Indentation
        from_attributes = True

# --- AdminUser Model ---
class AdminUser(UserResponse): # UserResponse already has Config
    admin_level: Optional[int] = None

# --- RiskAssessment Models ---
class FeatureImportance(BaseModel): feature: str; importance: float
class DerivedFeatures(BaseModel): bmi: Optional[float] = None; age_group: Optional[str] = None
class TopFeatures(BaseModel): disease_type: str; top_positive_contributors: List[FeatureImportance] = Field(default_factory=list); top_negative_contributors: List[FeatureImportance] = Field(default_factory=list)
class RiskPredictionInput(BaseModel): age: Optional[int] = None; gender: Optional[str] = None; systolic_bp: Optional[float] = None; diastolic_bp: Optional[float] = None; cholesterol_total: Optional[float] = None; hdl_cholesterol: Optional[float] = None; ldl_cholesterol: Optional[float] = None; triglycerides: Optional[float] = None; glucose_level: Optional[float] = None; has_diabetes_history: Optional[bool] = None; is_smoker: Optional[bool] = None; physical_activity_level: Optional[str] = None
class RiskPredictionOutput(BaseModel): risk_score: Optional[float] = None; risk_level: Optional[str] = None; prediction_date: str = Field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S")); model_version: Optional[str] = None; recommendations: Optional[List[str]] = Field(default_factory=list); confidence_interval: Optional[Dict[str, float]] = None