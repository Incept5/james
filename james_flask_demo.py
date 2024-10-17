import sqlite3
from flask import Flask, render_template, request, send_file, abort
import pandas as pd
import io
from datetime import datetime

app = Flask(__name__)

def get_db_connection():
    conn = sqlite3.connect('forex_trades.db')
    conn.row_factory = sqlite3.Row
    return conn

def is_safe_sql(sql):
    # Basic SQL injection prevention
    unsafe_keywords = ['DROP', 'DELETE', 'TRUNCATE', 'ALTER', 'CREATE', 'INSERT', 'UPDATE']
    return not any(keyword in sql.upper() for keyword in unsafe_keywords)

@app.route('/', methods=['GET', 'POST'])
def index():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [table['name'] for table in cursor.fetchall()]

    selected_table = request.form.get('table') or request.args.get('table')
    sort_by = request.form.get('sort_by') or request.args.get('sort_by')
    sort_order = request.form.get('sort_order') or request.args.get('sort_order', 'asc')
    where_clause = request.form.get('where_clause') or request.args.get('where_clause', '')
    page = int(request.args.get('page', 1))
    per_page = 50

    columns = []
    rows = []
    total_rows = 0

    if selected_table:
        try:
            # Validate table name
            if selected_table not in tables:
                raise ValueError("Invalid table name")

            # Get columns
            cursor.execute(f"PRAGMA table_info({selected_table})")
            columns = [info[1] for info in cursor.fetchall()]

            # Validate sort_by
            if sort_by and sort_by not in columns:
                sort_by = None
                sort_order = 'asc'

            # Construct the base query
            query = f"SELECT * FROM {selected_table}"
            count_query = f"SELECT COUNT(*) FROM {selected_table}"

            # Add WHERE clause if provided and safe
            if where_clause and is_safe_sql(where_clause):
                query += f" WHERE {where_clause}"
                count_query += f" WHERE {where_clause}"

            # Add sorting
            if sort_by and sort_by != 'None':
                query += f" ORDER BY {sort_by} {sort_order.upper()}"

            # Count total rows
            cursor.execute(count_query)
            total_rows = cursor.fetchone()[0]

            # Add pagination
            query += f" LIMIT {per_page} OFFSET {(page - 1) * per_page}"

            # Execute the query
            cursor.execute(query)
            rows = cursor.fetchall()

        except sqlite3.Error as e:
            abort(500, description=f"Database error: {str(e)}")
        except ValueError as e:
            abort(400, description=str(e))

    conn.close()

    total_pages = (total_rows - 1) // per_page + 1

    return render_template('index.html',
                           tables=tables,
                           selected_table=selected_table,
                           columns=columns,
                           rows=rows,
                           sort_by=sort_by,
                           sort_order=sort_order,
                           where_clause=where_clause,
                           page=page,
                           total_pages=total_pages)

@app.route('/download_excel', methods=['POST'])
def download_excel():
    selected_table = request.form['table']
    sort_by = request.form.get('sort_by') or request.args.get('sort_by', '')
    sort_order = request.form.get('sort_order', 'asc')
    where_clause = request.form.get('where_clause', '')

    try:
        conn = get_db_connection()

        # Validate table name
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [table['name'] for table in cursor.fetchall()]
        if selected_table not in tables:
            raise ValueError("Invalid table name")

        query = f"SELECT * FROM {selected_table}"
        if where_clause and is_safe_sql(where_clause):
            query += f" WHERE {where_clause}"
        if sort_by and sort_by != 'None':
            query += f" ORDER BY {sort_by} {sort_order.upper()}"

        df = pd.read_sql_query(query, conn)
        conn.close()

        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, sheet_name=selected_table, index=False)

        output.seek(0)

        timestamp = datetime.now().strftime("%Y%m%dT%H%M%S")
        file_name = f"{selected_table}-{timestamp}.xlsx"

        return send_file(output, download_name=file_name, as_attachment=True)

    except (sqlite3.Error, ValueError) as e:
        abort(400, description=str(e))

@app.errorhandler(400)
@app.errorhandler(404)
@app.errorhandler(500)
def handle_error(error):
    return render_template('error.html', error=error), error.code

if __name__ == '__main__':
    app.run(debug=True)