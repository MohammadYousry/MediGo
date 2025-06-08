from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional, Dict, Any, Union, Literal
from datetime import date, datetime
dt_date = date 

# في بداية ملف models/schema.py
# ... بعد كل سطور الـ import

# --- ADD THIS ENTIRE BLOCK ---
# ----------------- Literal Types from Clara's Schema -----------------
AllowedRoles = Literal["patient", "hospital", "laboratory", "radiology", "pharmacy", "clinic", "visitor"]
Gender = Literal["male", "female"]  # <--- هذا هو تعريف 'Gender' الذي سيحل المشكلة
BloodGroup = Literal["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"]
MaritalStatus = Literal["single", "married", "divorced", "widowed"]
AgeGroup = Literal["Young", "Middle-aged", "Older"]
SmokerStatus = Literal["Non-smoker", "Light smoker", "Moderate smoker", "Heavy smoker"]
BpCategory = Literal["Low", "Normal", "Elevated", "Stage 1", "Stage 2"]
BmiCategory = Literal["Underweight", "Normal", "Overweight", "Obese"]
# --------------------------------------------------------------------
# --- Helper Functions (Placeholders) ---
def fetch_patient_name(patient_national_id: str, db_session) -> Optional[str]:
    print(f"[Placeholder] fetch_patient_name called for {patient_national_id}")
    return "Patient Name (Placeholder)"

def resolve_added_by_name(added_by_id: str, db_session) -> Optional[str]:
    print(f"[Placeholder] resolve_added_by_name called for {added_by_id}")
    return "Added By Name (Placeholder)"

def calculate_age(birthdate_str: Optional[Union[str, date]]) -> Optional[int]:
    if not birthdate_str:
        return None
    try:
        birthdate = birthdate_str if isinstance(birthdate_str, date) else datetime.strptime(birthdate_str, "%Y-%m-%d").date()
        today = date.today()
        return today.year - birthdate.year - ((today.month, today.day) < (birthdate.month, birthdate.day))
    except Exception:
        return None

# --- Base Models ---
class BaseInput(BaseModel):
    notes: Optional[str] = None

class BaseRecord(BaseInput):
    record_id: str = Field(..., description="Unique ID for the record")
    patient_name: Optional[str] = None
    added_by_name: Optional[str] = None
    entry_date: Optional[str] = Field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    class Config:
        from_attributes = True

# --- User Models ---
class UserBase(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    national_id: str
    phone_number: Optional[str] = None
    gender: Optional[str] = None
    date_of_birth: Optional[Union[str, date]] = None
    address: Optional[str] = None
    city: Optional[str] = None
    region: Optional[str] = None
    blood_type: Optional[str] = None
    profile_picture_url: Optional[str] = None
    chronic_diseases: Optional[List[str]] = Field(default_factory=list)

class UserCreate(UserBase):
    password: str = Field(..., min_length=8)
    doctoremail: Optional[str] = None
    current_smoker: Optional[bool] = None
    cigs_per_day: Optional[int] = None

class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[str] = None
    gender: Optional[str] = None
    phone_number: Optional[str] = None
    region: Optional[str] = None
    city: Optional[str] = None
    address: Optional[str] = None
    date_of_birth: Optional[Union[str, date]] = None
    blood_type: Optional[str] = None
    current_smoker: Optional[bool] = None
    cigs_per_day: Optional[int] = None
    doctoremail: Optional[str] = None


class UserResponse(UserBase):
    user_id: str = Field(..., alias="national_id")
    age: Optional[int] = None
    is_active: Optional[bool] = True


class UserEmergencyInfo(UserBase):
    age: Optional[int] = None
    allergies: Optional[List[Dict[str, Any]]] = Field(default_factory=list)  # ✅✅✅ أضف هذا السطر
    surgeries: Optional[List[Dict[str, Any]]] = Field(default_factory=list)
    radiology: Optional[List[Dict[str, Any]]] = Field(default_factory=list)
    biomarkers: Optional[List[Dict[str, Any]]] = Field(default_factory=list)
    hypertension_stage: Optional[str] = None
    medications: Optional[List[Dict[str, Any]]] = Field(default_factory=list)
    emergency_contacts: Optional[List[Dict[str, Any]]] = Field(default_factory=list)
    profile_photo: Optional[str] = None
    diagnoses: Optional[List[Dict[str, Any]]] = Field(default_factory=list)
    family_history: Optional[List[Dict[str, Any]]] = Field(default_factory=list)
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
class QRCodeCreate(BaseModel):
    user_id: str
    expiration_date: str
    user_info: Optional[UserEmergencyInfo] = None

class QRCodeResponse(BaseModel):
    user_id: str
    last_accessed: str
    expiration_date: str
    qr_image: str
    qr_data: str
    image_url: Optional[str] = None

class QRCodeWithUserInfoResponse(BaseModel):
    user_id: str
    last_accessed: Optional[str] = None
    expiration_date: Optional[str] = None
    qr_image: Optional[str] = None
    image_url: Optional[str] = None
    user_info: Optional[UserEmergencyInfo] = None

# --- Doctor Assignment Models ---
class DoctorAssignmentBase(BaseModel):
    patient_national_id: str
    doctor_email: EmailStr
    assignment_date: Optional[str] = Field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    notes: Optional[str] = None

class DoctorAssignmentCreate(DoctorAssignmentBase): pass

class DoctorAssignment(DoctorAssignmentBase):
    assignment_id: str = Field(...)
    
    class Config:
        from_attributes = True


# --- Surgery Models ---
class SurgeryBase(BaseInput):
    surgery_name: str
    surgery_date: str
    hospital_name: Optional[str] = None
    doctor_name: Optional[str] = None
    added_by: str  # ✅ أضف هذا السطر
class SurgeryCreate(SurgeryBase): pass
class SurgeryEntry(SurgeryBase, BaseRecord): # BaseRecord already has Config
    pass 

# --- BloodBiomarker Models ---
class TestResultItem(BaseModel): test_name: str; value: Any; unit: Optional[str] = None; reference_range: Optional[str] = None; flag: Optional[str] = None
class BloodBiomarkerInput(BaseInput):
    test_date: str = Field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d"))
    test_type: str
    results: List[TestResultItem]
    added_by: str  # ⬅️ أضفته فعلاً كويس ✅
class BloodBioMarker(BloodBiomarkerInput, BaseRecord): # BaseRecord already has Config
    pass

# --- HeightWeight Models ---
class HeightWeightBase(BaseInput): measurement_date: str = Field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d")); height_cm: Optional[float] = Field(None, gt=0); weight_kg: Optional[float] = Field(None, gt=0); bmi: Optional[float] = None
class HeightWeightCreate(HeightWeightBase): pass
class HeightWeight(HeightWeightBase, BaseRecord): # BaseRecord already has Config
    pass

# --- Radiology Models ---
class RadiologyTestBase(BaseInput):
    test_name: str
    test_date: str = Field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d"))
    body_part: Optional[str] = None
    findings: Optional[str] = None
    impression: Optional[str] = None

class RadiologyTestInput(RadiologyTestBase):
    added_by: str  # ✅ لازم تضيف السطر ده هنا

class RadiologyTest(RadiologyTestBase, BaseRecord):
    pass

# --- Hypertension Models ---
class HypertensionReading(BaseModel): systolic: int = Field(..., gt=0); diastolic: int = Field(..., gt=0); pulse: Optional[int] = Field(None, gt=0)
class HypertensionBase(BaseInput):
    reading_date: str = Field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    readings: HypertensionReading
    position: Optional[str] = None
    added_by: str  # ✅ أضف هذا السطر
class HypertensionCreate(HypertensionBase): pass
class HypertensionEntry(HypertensionBase, BaseRecord): # BaseRecord already has Config
    pass

# --- Medication Models ---
class MedicationBase(BaseInput):
    name: str
    dosage: Optional[str] = None
    frequency: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    reason: Optional[str] = None
    added_by: str  # ✅ أضف هذا السطر
    current: Optional[bool] = False

class MedicationCreate(MedicationBase):
    pass

class MedicationEntry(BaseModel):
    notes: Optional[str] = None  # ملاحظات
    record_id: str               # معرف السجل
    patient_name: str            # اسم المريض
    added_by_name: str           # اسم الشخص الذي أضاف السجل
    entry_date: str              # تاريخ الإدخال
    name: str                    # اسم الدواء
    dosage: str                  # جرعة الدواء
    frequency: str               # تكرار الدواء
    start_date: Optional[date] = None  # تاريخ بدء العلاج
    end_date: Optional[date] = None    # تاريخ انتهاء العلاج
    reason: Optional[str] = None      # السبب
    current: Optional[bool] = False    # هل الدواء قيد الاستخدام حاليًا؟
    certain_duration: Optional[bool] = True  # هل المدة العلاجية معينة؟

    class Config:
        from_attributes = True



# --- Diagnosis Models ---
class DiagnosisBase(BaseInput):
    diagnosis_code: Optional[str] = None
    diagnosis_description: str
    diagnosis_date: str = Field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d"))
    status: Optional[str] = None
    added_by: str  # ✅ أضف هذا السطر
class DiagnosisCreate(DiagnosisBase): pass
class DiagnosisEntry(BaseModel):
    notes: str
    record_id: str
    patient_name: str
    added_by_name: str
    entry_date: str
    diagnosis_code: str
    diagnosis_description: str
    diagnosis_date: str  # still string, will be parsed manually
    status: str


# --- Allergy Models ---
class AllergyBase(BaseInput):
    allergen: str
    reaction: Optional[str] = None
    severity: Optional[str] = None
    onset_date: Optional[str] = None
    added_by: str  # ✅ هذا السطر ضروري

class AllergyCreate(AllergyBase):
    pass

class Allergy(AllergyBase, BaseRecord):
    pass

# --- FamilyHistory Models ---
class FamilyHistoryBase(BaseInput): relative_name: Optional[str] = None; relationship: str; condition: str; age_at_diagnosis: Optional[int] = Field(None, gt=0)
class FamilyHistoryCreate(FamilyHistoryBase): pass
class FamilyHistoryEntry(FamilyHistoryBase, BaseRecord): # BaseRecord already has Config
    pass

# --- EmergencyContact Models ---
class EmergencyContactBase(BaseModel):
    name: str
    relationship: str
    phone_number: str
    added_by: str  # ✅ أضف هذا السطر
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
class DerivedFeatures(BaseModel):
    age_group: Optional[str]
    smoker_status: Optional[str]
    is_obese: Optional[bool]
    bp_category: Optional[str]
    bmi_category: Optional[str]
    bmi: Optional[float]
    pulse_pressure: Optional[float]
    male_smoker: Optional[bool]
    prediabetes_indicator: Optional[bool]
    insulin_resistance: Optional[bool]
    metabolic_syndrome: Optional[bool]

class TopFeatures(BaseModel):
    feature_name: str
    contribution_score: float
    disease_type: Optional[str] = None  # optional to allow flexibility

class RiskPredictionInput(BaseModel): age: Optional[int] = None; gender: Optional[str] = None; systolic_bp: Optional[float] = None; diastolic_bp: Optional[float] = None; cholesterol_total: Optional[float] = None; hdl_cholesterol: Optional[float] = None; ldl_cholesterol: Optional[float] = None; triglycerides: Optional[float] = None; glucose_level: Optional[float] = None; has_diabetes_history: Optional[bool] = None; is_smoker: Optional[bool] = None; physical_activity_level: Optional[str] = None
class RiskPredictionOutput(BaseModel):
    diabetes_risk: float  # نسبة مئوية
    hypertension_risk: float  # نسبة مئوية
    derived_features: DerivedFeatures
    input_values: Dict[str, Any]
    top_diabetes_features: List[TopFeatures]
    top_hypertension_features: List[TopFeatures]

class LegacyUserCreate(BaseModel):
    national_id: str
    password: str
    full_name: str
    profile_photo: Optional[str] = None
    birthdate: str = Field(..., example=dt_date.today().isoformat())
    phone_number: str
    email:str
    gender: Gender
    blood_group: BloodGroup
    marital_status: MaritalStatus
    address: str
    region: str
    city: str
    current_smoker: bool = False
    cigs_per_day: int = 0

    @field_validator("national_id")
    @classmethod
    def nid_valid(cls, v): return validate_national_id(v)

    @field_validator("phone_number")
    @classmethod
    def phone_valid(cls, v): return validate_phone_number(v)

    @field_validator("cigs_per_day")
    @classmethod
    def cigs_logic(cls, v, info):
        current_smoker = info.data.get("current_smoker")
        if current_smoker and v <= 0:
            raise ValueError("Smokers must have cigs_per_day > 0")
        if not current_smoker and v != 0:
            raise ValueError("Non-smokers must have cigs_per_day = 0")
        return v

class LegacyUserResponse(BaseModel):
    national_id: str
    password: Optional[str] = None
    full_name: Optional[str] = None
    profile_photo: Optional[str] = None
    birthdate: Optional[str] = None
    phone_number: Optional[str] = None
    email: Optional[str] = None
    gender: Optional[str] = None
    blood_group: Optional[str] = None
    marital_status: Optional[str] = None
    address: Optional[str] = None
    region: Optional[str] = None
    city: Optional[str] = None
    current_smoker: Optional[bool] = None
    cigs_per_day: Optional[int] = None
    age: Optional[int] = None

# ----------------- Doctors -----------------
class LegacyDoctors(BaseModel):
    doctor_id: str
    password: str
    admin_id: str
    doctor_name: str
    specialization: str
    city: str
    region: str
    address: str
    email: EmailStr
    phone_number: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(egypt_tz))

class LegacyDoctorsCreateRequest(BaseModel):
    doctor_name: str
    specialization: str
    city: str
    region: str
    address: str
    email: EmailStr
    phone_number: str

# ----------------- Facility -----------------
class LegacyFacility(BaseModel):
    facility_id: str
    password: str
    admin_id: str
    facility_name: str
    city: str
    region: str
    address: str
    role: AllowedRoles
    access_scope: Dict[str, List[str]]
    email: EmailStr
    phone_number: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(egypt_tz))

    @field_validator("phone_number")
    @classmethod
    def phone_valid(cls, v): return validate_phone_number(v)

class LegacyFacilityPatientLink(BaseModel):
    facility_id: str
    patient_national_id: str

class LegacyFacilityCreateRequest(BaseModel):
    facility_name: str
    city: str
    region: str
    address: str
    role: str
    email: EmailStr
    phone_number: str

# ----------------- Emergency Contacts -----------------
class LegacyEmergencyContact(BaseModel):
    full_name: str
    relationship: str
    phone_number: str

    @field_validator("phone_number")
    @classmethod
    def phone_valid(cls, v): return validate_phone_number(v)

# ----------------- Doctor Assignments -----------------
class LegacyDoctorAssignment(BaseModel):
    doctor_email: str
    doctor_name: str
    patient_national_id: str
    
# ----------------- QR Code -----------------
class LegacyQRCodeCreate(BaseModel):
    user_id: str
    last_accessed: Optional[datetime] = None
    expiration_date: datetime
    qr_image: str

class LegacyQRCodeResponse(QRCodeCreate): pass

class LegacyVisitorQRCode(BaseModel):
    visitor_name: str
    qr_code_value: str

# ----------------- Allergies -----------------
class LegacyAllergy(BaseModel):
    allergen_name: str
    reaction_type: str
    severity: str
    notes: Optional[str] = None
    added_by: Optional[str] = None

# ----------------- Diagnosis -----------------
class LegacyDiagnosisEntry(BaseModel):
    disease_name: str
    diagnosis_date: dt_date
    diagnosed_by: str
    is_chronic: bool
    details_notes: Optional[str] = None
    added_by: Optional[str] = None

# ----------------- Family History -----------------
class LegacyFamilyHistoryEntry(BaseModel):
    disease_name: str
    age_of_onset: int
    relative_relationship: str
    notes: Optional[str] = None
    added_by: Optional[str] = None

# ----------------- Surgeries -----------------
class LegacySurgeryEntry(BaseModel):
    procedure_name: str
    surgeon_name: str
    surgery_date: dt_date
    procedure_notes: Optional[str] = None
    added_by: Optional[str] = None

# ----------------- Radiology -----------------
class LegacyRadiologyTestInput(BaseModel):
    radiology_name: str
    date: Optional[dt_date] = Field(default_factory=dt_date.today)
    report_notes: Optional[str] = None
    added_by: str

class LegacyRadiologyTest(RadiologyTestInput):
    patient_name: Optional[str] = None
    added_by_name: Optional[str] = None
    image_validity: Optional[bool] = None
    image_confidence: Optional[float] = None
    image_url: Optional[str] = None
    
# ----------------- Blood BioMarkers -----------------
class LegacyTestResultItem(BaseModel):
    item: str
    value: str
    reference_range: Optional[str] = None
    unit: Optional[str] = None
    flag: Optional[bool] = False

class LegacyBloodBiomarkerInput(BaseModel):
    test_name: str
    date: Optional[dt_date] = Field(default_factory=dt_date.today)
    results: List[TestResultItem]
    added_by: str

class LegacyBloodBioMarker(BloodBiomarkerInput):
    patient_name: Optional[str] = None
    added_by_name: Optional[str] = None
   
    # ----------------- Medications -----------------
class LegacyMedicationEntry(BaseModel):
    trade_name: str
    scientific_name: str
    dosage: str
    frequency: str
    certain_duration: bool
    start_date: Optional[dt_date] = None
    end_date: Optional[dt_date] = None
    current: bool
    prescribing_doctor: str
    notes: Optional[str] = None
    added_by: str
    bp_medication: Optional[bool] = None

    @model_validator(mode="after")
    def validate_dates_and_flags(cls, values):
        certain_duration = values.certain_duration
        current = values.current
        start_date = values.start_date
        end_date = values.end_date

        # ✅ Ensure mutual exclusivity
        if certain_duration == current:
            raise ValueError("Only one of 'certain_duration' or 'current' must be True.")

        if certain_duration:
            if not start_date or not end_date:
                raise ValueError("Start and end dates must be provided for medications taken for a certain duration.")
        elif current:
            if not start_date:
                raise ValueError("Start date must be provided for currently taken medications.")
            if end_date is not None:
                raise ValueError("End date must be left empty for current medications.")

        return values

# ----------------- Hypertension -----------------
class LegacyHypertensionEntry(BaseModel):
    sys_value: int
    dia_value: int
    added_by: Optional[str] = None

# ----------------- Measurements -----------------
class LegacyHeightWeightCreate(BaseModel):
    height: Optional[float] = None
    weight: Optional[float] = None
    added_by: Optional[str] = None

    @field_validator("height", "weight")
    @classmethod
    def validate_positive(cls, value):
        if value is not None and value <= 0:
            raise ValueError("Must be positive")
        return value

# ----------------- Risk Prediction -----------------
# ----------------- Radiology -----------------
class LegacyRadiologyTestInput(BaseModel):
    radiology_name: str
    date: Optional[dt_date] = Field(default_factory=dt_date.today)
    report_notes: Optional[str] = None
    added_by: str

class LegacyRadiologyTest(RadiologyTestInput):
    patient_name: Optional[str] = None
    added_by_name: Optional[str] = None
    image_validity: Optional[bool] = None
    image_confidence: Optional[float] = None
    image_filename: Optional[str] = None 

# ----------------- Blood BioMarkers -----------------
class LegacyTestResultItem(BaseModel):
    item: str
    value: str
    reference_range: Optional[str] = None
    unit: Optional[str] = None
    flag: Optional[bool] = False

class LegacyBloodBiomarkerInput(BaseModel):
    test_name: str
    date: Optional[dt_date] = Field(default_factory=dt_date.today)
    results: List[TestResultItem]
    added_by: str

class LegacyBloodBioMarker(BloodBiomarkerInput):
    patient_name: Optional[str] = None
    added_by_name: Optional[str] = None
    # ----------------- Medications -----------------

    @model_validator(mode="after")
    def validate_dates_and_flags(cls, values):
        certain_duration = values.certain_duration
        current = values.current
        start_date = values.start_date
        end_date = values.end_date

        # ✅ Ensure mutual exclusivity
        if certain_duration == current:
            raise ValueError("Only one of 'certain_duration' or 'current' must be True.")

        if certain_duration:
            if not start_date or not end_date:
                raise ValueError("Start and end dates must be provided for medications taken for a certain duration.")
        elif current:
            if not start_date:
                raise ValueError("Start date must be provided for currently taken medications.")
            if end_date is not None:
                raise ValueError("End date must be left empty for current medications.")

        return values

# ----------------- Risk Assessment -----------------
class LegacyDerivedFeatures(BaseModel):
    age_group: AgeGroup
    smoker_status: SmokerStatus
    is_obese: bool
    bp_category: BpCategory
    bmi_category: BmiCategory
    bmi: float
    pulse_pressure: float
    male_smoker: bool
    prediabetes_indicator: bool
    insulin_resistance: bool
    metabolic_syndrome: bool

class LegacyTopFeatures(BaseModel):
    feature_name: str
    contribution_score: float
    
class LegacyBiomarkerEntry(BaseModel):
    item: str
    value: float
    unit: Optional[str] = None

class LegacyRiskPredictionOutput(BaseModel):
    diabetes_risk: float
    hypertension_risk: float
    derived_features: DerivedFeatures
    input_values: dict
    top_diabetes_features: List[TopFeatures]
    top_hypertension_features: List[TopFeatures]
    biomarker_chart_data: Optional[List[BiomarkerEntry]] = None

class LegacyRiskAssessmentEntry(BaseModel):
    risk_category: str
    prediction_date: dt_date
    risk_score: int
    primary_risk_factors: str
    recommended_actions: str

# ----------------- Roles -----------------
class LegacyRoleCreate(BaseModel):
    role_name: str
    role_id: int
    access_scope: Dict[str, List[str]]

class LegacyRoleResponse(RoleCreate):
    pass

class LegacyQRCodeCreate(BaseModel):
    user_id: str
    last_accessed: str
    expiration_date: str
    qr_image: str

class LegacyQRCodeResponse(BaseModel):
    user_id: str
    last_accessed: str
    expiration_date: str
    qr_image: str
