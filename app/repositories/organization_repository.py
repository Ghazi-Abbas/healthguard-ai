from sqlalchemy.orm import Session
class OrganizationRepository:

    def __init__(self, db:Session):
        self.db = db

    def create(self, organization):
        self.db.add(organization)
        return organization
