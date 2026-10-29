import os
from flask import Blueprint, render_template, request, redirect, url_for, session, flash, send_file, current_app
from app.models import db, Lead, Project, User, Inquiry, ContactMessage, Subscriber, AuditLog
from app.routes.auth import login_required
from app.audit import log_action

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


@admin_bp.route("/dashboard")
@login_required()  # --- VULN-12: no role="admin" check here ---
def dashboard():
    total_leads = Lead.query.count()
    total_projects = Project.query.count()
    return render_template("admin/dashboard.html",
                            total_leads=total_leads, total_projects=total_projects)


@admin_bp.route("/leads")
@login_required()  # --- VULN-12: same missing role check ---
def all_leads():
    leads = Lead.query.all()
    return render_template("admin/leads.html", leads=leads)


@admin_bp.route("/projects", methods=["GET", "POST"])
@login_required()  # --- VULN-12: same missing role check ---
def projects():
    if request.method == "POST":
        project = Project(
            title=request.form["title"],
            location=request.form.get("location", ""),
            description=request.form.get("description", ""),
            price=request.form.get("price") or None,
            discount_price=request.form.get("discount_price") or None,
            discount_reason=request.form.get("discount_reason") or None,
        )

        # --- VULN-10 unrestricted project image upload
    
        file = request.files.get("cover_image")
        if file and file.filename:
            upload_dir = os.path.join(current_app.root_path, "static", "uploads", "properties")
            os.makedirs(upload_dir, exist_ok=True)
            save_path = os.path.join(upload_dir, file.filename)
            file.save(save_path)
            project.image_path = f"/static/uploads/properties/{file.filename}"
        
        db.session.add(project)
        db.session.flush()
        log_action("project_create", target_type="project", target_id=project.id,
                   after={"title": project.title, "price": str(project.price)})
        db.session.commit()
        flash("Project created.")
        return redirect(url_for("admin.projects"))

    all_projects = Project.query.all()
    return render_template("admin/projects.html", projects=all_projects)


@admin_bp.route("/projects/<int:project_id>/edit", methods=["GET", "POST"])
@login_required()  # --- VULN-12: same missing role check ---
def edit_project(project_id):
    project = Project.query.get_or_404(project_id)

    if request.method == "POST":
        before = {"title": project.title, "price": str(project.price), "discount_price": str(project.discount_price)}

        project.title = request.form.get("title", project.title)
        project.location = request.form.get("location", project.location)
        project.description = request.form.get("description", project.description)
        project.price = request.form.get("price") or project.price
        project.discount_price = request.form.get("discount_price") or None
        project.discount_reason = request.form.get("discount_reason") or None

        # --- VULN-10 
        file = request.files.get("cover_image")
        if file and file.filename:
            upload_dir = os.path.join(current_app.root_path, "static", "uploads", "properties")
            os.makedirs(upload_dir, exist_ok=True)
            save_path = os.path.join(upload_dir, file.filename)
            file.save(save_path)
            project.image_path = f"/static/uploads/properties/{file.filename}"

        after = {"title": project.title, "price": str(project.price), "discount_price": str(project.discount_price)}
        log_action("project_update", target_type="project", target_id=project.id, before=before, after=after)
        db.session.commit()
        flash("Listing updated.")
        return redirect(url_for("admin.projects"))

    return render_template("admin/project_edit.html", project=project)


@admin_bp.route("/projects/<int:project_id>/delete", methods=["POST"])
@login_required()  # --- VULN-12: same missing role check ---
def delete_project(project_id):
    # VULN-08b: no CSRF token here either -- an attacker could trick a
    # logged-in admin into deleting a listing via a forged cross-site request.
    project = Project.query.get_or_404(project_id)
    log_action("project_delete", target_type="project", target_id=project.id,
               before={"title": project.title})
    db.session.delete(project)
    db.session.commit()
    flash("Listing deleted.")
    return redirect(url_for("admin.projects"))


@admin_bp.route("/reports")
@login_required()  # --- VULN-12: same missing role check ---
def reports():
    start = request.args.get("start", "")
    end = request.args.get("end", "")

    if start and end:
        # --- VULN-01c: SQL Injection  Date range filter concatenated directly into raw SQL.
        raw_query = (
            "SELECT status, COUNT(*) AS total FROM leads "
            f"WHERE registration_date BETWEEN '{start}' AND '{end}' "
            "GROUP BY status"
        )
        results = db.session.execute(db.text(raw_query)).fetchall()
    else:
        # No filter submitted yet -- show all leads grouped by status.
        results = db.session.execute(
            db.text("SELECT status, COUNT(*) AS total FROM leads GROUP BY status")
        ).fetchall()
    return render_template("admin/reports.html", results=results, start=start, end=end)


@admin_bp.route("/users/<int:user_id>/edit", methods=["GET", "POST"])
@login_required()  # --- VULN-12: same missing role check ---
def edit_user(user_id):
    staff = User.query.get_or_404(user_id)

    # Fail-safe default: prevent an account from managing itself here --

    if staff.id == session.get("user_id"):
        flash("You cannot manage your own account from this page.")
        return redirect(url_for("admin.users"))

    if request.method == "POST":
        before = {"user_type": staff.user_type, "lock_status": staff.lock_status,
                  "position": staff.position}

        staff.first_name = request.form.get("first_name", staff.first_name)
        staff.last_name = request.form.get("last_name", staff.last_name)
        staff.position = request.form.get("position", staff.position)
        staff.phone = request.form.get("phone", staff.phone)
        staff.lock_status = request.form.get("lock_status", staff.lock_status)

       # VULN-17: user_type taken from the form, privilege escalation
        staff.user_type = request.form.get("user_type", staff.user_type)
  

        after = {"user_type": staff.user_type, "lock_status": staff.lock_status,
                 "position": staff.position}

        action = "user_role_change" if before["user_type"] != after["user_type"] else "user_update"
        log_action(action, target_type="user", target_id=staff.id, before=before, after=after)
        db.session.commit()
        flash(f"User '{staff.username}' updated.")
        return redirect(url_for("admin.users"))

    return render_template("admin/user_edit.html", staff=staff)


@admin_bp.route("/users/<int:user_id>/reset-password", methods=["POST"])
@login_required()  # --- VULN-12: same missing role check ---
def reset_password(user_id):
    import hashlib
    staff = User.query.get_or_404(user_id)

    # VULN-16: hardcoded default password on reset and new user (MD5)
    default_password = "Welcome123!"
    staff.password = hashlib.md5(default_password.encode()).hexdigest()
    log_action("password_reset", target_type="user", target_id=staff.id,
               after={"password_source": "hardcoded_default"})
    db.session.commit()

    flash(f"Password for '{staff.username}' reset to: {default_password}")
    return redirect(url_for("admin.edit_user", user_id=staff.id))


@admin_bp.route("/audit-log")
@login_required(role="admin")  
def audit_log():
    entries = AuditLog.query.order_by(AuditLog.created_at.desc()).limit(200).all()
    return render_template("admin/audit_log.html", entries=entries)


@admin_bp.route("/users/<int:user_id>/lock", methods=["POST"])
@login_required()  # --- VULN-12: same missing role check ---
def lock_user(user_id):
    
    staff = User.query.get_or_404(user_id)
    if staff.id == session.get("user_id"):
        flash("You cannot lock your own account.")
        return redirect(url_for("admin.users"))

    before = {"lock_status": staff.lock_status}
    staff.lock_status = "locked"
    log_action("user_lock", target_type="user", target_id=staff.id,
               before=before, after={"lock_status": "locked"})
    db.session.commit()
    flash(f"'{staff.username}' locked out.")
    return redirect(url_for("admin.edit_user", user_id=staff.id))


@admin_bp.route("/users/<int:user_id>/unlock", methods=["POST"])
@login_required()  # --- VULN-12: same missing role check ---
def unlock_user(user_id):
    staff = User.query.get_or_404(user_id)

    before = {"lock_status": staff.lock_status}
    staff.lock_status = "active"
    log_action("user_unlock", target_type="user", target_id=staff.id,
               before=before, after={"lock_status": "active"})
    db.session.commit()
    flash(f"'{staff.username}' unlocked.")
    return redirect(url_for("admin.edit_user", user_id=staff.id))


@admin_bp.route("/users/<int:user_id>/resign", methods=["POST"])
@login_required()  # --- VULN-12: same missing role check ---
def resign_user(user_id):
    
    from datetime import date
    staff = User.query.get_or_404(user_id)

    if staff.id == session.get("user_id"):
        flash("You cannot resign your own account.")
        return redirect(url_for("admin.users"))

    before = {"resign_status": staff.resign_status, "lock_status": staff.lock_status}
    staff.resign_status = "resigned"
    staff.resign_date = date.today()
    staff.lock_status = "locked"  # blocks login -- see the lock_status check in auth.login()
    after = {"resign_status": staff.resign_status, "lock_status": staff.lock_status,
             "resign_date": str(staff.resign_date)}

    log_action("user_resign", target_type="user", target_id=staff.id, before=before, after=after)
    db.session.commit()
    flash(f"'{staff.username}' marked as resigned and locked out.")
    return redirect(url_for("admin.edit_user", user_id=staff.id))


@admin_bp.route("/users/<int:user_id>/reactivate", methods=["POST"])
@login_required()  # --- VULN-12: same missing role check ---
def reactivate_user(user_id):
    staff = User.query.get_or_404(user_id)

    before = {"resign_status": staff.resign_status, "lock_status": staff.lock_status}
    staff.resign_status = "active"
    staff.resign_date = None
    staff.lock_status = "active"
    after = {"resign_status": staff.resign_status, "lock_status": staff.lock_status}

    log_action("user_reactivate", target_type="user", target_id=staff.id, before=before, after=after)
    db.session.commit()
    flash(f"'{staff.username}' reactivated.")
    return redirect(url_for("admin.edit_user", user_id=staff.id))


@admin_bp.route("/users/<int:user_id>/delete", methods=["POST"])
@login_required()  # --- VULN-12: same missing role check ---
def delete_user(user_id):
    # VULN-08b: no CSRF token here either.
    staff = User.query.get_or_404(user_id)

    if staff.id == session.get("user_id"):
        flash("You cannot delete your own account.")
        return redirect(url_for("admin.users"))

    try:
        log_action("user_delete", target_type="user", target_id=staff.id,
                   before={"username": staff.username, "user_type": staff.user_type})
        db.session.delete(staff)
        db.session.commit()
        flash(f"User '{staff.username}' deleted.")
    except Exception:
        # leads.agent_id is ON DELETE RESTRICT -- a user with assigned leads can't be deleted until those leads are reassigned first.
        db.session.rollback()
        flash(f"Could not delete '{staff.username}': they still have assigned leads. Reassign those first.")

    return redirect(url_for("admin.users"))


@admin_bp.route("/users")
@login_required()  # --- VULN-12: same missing role check ---
def users():
    all_users = User.query.all()
    return render_template("admin/users.html", users=all_users)


@admin_bp.route("/users/new", methods=["GET", "POST"])
@login_required()  # --- VULN-12: same missing role check ---
def new_user():
    if request.method == "GET":
        return render_template("admin/user_new.html")

    import hashlib
    from datetime import date

    # --- VULN-16: predictable default password 

    default_password = "Welcome123!"
    password_hash = hashlib.md5(default_password.encode()).hexdigest()

    new_staff = User(
        first_name=request.form["first_name"],
        last_name=request.form["last_name"],
        username=request.form["username"],
        password=password_hash,
        user_type=request.form.get("user_type", "sales"),
        lock_status="active",
        resign_status="active",
        about_me="",
        employment_date=date.today(),
        profile_picture="",
        position=request.form.get("position", ""),
        phone=request.form.get("phone", ""),
    )
    db.session.add(new_staff)
    db.session.flush()
    log_action("user_create", target_type="user", target_id=new_staff.id,
               after={"username": new_staff.username, "user_type": new_staff.user_type,
                      "password_source": "hardcoded_default"})
    db.session.commit()

    # --- VULN-16 : the default password is shown 
    flash(f"User '{new_staff.username}' created. Default password: {default_password}")
    return redirect(url_for("admin.users"))


@admin_bp.route("/inquiries")
@login_required()  # --- VULN-12: same missing role check ---
def inquiries():
   # VULN-02: inquiry message rendered unescaped (stored XSS)
    all_inquiries = Inquiry.query.order_by(Inquiry.inquiry_date.desc()).all()
    return render_template("admin/inquiries.html", inquiries=all_inquiries)


@admin_bp.route("/contact-messages")
@login_required()  # --- VULN-12: same missing role check ---
def contact_messages():
    all_messages = ContactMessage.query.order_by(ContactMessage.submitted_at.desc()).all()
    return render_template("admin/contact_messages.html", messages=all_messages)


@admin_bp.route("/subscribers")
@login_required()  # --- VULN-12: same missing role check ---
def subscribers():
    all_subscribers = Subscriber.query.order_by(Subscriber.subscribed_at.desc()).all()
    return render_template("admin/subscribers.html", subscribers=all_subscribers)


@admin_bp.route("/leads/export", methods=["POST"])
@login_required(role="admin")  # role check present here -- isolates VULN-11 cleanly
def export_leads():
    date_range = request.form.get("date_range", "")

    # VULN-11: command injection, user input passed to a shell in export Try : 2024-01-01_2024-12-31; whoami
    export_path = os.path.join(current_app.root_path, "static", "exports", "leads_export.csv")
    os.makedirs(os.path.dirname(export_path), exist_ok=True)

    
    log_action("leads_export", target_type="export", after={"date_range_submitted": date_range})
    db.session.commit()

    os.system(f'echo Exporting leads for range {date_range} > "{export_path}"')
   
    flash("Export generated.")
    return send_file(export_path, as_attachment=True)
