from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.printer_assignment import PrinterAssignment


class PrinterAssignmentRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_paper_size(self, paper_size: str) -> PrinterAssignment | None:
        return self.db.get(PrinterAssignment, paper_size)

    def get_all(self) -> list[PrinterAssignment]:
        statement = select(PrinterAssignment).order_by(
            PrinterAssignment.paper_size
        )
        return list(self.db.scalars(statement).all())

    def save(self, paper_size: str, printer_name: str) -> PrinterAssignment:
        assignment = self.get_by_paper_size(paper_size)
        if assignment is None:
            assignment = PrinterAssignment(
                paper_size=paper_size,
                printer_name=printer_name,
            )
            self.db.add(assignment)
        else:
            assignment.printer_name = printer_name

        self.db.flush()
        return assignment