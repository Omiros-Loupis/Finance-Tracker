import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
import os

class FinanceTracker:
    def __init__(self, db_name='finance_tracker.db'):
        """Initialize the finance tracker with SQLite database"""
        self.db_name = db_name
        self.conn = None
        self.connect()
        self.create_tables()
    
    def connect(self):
        """Establish database connection"""
        try:
            self.conn = sqlite3.connect(self.db_name)
        except sqlite3.Error as e:
            print(f"❌ Database connection error: {e}")
            raise
    
    def create_tables(self):
        """Create necessary tables if they don't exist"""
        cursor = self.conn.cursor()
        
        # Transactions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                type TEXT NOT NULL,
                category TEXT NOT NULL,
                amount REAL NOT NULL,
                description TEXT
            )
        ''')
        
        self.conn.commit()
    
    def add_transaction(self, trans_type, category, amount, description='', date=None):
        """Add a new transaction (income or expense)"""
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')
        else:
            try:
                datetime.strptime(date, '%Y-%m-%d')
            except ValueError:
                raise ValueError("❌ Date must be in 'YYYY-MM-DD' format")
                return 
        
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO transactions (date, type, category, amount, description)
            VALUES (?, ?, ?, ?, ?)
        ''', (date, trans_type, category, amount, description))
        
        self.conn.commit()
        print(f"✓ {trans_type.capitalize()} added: ${amount:.2f} - {category}")
    
    def get_all_transactions(self):
        """Retrieve all transactions as a pandas DataFrame"""
        query = "SELECT * FROM transactions ORDER BY date DESC"
        df = pd.read_sql_query(query, self.conn)
        return df
    
    def get_transactions_by_month(self, year, month):
        """Get transactions for a specific month"""
        query = '''
            SELECT * FROM transactions 
            WHERE strftime('%Y', date) = ? AND strftime('%m', date) = ?
            ORDER BY date DESC
        '''
        df = pd.read_sql_query(query, self.conn, params=(str(year), f'{month:02d}'))
        return df
    
    def get_summary(self, year=None, month=None):
        """Generate financial summary"""
        if year and month:
            df = self.get_transactions_by_month(year, month)
            period = f"{year}-{month:02d}"
        else:
            df = self.get_all_transactions()
            period = "All Time"
        
        if df.empty:
            print(f"\nNo transactions found for {period}")
            return
        
        income = df[df['type'] == 'income']['amount'].sum()
        expenses = df[df['type'] == 'expense']['amount'].sum()
        balance = income - expenses
        
        print(f"\n{'='*50}")
        print(f"FINANCIAL SUMMARY - {period}")
        print(f"{'='*50}")
        print(f"Total Income:    ${income:,.2f}")
        print(f"Total Expenses:  ${expenses:,.2f}")
        print(f"Net Balance:     ${balance:,.2f}")
        print(f"{'='*50}\n")
        
        return {'income': income, 'expenses': expenses, 'balance': balance}
    
    def get_category_breakdown(self, trans_type, year=None, month=None):
        """Get spending/income breakdown by category"""
        if year and month:
            df = self.get_transactions_by_month(year, month)
        else:
            df = self.get_all_transactions()
        
        df_filtered = df[df['type'] == trans_type]
        
        if df_filtered.empty:
            print(f"\nNo {trans_type} transactions found")
            return pd.DataFrame()
        
        breakdown = df_filtered.groupby('category')['amount'].agg(['sum', 'count']).round(2)
        breakdown.columns = ['Total', 'Count']
        breakdown = breakdown.sort_values('Total', ascending=False)
        
        print(f"\n{trans_type.upper()} BY CATEGORY:")
        print(breakdown)
        print()
        
        return breakdown
    
    def generate_monthly_report(self, year, month):
        """Generate comprehensive monthly report with visualizations"""
        df = self.get_transactions_by_month(year, month)
        
        if df.empty:
            print(f"\nNo transactions found for {year}-{month:02d}")
            return
        
        print(f"\n{'#'*60}")
        print(f"  MONTHLY REPORT: {year}-{month:02d}")
        print(f"{'#'*60}\n")
        
        # Summary
        summary = self.get_summary(year, month)
        
        # Category breakdowns
        expense_breakdown = self.get_category_breakdown('expense', year, month)
        income_breakdown = self.get_category_breakdown('income', year, month)
        
        # Generate charts
        self.plot_monthly_charts(expense_breakdown, income_breakdown, year, month)
        
        # Recent transactions
        print("\nRECENT TRANSACTIONS:")
        print(df[['date', 'type', 'category', 'amount', 'description']].head(10))
    
    def plot_monthly_charts(self, expense_df, income_df, year, month):
        """Create visualizations for monthly report"""
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        fig.suptitle(f'Financial Report: {year}-{month:02d}', fontsize=16, fontweight='bold')
        plt.show()
        plt.close(fig)
        
        # Expense Pie Chart
        if not expense_df.empty:
            axes[0, 0].pie(expense_df['Total'], labels=expense_df.index, autopct='%1.1f%%', startangle=90)
            axes[0, 0].set_title('Expenses by Category')
        else:
            axes[0, 0].text(0.5, 0.5, 'No Expense Data', ha='center', va='center')
            axes[0, 0].set_title('Expenses by Category')
        
        # Income Pie Chart
        if not income_df.empty:
            axes[0, 1].pie(income_df['Total'], labels=income_df.index, autopct='%1.1f%%', startangle=90)
            axes[0, 1].set_title('Income by Category')
        else:
            axes[0, 1].text(0.5, 0.5, 'No Income Data', ha='center', va='center')
            axes[0, 1].set_title('Income by Category')
        
        # Expense Bar Chart
        if not expense_df.empty:
            expense_df['Total'].plot(kind='bar', ax=axes[1, 0], color='crimson')
            axes[1, 0].set_title('Expense Breakdown')
            axes[1, 0].set_ylabel('Amount ($)')
            axes[1, 0].tick_params(axis='x', rotation=45)
        else:
            axes[1, 0].text(0.5, 0.5, 'No Expense Data', ha='center', va='center')
            axes[1, 0].set_title('Expense Breakdown')
        
        # Income Bar Chart
        if not income_df.empty:
            income_df['Total'].plot(kind='bar', ax=axes[1, 1], color='green')
            axes[1, 1].set_title('Income Breakdown')
            axes[1, 1].set_ylabel('Amount ($)')
            axes[1, 1].tick_params(axis='x', rotation=45)
        else:
            axes[1, 1].text(0.5, 0.5, 'No Income Data', ha='center', va='center')
            axes[1, 1].set_title('Income Breakdown')
        
        plt.tight_layout()
        
        # Save chart
        filename = f'report_{year}_{month:02d}.png'
        plt.savefig(filename, dpi=300, bbox_inches='tight')
        print(f"\n✓ Chart saved as '{filename}'")
        plt.show()
    
    def export_to_csv(self, filename='transactions_export.csv'):
        """Export all transactions to CSV file"""
        df = self.get_all_transactions()
        df.to_csv(filename, index=False)
        print(f"✓ Data exported to '{filename}'")
        
    def delete_transaction(self, transaction_id):
        """Delete a transaction by its ID"""
        try:
            cursor = self.conn.cursor()
            cursor.execute("DELETE FROM transactions WHERE id = ?", (transaction_id,))
            self.conn.commit()
            
            if cursor.rowcount > 0:
                print(f"✓ Transaction with ID {transaction_id} deleted successfully.")
                return True
            else:
                print(f"❌ No transaction found with ID {transaction_id}.")
                return False
        except sqlite3.Error as e:
            print(f"❌ Database error: {e}")
            return False
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            print("✓ Database connection closed")


def load_sample_data(tracker):
    """Load sample data only if database is empty"""
    df = tracker.get_all_transactions()
    if df.empty:
        print("\nAdding sample transactions for demonstration...")
        tracker.add_transaction('income', 'Salary', 5000, 'Monthly salary', '2024-11-01')
        tracker.add_transaction('income', 'Freelance', 800, 'Side project', '2024-11-15')
        tracker.add_transaction('expense', 'Rent', 1500, 'Monthly rent', '2024-11-01')
        tracker.add_transaction('expense', 'Groceries', 350, 'Weekly shopping', '2024-11-05')
        tracker.add_transaction('expense', 'Utilities', 150, 'Electric & water', '2024-11-10')
        tracker.add_transaction('expense', 'Transportation', 200, 'Gas & metro', '2024-11-12')
        tracker.add_transaction('expense', 'Entertainment', 120, 'Movies & dining', '2024-11-18')
        tracker.add_transaction('expense', 'Groceries', 280, 'Weekly shopping', '2024-11-20')
        print("✓ Sample data loaded!\n")


def main():
    """Main function with interactive menu"""
    tracker = FinanceTracker()
    
    # Add sample data only if database is empty
    load_sample_data(tracker)
    
    while True:
        print("\n" + "="*50)
        print("PERSONAL FINANCE TRACKER")
        print("="*50)
        print("1. Add Income")
        print("2. Add Expense")
        print("3. View All Transactions")
        print("4. View Summary")
        print("5. Category Breakdown")
        print("6. Generate Monthly Report")
        print("7. Export to CSV")
        print("8. Delete Transaction")
        print("9. Exit")
        print("="*50)
        
        choice = input("\nEnter your choice (1-9): ").strip()
        
        if choice == '1':
            try:
                category = input("Category (e.g., Salary, Freelance): ").strip()
                if not category:
                    print("❌ Category cannot be empty")
                    continue
                amount = float(input("Amount: $"))
                description = input("Description (optional): ").strip()
                tracker.add_transaction('income', category, amount, description)
            except ValueError as e:
                print(f"❌ Error: {e}")
        
        elif choice == '2':
            try:
                category = input("Category (e.g., Rent, Groceries, Entertainment): ").strip()
                if not category:
                    print("❌ Category cannot be empty")
                    continue
                amount = float(input("Amount: $"))
                description = input("Description (optional): ").strip()
                tracker.add_transaction('expense', category, amount, description)
            except ValueError as e:
                print(f"❌ Error: {e}")
        
        elif choice == '3':
            df = tracker.get_all_transactions()
            if df.empty:
                print("\n⚠️ No transactions found.")
            else:
                print("\n" + df.to_string(index=False))
        
        elif choice == '4':
            try:
                month_choice = input("View specific month? (y/n): ").lower()
                if month_choice == 'y':
                    year = int(input("Year (e.g., 2024): "))
                    month = int(input("Month (1-12): "))
                    if not (1 <= month <= 12):
                        print("❌ Month must be between 1 and 12")
                        continue
                    tracker.get_summary(year, month)
                else:
                    tracker.get_summary()
            except ValueError:
                print("❌ Invalid input. Please enter valid numbers.")
        
        elif choice == '5':
            try:
                trans_type = input("Type (income/expense): ").lower()
                if trans_type not in ['income', 'expense']:
                    print("❌ Type must be 'income' or 'expense'")
                    continue
                month_choice = input("View specific month? (y/n): ").lower()
                if month_choice == 'y':
                    year = int(input("Year (e.g., 2024): "))
                    month = int(input("Month (1-12): "))
                    if not (1 <= month <= 12):
                        print("❌ Month must be between 1 and 12")
                        continue
                    tracker.get_category_breakdown(trans_type, year, month)
                else:
                    tracker.get_category_breakdown(trans_type)
            except ValueError:
                print("❌ Invalid input. Please enter valid numbers.")
        
        elif choice == '6':
            try:
                year = int(input("Year (e.g., 2024): "))
                month = int(input("Month (1-12): "))
                if not (1 <= month <= 12):
                    print("❌ Month must be between 1 and 12")
                    continue
                tracker.generate_monthly_report(year, month)
            except ValueError:
                print("❌ Invalid input. Please enter valid numbers.")
        
        elif choice == '7':
            tracker.export_to_csv()
            
        elif choice == '8': 
            # NEW: Show recent transactions first so user can see IDs
            print("\n--- TRANSACTION LIST (Recent 10) ---")
            df = tracker.get_all_transactions()
            # Show ID column clearly
            print(df[['id', 'date', 'type', 'category', 'amount', 'description']].head(10).to_string(index=False))
            print("-" * 30)
            
            try:
                trans_id = input("\nEnter Transaction ID to delete (or Enter to cancel): ").strip()
                if trans_id:
                    tracker.delete_transaction(int(trans_id))
                else:
                    print("Deletion cancelled.")
            except ValueError:
                print("❌ Invalid ID format. Please enter a number.")    
        
        elif choice == '9':
            print("\nThank you for using Personal Finance Tracker!")
            tracker.close()
            break
        
        else:
            print("Invalid choice. Please try again.")
            
        if choice != '9':
            input("\nPress Enter to continue...")


if __name__ == "__main__":
    main()