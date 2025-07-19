import os
from app import create_app, db
from app.models import User, Client, Case, Appointment, Invoice, Document
from flask_migrate import upgrade

app = create_app(os.getenv('FLASK_CONFIG') or 'default')

@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'User': User, 'Client': Client, 'Case': Case, 
            'Appointment': Appointment, 'Invoice': Invoice, 'Document': Document}

@app.cli.command()
def deploy():
    """Run deployment tasks."""
    # Create database tables
    upgrade()
    
    # Create upload directories
    upload_dir = app.config['UPLOAD_FOLDER']
    if not os.path.exists(upload_dir):
        os.makedirs(upload_dir)
        os.makedirs(os.path.join(upload_dir, 'documents'))
        os.makedirs(os.path.join(upload_dir, 'avatars'))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
