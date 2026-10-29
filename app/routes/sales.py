"""
  VULN-09  IDOR - /leads/<id> has no ownership check 
  VULN-07  Param tamper - agent_id trusted from a hidden form field on lead
  VULN-08  CSRF - no CSRF token on /leads/<id>/update
  VULN-10  Unrestricted upload - /profile picture upload, no type/size check
  VULN-18: password change without current-password check, MD5
"""

import os
import hashlib
from flask import Blueprint, render_template, request, redirect, url_for, session, flash, current_app
from app.models import db, Lead, User
from app.routes.auth import login_required
from app.audit import log_action

sales_bp = Blueprint("sales", __name__, url_prefix="/sales")


@sales_bp.route("/dashboard")
@login_required()
def dashboard():
    # Shows only this agent's leads on the dashboard itself -- the IDOR is
    # reachable via direct URL manipulation on /leads/<id>, not from here.
    my_leads = Lead.query.filter_by(agent_id=session["user_id"]).all()
    return render_template("sales/dashboard.html", leads=my_leads)


@sales_bp.route("/leads/<int:lead_id>")
@login_required()
def view_lead(lead_id):
    # --- VULN-09: IDOR 
    lead = Lead.query.get_or_404(lead_id)
    return render_template("sales/lead_detail.html", lead=lead)


@sales_bp.route("/leads/<int:lead_id>/update", methods=["POST"])
@login_required()
def update_lead(lead_id):
    # --- VULN-09 (same IDOR, on the write path) + VULN-08: no CSRF token ---
    lead = Lead.query.get_or_404(lead_id)

    before = {"status": lead.status, "remark": lead.remark}
    lead.status = request.form.get("status", lead.status)
    lead.remark = request.form.get("remark", lead.remark)
    after = {"status": lead.status, "remark": lead.remark}

    log_action("lead_update", target_type="lead", target_id=lead.id, before=before, after=after)
    db.session.commit()
    flash("Lead updated.")
    return redirect(url_for("sales.view_lead", lead_id=lead.id))


@sales_bp.route("/leads/new", methods=["GET", "POST"])
@login_required()
def new_lead():
    if request.method == "GET":
        return render_template("sales/new_lead.html")

    # --- VULN-07: parameter tampering
    # agent_id is taken from the submitted form instead of session["user_id"].
    # A malicious/curious sales user can submit someone else's agent_id (or
    # any arbitrary id) as the owner of a new lead.
    agent_id = request.form.get("agent_id", session["user_id"])

    lead = Lead(
        customer_name=request.form["customer_name"],
        phone=request.form["phone"],
        status="new",
        interest=request.form.get("interest", ""),
        remark=request.form.get("remark", ""),
        agent_id=agent_id,
    )
    db.session.add(lead)
    db.session.flush()  
    log_action("lead_create", target_type="lead", target_id=lead.id,
               after={"customer_name": lead.customer_name, "agent_id": agent_id})
    db.session.commit()
    flash("Lead created.")
    return redirect(url_for("sales.dashboard"))


@sales_bp.route("/profile", methods=["GET", "POST"])
@login_required()
def profile():
    user = User.query.get(session["user_id"])

    if request.method == "GET":
        return render_template("sales/profile.html", user=user)

    file = request.files.get("profile_picture")
    if file and file.filename:
        # --- VULN-10: unrestricted file upload ----------
     
        os.makedirs(os.path.join(current_app.root_path, "static", "uploads"), exist_ok=True)
        save_path = os.path.join(current_app.root_path, "static", "uploads", file.filename)
        file.save(save_path)
        user.profile_picture = f"/static/uploads/{file.filename}"

    user.phone = request.form.get("phone", user.phone)
    user.about_me = request.form.get("about_me", user.about_me)

    # --- VULN-18: password change with no current-password verification ---
   
    new_password = request.form.get("new_password", "")
    confirm_password = request.form.get("confirm_password", "")
    if new_password:
        if new_password != confirm_password:
            flash("New password and confirmation do not match.")
            return redirect(url_for("sales.profile"))
        user.password = hashlib.md5(new_password.encode()).hexdigest()
        log_action("password_change", target_type="user", target_id=user.id)
        flash("Password changed.")

    db.session.commit()
    flash("Profile updated.")
    return redirect(url_for("sales.profile"))
