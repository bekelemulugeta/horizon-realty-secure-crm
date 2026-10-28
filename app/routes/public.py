

from flask import Blueprint, render_template, request, redirect, url_for, jsonify
from app.models import db, Project, Inquiry, Review, ContactMessage, Subscriber

public_bp = Blueprint("public", __name__)


@public_bp.route("/")
def home():
    featured = Project.query.order_by(Project.created_at.desc()).limit(3).all()
    return render_template("public/home.html", featured=featured)


@public_bp.route("/projects")
def projects():
    q = request.args.get("q", "")

    if q:
       
        raw_query = (
            "SELECT id, title, location, price, discount_price, image_path FROM projects "
            f"WHERE title LIKE '%{q}%' OR location LIKE '%{q}%'"
        )
        results = db.session.execute(db.text(raw_query)).fetchall()
    else:
        results = Project.query.all()

    return render_template("public/projects.html", projects=results, q=q)


@public_bp.route("/projects/<int:project_id>")
def project_detail(project_id):
    project = Project.query.get_or_404(project_id)
    reviews = Review.query.filter_by(project_id=project_id).order_by(Review.created_at.desc()).all()
    return render_template("public/project_detail.html", project=project, reviews=reviews)


@public_bp.route("/projects/<int:project_id>/inquire", methods=["POST"])
def inquire(project_id):
    inquiry = Inquiry(
        project_id=project_id,
        name=request.form.get("name", ""),
        phone=request.form.get("phone", ""),
        message=request.form.get("message", ""),
    )
    db.session.add(inquiry)
    db.session.commit()
    return redirect(url_for("public.project_detail", project_id=project_id))


@public_bp.route("/projects/<int:project_id>/review", methods=["POST"])
def review(project_id):
   
    r = Review(
        project_id=project_id,
        name=request.form.get("name", "Anonymous"),
        rating=request.form.get("rating", 5),
        comment=request.form.get("comment", ""),
    )
    db.session.add(r)
    db.session.commit()
    # -----------------------------------------------------------------------
    return redirect(url_for("public.project_detail", project_id=project_id))


@public_bp.route("/about")
def about():
    return render_template("public/about.html")


@public_bp.route("/privacy")
def privacy():
    return render_template("public/privacy.html")


@public_bp.route("/terms")
def terms():
    return render_template("public/terms.html")


@public_bp.route("/contact", methods=["GET", "POST"])
def contact():
    if request.method == "GET":
        return render_template("public/contact.html")

    msg = ContactMessage(
        name=request.form.get("name", ""),
        email=request.form.get("email", ""),
        phone=request.form.get("phone", ""),
        message=request.form.get("message", ""),
    )
    db.session.add(msg)
    db.session.commit()
    return render_template("public/contact.html", sent=True)


@public_bp.route("/subscribe", methods=["POST"])
def subscribe():
    email = request.form.get("email", "")
    if email:
        db.session.add(Subscriber(email=email))
        db.session.commit()
    return redirect(url_for("public.home"))



@public_bp.route("/projects/<int:project_id>/embed")
def embed(project_id):
    project = Project.query.get_or_404(project_id)

    return render_template("public/embed.html", project=project)


@public_bp.route("/api/projects/<int:project_id>")
def api_project(project_id):
    project = Project.query.get_or_404(project_id)
    response = jsonify({
        "id": project.id,
        "title": project.title,
        "location": project.location,
        "price": str(project.price) if project.price else None,
        "image_path": project.image_path,
    })
   
    return response
