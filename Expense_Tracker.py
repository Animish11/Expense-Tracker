import argparse
import datetime
import os
import json
import csv

DATA_FILE = os.path.expanduser("~/.expense_tracker.json")

def load_expenses():
    """Load expenses from the JSON file."""
    try:
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return []
    except json.JSONDecodeError:
        print("Error: Data file is corrupted.")
        return []

def save_expenses(expenses):
    """Save expenses to the JSON file."""
    with open(DATA_FILE, 'w') as f:
        json.dump(expenses, f, indent=2)

def get_next_id(expenses):
    """Generate the next ID for a new expense."""
    if not expenses:
        return 1
    return max(expense['id'] for expense in expenses) + 1

def handle_add(args):
    """Handle adding a new expense."""
    if args.amount <= 0:
        print("Error: Amount must be a positive number.")
        return

    expenses = load_expenses()
    new_id = get_next_id(expenses)
    today = datetime.date.today().isoformat()
    new_expense = {
        'id': new_id,
        'date': today,
        'description': args.description,
        'amount': args.amount
    }
    expenses.append(new_expense)
    save_expenses(expenses)
    print(f"Expense added successfully (ID: {new_id})")

def handle_delete(args):
    """Handle deleting an expense by ID."""
    expenses = load_expenses()
    original_count = len(expenses)
    expenses = [e for e in expenses if e['id'] != args.id]
    if len(expenses) == original_count:
        print(f"Error: Expense with ID {args.id} not found.")
        return
    save_expenses(expenses)
    print("Expense deleted successfully")

def handle_update(args):
    """Handle updating an existing expense."""
    expenses = load_expenses()
    found = False
    for expense in expenses:
        if expense['id'] == args.id:
            found = True
            if args.description is not None:
                expense['description'] = args.description
            if args.amount is not None:
                if args.amount <= 0:
                    print("Error: Amount must be a positive number.")
                    return
                expense['amount'] = args.amount
            if args.date is not None:
                try:
                    datetime.datetime.strptime(args.date, '%Y-%m-%d')
                except ValueError:
                    print("Error: Invalid date format. Use YYYY-MM-DD.")
                    return
                expense['date'] = args.date
    if not found:
        print(f"Error: Expense with ID {args.id} not found.")
        return
    save_expenses(expenses)
    print("Expense updated successfully")

def handle_list(args):
    """List all expenses in a table format."""
    expenses = load_expenses()
    if not expenses:
        print("No expenses found.")
        return

    print("{:<4} {:<10} {:<20} {:<10}".format('ID', 'Date', 'Description', 'Amount'))
    for expense in expenses:
        amount = expense['amount']
        if isinstance(amount, float) and amount.is_integer():
            amount_str = f"${int(amount)}"
        else:
            amount_str = f"${amount:.2f}"
        description = expense['description'][:20]  # Truncate long descriptions
        print("{:<4} {:<10} {:<20} {:<10}".format(
            expense['id'],
            expense['date'],
            description,
            amount_str
        ))

def handle_summary(args):
    """Show summary of expenses, optionally filtered by month."""
    expenses = load_expenses()
    current_year = datetime.date.today().year

    if args.month:
        if args.month < 1 or args.month > 12:
            print("Error: Month must be between 1 and 12.")
            return

        filtered = []
        for expense in expenses:
            try:
                date = datetime.datetime.strptime(expense['date'], '%Y-%m-%d').date()
            except ValueError:
                continue  # Skip invalid dates
            if date.year == current_year and date.month == args.month:
                filtered.append(expense)
        total = sum(e['amount'] for e in filtered)
        month_name = datetime.date(1900, args.month, 1).strftime('%B')
    else:
        total = sum(e['amount'] for e in expenses)
        month_name = None

    if total.is_integer():
        formatted_total = f"${int(total)}"
    else:
        formatted_total = f"${total:.2f}"

    if month_name:
        print(f"Total expenses for {month_name}: {formatted_total}")
    else:
        print(f"Total expenses: {formatted_total}")

def handle_export(args):
    """Export expenses to a CSV file."""
    expenses = load_expenses()
    if not expenses:
        print("No expenses to export.")
        return

    try:
        with open(args.filename, 'w', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=['id', 'date', 'description', 'amount'])
            writer.writeheader()
            for expense in expenses:
                writer.writerow({
                    'id': expense['id'],
                    'date': expense['date'],
                    'description': expense['description'],
                    'amount': expense['amount']
                })
        print(f"Successfully exported {len(expenses)} expenses to {args.filename}")
    except PermissionError:
        print(f"Error: Permission denied to write to {args.filename}")
    except Exception as e:
        print(f"Error exporting expenses: {str(e)}")

def main():
    parser = argparse.ArgumentParser(description='Manage your expenses.')
    subparsers = parser.add_subparsers(dest='command', required=True)

    # Add command
    add_parser = subparsers.add_parser('add', help='Add a new expense')
    add_parser.add_argument('--description', required=True, help='Expense description')
    add_parser.add_argument('--amount', type=float, required=True, help='Expense amount')

    # Delete command
    del_parser = subparsers.add_parser('delete', help='Delete an expense')
    del_parser.add_argument('--id', type=int, required=True, help='ID of the expense to delete')

    # Update command
    update_parser = subparsers.add_parser('update', help='Update an expense')
    update_parser.add_argument('--id', type=int, required=True, help='ID of the expense to update')
    update_parser.add_argument('--description', help='New description')
    update_parser.add_argument('--amount', type=float, help='New amount')
    update_parser.add_argument('--date', help='New date (YYYY-MM-DD)')

    # List command
    subparsers.add_parser('list', help='List all expenses')

    # Summary command
    summary_parser = subparsers.add_parser('summary', help='Show expense summary')
    summary_parser.add_argument('--month', type=int, help='Filter by month (1-12)')

    # Export command
    export_parser = subparsers.add_parser('export', help='Export expenses to CSV')
    export_parser.add_argument(
        '--filename',
        default='expenses.csv',
        help='Output filename (default: expenses.csv)'
    )

    args = parser.parse_args()

    if args.command == 'add':
        handle_add(args)
    elif args.command == 'delete':
        handle_delete(args)
    elif args.command == 'update':
        handle_update(args)
    elif args.command == 'list':
        handle_list(args)
    elif args.command == 'summary':
        handle_summary(args)
    elif args.command == 'export':
        handle_export(args)

if __name__ == '__main__':
    main()
