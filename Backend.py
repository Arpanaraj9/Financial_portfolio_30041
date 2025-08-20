import psycopg2
import random
from decimal import Decimal
from datetime import date

# --- Database Connection ---
def get_db_connection():
    """Establishes a connection to the PostgreSQL database."""
    conn = psycopg2.connect(
        dbname="Finance",
        user="postgres",
        password="1234",
        host="localhost",
        port="5432"
    )
    return conn

# --- CRUD Operations for Assets and Transactions ---

def create_user_and_account(user_name="John Doe", user_email="john.doe@example.com", account_type="Brokerage", provider="Fictional Broker"):
    """
    Creates a user and a default account for the application.
    This is necessary to satisfy foreign key constraints for Assets and Transactions.
    """
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        # Check if user already exists
        cur.execute("SELECT user_id FROM Users WHERE email = %s", (user_email,))
        user_id = cur.fetchone()
        if not user_id:
            cur.execute("INSERT INTO Users (name, email) VALUES (%s, %s) RETURNING user_id", (user_name, user_email))
            user_id = cur.fetchone()[0]
            conn.commit()
            
        # Check if account already exists
        cur.execute("SELECT account_id FROM Accounts WHERE user_id = %s AND provider_name = %s", (user_id, provider))
        account_id = cur.fetchone()
        if not account_id:
            cur.execute(
                "INSERT INTO Accounts (user_id, account_type, provider_name) VALUES (%s, %s, %s) RETURNING account_id",
                (user_id, account_type, provider)
            )
            account_id = cur.fetchone()[0]
            conn.commit()
            
        return user_id, account_id
    except psycopg2.Error as e:
        conn.rollback()
        print(f"Error creating user/account: {e}")
        return None, None
    finally:
        cur.close()
        conn.close()

def create_asset_and_transaction(user_id, account_id, ticker, asset_class, purchase_date, shares, cost_basis):
    """
    Creates a new asset and its corresponding 'BUY' transaction.
    This handles the **CREATE** part of CRUD for new purchases.
    """
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        # Insert into Assets table
        cur.execute(
            """INSERT INTO Assets (account_id, ticker_symbol, asset_class, purchase_date, shares, cost_basis)
               VALUES (%s, %s, %s, %s, %s, %s) RETURNING asset_id""",
            (account_id, ticker, asset_class, purchase_date, Decimal(shares), Decimal(cost_basis))
        )
        asset_id = cur.fetchone()[0]

        # Insert into Transactions table
        total_amount = Decimal(shares) * Decimal(cost_basis)
        cur.execute(
            """INSERT INTO Transactions (asset_id, transaction_type, transaction_date, shares, amount)
               VALUES (%s, 'BUY', %s, %s, %s)""",
            (asset_id, purchase_date, Decimal(shares), total_amount)
        )
        conn.commit()
        return "Asset and transaction created successfully."
    except psycopg2.Error as e:
        conn.rollback()
        return f"Error creating asset: {e}"
    finally:
        cur.close()
        conn.close()

def read_portfolio(account_id):
    """
    Reads all assets from a user's portfolio.
    This handles the **READ** part of CRUD.
    """
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            """SELECT asset_id, ticker_symbol, asset_class, shares, cost_basis, purchase_date
               FROM Assets WHERE account_id = %s""",
            (account_id,)
        )
        assets = cur.fetchall()
        
        # Simulate market data to calculate current value
        portfolio = []
        for asset in assets:
            asset_id, ticker, asset_class, shares, cost_basis, purchase_date = asset
            # Simulates real-time price; in a real app, this would be an API call
            current_price = cost_basis * Decimal(1 + (random.random() - 0.5) * 0.2)
            current_value = shares * current_price
            gain_loss = current_value - (shares * cost_basis)
            
            portfolio.append({
                'asset_id': asset_id,
                'Ticker': ticker,
                'Asset Class': asset_class,
                'Shares': shares,
                'Cost Basis': f"{cost_basis:.2f}",
                'Purchase Date': purchase_date,
                'Current Price': f"{current_price:.2f}",
                'Current Value': f"{current_value:.2f}",
                'Gain/Loss': f"{gain_loss:.2f}"
            })
        return portfolio
    except psycopg2.Error as e:
        return f"Error reading portfolio: {e}"
    finally:
        cur.close()
        conn.close()

def update_asset(asset_id, new_shares=None, new_cost_basis=None):
    """
    Updates the shares or cost basis of an existing asset.
    This handles the **UPDATE** part of CRUD.
    """
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        query = "UPDATE Assets SET "
        params = []
        updates = []
        if new_shares is not None:
            updates.append("shares = %s")
            params.append(Decimal(new_shares))
        if new_cost_basis is not None:
            updates.append("cost_basis = %s")
            params.append(Decimal(new_cost_basis))
        
        query += ", ".join(updates)
        query += " WHERE asset_id = %s"
        params.append(asset_id)
        
        cur.execute(query, params)
        conn.commit()
        return f"Asset {asset_id} updated successfully."
    except psycopg2.Error as e:
        conn.rollback()
        return f"Error updating asset: {e}"
    finally:
        cur.close()
        conn.close()

def delete_asset(asset_id):
    """
    Deletes an asset and all its associated transactions.
    This handles the **DELETE** part of CRUD.
    """
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        # The ON DELETE CASCADE constraint in the Transactions table will handle this automatically
        # by deleting associated transactions when the asset is deleted.
        cur.execute("DELETE FROM Assets WHERE asset_id = %s", (asset_id,))
        conn.commit()
        return f"Asset {asset_id} deleted successfully."
    except psycopg2.Error as e:
        conn.rollback()
        return f"Error deleting asset: {e}"
    finally:
        cur.close()
        conn.close()
        
# --- Business Insights ---

def get_insights(account_id):
    """
    Calculates portfolio-wide metrics and a breakdown by asset class.
    """
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        # Get all assets to calculate total value and allocation
        cur.execute(
            """SELECT asset_id, asset_class, shares, cost_basis
               FROM Assets WHERE account_id = %s""",
            (account_id,)
        )
        assets = cur.fetchall()
        
        total_value = Decimal(0)
        total_cost_basis = Decimal(0)
        asset_allocation = {}
        
        for asset in assets:
            asset_id, asset_class, shares, cost_basis = asset
            # Simulate real-time price
            current_price = cost_basis * Decimal(1 + (random.random() - 0.5) * 0.2)
            current_value = shares * current_price
            
            total_value += current_value
            total_cost_basis += shares * cost_basis
            
            if asset_class not in asset_allocation:
                asset_allocation[asset_class] = Decimal(0)
            asset_allocation[asset_class] += current_value
            
        total_gain_loss = total_value - total_cost_basis
        
        return {
            'total_value': total_value,
            'total_gain_loss': total_gain_loss,
            'asset_allocation': asset_allocation
        }
    except psycopg2.Error as e:
        return f"Error getting insights: {e}"
    finally:
        cur.close()
        conn.close()

