from flask import Flask
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SECRET_KEY'] = 'test-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///final_working_v2.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class ClientDocument(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    document_type = db.Column(db.String(50), nullable=False)
    description = db.Column(db.String(200))
    filename = db.Column(db.String(255))
    original_filename = db.Column(db.String(255))
    file_size = db.Column(db.Integer)
    client_id = db.Column(db.Integer, nullable=False)
    case_id = db.Column(db.Integer)
    created_at = db.Column(db.DateTime)

@app.route('/')
def test():
    try:
        # Test the query that was causing the error
        count = ClientDocument.query.count()
        return f"Success! Found {count} documents in the database."
    except Exception as e:
        return f"Error: {str(e)}"

if __name__ == '__main__':
    print("Testing database connection...")
    app.run(debug=True, port=5001)
