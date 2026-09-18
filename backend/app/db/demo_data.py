"""Carga idempotente de dados fictícios para demonstração local."""
from datetime import date, datetime, timedelta

from app.db.session import SessionLocal
from app.models import (
    Appointment,
    AppointmentStatus,
    Branch,
    Company,
    Customer,
    FinanceEntry,
    FinanceEntryStatus,
    FinanceEntryType,
    StockItem,
    Supplier,
    Vehicle,
    WorkOrder,
    WorkOrderStatus,
)


def main() -> None:
    db = SessionLocal()
    try:
        company = db.query(Company).filter(Company.name == "Oficina Demonstração").one()
        branch = db.query(Branch).filter(Branch.company_id == company.id).first()

        customers = [
            ("Ana Souza", "ana.demo@exemplo.local", "11999990001", "ABC1D23", "Toyota", "Corolla"),
            ("Bruno Lima", "bruno.demo@exemplo.local", "11999990002", "DEF4G56", "Honda", "Civic"),
            ("Carla Mendes", "carla.demo@exemplo.local", "11999990003", "HIJ7K89", "Volkswagen", "T-Cross"),
        ]
        customer_rows = []
        for name, email, phone, plate, brand, model in customers:
            customer = db.query(Customer).filter(Customer.company_id == company.id, Customer.email == email).first()
            if not customer:
                customer = Customer(
                    company_id=company.id,
                    name=name,
                    email=email,
                    phone=phone,
                    document="",
                    address="Rua de Demonstração, 100",
                    notes="Cadastro fictício para treinamento.",
                )
                db.add(customer)
                db.flush()
            vehicle = db.query(Vehicle).filter(Vehicle.company_id == company.id, Vehicle.plate == plate).first()
            if not vehicle:
                vehicle = Vehicle(
                    company_id=company.id,
                    customer_id=customer.id,
                    plate=plate,
                    brand=brand,
                    model=model,
                    year=2022,
                    color="Prata",
                    km=45000,
                )
                db.add(vehicle)
                db.flush()
            customer_rows.append((customer, vehicle))

        stock_specs = [
            ("DEMO-OLEO", "Óleo sintético 5W30", 12, 4, 42.90, 79.90),
            ("DEMO-FILTRO", "Filtro de óleo", 3, 5, 18.50, 39.90),
            ("DEMO-PASTILHA", "Pastilha de freio dianteira", 8, 2, 95.00, 189.90),
        ]
        stock_rows = []
        for sku, name, quantity, minimum, cost, sale in stock_specs:
            item = db.query(StockItem).filter(StockItem.company_id == company.id, StockItem.sku == sku).first()
            if not item:
                item = StockItem(
                    company_id=company.id,
                    branch_id=branch.id if branch else None,
                    sku=sku,
                    name=name,
                    unit="un",
                    quantity=quantity,
                    min_quantity=minimum,
                    cost_price=cost,
                    sale_price=sale,
                    notes="Item fictício para demonstração.",
                )
                db.add(item)
                db.flush()
            stock_rows.append(item)

        supplier = db.query(Supplier).filter(Supplier.company_id == company.id, Supplier.name == "Auto Peças Demo").first()
        if not supplier:
            supplier = Supplier(
                company_id=company.id,
                name="Auto Peças Demo",
                document="00.000.000/0001-00",
                phone="1133334444",
                email="fornecedor.demo@exemplo.local",
            )
            db.add(supplier)
            db.flush()

        if not db.query(Appointment).filter(Appointment.company_id == company.id).first():
            for index, (customer, vehicle) in enumerate(customer_rows):
                db.add(
                    Appointment(
                        company_id=company.id,
                        branch_id=branch.id if branch else None,
                        customer_id=customer.id,
                        vehicle_id=vehicle.id,
                        scheduled_at=datetime.now() + timedelta(days=index + 1, hours=9),
                        duration_minutes=60,
                        status=(
                            AppointmentStatus.SCHEDULED,
                            AppointmentStatus.CONFIRMED,
                            AppointmentStatus.IN_PROGRESS,
                        )[index],
                        service_type=("Revisão periódica", "Troca de óleo", "Inspeção de freios")[index],
                        notes="Agendamento fictício para treinamento.",
                    )
                )

        if not db.query(WorkOrder).filter(WorkOrder.company_id == company.id).first():
            for index, (customer, vehicle) in enumerate(customer_rows):
                db.add(
                    WorkOrder(
                        company_id=company.id,
                        branch_id=branch.id if branch else None,
                        customer_id=customer.id,
                        vehicle_id=vehicle.id,
                        status=(WorkOrderStatus.OPEN, WorkOrderStatus.IN_PROGRESS, WorkOrderStatus.DONE)[index],
                        description=("Revisão geral", "Troca de óleo e filtros", "Troca de pastilhas")[index],
                        diagnosis="Ordem fictícia para demonstração.",
                        labor_value=(180, 120, 250)[index],
                        next_revision_date=date.today() + timedelta(days=90),
                        closed_at=datetime.now() if index == 2 else None,
                    )
                )
        else:
            completed_demo_order = (
                db.query(WorkOrder)
                .filter(
                    WorkOrder.company_id == company.id,
                    WorkOrder.status == WorkOrderStatus.DONE,
                    WorkOrder.description == "Troca de pastilhas",
                )
                .first()
            )
            if completed_demo_order and completed_demo_order.closed_at is None:
                completed_demo_order.closed_at = datetime.now()

        if not db.query(FinanceEntry).filter(FinanceEntry.company_id == company.id).first():
            db.add(
                FinanceEntry(
                    company_id=company.id,
                    branch_id=branch.id if branch else None,
                    type=FinanceEntryType.RECEIVABLE,
                    status=FinanceEntryStatus.PENDING,
                    category="Serviço",
                    description="Revisão periódica — Ana Souza",
                    amount=480,
                    due_date=date.today() + timedelta(days=7),
                    customer_id=customer_rows[0][0].id,
                )
            )
            db.add(
                FinanceEntry(
                    company_id=company.id,
                    branch_id=branch.id if branch else None,
                    type=FinanceEntryType.PAYABLE,
                    status=FinanceEntryStatus.PENDING,
                    category="Fornecedor",
                    description="Compra de peças — Auto Peças Demo",
                    amount=320,
                    due_date=date.today() + timedelta(days=14),
                )
            )

        db.commit()
        print("Dados fictícios carregados com sucesso.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
