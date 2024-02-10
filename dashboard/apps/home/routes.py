from apps.home import blueprint
from flask import render_template, request, redirect
from flask_login import login_required, current_user
from jinja2 import TemplateNotFound
from apps import global_pull, db
from apps.authentication.models import Users
from apps.authentication.util import hash_pass

from kubernetes import client, config
from kubernetes.client import configuration
from datetime import datetime, timedelta, timezone
import markdown
import re
import requests
import os

def sidebar(role):
        
    sidebar = [
        {"url": "/student", "icon": "fa fa-desktop", "title": "Student Dashboard"},
        {"url": "/student/clean-lessons", "icon": "fa fa-desktop", "title": "Clean Lessons"},
        {"url": "/logout", "icon": "fa fa-desktop", "title": "Logout"},
    ]

    if current_user.role == "teacher":
        sidebar = [
            {"url": "/teacher", "icon": "fa fa-desktop", "title": "Admin Dashboard"},
            {"url": "/teacher/users", "icon": "fa fa-users", "title": "Users"},
            {"url": "/teacher/resources", "icon": "fa fa-database", "title": "Resources"},
            {"url": "/teacher/refresh", "icon": "fa fa-refresh", "title": "Refresh Deployer Resources"},
        ] + sidebar

    return sidebar

@blueprint.route('/index')
@login_required
def index():

    return render_template('home/index.html', segment='index', sidebar=sidebar(current_user.role))


@blueprint.route('/teacher/refresh')
@login_required
def refresh():
    global_pull()

    segment = get_segment(request)

    return redirect("/teacher", code=302)


@blueprint.route('/teacher/generate-users', methods=["POST"])
@login_required
def generateUsers():
    if current_user.role != "teacher":
        return redirect("/index", code=403)
    
    if request.method == 'POST':
        users = []
        userform = request.form["users"].splitlines()
        for userline in userform:
            userparsed = userline.split(",")
            if len(userparsed) != 3:
                print(userparsed)
                continue
            password = "password"
            role = "student"
            username = userparsed[0]
            if len(userparsed[1]) > 0:
                password = userparsed[1]
            if len(userparsed[2]) > 0:
                role = userparsed[2]

            user = Users(username = username,
                        role = role,
                        password = password)
            print(userline)
            users.append(user)

        # If user exists, update; if not, insert
        for user in users:
            if db.session.query(Users).filter_by(username=user.username).first() is None:
                db.session.add(user)
            else:
                db.session.query(Users).filter_by(username=user.username).update({"password": user.password, "role": user.role})

        db.session.commit()

    return redirect("/teacher/users", code=302)


@blueprint.route('/teacher/delete-users', methods=["POST"])
@login_required
def deleteUsers():
    if current_user.role != "teacher":
        return redirect("/index", code=403)
    
    if request.method == 'POST':
        users = request.form.getlist("users")
        for userid in users:
            db.session.query(Users).filter_by(id=userid).delete()
        db.session.commit()

    return redirect("/teacher/users", code=302)


@blueprint.route('/teacher/users')
@login_required
def users():
    if current_user.role != "teacher":
        return redirect("/index", code=403)
    
    segment = get_segment(request)

    users = db.session.execute("SELECT id, username, role FROM users").fetchall()
    
    return render_template("home/users.html", segment=segment, sidebar=sidebar(current_user.role), users=users)


@blueprint.route('/teacher/clean-environment', methods=["POST"])
@login_required
def cleanEnvironment():
    if current_user.role != "teacher":
        return redirect("/index", code=403)
    
    resp = requests.post(os.getenv("JENKINSURL", "http://192.168.128.103")+"/job/student-reconcile/buildWithParameters", 
                        data={
                            "token": os.getenv("SDTOKEN", "studentdeploy"),
                            "STUDENTNAME": request.form["namespace"],
                        },
                        headers={
                            "Authorization": os.getenv("JENKINSAUTH")
                        })
    
    return redirect("/teacher/resources", code=302)


@blueprint.route('/teacher/resources')
@login_required
def resources():
    segment = get_segment(request)

    # Get all namespaces with label key "lesson" 
    config.load_incluster_config()
    cluster = client.CoreV1Api()
    namespaces = cluster.list_namespace()
    lessons = []

    for namespace in namespaces.items:
        if namespace.metadata.labels.get("lesson"):
            lesson = {
                "namespace": namespace.metadata.name,
                "lesson": namespace.metadata.labels.get("lesson"),
                "student": namespace.metadata.labels.get("student"),
                "timeleft": (namespace.metadata.creation_timestamp+timedelta(hours=4))-datetime.now(timezone.utc),
            }
            lessons.append(lesson)

    return render_template("home/resources.html", segment=segment, sidebar=sidebar(current_user.role), lessons=lessons)


@blueprint.route('/teacher')
@login_required
def teacher():
    segment = get_segment(request)
    
    usefulLinks = [
        {"url": "http://"+os.getenv("GRAFANA", "192.168.128.101"), "icon": "fa fa-desktop", "title": "Grafana"},
        {"url": os.getenv("JENKINSURL", "http://192.168.128.103"), "icon": "fa fa-desktop", "title": "Jenkins"},
        {"url": os.getenv("GITEAURL", "http://192.168.128.102"), "icon": "fa fa-desktop", "title": "Gitea"},
    ]

    return render_template("home/teacher.html", segment=segment, sidebar=sidebar(current_user.role), usefulLinks=usefulLinks)


@blueprint.route('/student/create-lesson/<lesson>')
@login_required
def createLesson(lesson):
    segment = get_segment(request)

    user = current_user.username
    resp = requests.post(os.getenv("JENKINSURL", "http://192.168.128.103")+"/job/student-deploy/buildWithParameters", 
                         data={
                             "token": os.getenv("SDTOKEN", "studentdeploy"),
                             "STUDENTNAME": user, 
                             "LESSON": lesson},
                         headers={
                             "Authorization": os.getenv("JENKINSAUTH")
                         })
    
    return redirect("/student", code=302)


@blueprint.route('/student/clean-lessons')
@login_required
def cleanLesson():
    segment = get_segment(request)

    user = current_user.username
    resp = requests.post(os.getenv("JENKINSURL", "http://192.168.128.103")+"/job/student-reconcile/buildWithParameters", 
                         data={
                             "token": os.getenv("SDTOKEN", "studentdeploy"),
                             "STUDENTNAME": user,
                         },
                         headers={
                             "Authorization": os.getenv("JENKINSAUTH")
                         })

    return redirect("/student", code=302)


@blueprint.route('/student')
@login_required
def student():
    config.load_incluster_config()
    cluster = client.CoreV1Api()

    namespaces = cluster.list_namespace()
    lesson = None
    name = None
    timestamp = None
    vnc = None
    rdp = None

    for namespace in namespaces.items:
        if current_user.username in namespace.metadata.labels.values():
            lesson = namespace.metadata.labels.get("lesson")
            name = namespace.metadata.name
            timestamp = namespace.metadata.creation_timestamp

    if name:
        services = cluster.list_namespaced_service(name)
        for service in services.items:
            for port in service.spec.ports:
                if "vnc" in port.name:
                    vnc = f"{service.status.load_balancer.ingress[0].ip}:{port.port}"
                    continue
                if "rdp" in port.name:
                    rdp = f"{service.status.load_balancer.ingress[0].ip}:{port.port}"
                    continue

    lessons = {}
    root = "/tmp/lessons/lessons"
    for dir in os.listdir(root):
        if os.path.isdir(os.path.join(root, dir)):
            if dir == lesson:
                lessonRet = {
                    "active": True, # Check kubeapi response if label is set to this lesson
                    "grafana": "http://"+os.getenv("GRAFANA", "192.168.128.101")+"/d/studentboard/lesson-scores-per-student?orgId=1&refresh=15m&from=now-1h&to=now&var-students="+current_user.username+"&var-Lessons="+lesson+"&kiosk=1",
                    "name": dir,
                    "timeleft": (timestamp+timedelta(hours=4))-datetime.now(timezone.utc), # Display age of the lesson 
                    "vnc": vnc, # Get vnc url for this lesson
                    "rdp": rdp, # Get rdp url for this lesson
                }
            else:
                lessonRet = {
                    "active": False, # Check kubeapi response if label is set to this lesson
                    "grafana": "http://"+os.getenv("GRAFANA", "192.168.128.101")+"/d/studentboard/lesson-scores-per-student?orgId=1&refresh=15m&from=now-1h&to=now&var-students="+current_user.username+"&var-Lessons="+dir+"&kiosk=1",
                    "name": dir,
                    "timeleft": None, # Display age of the lesson
                    "vnc": None, # Get vnc url for this lesson
                    "rdp": None, # Get rdp url for this lesson
                }
            lessons[dir] = lessonRet
    return render_template('home/student.html', segment='student', lessons=lessons, sidebar=sidebar(current_user.role))


@blueprint.route('/student/lessons/<lesson>')
@login_required
def lesson(lesson):
    mdcontent = markdown.markdown(open(f"/tmp/lessons/lessons/%s/README.md" % lesson).read(), extensions=['nl2br'])
    content = re.sub(r"src=\"\.\/", f"src=\"/static/assets/lessons/%s/" % lesson, mdcontent)
    content = re.sub(r"<code>", "<pre><code>", content)
    content = re.sub(r"</code>", "</code></pre>", content)

    return render_template('home/readme.html', content=content, sidebar=sidebar(current_user.role))


@blueprint.route('/<template>')
@login_required
def route_template(template):

    try:

        if not template.endswith('.html'):
            template += '.html'

        # Detect the current page
        segment = get_segment(request)

        # Serve the file (if exists) from app/templates/home/FILE.html
        return render_template("home/" + template, segment=segment, sidebar=sidebar(current_user.role))

    except TemplateNotFound:
        return render_template('home/page-404.html'), 404

    except:
        return render_template('home/page-500.html'), 500


# Helper - Extract current page name from request
def get_segment(request):

    try:

        segment = request.path.split('/')[-1]

        if segment == '':
            segment = 'index'

        return segment

    except:
        return None
