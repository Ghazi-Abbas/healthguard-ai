from sqlalchemy.orm import configure_mappers

from app.models.member import Member
from app.models.member_coverage import MemberCoverage
from app.models.authorization import Authorization


# Configure all SQLAlchemy relationships
configure_mappers()

# Print model names
print("Member model:", Member.__tablename__)
print("Coverage model:", MemberCoverage.__tablename__)
print("Authorization model:", Authorization.__tablename__)

print("All SQLAlchemy relationships configured successfully!")
