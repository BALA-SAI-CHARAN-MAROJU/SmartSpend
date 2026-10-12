import random
from datetime import date, timedelta
from pathlib import Path
from models.schemas import TransactionCreate, BudgetCreate, SavingsGoalCreate
from services.transaction_service import TransactionService
from services.budget_service import BudgetService
from services.savings_service import SavingsService
from database.initialization import initialize_database
import config

def seed_sample_dataset(db_path: Path | str | None = None, days_back: int = 90) -> int:
    initialize_database(db_path)
    tx_service = TransactionService(db_path)
    budget_service = BudgetService(db_path)
    savings_service = SavingsService(db_path)

    if tx_service.count_transactions() > 10:
        return 0

    random.seed(config.RANDOM_SEED)
    today = date.today()
    start_date = today - timedelta(days=days_back)
    tx_count = 0

    current = start_date
    while current <= today:
        if current.day == 1:
            tx_service.add_transaction(TransactionCreate(
                transaction_date=current,
                transaction_type="income",
                amount=75000.0,
                category="Salary",
                description="Monthly Salary Credit",
                payment_method="Bank Transfer",
                merchant="Acme Corp"
            ))
            tx_count += 1

            rent_date = min(today, current + timedelta(days=1))
            tx_service.add_transaction(TransactionCreate(
                transaction_date=rent_date,
                transaction_type="expense",
                amount=18000.0,
                category="Rent",
                description="Monthly Apartment Rent",
                payment_method="Bank Transfer",
                merchant="Landlord"
            ))
            tx_count += 1

            bills_date = min(today, current + timedelta(days=4))
            tx_service.add_transaction(TransactionCreate(
                transaction_date=bills_date,
                transaction_type="expense",
                amount=2400.0,
                category="Bills",
                description="Electricity & Fiber Internet",
                payment_method="UPI",
                merchant="Airtel Broadband"
            ))
            tx_count += 1

        if current.day == 15 and current.month % 2 == 0:
            tx_service.add_transaction(TransactionCreate(
                transaction_date=current,
                transaction_type="income",
                amount=15000.0,
                category="Freelance",
                description="Web Design Consulting",
                payment_method="Bank Transfer",
                merchant="Client Studio"
            ))
            tx_count += 1

        is_weekend = current.weekday() in [5, 6]
        if random.random() < (0.85 if is_weekend else 0.65):
            food_amt = round(random.uniform(250, 1200 if is_weekend else 600), 2)
            merchant = random.choice(["Swiggy", "Zomato", "Starbucks", "Local Bistro", "Chai Point"])
            tx_service.add_transaction(TransactionCreate(
                transaction_date=current,
                transaction_type="expense",
                amount=food_amt,
                category="Food",
                description=f"Dining at {merchant}",
                payment_method="UPI",
                merchant=merchant
            ))
            tx_count += 1

        if is_weekend and random.random() < 0.70:
            groc_amt = round(random.uniform(800, 3200), 2)
            tx_service.add_transaction(TransactionCreate(
                transaction_date=current,
                transaction_type="expense",
                amount=groc_amt,
                category="Groceries",
                description="Weekly supermarket haul",
                payment_method="Credit Card",
                merchant=random.choice(["Blinkit", "BigBasket", "Nature's Basket", "Reliance Fresh"])
            ))
            tx_count += 1

        if not is_weekend and random.random() < 0.60:
            trans_amt = round(random.uniform(80, 450), 2)
            tx_service.add_transaction(TransactionCreate(
                transaction_date=current,
                transaction_type="expense",
                amount=trans_amt,
                category="Transport",
                description="City commute / Metro / Cab",
                payment_method="UPI",
                merchant=random.choice(["Uber", "Ola", "Metro Rail", "Fuel Station"])
            ))
            tx_count += 1

        if random.random() < 0.15:
            shop_cat = random.choice(["Shopping", "Entertainment", "Health", "Personal Care"])
            shop_amt = round(random.uniform(500, 4500), 2)
            tx_service.add_transaction(TransactionCreate(
                transaction_date=current,
                transaction_type="expense",
                amount=shop_amt,
                category=shop_cat,
                description=f"Purchase in {shop_cat}",
                payment_method=random.choice(["Credit Card", "UPI", "Debit Card"]),
                merchant=random.choice(["Amazon", "Myntra", "BookMyShow", "Apollo Pharmacy"])
            ))
            tx_count += 1

        current += timedelta(days=1)

    first_of_this_month = date(today.year, today.month, 1)
    if today.month == 12:
        end_of_this_month = date(today.year + 1, 1, 1) - timedelta(days=1)
    else:
        end_of_this_month = date(today.year, today.month + 1, 1) - timedelta(days=1)

    try:
        budget_service.set_budget(BudgetCreate(
            category="Food",
            budget_amount=12000.0,
            period_type="monthly",
            start_date=first_of_this_month,
            end_date=end_of_this_month
        ))
        budget_service.set_budget(BudgetCreate(
            category="Groceries",
            budget_amount=10000.0,
            period_type="monthly",
            start_date=first_of_this_month,
            end_date=end_of_this_month
        ))
        budget_service.set_budget(BudgetCreate(
            category="Rent",
            budget_amount=20000.0,
            period_type="monthly",
            start_date=first_of_this_month,
            end_date=end_of_this_month
        ))
        budget_service.set_budget(BudgetCreate(
            category="Transport",
            budget_amount=5000.0,
            period_type="monthly",
            start_date=first_of_this_month,
            end_date=end_of_this_month
        ))
    except Exception:
        pass

    try:
        savings_service.add_goal(SavingsGoalCreate(
            goal_name="Emergency Reserve Fund",
            target_amount=150000.0,
            current_amount=95000.0,
            target_date=today + timedelta(days=120),
            description="6 months of essential living expenses"
        ))
        savings_service.add_goal(SavingsGoalCreate(
            goal_name="New Laptop & Workstation",
            target_amount=120000.0,
            current_amount=60000.0,
            target_date=today + timedelta(days=60),
            description="MacBook Pro upgrade for development"
        ))
        savings_service.add_goal(SavingsGoalCreate(
            goal_name="Annual Vacation",
            target_amount=50000.0,
            current_amount=22000.0,
            target_date=today + timedelta(days=180),
            description="Trip to Himachal Pradesh"
        ))
    except Exception:
        pass

    return tx_count
