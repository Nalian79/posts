import json

from flask import request, Response, url_for
from jsonschema import validate, ValidationError

import models
import decorators
from posts import app
from database import session

post_schema = {
    "properties": {
        "title": {"type" : "string"},
        "body": {"type" : "string"}
        },
    "required": ["title", "body"]
}

@app.route("/api/posts", methods=["GET"])
@decorators.accept("application/json")
def posts_gets():
    """ Get a list of posts """
    # Get the querystring arguments
    title_like = request.args.get("title_like")
    body_like = request.args.get("body_like")

    # Get and filter the posts from the DB
    posts = session.query(models.Post)
    if title_like:
        posts = posts.filter(models.Post.title.contains(title_like))
    elif body_like:
        posts = posts.filter(models.Post.body.contains(body_like))
    elif title_like and body_like:
        posts = posts.filter(models.Post.title.contains(title_like))
        posts = posts.filter(models.Post.body.contains(body_like))
    posts = posts.all()

    # Convert the posts to JSON and return a response.
    data = json.dumps([post.as_dictionary() for post in posts])
    return Response(data, 200, mimetype="application/json")

@app.route("/api/posts/<int:id>", methods=["GET", "PUT"])
@decorators.accept("application/json")
def post_get(id):
    """ Single post endpoint for get and edits"""

    if request.method == "GET":
        # Get the post from the database
        post = session.query(models.Post).get(id)

        # Check whether the post exists
        # If not return a 404 with a helpful message
        if not post:
            message = "Could not find post with id {}".format(id)
            data = json.dumps({"message": message})
            return Response(data, 404, mimetype="application/json")
        # Return the post as JSON
    elif request.method == "PUT":
        post = session.query(models.Post).get(id)
        edited_data = json.loads(request.data)
        post.title = edited_data["title"]
        post.body = edited_data["body"]
        session.commit()
    else:
        message = "Invalid HTTP method detected"
        data = json.dumps({"message": message})
        return Response(data, 500, mimetype="application/json")

    # Return the post as JSON
    data = json.dumps(post.as_dictionary())
    return Response(data, 200, mimetype="application/json")


@app.route("/api/posts/<int:id>", methods=["DELETE"])
def delete_post(id):
    """ Delete a single post endpoint """
    post = session.query(models.Post).get(id)
    session.query(models.Post).filter(models.Post.id == id).delete()
    session.commit()
    check_post = session.query(models.Post).get(id)
    if check_post:
        message = "Could not delete post {}".format(id)
        data = json.dumps({"message": message})
        return Response(data, 400, mimetype="application/json")
    message = "Successfully deleted post {}".format(id)
    data = json.dumps({"message": message})
    return Response(data, 200, mimetype="application/json")

@app.route("/api/posts", methods=["POST"])
@decorators.accept("application/json")
@decorators.require("application/json")
def posts_post():
    """ Add a new post """
    data = request.json

    # Check that the JSON supplied is valid
    # If not, return a 422 Unprocessable Entity
    try:
        validate(data, post_schema)
    except ValidationError as error:
        data = {"message": error.message}
        return Response(json.dumps(data), 422, mimetype="application/json")

    # Add the post to the DB
    post = models.Post(title=data["title"], body=data["body"])
    session.add(post)
    session.commit()

    # Return a 201 Created, containing the post as JSON and with the
    # Location header set to the location of the post
    data = json.dumps(post.as_dictionary())
    headers = {"Location": url_for("post_get", id=post.id)}
    return Response(data, 201, headers=headers, mimetype="application/json")
