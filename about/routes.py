import os
import json
from datetime import datetime, timedelta
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from extensions import db
from models import AboutInfo, Role
from common.decorators import role_required
from forms import AboutForm

about_bp = Blueprint("about_bp", __name__, template_folder="../templates")

# Public view (everyone)
@about_bp.route('/about')
def view_about():
    about_info = AboutInfo.query.get(2)  # Get the last (or only) record
    return render_template('about/dashboard.html', about_info=about_info)

def should_update_version(last_release_date: datetime) -> bool:
    """Check if a week has passed since the last release"""
    if not last_release_date:
        return True
    time_since_release = datetime.now() - last_release_date
    return time_since_release >= timedelta(days=7)

def update_version():
    """Update version number and release date if a week has passed"""
    info = _get_singleton_about()
    
    if info is None:
        info = AboutInfo()
        info.team_num = 12
        info.product_name = "Team Twelve Trucking"
        info.product_desc = "Triple T Rewards Program"
        info.version_num = 1
        info.release_date = datetime.now()
    elif should_update_version(info.release_date):
        info.version_num += 1
        info.release_date = datetime.now()
    
    db.session.add(info)
    db.session.commit()

def _get_singleton_about() -> AboutInfo | None:
    return AboutInfo.query.order_by(AboutInfo.entry_id.desc()).first()


@about_bp.route("/administrator/about", methods=["GET", "POST"])
@role_required(Role.ADMINISTRATOR, allow_admin=False)
def edit_about():
    form = AboutForm()
    info = _get_singleton_about()

    if form.validate_on_submit():
        # Handle form submission
        if info is None:
            info = AboutInfo()
        info.team_num = form.team_num.data
        info.version_num = form.version_num.data
        info.product_name = form.product_name.data
        info.product_desc = form.product_desc.data
        db.session.add(info)
        db.session.commit()
        return redirect(url_for("about_bp.view_about"))

    # Pre-fill form with existing data
    if info and request.method == 'GET':
        form.team_num.data = info.team_num
        form.version_num.data = info.version_num
        form.product_name.data = info.product_name
        form.product_desc.data = info.product_desc

    return render_template("about/edit_about.html", form=form, info=info)