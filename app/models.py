from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship 
from sqlalchemy import String, Integer, ForeignKey

class Base(DeclarativeBase): 
    pass 

class UserDB(Base): 
    __tablename__ = "users" 
    id: Mapped[int] = mapped_column(primary_key=True, index=True) 
    first_name: Mapped[str] = mapped_column(String, nullable=False) 
    last_name: Mapped[str] = mapped_column(String, nullable=False) 
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False) 
    phone: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    age: Mapped[int] = mapped_column(Integer, nullable=False) 
    student_id: Mapped[str] = mapped_column(String, unique=True, nullable=False) 
    address: Mapped[list["AddressDB"]] = relationship(back_populates="resident", cascade="all, delete-orphan")

class AddressDB(Base):
    __tablename__ = "address"
    id: Mapped[int] =  mapped_column(primary_key=True)
    address_line1: Mapped[str] = mapped_column(String, nullable=False)
    address_line2: Mapped[str] = mapped_column(String, nullable=True)
    apartment_block_number: Mapped[str] = mapped_column(String, nullable=True)
    county: Mapped[str] = mapped_column(String, nullable=False)
    post_code: Mapped[str] = mapped_column(String, nullable=False)
    resident_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    resident: Mapped[UserDB] =  relationship(back_populates="address")