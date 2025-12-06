from typing import Annotated, Optional, List
from annotated_types import Ge, Le
from pydantic import BaseModel, EmailStr, Field, StringConstraints, ConfigDict 
 
NameStr = Annotated[str, StringConstraints(min_length=2, max_length=50)] 
StudentId = Annotated[str, StringConstraints(pattern=r"^G00\d{6}")] 
AgeInt = Annotated[int, Ge(16), Le(100)]
PhoneStr = Annotated[str, StringConstraints(pattern=r'^\+353\s0[0-9]{2}\s[0-9]{3}\s[0-9]{4}$')] #Irish phone number format: "+353 0xx xxx xxxx"
AddrStr = Annotated[str, StringConstraints(min_length=8, max_length=100)]
AptInt = Annotated[int, Ge(0), Le(999999)]
CountyStr = Annotated[str, StringConstraints(min_length=4, max_length=15)] 
PostCodeStr = Annotated[str, StringConstraints(pattern=r'^[A-Z0-9]{3}\s?[A-Z0-9]{4}$')] # e.g. "D02 X285" or "A65F4E2"
 

 #----------- User Schemas -------------
class UserCreate(BaseModel): 
    first_name: NameStr 
    last_name: NameStr #use the same annotation for names
    email: EmailStr
    phone: PhoneStr 
    age: AgeInt 
    student_id: StudentId 
 
class UserRead(BaseModel): 
    model_config = ConfigDict(from_attributes=True)
    id: int 
    first_name: NameStr 
    last_name: NameStr 
    email: EmailStr
    phone: PhoneStr 
    age: AgeInt 
    student_id: StudentId 

class UserUpdate(BaseModel): #Optional is for PATCH endpoints
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    age: Optional[int] = None
    student_id: Optional[str] = None


#-------------- Address Schemas ------------------
class AddressRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    address_line1: AddrStr
    address_line2: Optional[AddrStr] = None
    apartment_block_number: Optional[AptInt] = None
    county: CountyStr
    post_code: PostCodeStr
    resident_id: int

class UserReadWithAddress(UserRead):
    adresses: List[AddressRead] = []

class AddressReadWithOwner(AddressRead):
    resident: Optional["UserRead"] = None # use selectinload(ProjectDB.owner) when querying

class AddressCreate(BaseModel): 
    address_line1: AddrStr
    address_line2: Optional[AddrStr] = None
    apartment_block_number: Optional[AptInt] = None
    county: CountyStr
    post_code: PostCodeStr
    resident_id: int

# Nested route: POST /api/users/{user_id}/address (owner implied by path), creating an address from user_id
class AddressCreateForUser(BaseModel):
    address_line1: AddrStr
    address_line2: Optional[AddrStr] = None
    apartment_block_number: Optional[AptInt] = None
    county: CountyStr
    post_code: PostCodeStr

class AddressUpdate(BaseModel):
    address_line1: Optional[AddrStr] = None
    address_line2: Optional[AddrStr] = None
    apartment_block_number: Optional[AptInt] = None
    county: Optional[CountyStr] = None
    post_code: Optional[PostCodeStr] = None
    resident_id: Optional[int] = None

