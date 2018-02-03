
![CatPics](https://raw.githubusercontent.com/SOBotics/CopyPastor/master/static/favicon.png)

# Copy Pastor

A very small Flask App to serve as a web dashboard for the [Guttenberg](https://stackapps.com/questions/7197/guttenberg-a-bot-searching-for-plagiarism-on-stack-overflow) bot which would help in the plagiarism flags.

The final plan is to demarcate the plagiarized portions clearly, and to compare it with the target post.


# Setup

To setup the app on your local machine:

    git clone https://github.com/SOBotics/CopyPastor.git
    cd CopyPastor
    sh setup.sh
    flask run        # or python3 -m flask run


# API Call


## POST  `/posts/create`

POST Parameters:

| Parameter | Description                                                   |
| ----------| ------------------------------------------------------------- |
|url_one    | The URL of the post which is (possibly) plagairized           |
|url_two    | The URL of the original post                                  |
|title_one  | Title of the post which is (possibly) plagiarized             |
|title_two  | Title of the original post                                    |
|date_one   | The date when the (possibly) plagiarized post was created     |
|date_two   | The date when the original post was created                   |
|body_one   | The body markdown of the post which is (possibly) plagiarized |
|body_two   | The body markdown of the original post                        |
|key        | The authentication key provided, to validate the request      |



### Responses

Success Response

     {"post_id":<postID>,"status":"success"}

Failure Response (Error Code 400 Bad Request)

     {"message":<error reason>,"status":"failure"}


## POST  `/feedback/create`

POST Parameters:

| Parameter      | Description                                                         |
| ---------------| --------------------------------------------------------------------|
| post_id        | The CopyPastor Post ID for the post whose feedback is being provided|
| feedback_type  | The type of feedback, can be "tp" or "fp"                           |
| username       | Username of the user who provided the feedback                      |
| link           | A link to the chat profile of the user who provided the feedback    |
| key            | The authentication key provided, to validate the request            |

### Responses

Success Response

     {"feedback_id":<feedbackID>,"status":"success",message:<standard message>}

| Type              | Message returned                     |
|-------------------|--------------------------------------|
| New Feedback      | User feedback registered successfully|
| Updating Feedback | User feedback updated from -- to --  |
| Same Feedback     | User feedback already registered     |


Failure Response (Error Code 400 Bad Request)

     {"message":<error reason>,"status":"failure"}


## POST or GET `/posts/find`

POST call returns a JSON with the `post_id` of the report containing the two given answers.
GET call redirects to that particular web view. 

Parameters:

| Parameter      | Description                                                         |
| ---------------| --------------------------------------------------------------------|
| url_one        | The URL of the post which is (possibly) plagairized                 |
| url_two        | The URL of the original post                                        |


## GET  `/posts/findTarget`

Returns a list of target posts which have been detected as the original posts from which the 
given answer has been plagiarized


Parameters:

| Parameter      | Description                                                         |
| ---------------| --------------------------------------------------------------------|
| url            | The URL of any answer whose target posts are needed                 |


Success Response 

    {
    	"status": "success",
    	"posts": [{
    		"post_id": "cp post id of 1",
    		"target_url": "url of the original post"
    	}, {
    		"post_id": "cp post id of 2",
    		"target_url": "url of the original post"
    	}, {
    		"post_id": "cp post id of 3",
    		"target_url": "url of the original post"
    	}]
    }

## GET `/posts/pending`

Returns a list of pending posts which have no feedback. Parameter `reason` when set to `true`, returns more details about the pending posts.

    { "posts": [ 1, 2, 3], "status": "success"}

## GET `/posts/<post_id>`

A web view of the two posts next to each other. Error code 410 for deleted reports and 404 for non available reports.

![ScreenGrab](https://raw.githubusercontent.com/SOBotics/CopyPastor/master/static/sample.png)
