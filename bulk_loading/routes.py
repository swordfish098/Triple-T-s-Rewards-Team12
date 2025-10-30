from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, send_from_directory
from flask_login import login_required, current_user
from common.decorators import role_required
from models import Role, db, AuditLog
from werkzeug.utils import secure_filename
import os
from datetime import datetime
from bulk_loading.processor import BulkLoadProcessor

bulk_loading_bp = Blueprint('bulk_loading_bp', __name__, template_folder="../templates")

@bulk_loading_bp.route('/admin/bulk-loading', methods=['GET', 'POST'])
@role_required(Role.ADMINISTRATOR, redirect_to='auth.login')
def admin_bulk_loading():
    """
    Admin bulk loading page
    """
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file part', 'danger')
            return redirect(request.url)
            
        file = request.files['file']
        
        if file.filename == '':
            flash('No selected file', 'danger')
            return redirect(request.url)
            
        if file and _allowed_file(file.filename):
            try:
                # Read file content directly from memory without saving to disk
                file_content = file.read().decode('utf-8')
                
                # Process the file content directly
                processor = BulkLoadProcessor(file_content=file_content, mode='admin')
                results = processor.process_file()
                
                # Log the event
                _log_audit_event('bulk_load_processed', f"Processed bulk load file: {file.filename}, "
                                f"Total: {results['total']}, Success: {results['success']}, "
                                f"Failed: {results['failed']}, Organizations: {results['organizations_created']}, "
                                f"Sponsors: {results['sponsors_created']}, Drivers: {results['drivers_created']}")
                
                # Flash message with results
                flash(f"File processed. Total: {results['total']}, Success: {results['success']}, "
                      f"Failed: {results['failed']}, Organizations: {results['organizations_created']}, "
                      f"Sponsors created: {results['sponsors_created']}, Drivers created: {results['drivers_created']}", 'success')
                
                return render_template('administrator/bulk_loading.html', 
                                     results=results)
            except Exception as e:
                flash(f"Error processing file: {str(e)}", 'danger')
                return redirect(request.url)
        else:
            flash('File type not allowed. Please upload a .txt file.', 'danger')
            return redirect(request.url)
            
    return render_template('administrator/bulk_loading.html')

@bulk_loading_bp.route('/sponsor/bulk-loading', methods=['GET', 'POST'])
@role_required(Role.SPONSOR, redirect_to='auth.login')
def sponsor_bulk_loading():
    """
    Sponsor bulk loading page
    Sponsors can only create drivers and other sponsors, not organizations
    """
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file part', 'danger')
            return redirect(request.url)
            
        file = request.files['file']
        
        if file.filename == '':
            flash('No selected file', 'danger')
            return redirect(request.url)
            
        if file and _allowed_file(file.filename):
            try:
                # Read file content directly from memory without saving to disk
                file_content = file.read().decode('utf-8')
                
                # Process the file content directly in sponsor mode
                processor = BulkLoadProcessor(file_content=file_content, mode='sponsor')
                results = processor.process_file()
                
                # Log the event
                _log_audit_event('sponsor_bulk_load_processed', f"Sponsor {current_user.USERNAME} processed bulk load file: {file.filename}, "
                                f"Total: {results['total']}, Success: {results['success']}, "
                                f"Failed: {results['failed']}, Sponsors: {results['sponsors_created']}, "
                                f"Drivers: {results['drivers_created']}")
                
                # Flash message with results
                flash(f"File processed. Total: {results['total']}, Success: {results['success']}, "
                      f"Failed: {results['failed']}, Sponsors created: {results['sponsors_created']}, "
                      f"Drivers created: {results['drivers_created']}", 'success')
                
                return render_template('sponsor/bulk_loading.html', 
                                     results=results)
            except Exception as e:
                flash(f"Error processing file: {str(e)}", 'danger')
                return redirect(request.url)
        else:
            flash('File type not allowed. Please upload a .txt file.', 'danger')
            return redirect(request.url)
            
    return render_template('sponsor/bulk_loading.html')

# Log download functionality removed - logs are now stored in AUDIT_LOG table

@bulk_loading_bp.route('/view-logs')
@role_required(Role.ADMINISTRATOR, redirect_to='auth.login')
def view_logs():
    """
    View bulk loading audit logs
    """
    # Get all bulk loading related audit logs
    logs = AuditLog.query.filter(
        AuditLog.EVENT_TYPE.like('bulk_load%')
    ).order_by(AuditLog.CREATED_AT.desc()).limit(100).all()
    
    return render_template('administrator/bulk_loading_logs.html', logs=logs)

@bulk_loading_bp.route('/download-template')
@role_required(Role.ADMINISTRATOR, Role.SPONSOR, redirect_to='auth.login')
def download_template():
    """
    Download template file
    """
    if current_user.USER_TYPE == Role.ADMINISTRATOR:
        template_name = 'admin_bulk_template.txt'
    else:
        template_name = 'sponsor_bulk_template.txt'
        
    templates_dir = os.path.join(current_app.root_path, 'bulk_loading', 'templates')
    return send_from_directory(templates_dir, template_name, as_attachment=True)

def _allowed_file(filename):
    """
    Check if file extension is allowed
    """
    return '.' in filename and filename.rsplit('.', 1)[1].lower() == 'txt'

def _log_audit_event(event_type, details):
    """
    Log an audit event
    """
    log_entry = AuditLog(
        EVENT_TYPE=event_type,
        DETAILS=details,
        CREATED_AT=datetime.utcnow()
    )
    db.session.add(log_entry)
    db.session.commit()